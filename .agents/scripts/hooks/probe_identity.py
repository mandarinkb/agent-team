#!/usr/bin/env python3
"""Identity probe for the first real team run. Does nothing unless TEAM_PROBE=1.

Every gate trusts the agent_type field Claude Code puts in hook input. This hook records
what each hook actually receives, so the user can see whether teammates carry it:

    TEAM_PROBE=1 claude                       start the session, spawn a small team,
                                              let each teammate run one command
    python3 .agents/scripts/hooks/probe_identity.py --report
"""
import json
import os
import sys
from collections import Counter

from hooklib import read_input, teamlib as t

LOG = os.path.join(t.WORK, ".identity-probe.jsonl")
FIELDS = ("hook_event_name", "tool_name", "agent_id", "agent_type", "teammate_name", "session_id")


def report():
    if not os.path.exists(LOG):
        print(f"no probe data at {LOG}; start Claude Code with TEAM_PROBE=1 and run a team")
        return 1
    rows = [json.loads(line) for line in open(LOG, encoding="utf-8") if line.strip()]
    seen = Counter((r.get("agent_type"), bool(r.get("agent_id")), r.get("teammate_name")) for r in rows)
    print("| agent_type | has agent_id | teammate_name | calls |\n|---|---|---|---|")
    for (agent_type, has_id, name), n in seen.most_common():
        print(f"| {agent_type} | {has_id} | {name} | {n} |")
    missing = [k for k in seen if k[1] and not k[0]]
    print("\nVerdict: " + ("FAIL: some teammate calls had an agent_id but no agent_type. Role gates would refuse "
                           "them. Tell the lead before using the team." if missing else
                           "PASS: every call from a subagent or teammate carried agent_type."))
    return 1 if missing else 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        sys.exit(report())
    if os.environ.get("TEAM_PROBE") != "1":
        return
    event = read_input()
    os.makedirs(t.WORK, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": t.now(), **{k: event.get(k) for k in FIELDS}}) + "\n")


if __name__ == "__main__":
    main()
