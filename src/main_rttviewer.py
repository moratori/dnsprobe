#!/usr/bin/env python3

"""
docstring is here
"""

import common.common.config as config
import common.common.framework as framework
import common.data.dao as dao
import logic.viewer.rttviewer as rttviewerlogic
import dash_html_components as html
import dash_core_components as doc
import plotly.graph_objs as go

import traceback
import os
import sys
import argparse
import dash


SLV = None


class RTTViewer(framework.SetupwithInfluxdb):

    def __init__(self):
        super().__init__(__name__, __file__)
        self.dao_dnsprobe = dao.Dnsprobe(self)
        self.logic = rttviewerlogic.RTTViewerLogic(self)

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
                                     default=True,
                                     help="disable loading resources from cdn")

        self.args = argument_parser.parse_args()
        self.validate_commandline_argument()

    def make_header(self):

        header = html.Div([
            html.H1("Authoritative DNS Server Response Time")
        ], id="main-content-header")

        return header

    def make_menu(self):

        authoritative_group = self.dao_dnsprobe.make_authoritative_group()
        probe_group = self.dao_dnsprobe.make_probe_group()
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
            html.Div([
                doc.Graph(id="main-content-rttgraph-figure",
                          figure=dict(),
                          style=dict(height=600),
                          config=dict(displayModeBar=False))],
                     id="main-content-rttgraph",
                     style=dict(display="inline-block",
                                width="50%")),
            html.Div([
                doc.Graph(id="main-content-tograph-figure",
                          figure=dict(),
                          style=dict(height=600),
                          config=dict(displayModeBar=False))],
                     id="main-content-tograph",
                     style=dict(display="inline-block",
                                width="50%")),
            doc.Interval(id="main-content-graph-interval",
                         interval=30*1000,
                         n_intervals=0)
        ])

        return graph

    def make_map(self):

        map_height = 1100
        map_scale = 1
        map_center_lat = 25
        map_center_lon = 90
        map_region = "asia"
        map_title = "Location of Probes"
        map_land_color = "rgb(235, 235, 235)"
        map_resolution = 50
        map_projection_type = "equirectangular"

        probe_location_name, latitudes, longitudes = \
            self.dao_dnsprobe.make_probe_locations()

        data = [go.Scattergeo(lon=longitudes,
                              lat=latitudes,
                              text=probe_location_name,
                              mode="markers",
                              marker=dict(size=13,
                                          symbol="circle"))]

        layout = go.Layout(title=map_title,
                           height=map_height,
                           geo=dict(scope=map_region,
                                    projection=dict(type=map_projection_type,
                                                    scale=map_scale),
                                    showland=True,
                                    resolution=map_resolution,
                                    center=dict(lat=map_center_lat,
                                                lon=map_center_lon),
                                    landcolor=map_land_color,
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

    def setup_app(self):
        self.application = dash.Dash(__name__)
        self.application.server.url_map.converters["regex"] = \
            rttviewerlogic.RegexConverter
        self.application.css.config.serve_locally = self.args.offline
        self.application.scripts.config.serve_locally = self.args.offline
        self.application.title = "RTT monitor"

        self.set_layout()
        self.logic.setup_logic()

    def run(self):
        self.setup_app()
        self.application.run_server(debug=self.args.debug,
                                    host=self.args.host,
                                    port=self.args.port)


def nakedserver():
    try:
        slv = RTTViewer()
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
            slv = RTTViewer()
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
