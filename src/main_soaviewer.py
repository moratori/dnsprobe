#!/usr/bin/env python3

"""
docstring is here
"""

import traceback
import sys
import dash
from dash import dash_table
from dash import html
from dash import dcc

import common.common.framework as framework
import common.data.dao as dao
import logic.viewer.soaviewer as soaviewerlogic


SOAMON = None


class SOAMonitor(framework.SetupwithInfluxdb):

    def __init__(self):
        super().__init__(__name__, __file__)
        self.dao_dnsprobe = dao.Mes_dnsprobe(self)
        self.logic = soaviewerlogic.SOAViewerLogic(self)

    def make_header(self):

        header = html.Div([
            html.H1("SOA Serial Monitor Last 24 hours"),
            dcc.Interval(id="main-content-table-interval",
                         interval=30 * 1000,
                         n_intervals=0)
        ], id="main-content-header")

        return header

    def make_soa_table(self):

        columns = [dict(name="Address Family", id="af"),
                   dict(name="Nameserver", id="dst_name"),
                   dict(name="Transport", id="proto"),
                   dict(name="Probe", id="prb_id"),
                   dict(name="Serial value", id="serial"),
                   dict(name="First measured at(UTC)", id="first_measured_at"),
                   dict(name="Last measured at(UTC)", id="last_measured_at"),
                   dict(name="Period(min)", id="period")]

        soa_table = dash_table.DataTable(
            id="main-content-table",
            filter_action="native",
            columns=columns,
            style_data_conditional=[],
            data=[])

        return soa_table

    def set_layout(self):

        self.application.layout = html.Div([
            self.make_header(),
            self.make_soa_table()
        ])

    def setup_application(self):
        self.application = dash.Dash(__name__)
        self.application.server.url_map.converters["regex"] = \
            soaviewerlogic.RegexConverter
        self.application.css.config.serve_locally = self.cnfs.server.offline
        self.application.scripts.config.serve_locally = \
            self.cnfs.server.offline
        self.application.title = "SOA monitor"

        self.set_layout()
        self.logic.setup_logic()

    def run_application(self):
        self.application.run_server(debug=self.cnfs.server.debug,
                                    host=self.cnfs.server.host,
                                    port=self.cnfs.server.port)


def nakedserver():
    try:
        slv = SOAMonitor()
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)

    slv.start()


def wsgiserver(*positional, **kw):
    global SOAMON
    try:
        if SOAMON is None:
            slv = SOAMonitor()
            slv.setup_resource()
            slv.setup_application()
            SOAMON = slv
        return SOAMON.application.server(*positional, **kw)
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    nakedserver()
