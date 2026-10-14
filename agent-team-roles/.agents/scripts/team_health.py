#!/usr/bin/env python3
"""Show the lead which teammates may be stuck in a loop.

    python3 .agents/scripts/team_health.py [--json]

Reads three records and prints one warning per problem:
- the loop guard state: agents whose repeated command count is near or at the limit;
- each task's test and review report: tasks at round 3 or beyond;
- each task's log.tsv: the same phase, decision, and result logged twice in a row.
Exit 0 when there is nothing to act on, 1 when there are warnings.
"""
import argparse
import json
import os
import re
import sys
import time

AGENTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(AGENTS, "work")
ROUND = re.compile(r"^- \*\*Round:\*\*\s*(\d+)\b", re.M)
MAX = int(os.environ.get("LOOP_GUARD_MAX", "6"))
WINDOW = int(os.environ.get("LOOP_GUARD_WINDOW", "600"))


def loop_guard_warnings(now):
    warnings = []
    state_dir = os.path.join(WORK, ".loop-guard")
    for f in sorted(os.listdir(state_dir)) if os.path.isdir(state_dir) else []:
        try:
            state = json.load(open(os.path.join(state_dir, f), encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for entry in state.get("calls", {}).values():
            count = len([t for t in entry.get("times", []) if now - t < WINDOW])
            if count >= MAX:
                warnings.append(f"{state.get('agent', f)}: stopped by the loop guard on `{entry['command'][:80]}` ({count} times)")
            elif count >= MAX - 2:
                warnings.append(f"{state.get('agent', f)}: repeated `{entry['command'][:80]}` {count} times without changes")
    return warnings


def task_warnings():
    warnings = []
    for task in sorted(os.listdir(WORK)) if os.path.isdir(WORK) else []:
        task_dir = os.path.join(WORK, task)
        if not os.path.isdir(task_dir) or task.startswith("."):
            continue
        for report in ("test-report.md", "review-report.md"):
            path = os.path.join(task_dir, report)
            if os.path.isfile(path):
                m = ROUND.search(open(path, encoding="utf-8").read())
                if m and int(m.group(1)) >= 3:
                    warnings.append(f"{task}: {report} is at round {m.group(1)} (budget is 3, round 4 needs D9)")
        log = os.path.join(task_dir, "log.tsv")
        if os.path.isfile(log):
            rows = [l.rstrip("\n").split("\t") for l in open(log, encoding="utf-8")][1:]
            for prev, cur in zip(rows, rows[1:]):
                if len(prev) >= 6 and len(cur) >= 6 and (prev[1], prev[2], prev[5]) == (cur[1], cur[2], cur[5]):
                    warnings.append(f"{task}: log.tsv repeats '{cur[1]} / {cur[2][:60]} / {cur[5]}'")
    return warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    warnings = loop_guard_warnings(time.time()) + task_warnings()
    if args.json:
        print(json.dumps({"warnings": warnings}, ensure_ascii=False, indent=2))
    elif warnings:
        print("Possible loops. See .agents/protocols/loops.md, 'What the lead does':")
        for w in warnings:
            print(f"- {w}")
    else:
        print("No loop warnings.")
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
