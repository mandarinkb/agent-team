# Workflow: feature

Adapted from pstack's Feature playbook and the architect skill. The design is chosen by the user from real alternatives before anyone writes production code.

Skills named in a step are the usual choice. Pick another installed skill when it fits the work better, except the four required skills in `.agents/AGENTS.md` (`team-decision`, `team-verify`, `team-parity`, `team-review`).

## When

New behavior, or a change to existing behavior, that touches more than one file or crosses a module boundary.

## Team

lead, analyst, backend and/or frontend, qa, reviewer, git.

## Steps

Copy these into the task list. A step you skip stays in the list with `skip: <reason>`.

1. **lead** Run `new_task.py feature "<title>"`. Fill `brief.md` with the goal, the user who benefits, the acceptance criteria you were given, and the expected file scope. Spawn the team with the brief path.
2. **analyst** Use `team-investigate` on the affected subsystem: entry points, data flow, owners, and callers. Name the data shape the feature is built around.
3. **analyst** Use `team-design-options`. Write the caller's usage first, then at least two structurally different designs with type and signature sketches, and screen both against the red flags. Ask backend, frontend, and qa for their cost estimates and for what each design would take to verify.
4. **GATE G1 (D8 + D1)** **lead** Present the designs and the recommendation with `team-decision`. Record the choice.
5. **lead** Split the approved design into tasks with disjoint file scopes and dependencies in the task list. Fill one brief per writer from `.agents/templates/brief.md`. Tasks that write the same file run one after the other.
6. **qa** In parallel with step 7, write the acceptance tests from the brief and the approved design, not from the implementation. Confirm each test fails before the feature exists.
7. **backend/frontend** Implement against the approved design on separate branches or worktrees. A change to the design or contract is a decision (D2). Stop and raise it instead of absorbing it. When done, message git "ready to stage". qa does the same for its acceptance tests.
8. **git** Stage the task's files as in `.agents/protocols/commit-approval.md` step 2 and send the tree id to qa, the reviewer, and the lead.
9. **qa** Use `team-verify` at the tree id on the real surface. Run the acceptance tests, the regression tests, and the end-to-end path a user takes. Write the test report and complete the `verify` task.
10. **reviewer** Use `team-review` at the same tree id and write the review report.
11. **lead** Triage the review report with `team-review` ("As the lead"). Fixes go back to the implementer, and the team repeats from the staging step with the new tree id, within the round budget in `.agents/protocols/loops.md`.
12. **git** Draft one commit for the task with the final line `Task: <task-id>`. If the user wants several commits, such as types, logic, wiring, and tests, the lead asks first, and the hook warns the user on each partial commit.
13. **GATE G2 (D8)** **lead** Send the commit request from `.agents/protocols/commit-approval.md` with both reports and the triage. git commits only through the approval prompt.
14. **lead** Report to the user in Thai: what was built, which design was chosen and why, both report paths, and anything left open.

## Gates

| Gate | Code | User sees | Blocks |
|---|---|---|---|
| G1 | D8 + D1 | Usage sketch, two or more designs, costs, risks, recommendation | Steps 5 to 7 |
| G2 | D8 | Test and review reports at the same tree id, the lead's triage, staged files, commit message | `git commit` |

## Done when

- Every acceptance criterion in the brief maps to a passing check in the test report, measured by qa.
- The implementation matches the approved design, or each deviation is recorded as a decision.
- The user approved the commit at the prompt.
- The review report names the same tree id as the test report and has no open "fix before commit" item.
