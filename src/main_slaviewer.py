#!/usr/bin/env python3

"""
docstring is here
"""

import traceback
import sys
import dash
from dash import html
from dash import dcc

import common.common.framework as framework
import common.data.dao as dao
import logic.viewer.slaviewer as slaviewerlogic


SLAMON = None


class SLAMonitor(framework.SetupwithInfluxdb):

    def __init__(self):
        super().__init__(__name__, __file__)
        self.dao_nameserver_avail = \
            dao.Mes_nameserver_availability(self)
        self.dao_tcp_nameserver_avail = \
            dao.Mes_tcp_nameserver_availability(self)
        self.dao_udp_nameserver_avail = \
            dao.Mes_udp_nameserver_availability(self)
        self.logic = slaviewerlogic.SLAViewerLogic(self)

    def make_header(self):

        header = html.Div([
            html.H1("Authoritative DNS Server Service Level Monitor"),
            dcc.Interval(id="main-content-graph-interval",
                         interval=150 * 1000,
                         n_intervals=0)
        ], id="main-content-header")

        return header

    def make_menu(self):

        supported = self.logic.get_supported_service_levels()
        default = None

        if supported:
            default = supported[0]["value"]

        menu = html.Div([
            html.Div([
                html.H2("Select a criteria of service level"),
                dcc.Dropdown(id="main-content-menu-filter_sl",
                             options=supported,
                             value=default,
                             multi=False)])
        ], style=dict(marginTop="2%"))

        return menu

    def make_description(self):

        description = html.Div([
            html.H2("Description"),
            html.Div("", id="main-content-description")])

        return description

    def make_graph(self):
        graph = html.Div([
            html.Div([
                html.H2("Current Service Level"),
                html.Div(children=[],
                         id="main-content-graph-current")
            ])
        ])

        return graph

    def set_layout(self):

        self.application.layout = html.Div([
            self.make_header(),
            self.make_menu(),
            self.make_description(),
            self.make_graph()
        ])

    def setup_application(self):
        self.application = dash.Dash(__name__)
        self.application.server.url_map.converters["regex"] = \
            slaviewerlogic.RegexConverter
        self.application.css.config.serve_locally = self.cnfs.server.offline
        self.application.scripts.config.serve_locally = \
            self.cnfs.server.offline
        self.application.title = "SLA monitor"

        self.set_layout()
        self.logic.setup_logic()

    def run_application(self):
        self.application.run_server(debug=self.cnfs.server.debug,
                                    host=self.cnfs.server.host,
                                    port=self.cnfs.server.port)


def nakedserver():
    try:
        slv = SLAMonitor()
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)

    slv.start()


def wsgiserver(*positional, **kw):
    global SLAMON
    try:
        if SLAMON is None:
            slv = SLAMonitor()
            slv.setup_resource()
            slv.setup_application()
            SLAMON = slv
        return SLAMON.application.server(*positional, **kw)
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    nakedserver()
