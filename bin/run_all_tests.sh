#!/bin/bash

#######################################
CURRENT=$(cd $(dirname $0) && pwd)
PROJECT_ROOT="${CURRENT%/}/.."
BIN="${PROJECT_ROOT}/bin"

. ${BIN}/common.sh

SELF="`basename $0`"
COVERAGE="coverage"
#######################################

cd ${PROJECT_ROOT}
cd ${TESTS}

pipenv run ${COVERAGE} erase

pipenv run find . -type f -name "test_*.py" -exec ${COVERAGE} run -a {} \;

pipenv run ${COVERAGE} report
pipenv run ${COVERAGE} html

exit 0


