#!/usr/bin/env python3
"""Status line helper: save the rate-limit windows Claude Code sends the status line.

Agents and hooks never receive usage limits; only the status line does. Pipe the status
line's input through this script and limit_guard.py can read the result:

    input=$(cat); echo "$input" | python3 "<project>/.agents/scripts/hooks/record_limits.py"

It prints nothing and never fails the status line.
"""
import json
import os
import sys

from hooklib import teamlib as t

LIMITS = os.path.join(t.WORK, ".rate-limits.json")


def main():
    try:
        data = json.load(sys.stdin)
        limits = data.get("rate_limits")
        if not limits:
            return
        os.makedirs(t.WORK, exist_ok=True)
        tmp = f"{LIMITS}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"recorded": t.now(), "rate_limits": limits}, f)
        os.replace(tmp, LIMITS)
    except Exception:  # the status line must keep working whatever happens here
        pass


if __name__ == "__main__":
    main()
