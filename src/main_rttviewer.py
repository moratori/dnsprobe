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
            html.H1("Authoritative DNS Server Response Time"),
            doc.Interval(id="main-content-graph-interval",
                         interval=30 * 1000,
                         n_intervals=0)
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
                             value=[default_authoritative],
                             multi=True)
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

        ], id="main-content-menu",
            style=dict(marginBottom="1.5%"))

        return menu

    def make_graph(self):

        graph = html.Div(children=[],
                         id="main-content-graph")

        return graph

    def make_map(self):

        graph = html.Div([doc.Graph("main-content-map-figure",
                                    figure=dict(),
                                    config=dict(displayModeBar=False),
                                    style=dict(paddingTop="0%"))
                          ], style=dict(display="block",
                                        marginTop="0%",
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
                          marginTop="1%",
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
