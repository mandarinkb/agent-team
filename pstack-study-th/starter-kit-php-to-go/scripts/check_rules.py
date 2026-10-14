#!/usr/bin/env python3
"""Fail when a pinned rule sentence disappears from the file that carries it.

    python3 scripts/check_rules.py [rules.json]

Each entry in rules.json names the file, the exact sentence, and where the rule came from.
Add an entry whenever a rule is earned from a real incident.
"""
import json
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "rules.json")
rules = json.load(open(path, encoding="utf-8"))
problems = []
phrases = [r["phrase"] for r in rules]
if len(set(phrases)) != len(phrases):
    problems.append("two rules pin the same phrase")
for r in rules:
    if len(r["phrase"]) < 20:
        problems.append(f"{r['source']}: phrase is under 20 characters, too short to pin a rule")
    target = os.path.join(root, r["file"])
    if not os.path.exists(target):
        problems.append(f"{r['source']}: {r['file']} does not exist")
    elif r["phrase"] not in open(target, encoding="utf-8").read():
        problems.append(f"{r['source']}: {r['file']} no longer says \"{r['phrase']}\"")
for p in problems:
    print(p, file=sys.stderr)
print(f"{len(rules) - len(problems)} of {len(rules)} rules hold" if problems else f"all {len(rules)} rules hold")
sys.exit(1 if problems else 0)
