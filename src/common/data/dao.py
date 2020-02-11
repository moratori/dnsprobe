#!/usr/bin/env python

import json
import time

from logging import getLogger
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base

import common.data.types as types

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

    def __make_multiple_or_condition(self, keyname, values):
        # keyname,values parameter MUST BE TRUSTED value
        condition = " or ".join(["%s = '%s'" % (keyname, value)
                                 for value in values])
        return condition

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

    # deprecated
    def __get_af_proto_combination_core(self, dns_server_name, probe_name):

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

    # deprecated
    def get_af_proto_combination(self, dns_server_name, probe_names):
        ret = []
        for probe_name in probe_names:
            ret.extend(self.__get_af_proto_combination_core(dns_server_name,
                                                            probe_name))
        return list(set(ret))

    def get_rttgraph_data(self, dns_server_name, probe_names, af, proto,
                          rrtype, start_time, end_time):

        proc_start = time.time()
        prb_id_condition = self.__make_multiple_or_condition("prb_id",
                                                             probe_names)

        ret = self.app.session.query(
            "select mean(time_took) as averaged_time_took from dnsprobe where \
             dst_name = $dst_name and \
             got_response = 'True' and \
             af = $af and \
             proto = $proto and \
             rrtype = $rrtype and \
             $start_time < time and \
             time < $end_time and \
             (%s) \
             group by time(1m)" % prb_id_condition,
            params=dict(params=json.dumps(
                dict(dst_name=dns_server_name,
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
                y.append(data["averaged_time_took"])

        return x, y

    def get_nsidgraph_data(self, dns_server_name, probe_names, rrtype,
                           start_time, end_time):

        proc_start = time.time()
        prb_id_condition = self.__make_multiple_or_condition("prb_id",
                                                             probe_names)

        ret = self.app.session.query(
            "select count(time_took) \
             from dnsprobe where \
             got_response = 'True' and \
             dst_name = $dst_name and \
             rrtype = $rrtype and \
             $start_time < time and \
             time < $end_time and\
             (%s) \
            group by nsid" % prb_id_condition,
            params=dict(params=json.dumps(
                dict(dst_name=dns_server_name,
                     rrtype=rrtype,
                     start_time=start_time,
                     end_time=end_time))))

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

        return ret

    def get_ratiograph_unanswered(self, dns_server_name, probe_names, af,
                                  proto, rrtype, start_time, end_time):

        proc_start = time.time()

        prb_id_condition = self.__make_multiple_or_condition("prb_id",
                                                             probe_names)

        unanswered = self.app.session.query(
            "select count(time_took) from dnsprobe where \
             got_response = 'False' and \
             dst_name = $dst_name and \
             af = $af and \
             proto = $proto and \
             rrtype = $rrtype and \
             $start_time < time and \
             time < $end_time and \
             (%s)" % prb_id_condition,
            params=dict(params=json.dumps(
                dict(dst_name=dns_server_name,
                     af=af,
                     proto=proto,
                     rrtype=rrtype,
                     start_time=start_time,
                     end_time=end_time))))

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

        return unanswered

    def get_ratiograph_answered(self, dns_server_name, probe_names, af, proto,
                                rrtype, start_time, end_time):

        proc_start = time.time()
        prb_id_condition = self.__make_multiple_or_condition("prb_id",
                                                             probe_names)

        answered = self.app.session.query(
            "select count(time_took) from dnsprobe where \
             got_response = 'True' and \
             dst_name = $dst_name and \
             af = $af and \
             proto = $proto and \
             rrtype = $rrtype and \
             $start_time < time and \
             time < $end_time and \
             (%s)" % prb_id_condition,
            params=dict(params=json.dumps(
                dict(dst_name=dns_server_name,
                     af=af,
                     proto=proto,
                     rrtype=rrtype,
                     start_time=start_time,
                     end_time=end_time))))

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

        return answered

    def get_percentilegraph_data(self, dns_server_name, probe_names, rrtype,
                                 start_time, end_time):

        default_step = 20
        xaxis_step = int(self.app.cnfs.graph.percentile_axis_step)

        if 100 % xaxis_step != 0:
            xaxis_step = default_step

        proc_start = time.time()
        result = {}
        prb_id_condition = self.__make_multiple_or_condition("prb_id",
                                                             probe_names)

        for each_step in range(0, 100+1, xaxis_step):

            percentile = self.app.session.query(
                "select percentile(time_took, $each_step) \
                 from dnsprobe \
                 where \
                 got_response = 'True' and \
                 time > $start_time and \
                 time < $end_time and \
                 dst_name = $dst_name and \
                 rrtype = $rrtype and \
                 (%s) \
                 group by af, proto" % (prb_id_condition),
                params=dict(params=json.dumps(
                    dict(each_step=each_step,
                         dst_name=dns_server_name,
                         rrtype=rrtype,
                         start_time=start_time,
                         end_time=end_time))))

            for (measurement_name, tags) in percentile.keys():
                record = list(percentile.get_points(
                    measurement=measurement_name,
                    tags=tags))

                if ("af" not in tags) or ("proto" not in tags) or \
                        (len(record) != 1) or ("percentile" not in record[0]):
                    LOGGER.warning(str(tags))
                    LOGGER.warning(str(record))
                    LOGGER.warning("unexpected influxdb scheme")
                    continue

                key = (tags["af"], tags["proto"])
                value = record[0]["percentile"]
                if key in result:
                    result[key][0].append(value)
                    result[key][1].append(each_step)
                else:
                    result[key] = ([value], [each_step])

        LOGGER.debug("time took: %s" % (time.time() - proc_start))

        return result

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
