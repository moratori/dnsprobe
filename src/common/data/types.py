#!/usr/bin/env python

import enum
import json
import base64
import gzip
import dns.name
import dns.message
import dns.query
import dns.rdatatype
import dns.exception

from logging import getLogger

LOGGER = getLogger(__name__)


class TransportProtocol(enum.Enum):

    TCP = enum.auto()
    UDP = enum.auto()

    def __str__(self):
        return "%s" % (self.name.lower())


class AddressFamily(enum.Enum):

    V4 = enum.auto()
    V6 = enum.auto()

    def __str__(self):
        return "%s" % (self.name.lower())


class SupportedRRType(enum.IntEnum):

    SOA = dns.rdatatype.from_text("SOA")
    NS = dns.rdatatype.from_text("NS")
    DNSKEY = dns.rdatatype.from_text("DNSKEY")

    def __str__(self):
        return "%s" % (self.name.lower())


class InfluxDBPoints():

    """
    InfluxDBに書き込むデータを保持するクラス
    """


class CalculatedSLA(InfluxDBPoints):

    """
    サービスレベルの計算結果を保持するクラス
    """

    def __init__(self, end_time, start_time, dst_name, af, sla):
        self.end_time = end_time
        self.start_time = start_time
        self.dst_name = dst_name
        self.af = af
        self.sla = sla

    def convert_influx_notation(self, measurement_name):

        result = dict(measurement=measurement_name,
                      time=self.end_time,
                      tags=dict(af=self.af,
                                dst_name=self.dst_name),
                      fields=dict(sla=self.sla,
                                  start_time=self.start_time))

        return result


class DNS_name_server_availability(CalculatedSLA):

    def __init__(self, *positional, **kw):
        super().__init__(*positional, **kw)


class DNSMeasurementData(InfluxDBPoints):

    """
    測定結果を保持するクラス
    """

    def __init__(self,
                 current_time,
                 time_diff,
                 nameserver,
                 dst,
                 src,
                 prb_id,
                 prb_asn,
                 prb_asn_desc,
                 server_boottime,
                 latitude,
                 longitude,
                 af,
                 proto,
                 qname,
                 rrtype,
                 err,
                 response,
                 rdata_storing):

        self.current_time = current_time
        self.time_diff = time_diff
        self.nameserver = nameserver
        self.dst = dst
        self.src = src
        self.prb_id = prb_id
        self.prb_asn = prb_asn
        self.prb_asn_desc = prb_asn_desc
        self.server_boottime = server_boottime
        self.latitude = latitude
        self.longitude = longitude
        self.af = af
        self.proto = proto
        self.qname = qname
        self.rrtype = rrtype
        self.err = err
        self.response = response
        self.rdata_storing = rdata_storing

    def __parse_response_to_fields(self, qname, rtype, res):

        try:
            qname_obj = dns.name.from_text(qname)
            rtype_obj = dns.rdatatype.from_text(rtype)
            parsed = self.parser(qname_obj, rtype_obj, res)
            return parsed
        except Exception as ex:
            LOGGER.warning("unexpected error %s occurred while parsing" %
                           (str(ex)))

            LOGGER.warning("unable to parse %s %s with parser" %
                           (qname, rtype))
            return {}

    def rdata_encode(self, python_obj):
        try:
            json_string = json.dumps(python_obj)
            LOGGER.debug("rdata json string: %s" % str(json_string))
            b64_bytes = base64.b64encode(
                gzip.compress(json_string.encode("utf8")))
            return b64_bytes.decode("utf8")
        except Exception as ex:
            LOGGER.warning("unexpected error while converting \
                           python object to base64: %s" % str(ex))
            return ""

    def parser(self, qname_obj, rtype_obj, res):
        return {}

    def convert_influx_notation(self, measurement_name):

        nsid = ""

        if self.err:
            field_data = dict(reason=str(self.err))
            error_class_name = self.err.__class__.__name__
        else:
            field_data = self.__parse_response_to_fields(self.qname,
                                                         self.rrtype,
                                                         self.response)
            error_class_name = ""

            for opt in self.response.options:
                if opt.otype == dns.edns.NSID:
                    nsid = opt.data.decode("utf8")
                    break

        if not nsid:
            nsid = "unknown"

        got_response = self.err is None

        field_data.update(dict(time_took=self.time_diff,
                               # following field is needed by SLA calculation
                               got_response_field=(1 if got_response else 0),
                               probe_uptime=self.server_boottime,
                               probe_asn=self.prb_asn,
                               probe_asn_desc=self.prb_asn_desc))

        result = dict(measurement=measurement_name,
                      time=self.current_time,
                      tags=dict(af=self.af,
                                dst_addr=self.dst,
                                dst_name=self.nameserver,
                                nsid=nsid,
                                src_addr=self.src,
                                prb_id=self.prb_id,
                                prb_lat=self.latitude,
                                prb_lon=self.longitude,
                                proto=self.proto,
                                rrtype=self.rrtype,
                                qname=self.qname,
                                got_response=got_response,
                                error_class_name=error_class_name),
                      fields=field_data)

        LOGGER.debug("result: %s" % (result))

        return result


