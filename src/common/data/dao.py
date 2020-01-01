#!/usr/bin/env python

import common.data.types as types

import json
import time

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
        proc_start = time.time()

        ret = self.app.session.query("show tag values with key = %s" %
                                     (tag))

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

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

    def make_rrtype_group(self):
        ret = self.__show_tag_list("rrtype")
        result = [dict(label=each, value=each) for each in ret]
        return result

    def make_probe_locations(self):
        probe_list = self.__show_tag_list("prb_id")
        lats = []
        lons = []
        for prb_id in probe_list:

            proc_start = time.time()

            ret = self.app.session.query(
                "show tag values with key in \
                (prb_lat, prb_lon) where prb_id = $prb_id",
                params=dict(params=json.dumps(dict(prb_id=prb_id))))

            LOGGER.debug("time took: %s" % (time.time() - proc_start))

            for each in ret:
                for record in each:
                    key = record["key"]
                    value = record["value"]
                    if key == "prb_lat":
                        lats.append(value)
                    if key == "prb_lon":
                        lons.append(value)

        return probe_list, lats, lons

    def get_probe_last_measured(self, probe_id):

        lasttime_value = "unknown"

        # performance issue #45
        return lasttime_value

        proc_start = time.time()

        ret_uptime = self.app.session.query(
                    "select time, time_took from dnsprobe where \
                     prb_id = $prb_id \
                     order by time desc \
                     limit 1",
                    params=dict(params=json.dumps(
                        dict(prb_id=probe_id))))

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

        for uptimes in ret_uptime:
            for uptime in uptimes:
                lasttime_value = uptime["time"]

        return str(lasttime_value)

    def get_probe_uptime(self, probe_id):

        uptime_value = "unknown"

        # performance issue #45
        return uptime_value

        proc_start = time.time()

        ret_uptime = self.app.session.query(
                    "select probe_uptime from dnsprobe where \
                     prb_id = $prb_id \
                     order by time desc \
                     limit 1",
                    params=dict(params=json.dumps(
                        dict(prb_id=probe_id))))

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

        for uptimes in ret_uptime:
            for uptime in uptimes:
                uptime_value = uptime["probe_uptime"]

        return str(uptime_value)

    def get_probe_net_desc(self, probe_id):

        v4_asn = "unknown"
        v4_desc = "unknown"
        v6_asn = "unknown"
        v6_desc = "unknown"

        # performance issue #45
        return v4_asn, v4_desc, v6_asn, v6_desc

        proc_start = time.time()

        ret_desc = self.app.session.query(
            "select probe_asn, probe_asn_desc \
             from dnsprobe  \
             where prb_id = $prb_id \
             group by af \
             order by time desc \
             limit 1",
            params=dict(params=json.dumps(
                dict(prb_id=probe_id))))

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

        try:
            LOGGER.debug("ip description object: %s" % (str(ret_desc)))
            measurement = (self.__class__.__name__).lower()
            v4 = list(ret_desc.get_points(measurement=measurement,
                                          tags=dict(af="4")))
            v6 = list(ret_desc.get_points(measurement=measurement,
                                          tags=dict(af="6")))
            v4_asn = v4[0]["probe_asn"]
            v4_desc = v4[0]["probe_asn_desc"]
            v6_asn = v6[0]["probe_asn"]
            v6_desc = v6[0]["probe_asn_desc"]
        except Exception as ex:
            LOGGER.warning("unable to get IP description: %s" % (str(ex)))

        return v4_asn, v4_desc, v6_asn, v6_desc

    def get_af_proto_combination(self, dns_server_name, probe_name):

        proc_start = time.time()

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

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

        result = []

        for afs in ret_af:
            for af in afs:
                af_value = af["value"]
                for prots in ret_proto:
                    for proto in prots:
                        proto_value = proto["value"]
                        result.append((af_value, proto_value))

        return result

    def get_rttgraph_data(self, dns_server_name, probe_name, af, proto, rrtype,
                          start_time, end_time):

        proc_start = time.time()

        ret = self.app.session.query(
            "select time,time_took from dnsprobe where \
             dst_name = $dst_name and \
             prb_id = $prb_id and \
             got_response = 'True' and \
             af = $af and \
             proto = $proto and \
             rrtype = $rrtype and \
             $start_time < time and \
             time < $end_time",
            params=dict(params=json.dumps(
                dict(dst_name=dns_server_name,
                     prb_id=probe_name,
                     af=af,
                     proto=proto,
                     rrtype=rrtype,
                     start_time=start_time,
                     end_time=end_time))))

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

        x = []
        y = []
        for records in ret:
            for data in records:
                x.append(data["time"])
                y.append(data["time_took"])

        return x, y

    def get_nsidgraph_data(self, dns_server_name, probe_name, rrtype,
                           start_time, end_time):

        proc_start = time.time()

        ret = self.app.session.query(
            "select count(time_took) \
             from dnsprobe where \
             got_response = 'True' and \
             dst_name = $dst_name and \
             prb_id = $prb_id and \
             rrtype = $rrtype and \
             $start_time < time and \
             time < $end_time \
            group by nsid",
            params=dict(params=json.dumps(
                dict(dst_name=dns_server_name,
                     prb_id=probe_name,
                     rrtype=rrtype,
                     start_time=start_time,
                     end_time=end_time))))

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

        return ret

    def get_ratiograph_unanswered(self, dns_server_name, probe_name, af, proto,
                                  rrtype, start_time, end_time):

        proc_start = time.time()

        unanswered = self.app.session.query(
            "select count(time_took) from dnsprobe where \
             got_response = 'False' and \
             dst_name = $dst_name and \
             prb_id = $prb_id and \
             af = $af and \
             proto = $proto and \
             rrtype = $rrtype and \
             $start_time < time and \
             time < $end_time",
            params=dict(params=json.dumps(
                dict(dst_name=dns_server_name,
                     prb_id=probe_name,
                     af=af,
                     proto=proto,
                     rrtype=rrtype,
                     start_time=start_time,
                     end_time=end_time))))

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

        return unanswered

    def get_ratiograph_answered(self, dns_server_name, probe_name, af, proto,
                                rrtype, start_time, end_time):

        proc_start = time.time()

        answered = self.app.session.query(
            "select count(time_took) from dnsprobe where \
             got_response = 'True' and \
             dst_name = $dst_name and \
             prb_id = $prb_id and \
             af = $af and \
             proto = $proto and \
             rrtype = $rrtype and \
             $start_time < time and \
             time < $end_time",
            params=dict(params=json.dumps(
                dict(dst_name=dns_server_name,
                     prb_id=probe_name,
                     af=af,
                     proto=proto,
                     rrtype=rrtype,
                     start_time=start_time,
                     end_time=end_time))))

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

        return answered

    def write_measurement_data(self, measured_data):
        ret = False

        measurement_name = self.app.cnfg.data_store.database

        try:
            points = [each.convert_influx_notation(measurement_name)
                      for each in measured_data]
            LOGGER.info("writing data to influxdb")
            ret = self.app.session.write_points(points)
            if not ret:
                LOGGER.warning("writing data to the influxdb failed")
                LOGGER.debug("while writing followeing %s" % str(points))
        except Exception as ex:
            LOGGER.warning("%s occurred while writing" % str(ex))
            LOGGER.debug("while writing following %s" % str(points))
        finally:
            pass

        return ret
