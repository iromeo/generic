#!/usr/bin/env python3

import sys
import subprocess

jobid = sys.argv[1]
# print("Checking status for Job ID <" + jobid + ">...", file=sys.stderr)

out = subprocess.run(
    # fix output format using -o because user's columns order could be custom
    ['bjobs', '-noheader', '-o', 'stat:', jobid],
    stdout=subprocess.PIPE
).stdout.decode('utf-8')

state = out.strip()

map_state = {
    "PEND": 'running',
    "RUN": 'running',
    "PROV": "running",
    "WAIT": 'running',
    "DONE": 'success',
    "": 'success'
}

# print("Job ID <" + jobid + "> state is <" + state + ">", file=sys.stderr)
print(map_state.get(state, 'failed'))
