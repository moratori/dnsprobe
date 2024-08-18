#!/usr/bin/env python3

"""
docstring is here
"""

import plotly.graph_objs as go
import html as snt
import os
import datetime
import math
import re
from dash import html
from dash import dcc

from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
from flask import abort, Response
from logging import getLogger
from werkzeug.routing import BaseConverter

import common.common.config as config


LOGGER = getLogger(__name__)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


class RTTViewerLogic():

    def __init__(self, rttviewer, plotarea_coloring):
        self.rttviewer = rttviewer
        self.plotarea_coloring = plotarea_coloring

    def convert_range_index_to_time(self, time_range):

        upper = 24
        seconds_for_hour = 3600
        current_time = datetime.datetime.utcnow()
        start_index, end_index = time_range

        start_time = current_time - datetime.timedelta(
            seconds=(upper - start_index) * seconds_for_hour)
        end_time = current_time - datetime.timedelta(
            seconds=(upper - end_index) * seconds_for_hour)

        return start_time.isoformat() + "Z", end_time.isoformat() + "Z"

    def check_time_range(self, time_range):
        return (time_range is not None and
                type(time_range) is list and
                len(time_range) == 2 and
                type(time_range[0]) is int and
                type(time_range[1]) is int)

    def check_dns_server_name(self, dns_server_name):
        if dns_server_name is None or not dns_server_name:
            return False
        pat = re.compile(r"^[A-Za-z0-9\.\-]+$")
        if not pat.findall(dns_server_name):
            return False
        return True

    def check_probe_names(self, probe_names):
        if probe_names is None or not probe_names:
            return False
        pat = re.compile(r"^[a-z0-9\-]+$")
        for each in probe_names:
            if each is None:
                return False
            if not pat.findall(each):
                return False
        return True

    def check_rrtype(self, rrtype):
        if rrtype is None:
            return False
        if re.compile("^[a-zA-Z]+$").findall(rrtype):
            return True
        return False

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
            Output("main-content-graph-percentile-figure", "figure"),
            [Input("main-content-menu-filter_measurement_time", "value"),
             Input("main-content-menu-filter_authoritative", "value"),
             Input("main-content-menu-filter_probe", "value"),
             Input("main-content-menu-filter_rrtype", "value"),
             Input("main-content-graph-interval", "n_intervals")])
        def update_percentilegraph(time_range, dns_server_name, probe_names,
                                   rrtype, cnt):

            if not (self.check_time_range(time_range) and
                    self.check_dns_server_name(dns_server_name) and
                    self.check_probe_names(probe_names) and
                    self.check_rrtype(rrtype)):
                LOGGER.warning("lack of argument for rendering graph")
                return dict()

            start_time, end_time = \
                self.convert_range_index_to_time(time_range)

            ret = self.rttviewer.dao_dnsprobe.get_percentilegraph_data(
                dns_server_name,
                probe_names,
                rrtype,
                start_time,
                end_time)

            LOGGER.debug("timerange: %s ~ %s" % (start_time, end_time))
            LOGGER.debug("percentile raw data: %s" % (str(ret)))

            traces = []

            for (af, proto) in sorted(ret.keys()):
                x, y = ret[(af, proto)]
                traces.append(go.Scatter(mode="lines",
                                         x=x,
                                         y=y,
                                         name=snt.escape("%s over IPv%s" %
                                                         (proto.upper(), af))))

            figure = dict(data=traces,
                          layout=go.Layout(
                              margin=dict(t=70,
                                          b=35,
                                          r=15,
                                          l=45),
                              title="Round Trip Time Percentile",
                              showlegend=True,
                              xaxis=dict(title="Round Trip Time(msec)",
                                         autorange=True,
                                         type="log",
                                         rangemode="tozero"),
                              yaxis=dict(title="Percentile(%)",
                                         autorange=True,
                                         rangemode="tozero"),
                              legend=dict(orientation="h",
                                          font=dict(size=9),
                                          yanchor="top",
                                          x=0,
                                          y=1.08),
                              paper_bgcolor=self.plotarea_coloring["paper_bgcolor"],
                              plot_bgcolor=self.plotarea_coloring["plot_bgcolor"],
                              font_color=self.plotarea_coloring["font_color"],
                              title_font_color=self.plotarea_coloring["title_font_color"],
                          ))

            return figure

        @self.rttviewer.application.callback(
            Output("main-content-graph-nsid-figure", "figure"),
            [Input("main-content-menu-filter_measurement_time", "value"),
             Input("main-content-menu-filter_authoritative", "value"),
             Input("main-content-menu-filter_probe", "value"),
             Input("main-content-menu-filter_rrtype", "value"),
             Input("main-content-graph-interval", "n_intervals")])
        def update_nsidgraph(time_range, dns_server_name, probe_names,
                             rrtype, cnt):

            if not (self.check_time_range(time_range) and
                    self.check_dns_server_name(dns_server_name) and
                    self.check_probe_names(probe_names) and
                    self.check_rrtype(rrtype)):
                LOGGER.warning("lack of argument for rendering graph")
                return dict()

            start_time, end_time = \
                self.convert_range_index_to_time(time_range)

            ret = self.rttviewer.dao_dnsprobe.get_nsidgraph_data(
                dns_server_name,
                probe_names,
                rrtype,
                start_time,
                end_time)

            values = []
            labels = []
            title = "NSID Ratio(%s from selected probes)" % (dns_server_name)
            legend_max_num = 4

            for (measurement_name, tags) in ret.keys():
                count = list(ret.get_points(measurement=measurement_name,
                                            tags=tags))
                if ("nsid" not in tags) or (len(count) != 1) or \
                        ("count" not in count[0]):
                    break
                else:
                    labels.append(tags["nsid"])
                    values.append(count[0]["count"])

            trace = go.Pie(values=values,
                           labels=labels,
                           name="NSID",
                           title="NSID",
                           hoverinfo="label+percent+name",
                           hole=0.4)

            figure = dict(data=[trace],
                          layout=go.Layout(title=dict(text=title,
                                                      xanchor="center",
                                                      yanchor="top",
                                                      x=0.5,
                                                      y=0.97),
                                           legend=dict(orientation="h",
                                                       font=dict(size=9),
                                                       yanchor="top",
                                                       x=0,
                                                       y=1.17),
                                           showlegend=(len(values) <
                                                       legend_max_num),
                                           margin=dict(t=110,
                                                       b=90,
                                                       r=90,
                                                       l=90
                                                       ),
                                           paper_bgcolor=self.plotarea_coloring["paper_bgcolor"],
                                           plot_bgcolor=self.plotarea_coloring["plot_bgcolor"],
                                           font_color=self.plotarea_coloring["font_color"],
                                           title_font_color=self.plotarea_coloring["title_font_color"],
                                           ))

            return figure

        @self.rttviewer.application.callback(
            Output("main-content-graph-ratio-figure", "figure"),
            [Input("main-content-menu-filter_measurement_time", "value"),
             Input("main-content-menu-filter_authoritative", "value"),
             Input("main-content-menu-filter_probe", "value"),
             Input("main-content-menu-filter_rrtype", "value"),
             Input("main-content-graph-interval", "n_intervals")])
        def update_ratiograph(time_range, dns_server_name, probe_names,
                              rrtype, cnt):

            if not (self.check_time_range(time_range) and
                    self.check_dns_server_name(dns_server_name) and
                    self.check_probe_names(probe_names) and
                    self.check_rrtype(rrtype)):
                LOGGER.warning("lack of argument for rendering graph")
                return dict()

            start_time, end_time = \
                self.convert_range_index_to_time(time_range)

            af_proto_combination = \
                self.rttviewer.dao_dnsprobe.get_af_proto_combination(
                    dns_server_name, probe_names)

            LOGGER.debug("time range %s to %s" % (start_time, end_time))
            LOGGER.debug("af proto combination: %s" %
                         (af_proto_combination))

            title = "Query Response Rate(%s from selected probes)" % (
                dns_server_name)

            labels = ["Failed", "Exceeded specific RTT threshold",
                      "Successful"]
            donut_size = 0.45
            hoverinfo = "label+percent+name"
            row_tiling_num = 2

            num_of_graphs = len(af_proto_combination)
            rows = int(math.ceil(num_of_graphs / row_tiling_num))
            columns = int(num_of_graphs if row_tiling_num >= num_of_graphs
                          else row_tiling_num)

            subplots = make_subplots(rows=rows,
                                     cols=columns,
                                     specs=[[dict(type="domain")
                                             for column in range(columns)]
                                            for row in range(rows)],
                                     vertical_spacing=0.1)

            for (n, (af, proto)) in enumerate(sorted(af_proto_combination)):
                r = int(n / row_tiling_num)
                c = int(n % row_tiling_num)

                args = (dns_server_name, probe_names, af, proto, rrtype,
                        start_time, end_time)

                failed_count = self.rttviewer.dao_dnsprobe.\
                    get_ratiograph_failed(*args)

                exceeded_count = self.rttviewer.dao_dnsprobe.\
                    get_ratiograph_exceeded_slr(*args)

                successful_count = self.rttviewer.dao_dnsprobe.\
                    get_ratiograph_successful(*args)

                if (failed_count + successful_count + exceeded_count) == 0:
                    continue

                subtitle = snt.escape("%s IPv%s" % (proto.upper(), af))

                subplots.add_trace(go.Pie(values=[failed_count,
                                                  exceeded_count,
                                                  successful_count],
                                          labels=labels,
                                          domain=dict(row=r, column=c),
                                          name=subtitle,
                                          hoverinfo=hoverinfo,
                                          hole=donut_size,
                                          title=subtitle,
                                          marker=dict(colors=["red",
                                                              "orange",
                                                              "green"])),
                                   r+1,
                                   c+1)

            subplots.update_layout(title=dict(text=title,
                                              xanchor="center",
                                              yanchor="top",
                                              x=0.5,
                                              y=0.97),
                                   margin=dict(t=100,
                                               b=30,
                                               r=0,
                                               l=50),
                                   legend=dict(orientation="h",
                                               font=dict(size=9),
                                               yanchor="top",
                                               x=0.1,
                                               y=1.15),
                                   grid=dict(rows=rows,
                                             columns=columns),
                                   paper_bgcolor=self.plotarea_coloring["paper_bgcolor"],
                                   plot_bgcolor=self.plotarea_coloring["plot_bgcolor"],
                                   font_color=self.plotarea_coloring["font_color"],
                                   title_font_color=self.plotarea_coloring["title_font_color"],
                                   )

            return subplots


        @self.rttviewer.application.callback(
            Output("main-content-graph-rtt-figure", "figure"),
            [Input("main-content-menu-filter_measurement_time", "value"),
             Input("main-content-menu-filter_authoritative", "value"),
             Input("main-content-menu-filter_probe", "value"),
             Input("main-content-menu-filter_rrtype", "value"),
             Input("main-content-graph-interval", "n_intervals")])
        def update_rttgraph(time_range, dns_server_name, probe_names, rrtype,
                            cnt):

            LOGGER.debug("time range: %s" % time_range)
            LOGGER.debug("dns server name: %s" % dns_server_name)
            LOGGER.debug("probe name: %s" % probe_names)

            if not (self.check_time_range(time_range) and
                    self.check_dns_server_name(dns_server_name) and
                    self.check_probe_names(probe_names) and
                    self.check_rrtype(rrtype)):
                LOGGER.warning("lack of argument for rendering graph")
                return dict()

            if not dns_server_name:
                return dict()

            title = "Time Variation of RTT(%s from selected probes)" % (
                dns_server_name)

            start_time, end_time = \
                self.convert_range_index_to_time(time_range)

            af_proto_combination = \
                self.rttviewer.dao_dnsprobe.get_af_proto_combination(
                    dns_server_name, probe_names)

            traces = []
            for (af, proto) in sorted(af_proto_combination):

                x, y = \
                    self.rttviewer.dao_dnsprobe.get_rttgraph_data(
                        dns_server_name,
                        probe_names,
                        af,
                        proto,
                        rrtype,
                        start_time,
                        end_time)

                if not (x and y):
                    continue

                traces.append(go.Scatter(mode="lines",
                                         x=x,
                                         y=y,
                                         name=snt.escape("%s over IPv%s" %
                                                         (proto.upper(), af))))

            figure = dict(data=traces,
                          layout=go.Layout(
                              margin=dict(t=70,
                                          b=35,
                                          r=15,
                                          l=45),
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
                                          y=1.05),
                              paper_bgcolor=self.plotarea_coloring["paper_bgcolor"],
                              plot_bgcolor=self.plotarea_coloring["plot_bgcolor"],
                              font_color=self.plotarea_coloring["font_color"],
                              title_font_color=self.plotarea_coloring["title_font_color"],
                          ))

            return figure

        @self.rttviewer.application.callback(
            Output("main-content-graph-map-figure", "figure"),
            [Input("main-content-menu-filter_probe", "value"),
             Input("main-content-graph-interval", "n_intervals")])
        def update_map(probe_names, cnt):

            map_height = 500
            map_scale = 1.1
            map_center_lat = 0
            map_center_lon = 0
            map_region = "world"
            map_title = "Location of Probes"
            map_land_color = "rgb(235, 235, 235)"
            map_resolution = 50
            map_proj_type = "equirectangular"
            color_map = {True: "orange", False: "grey"}
            size_map = {True: 11, False: 10}
            hovertext = "probe-id: %s<br />last measured: %s<br />uptime: %s\
            <br />ASN(v4): AS%s<br />description(v4): %s\
            <br />ASN(v6): AS%s<br />description(v6): %s"

            probe_location_name, latitudes, longitudes = \
                self.rttviewer.dao_dnsprobe.make_probe_locations()

            data = []
            for (locname, lat, lon) in zip(probe_location_name,
                                           latitudes,
                                           longitudes):

                color = color_map[locname in probe_names]
                size = size_map[locname in probe_names]

                last_measured = \
                    self.rttviewer.dao_dnsprobe.get_probe_last_measured(
                        locname)
                uptime = \
                    self.rttviewer.dao_dnsprobe.get_probe_uptime(
                        locname)
                v4_asn, v4_desc, v6_asn, v6_desc = \
                    self.rttviewer.dao_dnsprobe.get_probe_net_desc(locname)

                data.append(go.Scattergeo(lon=[lon],
                                          lat=[lat],
                                          text=locname,
                                          name=locname,
                                          hovertext=hovertext % (locname,
                                                                 last_measured,
                                                                 uptime,
                                                                 v4_asn,
                                                                 v4_desc,
                                                                 v6_asn,
                                                                 v6_desc),
                                          mode="markers",
                                          showlegend=False,
                                          marker=dict(size=size,
                                                      symbol="circle",
                                                      color=color)))

            layout = go.Layout(title=dict(text=map_title,
                                          y=0.97),
                               height=map_height,
                               margin=dict(t=15,
                                           b=15,
                                           pad=0,
                                           r=0,
                                           l=0),
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
                                        subunitwidth=0.3),
                               paper_bgcolor=self.plotarea_coloring["paper_bgcolor"],
                               plot_bgcolor=self.plotarea_coloring["plot_bgcolor"],
                               font_color=self.plotarea_coloring["font_color"],
                               title_font_color=self.plotarea_coloring["title_font_color"],
                               )

            return dict(data=data, layout=layout)
