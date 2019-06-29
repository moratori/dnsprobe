#!/usr/bin/env python3

"""
docstring is here
"""

import os
import common.config as config
import json
import datetime
import plotly.graph_objs as go
import html as snt
from dash.dependencies import Input, Output
from flask import abort, Response
from logging import getLogger

LOGGER = getLogger(__name__)


class RTTViewerLogic():

    def __init__(self, rttviewer):
        self.rttviewer = rttviewer

    def __convert_range_index_to_time(self, time_range):

        upper = 24
        seconds_for_hour = 3600
        current_time = datetime.datetime.utcnow()
        start_index, end_index = time_range

        start_time = current_time - datetime.timedelta(
            seconds=(upper - start_index) * seconds_for_hour)
        end_time = current_time - datetime.timedelta(
            seconds=(upper - end_index) * seconds_for_hour)

        return start_time.isoformat() + "Z", end_time.isoformat() + "Z"

    def setup_logic(self):

        @self.rttviewer.application.server.route(os.path.join(
            "/",
            os.path.basename(config.STATIC_DIR),
            self.rttviewer.cnfs.resource.css_dir,
            '<regex("[a-zA-Z0-9]+\\.css"):stylesheet>'))
        def serve_css(stylesheet):

            LOGGER.info("requested css file \"%s\"" % str(stylesheet))

            try:
                with open(os.path.join(config.STATIC_DIR,
                                       self.rttviewer.cnfs.resource.css_dir,
                                       stylesheet), "r") as handle:
                    return Response(handle.read(), mimetype="text/css")

            except Exception:
                LOGGER.warning("exception while loading css \"%s\"" %
                               str(stylesheet))
                abort(404)

        @self.rttviewer.application.callback(
            Output("main-content-tograph-figure", "figure"),
            [Input("main-content-menu-filter_measurement_time", "value"),
             Input("main-content-menu-filter_authoritatives", "value"),
             Input("main-content-menu-filter_probe", "value"),
             Input("main-content-graph-interval", "n_intervals")])
        def update_tograph(time_range, dns_server_name, probe_name, cnt):

            if (time_range is None) or \
                    (dns_server_name is None) or \
                    (probe_name is None) or \
                    not time_range:
                LOGGER.warning("lack of argument for update_tograph")
                return dict()

            title = "Number of error queries(e.g. timeout, no route to host)"
            start_time, end_time = \
                self.__convert_range_index_to_time(time_range)

            af_proto_combination = \
                self.rttviewer.dao_dnsprobe.get_af_proto_combination(
                    dns_server_name, probe_name)

            LOGGER.debug("time range %s to %s" % (start_time, end_time))
            LOGGER.debug("af proto combination: %s" %
                         (af_proto_combination))

            xdata = []
            ydata = []
            for (af, proto) in af_proto_combination:

                ret = self.rttviewer.session.query(
                    "select count(time_took) from dnsprobe where \
                     got_response = 'False' and \
                     dst_name = $dst_name and \
                     prb_id = $prb_id and \
                     af = $af and \
                     proto = $proto and \
                     $start_time < time and \
                     time < $end_time",
                    params=dict(params=json.dumps(
                        dict(dst_name=dns_server_name,
                             prb_id=probe_name,
                             af=af,
                             proto=proto,
                             start_time=start_time,
                             end_time=end_time))))

                # influxdb のカウント(count)に纏わる仕様の補正の為に
                # デフォルトで0を表示するようにする
                # 上記クエリで所望の条件でカウントした際に、該当するレコードがない場合は
                # 0件として扱ってほしい
                # af_proto_combinationに入っているペアは、測定が実行されたことを示しているため
                timeouted_count = 0
                for records in ret:
                    for data in records:
                        timeouted_count = data["count"]
                xdata.append(snt.escape("%s over IPv%s" % (proto, af)))
                ydata.append(timeouted_count)

            figure = dict(data=[go.Bar(x=xdata, y=ydata)],
                          layout=go.Layout(
                              title=title,
                              xaxis=dict(title="Measurement Target"),
                              yaxis=dict(title="Number of error queries",
                                         autorange=True,
                                         rangemode="tozero")))

            return figure

        @self.rttviewer.application.callback(
            Output("main-content-rttgraph-figure", "figure"),
            [Input("main-content-menu-filter_measurement_time", "value"),
             Input("main-content-menu-filter_authoritatives", "value"),
             Input("main-content-menu-filter_probe", "value"),
             Input("main-content-graph-interval", "n_intervals")])
        def update_rttgraph(time_range, dns_server_name, probe_name, cnt):

            if (time_range is None) or \
                    (dns_server_name is None) or \
                    (probe_name is None) or \
                    not time_range:
                LOGGER.warning("lack of argument for update_rttgraph")
                return dict()

            title = """RTT Transition(only successful queries)"""

            start_time, end_time = \
                self.__convert_range_index_to_time(time_range)

            af_proto_combination = \
                self.rttviewer.dao_dnsprobe.get_af_proto_combination(
                    dns_server_name, probe_name)

            LOGGER.debug("time range %s to %s" % (start_time, end_time))
            LOGGER.debug("af proto combination: %s" %
                         (af_proto_combination))

            traces = []
            for (af, proto) in af_proto_combination:

                ret = self.rttviewer.session.query(
                    "select time,time_took from dnsprobe where \
                     dst_name = $dst_name and \
                     prb_id = $prb_id and \
                     got_response = 'True' and \
                     af = $af and \
                     proto = $proto and \
                     $start_time < time and \
                     time < $end_time",
                    params=dict(params=json.dumps(
                        dict(dst_name=dns_server_name,
                             prb_id=probe_name,
                             af=af,
                             proto=proto,
                             start_time=start_time,
                             end_time=end_time))))

                x = []
                y = []
                for records in ret:
                    for data in records:
                        x.append(data["time"])
                        y.append(data["time_took"])

                if not (x and y):
                    continue

                traces.append(go.Scatter(mode="lines",
                                         x=x,
                                         y=y,
                                         name=snt.escape("%s over IPv%s" %
                                                         (proto, af))))

            figure = dict(data=traces,
                          layout=go.Layout(
                              title=title,
                              showlegend=True,
                              xaxis=dict(title="UTC Time",
                                         autorange=True,
                                         rangemode="tozero"),
                              yaxis=dict(title="Round Trip Time(msec)",
                                         autorange=True,
                                         rangemode="tozero"),
                              legend=dict(orientation="h",
                                          font=dict(size=9),
                                          yanchor="top",
                                          x=0,
                                          y=1.1)))

            return figure
