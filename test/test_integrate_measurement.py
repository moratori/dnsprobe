#!/usr/bin/env python3

import unittest
import sys
import os
import multiprocessing as mp
import itertools
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))


import main_create_measurement_target as cmt
import main_initialize_database as idb
import main_measurer as measurer
import main_measurer_controller as mc

import common.data.dao as dao
import common.data.types as types
import common.common.framework as framework


class TestIntegrateMeasurement(framework.SetupwithMySQLdb,
                               unittest.TestCase):

    def __init__(self, *positional, **keyword):
        framework.SetupwithMySQLdb.__init__(self, __name__, __file__)
        unittest.TestCase.__init__(self, *positional, **keyword)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_0_scenario(self):

        # initialize table
        # todo: rewrite not to use multiprocessing
        idb_process = mp.Process(target=idb.main)
        idb_process.start()
        idb_process.join()
        self.assertTrue(idb_process.exitcode == 0)

        # insert some data to table
        hostnames = ["a.dns.jp",
                     "b.dns.jp",
                     "c.dns.jp",
                     "d.dns.jp",
                     "e.dns.jp",
                     "f.dns.jp",
                     "g.dns.jp",
                     "h.dns.jp"]
        transport_protocols = [types.TransportProtocol.UDP,
                               types.TransportProtocol.TCP]
        rrtypes = ["SOA", "NS", "DNSKEY"]

        datum = []
        for (hostname, proto, rrtype) in itertools.product(hostnames,
                                                           transport_protocols,
                                                           rrtypes):
            datum.append(dao.MeasurementTarget(
                hostname=hostname,
                address_family=types.AddressFamily.V4,
                transport_protocol=proto,
                qname="jp",
                rrtype=rrtype))

        self.setup_resource()
        self.session.query(dao.MeasurementTarget).delete()
        self.session.add_all(datum)
        self.session.commit()

        # create measurement target
        self.cmt = cmt.CreateMeasurementTarget()
        self.cmt.setup_resource()

        measurement_infos = self.cmt.retrieve_measurement_info()
        self.assertTrue(measurement_infos)
        result = self.cmt.construct_json_data(measurement_infos,
                                              ["192.168.1.1"])
        self.assertTrue(result)
        self.cmt.save_json_data(result)
        self.cmt.teardown_resource()

        # start measurement controller
        mc_process = mp.Process(target=mc.nakedserver)
        mc_process.start()
        time.sleep(5)

        # measurer
        for _ in range(3):
            mes = measurer.Measurer()
            mes.setup_resource()
            mes.set_measurer_id()
            mes.set_global_ipaddress()
            mes.ipv4 = "10.0.2.15"
            mes.set_server_boottime()
            mes.set_net_description()
            self.assertFalse(hasattr(mes, "measurement_info"))
            mes.load_measurement_info()
            self.assertTrue(hasattr(mes, "measurement_info"))

            mes.dao_dnsprobe = dao.Mes_dnsprobe(mes)

            self.assertTrue(mes.run_application() == 0)

            mes.teardown_application()
            mes.teardown_resource()
            time.sleep(0.5)

        # terminate measurement controller
        mc_process.terminate()
