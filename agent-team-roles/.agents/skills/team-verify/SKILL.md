---
name: team-verify
description: Independently verify a change on the real surface and write the test report the user reads. Use for every verify task. Only the qa teammate runs this, and never on work it wrote.
when_to_use: Required for qa on every verify task. Triggers: verify, test this change, is it correct, write the test report, ready to verify at a tree id.
---

# Team verify

Adapted from pstack's principles prove-it-works and test-behavior-not-implementation, the tdd skill, and the swarm verdict rules.

## Before you start

- Get the tree id and the worktree path from git. In that worktree, confirm `git write-tree` prints the same id and `git diff --stat` shows no unstaged change in the scope. Record the tree id as the report's Revision. If anything changes after that, git restages and you verify the new tree id.
- Do not read the implementer's report as evidence. Run everything yourself.
- If you wrote any of the production code under test, stop and tell the lead.

## What to run

1. **The reproduction or acceptance tests from the brief.** For a bug, show the failing output on the old revision and the passing output on the new one.
2. **Prove each new test can fail.** Run it against the old revision, or temporarily break the behavior it checks, and confirm it goes red for the right reason. Quote the failure content, not the assertion line. An exception, an empty result, and a real mismatch all print red, and only the predicted mismatch proves the test measures the bug.
3. **The real surface.** Call the API, drive the UI, or run the job the way a client does. A passing unit test shows branch behavior, not that the feature works.
4. **Regression tests** around the changed code.
5. **Side effects** the change should or should not have: database rows, messages, files, emails. Check absence when the contract requires it.
6. **For a migration,** run `team-parity` and include its counts.

A good test checks the required result, not the implementation. A test that only checks that a mock was called, or that compares against a value computed by the same code under test, does not count.

## Verdict

| Verdict | Use when |
|---|---|
| `PASS` | Every check passed on the real surface, and no gap is left unaccepted |
| `ISSUES` | You proved at least one defect. List every defect you can prove, not only the first |
| `BLOCKED` | You could not run the checks because the environment or a prerequisite is missing |
| `INCONCLUSIVE` | You ran the checks but the result does not settle the question. This is not a pass |

## Report

Fill `.agents/work/<task-id>/test-report.md` from the template. Set **Round** to this pass's number: 1 for the first verification, plus one for each fix since. If this round fails for the same reason as the last one, say so in the report and tell the lead, who stops the loop (`.agents/protocols/loops.md`). Leave no `<fill` placeholder. The `gate_reports.py` hook will not let you complete the `verify` task until the report has a verdict and a revision SHA.

Then send the lead and the implementer a short message: the verdict, the report path, and the defects or gaps.
