# Migration plan: {{TITLE}}

- **Program task:** {{TASK_ID}}
- **Workflow:** `.agents/workflows/migration-program.md`
- **Created:** {{DATE}}

The analyst writes this plan. The user approves it at G1. Design rules: `team-migration`.

## Done condition

<fill: countable, for example "all 24 units MATCH at their committed SHA, every ignored path approved, every data migration proven rerunnable">

## Scope

- **Units:** <fill: count by kind, for example 3 shared primitives, 21 endpoints>
- **Out of scope:** <fill: what this program will not migrate>

## Target shape of the new side

<fill: package layout, domain types, where validation happens, how handlers stay thin>

## Compatibility layer

<fill: where the response-mapping layer lives, and the rule that every compatibility behavior names the parity case that requires it>

## Order and why

<fill: shared primitives first, then the pilot, then the riskiest unknowns. One line per early unit explaining its position. The full order is the `order` column in inventory.tsv>

## Data migrations

<fill: each one with its answers to rerun, crash-resume, convergence, rollback, and dry run. Each one is a D6 decision. Or "none">

## Risks

<fill: one line each, with the unit it lands in and what qa watches>

## Program-wide rulings

<fill: rulings the user made that apply to every unit, each with the user's original words, the date, and its scope. The lead adds these after G1>

## Lever

<fill: after the pilot, whether a generator or codemod would pay off, and the decision>
