#!/usr/bin/env python3

import unittest
import ipaddress
import re
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import main_measurer_controller as controller
import main_measurer as measurer
import common.data.errors as errors


class TestMainMeasurer(unittest.TestCase):

    def setUp(self):
        self.measurer = measurer.Measurer()

    def tearDown(self):
        pass

    def test_0_set_measurer_id(self):
        id_pattern = re.compile("^[a-z][a-z][a-z]\-[0-9]+$")
        self.measurer.set_measurer_id()
        self.assertTrue(id_pattern.findall(self.measurer.measurer_id))

    def test_1_set_global_ipaddress(self):
        self.measurer.set_global_ipaddress()
        if self.measurer.ipv4 is not None:
            self.assertTrue(ipaddress.ip_address(
                self.measurer.ipv4).is_global)
        else:
            self.assertIsNone(self.measurer.ipv4)
        if self.measurer.ipv6 is not None:
            self.assertTrue(ipaddress.ip_address(
                self.measurer.ipv6).is_global)
        else:
            self.assertIsNone(self.measurer.ipv6)

    def test_2_set_server_boottime(self):
        self.measurer.set_server_boottime()
        pat = re.compile("^[0-9]{4}\-[0-9]{2}\-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$")
        self.assertTrue(pat.findall(self.measurer.server_boottime))

    def test_3_validate_id(self):
        self.measurer.set_global_ipaddress()
        if self.measurer.ipv4 is None or self.measurer.ipv6 is None:
            self.assertRaises(errors.DNSProbeError,
                              self.measurer.validate_id)
