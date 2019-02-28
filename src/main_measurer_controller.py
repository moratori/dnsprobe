#!/usr/bin/env python3

"""
docstring is here
"""

import common.config as config
import common.framework as framework

import traceback
import sys
import argparse
import flask
from flask import render_template


class MeasurerController(framework.BaseSetup):

    def __init__(self):
        super().__init__(__name__, __file__)
        self.server = flask.Flask(__name__,
                                  static_folder=config.STATIC_DIR,
                                  template_folder=config.TEMPLATES_DIR)
        self.setup_server_route()

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

        self.args = argument_parser.parse_args()
        self.validate_commandline_argument()

    def index(self):
        return render_template("index.tmpl")

    def setup_server_route(self):
        self.server.add_url_rule("/", "index", self.index)

    def run(self):
        self.server.run(host=self.args.host, port=self.args.port)


if __name__ == "__main__":

    try:
        mc = MeasurerController()
        mc.start()
    except Exception:
        # LOGGERのセットアップ自体にも失敗している可能性ありの為
        # 標準出力にログ出力
        print(traceback.format_exc())
        sys.exit(1)
