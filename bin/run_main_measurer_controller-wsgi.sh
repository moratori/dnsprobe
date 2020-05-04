#!/bin/bash

#######################################
CURRENT=$(cd $(dirname $0) && pwd)
PROJECT_ROOT="$(cd ${CURRENT%/}/.. && pwd)"
BIN="${PROJECT_ROOT}/bin"

. ${BIN}/common.sh

SELF="`basename $0`"
#######################################

cd ${PROJECT_ROOT}

unix_sock="/tmp/dnsprobe_measurer_controller.sock"
wsgi_entry="wsgiserver"
script_name="main_measurer_controller"

pipenv run uwsgi \
        --socket "${unix_sock}" \
        --manage-script-name \
        --chdir "${SOURCES}" \
        --mount "/=${script_name}:${wsgi_entry}" \
        --chmod-socket=777 \
        --logger file:logfile=${LOGS}/${SELF}.wsgi.log,maxsize=${WSGI_LOG_ROTATION_SIZE} \
        > /dev/null 2>&1 &
