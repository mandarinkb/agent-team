# Workflow: migration

Moving behavior from an old implementation to a new one, such as a PHP endpoint to Go. The old behavior is the spec unless the user decides otherwise.

**Team:** lead, analyst, qa, backend, spec-reviewer, git.

## Before the spec

1. **lead** `job.py new migration "<unit>" --api`. Grill the user: which units, which environments, what may differ, when the old code is retired (a separate job, never this one).
2. **analyst** Inventory the unit: routes, handlers, callers, side effects, tables and columns written, odd behaviors and their history. Write `investigation.md`.
3. **qa** Record the baseline from the old system before any new code exists: a Bruno collection with an env for each system (`legacy` and `new`), run against `legacy` with `--reporter-json` into `evidence/baseline-bruno.json`, and the database columns each case writes into `evidence/baseline-db.md`. Test data only.
4. **lead** `job.py grill-done`. Write `spec.md`: the API and data contracts taken from the baseline, acceptance criteria "matches the baseline for case X", and every known difference as a decision request. Add tasks.
5. **Gate G1** The user approves the spec and every accepted difference. `job.py approve`.

## The run

Follow `_run.md`, with these changes:
- backend never edits the old implementation, the baseline, or the Bruno collection.
- qa runs the same collection against `new`, compares every response and column with the baseline, and reports each difference. A difference the user has not accepted is a FAIL, even when the new behavior looks better.
- The test report's parity section lists matches, accepted differences with their decision ids, and anything unreachable.
