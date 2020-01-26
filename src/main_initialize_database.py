#!/usr/bin/env python3

"""
テーブルを定義する
"""

import traceback
import sys

import common.common.framework as framework
import common.data.dao as dao


class InitializeDatabase(framework.SetupwithMySQLdb):

    def __init__(self):
        super().__init__(__name__, __file__)

    def run(self, **args):
        dao.Base.metadata.create_all(bind=self.dbengine)


if __name__ == "__main__":

    try:
        initdb = InitializeDatabase()
    except Exception:
        print(traceback.format_exc())
        sys.exit(1)

    initdb.start()
