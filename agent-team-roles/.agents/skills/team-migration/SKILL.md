---
name: team-migration
description: The design rules for migrating or porting a system, such as PHP to Go, gathered from pstack's Refactoring, Visual parity, figure-it-out, Orchestrate, and its migration principles. Use when planning a migration program, porting a unit, migrating data, or retiring old code.
when_to_use: Used by the lead and analyst to plan a program or a unit, by backend while porting, and by qa when judging parity. Triggers: migrate, port, convert PHP to Go, rewrite, move endpoints, data migration, backfill, retire the old code, strangler.
---

# Team migration

Adapted from pstack. Each rule names its source so you can read the original reasoning in the pstack study notes. Where pstack's default does not fit a live API migration, the team rule says so.

## 1. Pick the scale first

| Scale | Workflow | Source |
|---|---|---|
| One endpoint, job, or module | `.agents/workflows/migration.md` | Refactoring playbook |
| Many units, or work the user reviews later | `.agents/workflows/migration-program.md`, which runs `migration.md` once per unit | figure-it-out, Multi-phase plan |
| Removing the old implementation after traffic moved | `.agents/workflows/migration-retire.md` | migrate-callers-then-delete-legacy-apis |

## 2. Pin before you port (Refactoring step 1, figure-it-out phase B)

- Record the old behavior before any new code exists. The baseline is the spec.
- Type checks, lint, and "it compiles" are not a pin.
- Build the verification harness before the work, so every check reads as "old value versus new value".

## 3. Anti-shortcut rules (Visual parity)

- **Never edit the baseline.** If the baseline looks wrong, stop and raise a decision (D3). Do not "fix" it.
- **Never change the harness to make a diff pass.** A change to `parity.py`, its config, or the case list during a port is a decision (D3), with the reason.
- **Never restructure the new code just to make a diff disappear** when the diff points at a real behavior difference. Find the behavior and match it, or raise it.
- A nonzero diff is a fail. Investigate the exact path and values.

## 4. Order the work (figure-it-out phase B, Visual parity, foundational-thinking)

- **Shared primitives first, as a blocking phase.** Auth middleware, the error response format, pagination, database access, and serialization helpers are ported and verified before the endpoints that use them.
- **Riskiest unknown first, after the pilot.** The pilot is a low-risk, read-only unit that proves the whole path. Then take the unit that would most change the plan if it failed: writes, money, auth, high traffic.
- **One unit, one owner.** Code-coupled work goes to one implementer. Parallel units only when their files and packages are disjoint, each on its own worktree (Feature playbook, separate-before-serializing-shared-state).

## 5. Converge on the target, keep the quirks at the edge (outcome-oriented-execution, boundary-discipline, model-the-domain)

- Build the Go side in its target shape: typed domain models, pure business logic, validation at the boundary.
- Callers still need the PHP behavior: strings for IDs, `[]` for empty objects, specific error shapes. Put that compatibility in one response-mapping layer at the HTTP boundary, not scattered through the domain code.
- Mark each compatibility rule in that layer with the parity case that requires it, so it can be removed deliberately later.
- Do not build throwaway shims inside the domain to keep intermediate states smooth. Planned, scoped breakage behind a disabled route is acceptable.

## 6. Small verified units (sequence-verifiable-units, prove-it-works)

- Each unit is a before and after bracket: known-good state, one change, the parity check, then the next unit. Never batch checks to the end.
- Rebase onto a clean trunk before each unit so the check measures against the real baseline.
- Order commits so the sequence proves itself: cases and baseline, then the handler, then the disabled route wiring.

## 7. Build the lever once the work repeats (build-the-lever)

- Port the pilot and the next unit by hand to learn the recipe.
- When units start to look alike, build the tool: a generator for case files from the route list, a struct generator from recorded responses or an OpenAPI file, a codemod for repeated handler shapes.
- Prove the tool by running it on a unit you already did by hand and diffing the output. Commit it with the work.
- Building a lever is a decision (D4) when it widens the scope of the current task.

## 8. Data migrations and backfills (make-operations-idempotent)

Every data migration is a decision (D6). Its design must answer, in writing:

1. What happens if it runs twice in a row?
2. What happens if it crashes at any row and runs again?
3. Does re-running converge to the same end state?
4. How is it rolled back, and what does the dry run print?

Prove it on a copy: row counts and checksums before and after, a second run that changes nothing, and a crash-then-resume run. Never run it against shared data without the user's approval for that exact run.

## 9. Retire the old code in one wave (migrate-callers-then-delete-legacy-apis)

- Only after the user moved traffic and confirmed the new side served it cleanly (D7).
- Inventory every caller and reference: routes, clients, cron jobs, config, tests, docs, feature flags.
- Remove the old endpoint, its route, its tests, and its configuration together in one change. No lingering dual paths.
- Remove each compatibility rule in the response-mapping layer only when no remaining caller needs it, as its own decision.

## 10. Understand odd behavior before copying it (why, epistemics)

- When the old code does something that looks like a bug, read its history with `team-investigate` before you copy it. Defensive code often exists because of an incident.
- Keeping a bug, fixing it, or making it configurable is a decision (D2 or D3). Never decide it silently in either direction.
- Record program-wide rulings in the migration plan with the user's original words and their scope. "Keep string IDs during this migration" is not "keep string IDs forever".

## 11. Know when it is done (Orchestrate, figure-it-out phase A)

- The done condition is countable: "all N units MATCH at their committed SHA, with every ignored path approved".
- Status comes from the records, not from memory. Run `python3 .agents/scripts/migration_status.py <program-task-id>` to compute the board.
- Inconclusive is not done. A unit with exit 3 or a missing report counts as not verified.
