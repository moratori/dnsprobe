#!/usr/bin/env python3

"""
docstring is here
"""

import os
import dash_core_components as doc
import plotly.graph_objs as go

from dash.dependencies import Input, Output
from flask import abort, Response
from logging import getLogger
from werkzeug.routing import BaseConverter

import common.common.config as config
import common.data.types as types

LOGGER = getLogger(__name__)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


class SLAViewerLogic():

    def __init__(self, slaviewer):
        self.slaviewer = slaviewer

    def setup_logic(self):

        @self.slaviewer.application.server.route(os.path.join(
            "/",
            os.path.basename(config.STATIC_DIR),
            self.slaviewer.cnfs.resource.css_dir,
            '<regex("[a-zA-Z0-9]+\\.css"):stylesheet>'))
        def serve_css(stylesheet):

            LOGGER.info("requested css file \"%s\"" % str(stylesheet))

            try:
                with open(os.path.join(config.STATIC_DIR,
                                       self.slaviewer.cnfs.resource.css_dir,
                                       stylesheet), "r") as handle:
                    return Response(handle.read(), mimetype="text/css")

            except Exception:
                LOGGER.warning("exception while loading css \"%s\"" %
                               str(stylesheet))
                abort(404)

        @self.slaviewer.application.callback(
            Output("main-content-description", "children"),
            [Input("main-content-menu-filter_sl", "value")])
        def update_description(kind):

            if not self.check_supported_service_level(kind):
                LOGGER.warning("unknown service level kind: %s" % str(kind))
                return ""

            try:
                path = os.path.join(config.STATIC_DIR,
                                    self.slaviewer.cnfs.resource.description,
                                    kind)
                with open(path, "r", encoding="utf8") as handle:
                    text = handle.read()
                    return text
            except IOError as ex:
                LOGGER.warning("ioerror occurred: %s" % str(ex))
                return ""

        @self.slaviewer.application.callback(
            Output("main-content-graph-current", "children"),
            [Input("main-content-menu-filter_sl", "value"),
             Input("main-content-graph-interval", "n_intervals")])
        def update_current_graph(kind, n_intervals):

            if not self.check_supported_service_level(kind):
                return []

            graph = doc.Graph(figure=__update_current_graph(kind),
                              style=dict(height=600,
                                         width=1650,
                                         marginTop=0,
                                         marginLeft="auto",
                                         marginRight="auto"),
                              config=dict(displayModeBar=False))

            return [graph]

        def __update_current_graph(kind):
            traces = []

            if kind == types.DNS_name_server_availability.__name__.lower():

                dst_name_versus_af = \
                    self.slaviewer.dao_nameserver_avail.\
                    get_af_dst_name_combination()

                v4_x = []
                v4_y = []
                v6_x = []
                v6_y = []

                for (dst_name, afs) in dst_name_versus_af.items():
                    for af in afs:
                        if af == "4":
                            v4_x.append(dst_name)
                            v4_y.append(self.slaviewer.dao_nameserver_avail.
                                        get_recent_sla(dst_name, af))
                        elif af == "6":
                            v6_x.append(dst_name)
                            v6_y.append(self.slaviewer.dao_nameserver_avail.
                                        get_recent_sla(dst_name, af))
                        else:
                            LOGGER.warning("unexpected address family: %s" %
                                           str(af))

                traces.append(go.Bar(name="v4", x=v4_x, y=v4_y))
                traces.append(go.Bar(name="v6", x=v6_x, y=v6_y))

            else:
                pass

            figure = dict(data=traces,
                          layout=go.Layout(
                              title=kind,
                              showlegend=True,
                              barmode="group",
                              xaxis=dict(title="Authoritative DNS Servers"),
                              yaxis=dict(title="Service Level (%)",
                                         tickmode="linear",
                                         range=[95, 100],
                                         dtick=0.5
                                         ),
                              legend=dict(orientation="h",
                                          font=dict(size=10),
                                          yanchor="top",
                                          x=0,
                                          y=1.075)))

            return figure

        def __update_past_graph(kind):

            if kind == types.DNS_name_server_availability.__name__.lower():
                pass
            else:
                pass

            return dict(data=[])

    def check_supported_service_level(self, kind):
        supprted_list = self.get_supported_service_levels()

        for each in supprted_list:
            if kind == each["value"]:
                return True

        return False

    def get_supported_service_levels(self):

        supprted_list = []

        for cls in types.CalculatedSLA.__subclasses__():
            name = cls.__name__.lower()
            supprted_list.append(dict(label=name, value=name))

        return supprted_list
