#!/usr/bin/env python3

"""
docstring is here
"""

import traceback
import sys
import os
import flask
from flask import render_template

import common.common.config as config
import common.common.framework as framework
import common.data.dao as dao


MC = None


class MeasurerController(framework.SetupwithMySQLdb):

    def __init__(self):
        super().__init__(__name__, __file__)
        self.server = flask.Flask(__name__,
                                  static_folder=config.STATIC_DIR,
                                  template_folder=config.TEMPLATES_DIR)

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

    def setup_application(self):
        self.server.add_url_rule("/",
                                 "index",
                                 self.index)

        self.server.add_url_rule("/edit/measurement_target",
                                 "edit_measurement_target",
                                 self.edit_measurement_target)

    def run_application(self):
        self.server.run(host=self.cnfs.server.host,
                        port=self.cnfs.server.port)


def nakedserver():
    try:
        mc = MeasurerController()
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)

    mc.start()


def wsgiserver(*positional, **kw):
    global MC
    try:
        if MC is None:
            mc = MeasurerController()
            mc.setup_resource()
            mc.setup_application()
            MC = mc
        return MC.server(*positional, **kw)
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    nakedserver()
