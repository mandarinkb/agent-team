#!/usr/bin/env python3
"""UserPromptSubmit hook. Appends what the user typed to .agents/work/.user-prompts.jsonl.

job.py accepts an approval or a decision only when the user's words appear in this log,
so a teammate's message can never stand in for the user. Turns that Claude Code starts
on its own (teammate messages, task notifications) are skipped.
"""
import json
import os
import re

from hooklib import read_input, teamlib

SYSTEM_TURN = re.compile(r"^\s*<(teammate-message|task-notification|system-reminder|agent-message|cross-session)", re.I)


def main():
    event = read_input()
    prompt = event.get("prompt") or ""
    if not prompt.strip() or event.get("agent_id") or SYSTEM_TURN.match(prompt):
        return
    os.makedirs(teamlib.WORK, exist_ok=True)
    with open(teamlib.USER_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": teamlib.now(), "session": event.get("session_id"), "prompt": prompt},
                           ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
