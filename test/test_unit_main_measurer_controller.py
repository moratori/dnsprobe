#!/usr/bin/env python3

import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import main_measurer_controller as mc


class TestMainMeasurerController(unittest.TestCase):

    def setUp(self):
        self.mc = mc.MeasurerController()
        self.mc.setup_resource()
        self.mc.setup_application()

        self.client = self.mc.server.test_client()

    def tearDown(self):
        self.mc.teardown_application()
        self.mc.teardown_resource()

    def test_0_index(self):
        ret = self.client.get("/")
        self.assertTrue(ret)

    def test_1_edit_measurement_target(self):
        ret = self.client.get("/edit/measurement_target")
        self.assertTrue(ret)

    def test_2_static_data_measurement_info(self):
        ret = self.client.get("/static/data/measurement_info.json")
        self.assertTrue(ret)

