#!/usr/bin/env python3
"""Check that the team kit is complete and consistent.

    python3 .agents/scripts/check_team.py [root] [--installed]

root is the directory that holds `.agents/` (default: the parent of `.agents`).
--installed also checks the copies under `.claude/agents`, `.claude/skills`, and the CLAUDE.md import.
Exit 0 when every check holds, 1 otherwise.
"""
import argparse
import filecmp
import json
import os
import re
import sys

REQUIRED = [
    ".agents/AGENTS.md",
    ".agents/rules.json",
    ".agents/standing-decisions.md",
    ".agents/settings.example.json",
    ".agents/protocols/decisions.md",
    ".agents/protocols/messaging.md",
    ".agents/protocols/commit-approval.md",
    ".agents/protocols/loops.md",
    ".agents/templates/brief.md",
    ".agents/templates/decision-request.md",
    ".agents/templates/decisions.md",
    ".agents/templates/test-report.md",
    ".agents/templates/review-report.md",
    ".agents/workflows/bug-fix.md",
    ".agents/workflows/feature.md",
    ".agents/workflows/migration.md",
    ".agents/workflows/migration-program.md",
    ".agents/workflows/migration-retire.md",
    ".agents/templates/migration-plan.md",
    ".agents/templates/inventory.tsv",
    ".agents/scripts/migration_status.py",
    ".agents/scripts/checkpoint.py",
    ".agents/scripts/sync_claude.py",
    ".agents/workflows/retro.md",
    ".agents/templates/retro.md",
    ".agents/skills/team-reflect/references/judgment.md",
    ".agents/skills/team-reflect/references/tooling.md",
    ".agents/skills/team-reflect/references/divergent.md",
    ".agents/skills/team-reflect/references/synthesizer.md",
    ".agents/templates/checkpoint-note.md",
    ".agents/scripts/new_task.py",
    ".agents/scripts/log_row.py",
    ".agents/scripts/parity.py",
    ".agents/scripts/hooks/guard_git.py",
    ".agents/scripts/hooks/gate_reports.py",
    ".agents/scripts/hooks/loop_guard.py",
    ".agents/scripts/team_health.py",
    ".agents/scripts/vendor_pstack_skills.py",
]
AGENT_KEYS = ["name", "description", "tools", "model"]
WORKFLOW_SECTIONS = ["## When", "## Team", "## Steps", "## Gates", "## Done when"]
PATH_REF = re.compile(r"`(\.agents/[^`\s]+)`")


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return None, text
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields, text[m.end():]


STANDING_FIELDS = ["Codes", "Scope", "Ruling", "Recorded", "Status"]
NEVER_STANDING = {"D7", "D8", "D11"}


def check_standing(path):
    """Validate .agents/standing-decisions.md entries outside HTML comments."""
    problems = []
    text = re.sub(r"<!--.*?-->", "", open(path, encoding="utf-8").read(), flags=re.DOTALL)
    entries = re.split(r"^## (?=SD-)", text, flags=re.M)[1:]
    seen = set()
    for entry in entries:
        head = entry.splitlines()[0]
        m = re.match(r"^(SD-\d+): \S", head)
        if not m:
            problems.append(f"standing decision heading {head!r} must look like 'SD-<n>: <title>'")
            continue
        sid = m.group(1)
        if sid in seen:
            problems.append(f"{sid}: duplicate id")
        seen.add(sid)
        fields = dict(re.findall(r"^- \*\*(\w+):\*\*\s*(.+?)\s*$", entry, re.M))
        for f in STANDING_FIELDS:
            if not fields.get(f):
                problems.append(f"{sid}: missing **{f}:**")
        codes = set(re.findall(r"D\d+", fields.get("Codes", "")))
        if not codes:
            problems.append(f"{sid}: Codes must name decision codes such as D3")
        bad = codes & NEVER_STANDING
        if bad:
            problems.append(f"{sid}: {', '.join(sorted(bad))} can never be a standing decision")
        ruling = fields.get("Ruling", "")
        if not re.search(r'["\u201c].+["\u201d]', ruling):
            problems.append(f"{sid}: Ruling must quote the user's own words")
        status = fields.get("Status", "")
        if not re.match(r"^(active|revoked \d{4}-\d{2}-\d{2}\b.*)$", status):
            problems.append(f"{sid}: Status must be 'active' or 'revoked YYYY-MM-DD ...'")
        if "critical" in entry.lower() and "dismiss" in entry.lower():
            problems.append(f"{sid}: dismissing critical review findings can never be a standing decision")
    return problems


