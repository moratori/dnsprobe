#!/usr/bin/env python3

import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import main_calculate_sla as calculator


class TestMainCalculateSLA(unittest.TestCase):

    def setUp(self):
        self.calc = calculator.SLACalculator()
        self.calc.setup_resource()
        self.calc.setup_application()

    def tearDown(self):
        self.calc.teardown_application()
        self.calc.teardown_resource()

    def test_0_calculate_DNS_name_server_availability(self):
        ret = self.calc.calculate_DNS_name_server_availability()
        self.assertTrue(ret is None)
