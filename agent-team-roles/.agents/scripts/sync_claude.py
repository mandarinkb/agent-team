#!/usr/bin/env python3
"""Copy the team's agents and skills from .agents/ into .claude/, where Claude Code reads them.

    python3 .agents/scripts/sync_claude.py [--check]

.agents/ is the source. Run this after any edit to .agents/agents/ or .agents/skills/.
--check writes nothing and exits 1 when a copy is missing or differs.
A copy in .claude/ with no source in .agents/ is reported, never deleted.
"""
import argparse
import filecmp
import os
import shutil
import sys

AGENTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(AGENTS)
SKIP = {".DS_Store"}


def pairs():
    src_agents = os.path.join(AGENTS, "agents")
    for f in sorted(os.listdir(src_agents)):
        if f.endswith(".md"):
            yield os.path.join(src_agents, f), os.path.join(ROOT, ".claude", "agents", f)
    src_skills = os.path.join(AGENTS, "skills")
    for d in sorted(os.listdir(src_skills)):
        skill = os.path.join(src_skills, d)
        if not os.path.isfile(os.path.join(skill, "SKILL.md")):
            continue
        for dirpath, _, files in os.walk(skill):
            for f in files:
                if f in SKIP:
                    continue
                src = os.path.join(dirpath, f)
                yield src, os.path.join(ROOT, ".claude", "skills", os.path.relpath(src, src_skills))


def orphans():
    found = []
    team_skills = {d for d in os.listdir(os.path.join(AGENTS, "skills"))
                   if os.path.isfile(os.path.join(AGENTS, "skills", d, "SKILL.md"))}
    team_agents = {f for f in os.listdir(os.path.join(AGENTS, "agents")) if f.endswith(".md")}
    claude_agents = os.path.join(ROOT, ".claude", "agents")
    for f in sorted(os.listdir(claude_agents)) if os.path.isdir(claude_agents) else []:
        if f.endswith(".md") and f not in team_agents and f[:-3] in {"analyst", "backend", "frontend", "qa", "reviewer", "git"}:
            found.append(f".claude/agents/{f}")
    claude_skills = os.path.join(ROOT, ".claude", "skills")
    for d in sorted(os.listdir(claude_skills)) if os.path.isdir(claude_skills) else []:
        if d.startswith("team-") and d not in team_skills:
            found.append(f".claude/skills/{d}")
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    stale = []
    for src, dst in pairs():
        if os.path.isfile(dst) and filecmp.cmp(src, dst, shallow=False):
            continue
        stale.append(os.path.relpath(dst, ROOT))
        if not args.check:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    verb = "stale" if args.check else "synced"
    for path in stale:
        print(f"{verb} {path}")
    for path in orphans():
        print(f"orphan {path} (no source in .agents/; remove it by hand if it is no longer wanted)")
    print(f"{len(stale)} {verb}")
    return 1 if args.check and stale else 0


if __name__ == "__main__":
    sys.exit(main())
