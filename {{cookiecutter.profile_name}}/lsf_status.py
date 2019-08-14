#!/usr/bin/env python3

import sys
import subprocess

jobid = sys.argv[1]
# print("Checking status for Job ID <" + jobid + ">...", file=sys.stderr)

out = subprocess.run(['bjobs', '-noheader', jobid], stdout=subprocess.PIPE).stdout.decode('utf-8')

state = out.split()[2]

map_state = {
    "PEND": 'running',
    "RUN": 'running',
    "PROV": "running",
    "WAIT": 'running',
    "DONE": 'success',
    "": 'success'
}

print(map_state.get(state, 'failed'))
