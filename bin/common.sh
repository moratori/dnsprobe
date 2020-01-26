#!/bin/bash

#######################################
CURRENT=$(cd $(dirname $0) && pwd)
PROJECT_ROOT="$(cd ${CURRENT%/}/.. && pwd)"
BIN="${PROJECT_ROOT}/bin"
LOCKS="${PROJECT_ROOT}/jobs/locks"
SOURCES="${PROJECT_ROOT}/src"
TESTS="${PROJECT_ROOT}/test"
#######################################

# do for common setting

