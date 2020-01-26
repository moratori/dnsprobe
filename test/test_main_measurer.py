#!/usr/bin/env python3

import unittest
import time
import multiprocessing as mp
import ipaddress
import re
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import src.main_measurer_controller as controller
import src.main_measurer as measurer


class TestMainMeasurer(unittest.TestCase):

    def setUp(self):

        self.controller = mp.Process(target=controller.nakedserver,
                                     args=())
        self.controller.start()

        time.sleep(4)

        self.measurer = measurer.Measurer()

    def tearDown(self):
        self.controller.terminate()

    def test_set_measurer_id(self):
        id_pattern = re.compile("^[a-z][a-z][a-z]\-[0-9]+$")
        self.measurer.set_measurer_id()
        self.assertTrue(id_pattern.findall(self.measurer.measurer_id))

    def test_set_global_ipaddress(self):
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

