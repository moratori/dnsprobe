#!/bin/bash

#######################################
CURRENT=$(cd $(dirname $0) && pwd)
PROJECT_ROOT="$(cd ${CURRENT%/}/.. && pwd)"
BIN="${PROJECT_ROOT}/bin"
LOCKS="${PROJECT_ROOT}/jobs/locks"
SOURCES="${PROJECT_ROOT}/src"
TESTS="${PROJECT_ROOT}/test"
VENV="${PROJECT_ROOT}/.venv"
LOGS="${PROJECT_ROOT}/logs"
WSGI_LOG_ROTATION_SIZE=3145728
#######################################

# do for common setting

