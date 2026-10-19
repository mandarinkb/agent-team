#!/usr/bin/env python3
"""Keep each teammate's model in one place: .agents/models.json.

    models.py                    show the active profile and each role's model
    models.py --profile economy  switch profile and stamp it into .agents/agents/*.md
    models.py --check            exit 1 if any role file disagrees with models.json

qa keeps the strongest model in every profile: it is the last check before a commit.
Switching profile changes who checks whom, so it is the user's decision.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import teamlib as t  # noqa: E402

SRC = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
CONFIG = os.path.join(SRC, "models.json")
AGENTS_DIR = os.path.join(SRC, "agents")


def load():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def current(role):
    text = t.read_text(os.path.join(AGENTS_DIR, f"{role}.md"))
    m = re.search(r"^model:\s*(\S+)\s*$", text, re.M)
    return m.group(1) if m else None


def stamp(role, model):
    path = os.path.join(AGENTS_DIR, f"{role}.md")
    text = t.read_text(path)
    new = re.sub(r"^model:\s*\S+\s*$", f"model: {model}", text, count=1, flags=re.M)
    if new != text:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--profile")
    p.add_argument("--check", action="store_true")
    a = p.parse_args(argv)
    cfg = load()
    if a.profile:
        if a.profile not in cfg["profiles"]:
            print(f"unknown profile {a.profile}; one of {', '.join(cfg['profiles'])}", file=sys.stderr)
            return 1
        cfg["profile"] = a.profile
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
            f.write("\n")
        for role, model in cfg["profiles"][a.profile].items():
            stamp(role, model)
    wanted = cfg["profiles"][cfg["profile"]]
    drift = [f"{role}: file says {current(role)}, models.json says {model}"
             for role, model in wanted.items() if current(role) != model]
    if a.check:
        for line in drift:
            print(line, file=sys.stderr)
        return 1 if drift else 0
    print(f"profile: {cfg['profile']}")
    for role, model in wanted.items():
        print(f"  {role:<14} {model}" + ("" if current(role) == model else f"   (file says {current(role)})"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
