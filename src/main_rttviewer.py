#!/usr/bin/env python3

"""
docstring is here
"""

import traceback
import os
import sys
import dash
import dash_html_components as html
import dash_core_components as doc

import common.common.config as config
import common.common.framework as framework
import common.data.dao as dao
import logic.viewer.rttviewer as rttviewerlogic


SLV = None


class RTTViewer(framework.SetupwithInfluxdb):

    def __init__(self):
        super().__init__(__name__, __file__)
        self.dao_dnsprobe = dao.Dnsprobe(self)
        self.logic = rttviewerlogic.RTTViewerLogic(self)

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
        rrtype_group = self.dao_dnsprobe.make_rrtype_group()
        default_authoritative = None
        default_probe = None
        default_rrtype = None

        if authoritative_group:
            default_authoritative = authoritative_group[0]["value"]

        if probe_group:
            default_probe = probe_group[0]["value"]

        if rrtype_group:
            default_rrtype = rrtype_group[0]["value"]

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
                          width="32%",
                          marign="auto",
                          marginTop="3%",
                          marginRight="1%"
                          )),

            html.Div([
                "Filter by Resource Record type:",
                doc.Dropdown(id="main-content-menu-filter_rrtype",
                             options=rrtype_group,
                             value=default_rrtype,
                             multi=False)
            ], style=dict(display="inline-block",
                          width="32%",
                          marign="auto",
                          marginTop="3%",
                          marginRight="1%",
                          marginLeft="1%"
                          )),

            html.Div([
                "Filter by measurer:",
                doc.Dropdown(id="main-content-menu-filter_probe",
                             options=probe_group,
                             value=default_probe,
                             multi=False),
            ], style=dict(display="inline-block",
                          width="32%",
                          margin="auto",
                          marginTop="3%",
                          marginLeft="1%"))

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
                                    config=dict(displayModeBar=False,
                                                scrollZoom=False),
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
                          marginTop="0%",
                          width="100%",
                          boxShadow="0px 0px 3px",
                          border="1px solid #eee",
                          bacgroundColor="#ffffff"))])

    def setup_application(self):
        self.application = dash.Dash(__name__)
        self.application.server.url_map.converters["regex"] = \
            rttviewerlogic.RegexConverter
        self.application.css.config.serve_locally = self.cnfs.server.offline
        self.application.scripts.config.serve_locally = \
            self.cnfs.server.offline
        self.application.title = "RTT monitor"

        self.set_layout()
        self.logic.setup_logic()

    def run_application(self):
        self.application.run_server(debug=self.cnfs.server.debug,
                                    host=self.cnfs.server.host,
                                    port=self.cnfs.server.port)


def nakedserver():
    try:
        slv = RTTViewer()
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)

    slv.start()


def wsgiserver(*positional, **kw):
    global SLV
    try:
        if SLV is None:
            slv = RTTViewer()
            slv.setup_resource()
            slv.setup_application()
            SLV = slv
        return SLV.application.server(*positional, **kw)
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    nakedserver()
