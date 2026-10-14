# Workflow: retire the old implementation

Adapted from pstack's principle migrate-callers-then-delete-legacy-apis. Once the user has moved traffic and confirmed the new side served it cleanly, remove the old code in one wave so no dual path lingers. Design rules: `team-migration` section 9.

Skills named in a step are the usual choice. Pick another installed skill when it fits the work better, except the four required skills in `.agents/AGENTS.md` (`team-decision`, `team-verify`, `team-parity`, `team-review`).

## When

A migrated unit whose traffic the user moved to the new implementation, after the user decided to retire the old one (D7). Never before.

## Team

lead, analyst, backend, qa, reviewer, git.

## Steps

Copy these into the task list. A step you skip stays in the list with `skip: <reason>`.

1. **lead** Run `new_task.py retire "<unit>"`. Link the unit's migration task and the user's D7 decision in the brief.
2. **analyst** Inventory every reference to the old implementation with `team-investigate` and `blast-radius`: routes, handlers, clients and SDKs, cron jobs, configuration, feature flags, tests, fixtures, documentation, dashboards.
3. **qa** Prove the old path is idle with evidence the user can check, such as access logs or metrics over a window the user names. Silence in a log is a measurement only when the log is known to receive that traffic.
4. **analyst** List the compatibility rules in the new response-mapping layer that only this caller needed. Removing each one is its own decision (D2), not part of this wave by default.
5. **GATE G1 (D7 + D8)** **lead** Present the reference inventory, the idle evidence, and the removal plan with `team-decision`.
6. **backend** Remove the old endpoint, its route, its tests, fixtures, and configuration together on one branch. Leave no dead references. When done, message git "ready to stage".
7. **git** Stage the task's files as in `.agents/protocols/commit-approval.md` step 2 and send the tree id to qa, the reviewer, and the lead.
8. **qa** Use `team-verify` at the tree id: the new endpoint still passes its parity cases against the recorded baseline, the old route returns what the user decided (404, 410, or a redirect), and the build, tests, and linters pass with the old code gone. Search for leftover references and report the command and the result.
9. **reviewer** Use `team-review` at the same tree id and write the review report. Confirm nothing still references the removed code, and that no security check lived only in the removed code.
10. **lead** Triage the review report with `team-review` ("As the lead"). Fixes go back to the implementer, and the team repeats from the staging step with the new tree id, within the round budget in `.agents/protocols/loops.md`.
11. **git** Draft one commit for the task with the final line `Task: <task-id>`.
12. **GATE G2 (D8)** **lead** Send the commit request from `.agents/protocols/commit-approval.md` with both reports and the triage. git commits only through the approval prompt.
13. **lead** Set the unit's state to `retired` in the program `inventory.tsv`.

## Gates

| Gate | Code | User sees | Blocks |
|---|---|---|---|
| G1 | D7 + D8 | Reference inventory, idle evidence, removal plan | Step 6 |
| G2 | D8 | Test and review reports at the same tree id, the lead's triage, staged files, commit message | `git commit` |

## Done when

- No reference to the old implementation remains, shown by the search qa ran.
- The new endpoint still matches its baseline.
- The user approved the commit at the prompt.
- The review report names the same tree id as the test report and has no open "fix before commit" item.
