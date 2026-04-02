#!/bin/bash
unset DD4HEP_DIR
if [ -n "${ROOT_INCLUDE_PATH}" ]; then
    export ROOT_INCLUDE_PATH=$(echo "${ROOT_INCLUDE_PATH}" | sed "s|${CONDA_PREFIX}/include:||; s|:${CONDA_PREFIX}/include||; s|${CONDA_PREFIX}/include||")
    [ -z "${ROOT_INCLUDE_PATH}" ] && unset ROOT_INCLUDE_PATH
fi
