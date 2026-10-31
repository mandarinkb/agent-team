# Workflow: feature

**Team:** lead, analyst, backend and/or frontend, spec-reviewer, qa, git.

## Before the spec

1. **lead** `job.py new feature "<title>" [--api]`. Grill the user: who uses it, what they can do afterwards, what is out of scope, the API and data shape, error cases, how it should be verified.
2. **analyst** Map the code the feature touches, its callers, and what could break. Write `investigation.md`. When two designs both meet the need, write them as a decision request. The lead spawns backend or frontend with the options to estimate each one's cost, and adds the estimates to the request.
3. **lead** `job.py grill-done`. Write `spec.md` with acceptance criteria, the API contract, and the data contract. Split tasks so no two tasks share a path. Add tasks.
4. **Gate G1** The user approves. `job.py approve`.

## The run

Follow `_run.md`.
