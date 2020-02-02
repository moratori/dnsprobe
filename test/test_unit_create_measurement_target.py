#!/usr/bin/env python3

import unittest
import re
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import main_create_measurement_target as cmt
import common.data.dao as dao
import common.data.types as types


class TestMainCreateMeasurementTarget(unittest.TestCase):

    def setUp(self):
        self.cmt = cmt.CreateMeasurementTarget()
        self.full_resolvers = ["192.168.1.1", "8.8.8.8", "1.1.1.1"]

    def tearDown(self):
        pass

    def test_0_construct_json_data(self):

        self.assertTrue(len(
            self.cmt.construct_json_data([], self.full_resolvers)) == 0)

    def test_1_construct_json_data(self):

        mes_info1 = dao.MeasurementTarget()
        mes_info1.hostname = "a.dns.jp"
        mes_info1.address_family = types.AddressFamily.V4
        mes_info1.transport_protocol = types.TransportProtocol.UDP
        mes_info1.qname = "jp"
        mes_info1.rrtype = "SOA"

        measurements_infos = [mes_info1]

        self.assertTrue(self.cmt.construct_json_data(measurements_infos,
                                                     self.full_resolvers))

    def test_2_construct_json_data(self):

        mes_info1 = dao.MeasurementTarget()
        mes_info1.hostname = "a.dns.jp"
        mes_info1.address_family = types.AddressFamily.V4
        mes_info1.transport_protocol = types.TransportProtocol.UDP
        mes_info1.qname = "jp"
        mes_info1.rrtype = "SOA"

        mes_info2 = dao.MeasurementTarget()
        mes_info2.hostname = "b.dns.jp"
        mes_info2.address_family = types.AddressFamily.V4
        mes_info2.transport_protocol = types.TransportProtocol.TCP
        mes_info2.qname = "jp"
        mes_info2.rrtype = "NS"

        measurements_infos = [mes_info1,
                              mes_info2]

        self.assertTrue(self.cmt.construct_json_data(measurements_infos,
                                                     self.full_resolvers))
