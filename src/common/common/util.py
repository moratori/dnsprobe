#!/usr/bin/env python3

"""
docstring
"""

import datetime
from logging import getLogger

LOGGER = getLogger(__name__)


def parse_influx_string_time_to_datetime(string_time):
    LOGGER.debug("date time in string: %s" % string_time)

    index = string_time.find(".")

    if -1 < index:
        stripped = string_time[:index]
        return datetime.datetime.fromisoformat(stripped)
    else:
        return datetime.datetime.fromisoformat(string_time)
