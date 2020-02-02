#!/bin/bash

#######################################
CURRENT=$(cd $(dirname $0) && pwd)
PROJECT_ROOT="$(cd ${CURRENT%/}/.. && pwd)"
BIN="${PROJECT_ROOT}/bin"

. ${BIN}/common.sh

SELF="`basename $0`"
COVERAGE="coverage"
COVERAGE_BADGE="coverage-badge"
#######################################

cd ${PROJECT_ROOT}
cd ${TESTS}

pipenv run ${COVERAGE} erase

pipenv run ${COVERAGE} run -a --omit ${VENV}/'*' -m unittest discover

pipenv run ${COVERAGE} report --omit ${VENV}/'*'
pipenv run ${COVERAGE} html --omit ${VENV}/'*'

pipenv run ${COVERAGE_BADGE} -fo ${PROJECT_ROOT}/coverage.svg

exit 0


