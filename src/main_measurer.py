#!/usr/bin/env python3

"""
docstring is here
"""

import common.common.framework as framework

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
import dns.name
import dns.message
import dns.query
import dns.rdatatype
import dns.exception

from multiprocessing.pool import ThreadPool


class MeasurementDataConverter():

    def __init__(self, logger, cnfg, cnfs):
        self.record_parser = {}
        self.logger = logger
        self.cnfg = cnfg
        self.cnfs = cnfs

    def add_record_parser(self, qname, rtype, func):
        self.record_parser[(qname, rtype)] = func

    def parse_response_to_fields(self, qname, rtype, res):

        if not (qname, rtype) in self.record_parser:
            self.logger.warning("unable to find parser for %s %s" %
                                (qname, rtype))
            return {}

        parser = self.record_parser[(qname, rtype)]

        try:
            qname_obj = dns.name.from_text(qname)
            rtype_obj = dns.rdatatype.from_text(rtype)
            parsed = parser(qname_obj, rtype_obj, res)
            return parsed
        except Exception as ex:
            self.logger.warning("unexpected error %s occurred while parsing" %
                                (str(ex)))
            self.logger.warning("unable to parse %s %s with parser" %
                                (qname, rtype))
            return {}

    def convert_influx_notation(self,
                                current_time,
                                time_diff,
                                nameserver,
                                dst,
                                src,
                                prb_id,
                                af,
                                proto,
                                qname,
                                rrtype,
                                result):

        measurement_name = self.cnfg.data_store.database

        (err, response) = result

        if err:
            field_data = dict(reason=str(err))
            error_class_name = err.__class__.__name__
        else:
            field_data = self.parse_response_to_fields(qname, rrtype, response)
            error_class_name = ""

        field_data.update(dict(time_took=time_diff))

        result = dict(measurement=measurement_name,
                      time=current_time,
                      tags=dict(af=af,
                                dst_addr=dst,
                                dst_name=nameserver,
                                src_addr=src,
                                prb_id=prb_id,
                                prb_lat=self.cnfs.measurement.latitude,
                                prb_lon=self.cnfs.measurement.longitude,
                                proto=proto,
                                rrtype=rrtype,
                                qname=qname,
                                got_response=err is None,
                                error_class_name=error_class_name),
                      fields=field_data)

        return result


def soa_parser(qname_obj, rtype_obj, res):

    rrset = res.get_rrset(res.answer, qname_obj, dns.rdataclass.IN, rtype_obj)

    if (rrset is None) or (len(rrset) == 0):
        return {}

    record = rrset[0]
    result = dict(id=res.id,
                  ttl=rrset.ttl,
                  name=str(rrset.name),
                  mname=str(record.mname),
                  rname=str(record.rname),
                  serial=record.serial,
                  type=dns.rdatatype.to_text(rtype_obj))

    return result


def ns_parser(qname_obj, rtype_obj, res):

    rrset = res.get_rrset(res.answer, qname_obj, dns.rdataclass.IN, rtype_obj)

    if (rrset is None) or (len(rrset) == 0):
        return {}

    # todo: 正しく実装！

    return {}


