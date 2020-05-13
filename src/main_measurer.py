#!/usr/bin/env python3

"""
docstring is here
"""

import requests
import traceback
import namedtupled
import sys
import json
import socket
import binascii
import netifaces
import ipaddress
import datetime
import time
import ipwhois
import uptime
import dns.name
import dns.message
import dns.query
import dns.rdatatype
import dns.exception
import concurrent.futures as cfu

import common.common.framework as framework
import common.data.dao as dao
import common.data.types as types
import common.data.errors as errors


class Measurer(framework.SetupwithInfluxdb):

    def __init__(self):
        super().__init__(__name__, __file__)

    def set_measurer_id(self):
        hostname = socket.gethostname()
        self.measurer_id = "%s-%d" % (
            self.cnfs.measurement.region,
            binascii.crc32(hostname.encode("utf8")))

    def set_server_boottime(self):
        current_time = datetime.datetime.utcnow()
        delta = datetime.timedelta(seconds=uptime.uptime())
        self.server_boottime = str((current_time - delta).isoformat()) + "Z"

    def set_global_ipaddress(self):
        selected_ipv4 = None
        selected_ipv6 = None

        for interface in netifaces.interfaces():
            ifaddresses = netifaces.ifaddresses(interface)
            addrs = []
            if netifaces.AF_INET in ifaddresses:
                addrs.extend(ifaddresses[netifaces.AF_INET])
            if netifaces.AF_INET6 in ifaddresses:
                addrs.extend(ifaddresses[netifaces.AF_INET6])
            for addr in addrs:
                if "addr" not in addr:
                    continue
                try:
                    addr_obj = ipaddress.ip_address(addr["addr"])
                except Exception as ex:
                    self.logger.warning(
                        "exception occurred while converting addr: %s" %
                        str(ex))
                    continue
                if addr_obj.is_global:
                    ipadr = str(addr_obj)
                    if addr_obj.version == 4 and selected_ipv4 is None:
                        selected_ipv4 = ipadr
                        if selected_ipv6 is not None:
                            break
                    elif addr_obj.version == 6 and selected_ipv6 is None:
                        selected_ipv6 = ipadr
                        if selected_ipv4 is not None:
                            break
            else:
                continue
            break

        self.logger.info("selected ipv4 address: %s" % (selected_ipv4))
        self.logger.info("selected ipv6 address: %s" % (selected_ipv6))

        self.ipv4 = selected_ipv4
        self.ipv6 = selected_ipv6

    def validate_id(self):
        if self.ipv4 is None or self.ipv6 is None:
            self.logger.critical("measurer must have global IPv4/IPv6 address")
            raise errors.DNSProbeError("failed to validate ipaddress")

    def set_net_description(self):

        self.net_desc_v4 = None
        self.net_desc_v4 = None

        self.load_tmpdata()

        if "net_desc" in self.tmp_data:
            net_desc = self.tmp_data["net_desc"]
            if ("v4" in net_desc) and ("v6" in net_desc):
                self.logger.debug("found net description from tmp data")
                self.net_desc_v4 = net_desc["v4"]
                self.net_desc_v6 = net_desc["v6"]

        if (self.net_desc_v4 is None) or (self.net_desc_v6 is None):
            try:
                self.logger.debug("querying rdap...")
                v4 = ipwhois.IPWhois(self.ipv4)
                v6 = ipwhois.IPWhois(self.ipv6)
                v4ret = v4.lookup_rdap()
                v6ret = v6.lookup_rdap()

                self.net_desc_v4 = (v4ret["asn"], v4ret["asn_description"])
                self.net_desc_v6 = (v6ret["asn"], v6ret["asn_description"])

                self.tmp_data["net_desc"] = dict(v4=self.net_desc_v4,
                                                 v6=self.net_desc_v6)
                self.write_tmpdata()

            except Exception as ex:
                self.logger.warning("unable to get ipaddress description: %s" %
                                    (str(ex)))
                self.net_desc_v4 = ("unknown", "unknown")
                self.net_desc_v6 = ("unknown", "unknown")

        self.logger.info("IPv4 description: %s" % str(self.net_desc_v4))
        self.logger.info("IPv6 description: %s" % str(self.net_desc_v6))

    def load_measurement_info(self):

        protocol = self.cnfs.controller.protocol
        host = self.cnfs.controller.host
        port = self.cnfs.controller.port
        user = self.cnfs.controller.user
        passwd = self.cnfs.controller.passwd
        path = self.cnfs.controller.path
        timeout = int(self.cnfs.controller.timeout)

        controller = "%s://%s:%s%s" % (protocol, host, port, path)
        self.logger.info("controller: %s" % (controller))

        try:
            response = requests.get(controller,
                                    auth=(user, passwd),
                                    timeout=timeout)
        except requests.RequestException as ex:
            self.logger.error("unexpected error occurred: %s" % (str(ex)))
            raise errors.DNSProbeError("unable to get measurement info")

        self.logger.info("http status code: %s" % (response.status_code))

        if response.status_code != 200:
            self.logger.error("status code is not 200: %s" %
                              (response.status_code))
            raise errors.DNSProbeError("unable to get measurement info")

        try:
            json_obj = json.loads(response.text)
            self.logger.info("json object load in properly from controller")
        except json.decoder.JSONDecodeError as ex:
            self.logger.error("undecodable object responsed: %s" % (str(ex)))
            raise errors.DNSProbeError("unable to get measurement info")

        self.logger.debug(json_obj)

        try:
            self.measurement_info = namedtupled.map(json_obj)
        except Exception:
            self.logger.error("unable to map json obj to namedtuple")
            raise errors.DNSProbeError("unable to get measurement info")

    def measurement_core(self,
                         current_time,
                         nameserver,
                         queryer,
                         dst,
                         src,
                         af,
                         asn,
                         asn_desc,
                         timeout,
                         proto,
                         qname,
                         rrtype,
                         qo,
                         slr_threshold):

        response = None
        err = None

        start_at = time.time()

        try:
            response = queryer(qo, dst, timeout=timeout, source=src)
        except dns.exception.Timeout as ex:
            self.logger.warning("timeout while measurement: %s" % str(ex))
            err = ex
        except OSError as ex:
            self.logger.warning("OSError while measurement: %s" % str(ex))
            err = ex
        except Exception as ex:
            self.logger.warning("unexpected error while measuremet")
            self.logger.warning("%s" % str(ex))
            err = ex
        finally:
            time_diff = (time.time() - start_at) * 1000

        latitude = self.cnfs.measurement.latitude
        longitude = self.cnfs.measurement.longitude

        measured_data = types.make_DNSMeasurementData(current_time,
                                                      time_diff,
                                                      nameserver,
                                                      dst,
                                                      src,
                                                      self.measurer_id,
                                                      asn,
                                                      asn_desc,
                                                      self.server_boottime,
                                                      latitude,
                                                      longitude,
                                                      af,
                                                      proto,
                                                      qname,
                                                      rrtype,
                                                      err,
                                                      response,
                                                      self.cnfs.rdata_storing,
                                                      slr_threshold)
        return measured_data

    def measure_toplevel(self):

        tcp_timeout = self.cnfg.constants.tcp_timeout
        udp_timeout = self.cnfg.constants.udp_timeout
        current_time = str(datetime.datetime.utcnow().isoformat()) + "Z"
        result = []

        queryer_info_by_protocol = \
            {"udp": (dns.query.udp,
                     udp_timeout,
                     self.cnfg.constants.udp_slr_threshold * 1000),
             "tcp": (dns.query.tcp,
                     tcp_timeout,
                     self.cnfg.constants.tcp_slr_threshold * 1000)}

        workers = self.cnfs.measurement.number_of_max_workers
        futures = []

        with cfu.ThreadPoolExecutor(max_workers=workers) as threadpool:

            for measurement in self.measurement_info:

                nameserver = measurement.nameserver
                protocol = measurement.proto
                query = measurement.query
                dst = measurement.destination

                for addr in dst:

                    addr_obj = ipaddress.ip_address(addr)

                    if addr_obj.version == 4:
                        source = self.ipv4
                        asn, asn_desc = self.net_desc_v4
                    elif addr_obj.version == 6:
                        source = self.ipv6
                        asn, asn_desc = self.net_desc_v6
                    else:
                        self.logger.error(
                            "unknown version addr: %s" % str(addr))
                        continue

                    queryer, timeout, slr_threshold = \
                        queryer_info_by_protocol[protocol]

                    qname = query.qname
                    rrtype = query.rrtype

                    try:
                        qname_obj = dns.name.from_text(qname)
                        rrtype_obj = dns.rdatatype.from_text(rrtype)
                        qo = dns.message.make_query(qname_obj,
                                                    rrtype_obj,
                                                    use_edns=True)
                        qo.flags &= 0xFEFF
                        qo.use_edns(edns=0,
                                    options=[dns.edns.GenericOption(
                                        dns.edns.NSID, bytes())])

                    except dns.rdatatype.UnknownRdatatype:
                        self.logger.warning("unknown query: %s" % (rrtype))
                        self.logger.warning("measurement skipped")
                        continue
                    except Exception as ex:
                        self.logger.warning("unable to query: %s" % (str(ex)))
                        self.logger.warning("measurement skipped")
                        continue

                    futures.append(threadpool.submit(self.measurement_core,
                                                     current_time,
                                                     nameserver,
                                                     queryer,
                                                     addr,
                                                     source,
                                                     addr_obj.version,
                                                     asn,
                                                     asn_desc,
                                                     timeout,
                                                     protocol,
                                                     qname,
                                                     rrtype,
                                                     qo,
                                                     slr_threshold))

        for future in cfu.as_completed(futures):
            result.append(future.result())

        self.logger.info("%s data measured" % (len(result)))
        self.logger.debug("following is massured data %s" % str(result))

        return result

    def setup_application(self):
        self.set_measurer_id()
        self.set_global_ipaddress()
        self.set_server_boottime()
        self.validate_id()
        self.set_net_description()
        self.load_measurement_info()
        self.dao_dnsprobe = dao.Mes_dnsprobe(self)

    def run_application(self):
        result = self.measure_toplevel()
        ret = self.dao_dnsprobe.write_measurement_data(result)
        if not ret:
            return 1
        return 0


def main():
    try:
        measurer = Measurer()
    except Exception:
        # LOGGERのセットアップ自体にも失敗している可能性ありの為
        # 標準出力にログ出力
        print(traceback.format_exc())
        sys.exit(1)

    measurer.start()


if __name__ == "__main__":
    main()
