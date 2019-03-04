#!/usr/bin/env python3

"""
docstring is here
"""

import os
import common.config as config
import common.framework as framework
import data.dao as dao
import datetime
import traceback
import sys
import argparse
import dash
import dash_html_components as html
import dash_core_components as doc
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from flask import abort, Response


class ServiceLevelViewer(framework.SetupwithMySQLdb):

    def __init__(self):
        super().__init__(__name__, __file__)

    def setup_commandline_argument(self):
        argument_parser = argparse.ArgumentParser()

        argument_parser.add_argument("host",
                                     type=str,
                                     help="host to bind")
        argument_parser.add_argument("port",
                                     type=str,
                                     help="port to bind")
        argument_parser.add_argument("--debug",
                                     action="store_true",
                                     help="whether to set debug mode")
        argument_parser.add_argument("--offline",
                                     action="store_true",
                                     help="disable loading resources from cdn")

        self.args = argument_parser.parse_args()
        self.validate_commandline_argument()

    def make_header(self):

        header = html.Div([
            html.H1("Authoritative DNS Server Response Time")
        ], id="main-content-header")

        return header

    def make_menu(self):

        # TODO: 正しく実装
        authoritative_group = [dict(label="root dns server", value="root"),
                               dict(label="jp dns server", value="jp")]

        probe_group = [dict(label="tyo", value="tyo"),
                       dict(label="sjc", value="sjc")]

        menu = html.Div([
            html.Div([
                "Filter by measurement time:",
                doc.RangeSlider(id="main-content-menu-filter_measurement_time",
                                min=1,
                                max=24,
                                step=1,
                                value=[12, 22],
                                marks={
                                    2: "23 hours ago",
                                    7: "18 horus ago",
                                    12: "13 horus ago",
                                    17: "8 horus ago",
                                    22: "3 horus ago"})],
                     style=dict(width="100%",
                                marginTop="2%")),

            html.Div([
                "Filter by authoritative server:",
                doc.Dropdown(id="main-content-menu-filter_authoritative_server",
                             options=authoritative_group,
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
                             multi=False),
            ], style=dict(display="inline-block",
                          width="48%",
                          margin="auto",
                          marginTop="3%",
                          marginLeft="2%"))

        ], id="main-content-menu")

        return menu

    def make_graph(self):

        # TODO: 正しく実装
        trace1 = go.Scatter(mode="lines",
                            x=[datetime.datetime(2019, 2, 1, 15, 30, 10),
                               datetime.datetime(2019, 2, 1, 15, 31, 10),
                               datetime.datetime(2019, 2, 1, 15, 32, 10),
                               datetime.datetime(2019, 2, 1, 15, 33, 10),
                               datetime.datetime(2019, 2, 1, 15, 34, 10)],
                            y=[0.022,
                               0.02,
                               0.05,
                               0.18,
                               0.42],
                            name="UDP over IPv4")

        trace2 = go.Scatter(mode="lines",
                            x=[datetime.datetime(2019, 2, 1, 15, 30, 10),
                               datetime.datetime(2019, 2, 1, 15, 31, 10),
                               datetime.datetime(2019, 2, 1, 15, 32, 10),
                               datetime.datetime(2019, 2, 1, 15, 33, 10),
                               datetime.datetime(2019, 2, 1, 15, 34, 10)],
                            y=[0.122,
                               0.02,
                               0.49,
                               0.18,
                               0.02],
                            name="UDP over IPv6")

        data = [trace1, trace2]

        graph = html.Div([
            doc.Graph(id='main-content-graph-example',
                      figure=dict(data=data,
                                  layout=go.Layout(title="m.root-servers.net",
                                                   xaxis=dict(title="time"),
                                                   yaxis=dict(title="RTT"),
                                                   )))
        ], id="main-content-graph")

        return graph

    def make_css(self):

        cssdir = self.cnfs.resource.css_dir
        path = os.path.join(config.STATIC_DIR, cssdir)

        if not os.path.isdir(path):
            self.logger.warning("path is not css dir: %s" % path)

        csslists = os.listdir(path)
        self.logger.info("css found for %s" % str(csslists))

        result = html.Div([html.Link(rel="stylesheet",
                                     href=os.path.join("/static/",
                                                       cssdir,
                                                       each))
                           for each in csslists if each.endswith(".css")])

        return result

    def set_layout(self):
        self.application.layout = html.Div([
            self.make_css(),
            html.Div([
                html.Div([
                    self.make_header(),
                    self.make_menu(),
                    self.make_graph()
                ], style=dict(id="main-content",
                              width="96%",
                              margin="auto"))
            ], id="main",
               style=dict(margin="auto",
                          marginTop="2%",
                          width="90%",
                          boxShadow="0px 0px 3px",
                          border="1px solid #eee",
                          bacgroundColor="#ffffff"))])

    def set_callbacks(self):

        @self.application.server.route(os.path.join("/static/",
                                                    self.cnfs.resource.css_dir,
                                                    "<stylesheet>"))
        def serve_css(stylesheet):

            self.logger.info("requested css file \"%s\"" % str(stylesheet))

            if (".." in stylesheet) or ("/" in stylesheet):
                self.logger.warn("invalid file name \"%s\"" % str(stylesheet))
                abort(404)

            try:
                with open(os.path.join(config.STATIC_DIR,
                                       self.cnfs.resource.css_dir,
                                       stylesheet), "r") as handle:
                    return Response(handle.read(), mimetype="text/css")

            except Exception:
                self.logger.warning("exception while loading css \"%s\"" %
                                    str(stylesheet))
                abort(404)

    def run(self):
        self.application = dash.Dash()
        self.application.css.config.serve_locally = self.args.offline
        self.application.scripts.config.serve_locally = self.args.offline

        self.set_layout()
        self.set_callbacks()

        self.application.run_server(debug=self.args.debug,
                                    host=self.args.host,
                                    port=self.args.port)


if __name__ == "__main__":

    try:
        mc = ServiceLevelViewer()
        mc.start()
    except Exception:
        # LOGGERのセットアップ自体にも失敗している可能性ありの為
        # 標準出力にログ出力
        print(traceback.format_exc())
        sys.exit(1)
