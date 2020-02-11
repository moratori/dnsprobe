#!/bin/bash

rm -r /tmp/dnsprobe-influxdb-dump-* > /dev/null 2>&1
/usr/bin/influxd backup -portable -database dnsprobe -host 127.0.0.1:8088 "/tmp/dnsprobe-influxdb-dump-`date +"%Y%m%d"`" > /dev/null 2>&1
