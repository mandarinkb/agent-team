#!/usr/bin/env python3
"""TaskCompleted hook: verify and review tasks complete only when their report is filled in.

A task whose subject starts with `[<task-id>] verify` needs `.agents/work/<task-id>/test-report.md`.
A task whose subject starts with `[<task-id>] review` needs `.agents/work/<task-id>/review-report.md`.
Each report needs no `<fill` placeholder, a valid Verdict, and the Revision SHA it covers.
Other tasks pass through. Exit 2 blocks the completion and sends the reason back to the teammate.
"""
import json
import os
import re
import sys

SUBJECT = re.compile(r"^\s*\[(T-[A-Za-z0-9._-]+)\]\s*(verify|review)\b", re.IGNORECASE)
REPORTS = {
    "verify": ("test-report.md", ("PASS", "ISSUES", "BLOCKED", "INCONCLUSIVE"), "team-verify"),
    "review": ("review-report.md", ("NO_FINDINGS", "FINDINGS", "BLOCKED"), "team-review"),
}
PLACEHOLDER = re.compile(r"<(fill|lead)(?::[^>]*)?>")
ROUND = re.compile(r"^- \*\*Round:\*\*\s*(\d+)\b", re.MULTILINE)
ROUND_APPROVAL = re.compile(r"^- \*\*Round approval:\*\*\s*(.+?)\s*$", re.MULTILINE)
ROUND_BUDGET = 3
REVISION = re.compile(r"^- \*\*Revision:\*\*\s*`?([0-9a-f]{7,40})`?\s*$", re.MULTILINE)


def problems_for(report_path, verdicts):
    if not os.path.isfile(report_path):
        return [f"missing {report_path}. Fill it from .agents/templates/{os.path.basename(report_path)}"]
    text = open(report_path, encoding="utf-8").read()
    found = []
    fills = [m for m in PLACEHOLDER.finditer(text) if m.group(1) == "fill"]
    if fills:
        found.append(f"{len(fills)} '<fill' placeholder(s) remain")
    verdict = re.compile(r"^- \*\*Verdict:\*\*\s*(" + "|".join(verdicts) + r")\s*$", re.MULTILINE)
    if not verdict.search(text):
        found.append(f"the Verdict line must be exactly one of {', '.join(verdicts)}")
    if not REVISION.search(text):
        found.append("the Revision line must hold the tree id the report covers (7 to 40 lowercase hex characters)")
    rnd = ROUND.search(text)
    if not rnd:
        found.append("the Round line must hold the round number (1, 2, 3, ...)")
    elif int(rnd.group(1)) > ROUND_BUDGET:
        approval = ROUND_APPROVAL.search(text)
        if not approval or "D9" not in approval.group(1):
            found.append(f"round {rnd.group(1)} is past the budget of {ROUND_BUDGET}. Stop and raise D9 "
                         "(.agents/protocols/loops.md). The Round approval line must cite the approved D9.")
    return found


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    match = SUBJECT.match(data.get("task_subject") or "")
    if not match:
        return 0
    task_id, kind = match.group(1), match.group(2).lower()
    filename, verdicts, skill = REPORTS[kind]
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    found = problems_for(os.path.join(root, ".agents", "work", task_id, filename), verdicts)
    if not found:
        return 0
    print(f"Cannot complete '{data.get('task_subject')}': {filename} is not ready.", file=sys.stderr)
    for p in found:
        print(f"- {p}", file=sys.stderr)
    print(f"Finish the report with the {skill} skill, then complete the task again.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
