#!/usr/bin/env python3
"""PreToolUse hook on Bash: no new task starts once a usage window is nearly spent.

When the 5-hour or 7-day window recorded by record_limits.py is at or above the
threshold (team.json "limit_threshold", default 95), `task.py ... in_progress` is
refused. Work already in progress may finish its step and record it, so nothing is left
half done when the limit hits. A window whose resets_at has passed is ignored, and with
no recorded data (an API key, or before the first response) the hook does nothing.
"""
import os
import time

from guard_task import script_calls
from hooklib import deny, read_input, teamlib as t
from record_limits import LIMITS

WINDOWS = {"five_hour": "5-hour", "seven_day": "7-day"}


def spent_windows(threshold, now=None):
    now = now or time.time()
    try:
        limits = t.read_json(LIMITS).get("rate_limits") or {}
    except (OSError, ValueError):
        return []
    spent = []
    for key, label in WINDOWS.items():
        w = limits.get(key) or {}
        used, resets = w.get("used_percentage"), w.get("resets_at")
        if used is None or (resets and resets <= now):
            continue
        if used >= threshold:
            when = time.strftime("%H:%M on %d %b", time.localtime(resets)) if resets else "unknown"
            spent.append(f"{label} window at {used:g}% (resets {when})")
    return spent


def main():
    event = read_input()
    if event.get("tool_name") != "Bash":
        return
    command = (event.get("tool_input") or {}).get("command", "")
    starts = [args for name, args in script_calls(command)
              if name == "task.py" and len(args) >= 4 and args[0] == "set" and args[3] == "in_progress"]
    if not starts:
        return
    threshold = float(t.config().get("limit_threshold", 95))
    spent = spent_windows(threshold)
    if spent:
        deny(f"Usage limit guard: {'; '.join(spent)}, threshold {threshold:g}%. Do not start a new task. "
             "Finish the step you are on, record it with task.py, and report to the lead, who tells the user "
             "when work can resume (job.py resume picks it up).")


if __name__ == "__main__":
    main()