def check(root, installed):
    problems = []
    a = os.path.join(root, ".agents")
    for rel in REQUIRED:
        if not os.path.isfile(os.path.join(root, rel)):
            problems.append(f"missing {rel}")

    agents_dir = os.path.join(a, "agents")
    agent_names = []
    for f in sorted(os.listdir(agents_dir)) if os.path.isdir(agents_dir) else []:
        if not f.endswith(".md"):
            continue
        fm, body = frontmatter(os.path.join(agents_dir, f))
        rel = f".agents/agents/{f}"
        if fm is None:
            problems.append(f"{rel}: no frontmatter")
            continue
        for k in AGENT_KEYS:
            if not fm.get(k):
                problems.append(f"{rel}: frontmatter needs {k}")
        if fm.get("name") != f[:-3]:
            problems.append(f"{rel}: name {fm.get('name')!r} does not match the file name")
        if ".agents/AGENTS.md" not in body:
            problems.append(f"{rel}: body must tell the teammate to read .agents/AGENTS.md")
        if "## Choosing skills" not in body:
            problems.append(f"{rel}: body needs a '## Choosing skills' section")
        agent_names.append(f[:-3])
    for role in ("analyst", "backend", "qa", "git"):
        if role not in agent_names:
            problems.append(f"missing core teammate .agents/agents/{role}.md")

    skills_dir = os.path.join(a, "skills")
    skill_names = []
    for d in sorted(os.listdir(skills_dir)) if os.path.isdir(skills_dir) else []:
        p = os.path.join(skills_dir, d, "SKILL.md")
        if not os.path.isdir(os.path.join(skills_dir, d)) or d == "licenses":
            continue
        if not os.path.isfile(p):
            problems.append(f".agents/skills/{d}: missing SKILL.md")
            continue
        if "Vendored from pstack-claude" in open(p, encoding="utf-8").read():
            for need in ("THIRD_PARTY_NOTICES.md", "licenses/LICENSE-pstack", "licenses/LICENSE-cursor-team-kit"):
                if not os.path.isfile(os.path.join(skills_dir, need)):
                    problems.append(f".agents/skills/{d} is vendored but .agents/skills/{need} is missing")
        fm, _ = frontmatter(p)
        if not fm or fm.get("name") != d or not fm.get("description"):
            problems.append(f".agents/skills/{d}/SKILL.md: frontmatter needs name {d!r} and a description")
        elif not fm.get("when_to_use"):
            problems.append(f".agents/skills/{d}/SKILL.md: frontmatter needs when_to_use so teammates can pick it")
        skill_names.append(d)

    md_files = []
    for dirpath, _, files in os.walk(a):
        if os.path.relpath(dirpath, a).split(os.sep)[0] == "work":
            continue
        md_files += [os.path.join(dirpath, f) for f in files if f.endswith(".md")]
    for p in md_files:
        text = open(p, encoding="utf-8").read()
        rel = os.path.relpath(p, root)
        for ref in PATH_REF.findall(text):
            if "<" in ref or "{" in ref or "*" in ref:
                continue
            if not os.path.exists(os.path.join(root, ref.rstrip("/"))):
                problems.append(f"{rel}: refers to {ref}, which does not exist")
        for name in set(re.findall(r"`(team-[a-z-]+)`", text)):
            if name not in skill_names:
                problems.append(f"{rel}: refers to skill {name}, which does not exist")

    wf_dir = os.path.join(a, "workflows")
    for wf in sorted(f[:-3] for f in os.listdir(wf_dir) if f.endswith(".md")) if os.path.isdir(wf_dir) else []:
        p = os.path.join(wf_dir, f"{wf}.md")
        text = open(p, encoding="utf-8").read()
        for s in WORKFLOW_SECTIONS:
            if s not in text:
                problems.append(f".agents/workflows/{wf}.md: missing section {s!r}")
        for gate in ("GATE G1", "GATE G2"):
            if gate not in text:
                problems.append(f".agents/workflows/{wf}.md: missing {gate}")
        if wf not in ("migration-program", "retro") and ("**reviewer**" not in text or "`team-review`" not in text):
            problems.append(f".agents/workflows/{wf}.md: needs a reviewer step that uses team-review")

    settings = os.path.join(a, "settings.example.json")
    if os.path.isfile(settings):
        try:
            cfg = json.load(open(settings, encoding="utf-8"))
            if "Bash(git commit *)" not in cfg.get("permissions", {}).get("ask", []):
                problems.append(".agents/settings.example.json: ask rules must include Bash(git commit *)")
            hooks = json.dumps(cfg.get("hooks", {}))
            for script in ("guard_git.py", "gate_reports.py", "loop_guard.py"):
                if script not in hooks:
                    problems.append(f".agents/settings.example.json: hooks must run {script}")
        except json.JSONDecodeError as e:
            problems.append(f".agents/settings.example.json: invalid JSON ({e})")

    tpl_dir = os.path.join(a, "templates")
    for f in sorted(os.listdir(tpl_dir)) if os.path.isdir(tpl_dir) else []:
        text = open(os.path.join(tpl_dir, f), encoding="utf-8").read()
        for comment in re.findall(r"<!--(.*?)-->", text, re.DOTALL):
            if re.search(r"<(fill|lead)(?::[^>]*)?>|\"<(fill|lead)\"", comment):
                problems.append(f".agents/templates/{f}: a comment contains a placeholder token, "
                                "so a finished report would still look unfinished to the hooks")

    for rpt in ("test-report.md", "review-report.md"):
        rp = os.path.join(a, "templates", rpt)
        if os.path.isfile(rp):
            rtext = open(rp, encoding="utf-8").read()
            for need in ("- **Round:**", "- **Round approval:**"):
                if need not in rtext:
                    problems.append(f".agents/templates/{rpt}: missing {need!r}, which gate_reports.py relies on")

    review_tpl = os.path.join(a, "templates", "review-report.md")
    if os.path.isfile(review_tpl):
        text = open(review_tpl, encoding="utf-8").read()
        for need in ("- **Verdict:** <fill: NO_FINDINGS | FINDINGS | BLOCKED>", "- **Revision:**", "## การคัดกรองของ lead", "<lead"):
            if need not in text:
                problems.append(f".agents/templates/review-report.md: missing {need!r}, which the hooks rely on")

    standing = os.path.join(a, "standing-decisions.md")
    if os.path.isfile(standing):
        problems += [f".agents/standing-decisions.md: {p}" for p in check_standing(standing)]

    rules_path = os.path.join(a, "rules.json")
    if os.path.isfile(rules_path):
        rules = json.load(open(rules_path, encoding="utf-8"))
        phrases = [r["phrase"] for r in rules]
        if len(set(phrases)) != len(phrases):
            problems.append(".agents/rules.json: two rules pin the same phrase")
        for r in rules:
            target = os.path.join(root, r["file"])
            if len(r["phrase"]) < 20:
                problems.append(f"rule '{r['source']}': phrase under 20 characters")
            elif not os.path.isfile(target):
                problems.append(f"rule '{r['source']}': {r['file']} does not exist")
            elif r["phrase"] not in open(target, encoding="utf-8").read():
                problems.append(f"rule '{r['source']}': {r['file']} no longer says \"{r['phrase']}\"")

    if installed:
        for name in agent_names:
            src = os.path.join(agents_dir, f"{name}.md")
            dst = os.path.join(root, ".claude", "agents", f"{name}.md")
            if not os.path.isfile(dst) or not filecmp.cmp(src, dst, shallow=False):
                problems.append(f".claude/agents/{name}.md is missing or differs from .agents/agents/{name}.md")
        for name in skill_names:
            for dirpath, _, files in os.walk(os.path.join(skills_dir, name)):
                for f in files:
                    src = os.path.join(dirpath, f)
                    rel = os.path.relpath(src, skills_dir)
                    dst = os.path.join(root, ".claude", "skills", rel)
                    if not os.path.isfile(dst) or not filecmp.cmp(src, dst, shallow=False):
                        problems.append(f".claude/skills/{rel} is missing or differs from .agents/skills/{rel}")
        imports = [os.path.join(root, "CLAUDE.md"), os.path.join(root, ".claude", "CLAUDE.md")]
        if not any(os.path.isfile(p) and re.search(r"^@(\.\./)?\.agents/AGENTS\.md\s*$",
                                                    open(p, encoding="utf-8").read(), re.MULTILINE)
                   for p in imports):
            problems.append("CLAUDE.md does not import @.agents/AGENTS.md")
    return problems, agent_names, skill_names


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    parser.add_argument("--installed", action="store_true")
    args = parser.parse_args(argv)
    problems, agents, skills = check(os.path.abspath(args.root), args.installed)
    for p in problems:
        print(p, file=sys.stderr)
    status = "FAIL" if problems else "OK"
    print(f"{status}: {len(agents)} teammates, {len(skills)} skills, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
