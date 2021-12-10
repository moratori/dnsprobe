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
import logic.viewer.rateviewer as rateviewerlogic


RATEMON = None


class RateMonitor(framework.SetupwithInfluxdb):

    def __init__(self):
        super().__init__(__name__, __file__)
        self.dao_dnsprobe = dao.Mes_dnsprobe(self)
        self.logic = rateviewerlogic.RateViewerLogic(self)

    def make_header(self):

        header = html.Div([
            html.H1("Overview of Successful Response Rate Last 24 hours"),
            dcc.Interval(id="main-content-table-interval",
                         interval=30 * 1000,
                         n_intervals=0)
        ], id="main-content-header")

        return header

    def make_description(self):

        text = """This tool displays the successful response rate for each DNS server for the past 24 hours.
A successful response means that the RTT of the query is less than 1.5 seconds for TCP and 
less than 0.5 seconds for UDP. For more information, please refer the following tool : """

        description = html.Div([
            html.H2("Description"),
            html.Div([text, html.A("https://rtt.dns.mtcq.jp/", href="https://rtt.dns.mtcq.jp/")],
                     id="main-content-description",
                     style=dict(whiteSpace="pre-wrap",
                                display="inline-block")) ])
        return description

    def make_menu(self):
        rrtype_group = self.dao_dnsprobe.make_rrtype_group()
        default_rrtype = None

        if rrtype_group:
            default_rrtype = rrtype_group[0]["value"]

        menu = html.Div([
            html.Div([
                "Filter by Resource Record type:",
                dcc.Dropdown(id="main-content-menu-filter_rrtype",
                             options=rrtype_group,
                             value=default_rrtype,
                             multi=False)],
                     style=dict(display="inline-block",
                                width="32%",
                                marign="auto",
                                marginTop="0%",
                                marginRight="1%",
                                marginLeft="1%"))],
                        id="main-content-menu",
                        style=dict(marginBottom="1.5%"))
        
        return menu

    def make_rate_table(self):

        probe_group = [dict(name="Measured From %s" % each["value"],
                            id=each["value"].replace("-", "")) 
                       for each in self.dao_dnsprobe.make_probe_group()]

        columns = [dict(name="Address Family", id="af"),
                   dict(name="Nameserver", id="dst_name"),
                   dict(name="Transport", id="proto")] + probe_group

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
            self.make_description(),
            html.H2("Overview"),
            self.make_menu(),
            self.make_rate_table()
        ])

    def setup_application(self):
        self.application = dash.Dash(__name__)
        self.application.server.url_map.converters["regex"] = \
            rateviewerlogic.RegexConverter
        self.application.css.config.serve_locally = self.cnfs.server.offline
        self.application.scripts.config.serve_locally = \
            self.cnfs.server.offline
        self.application.title = "RATE monitor"

        self.set_layout()
        self.logic.setup_logic()

    def run_application(self):
        self.application.run_server(debug=self.cnfs.server.debug,
                                    host=self.cnfs.server.host,
                                    port=self.cnfs.server.port)


def nakedserver():
    try:
        slv = RateMonitor()
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)

    slv.start()


def wsgiserver(*positional, **kw):
    global RATEMON
    try:
        if RATEMON is None:
            slv = RateMonitor()
            slv.setup_resource()
            slv.setup_application()
            RATEMON = slv
        return RATEMON.application.server(*positional, **kw)
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    nakedserver()
