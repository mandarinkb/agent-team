#!/usr/bin/env python3
"""PreToolUse hook on Bash, Write, Edit, MultiEdit, and NotebookEdit.

- job.py and task.py run only as the role that owns the step. task.py's --by must be
  the agent actually running it.
- Nobody edits job state, the logs, or the user prompt log by hand.
- Teammates never edit the gates themselves: scripts, hooks, settings, role files.
- Inside a job worktree, an implementer writes only the scope of a task it holds in
  progress, qa writes only the job's Bruno collection, and nobody else writes at all,
  the lead included.
"""
import os
import re
import shlex

from hooklib import deny, lenient_identity, read_input, role_of, teamlib as t

JOB_ROLES = {"new": "lead", "grill-done": "lead", "add-task": "lead", "approve": "lead", "decide": "lead",
             "set-worktree": "git", "done": "git", "status": None}
STATE = re.compile(r"\.agents/work/[^/\s]+/(state/|job\.json|log\.tsv|decisions\.md)|\.user-prompts\.jsonl")
GATES = re.compile(r"\.agents/(scripts|agents|settings|team\.json|models\.json|db-mcp\.json)|\.claude/(settings[^/]*\.json|agents/|hooks/)")
WRITES = re.compile(r"(>|\btee\b|\bsed\s+-i|\brm\b|\bmv\b|\bcp\b|\btruncate\b|\bchmod\b|\bln\b|open\(|write_text|\bperl\s+-p?i)")
HARMLESS_REDIRECT = re.compile(r"\d*>\s*/dev/null|\d*>&\d")
FILE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")


def check_file_edit(role, path):
    if STATE.search(path):
        deny(f"{path} is written only by job.py and task.py.")
    if role != "lead" and GATES.search(path):
        deny(f"teammates never change the team's gates ({path}). Changing them is the user's decision.")
    check_worktree_write(role, path)


def check_worktree_write(role, path):
    if not path:
        return
    real = os.path.realpath(path)
    for job in t.active_jobs():
        wt = os.path.realpath(job["worktree"])
        if real != wt and not real.startswith(wt + os.sep):
            continue
        if role is None and lenient_identity():
            return
        rel = os.path.relpath(real, wt)
        allowed = t.writable_paths(job, role)
        if not t.matches_any(rel, allowed):
            where = f"you may write {', '.join(allowed)}" if allowed else "you hold no task in progress that lets you write here"
            deny(f"{rel} in the {job['id']} worktree is outside your scope as {role or 'an unidentified agent'}; {where}.")
        return


HEREDOC = re.compile(r"(?P<head>[^\n]*?<<-?\s*(?P<q>['\"]?)(?P<tag>\w+)(?P=q)[^\n]*\n)(?P<body>.*?)\n\s*(?P=tag)\b", re.S)
SHELLS = ("bash", "sh", "zsh", "dash", "eval", "source", ".")


def without_data_heredocs(command):
    """Drop heredoc bodies that are data (python -, cat >), keep the ones a shell executes."""
    def strip(m):
        before = m.group("head").split("<<", 1)[0]
        words = re.split(r"[;&|]+", before)[-1].split()
        cmd = words[0].rsplit("/", 1)[-1] if words else ""
        return m.group(0) if cmd in SHELLS else m.group("head")
    return HEREDOC.sub(strip, command)


def script_calls(command):
    command = without_data_heredocs(command)
    lex = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lex.whitespace_split = True
    try:
        tokens = list(lex)
    except ValueError:
        tokens = command.split()
    for i, tok in enumerate(tokens):
        name = tok.rsplit("/", 1)[-1]
        if name not in ("job.py", "task.py"):
            continue
        prev = tokens[i - 1].rsplit("/", 1)[-1] if i else ""
        if i == 0 or prev.startswith("python") or prev in (";", "&&", "||", "|", "then", "do"):
            yield name, tokens[i + 1:]


def check_scripts(role, command):
    for name, args in script_calls(command):
        if name == "job.py":
            sub = args[0] if args else ""
            need = JOB_ROLES.get(sub)
            if need and role != need:
                if role is None and lenient_identity():
                    continue
                deny(f"job.py {sub} is run by the {need} only; this agent is {role or 'unidentified'}.")
        else:
            by = args[args.index("--by") + 1] if "--by" in args and args.index("--by") + 1 < len(args) else None
            if by and by != role:
                if role is None and lenient_identity():
                    continue
                deny(f"task.py --by {by} but this agent is {role or 'unidentified'}. Use your own role.")


def main():
    event = read_input()
    tool, inp = event.get("tool_name", ""), event.get("tool_input") or {}
    role = role_of(event)
    if tool in FILE_TOOLS:
        check_file_edit(role, inp.get("file_path") or inp.get("notebook_path") or "")
        return
    if tool != "Bash":
        return
    command = inp.get("command", "")
    calls = list(script_calls(command))
    if calls:
        check_scripts(role, command)
    elif WRITES.search(HARMLESS_REDIRECT.sub(" ", command)):
        if STATE.search(command):
            deny("job state and logs are written only by job.py and task.py.")
        if role != "lead" and GATES.search(command):
            deny("teammates never change the team's gates. Changing them is the user's decision.")


if __name__ == "__main__":
    main()
