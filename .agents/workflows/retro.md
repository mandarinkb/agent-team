# Workflow: retro

After a job is done, the team learns from it so the next job needs fewer rounds and fewer questions. Adapted from pstack's `reflect`. Nothing changes without the user approving each row.

**Team:** lead alone by default. With the user's decision, three analysts each read the job through one lens and the lead merges their findings.

## Steps

1. **lead** `job.py retro <job>` creates `retro.md`. Offer the retro to the user when the job ends; skip it if the user declines.
2. **lead** Read the job's records, never memory: `log.tsv`, `task.py list`, `fixes/`, `reviews/`, `decisions.md`, `test-report.md`, the hook refusals the teammates reported. Fill the numbers table.
3. **lead** Look through three lenses:
   - **Judgment:** which fix tasks came from an unclear spec or brief, which decisions recurred.
   - **Tooling:** which commands teammates had to discover, which context the user had to supply by hand.
   - **Divergent:** what worked for the wrong reason, which check was skipped, which gate refused something it should have allowed or allowed something it should have refused.
4. **lead** Keep a proposal only if it passes all four criteria in the template: still true in six months, changes what the team does, not already in the target file, and code instead of prose when code can enforce it. Write the rest under "rejected" with the criterion that failed.
5. **User** For each row the user approves, `job.py retro-approve <job> R-<n> --quote "<the user's words>"`.
6. **lead** Apply only approved rows. A row that changes a gate or a rule needs its test in `.agents/tests/test_team.py` to pass, and a new gate needs a case that trips it. Run the tests, then commit outside the job (the commit hook asks the user).
