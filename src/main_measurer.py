#!/usr/bin/env python3

"""
docstring is here
"""

import common.framework as framework

import requests
import traceback
import sys
import json
import socket
import binascii
import netifaces
import ipaddress
import datetime
import influxdb
import dns.name
import dns.message
import dns.query
import dns.rdatatype
import dns.exception


class Measurer(framework.Setup):

    def __init__(self):
        super().__init__(__name__, __file__)
        self.__set_measurer_id()
        self.__set_global_ipaddress()
# todo: 下行をコメントアウトを消す
#        self.__validate_id()
        self.__load_measurement_info()
        self.record_parser = {}

    def __set_measurer_id(self):
        hostname = socket.gethostname()
        self.measurer_id = binascii.crc32(hostname.encode("utf8"))

    def __set_global_ipaddress(self):
        canonical_addrs = []
        selected_ipv4 = None
        selected_ipv6 = None

        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)[netifaces.AF_INET]
            for addr in addrs:
                if "addr" not in addr:
                    continue
                addr_obj = ipaddress.ip_address(addr["addr"])
                if addr_obj.is_global:
                    canonical_addrs.append(addr_obj)

        canonical_addrs.sort(key=str)
        self.logger.info("global ip addresses found for: %s" %
                         (canonical_addrs))

        for each in canonical_addrs:
            if each.version == 4:
                selected_ipv4 = each
                break

        for each in canonical_addrs:
            if each.version == 6:
                selected_ipv6 = each
                break

        self.logger.info("selected ipv4 address: %s" % (selected_ipv4))
        self.logger.info("selected ipv6 address: %s" % (selected_ipv6))

        self.ipv4 = selected_ipv4
        self.ipv6 = selected_ipv6

        self.ipv4 = "10.0.2.15"

    def __validate_id(self):
        if self.ipv4 is None or self.ipv6 is None:
            self.logger.critical("measurer must have global IPv4/IPv6 address")
            sys.exit(1)

    def __load_measurement_info(self):

        protocol = self.cnfs.controller.protocol
        host = self.cnfs.controller.host
        port = self.cnfs.controller.port
        path = self.cnfs.controller.path

        controller = "%s://%s:%s%s" % (protocol, host, port, path)
        self.logger.info("controller: %s" % (controller))

        try:
            response = requests.get(controller)
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
            self.logger.info("json object load in properly")
        except json.decoder.JSONDecodeError as ex:
            self.logger.error("undecodable object responsed: %s" % (str(ex)))
            sys.exit(1)

        self.logger.debug(json_obj)
        self.measurement_info = json_obj

    def add_record_parser(self, qname, rtype, func):
        self.record_parser[(qname, rtype)] = func

    def parse_response_to_fields(self, qname, rtype, res):

        if not (qname, rtype) in self.record_parser:
            self.logger.warning("unable to find parser for %s %s" %
                                (qname, rtype))
            return {}

        qname_obj = dns.name.from_text(qname)
        rtype_obj = dns.rdatatype.from_text(rtype)

        return self.record_parser[(qname, rtype)](qname_obj, rtype_obj, res)

    def convert_influx_notation(self, current_time, nameserver, addr, af, proto, qname, rtype, res, err):
        conf = self.conf_script["data_store"]
        measurement_name = conf["database"]

        result = {"measurement": measurement_name,
                  "time":        current_time,
                  "tags": {
                      "af": af,
                      "dst_addr": addr,
                      "dst_name": nameserver,
                      "from": self.ipv4 if af == 4 else self.ipv6,
                      "msm_name": "Tdig",
                      "prb_id": self.measurer_id,
                      "proto": proto}}

        if err is None:
            result["fields"] = self.parse_response_to_fields(qname, rtype, res)
        else:
            result["fields"] = {"getaddrinfo": str(err)}

        return result

    def measure_toplevel(self):

        conf = self.conf_script["measurement"]
        tcp_timeout = float(conf["tcp_timeout"])
        udp_timeout = float(conf["udp_timeout"])
        current_time = str(datetime.datetime.utcnow().isoformat()) + "Z"
        result = []

        for measurement in self.measurement_info:
            v4_dst = measurement["destination"]["v4"]
            v6_dst = measurement["destination"]["v6"]
            queries = measurement["query"]
            nameserver = measurement["nameserver"]

