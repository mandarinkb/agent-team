#!/usr/bin/env python3
"""Install the team kit into a project.

    python3 install.py <project-dir> [--force]

Copies `.agents/` into the project, copies teammates to `.claude/agents/` and skills to
`.claude/skills/`, adds the `@.agents/AGENTS.md` import to CLAUDE.md, and creates
`.claude/settings.json` from the example when the project has none. An existing file that
differs is left alone and reported, unless --force is given. settings.json is never overwritten.
"""
import argparse
import filecmp
import os
import shutil
import subprocess
import sys

KIT = os.path.dirname(os.path.abspath(__file__))
IMPORT_LINE = "@.agents/AGENTS.md"


def copy(src, dst, force, report):
    if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
        return
    if os.path.exists(dst) and not force:
        report["skipped"].append(dst)
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    report["written"].append(dst)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project")
    parser.add_argument("--force", action="store_true", help="overwrite files that differ (never settings.json)")
    args = parser.parse_args(argv)
    project = os.path.abspath(args.project)
    if not os.path.isdir(project):
        print(f"install: {project} is not a directory", file=sys.stderr)
        return 2
    report = {"written": [], "skipped": [], "notes": []}

    src_agents = os.path.join(KIT, ".agents")
    for dirpath, _, files in os.walk(src_agents):
        rel_dir = os.path.relpath(dirpath, KIT)
        work = os.path.join(".agents", "work")
        if rel_dir == work or rel_dir.startswith(work + os.sep):
            files = [f for f in files if rel_dir == work and f in (".gitignore", "README.md")]
        for f in files:
            if f == ".DS_Store" or f.endswith(".pyc"):
                continue
            copy(os.path.join(dirpath, f), os.path.join(project, rel_dir, f), args.force, report)

    for f in sorted(os.listdir(os.path.join(src_agents, "agents"))):
        if f.endswith(".md"):
            copy(os.path.join(src_agents, "agents", f), os.path.join(project, ".claude", "agents", f), args.force, report)
    for d in sorted(os.listdir(os.path.join(src_agents, "skills"))):
        skill = os.path.join(src_agents, "skills", d)
        if not os.path.isfile(os.path.join(skill, "SKILL.md")):
            continue
        for dirpath, _, files in os.walk(skill):
            for f in files:
                if f == ".DS_Store":
                    continue
                rel = os.path.relpath(os.path.join(dirpath, f), skill)
                copy(os.path.join(dirpath, f), os.path.join(project, ".claude", "skills", d, rel), args.force, report)

    claude_md = os.path.join(project, "CLAUDE.md")
    if not os.path.exists(claude_md):
        shutil.copy2(os.path.join(KIT, "CLAUDE.md.example"), claude_md)
        report["written"].append(claude_md)
    else:
        text = open(claude_md, encoding="utf-8").read()
        if IMPORT_LINE not in text:
            with open(claude_md, "a", encoding="utf-8") as f:
                f.write(("" if text.endswith("\n") else "\n") + "\n" + IMPORT_LINE + "\n")
            report["notes"].append(f"appended {IMPORT_LINE} to CLAUDE.md")

    settings = os.path.join(project, ".claude", "settings.json")
    if not os.path.exists(settings):
        os.makedirs(os.path.dirname(settings), exist_ok=True)
        shutil.copy2(os.path.join(src_agents, "settings.example.json"), settings)
        report["written"].append(settings)
    else:
        report["notes"].append(".claude/settings.json exists: merge permissions, hooks, and env from "
                               ".agents/settings.example.json by hand")

    for path in report["written"]:
        print(f"wrote    {os.path.relpath(path, project)}")
    for path in report["skipped"]:
        print(f"skipped  {os.path.relpath(path, project)} (exists and differs; rerun with --force to replace)")
    for note in report["notes"]:
        print(f"note     {note}")
    check = subprocess.run([sys.executable, os.path.join(project, ".agents", "scripts", "check_team.py"),
                            project, "--installed"])
    return check.returncode


if __name__ == "__main__":
    sys.exit(main())
