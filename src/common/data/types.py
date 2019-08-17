#!/usr/bin/env python

import enum
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


class DNSMeasurementData():

    def __init__(self,
                 current_time,
                 time_diff,
                 nameserver,
                 dst,
                 src,
                 prb_id,
                 server_boottime,
                 latitude,
                 longitude,
                 af,
                 proto,
                 qname,
                 rrtype,
                 err,
                 response):

        self.current_time = current_time
        self.time_diff = time_diff
        self.nameserver = nameserver
        self.dst = dst
        self.src = src
        self.prb_id = prb_id
        self.server_boottime = server_boottime
        self.latitude = latitude
        self.longitude = longitude
        self.af = af
        self.proto = proto
        self.qname = qname
        self.rrtype = rrtype
        self.err = err
        self.response = response

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

    def parser(self, qname_obj, rtype_obj, res):
        pass

    def convert_influx_notation(self, measurement_name):

        if self.err:
            field_data = dict(reason=str(self.err))
            error_class_name = self.err.__class__.__name__
        else:
            field_data = self.__parse_response_to_fields(self.qname,
                                                         self.rrtype,
                                                         self.response)
            error_class_name = ""

        field_data.update(dict(time_took=self.time_diff,
                               probe_uptime=self.server_boottime))

        result = dict(measurement=measurement_name,
                      time=self.current_time,
                      tags=dict(af=self.af,
                                dst_addr=self.dst,
                                dst_name=self.nameserver,
                                src_addr=self.src,
                                prb_id=self.prb_id,
                                prb_lat=self.latitude,
                                prb_lon=self.longitude,
                                proto=self.proto,
                                rrtype=self.rrtype,
                                qname=self.qname,
                                got_response=self.err is None,
                                error_class_name=error_class_name),
                      fields=field_data)

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
