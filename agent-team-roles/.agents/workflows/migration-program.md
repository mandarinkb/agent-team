# Workflow: migration program (many units)

Adapted from pstack's figure-it-out, Multi-phase plan, and Orchestrate. The program plans and tracks many units. Each unit runs `.agents/workflows/migration.md`. Design rules: `team-migration`.

Skills named in a step are the usual choice. Pick another installed skill when it fits the work better, except the four required skills in `.agents/AGENTS.md` (`team-decision`, `team-verify`, `team-parity`, `team-review`).

## When

Migrating more than one endpoint, job, or module, such as a whole PHP API to Go. For a single unit, use `migration.md` directly.

## Team

lead, analyst, qa. backend, reviewer, and git join per unit.

## Steps

Copy these into the task list. A step you skip stays in the list with `skip: <reason>`.

1. **lead** Run `new_task.py program "<what is migrating>"`. It creates `migration-plan.md` and `inventory.tsv` in the program directory.
2. **analyst** Inventory every unit with `team-investigate`: method, path, handler location, callers you can prove, writes versus reads, traffic if logs show it, and the shared primitives each unit uses. One row per unit in `inventory.tsv`.
3. **analyst** List the shared primitives (auth, error format, pagination, database access, serialization) as their own units. Every endpoint row names the primitives it depends on in `depends_on`.
4. **analyst** Order the units with `team-migration` section 4: shared primitives first, then a low-risk read-only pilot, then the riskiest unknowns. Write the order and the reason for each early position in `migration-plan.md`.
5. **analyst** Fill the rest of `migration-plan.md`: the countable done condition, the target architecture for the new side, where the compatibility layer lives, data migrations (each one a D6 decision), the risks, and the program-wide rulings you need from the user.
6. **qa** Confirm the harness works end to end on one case against the old system before the plan is approved. Report the command and the output.
7. **GATE G1 (D8, plus D6 for each data migration)** **lead** Present the plan with `team-decision`: the order, the pilot, the done condition, and each program-wide ruling. Record each ruling in `migration-plan.md` with the user's original words and its scope.
8. **lead** Run each unit through `.agents/workflows/migration.md` in the planned order, with the program task id in each unit's brief. Set the unit's `task_id` and `state` in `inventory.tsv` as it moves. Start the next unit only when its `depends_on` units are committed.
9. **lead** After the pilot is committed, review the plan with the team: what the pilot taught, whether unit sizes and the case list hold, whether a lever would pay off (`team-migration` section 7). Changes to the order or scope are a decision (D4).
10. **lead** At every checkpoint the user asks for, and before each gate, run `python3 .agents/scripts/migration_status.py <program-task-id>` and send the user the board it writes. Never report status from memory.
11. **lead** When the user moves traffic for a unit (D7), set its state to `traffic`. Retiring the old code is a separate task: `.agents/workflows/migration-retire.md`.
12. **GATE G2 (D8)** **lead** When `migration_status.py` shows the done condition met with zero inconsistencies, present the final board and the open items to the user to close the program.

## Gates

| Gate | Code | User sees | Blocks |
|---|---|---|---|
| G1 | D8 + D6 | Inventory, order, pilot, done condition, target shape, rulings | Every unit |
| Per unit | as in `migration.md` | Each unit's plan and commit | That unit |
| G2 | D8 | Final board from `migration_status.py` | Closing the program |

## Done when

- `migration_status.py` reports the done condition met and zero inconsistencies.
- Every ruling the program relied on is recorded in `migration-plan.md` with the user's own words.
- The user closed the program at G2.
