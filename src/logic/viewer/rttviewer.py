#!/usr/bin/env python3

"""
docstring is here
"""

import common.common.config as config
import plotly.graph_objs as go
import html as snt

import os
import json
import datetime
import math

import dash_html_components as html
import dash_core_components as doc
from dash.dependencies import Input, Output
from flask import abort, Response
from logging import getLogger
from werkzeug.routing import BaseConverter


LOGGER = getLogger(__name__)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


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
            Output("main-content-graph", "children"),
            [Input("main-content-menu-filter_measurement_time", "value"),
             Input("main-content-menu-filter_authoritatives", "value"),
             Input("main-content-menu-filter_probe", "value"),
             Input("main-content-graph-interval", "n_intervals")])
        def update_graph(time_range, dns_server_names, probe_name, cnt):

            result = [doc.Interval(id="main-content-graph-interval",
                                   interval=30 * 1000,
                                   n_intervals=0)]

            for dns_server_name in reversed(dns_server_names):
                result.append(html.Div([
                    html.Div([
                        doc.Graph(figure=__update_rttgraph(time_range,
                                                           dns_server_name,
                                                           probe_name),
                                  style=dict(height=600),
                                  config=dict(displayModeBar=False))],
                             style=dict(display="inline-block",
                                        width="50%")),
                    html.Div([
                        doc.Graph(figure=__update_ratiograph(time_range,
                                                             dns_server_name,
                                                             probe_name),
                                  style=dict(height=600),
                                  config=dict(displayModeBar=False))],
                             style=dict(display="inline-block",
                                        width="50%"))]))

            return result

        def __update_ratiograph(time_range, dns_server_name, probe_name):

            if (time_range is None) or \
                    (dns_server_name is None) or \
                    (probe_name is None) or \
                    not time_range:
                LOGGER.warning("lack of argument for update_ratiograph")
                return dict()

            start_time, end_time = \
                self.__convert_range_index_to_time(time_range)

            af_proto_combination = \
                self.rttviewer.dao_dnsprobe.get_af_proto_combination(
                    dns_server_name, probe_name)

            LOGGER.debug("time range %s to %s" % (start_time, end_time))
            LOGGER.debug("af proto combination: %s" %
                         (af_proto_combination))

            title = "Answered Ratio<br />%s from %s" % (dns_server_name,
                                                        probe_name)
            labels = ["Unanswered", "Answered"]
            donut_size = 0.3
            hoverinfo = "label+percent+name"
            row_tiling_num = 2

            num_of_graphs = len(af_proto_combination)
            rows = int(math.ceil(num_of_graphs / row_tiling_num))
            columns = int(num_of_graphs if row_tiling_num >= num_of_graphs
                          else row_tiling_num)

            traces = []
            for (n, (af, proto)) in enumerate(af_proto_combination):
                r = int(n / row_tiling_num)
                c = int(n % row_tiling_num)

                unanswered = self.rttviewer.session.query(
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

                answered = self.rttviewer.session.query(
                    "select count(time_took) from dnsprobe where \
                     got_response = 'True' and \
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

                unanswered_count = 0
                for records in unanswered:
                    for data in records:
                        unanswered_count = data["count"]
                answered_count = 0
                for records in answered:
                    for data in records:
                        answered_count = data["count"]

                if (unanswered_count + answered_count) == 0:
                    continue

                traces.append(go.Pie(values=[unanswered_count, answered_count],
                                     labels=labels,
                                     domain=dict(row=r, column=c),
                                     name=snt.escape("%s IPv%s" %
                                                     (proto.upper(), af)),
                                     hoverinfo=hoverinfo,
                                     hole=donut_size,
                                     marker=dict(colors=["red", "green"])))

            figure = dict(data=traces,
                          layout=dict(title=title,
                                      grid=dict(rows=rows,
                                                columns=columns)))

            return figure

        def __update_rttgraph(time_range, dns_server_name, probe_name):

            if (time_range is None) or \
                    (dns_server_name is None) or \
                    (probe_name is None) or \
                    not time_range:
                LOGGER.warning("lack of argument for update_rttgraph")
                return dict()

            LOGGER.debug("time range: %s" % time_range)
            LOGGER.debug("dns server name: %s" % dns_server_name)
            LOGGER.debug("probe name: %s" % probe_name)

            if not dns_server_name:
                return dict()

            title = "RTT Performance<br />%s from %s" % (dns_server_name,
                                                         probe_name)

            start_time, end_time = \
                self.__convert_range_index_to_time(time_range)

            af_proto_combination = \
                self.rttviewer.dao_dnsprobe.get_af_proto_combination(
                    dns_server_name, probe_name)

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
                                                         (proto.upper(), af))))

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

        @self.rttviewer.application.callback(
            Output("main-content-map-figure", "figure"),
            [Input("main-content-menu-filter_probe", "value"),
             Input("main-content-graph-interval", "n_intervals")])
        def update_map(probe_name, cnt):

            map_height = 850
            map_scale = 1
            map_center_lat = 25
            map_center_lon = 90
            map_region = "asia"
            map_title = "Location of Probes"
            map_land_color = "rgb(235, 235, 235)"
            map_resolution = 50
            map_proj_type = "equirectangular"
            color_map = {True: "orange", False: "grey"}
            size_map = {True: 14, False: 13}
            hovertext = "probe: %s<br />last measured at: %s<br />uptime: %s"

            probe_location_name, latitudes, longitudes = \
                self.rttviewer.dao_dnsprobe.make_probe_locations()

            data = []
            for (locname, lat, lon) in zip(probe_location_name,
                                           latitudes,
                                           longitudes):

                color = color_map[probe_name == locname]
                size = size_map[probe_name == locname]

                last_measured = \
                    self.rttviewer.dao_dnsprobe.get_probe_last_measured(
                        locname)
                uptime = \
                    self.rttviewer.dao_dnsprobe.get_probe_uptime(
                        locname)

                data.append(go.Scattergeo(lon=[lon],
                                          lat=[lat],
                                          text=locname,
                                          name=locname,
                                          hovertext=hovertext % (locname,
                                                                 last_measured,
                                                                 uptime),
                                          mode="markers",
                                          showlegend=False,
                                          marker=dict(size=size,
                                                      symbol="circle",
                                                      color=color)))

            layout = go.Layout(title=map_title,
                               height=map_height,
                               geo=dict(lonaxis=dict(showgrid=True),
                                        lataxis=dict(showgrid=True),
                                        showcountries=True,
                                        showsubunits=True,
                                        scope=map_region,
                                        projection=dict(type=map_proj_type,
                                                        scale=map_scale),
                                        showland=True,
                                        resolution=map_resolution,
                                        center=dict(lat=map_center_lat,
                                                    lon=map_center_lon),
                                        landcolor=map_land_color,
                                        countrywidth=0.3,
                                        subunitwidth=0.3))

            return dict(data=data, layout=layout)
