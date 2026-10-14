# Workflow: migration (PHP to Go and other ports)

Adapted from pstack's Refactoring and Visual parity playbooks and the PHP-to-Go starter kit. Pin the old behavior first, port one unit at a time, and prove parity before traffic moves. The old system stays live until the user moves traffic. Design rules: `team-migration`. For many units, run this inside `.agents/workflows/migration-program.md`.

Skills named in a step are the usual choice. Pick another installed skill when it fits the work better, except the four required skills in `.agents/AGENTS.md` (`team-decision`, `team-verify`, `team-parity`, `team-review`).

## When

Porting an endpoint, job, or module from one implementation to another while callers must see the same behavior. One unit per task. The first unit is the pilot: run it end to end before starting the next.

## Team

lead, analyst, backend, qa, reviewer, git.

## Steps

Copy these into the task list. A step you skip stays in the list with `skip: <reason>`.

1. **lead** Run `new_task.py migration "<METHOD path or unit name>"`. Fill `brief.md` with the old handler location, the target package, the expected file scope, and, inside a program, the program task id and the rulings from `migration-plan.md` that apply. Confirm every `depends_on` unit in the program inventory is committed.
2. **analyst** Use `team-investigate` on the old handler: inputs, outputs, side effects, error paths, and hidden behavior such as type coercion and default values. List every caller you can prove (web, mobile, cron, other services). An unproven caller is an open risk in the brief. When the old code does something that looks like a bug, read its history before deciding anything (`team-migration` section 10).
3. **qa** Use `team-parity`. Write `cases.jsonl` covering the happy path, empty results, not-found, validation errors, auth failures, and every item on the PHP-to-Go checklist in `.agents/templates/brief.md`. Record the baseline from the old system with synthetic accounts only. Never record customer data.
4. **analyst** Write the port plan with `team-migration`: the target domain types, the response-mapping layer that reproduces the old behavior at the boundary, the known risky differences, any data migration with its rerun and rollback answers (section 8), and any ignored response paths with a reason for each.
5. **GATE G1 (D8, plus D3 for each proposed ignored path)** **lead** Present the plan, the case list, and every proposed ignored path to the user with `team-decision`.
6. **backend** Port to the target on its own branch, rebased on a clean trunk. Do not delete, redirect, or disable the old endpoint. Keep the domain code in its target shape and put every compatibility rule (string IDs, `[]` for empty lists, error shapes) in the response-mapping layer, each one naming the parity case that requires it. Never edit the baseline, the case list, or the parity config to make a diff pass. When done, message git "ready to stage". qa does the same for the case files.
7. **git** Stage the task's files as in `.agents/protocols/commit-approval.md` step 2 and send the tree id to qa, the reviewer, and the lead.
8. **qa** Run `parity.py check --json` against the new endpoint built from that tree. Exit 0 is the only pass. Exit 3 means a case was unreachable, which is `INCONCLUSIVE`. Send each DIFF to backend with the path and values. After a fix, git restages and qa rechecks at the new tree id, until exit 0, until a DIFF needs a decision, or until the round budget in `.agents/protocols/loops.md` runs out. The same DIFF twice means stop and raise D9. If the baseline itself looks wrong, stop and raise it (D3). Never fix it by hand.
9. **GATE (D3, when needed)** A DIFF where the new behavior is arguably better is still a DIFF. **lead** raises it to the user. Keep the old behavior until the user accepts the change.
10. **qa** Use `team-verify` at the tree id for side effects the parity check cannot see: database writes, messages sent, files written, and each data migration's rerun and crash-resume proof. When the plan claims a performance result, check it with `benchmark-checklist`. Write the test report with the MATCH, DIFF, and UNREACHABLE counts, and complete the `verify` task.
11. **reviewer** Use `team-review` at the same tree id and write the review report. Compare the security checks of the old handler with the new one (auth, object-level access, rate limits, input validation): a check the port dropped is a critical finding.
12. **lead** Triage the review report with `team-review` ("As the lead"). Fixes go back to the implementer, and the team repeats from the staging step with the new tree id, within the round budget in `.agents/protocols/loops.md`.
13. **git** Draft one commit for the task with the final line `Task: <task-id>`. It carries the baseline cases, the new handler, and the route wiring that stays disabled.
14. **GATE G2 (D8)** **lead** Send the commit request from `.agents/protocols/commit-approval.md` with both reports and the triage. git commits only through the approval prompt.
15. **lead** Report to the user in Thai. Inside a program, update the unit's row in `inventory.tsv`. Moving traffic and removing the old code are separate decisions (D7), never part of this task. Retirement runs `.agents/workflows/migration-retire.md`.

## Gates

| Gate | Code | User sees | Blocks |
|---|---|---|---|
| G1 | D8 + D3 | Port plan, case list, proposed ignored paths with reasons | Step 6 |
| DIFF | D3 | Each accepted behavior change | Completing step 8 |
| G2 | D8 | Test and review reports at the same tree id, the lead's triage, staged files, commit message | `git commit` |

## Done when

- `parity.py check` exits 0 against the new endpoint, measured by qa, with every ignored path approved in `decisions.md`.
- The old endpoint is untouched and still reachable.
- The user approved the commit at the prompt.
- The review report names the same tree id as the test report and has no open "fix before commit" item.
