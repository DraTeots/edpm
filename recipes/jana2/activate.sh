#!/bin/bash
export JANA_HOME="${CONDA_PREFIX}"
export JANA_PLUGIN_PATH="${CONDA_PREFIX}/lib/JANA/plugins:${JANA_PLUGIN_PATH:-}"
