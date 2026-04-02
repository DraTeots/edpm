#!/bin/bash
export EICRECON_HOME="${CONDA_PREFIX}"
export JANA_PLUGIN_PATH="${CONDA_PREFIX}/lib/EICrecon/plugins:${JANA_PLUGIN_PATH:-}"
