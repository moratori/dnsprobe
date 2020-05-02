#!/usr/bin/env python3

"""
docstring is here
"""

import os
import datetime

from dash.dependencies import Input, Output
from flask import abort, Response
from logging import getLogger
from werkzeug.routing import BaseConverter

import common.common.config as config

LOGGER = getLogger(__name__)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


class SOAViewerLogic():

    def __init__(self, soaviewer):
        self.soaviewer = soaviewer

    def setup_logic(self):

        @self.soaviewer.application.server.route(os.path.join(
            "/",
            os.path.basename(config.STATIC_DIR),
            self.soaviewer.cnfs.resource.css_dir,
            '<regex("[a-zA-Z0-9]+\\.css"):stylesheet>'))
        def serve_css(stylesheet):

            LOGGER.info("requested css file \"%s\"" % str(stylesheet))

            try:
                with open(os.path.join(config.STATIC_DIR,
                                       self.soaviewer.cnfs.resource.css_dir,
                                       stylesheet), "r") as handle:
                    return Response(handle.read(), mimetype="text/css")

            except Exception:
                LOGGER.warning("exception while loading css \"%s\"" %
                               str(stylesheet))
                abort(404)

        @self.soaviewer.application.callback(
            [Output("main-content-table", "data"),
             Output("main-content-table", "style_data_conditional")],
            [Input("main-content-table-interval", "n_intervals")])
        def update_soa_table(n_intervals):

            hours = self.soaviewer.cnfs.application.back_range_in_hours
            data = self.soaviewer.dao_dnsprobe.get_last_measured_soa_data(
                hours)

            max_serial = max([each["serial"] for each in data])

            style = [
                {"if": {
                    "column_id": "serial",
                    "filter_query": "{serial} >= %d" % max_serial},
                 "color": "green"},
                {"if": {
                    "column_id": "serial",
                    "filter_query": "{serial} < %d" % max_serial},
                 "color": "red",
                 "fontWeight": "bold"}]

            return data, style
