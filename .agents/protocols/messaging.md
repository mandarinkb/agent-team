# Messaging

## Direct between teammates

| From | To | For |
|---|---|---|
| analyst | backend, frontend | root cause, files involved, the contract |
| backend | frontend | API contract details inside the approved spec |
| backend, frontend | git | "ready to stage" with the task id and the files |
| qa | git | "ready to stage" for files in `bruno/` |
| git | spec-reviewer, qa, lead | the tree id, the worktree, `git diff --cached --stat` |
| spec-reviewer, qa | backend, frontend | a fix task path |
| qa | analyst | a reproduction that contradicts the root cause |

Everything else goes to the lead: status, blockers, decision requests, scope questions.

## Shape

```
[J-20261017-orders T-02] fix: fixes/F-03.md
Revision: 4b825dc6...  AC-3 fails: status 200, spec says 422
Run: bru run orders --env local
```

Start with the job and task, then the kind (handoff, fix, ready to stage, tree, blocked, decision). Point at files instead of pasting output.

## Limits

- Never ask another teammate to write outside its scope. Ask the lead.
- Agreement between teammates is input to a decision, never the decision.
- When two teammates disagree on a fact, each runs the check that would prove the other wrong.

## Report to the lead when your part ends

- **Status:** `PASS`, `ISSUES`, or `BLOCKED`.
- **What:** one line per file or finding.
- **Evidence:** commands and decisive output, labeled measured, inferred, or guess.
- **Not checked:** what and why.
- **Decisions:** paths of any requests.
