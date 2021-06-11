#!/usr/bin/env python3

"""
docstring is here
"""

import os
import re
import datetime

from dash.dependencies import Input, Output
from flask import abort, Response
from logging import getLogger
from werkzeug.routing import BaseConverter

import common.common.util as util
import common.common.config as config

LOGGER = getLogger(__name__)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


class RateViewerLogic():

    def __init__(self, rateviewer):
        self.rateviewer = rateviewer

    def check_rrtype(self, rrtype):
        if rrtype is None:
            return False
        if re.compile("^[a-zA-Z]+$").findall(rrtype):
            return True
        return False

    def setup_logic(self):

        @self.rateviewer.application.server.route(os.path.join(
            "/",
            os.path.basename(config.STATIC_DIR),
            self.rateviewer.cnfs.resource.css_dir,
            '<regex("[a-zA-Z0-9]+\\.css"):stylesheet>'))
        def serve_css(stylesheet):

            LOGGER.info("requested css file \"%s\"" % str(stylesheet))

            try:
                with open(os.path.join(config.STATIC_DIR,
                                       self.rateviewer.cnfs.resource.css_dir,
                                       stylesheet), "r") as handle:
                    return Response(handle.read(), mimetype="text/css")

            except Exception:
                LOGGER.warning("exception while loading css \"%s\"" %
                               str(stylesheet))
                abort(404)

        @self.rateviewer.application.callback(
            [Output("main-content-table", "data"),
             Output("main-content-table", "style_data_conditional")],
            [Input("main-content-table-interval", "n_intervals"),
             Input("main-content-menu-filter_rrtype", "value")])
        def update_rate_table(n_intervals, rrtype):

            if not self.check_rrtype(rrtype):
                LOGGER.info("argument %s is not properly" % rrtype)
                return []
            
            # 算出対象の時刻を計算
            current_time = datetime.datetime.utcnow()
            hours = self.rateviewer.cnfs.application.back_range_in_hours
            start_time = (current_time - datetime.timedelta(
                seconds=hours * 3600)).isoformat() + "Z"
            end_time = current_time.isoformat() + "Z"
            
            # 対象のプローブを取得
            probe_group = [each["value"]
                           for each in self.rateviewer.dao_dnsprobe.make_probe_group()]
            
            # 測定対象を取得
            target = self.rateviewer.dao_dnsprobe.get_af_dst_name_combination()

            result = []
            for (dst_name, aflist) in target.items():
                for af in aflist:
                    for proto in ["tcp", "udp"]:
                        
                        probe_result = {}
                        for probe in probe_group:
                            success = \
                                self.rateviewer.dao_dnsprobe.get_ratiograph_successful(
                                    dst_name, [probe], af, proto, rrtype, start_time, end_time)
                            exceeded = \
                                self.rateviewer.dao_dnsprobe.get_ratiograph_exceeded_slr(
                                    dst_name, [probe], af, proto, rrtype, start_time, end_time)
                            failed = \
                                self.rateviewer.dao_dnsprobe.get_ratiograph_failed(
                                    dst_name, [probe], af, proto, rrtype, start_time, end_time)
                            denominator = success + exceeded + failed
                            if denominator != 0:
                                percentage = (success / float(denominator)) * 100
                                probe_result[probe.replace("-", "")] = round(percentage,3)
                            else:
                                LOGGER.info("%s %s %s from %s zero counted: " %
                                            (dst_name, af, proto, probe))

                        result.append({
                            **{"af": af, "dst_name": dst_name, "proto": proto},
                            **probe_result})

            style = [{"if": {"column_id": probe.replace("-",""),
                             "filter_query": "{%s} < 100" % probe.replace("-","")},
                      "color": "red",
                      "fontWeight": "bold"} for probe in probe_group]

            return result, style
