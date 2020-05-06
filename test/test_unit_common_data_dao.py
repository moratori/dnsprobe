#!/usr/bin/env python3

import unittest
import sys
import os
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import common.common.framework as framework
import common.data.dao as dao


class TestCommonDataDao(unittest.TestCase,
                        framework.SetupwithInfluxdb):

    def __init__(self, *positional, **keyword):
        framework.SetupwithInfluxdb.__init__(self, __name__, __file__)
        unittest.TestCase.__init__(self, *positional, **keyword)

    def setUp(self):
        self.setup_resource()
        self.dao_dnsprobe = dao.Dnsprobe(self)
        self.dao_mes_cq_nameserver_availability = \
            dao.MES_CQ_Nameserver_Availability(self)

    def tearDown(self):
        self.teardown_resource()

    def test_0_make_authoritative_group(self):
        self.assertTrue(self.dao_dnsprobe.make_authoritative_group())

    def test_1_make_probe_group(self):
        self.assertTrue(self.dao_dnsprobe.make_probe_group())

    def test_2_make_rrtype_group(self):
        self.assertTrue(self.dao_dnsprobe.make_rrtype_group())

    def test_3_make_probe_locations(self):
        self.assertTrue(self.dao_dnsprobe.make_probe_locations())

    def test_4_get_probe_last_measured(self):
        for (label, probe_id) in self.dao_dnsprobe.make_probe_group():
            self.assertTrue(self.dao_dnsprobe.get_probe_last_measured(
                probe_id))

    def test_5_get_probe_uptime(self):
        for (label, probe_id) in self.dao_dnsprobe.make_probe_group():
            self.assertTrue(self.dao_dnsprobe.get_probe_uptime(probe_id))

    def test_6_get_probe_net_desc(self):
        for (label, probe_id) in self.dao_dnsprobe.make_probe_group():
            self.assertTrue(self.dao_dnsprobe.get_probe_net_desc(probe_id))

    def test_7_get_af_proto_combination(self):
        self.assertTrue(self.dao_dnsprobe.get_af_proto_combination(
            "a.dns.jp",
            ["sjc-3640367842", "tyo-3583024419"]))

    def test_8_get_percentile_data(self):
        current_time = datetime.datetime.utcnow()
        start_time = current_time - datetime.timedelta(seconds=3600*5)
        end_time = current_time

        self.assertTrue(isinstance(
            self.dao_dnsprobe.get_percentilegraph_data(
                "a.dns.jp",
                ["sjc-3640367842", "tyo-3583024419"],
                "SOA",
                start_time.isoformat() + "Z",
                end_time.isoformat() + "Z"),
            dict))

    def test_9_get_af_dst_name_combination(self):
        self.assertTrue(isinstance(
            self.dao_mes_cq_nameserver_availability.get_af_dst_name_combination(),
            dict))
