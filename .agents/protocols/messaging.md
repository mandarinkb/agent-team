# Handoffs

Every teammate is a subagent. The lead spawns it for one step with a brief, it does that step, reports to the lead, and ends. Teammates never message each other. Every handoff goes through the lead and through files on disk, as in pstack ("keep sibling communication upward only").

## Spawning

- Use the Agent tool with `subagent_type` set to the role. Leave `name` unset.
- One spawn per step. A fix round is a fresh spawn that reads the fix task. Never rely on what an earlier spawn remembers.
- Steps that do not depend on each other run in parallel with `run_in_background: true`: qa writing the Bruno collection while the implementers code, implementers of tasks with separate scopes, competing analysts.
- Wait for a report before spawning a step that needs it. Never write a report yourself or guess one that has not arrived.

## The brief

The brief is the product. A fresh subagent knows only what it says and what the files say.

```
Role: spec-reviewer   Job: J-20261017-orders   Task: T-02   Round: 2
Step: _run.md step 5
Worktree: ../app-wt/J-20261017-orders
Tree: 4b825dc6...  (previous: 9f1e2a07...)
Read: spec.md, tasks/T-02.md, fixes/F-03.md
Report: verdict, review path, fix task paths
```

Name the job, task, round, and the workflow step. Give paths and ids, not pasted content. Include the user's exact words for any decision the step depends on.

## What each report carries to the next step

| Report from | Carries | The lead spawns next |
|---|---|---|
| qa (reproduction) | the command, failing output, commit | analyst |
| analyst | `investigation.md`, decision requests | analyst (to refute a rival), or the lead writes the spec |
| backend, frontend | "ready to stage", task id, files | git |
| qa (Bruno written) | "ready to stage" for `bruno/<job>/` | git |
| git | tree id, worktree, `git diff --cached --stat` | spec-reviewer, then qa |
| spec-reviewer, qa | verdict, fix task paths | the owner, with the fix task |
| qa | a reproduction that contradicts the root cause | analyst |

Status, blockers, decision requests, and scope questions also go to the lead in the report.

## Limits

- Never ask in a report for another teammate to write outside its scope. Ask the lead.
- Agreement between teammates is input to a decision, never the decision.
- When two teammates disagree on a fact, the lead spawns each to run the check that would prove the other wrong.

## Report to the lead when your step ends

- **Status:** `PASS`, `ISSUES`, or `BLOCKED`.
- **What:** one line per file or finding.
- **Evidence:** commands and decisive output, labeled measured, inferred, or guess.
- **Not checked:** what and why.
- **Decisions:** paths of any requests.
- **Next:** the handoff from the table above, with the ids and paths it needs.
