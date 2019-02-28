#!/usr/bin/env python

import dns.name
import dns.message
import dns.query

from logging import getLogger

LOGGER = getLogger(__name__)


class DirectQuery(object):

    def __init__(self, dest, source, timeout):
        self.dest = dest
        self.source = source
        self.timeout = timeout

    def resolve_soa_udp(self, domain):
        q = dns.message.make_query(dns.name.from_text(domain),
                                   dns.rdatatype.SOA)
        r = dns.query.udp(q,
                          self.dest,
                          timeout=self.timeout,
                          source=self.source)
        return r

    def resolve_soa_tcp(self, domain):
        q = dns.message.make_query(dns.name.from_text(domain),
                                   dns.rdatatype.SOA)
        r = dns.query.tcp(q,
                          self.dest,
                          timeout=self.timeout,
                          source=self.source)
        return r
