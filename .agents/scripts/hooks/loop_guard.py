#!/usr/bin/env python3
"""PreToolUse hook on Bash: stop an agent that repeats the same command without progress.

The key is the agent, the command, and a fingerprint of the working tree (each changed
file with its modification time). Editing or staging a file changes the fingerprint, so
honest iteration is never counted. The sixth identical call within ten minutes is
denied. Adapted from agent-team-roles. The limits are team rules: changing them
(LOOP_GUARD_MAX, LOOP_GUARD_WINDOW) is the user's decision.
"""
import hashlib
import json
import os
import re
import subprocess
import time

from hooklib import deny, read_input, teamlib as t

MAX = int(os.environ.get("LOOP_GUARD_MAX", "6"))
WINDOW = int(os.environ.get("LOOP_GUARD_WINDOW", "600"))


def tree_fingerprint(cwd):
    try:
        out = subprocess.run(["git", "-C", cwd, "status", "--porcelain", "--untracked-files=all"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return "no-git"
    if out.returncode != 0:
        return "no-git"
    parts = []
    for line in out.stdout.splitlines():
        path = line[3:].split(" -> ")[-1].strip('"')
        if ".agents/work/" in path:
            continue  # the team's own records are not progress
        try:
            mtime = os.stat(os.path.join(cwd, path)).st_mtime_ns
        except OSError:
            mtime = 0
        parts.append(f"{line[:2]}|{path}|{mtime}")
    return hashlib.sha256("\n".join(sorted(parts)).encode()).hexdigest()


def main():
    event = read_input()
    if event.get("tool_name") != "Bash":
        return
    command = re.sub(r"\s+", " ", (event.get("tool_input") or {}).get("command", "")).strip()
    if not command:
        return
    cwd = event.get("cwd") or os.getcwd()
    agent = event.get("agent_id") or event.get("agent_type") or f"session-{event.get('session_id', 'unknown')}"
    state_dir = os.path.join(t.WORK, ".loop-guard")
    try:
        os.makedirs(state_dir, exist_ok=True)
    except OSError:
        return
    path = os.path.join(state_dir, re.sub(r"[^A-Za-z0-9._-]", "_", agent) + ".json")
    now = time.time()
    try:
        with open(path, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {"agent": agent, "calls": {}}
    key = hashlib.sha256(f"{command}\n{tree_fingerprint(cwd)}".encode()).hexdigest()
    calls = {}
    for k, v in state.get("calls", {}).items():
        recent = [x for x in v.get("times", []) if now - x < WINDOW]
        if recent:
            calls[k] = {"command": v.get("command", ""), "times": recent}
    entry = calls.setdefault(key, {"command": command[:300], "times": []})
    entry["times"].append(now)
    state["calls"] = calls
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, path)
    if len(entry["times"]) >= MAX:
        deny(f"Loop guard: this exact command ran {len(entry['times'])} times in {WINDOW // 60} minutes with no "
             "change to the working tree. Report the command, its last output, and what you assumed each time. "
             "To wait for a service, use one command with a time limit.")


if __name__ == "__main__":
    main()
