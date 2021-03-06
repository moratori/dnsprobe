#!/usr/bin/env python3

"""
docstring is here
"""

import traceback
import os
import sys
import json

import common.common.config as config
import common.common.framework as framework
import common.data.types as types
import common.data.dao as dao
import common.net.resolver.rec_resolver as rec_resolver


class CreateMeasurementTarget(framework.SetupwithMySQLdb):

    def __init__(self):
        super().__init__(__name__, __file__)

    def run_application(self):
        measurement_infos = self.retrieve_measurement_info()
        fullresolvers = [self.cnfs.nameserver.primary,
                         self.cnfs.nameserver.secondary]

        result = self.construct_json_data(measurement_infos, fullresolvers)
        self.save_json_data(result)

    def construct_json_data(self, measurement_infos, full_resolvers):

        result = []
        tmp_group_by_nameserver_addr = {}

        fr = rec_resolver.FullResolver(full_resolvers)

        for mi in measurement_infos:
            nameserver = mi.hostname
            af = mi.address_family
            proto = str(mi.transport_protocol)
            qname = mi.qname
            rrtype = mi.rrtype

            if (af, nameserver) not in tmp_group_by_nameserver_addr:
                if af == types.AddressFamily.V4:
                    addr = fr.resolve_a(nameserver)
                elif af == types.AddressFamily.V6:
                    addr = fr.resolve_aaaa(nameserver)
                else:
                    self.logger.warning("address family must be v4 or v6 %s" %
                                        (str(af)))
                    continue
                tmp_group_by_nameserver_addr[(af, nameserver)] = addr
                self.logger.info("%s address for %s is %s" %
                                 (str(af), nameserver, addr))

            addr = tmp_group_by_nameserver_addr[(af, nameserver)]

            result.append(dict(nameserver=nameserver,
                               destination=addr,
                               proto=proto,
                               query=dict(qname=qname, rrtype=rrtype)))

        self.logger.debug("object for json is constructed: %s" % (result))

        return result

    def retrieve_measurement_info(self):
        """
        DB より測定対象のホスト測定クエリ情報を取得する
        """

        measurement_infos = (self.session.query(dao.MeasurementTarget)
                             .order_by(dao.MeasurementTarget.hostname)
                             .all())

        return measurement_infos

    def save_json_data(self, target):
        """
        targetにて表される辞書データをjsonとして、STATIC_DIR配下に保存する
        """

        filebasename = self.cnfs.data.path
        path = os.path.join(config.STATIC_DIR, filebasename)

        with open(path, "w", encoding="utf-8") as handle:
            json.dump(target, handle)

        return


def main():
    try:
        cmt = CreateMeasurementTarget()
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)

    cmt.start()


if __name__ == "__main__":
    main()
