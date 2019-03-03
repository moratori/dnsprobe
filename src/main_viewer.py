#!/usr/bin/env python3

"""
docstring is here
"""

import common.config as config
import common.framework as framework
import data.dao as dao
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

    def run(self):
        application = dash.Dash()
        application.css.config.serve_locally = self.args.offline
        application.scripts.config.serve_locally = self.args.offline

        application.layout = html.Div(children=[
            html.H1(children='Hello Dash'),
            html.Div(children='''
                Dash: A web application framework for Python.'''),
            doc.Graph(
                id='example-graph',
                figure={
                    'data': [
                        {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                        {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
                    ],
                    'layout': {
                        'title': 'Dash Data Visualization'
                    }
                }
            )
        ])

        application.run_server(debug=self.args.debug,
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
