#!/usr/bin/env python3

"""
InfluxDBのline protocolで、テスト用データを作成する
生成したテストデータは、標準出力に出力する
"""

import datetime
import argparse
import itertools


TRANSPORT = ["tcp", "udp"]
AF = [4, 6]
RRTYPE = ["SOA"]


def generate_time_took():
    pass


def generate_data(argument):

    end_time = datetime.datetime.now()
    start_time = \
        end_time - datetime.timedelta(minutes=argument.range_in_minutes)
    probes = ["prb%d" % n for n in range(argument.probes)]
    nameservers = ["srv%d" % n for n in range(argument.nameservers)]

    while (start_time < end_time):
        for (nameserver, probe, af, rrtype) in itertools.product(nameservers,
                                                                 probes,
                                                                 AF,
                                                                 RRTYPE):
            pass
        start_time += datetime.timedelta(minutes=argument.step_in_minutes)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--nameservers", type=int, default=8)
    argparser.add_argument("--probes", type=int, default=20)
    argparser.add_argument("--range-in-minutes", type=int, default=3)
    argparser.add_argument("--step-in-minutes", type=int, default=1)

    generate_data(argparser.parse_args())
