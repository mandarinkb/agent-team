#!/usr/bin/env python3
"""Install the team into a project by linking it to this repo's .agents/.

    python3 .agents/scripts/install.py /path/to/project

The rules, roles, scripts, and templates stay here and are symlinked, so a fix here
reaches every project. Each project keeps its own .agents/work/, GLOSSARY.md, and
.agents/db-mcp.json. Existing files are never overwritten; the script says what to merge.
"""
import json
import os
import sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKED = ("AGENTS.md", "README-TH.md", "agents", "protocols", "scripts", "skills", "templates", "workflows")
IMPORT = "@../.agents/AGENTS.md"
HOOKS = {
    "UserPromptSubmit": [(None, "log_user_prompt.py")],
    "PreToolUse": [("Bash", "guard_git.py"), ("Bash|Write|Edit|MultiEdit|NotebookEdit", "guard_task.py"),
                   ("mcp__.*", "guard_sql.py"), ("Bash", "loop_guard.py"), ("Bash", "limit_guard.py"), (None, "probe_identity.py")],
}
TIMEOUTS = {"guard_git.py": 600}
DENY = ["Bash(git push)", "Bash(git push *)", "Bash(git reset --hard*)", "Bash(git clean -f*)",
        "Bash(gh pr create*)", "Bash(gh pr merge*)"]


def link(target, path, notes):
    if os.path.islink(path) and os.path.realpath(path) == os.path.realpath(target):
        return
    if os.path.lexists(path):
        notes.append(f"exists, left alone: {path}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    os.symlink(target, path)
    notes.append(f"linked {path} -> {target}")


def settings_block():
    hooks = {}
    for event, entries in HOOKS.items():
        for matcher, script in entries:
            hook = {"type": "command", "command": f'python3 "${{CLAUDE_PROJECT_DIR}}/.agents/scripts/hooks/{script}"'}
            if script in TIMEOUTS:
                hook["timeout"] = TIMEOUTS[script]
            entry = {"hooks": [hook]}
            if matcher:
                entry["matcher"] = matcher
            hooks.setdefault(event, []).append(entry)
    return {"permissions": {"deny": DENY}, "hooks": hooks}


def main(argv):
    if len(argv) != 1 or not os.path.isdir(argv[0]):
        print(__doc__, file=sys.stderr)
        return 2
    project = os.path.abspath(argv[0])
    if os.path.realpath(project) == os.path.realpath(os.path.dirname(SRC)):
        print("this repo is the source; install into another project", file=sys.stderr)
        return 2
    notes = []
    for name in LINKED:
        link(os.path.join(SRC, name), os.path.join(project, ".agents", name), notes)
    link(os.path.join("..", ".agents", "agents"), os.path.join(project, ".claude", "agents"), notes)
    link(os.path.join("..", ".agents", "skills"), os.path.join(project, ".claude", "skills"), notes)
    work_ignore = os.path.join(project, ".agents", "work", ".gitignore")
    if not os.path.exists(work_ignore):
        os.makedirs(os.path.dirname(work_ignore), exist_ok=True)
        with open(work_ignore, "w") as f:
            f.write("*\n!.gitignore\n")
    claude_md = os.path.join(project, ".claude", "CLAUDE.md")
    text = open(claude_md, encoding="utf-8").read() if os.path.exists(claude_md) else ""
    if IMPORT not in text:
        with open(claude_md, "a", encoding="utf-8") as f:
            f.write(("\n" if text and not text.endswith("\n") else "") + IMPORT + "\n")
        notes.append(f"added {IMPORT} to {claude_md}")
    settings = os.path.join(project, ".claude", "settings.json")
    if os.path.exists(settings):
        notes.append(f"{settings} exists. Merge this into it by hand:\n{json.dumps(settings_block(), indent=2)}")
    else:
        with open(settings, "w") as f:
            json.dump(settings_block(), f, indent=4)
            f.write("\n")
        notes.append(f"wrote {settings}")
    print("\n".join(notes))
    print("Usage limit guard: add this line right after 'input=$(cat)' in your status line script:\n"
          '  echo "$input" | python3 "${CLAUDE_PROJECT_DIR:-.}/.agents/scripts/hooks/record_limits.py" 2>/dev/null')
    print("Next: point a DB MCP server at a test database with a SELECT-only user, write "
          ".agents/db-mcp.json, and install Bruno CLI (npm i -g @usebruno/cli).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
