#!/usr/bin/env python3
"""PreToolUse hook for Bash: stop an agent that repeats the same command without making progress.

The key is the agent, the command, and a fingerprint of the working tree (each changed file with its
modification time). Editing or staging a file changes the fingerprint, so honest iteration is never
counted as a loop. When the same key is seen LOOP_GUARD_MAX times within LOOP_GUARD_WINDOW seconds,
the hook denies the command and tells the agent to stop and report BLOCKED to the lead.

Defaults: 6 calls in 600 seconds. State lives in .agents/work/.loop-guard/ (not committed).
The limits are part of the team's rules. Changing them is the user's decision (D11).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

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
        if path.startswith(".agents/work/") or "/.agents/work/" in path:
            continue  # the team's own records, including this hook's state, are not progress
        try:
            mtime = os.stat(os.path.join(cwd, path)).st_mtime_ns
        except OSError:
            mtime = 0
        parts.append(f"{line[:2]}|{path}|{mtime}")
    return hashlib.sha256("\n".join(sorted(parts)).encode()).hexdigest()


def normalize(command):
    return re.sub(r"\s+", " ", command).strip()


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    command = normalize(data.get("tool_input", {}).get("command", ""))
    if not command:
        return 0
    cwd = data.get("cwd") or os.getcwd()
    root = os.environ.get("CLAUDE_PROJECT_DIR") or cwd
    agent = data.get("agent_id") or data.get("agent_type") or f"session-{data.get('session_id', 'unknown')}"
    state_dir = os.path.join(root, ".agents", "work", ".loop-guard")
    try:
        os.makedirs(state_dir, exist_ok=True)
    except OSError:
        return 0
    path = os.path.join(state_dir, re.sub(r"[^A-Za-z0-9._-]", "_", agent) + ".json")
    now = time.time()
    try:
        state = json.load(open(path, encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {"agent": agent, "calls": {}}
    key = hashlib.sha256(f"{command}\n{tree_fingerprint(cwd)}".encode()).hexdigest()
    calls = {}
    for k, v in state.get("calls", {}).items():
        recent = [t for t in v.get("times", []) if now - t < WINDOW]
        if recent:
            calls[k] = {"command": v.get("command", ""), "times": recent}
    entry = calls.setdefault(key, {"command": command[:300], "times": []})
    entry["times"].append(now)
    state["calls"] = calls
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, path)
    count = len(entry["times"])
    if count < MAX:
        return 0
    reason = (f"Loop guard: you have run this exact command {count} times in {WINDOW // 60} minutes "
              f"with no change to the working tree. Stop. Do not retry it. Report BLOCKED to the lead with "
              f"the command, its last output, and what you assumed each time "
              f"(.agents/protocols/loops.md). To wait for a service, use one command with a time limit.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
