#!/usr/bin/env bash
# EDPM environment script
export GLOBAL_VAR="some_global_value"
export PATH=/usr/local/global/bin${PATH:+:${PATH}}

export PYTHONPATH=${PYTHONPATH:+${PYTHONPATH}:}/usr/local/global/python

