#!/bin/bash
# +++++++++++++++++++++++++++++++++++++++++++++
# invoke with --jobscript

# Propagate TMPDIR for LSF nodes:

if [ -z "$__LSF_JOB_CUSTOM_TMPDIR__" ]
then
  # $__LSF_JOB_CUSTOM_TMPDIR__ is empty or not set:
  if [[ ! -z "$__LSF_JOB_TMPDIR__" ]]; then
    echo 'Set TMPDIR from $__LSF_JOB_TMPDIR__'
    export TMPDIR=$__LSF_JOB_TMPDIR__
  fi
else
  # # $__LSF_JOB_CUSTOM_TMPDIR__ is set and NOT empty
  export TMPDIR=$__LSF_JOB_CUSTOM_TMPDIR__
  echo 'Set TMPDIR from $__LSF_JOB_CUSTOM_TMPDIR__'
fi

echo "Job uses tempdir: TMPDIR=$TMPDIR"

# Snakemake job properties:

# properties = {properties}

# Snakemake job script:

{exec_job}

# +++++++++++++++++++++++++++++++++++++++++++++