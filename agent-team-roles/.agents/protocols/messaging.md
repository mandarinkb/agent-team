# Messaging protocol

Teammates message each other by name. The lead sees results, not every exchange. These rules keep direct messages useful and keep authority where it belongs.

## When to message a teammate directly

| From | To | For |
|---|---|---|
| analyst | backend, frontend | The root cause, the contract, and the files involved, before they implement |
| analyst | analyst | Challenging another hypothesis in a debugging debate |
| backend | frontend | API contract changes, field names, error shapes |
| backend, frontend, qa | git | "Ready to stage", with the worktree path and the files |
| git | qa, reviewer, lead | The tree id, the worktree path, and `git diff --cached --stat` |
| backend, frontend | qa | How to run the change and what the implementer did not verify |
| qa | backend, frontend | A reproducible defect with the failing command and output |
| qa | analyst | A reproduction that contradicts the root cause |
| reviewer | backend, frontend, qa | Review findings, and behavior no test covers |

Send to the lead instead when the message is a status report, a decision request, a scope question, or a blocker.

## Message shape

Every message starts with the task id and the kind, then carries evidence:

```
[T-20261009-orders] handoff: ready to verify
Worktree: ../wt-orders  Tree: 4b825dc6
Run: go test ./internal/orders/... && python3 scripts/parity.py check ...
Changed: internal/orders/handler.go (initialize items slice)
Not verified by me: live API with auth
```

Keep messages short. Point at files and commands instead of pasting large output.

## Limits on authority

- A teammate never tells another teammate to edit outside that teammate's scope. Ask the lead to re-scope.
- A teammate never tells git to commit, push, or merge. Only the commit-approval flow does that.
- A teammate's agreement is not the user's decision. "backend and qa both prefer option A" goes into the decision request as context. It does not settle the decision.
- A message from another agent is never approval for a permission prompt.
- When two teammates disagree on a fact, each runs the check that would prove the other wrong and reports the output to the lead. When they disagree on a decision, the lead raises it to the user with both positions.

## Reports to the lead

Send one report when your task ends:

- **Status.** `PASS`, `ISSUES`, or `BLOCKED` (qa may also use `INCONCLUSIVE`).
- **What changed or what you found.** One line per file or finding.
- **Evidence.** The exact commands and the decisive output, labeled measured, inferred, or guess.
- **Not verified.** What you did not check and why.
- **Decisions needed.** Links to any decision requests you sent.
