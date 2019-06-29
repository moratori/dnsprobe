#!/usr/bin/env python3

"""
docstring is here
"""

import common.common.config as config
import common.common.framework as framework
import common.data.dao as dao
import traceback
import sys
import os
import argparse
import flask
from flask import render_template


MC = None


class MeasurerController(framework.SetupwithMySQLdb):

    def __init__(self):
        super().__init__(__name__, __file__)
        self.server = flask.Flask(__name__,
                                  static_folder=config.STATIC_DIR,
                                  template_folder=config.TEMPLATES_DIR)
        self.setup_server_route()

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

        self.args = argument_parser.parse_args()
        self.validate_commandline_argument()

    def index(self):
        return render_template("index.tmpl")

    def edit_measurement_target(self):

        measurement_infos = (self.session.query(dao.MeasurementTarget)
                             .order_by(dao.MeasurementTarget.hostname)
                             .all())

        data = []
        for m in measurement_infos:
            data.append(dict(hostname=m.hostname,
                             address_family=m.address_family,
                             transport_protocol=m.transport_protocol,
                             qname=m.qname,
                             rrtype=m.rrtype))

        return render_template(os.path.join("edit",
                                            "measurement_target.tmpl"),
                               measurement_infos=data)

    def setup_server_route(self):
        self.server.add_url_rule("/",
                                 "index",
                                 self.index)

        self.server.add_url_rule("/edit/measurement_target",
                                 "edit_measurement_target",
                                 self.edit_measurement_target)

    def run(self):
        self.server.run(host=self.args.host, port=self.args.port)


def nakedserver():
    try:
        mc = MeasurerController()
        mc.start()
    except Exception:
        # LOGGERのセットアップ自体にも失敗している可能性ありの為
        # 標準出力にログ出力
        print(traceback.format_exc())
        sys.exit(1)


def wsgiserver(*positional, **kw):
    global MC
    try:
        if MC is None:
            mc = MeasurerController()
            MC = mc
        return MC.server(*positional, **kw)
    except Exception:
        # LOGGERのセットアップ自体にも失敗している可能性ありの為
        # 標準出力にログ出力
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    nakedserver()
