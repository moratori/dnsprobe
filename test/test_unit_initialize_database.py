#!/usr/bin/env python3

import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import main_initialize_database as idb
import common.data.dao as dao
import common.common.framework as framework


class TestInitializeDatabase(framework.SetupwithMySQLdb,
                             unittest.TestCase):

    def __init__(self, *positional, **keyword):
        framework.SetupwithMySQLdb.__init__(self, __name__, __file__)
        unittest.TestCase.__init__(self, *positional, **keyword)

    def setUp(self):
        self.idb = idb.InitializeDatabase()
        self.idb.setup_resource()
        self.idb.setup_application()

    def tearDown(self):
        self.idb.teardown_application()
        self.idb.teardown_resource()

    def test_0_run(self):
        self.idb.run_application()

        self.setup_resource()

        measurement_infos = (self.session.query(dao.MeasurementTarget)
                             .all())

        self.assertTrue(len(measurement_infos) >= 0)

        self.teardown_resource()

