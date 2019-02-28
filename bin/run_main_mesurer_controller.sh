#!/bin/bash

#######################################
CURRENT=$(cd $(dirname $0) && pwd)
PROJECT_ROOT="${CURRENT%/}/.."
BIN="${PROJECT_ROOT}/bin"

. ${BIN}/common.sh

SELF="`basename $0`"
#######################################

cd ${PROJECT_ROOT}


## If exclusive control is required, please comment out the following
#if ! ln -s $$ "${LOCKS}/${SELF}" > /dev/null 2>&1; then
#    echo "the script ${SELF} seems to be running"
#    echo "aborted"
#    exit 1
#fi


pipenv run ${SOURCES}/main_measurer_controller.py $@
return_code=$?

## If exclusive control is required, please comment out the following
#rm "${LOCKS}/${SELF}"

exit $return_code


