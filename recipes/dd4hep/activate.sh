#!/bin/bash
export DD4HEP_DIR="${CONDA_PREFIX}"
export ROOT_INCLUDE_PATH="${CONDA_PREFIX}/include:${ROOT_INCLUDE_PATH:-}"
if [ -f "${CONDA_PREFIX}/bin/thisdd4hep_only.sh" ]; then
    source "${CONDA_PREFIX}/bin/thisdd4hep_only.sh"
fi
