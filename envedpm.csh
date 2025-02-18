#!/usr/bin/env csh
# EDPM environment script
setenv GLOBAL_VAR "some_global_value"

# Make sure PATH is set
if ( ! $?PATH ) then
    setenv PATH "/usr/local/global/bin"
else
    setenv PATH "/usr/local/global/bin":${PATH}
endif

# Make sure PYTHONPATH is set
if ( ! $?PYTHONPATH ) then
    setenv PYTHONPATH "/usr/local/global/python"
else
    setenv PYTHONPATH ${PYTHONPATH}:"/usr/local/global/python"
endif