# todo: implement multithread
            for addr in v4_dst:  # + v6_dst:
                addr_obj = ipaddress.ip_address(addr)
                source = self.ipv4 if addr_obj.version == 4 else self.ipv6
                for query in queries:
                    qname = query["qname"]
                    rtype = query["rtype"]
                    err_udp = res_udp = None
                    err_tcp = res_tcp = None

                    try:
                        qo = dns.message.make_query(
                            dns.name.from_text(qname),
                            dns.rdatatype.from_text(rtype))
                    except dns.rdatatype.UnknownRdatatype as ex:
                        self.logger.warning("unknown query type: %s skipped measurement" %(rtype))
                        continue

                    try:
                        res_udp = dns.query.udp(qo, str(addr_obj), timeout=udp_timeout, source=source)
                    except dns.exception.Timeout as ex:
                        self.logger.warning("timeout occurred while measurement: %s" %(ex))
                        err_udp = ex
                    except OSError as ex:
                        self.logger.warning("os error occurred while measurement: %s" %(ex))
                        err_udp = ex

                    try:
                        res_tcp = dns.query.tcp(qo, str(addr_obj), timeout=tcp_timeout, source=source)
                    except dns.exception.Timeout as ex:
                        err_tcp = ex
                        self.logger.warning("timeout occurred while measurement: %s" %(ex))
                    except OSError as ex:
                        err_tcp = ex
                        self.logger.warning("os error occurred while measurement: %s" %(ex))

                    result.append(
                        self.convert_influx_notation(
                            current_time, nameserver, str(addr_obj), addr_obj.version, "udp", qname, rtype, res_udp, err_udp))
                    result.append(
                        self.convert_influx_notation(
                            current_time, nameserver, str(addr_obj), addr_obj.version, "tcp", qname, rtype, res_tcp, err_tcp))

        self.logger.info("%s data measured" % (len(result)))
        return result

    def write_measurement_data(self, data):
        conf = self.conf_script["data_store"]
        host = conf["host"]
        port = conf["port"]
        user = conf["user"]
        passwd = conf["passwd"]
        database = conf["database"]

        client = influxdb.InfluxDBClient(host, int(port), user, passwd, database)

        ret = False

        try:
            ret = client.write_points(data)
            if not ret:
                self.logger.warning("writing measurement data to the influxdb seems to have failed")
                self.logger.debug("while writing followeing data %s" %(data))
        except Exception as ex:
            self.logger.warning("exception %s occurred while writing measurement data to influxdb" %(ex))
            self.logger.debug("exception occurred while writing followeing data %s" %(data))
        finally:
            client.close()

        return ret

    def run(self):
        try:
            result = self.measure_toplevel()
            ret = self.write_measurement_data(result)
            if not ret:
                sys.exit(1)
        except Exception as ex:
            self.logger.error("unexpected exception <%s> occurred" %(str(ex)))
            self.logger.error(traceback.format_exc())
            sys.exit(1)

        sys.exit(0)


def soa_parser(qname_obj, rtype_obj, res):

    result = {}
    rrset = res.get_rrset(res.answer, qname_obj, dns.rdataclass.IN, rtype_obj)

    if (rrset is None) or (len(rrset) == 0):
        self.logger.warning("unable to get RRset: qname=%s, rtype=%s, response=%s" %(qname, rtype, res))
        return result

    record = rrset[0]

    result["id"] = res.id
    result["rt"] = res.time
    result["ttl"] = rrset.ttl
    result["name"] = str(rrset.name)
    result["mname"] = str(record.mname)
    result["rname"] = str(record.rname)
    result["serial"] = record.serial
    result["type"] = dns.rdatatype.to_text(rtype_obj)

    return result


if __name__ == "__main__":

    try:
        measurer = Measurer()
        measurer.add_record_parser("jp", "SOA", soa_parser)
    except Exception:
        # LOGGERのセットアップ自体にも失敗している可能性ありの為
        # 標準出力にログ出力
        print(traceback.format_exc())
        sys.exit(1)

    measurer.run()

