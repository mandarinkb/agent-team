---
name: team-review
description: Review the staged change for correctness, root causes, security, structure, verification, complexity, and clutter, write the review report, and, as the lead, triage it into fix, consider, noted, and dismissed. Required for every review task. Use after qa has the same tree id and before the commit request.
when_to_use: Required for the reviewer on every review task and for the lead triaging a review report. Also usable by an implementer checking its own diff before handoff. Triggers: review this change, code review, check code quality, security review, anything wrong with this diff, triage the review.
---

# Team review

Adapted from pstack's interrogate skill (rubric, code-quality lens, lead judgment), deslop, and no-comments.

## As the reviewer

### Inputs

- The tree id from git, and the worktree path. Run `git -C <worktree> write-tree` and confirm it prints the same id. If it does not, stop, set the verdict to `BLOCKED`, and tell git and the lead.
- The staged diff: `git -C <worktree> diff --cached`, and the files around it that the diff calls or is called by.
- The brief, the approved decisions in `decisions.md`, and `design.md` when there is one. Assume the approved intent is correct and review the execution.

### Lenses

Apply each lens that fits and say in the report which ones you applied. A small fix does not need an architecture review, but every review considers Correctness and Security.

1. **Correctness.** Edge cases (empty, null, boundary values), error handling, concurrency, and what happens if the operation runs twice or crashes halfway. For a suspected bug, trace the call path that triggers it. Do not just say "this could be nil".
2. **Root cause or symptom.** Guards that hide a broken invariant, retries that hide a broken contract, casts that hide a modeling error, a fix in one module that belongs in another module's contract, and a "don't do X" comment where a type, lint, or check would make X impossible.
3. **Security.** For each finding, trace the input path through the code and show it.
   - User input reaching a dangerous sink (SQL, shell, file paths, templates or HTML, deserialization) without parsing or escaping.
   - Authentication and authorization on every new or changed endpoint, including object-level checks (can user A read user B's order?).
   - Secrets, tokens, or personal data in code, logs, error messages, fixtures, or baselines.
   - Time-of-check to time-of-use gaps in security-critical paths.
   - For a port: a check the old code did that the new code skips, such as an auth middleware, a rate limit, or input validation.
4. **Structure.** Validation at system boundaries and trusted types inside, logic in the right layer, no new scattered `if` branches in unrelated code, no file pushed past about 1,000 lines without a reason, no old and new code paths side by side without an approved decision. For a migration, compatibility behavior lives in the response-mapping layer, each rule naming its parity case.
5. **Verification.** Do the tests check the required result or only that a mock was called? Is there a test for the bug being fixed? Would the tests fail if the behavior broke? Does the code check the real thing rather than a cached or derived value? Cross-check against qa's test report at the same tree id.
6. **Complexity budget.** Abstractions with one caller, configuration for cases that do not exist, dead code, unused imports and parameters, compatibility paths no caller needs. Simpler is better unless simpler is wrong. Three similar lines beat a premature abstraction.
7. **Clutter.** Comments that narrate the obvious, defensive checks on trusted paths, `any` or casts used to silence the type checker, deep nesting that early returns would flatten. Keep a comment only for a non-obvious reason the code cannot show.
8. **Matches the decision.** The diff implements the option the user approved and nothing more.

### High-risk changes

If the diff touches authentication or authorization, money or billing, personal data, permission boundaries, a data migration, cryptography, or anything the brief marks high risk:

1. Mark the report `High risk: ใช่` with the areas.
2. Write a decision request (D10) with `team-decision`: option A, a second review of the same tree id by another model the lead names (state the rough extra cost); option B, proceed with this single review. Recommend one.
3. Finish your own review either way. The second review, when the user approves it, uses this skill and its own report section, and the lead merges both: findings raised independently by both reviewers carry the most weight.

### Judging your own findings

- A hypothetical is a finding only if a real caller can trigger it. Trace the call site.
- "I would have done it differently" is not a finding.
- Findings that are all nits mean the code is probably fine. Say so.
- Report every real problem you can show, not only the first.

### Report

Fill `.agents/work/<task-id>/review-report.md` from the template, leaving the lead's section untouched. Set **Round** to the same round number qa uses. A finding that comes back unresolved after a fix is a sign of a loop: say so in the report. Leave no `<fill` placeholder. The `gate_reports.py` hook will not let the `review` task complete until the report has a verdict and the tree id.

| Severity | Meaning |
|---|---|
| `critical` | Bug, data loss, security issue, broken behavior |
| `warning` | Maintainability or correctness risk that will cause pain |
| `nit` | Style or small improvement |

Each finding: severity, `file:line`, the problem, the evidence, and a concrete suggestion when you have one. Zero findings is a valid review: set the verdict to `NO_FINDINGS`.

Then message the implementer and the lead: the verdict, the report path, and the critical findings.

### Re-review

After a fix, git sends a new tree id. Review the change between the old and new tree (`git diff <old-tree> <new-tree>`), confirm each "fix before commit" finding is resolved, check the fix did not add new problems, and update the Revision and the "หลังแก้" line the lead will read.

## As the lead

Triage the report. You are a pragmatic senior engineer, not an aggregator. You know the context the reviewer did not see: the brief, the decisions, what comes in later tasks.

1. Put every finding in exactly one group in the report's lead section:
   - **แก้ก่อน commit (fix before commit).** Real issues of correctness, security, or maintainability that would block a careful human review.
   - **ควรพิจารณา (consider).** Legitimate points where the cost of fixing now is unclear. If fixing one would change the approved design or behavior, raise it to the user as a decision (D2). Do not decide it.
   - **รับทราบ (noted).** Valid but not actionable now.
   - **ปัดตก (dismissed).** Wrong, out of scope, or a matter of taste. Give the reason in one line. Dismissing a `critical` finding is a decision (D3) for the user, never yours alone.
2. Watch for the usual false positives: a null path no caller can reach, a pattern that matches the rest of the codebase, a suggestion to edit code outside the diff, a premature abstraction.
3. Take security and correctness findings seriously even from one reviewer. Findings raised by two reviewers independently are the strongest signal.
4. If "fix before commit" has more than five items, filter harder or tell the user the change may need to be rethought.
5. Send the "fix before commit" items to the implementer. After the fix, git restages, qa reverifies, and the reviewer re-reviews at the new tree id.
6. Replace every `<lead` placeholder before the commit request. `guard_git.py` blocks the commit while one remains.

The dismissed group is not busywork. It shows the user what was rejected and why, so the user can overrule you.
