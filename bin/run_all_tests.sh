#!/bin/bash

#######################################
CURRENT=$(cd $(dirname $0) && pwd)
PROJECT_ROOT="$(cd ${CURRENT%/}/.. && pwd)"
BIN="${PROJECT_ROOT}/bin"

. ${BIN}/common.sh

SELF="`basename $0`"
COVERAGE="coverage"
#######################################

cd ${PROJECT_ROOT}
cd ${TESTS}

pipenv run ${COVERAGE} erase

pipenv run ${COVERAGE} run -a --omit ${VENV}/'*' -m unittest discover

pipenv run ${COVERAGE} report --omit ${VENV}/'*'
pipenv run ${COVERAGE} html --omit ${VENV}/'*'

exit 0


