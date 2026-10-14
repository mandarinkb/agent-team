# Loops, retries, and dead ends

A teammate that repeats the same failing step burns time and tokens without progress. These rules bound every loop. Adapted from pstack: Orchestrate's retry-by-failure-mode and "two retries, then abandon", the babysit skill's three-round limit, the Babysit playbook's one-retry rule for flakes, swarm's respawn-once rule, and the principle attack-the-premise.

## The round budget

A **round** is one pass of fix, stage, verify, and review on the same task. Round 1 is the first verification. Each fix that sends the work back to staging starts the next round.

- **At most three rounds per task.** qa and the reviewer write the round number in their reports. The `gate_reports.py` hook refuses to complete a `verify` or `review` task in round 4 or later unless the report names an approved D9 decision.
- **The same failure twice means stop.** If round N fails for the same reason as round N-1 (the same test, the same DIFF path, the same review finding), do not start another round. Apply attack-the-premise: write down the assumption both fixes shared, and run the check that could disprove it. Then raise D9 with `team-decision`.
- **D9 options** usually include: try a different approach (named), narrow the scope, ask for a missing prerequisite, or stop the task. The user decides. There is no default.

## Retries of a single command or step

Match the retry to the failure, as pstack's Orchestrate does:

| Failure | Next action |
|---|---|
| Ran out of time, memory, or context | Retry once with a smaller scope |
| Network or a service that was not ready | Retry once as is, with a wait that has a time limit |
| Tool or command error | Change the approach, not just the arguments |
| Flaky test | One fresh run. An identical second failure means it is not flaky |
| Unknown | Retry once |

After two failed retries of the same step, stop and report `BLOCKED` to the lead with the exact commands and outputs. Never loop on a command hoping the result changes.

## Waiting for something

To wait for a server or a job, use one command with a time limit, for example:

```bash
for i in $(seq 60); do curl -fsS http://localhost:8081/health && break; sleep 1; done
```

Do not call the same check again and again as separate commands. The loop guard counts those.

## What enforces it

- **`loop_guard.py`** (PreToolUse hook on Bash). It counts how often the same agent runs the same command while the changed files in the working tree stay the same. On the sixth identical call within ten minutes it denies the command and tells the agent to stop and report `BLOCKED`. Editing a file, staging, or any other change to the tree resets the count, because that is progress.
- **`gate_reports.py`** refuses round 4 or later without an approved D9.
- **`team_health.py`** shows the lead which agents are near the loop limit, which tasks are at round 3 or beyond, and which log rows repeat.

## What the lead does

1. Run `python3 .agents/scripts/team_health.py` whenever a teammate reports, and at least every time you check the task list. Act on every warning.
2. A teammate that the loop guard stopped, that repeats a log row, or that stays busy with no new log row for a long time is stuck. Ask it for its status once.
3. If it is still stuck, **stop it** (shutdown request, or the user presses `x` on it) and **spawn a fresh teammate** with a consolidated brief: the original brief, every later instruction, the stuck teammate's last report, its branch or worktree, and the evidence of the loop. Do not keep sending the stuck teammate new instructions. pstack found that chained resumes silently drop directives.
4. If the fresh teammate hits the same wall, it is a dead end. Raise D9 to the user.

## Never

- Never raise the round limit, the loop-guard limit, or a timebox yourself. Changing them is a decision (D11).
- Never relax a check, an assertion, or a parity case to escape a loop. That is a decision (D3) for the user.
