"""Input and output helpers shared by the hooks."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import teamlib  # noqa: E402,F401


def read_input():
    try:
        return json.load(sys.stdin)
    except ValueError:
        return {}


def role_of(event):
    """'lead' for the main session, the agent type for a teammate, None when it cannot be told."""
    agent_type = event.get("agent_type")
    if agent_type:
        return agent_type.split(":")[-1]
    if event.get("agent_id"):
        return None
    return teamlib.LEAD


def lenient_identity():
    return os.environ.get("TEAM_IDENTITY") == "lenient"


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": decision,
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def deny(reason):
    decide("deny", reason + " Stop and report BLOCKED to the lead with this message. Do not work around it.")


def allow(reason):
    decide("allow", reason)


def ask(reason):
    decide("ask", reason)
