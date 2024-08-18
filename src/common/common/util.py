#!/usr/bin/env python3

"""
docstring
"""

import datetime
from collections import namedtuple
from logging import getLogger

LOGGER = getLogger(__name__)


def recursive_namedtuple(data, name='NT'):
    if isinstance(data, dict):
        # 辞書のキーからnamedtupleのフィールド名を作成
        fields = {k: recursive_namedtuple(v, k) for k, v in data.items()}
        # 名前付きタプルを作成
        return namedtuple(name, fields.keys())(**fields)
    elif isinstance(data, list):
        # リスト内の要素を再帰的に変換
        return [recursive_namedtuple(item) for item in data]
    else:
        # 辞書でもリストでもない場合、そのまま値を返す
        return data


def parse_influx_string_time_to_datetime(string_time):
    LOGGER.debug("date time in string: %s" % string_time)

    index = string_time.find(".")

    if -1 < index:
        stripped = string_time[:index]
        return datetime.datetime.fromisoformat(stripped)
    else:
        return datetime.datetime.fromisoformat(string_time)
