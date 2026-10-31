# Workflow: bug fix

Every line that ships traces to runtime evidence. A change that "might help" is a hypothesis and does not ship.

**Team:** lead, qa, analyst (one to three for competing hypotheses), backend or frontend, spec-reviewer, git.

## Before the spec

1. **lead** `job.py new bug "<symptom>" [--api]`. Grill the user: the symptom, where it shows, how often, what "fixed" looks like, what must not change. Spawn qa with `grill-notes.md`.
2. **qa** Reproduce on the surface the user sees. For an API, a Bruno request that fails today. Record the command, the failing output, and the commit. Report it. The lead spawns the analyst with it.
3. **analyst** Find the root cause with runtime evidence: list candidate causes, cut the space in half each round, confirm the survivor with a log line, a query, or a reverted line that makes the bug vanish. Write `investigation.md`. If more than one fix is viable, write the options. With competing hypotheses, the lead spawns one analyst per hypothesis in parallel, then spawns each again with the others' `investigation` notes to try to refute them.
4. **lead** `job.py grill-done`. Write `spec.md`: the root cause with its evidence, the fix, and acceptance criteria. AC-1 is always "the reproduction from step 2 passes". Add one criterion for each behavior that must not change. Add tasks.
5. **Gate G1** The user approves the spec and tasks. `job.py approve`.

## The run

Follow `_run.md`. In step 6, qa also proves the reproduction fails on the job's base commit and passes on the tree, and quotes both outputs in the test report.
