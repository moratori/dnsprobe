#!/usr/bin/env python3

"""
InfluxDBのline protocolで、テスト用データを作成する
生成したテストデータは、標準出力に出力する
"""

import time
import random
import argparse
import itertools


def generate_time_took(transport, threshold_tcp, threshold_udp):

    if transport == "tcp":
        time_took = abs(random.gauss(15.0, threshold_tcp * 1000))
        return time_took < threshold_tcp * 1000, time_took

    if transport == "udp":
        time_took = abs(random.gauss(3.5, threshold_udp * 1000))
        return time_took < threshold_udp * 1000, time_took


def to_nanosecond(timestamp):
    return timestamp * 1000000000


def generate_data(argument):

    end_time = int(time.time())
    start_time = end_time - argument.range_in_minutes * 60

    probes = ["prb%d" % n for n in range(argument.probes)]
    nameservers = ["srv%d" % n for n in range(argument.nameservers)]

    while (start_time < end_time):
        for (nameserver, af, transport, probe) in \
                itertools.product(nameservers,
                                  [4, 6],
                                  ["tcp", "udp"],
                                  probes):

            got_response, time_took = \
                generate_time_took(transport,
                                   argument.threshold_tcp,
                                   argument.threshold_udp)

            got_response_field = 1 if got_response else 0

            print("dnsprobe,dst_name=%s,af=%d,proto=%s,prb_id=%s,got_response=%s time_took=%f,got_response_field=%d %d" %
                  (nameserver,
                   af,
                   transport,
                   probe,
                   got_response,
                   time_took,
                   got_response_field,
                   to_nanosecond(start_time)))

        start_time += argument.step_in_minutes * 60


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--threshold-tcp", type=float, default=7.5)
    argparser.add_argument("--threshold-udp", type=float, default=2.5)
    argparser.add_argument("--nameservers", type=int, default=8)
    argparser.add_argument("--probes", type=int, default=20)
    argparser.add_argument("--range-in-minutes", type=int, default=3)
    argparser.add_argument("--step-in-minutes", type=int, default=1)

    generate_data(argparser.parse_args())
