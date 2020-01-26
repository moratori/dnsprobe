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

pipenv run find . \
        -type f \
        -name 'test_*.py' \
        -exec ${COVERAGE} run -a --omit ${VENV}/'*' {} \;

pipenv run ${COVERAGE} report --omit ${VENV}/'*'
pipenv run ${COVERAGE} html --omit ${VENV}/'*'

exit 0


