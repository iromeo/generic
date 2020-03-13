#!/bin/bash
# +++++++++++++++++++++++++++++++++++++++++++++
# invoke with --jobscript

# Propagate TMPDIR for LSF nodes:
if [ -n "$__LSF_JOB_TMPDIR__" ]; then
  export TMPDIR=$__LSF_JOB_TMPDIR__
fi

# Snakemake job properties:

# properties = {properties}

# Snakemake job script:

{exec_job}

# +++++++++++++++++++++++++++++++++++++++++++++