#!/bin/bash
unset EICRECON_HOME
if [ -n "${JANA_PLUGIN_PATH}" ]; then
    export JANA_PLUGIN_PATH=$(echo "${JANA_PLUGIN_PATH}" | sed "s|${CONDA_PREFIX}/lib/EICrecon/plugins:||; s|:${CONDA_PREFIX}/lib/EICrecon/plugins||; s|${CONDA_PREFIX}/lib/EICrecon/plugins||")
    [ -z "${JANA_PLUGIN_PATH}" ] && unset JANA_PLUGIN_PATH
fi
