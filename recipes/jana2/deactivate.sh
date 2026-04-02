#!/bin/bash
unset JANA_HOME
if [ -n "${JANA_PLUGIN_PATH}" ]; then
    export JANA_PLUGIN_PATH=$(echo "${JANA_PLUGIN_PATH}" | sed "s|${CONDA_PREFIX}/lib/JANA/plugins:||; s|:${CONDA_PREFIX}/lib/JANA/plugins||; s|${CONDA_PREFIX}/lib/JANA/plugins||")
    [ -z "${JANA_PLUGIN_PATH}" ] && unset JANA_PLUGIN_PATH
fi