class SOA_DNSMeasurementData(DNSMeasurementData):

    def __init__(self, *positional, **kw):
        super().__init__(*positional, **kw)

    def parser(self, qname_obj, rtype_obj, res):

        rrset = res.get_rrset(res.answer,
                              qname_obj,
                              dns.rdataclass.IN,
                              rtype_obj)

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


class NS_DNSMeasurementData(DNSMeasurementData):

    def __init__(self, *positional, **kw):
        super().__init__(*positional, **kw)

    def parser(self, qname_obj, rtype_obj, res):

        rrset = res.get_rrset(res.answer,
                              qname_obj,
                              dns.rdataclass.IN,
                              rtype_obj)

        if (rrset is None) or (len(rrset) == 0):
            return {}

        data = sorted([record.target.to_text()
                       for record in rrset])

        result = dict(id=res.id,
                      ttl=rrset.ttl,
                      name=str(rrset.name),
                      data=self.rdata_encode(data),
                      type=dns.rdatatype.to_text(rtype_obj))

        return result


class DNSKEY_DNSMeasurementData(DNSMeasurementData):

    def __init__(self, *positional, **kw):
        super().__init__(*positional, **kw)

    def parser(self, qname_obj, rtype_obj, res):

        rrset = res.get_rrset(res.answer,
                              qname_obj,
                              dns.rdataclass.IN,
                              rtype_obj)

        if (rrset is None) or (len(rrset) == 0):
            return {}

        data = []
        for record in rrset:
            base = dict(flags=record.flags,
                        algorithm=record.algorithm)
            if self.rdata_storing.save_dnskey:
                base.update(dict(
                    key=base64.b64encode(record.key).decode("utf8")))
            data.append(base)

        data = sorted(data, key=((lambda x: x["key"])
                                 if self.rdata_storing.save_dnskey
                                 else (lambda x: x["flags"])))

        result = dict(id=res.id,
                      ttl=rrset.ttl,
                      name=str(rrset.name),
                      data=self.rdata_encode(data),
                      type=dns.rdatatype.to_text(rtype_obj))

        return result


def make_DNSMeasurementData(current_time,
                            time_diff,
                            nameserver,
                            dst,
                            src,
                            measurer_id,
                            asn,
                            asn_desc,
                            server_boottime,
                            latitude,
                            longitude,
                            af,
                            proto,
                            qname,
                            rrtype,
                            err,
                            response,
                            rdata_storing):

    constractors = {SupportedRRType.SOA: SOA_DNSMeasurementData,
                    SupportedRRType.NS: NS_DNSMeasurementData,
                    SupportedRRType.DNSKEY: DNSKEY_DNSMeasurementData}

    args = (current_time,
            time_diff,
            nameserver,
            dst,
            src,
            measurer_id,
            asn,
            asn_desc,
            server_boottime,
            latitude,
            longitude,
            af,
            proto,
            qname,
            rrtype,
            err,
            response,
            rdata_storing)

    rrtype_obj = dns.rdatatype.from_text(rrtype)

    default = DNSMeasurementData(*args)
    try:
        target = SupportedRRType(rrtype_obj)
        for supported in SupportedRRType:
            if supported == target:
                LOGGER.debug("parser class found for %s" % (str(rrtype)))
                return constractors[target](*args)
    except ValueError:
        LOGGER.warning("unsupported RR type for parsing: %s" % (rrtype))
    LOGGER.debug("parser class NOT found for %s" % (str(rrtype)))
    return default
