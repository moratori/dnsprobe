#!/usr/bin/env python3

"""
テーブルを定義する
"""

import common.common.framework as framework
import common.data.dao as dao

import traceback
import sys


class InitializeDatabase(framework.SetupwithMySQLdb):

    def __init__(self):
        super().__init__(__name__, __file__)

    def run(self, **args):
        dao.Base.metadata.create_all(bind=self.dbengine)


if __name__ == "__main__":

    try:
        initdb = InitializeDatabase()
        initdb.start()
    except Exception:
        # LOGGERのセットアップ自体にも失敗している可能性ありの為
        # 標準出力にログ出力
        print(traceback.format_exc())
        sys.exit(1)
