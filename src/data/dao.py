#!/usr/bin/env python

import data.types as types
import json

from logging import getLogger
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base

LOGGER = getLogger(__name__)
Base = declarative_base()


class MeasurementTarget(Base):

    __tablename__ = "measurement_target"

    target_id = Column("target_id",
                       Integer, primary_key=True, autoincrement=True)

    hostname = Column("hostname",
                      String(253), nullable=False)

    address_family = Column(Enum(types.AddressFamily),
                            index=True)

    transport_protocol = Column(Enum(types.TransportProtocol),
                                index=True)

    qname = Column("qname", String(253),
                   nullable=False)

    rrtype = Column("rrtype", String(8),
                    nullable=False)


# PythonからInfluxdbを使うORMがなさそうなので、以下寄せ集め...
class Dnsprobe:

    def __init__(self, app):
        # app is subclass of `SetupwithInfluxdb`
        self.app = app

    def __show_tag_list(self, tag):
        # tag parameter MUST BE TRUSTED value
        # unable to use `bind-parameter` for `with key` statement
        ret = self.app.session.query("show tag values with key = %s" %
                                     (tag))
        result = []
        for each in ret:
            for record in each:
                result.append(record["value"])
        return result

    def make_authoritative_group(self):
        ret = self.__show_tag_list("dst_name")
        result = [dict(label=each, value=each) for each in ret]
        return result

    def make_probe_group(self):
        ret = self.__show_tag_list("prb_id")
        result = [dict(label=each, value=each) for each in ret]
        return result

    def make_probe_locations(self):
        probe_list = self.__show_tag_list("prb_id")
        lats = []
        lons = []
        for prb_id in probe_list:
            ret = self.app.session.query(
                "show tag values with key in \
                (prb_lat, prb_lon) where prb_id = $prb_id",
                params=dict(params=json.dumps(dict(prb_id=prb_id))))

            for each in ret:
                for record in each:
                    key = record["key"]
                    value = record["value"]
                    if key == "prb_lat":
                        lats.append(value)
                    if key == "prb_lon":
                        lons.append(value)

        return probe_list, lats, lons

    def get_af_proto_combination(self, dns_server_name, probe_name):

        ret_af = self.app.session.query(
            "show tag values with key = af where \
             dst_name = $dst_name and prb_id = $prb_id",
            params=dict(params=json.dumps(dict(dst_name=dns_server_name,
                                               prb_id=probe_name))))

        ret_proto = self.app.session.query(
            "show tag values with key = proto where \
             dst_name = $dst_name and prb_id = $prb_id",
            params=dict(params=json.dumps(dict(dst_name=dns_server_name,
                                               prb_id=probe_name))))

        result = []

        for afs in ret_af:
            for af in afs:
                af_value = af["value"]
                for prots in ret_proto:
                    for proto in prots:
                        proto_value = proto["value"]
                        result.append((af_value, proto_value))

        return result
