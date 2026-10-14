#!/usr/bin/env python3
"""Create a task directory from the templates.

    python3 .agents/scripts/new_task.py <bug|feature|migration|program|retire> "<title>" [--id T-...]

Creates .agents/work/<task-id>/ with the templates for that kind and log.tsv
(a program gets migration-plan.md, decisions.md, and inventory.tsv),
and prints the task id. Refuses to overwrite an existing task.
"""
import argparse
import datetime
import os
import re
import sys

AGENTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOWS = {"bug": "bug-fix.md", "feature": "feature.md", "migration": "migration.md",
             "program": "migration-program.md", "retire": "migration-retire.md"}
TEMPLATES = {
    "program": ["migration-plan.md", "decisions.md", "inventory.tsv"],
}
DEFAULT_TEMPLATES = ["brief.md", "decisions.md", "test-report.md", "review-report.md"]
LOG_HEADER = "ts\tphase\tdecision\twhy\tevidence\tresult\n"


def slug(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:40].strip("-")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("kind", choices=sorted(WORKFLOWS))
    parser.add_argument("title")
    parser.add_argument("--id", help="use this task id instead of a generated one")
    args = parser.parse_args(argv)

    now = datetime.datetime.now()
    task_id = args.id or f"T-{now:%Y%m%d}-{slug(args.title) or now.strftime('%H%M%S')}"
    if not re.match(r"^T-[A-Za-z0-9._-]+$", task_id):
        print(f"new_task: invalid task id {task_id!r}", file=sys.stderr)
        return 2
    work = os.path.join(AGENTS, "work", task_id)
    if os.path.exists(work):
        print(f"new_task: {work} already exists", file=sys.stderr)
        return 2
    os.makedirs(os.path.join(work, "parity") if args.kind == "migration" else work)

    values = {
        "{{TITLE}}": args.title,
        "{{TASK_ID}}": task_id,
        "{{KIND}}": args.kind,
        "{{WORKFLOW_FILE}}": WORKFLOWS[args.kind],
        "{{DATE}}": now.strftime("%Y-%m-%d %H:%M"),
    }
    templates = TEMPLATES.get(args.kind, DEFAULT_TEMPLATES)
    for name in templates:
        text = open(os.path.join(AGENTS, "templates", name), encoding="utf-8").read()
        for key, value in values.items():
            text = text.replace(key, value)
        with open(os.path.join(work, name), "w", encoding="utf-8") as f:
            f.write(text)
    with open(os.path.join(work, "log.tsv"), "w", encoding="utf-8") as f:
        f.write(LOG_HEADER)

    print(task_id)
    print(f"created {os.path.relpath(work)}/ with {', '.join(templates)}, log.tsv")
    print(f"workflow: .agents/workflows/{WORKFLOWS[args.kind]}")
    print(f"task subjects: [{task_id}] investigate|design|implement|verify|review|commit: ...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
