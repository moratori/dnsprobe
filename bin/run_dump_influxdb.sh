#!/bin/bash

basename="/tmp/dnsprobe-influxdb-dump"
bkdirname="${basename}-`date +"%Y%m%d"`"

rm -r ${basename}-* > /dev/null 2>&1
/usr/bin/influxd backup -portable -database dnsprobe -host 127.0.0.1:8088 ${bkdirname} > /dev/null 2>&1

chmod 755 "${bkdirname}"
chmod 666 ${bkdirname}/*
