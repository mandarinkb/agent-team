# Workflow: bug fix

Adapted from pstack's Bug fix playbook. Every shipped line traces to runtime evidence. A change that "might help" is a hypothesis, not a fix, and it does not ship.

Skills named in a step are the usual choice. Pick another installed skill when it fits the work better, except the four required skills in `.agents/AGENTS.md` (`team-decision`, `team-verify`, `team-parity`, `team-review`).

## When

A defect in a running system whose cause is not yet proven. A typo or a one-line fix with an obvious test does not need a team.

## Team

lead, analyst (one to three for competing hypotheses), backend or frontend, qa, reviewer, git. The reviewer may be skipped only for a single-file, low-risk fix, with the reason logged.

## Steps

Copy these into the task list. A step you skip stays in the list with `skip: <reason>`.

1. **lead** Run `new_task.py bug "<title>"`. Fill `brief.md` with the symptom, where it appears, who reported it, and the file scope you expect. Spawn the team with the brief path.
2. **qa** Reproduce on the same surface the user sees: the API, the UI, or the job. Write the reproduction as a script or a failing test under the verification paths. Record the command, the failing output, and the revision. If it will not reproduce, tighten the conditions or add instrumentation until it does. Report to the lead and send the reproduction to the analyst.
3. **analyst** Use `team-investigate` to map the code path, then `team-root-cause`. List the candidate causes and eliminate them with runtime evidence, cutting the largest share of the problem each round. For an unclear bug, the lead spawns two or three analysts, one per hypothesis. Each one tries to disprove the others and reports only what survives.
4. **analyst** Confirm the surviving mechanism with evidence, such as a log line, a debugger value, or a reverted line that makes the bug vanish. Write the fix options with `team-design-options` when more than one fix is viable or the fix changes behavior.
5. **GATE G1 (D8, plus D1 or D2 when they apply)** **lead** Present the root cause, the evidence, and the fix plan to the user with `team-decision`. Implementation waits for the user's answer.
6. **backend/frontend** Implement the approved fix, the smallest change the evidence justifies, on its own branch or worktree. When done, message git "ready to stage". qa does the same for the reproduction test from step 2.
7. **git** Stage the task's files as in `.agents/protocols/commit-approval.md` step 2 and send the tree id to qa, the reviewer, and the lead.
8. **qa** Use `team-verify` at the tree id. Run the reproduction from step 2. It must now pass. Run the regression tests around the change. Confirm the new or updated test fails on the old revision and quote that output in the report, because the test and the fix land in one commit. Write the test report and complete the `verify` task.
9. **reviewer** Use `team-review` at the same tree id and write the review report. Required when the change touches more than one file or a high-risk area (auth, money, personal data, permissions, data migrations). Otherwise the lead may mark this step `skip: <reason>` and log it.
10. **lead** Triage the review report with `team-review` ("As the lead"). Fixes go back to the implementer, and the team repeats from the staging step with the new tree id, within the round budget in `.agents/protocols/loops.md`.
11. **git** Draft one commit for the task with the final line `Task: <task-id>`.
12. **GATE G2 (D8)** **lead** Send the commit request from `.agents/protocols/commit-approval.md` with both reports and the triage. git commits only through the approval prompt.
13. **lead** Report to the user in Thai: what was broken, the root cause, the fix, how it was verified, and both report paths.

## Gates

| Gate | Code | User sees | Blocks |
|---|---|---|---|
| G1 | D8, D1/D2 | Root cause with evidence, fix options, recommendation | Step 6 |
| G2 | D8 | Test and review reports at the same tree id, the lead's triage, staged files, commit message | `git commit` |

## Done when

- The reproduction from step 2 fails on the old revision and passes on the new one, measured by qa.
- The test report verdict is `PASS`, or the user accepted every listed gap in `decisions.md`.
- The user approved the commit at the prompt.
- The review report names the same tree id as the test report and has no open "fix before commit" item, or review was skipped with a logged reason.
