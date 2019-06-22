#!/usr/bin/env python3

"""
docstring is here
"""

import os
import common.config as config
import common.framework as framework
import datetime
import traceback
import sys
import argparse
import json
import dash
import dash_html_components as html
import dash_core_components as doc
import plotly.graph_objs as go
import html as sanitizer
from dash.dependencies import Input, Output
from flask import abort, Response
from werkzeug.routing import BaseConverter


SLV = None


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


class ServiceLevelViewer(framework.SetupwithInfluxdb):

    def __init__(self):
        super().__init__(__name__, __file__)

    def setup_commandline_argument(self):
        argument_parser = argparse.ArgumentParser()

        argument_parser.add_argument("--host",
                                     type=str,
                                     default="0.0.0.0",
                                     help="host to bind")
        argument_parser.add_argument("--port",
                                     type=int,
                                     default=8080,
                                     help="port to bind")
        argument_parser.add_argument("--debug",
                                     action="store_true",
                                     help="whether to set debug mode")
        argument_parser.add_argument("--offline",
                                     action="store_true",
                                     help="disable loading resources from cdn")

        self.args = argument_parser.parse_args()
        self.validate_commandline_argument()

    def __show_tag_list(self, tag):
        # tag parameter MUST BE TRUSTED value
        # unable to use `bind-parameter` for `with key` statement
        ret = self.session.query("show tag values with key = %s" % (tag))
        result = []
        for each in ret:
            for record in each:
                result.append(record["value"])
        return result

    def __make_authoritative_group(self):
        ret = self.__show_tag_list("dst_name")
        result = [dict(label=each, value=each) for each in ret]
        return result

    def __make_probe_group(self):
        ret = self.__show_tag_list("prb_id")
        result = [dict(label=each, value=each) for each in ret]
        return result

    def __make_probe_locations(self):
        probe_list = self.__show_tag_list("prb_id")
        lats = []
        lons = []
        for prb_id in probe_list:
            ret = self.session.query("show tag values with key in \
                                      (prb_lat, prb_lon) where \
                                      prb_id = $prb_id",
                                     params=dict(params=json.dumps(
                                         dict(prb_id=prb_id))))
            for each in ret:
                for record in each:
                    key = record["key"]
                    value = record["value"]
                    if key == "prb_lat":
                        lats.append(value)
                    if key == "prb_lon":
                        lons.append(value)

        return probe_list, lats, lons

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

    def __get_af_proto_combination(self, dns_server_name, probe_name):

        ret_af = self.session.query(
            "show tag values with key = af where \
             dst_name = $dst_name and prb_id = $prb_id",
            params=dict(params=json.dumps(dict(dst_name=dns_server_name,
                                               prb_id=probe_name))))

        ret_proto = self.session.query(
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

    def make_header(self):

        header = html.Div([
            html.H1("Authoritative DNS Server Response Time")
        ], id="main-content-header")

        return header

    def make_menu(self):

        authoritative_group = self.__make_authoritative_group()
        probe_group = self.__make_probe_group()
        default_authoritative = None
        default_probe = None

        if authoritative_group:
            default_authoritative = authoritative_group[0]["value"]

        if probe_group:
            default_probe = probe_group[0]["value"]

        menu = html.Div([
            html.Div([
                "Filter by measurement time:",
                doc.RangeSlider(id="main-content-menu-filter_measurement_time",
                                min=1,
                                max=24,
                                step=1,
                                value=[21, 24],
                                marks={
                                    2: "22 hours ago",
                                    9: "15 hours ago",
                                    16: "8 hours ago",
                                    23: "1 horus ago"})],
                     style=dict(width="100%",
                                marginTop="2%")),

            html.Div([
                "Filter by authoritative server:",
                doc.Dropdown(id="main-content-menu-filter_authoritatives",
                             options=authoritative_group,
                             value=default_authoritative,
                             multi=False)
            ], style=dict(display="inline-block",
                          width="48%",
                          marign="auto",
                          marginTop="3%",
                          marginRight="2%"
                          )),

            html.Div([
                "Filter by measurer:",
                doc.Dropdown(id="main-content-menu-filter_probe",
                             options=probe_group,
                             value=default_probe,
                             multi=False),
            ], style=dict(display="inline-block",
                          width="48%",
                          margin="auto",
                          marginTop="3%",
                          marginLeft="2%"))

        ], id="main-content-menu")

        return menu

    def make_graph(self):

        graph = html.Div([
            doc.Graph(id="main-content-graph-figure",
                      figure=dict(),
                      style=dict(height=600),
                      config=dict(displayModeBar=False)
                      ),
            doc.Interval(
                id="main-content-graph-interval",
                interval=30*1000,
                n_intervals=0),
        ], style=dict(display="block"), id="main-content-graph")

        return graph

    def make_map(self):

        map_height = 1100
        scale = 1
        center_lat = 25
        center_lon = 90
        region = "asia"
        title = "Location of Probes"

        probe_location_name, latitudes, longitudes = \
            self.__make_probe_locations()

        data = [go.Scattergeo(lon=longitudes,
                              lat=latitudes,
                              text=probe_location_name,
                              mode="markers",
                              marker=dict(size=13,
                                          symbol="circle"))]

        layout = go.Layout(title=title,
                           height=map_height,
                           geo=dict(scope=region,
                                    projection=dict(type="equirectangular",
                                                    scale=scale),
                                    showland=True,
                                    resolution=50,
                                    center=dict(lat=center_lat,
                                                lon=center_lon),
                                    landcolor="rgb(235, 235, 235)",
                                    countrywidth=0.3,
                                    subunitwidth=0.3))

        graph = html.Div([doc.Graph("main-content-map-figure",
                                    figure=dict(data=data,
                                                layout=layout),
                                    config=dict(displayModeBar=False))
                          ], style=dict(display="block",
                                        marginTop="2%",
                                        marginLeft="auto",
                                        marginRight="auto"),
                         id="main-content-map")

        return graph

    def make_css(self):

        cssdir = self.cnfs.resource.css_dir
        path = os.path.join(config.STATIC_DIR, cssdir)
        cssext = ".css"

        if not os.path.isdir(path):
            self.logger.warning("path is not css dir: %s" % path)

        csslists = os.listdir(path)
        self.logger.info("css found for %s" % str(csslists))

        result = html.Div([html.Link(rel="stylesheet",
                                     href=os.path.join("/",
                                                       os.path.basename(
                                                           config.STATIC_DIR),
                                                       cssdir,
                                                       each))
                           for each in csslists if each.endswith(cssext)])

        return result

    def set_layout(self):
        self.application.layout = html.Div([
            self.make_css(),
            html.Div([
                html.Div([
                    self.make_header(),
                    self.make_menu(),
                    self.make_graph(),
                    self.make_map()
                ], style=dict(id="main-content",
                              width="96%",
                              margin="auto"))
            ], id="main",
               style=dict(margin="auto",
                          marginTop="2%",
                          width="96%",
                          boxShadow="0px 0px 3px",
                          border="1px solid #eee",
                          bacgroundColor="#ffffff"))])

    def set_callbacks(self):

        @self.application.server.route(os.path.join(
            "/",
            os.path.basename(
                config.STATIC_DIR),
            self.cnfs.resource.css_dir,
            '<regex("[a-zA-Z0-9]+\\.css"):stylesheet>'))
        def serve_css(stylesheet):

            self.logger.info("requested css file \"%s\"" % str(stylesheet))

            try:
                with open(os.path.join(config.STATIC_DIR,
                                       self.cnfs.resource.css_dir,
                                       stylesheet), "r") as handle:
                    return Response(handle.read(), mimetype="text/css")

            except Exception:
                self.logger.warning("exception while loading css \"%s\"" %
                                    str(stylesheet))
                abort(404)

        @self.application.callback(
            Output("main-content-graph-figure", "figure"),
            [Input("main-content-menu-filter_measurement_time", "value"),
             Input("main-content-menu-filter_authoritatives", "value"),
             Input("main-content-menu-filter_probe", "value"),
             Input("main-content-graph-interval", "n_intervals")])
        def update_graph(time_range, dns_server_name, probe_name, n_intervals):

            if (time_range is None) or \
                    (dns_server_name is None) or \
                    (probe_name is None) or \
                    not time_range:
                return dict()

            title = sanitizer.escape("Measurement %s from %s" %
                                     (dns_server_name, probe_name))

            start_time, end_time = \
                self.__convert_range_index_to_time(time_range)

            af_proto_combination = \
                self.__get_af_proto_combination(dns_server_name, probe_name)

            self.logger.debug("time range %s to %s" % (start_time, end_time))

            traces = []
            for (af, proto) in af_proto_combination:

                ret = self.session.query(
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

                traces.append(go.Scatter(mode="lines",
                                         x=x,
                                         y=y,
                                         name="%s over IPv%s" % (proto, af)))

            figure = dict(data=traces,
                          layout=go.Layout(
                              title=title,
                              xaxis=dict(title="UTC Time"),
                              yaxis=dict(title="Round Trip Time(ms)")))

            return figure

    def setup_app(self):
        self.application = dash.Dash(__name__)
        self.application.server.url_map.converters["regex"] = RegexConverter
        self.application.css.config.serve_locally = self.args.offline
        self.application.scripts.config.serve_locally = self.args.offline
        self.application.title = "RTT monitor"

        self.set_layout()
        self.set_callbacks()

    def run(self):
        self.setup_app()
        self.application.run_server(debug=self.args.debug,
                                    host=self.args.host,
                                    port=self.args.port)


def nakedserver():
    try:
        slv = ServiceLevelViewer()
        slv.start()
    except Exception:
        # LOGGERのセットアップ自体にも失敗している可能性ありの為
        # 標準出力にログ出力
        print(traceback.format_exc())
        sys.exit(1)


def wsgiserver(*positional, **kw):
    global SLV
    try:
        if SLV is None:
            slv = ServiceLevelViewer()
            slv.setup_app()
            SLV = slv
        return SLV.application.server(*positional, **kw)
    except Exception:
        # LOGGERのセットアップ自体にも失敗している可能性ありの為
        # 標準出力にログ出力
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    nakedserver()
