#!/usr/bin/env python3

import unittest
import ipaddress
import re
import sys
import os
import datetime
import multiprocessing as mp
import time
import dns.query
import namedtupled

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import main_measurer as measurer
import main_measurer_controller as mc
import common.data.errors as errors


class TestMainMeasurer(unittest.TestCase):

    def setUp(self):
        self.measurer = measurer.Measurer()
        self.measurer.setup_resource()

    def tearDown(self):
        self.measurer.teardown_resource()

    def test_0_set_measurer_id(self):
        id_pattern = re.compile("^[a-z][a-z][a-z]\-[0-9]+$")
        self.measurer.set_measurer_id()
        self.assertTrue(id_pattern.findall(self.measurer.measurer_id))

    def test_1_set_global_ipaddress(self):
        self.measurer.set_global_ipaddress()
        if self.measurer.ipv4 is not None:
            self.assertTrue(ipaddress.ip_address(
                self.measurer.ipv4).is_global)
        else:
            self.assertIsNone(self.measurer.ipv4)
        if self.measurer.ipv6 is not None:
            self.assertTrue(ipaddress.ip_address(
                self.measurer.ipv6).is_global)
        else:
            self.assertIsNone(self.measurer.ipv6)

    def test_2_set_server_boottime(self):
        self.measurer.set_server_boottime()
        pat = re.compile("^[0-9]{4}\-[0-9]{2}\-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$")
        self.assertTrue(pat.findall(self.measurer.server_boottime))

    def test_3_validate_id(self):
        self.measurer.set_global_ipaddress()
        if self.measurer.ipv4 is None or self.measurer.ipv6 is None:
            self.assertRaises(errors.DNSProbeError,
                              self.measurer.validate_id)

    def test_4_set_net_description(self):
        self.measurer.set_global_ipaddress()
        self.measurer.set_net_description()
        v4_asn, v4_desc = self.measurer.net_desc_v4
        v6_asn, v6_desc = self.measurer.net_desc_v6
        self.assertIsInstance(v4_asn, str)
        self.assertIsInstance(v4_desc, str)
        self.assertIsInstance(v6_asn, str)
        self.assertIsInstance(v6_desc, str)

    def test_5_load_measurement_info(self):
        proc = mp.Process(target=mc.nakedserver)

        proc.start()
        time.sleep(4)

        self.measurer.load_measurement_info()
        self.assertTrue(hasattr(self.measurer, "measurement_info"))
        self.assertTrue(len(self.measurer.measurement_info) >= 0)

        proc.terminate()

    def test_6_load_measurement_info(self):
        self.assertRaises(errors.DNSProbeError, 
                          self.measurer.load_measurement_info)
        self.assertFalse(hasattr(self.measurer, "measurement_info"))

    def test_7_measurement_core(self):

        self.measurer.set_measurer_id()
        self.measurer.set_server_boottime()

        current_time = str(datetime.datetime.utcnow().isoformat()) + "Z"
        nameserver = "a.dns.jp"
        queryer = dns.query.udp
        addr = "203.119.1.1"
        source = "10.0.2.15"  # rewrite addr depending on test environment
        version = 4
        asn = "ASXXXX"
        asn_desc = "test AS"
        timeout = 2.5
        protocol = "udp"
        qname = "jp"
        rrtype = "SOA"

        qo = dns.message.make_query(dns.name.from_text(qname),
                                    dns.rdatatype.from_text(rrtype),
                                    use_edns=True)
        qo.flags &= 0xFEFF
        qo.use_edns(edns=0,
                    options=[dns.edns.GenericOption(dns.edns.NSID,
                                                    bytes())])
        self.assertTrue(self.measurer.measurement_core(
            current_time,
            nameserver,
            queryer,
            addr,
            source,
            version,
            asn,
            asn_desc,
            timeout,
            protocol,
            qname,
            rrtype,
            qo,
            500))

    def test_8_measurement_core(self):

        self.measurer.set_measurer_id()
        self.measurer.set_server_boottime()

        current_time = str(datetime.datetime.utcnow().isoformat()) + "Z"
        nameserver = "a.dns.jp"
        queryer = dns.query.tcp
        addr = "203.119.1.1"
        source = "10.0.2.15"  # rewrite addr depending on test environment
        version = 4
        asn = "ASXXXX"
        asn_desc = "test AS"
        timeout = 2.5
        protocol = "tcp"
        qname = "jp"
        rrtype = "SOA"

        qo = dns.message.make_query(dns.name.from_text(qname),
                                    dns.rdatatype.from_text(rrtype),
                                    use_edns=True)
        qo.flags &= 0xFEFF
        qo.use_edns(edns=0,
                    options=[dns.edns.GenericOption(dns.edns.NSID,
                                                    bytes())])
        self.assertTrue(self.measurer.measurement_core(
            current_time,
            nameserver,
            queryer,
            addr,
            source,
            version,
            asn,
            asn_desc,
            timeout,
            protocol,
            qname,
            rrtype,
            qo,
            1500))

    def test_9_measurement_core(self):

        self.measurer.set_measurer_id()
        self.measurer.set_server_boottime()

        current_time = str(datetime.datetime.utcnow().isoformat()) + "Z"
        nameserver = "a.dns.jp"
        queryer = dns.query.tcp
        addr = "203.119.1.1"
        source = "10.0.2.15"  # rewrite addr depending on test environment
        version = 4
        asn = "ASXXXX"
        asn_desc = "test AS"
        timeout = 0
        protocol = "tcp"
        qname = "jp"
        rrtype = "SOA"

        qo = dns.message.make_query(dns.name.from_text(qname),
                                    dns.rdatatype.from_text(rrtype),
                                    use_edns=True)
        qo.flags &= 0xFEFF
        qo.use_edns(edns=0,
                    options=[dns.edns.GenericOption(dns.edns.NSID,
                                                    bytes())])
        self.assertTrue(self.measurer.measurement_core(
            current_time,
            nameserver,
            queryer,
            addr,
            source,
            version,
            asn,
            asn_desc,
            timeout,
            protocol,
            qname,
            rrtype,
            qo,
            1500))

    def test_10_measurement_toplevel(self):
        raw_measurement_info = [
            {"nameserver": "a.dns.jp",
             "destination": [
                 "203.119.1.1"],
             "proto": "udp",
             "query": {
                 "qname": "jp",
                 "rrtype": "SOA"
             }
            },
            {"nameserver": "a.dns.jp",
             "destination": [
                 "203.119.1.1"
             ],
             "proto": "tcp",
             "query": {
                 "qname": "jp",
                 "rrtype": "SOA"
             }}]

        self.measurer.measurement_info = namedtupled.map(raw_measurement_info)
        self.measurer.set_measurer_id()
        self.measurer.set_server_boottime()
        self.measurer.ipv4 = "10.0.2.15"  # rewrite addr depending on test environment
        self.measurer.net_desc_v4 = ("", "")

        self.assertTrue(
            self.measurer.measure_toplevel())
