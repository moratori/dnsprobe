#!/usr/bin/env python3

"""
docstring is here
"""

import traceback
import os
import sys
import dash
from dash import html
from dash import dcc

import common.common.config as config
import common.common.framework as framework
import common.data.dao as dao
import logic.viewer.rttviewer as rttviewerlogic


SLV = None


class RTTViewer(framework.SetupwithInfluxdb):

    def __init__(self):
        super().__init__(__name__, __file__)

        self.backmost_color = "#212027" # set same value in css
        self.text_color = "#cbcad3"
        self.floating_area_background = "#3c3b45"
        self.dropdown_background_color = "#ffffff"

        plot_area_coloring = {
            "paper_bgcolor": self.floating_area_background,
            "plot_bgcolor": self.floating_area_background,
            "font_color": self.text_color,
            "title_font_color": self.text_color,
        }

        self.dao_dnsprobe = dao.Mes_dnsprobe(self)
        self.logic = rttviewerlogic.RTTViewerLogic(self,
                                                   plot_area_coloring)

    def make_header(self):

        header = html.Div([
            html.H2("Authoritative DNS Server Response Time"),
            dcc.Interval(id="main-content-graph-interval",
                         interval=60 * 1000,
                         n_intervals=0)
        ], id="main-content-header",
           style=dict(color=self.text_color))

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
                dcc.RangeSlider(id="main-content-menu-filter_measurement_time",
                                min=1,
                                max=24,
                                step=1,
                                value=[21, 24],
                                marks={
                                    2: "22 hours ago",
                                    9: "15 hours ago",
                                    16: "8 hours ago",
                                    23: "1 horus ago"})],
                     style=dict(width="95%",
                                paddingTop="0.5%",
                                paddingLeft="0%",
                                marginLeft="3%",
                                marginRight="3%",
                                color=self.text_color
                                )),

            html.Div([
                "Filter by authoritative server:",
                dcc.Dropdown(id="main-content-menu-filter_authoritative",
                             options=authoritative_group,
                             value=default_authoritative,
                             multi=False,
                             style=dict(backgroundColor=self.dropdown_background_color))
            ], style=dict(display="inline-block",
                          width="30%",
                          marign="auto",
                          marginTop="0.5%",
                          marginLeft="3%",
                          marginRight="1%",
                          marginBottom="1%",
                          color=self.text_color
                          )),

            html.Div([
                "Filter by Resource Record type:",
                dcc.Dropdown(id="main-content-menu-filter_rrtype",
                             options=rrtype_group,
                             value=default_rrtype,
                             multi=False,
                             style=dict(backgroundColor=self.dropdown_background_color))
            ], style=dict(display="inline-block",
                          width="30%",
                          marign="auto",
                          marginTop="0.5%",
                          marginRight="1%",
                          marginLeft="1%",
                          marginBottom="1%",
                          color=self.text_color
                          )),

            html.Div([
                "Filter by measurer:",
                dcc.Dropdown(id="main-content-menu-filter_probe",
                             options=probe_group,
                             value=[default_probe],
                             multi=True,
                             style=dict(backgroundColor=self.dropdown_background_color)),
            ], style=dict(display="inline-block",
                          width="30%",
                          margin="auto",
                          marginTop="0.5%",
                          marginLeft="1%",
                          marginRight="3%",
                          marginBottom="1%",
                          color=self.text_color
                          ))

        ], id="main-content-menu",
            style=dict(marginBottom="0.5%",
                       backgroundColor=self.floating_area_background,
                       boxShadow="0 0 10px black"))

        return menu

    def make_graph(self):

        graph_height = 500

        graph = html.Div(
            children=[
                    html.Div([
                        html.Div([
                            dcc.Graph("main-content-graph-rtt-figure",
                                      figure=dict(),
                                      style=dict(height=graph_height),
                                      config=dict(displayModeBar=False))],
                                 style=dict(display="inline-block",
                                            boxShadow="0 0 10px black",
                                            verticalAlign="bottom",
                                            width="33%")),
                        html.Div([
                            dcc.Graph("main-content-graph-ratio-figure",
                                      figure=dict(),
                                      style=dict(height=graph_height),
                                      config=dict(displayModeBar=False))],
                                 style=dict(display="inline-block",
                                            boxShadow="0 0 10px black",
                                            marginLeft="0.5%",
                                            verticalAlign="bottom",
                                            width="33%")),
                        html.Div([
                            dcc.Graph("main-content-graph-nsid-figure",
                                      figure=dict(),
                                      style=dict(height=graph_height),
                                      config=dict(displayModeBar=False))],
                                 style=dict(display="inline-block",
                                            boxShadow="0 0 10px black",
                                            marginLeft="0.5%",
                                            verticalAlign="bottom",
                                            width="33%"))],
                             style=dict(marginBottom="0.5%")),

                    html.Div([
                        html.Div([
                            dcc.Graph("main-content-graph-percentile-figure",
                                      figure=dict(),
                                      style=dict(height=graph_height),
                                      config=dict(displayModeBar=False))],
                                 style=dict(display="inline-block",
                                            verticalAlign="top",
                                            boxShadow="0 0 10px black",
                                            width="39.5%")),
                        html.Div([
                            dcc.Graph("main-content-graph-map-figure",
                                      figure=dict(),
                                      config=dict(displayModeBar=False,
                                                  scrollZoom=False),
                                      style=dict(paddingTop="0%"))],
                                 style=dict(display="inline-block",
                                            verticalAlign="top",
                                            boxShadow="0 0 10px black",
                                            marginLeft="0.5%",
                                            width="60%"))])
            ],
            id="main-content-graph")

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
                ], style=dict(id="main-content",
                              width="97%",
                              margin="auto",
                              backgroundColor=self.backmost_color))
            ], id="main",
               style=dict(margin="auto",
                          marginTop="0%",
                          width="100%",
                          boxShadow="0px 0px 3px",
                          border="1px solid " + self.backmost_color,
                          bacgroundColor=self.backmost_color))])

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
