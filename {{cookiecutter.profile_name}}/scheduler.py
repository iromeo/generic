#!/usr/bin/env python3

import re
import sys
import os
import shlex
from subprocess import Popen, PIPE


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# let snakemake read job_properties
from snakemake.utils import read_job_properties

jobscript = sys.argv[1]
job_properties = read_job_properties(jobscript)

# process pid
job_properties['pid'] = os.getpid()

# default parameters defined in cluster_spec (accessed via snakemake read_job_properties)
cluster_param = job_properties["cluster"]

# 'rule' isn't defined for group jobs
cluster_param['name'] = job_properties.get(
    'rule',  # try rule name
    job_properties.get(
        'groupid',  # try as group
        job_properties['jobid']  # should always work
    )
)

# log is array, so take first file if log option is provided
# and the array isn't empty (job_properties could contain empty array
#  if log section isn't provided by rule)
if job_properties.get('log', []):
    cluster_param['log'] = job_properties['log'][0]
else:
    # if log not specified put job logs into 'cluster_logs' folder
    cluster_param['log'] = "job_log.{}.{}.log".format(
        cluster_param['name'], job_properties['jobid'],
    )

# overwrite default parameters if defined in rule (or config file)
if 'threads' in job_properties:
    cluster_param["threads"] = job_properties["threads"]

# resource options overrides defaults:
for key in job_properties["resources"]:
    cluster_param[key] = job_properties["resources"][key]

# params overrides defaults. 'params' section isn't available for job groups
# e.g.
# 1. add 'rule_params_options: email, docker' line into your cluster profile.
# 2. specify 'email=user@domain.com, docker=ubuntu:latest' in rule 'params:'
# section, so cluster will submit a task with specified e-mail and docker
# container instead of defaults
job_params = job_properties.get("params", {})
rule_params_options = cluster_param.get("rule_params_options", "")
for key in job_params.keys() & {k.strip() for k in rule_params_options.split(',')}:
    cluster_param[key] = job_params[key]

# check which system you are on and load command command_options
command_options = cluster_param['command_options'][cluster_param['system']]
command = command_options['command']

key_mapping = command_options['key_mapping']

# Let's allow key mapping to use all variables here:
key_mapping_vars = {**cluster_param}
for k in job_properties:
    if (k != 'key_mapping') and (k not in key_mapping_vars):
        key_mapping_vars[k] = job_properties[k]

# construct command:
for key in key_mapping:

    command_arg = key_mapping[key]
    command_arg_keys = sorted(set(re.findall("\\{([a-z][a-z_0-9]*)\\}", command_arg)))

    # for each cluster param key with not empty value:
    command_arg_keys_2_defined = [(k, k in key_mapping_vars and bool(key_mapping_vars[k])) for k in command_arg_keys]

    undefined_args = [k for k, defined in command_arg_keys_2_defined if not defined]

    if len(undefined_args) == 0:
        # Do not split with ws, e.g. is critical for 'qsub', where
        # '-l' option has value "mem,time,threads args"
        command += key_mapping[key].format(**key_mapping_vars)
    else:
        eprint("Key '{}' ignored: Undefined variables [{}] in: {}".format(
            key, ", ".join(undefined_args), command_arg
        ))

command += ' {}'.format(jobscript)

eprint("Submit job command:", command)
args = shlex.split(command)
eprint("\nSubmit job command args:\n      {}".format(args))

p = Popen(args, stdout=PIPE, stderr=PIPE)
output, error = p.communicate()
if p.returncode != 0:
    raise Exception("Job can't be submitted\n" + output.decode("utf-8") + error.decode("utf-8"))
else:
    res = output.decode("utf-8")

    # Result could be some text that contains job id
    # LSF case:
    matcher = re.match("Job <(\\d+)> is submitted", res)
    if matcher:
        jobid = matcher[1]
    else:
        jobid = res

    print(jobid)
