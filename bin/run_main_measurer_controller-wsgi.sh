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


## If exclusive control is required, please comment out the following
#if ! ln -s $$ "${LOCKS}/${SELF}" > /dev/null 2>&1; then
#    echo "the script ${SELF} seems to be running"
#    echo "aborted"
#    exit 1
#fi


pipenv run uwsgi \
        --socket "${unix_sock}" \
        --manage-script-name \
        --chdir "${SOURCES}" \
        --mount "/=${script_name}:${wsgi_entry}" \
        --chmod-socket=777 > /dev/null 2>&1 &

#return_code=$?
#
#
### If exclusive control is required, please comment out the following
##rm "${LOCKS}/${SELF}"
#
#exit $return_code
