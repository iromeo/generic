#!/usr/bin/env python

import argparse
from glob import glob
from collections import OrderedDict
import sys
from collections import defaultdict

from datetime import datetime
from dateutil.parser import parse as datetime_parser

import pandas as pd
import numpy as np

PARSING_ERRORS_COL = "parsing errors"

def _cli():
    ########################################################################
    parser = argparse.ArgumentParser(
        description="Collects stats from LSF execution logs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "workdir", metavar="PATH",
        help="Working directory"
    )

    parser.add_argument(
        "--output", metavar="PATH",
        help="Output path for results table"
    )

    args = parser.parse_args()
    workdir = args.workdir
    output = args.output

    ################################
    metric2details = metric2details_mapping()
    logs_search_pth = "*.log_job.log"

    print("Metrics:", list(metric2details.keys()), file=sys.stderr)
    print("Working directory:", workdir, file=sys.stderr)
    print("Output path:", output, file=sys.stderr)
    print("Logs mask:", logs_search_pth, file=sys.stderr)

    tag_columns = [col_name for col_name, (_, _, _, fun) in metric2details.items() if fun]
    column_names = ("Target", "Files", *tag_columns)
    records = []

    rule2metrics, rule2files_count = collect_targets(logs_search_pth, workdir, metric2details)
    for rule, metric2values in rule2metrics.items():
        files_number = rule2files_count[rule]
        results = process_rule(metric2values, metric2details)
        records.append((rule, files_number, *[results.get(c, 'N/A') for c in tag_columns]))

    df = pd.DataFrame.from_records(records, columns=column_names)
    df["mean_execution_time_hms"] = [strfdelta(v) for v in df["mean_execution_time_hms"]]
    df["max_execution_time_hms"] = [strfdelta(v) for v in df["max_execution_time_hms"]]
    df.sort_values(by="max_execution_time_hms", ascending=False, inplace=True)
    print(df)
    if output:
        df.to_csv(output, sep="\t", index=False)
        print("Results saved to:", output, file=sys.stderr)


def strfdelta(time_delta):
    if type(time_delta) == str:
        return time_delta
    d = time_delta.days
    h, rem = divmod(time_delta.seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{d*24+h:2d}:{m:2d}:{s:2d}".replace(' ', '0')


def collect_targets(ptn, root_dir, metric2details):
    rule2metrics2values = defaultdict(dict)
    rule2files_count = defaultdict(int)

    files_number = 0
    for fn in glob(f"{root_dir}/**/{ptn}", recursive=True):
        files_number += 1

        file_metrics2values = {}
        rule = None

        print("    Processing:", fn, file=sys.stderr)
        with open(fn) as f:
            for line in f:
                if line.startswith("Subject: Job"):
                    job_id = line.split()[3]
                    assert job_id[0] == '<' and job_id[-1] == '>', "Unexpected Job ID format in: " + line
                    rule = job_id.split('.')[1]
                else:
                    match_line(line.strip(), metric2details, file_metrics2values)

        current_rule_metric2values = rule2metrics2values[rule]
        m2values = {}
        for metric, values in file_metrics2values.items():
            if len(values) != 1:
                values_str = ", ".join(str(s) for s in values)
                print(f"[ERROR] Result ignored: Expected 1 value for metric <{metric}>, "
                      f"but was {len(values)} in {fn}: {values_str}", file=sys.stderr)
                m2values = None
                break
            else:
                m2values[metric] = values[0]

        rule2files_count[rule] = rule2files_count[rule] + 1
        if m2values:
            for m,v in m2values.items():
                current_rule_metric2values.setdefault(m, []).append(v)
        else:
            current_rule_metric2values.setdefault(PARSING_ERRORS_COL, []).append(1)

    return rule2metrics2values, rule2files_count


def process_rule(metric2values, metric2details):
    # DEBUG:
    # print(metric2values, file=sys.stderr)
    
    results = {}
    for metric, values in metric2values.items():
        _, _, _, fun = metric2details[metric]

        if fun:
            res = eval(fun, globals(), {'col_values': values, **metric2values})
            results[metric] = res

    return results


def metric2details_mapping():
    return OrderedDict([
        (
            PARSING_ERRORS_COL,
            (None, None, None, "len(col_values)")
        ),
        ("cpu_time_sec", (
            ("CPU time :", "float", "sec.", "np.max(col_values)")
        )),
        ("max_mem_mb", (
            ("Max Memory :", "float", "MB", "np.max(col_values)")
        )),
        ("avg_mem_mb", (
            ("Average Memory :", "float", "MB", "np.mean(col_values)")
        )),
        ("min_delta_requested_mem_mb", (
            ("Delta Memory :", "float", "MB", "np.min(col_values)")
        )),
        ("max_swap_mb", (
            ("Max Swap :", "float", "MB", "np.max(col_values)")
        )),
        ("max_processes", (
            ("Max Processes :", "int", None, "np.max(col_values)")
        )),
        ("max_threads", (
            ("Max Threads :", "int", None, "np.max(col_values)")
        )),

        ("started_time", (
            ("Started at", "datetime", None, None)
        )),

        # MGI cluster:
        ("mean_execution_time_hms", (
            ("Results reported on ", "datetime", None,
             "np.mean(np.asarray(max_execution_time_hms)-np.asarray(started_time))")
        )),
        ("max_execution_time_hms", (
            ("Results reported on ", "datetime", None,
             "np.max(np.asarray(max_execution_time_hms)-np.asarray(started_time))")
        )),
        # New cluster:
        ("mean_execution_time_hms", (
            ("Results reported at ", "datetime", None,
             "np.mean(np.asarray(max_execution_time_hms)-np.asarray(started_time))")
        )),
        ("max_execution_time_hms", (
            ("Results reported at ", "datetime", None,
             "np.max(np.asarray(max_execution_time_hms)-np.asarray(started_time))")
        )),
    ])


def match_line(line, metric2details, metric2values):
    line_lower = line.lower().strip()
    type_2_parser = {
        'float': float,
        'int': int,
        'datetime': datetime_parser
    }
    for metric, (ptn, el_type, scale, fun) in metric2details.items():
        if ptn is None:
            # errors handling
            continue

        if line_lower.startswith(ptn.lower()):
            # print(f"Line: <{line}>", file=sys.stderr)

            value_str = line[len(ptn):].strip()
            if value_str == '-':
                # skip
                continue

            values = metric2values.setdefault(metric, [])

            if el_type != "datetime":
                items = value_str.split()
            else:
                items = [value_str]

            str_value = items[0]
            if scale:
                assert len(items) > 1, f"Expected '{scale}' for <{value_str}> in: {line}"
                assert scale == items[1], f"Expected '{scale}', but was '{items[1]}' in: {value_str}"

            value = type_2_parser[el_type](str_value)
            values.append(value)


if __name__ == "__main__":
    _cli()