class Measurer(framework.SetupwithInfluxdb):

    def __init__(self):
        super().__init__(__name__, __file__)
        self.__set_measurer_id()
        self.__set_global_ipaddress()
        self.__validate_id()
        self.__load_measurement_info()
        self.converter = MeasurementDataConverter(self.logger,
                                                  self.cnfg,
                                                  self.cnfs)

    def __set_measurer_id(self):
        hostname = socket.gethostname()
        self.measurer_id = "%s-%d" % (
            self.cnfs.measurement.region,
            binascii.crc32(hostname.encode("utf8")))

    def __set_global_ipaddress(self):
        canonical_addrs = []
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
                    canonical_addrs.append(addr_obj)

        canonical_addrs.sort(key=str)
        self.logger.info("global ip addresses found for: %s" %
                         (canonical_addrs))

        for each in canonical_addrs:
            if each.version == 4:
                selected_ipv4 = str(each)
                if selected_ipv6 is not None:
                    break
            elif each.version == 6:
                selected_ipv6 = str(each)
                if selected_ipv4 is not None:
                    break

        self.logger.info("selected ipv4 address: %s" % (selected_ipv4))
        self.logger.info("selected ipv6 address: %s" % (selected_ipv6))

        self.ipv4 = selected_ipv4
        self.ipv6 = selected_ipv6

    def __validate_id(self):
        if self.ipv4 is None or self.ipv6 is None:
            self.logger.critical("measurer must have global IPv4/IPv6 address")
            sys.exit(1)

    def __load_measurement_info(self):

        protocol = self.cnfs.controller.protocol
        host = self.cnfs.controller.host
        port = self.cnfs.controller.port
        user = self.cnfs.controller.user
        passwd = self.cnfs.controller.passwd
        path = self.cnfs.controller.path

        controller = "%s://%s:%s%s" % (protocol, host, port, path)
        self.logger.info("controller: %s" % (controller))

        try:
            response = requests.get(controller, auth=(user, passwd))
        except requests.RequestException as ex:
            self.logger.error("unexpected error occurred: %s" % (str(ex)))
            sys.exit(1)

        self.logger.info("http status code: %s" % (response.status_code))

        if response.status_code != 200:
            self.logger.error("status code is not 200: %s" %
                              (response.status_code))
            sys.exit(1)

        try:
            json_obj = json.loads(response.text)
            self.logger.info("json object load in properly from controller")
        except json.decoder.JSONDecodeError as ex:
            self.logger.error("undecodable object responsed: %s" % (str(ex)))
            sys.exit(1)

        self.logger.debug(json_obj)

        try:
            self.measurement_info = namedtupled.map(json_obj)
        except Exception:
            self.logger.error("unable to map json obj to namedtuple")
            sys.exit(1)

    def write_measurement_data(self, data):
        ret = False

        try:
            self.logger.info("writing data to influxdb")
            ret = self.session.write_points(data)
            if not ret:
                self.logger.warning("writing data to the influxdb failed")
                self.logger.debug("while writing followeing %s" % str(data))
        except Exception as ex:
            self.logger.warning("%s occurred while writing" % str(ex))
            self.logger.debug("while writing following %s" % str(data))
        finally:
            pass

        return ret

    def __measurement_core(self,
                           current_time,
                           nameserver,
                           queryer,
                           dst,
                           src,
                           af,
                           timeout,
                           proto,
                           qname,
                           rrtype,
                           qo):

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

        writable = self.converter.convert_influx_notation(current_time,
                                                          time_diff,
                                                          nameserver,
                                                          dst,
                                                          src,
                                                          self.measurer_id,
                                                          af,
                                                          proto,
                                                          qname,
                                                          rrtype,
                                                          (err, response))
        return writable

    def measure_toplevel(self):

        tcp_timeout = float(self.cnfs.measurement.tcp_timeout)
        udp_timeout = float(self.cnfs.measurement.udp_timeout)
        current_time = str(datetime.datetime.utcnow().isoformat()) + "Z"
        result = []

        queryer_info_by_protocol = {"udp": (dns.query.udp, udp_timeout),
                                    "tcp": (dns.query.tcp, tcp_timeout)}

        threadpool = ThreadPool(processes=1)
        async_results = []

        for measurement in self.measurement_info:

            nameserver = measurement.nameserver
            protocol = measurement.proto
            query = measurement.query
            dst = measurement.destination

            for addr in dst:

                addr_obj = ipaddress.ip_address(addr)

                if addr_obj.version == 4:
                    source = self.ipv4
                elif addr_obj.version == 6:
                    source = self.ipv6
                else:
                    self.logger.error("unknown version addr: %s" % str(addr))
                    sys.exit(1)

                queryer, timeout = queryer_info_by_protocol[protocol]

                qname = query.qname
                rrtype = query.rrtype

                try:
                    qname_obj = dns.name.from_text(qname)
                    rrtype_obj = dns.rdatatype.from_text(rrtype)
                    qo = dns.message.make_query(qname_obj, rrtype_obj)
                except dns.rdatatype.UnknownRdatatype:
                    self.logger.warning("unknown query: %s" % (rrtype))
                    self.logger.warning("measurement skipped")
                    continue

                async_results.append(
                    threadpool.apply_async(self.__measurement_core,
                                           (current_time,
                                            nameserver,
                                            queryer,
                                            addr,
                                            source,
                                            addr_obj.version,
                                            timeout,
                                            protocol,
                                            qname,
                                            rrtype,
                                            qo
                                            )))
        for each in async_results:
            result.append(each.get())

        self.logger.info("%s data measured" % (len(result)))
        self.logger.debug("following is massured data %s" % str(result))

        return result

    def run(self):
        result = self.measure_toplevel()
        ret = self.write_measurement_data(result)
        if not ret:
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":

    try:
        measurer = Measurer()
        measurer.converter.add_record_parser("jp", "SOA", soa_parser)
    except Exception:
        # LOGGERのセットアップ自体にも失敗している可能性ありの為
        # 標準出力にログ出力
        print(traceback.format_exc())
        sys.exit(1)

    measurer.start()
