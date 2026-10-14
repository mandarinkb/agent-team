#!/usr/bin/env python3
"""Compute a migration program's status board from its records.

    python3 .agents/scripts/migration_status.py <program-task-id> [--json]

Reads the program's inventory.tsv and each unit's test-report.md, then writes STATUS.md in the
program directory. Adapted from pstack Orchestrate: status is derived from the tables, never
narrated. A unit counts as done only when its state is committed or later AND its report says
PASS with parity 0 DIFF and 0 UNREACHABLE AND the report lists a commit.

Exit 0 when the board has no inconsistencies, 1 when it has some, 2 on input errors.
"""
import argparse
import json
import os
import re
import sys

AGENTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATES = ["planned", "baseline", "porting", "verified", "committed", "traffic", "retired"]
DONE_STATES = {"committed", "traffic", "retired"}
COLUMNS = ["unit", "kind", "method", "path", "risk", "order", "depends_on", "task_id", "state", "notes"]

VERDICT = re.compile(r"^- \*\*Verdict:\*\*\s*(PASS|ISSUES|BLOCKED|INCONCLUSIVE)\s*$", re.M)
REVISION = re.compile(r"^- \*\*Revision:\*\*\s*`?([0-9a-f]{7,40})`?\s*$", re.M)
PARITY = re.compile(r"MATCH / DIFF / UNREACHABLE:\*\*\s*(\d+)\s*/\s*(\d+)\s*/\s*(\d+)")
PLACEHOLDER = re.compile(r"<fill(?::[^>]*)?>")
COMMIT_ROW = re.compile(r"^\|\s*`?([0-9a-f]{7,40})`?\s*\|", re.M)


class InputError(Exception):
    pass


def read_inventory(path):
    if not os.path.isfile(path):
        raise InputError(f"missing {path}")
    lines = [l.rstrip("\n") for l in open(path, encoding="utf-8") if l.strip()]
    header = lines[0].split("\t")
    if header != COLUMNS:
        raise InputError(f"{path}: header must be {' '.join(COLUMNS)}")
    rows = []
    for n, line in enumerate(lines[1:], 2):
        cells = line.split("\t") + [""] * (len(COLUMNS) - len(line.split("\t")))
        row = dict(zip(COLUMNS, (c.strip() for c in cells)))
        if not row["unit"]:
            raise InputError(f"{path}:{n}: unit is empty")
        if row["state"] not in STATES:
            raise InputError(f"{path}:{n}: state {row['state']!r} is not one of {', '.join(STATES)}")
        rows.append(row)
    names = [r["unit"] for r in rows]
    if len(set(names)) != len(names):
        raise InputError(f"{path}: unit names must be unique")
    return rows


def read_report(task_id):
    path = os.path.join(AGENTS, "work", task_id, "test-report.md")
    if not task_id or not os.path.isfile(path):
        return None
    text = open(path, encoding="utf-8").read()
    v, r, p = VERDICT.search(text), REVISION.search(text), PARITY.search(text)
    commit_section = text.split("## Commit", 1)[1] if "## Commit" in text else ""
    return {
        "verdict": v.group(1) if v else None,
        "revision": r.group(1) if r else None,
        "parity": tuple(int(x) for x in p.groups()) if p else None,
        "commits": COMMIT_ROW.findall(commit_section),
        "placeholders": len(PLACEHOLDER.findall(text)),
    }


def assess(rows):
    by_name = {r["unit"]: r for r in rows}
    board, problems = [], []
    for r in rows:
        rank = STATES.index(r["state"])
        report = read_report(r["task_id"])
        issues = []
        if rank >= STATES.index("baseline") and not r["task_id"]:
            issues.append("state is past planned but no task_id")
        if rank >= STATES.index("porting"):
            for dep in filter(None, (d.strip() for d in r["depends_on"].split(","))):
                if dep not in by_name:
                    issues.append(f"depends on unknown unit {dep}")
                elif by_name[dep]["state"] not in DONE_STATES:
                    issues.append(f"started before dependency {dep} was committed")
        if rank >= STATES.index("verified"):
            if report is None:
                issues.append("claims verified but has no test report")
            else:
                if report["placeholders"]:
                    issues.append("test report still has placeholders")
                if report["verdict"] != "PASS":
                    issues.append(f"claims verified but report verdict is {report['verdict']}")
                if report["parity"] is None:
                    issues.append("report has no parity counts")
                elif report["parity"][1] or report["parity"][2]:
                    issues.append(f"parity shows {report['parity'][1]} DIFF and {report['parity'][2]} UNREACHABLE")
        if rank >= STATES.index("committed") and report is not None and not report["commits"]:
            issues.append("claims committed but the report lists no commit")
        done = r["state"] in DONE_STATES and not issues
        board.append({**r, "report": report, "issues": issues, "done": done})
        problems += [f"{r['unit']}: {i}" for i in issues]
    return board, problems


def render(task_id, board, problems):
    total, done = len(board), sum(b["done"] for b in board)
    counts = {s: sum(b["state"] == s for b in board) for s in STATES}
    out = [f"# Migration status: {task_id}", "",
           "Generated by `.agents/scripts/migration_status.py` from inventory.tsv and the unit test reports. Do not edit by hand.", "",
           f"**Done:** {done} of {total} units (committed or later, PASS, 0 DIFF, 0 UNREACHABLE, commit recorded)", "",
           "**By state:** " + ", ".join(f"{s} {counts[s]}" for s in STATES), "",
           f"**Inconsistencies:** {len(problems)}", ""]
    out += [f"- {p}" for p in problems] + ([""] if problems else [])
    out += ["| Order | Unit | Kind | Risk | State | Task | Verdict | Revision | Parity M/D/U | Done |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for b in sorted(board, key=lambda b: (int(b["order"]) if b["order"].isdigit() else 10**9, b["unit"])):
        rep = b["report"] or {}
        parity = "/".join(map(str, rep["parity"])) if rep.get("parity") else "-"
        out.append(f"| {b['order'] or '-'} | {b['unit']} | {b['kind'] or '-'} | {b['risk'] or '-'} | {b['state']} | "
                   f"{b['task_id'] or '-'} | {rep.get('verdict') or '-'} | {rep.get('revision') or '-'} | {parity} | "
                   f"{'yes' if b['done'] else 'no'} |")
    return "\n".join(out) + "\n", done, total


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("program")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    program_dir = os.path.join(AGENTS, "work", args.program)
    try:
        rows = read_inventory(os.path.join(program_dir, "inventory.tsv"))
    except InputError as e:
        print(f"migration_status: {e}", file=sys.stderr)
        return 2
    board, problems = assess(rows)
    text, done, total = render(args.program, board, problems)
    with open(os.path.join(program_dir, "STATUS.md"), "w", encoding="utf-8") as f:
        f.write(text)
    if args.json:
        print(json.dumps({"done": done, "total": total, "problems": problems,
                          "units": [{k: v for k, v in b.items() if k != "report"} for b in board]},
                         ensure_ascii=False, indent=2))
    else:
        print(f"done {done} of {total}, {len(problems)} inconsistencies; wrote {os.path.relpath(program_dir)}/STATUS.md")
        for p in problems:
            print(f"  {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
