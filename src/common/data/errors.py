#!/usr/bin/env python


class DNSProbeError(Exception):

    def __init__(self, message):
        self.message = message
