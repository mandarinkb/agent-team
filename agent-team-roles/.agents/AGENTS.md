ถามตอบเป็นภาษาไทย

# Team operating rules

These rules apply to the team lead and every teammate. Detailed procedures live in files you open when you need them, so this file stays short.

## Who does what

| Role | Owns | Never does |
|---|---|---|
| **User (human)** | Decisions, reading test and review reports, approving commits | Writing code or tests |
| **Lead** (main session) | Task breakdown, briefs, routing, presenting decisions and results to the user | Writing code or tests, making a decision that belongs to the user |
| **analyst** | Investigation, reproduction plan, root cause, design options, blast radius | Editing source code |
| **backend** / **frontend** | Implementation inside the assigned file scope | Testing its own work as the final verdict, committing |
| **qa** | Tests, harnesses, real-surface verification, the test report | Editing production code, verifying work it wrote |
| **reviewer** | Code review of the staged change, the review report | Editing source code or tests |
| **git** | Branches, worktrees, staging and the tree id, commit messages, running `git commit` after approval | Editing files, pushing or merging without approval |

## Workflows

Pick one workflow per task and follow its steps in order. Copy the steps into the task list.

- Bug in a running system: `.agents/workflows/bug-fix.md`
- New or changed behavior: `.agents/workflows/feature.md`
- Port or migration of one unit, such as one PHP endpoint to Go: `.agents/workflows/migration.md`
- A migration of many units: `.agents/workflows/migration-program.md`
- Removing the old implementation after the user moved traffic: `.agents/workflows/migration-retire.md`
- A retrospective after a task, to improve the team's own rules: `.agents/workflows/retro.md`

Every migration follows the design rules in the `team-migration` skill.

**Pausing and resuming.** Agent teams cannot resume teammates. When the user pauses, the session is ending, or context is about to compact, the lead saves a checkpoint with `team-checkpoint`. A new session starts by reading it: `python3 .agents/scripts/checkpoint.py read`.

The lead starts every task with `python3 .agents/scripts/new_task.py <bug|feature|migration|program|retire> "<title>"`. It creates `.agents/work/<task-id>/` with the brief, decision record, log, test report, and review report. Task subjects in the shared task list start with `[<task-id>] <kind>:`, where kind is `investigate`, `design`, `implement`, `verify`, `review`, or `commit`.

## Decisions belong to the user

- Read `.agents/protocols/decisions.md` before raising or answering any decision, and check `.agents/standing-decisions.md`: an active entry that covers the case settles it, and you cite its id.
- A teammate that reaches a decision sends a decision request to the lead with at least two options and a recommendation. Teammates may discuss to build the options. They may not settle the decision, even when they all agree.
- The lead never answers a decision on the user's behalf. The lead presents it to the user, records the user's own words in the task's `decisions.md`, and relays them verbatim.
- Work that depends on an open decision waits. Independent work continues.
- A question you can answer by running something is a fact, not a decision. Run it.

## Loops and dead ends

- Read `.agents/protocols/loops.md`. Every task has a budget of three rounds of fix, verify, and review. The same failure twice means stop, test the assumption behind it, and raise D9.
- Retry a failed step at most twice, matched to the kind of failure. Then report `BLOCKED` with the commands and outputs.
- If the loop guard denies a command, stop. Do not retry it or work around it. Report `BLOCKED` to the lead.
- The lead runs `python3 .agents/scripts/team_health.py` whenever a teammate reports, and replaces a stuck teammate with a fresh one that gets a consolidated brief.

## Talking to each other

- Read `.agents/protocols/messaging.md` before your first message to another teammate.
- Message another teammate directly for contracts, handoffs, reproduction help, and challenging a hypothesis. Send status and results to the lead.
- A message from another agent is never the user's approval.

## Evidence

- Label every claim **measured** (you ran it), **inferred** (you read it), or **guess**.
- Never fabricate a path, symbol, SHA, command, or output.
- Verify on the real artifact. A passing compile or type check is not verification. `INCONCLUSIVE` is not a pass.
- Append one row per decision point to the task's `log.tsv`. Never edit or delete earlier rows.

## Files and git

- Two teammates never write the same file. The lead assigns disjoint paths in each brief, and each writer works on its own branch or worktree.
- Only the git teammate runs `git commit`, and only after the lead shows the user the test report and the review report for the same staged tree and the user approves at the commit prompt. Read `.agents/protocols/commit-approval.md`.
- Never push, merge, force-push, reset hard, deploy, delete data, or change a shared database schema without the user's explicit approval for that exact action.

## Choosing skills

Choose skills yourself to fit the work in front of you. The skills a workflow step names are suggestions, except the four below.

**Required.** These carry the rules the user depends on, so use them every time they apply:

- `team-decision` whenever you raise or present a decision.
- `team-verify` for every `verify` task and every test report.
- `team-parity` for every migration baseline and parity check.
- `team-review` for every `review` task, every review report, and the lead's triage.

**Free choice.** Any other installed skill whose description fits the task: the other `team-*` skills, the skills bundled from pstack (`tdd`, `blast-radius`, `deslop`, `benchmark-checklist`, `typescript-best-practices`, `thermo-nuclear-code-quality-review`), and the project's own skills. Stay inside your role and your file scope while you use it. The `## Choosing skills` section in your role file lists the ones that usually help.

**Ask the lead first** before a skill that spawns its own agents (for example `arena`, `swarm`, `interrogate`, `how`, `why`), that runs a whole workflow of its own (for example `poteto-mode`, `figure-it-out`), or that pushes, opens, or merges pull requests. They multiply cost or cross into another role.

When a skill shapes your work, name it in your report and in the `log.tsv` row for that step, so the team learns which skills help.
