#!/usr/bin/env python3

import unittest
import time
import multiprocessing as mp
import re

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
