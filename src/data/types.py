#!/usr/bin/env python

import enum
from logging import getLogger

LOGGER = getLogger(__name__)


class TransportProtocol(enum.Enum):

    TCP = enum.auto()
    UDP = enum.auto()

    def __str__(self):
        return "%s" % (self.name.lower())


class AddressFamily(enum.Enum):

    V4 = enum.auto()
    V6 = enum.auto()

    def __str__(self):
        return "%s" % (self.name.lower())
