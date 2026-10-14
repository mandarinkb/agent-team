# Workflow: retrospective

Adapted from pstack's reflect skill. Turn what one task taught the team into changes the user approves row by row: rule edits, skill tuning, standing decisions, and mechanisms. Method: `team-reflect`.

Skills named in a step are the usual choice. Pick another installed skill when it fits the work better, except the four required skills in `.agents/AGENTS.md` (`team-decision`, `team-verify`, `team-parity`, `team-review`).

## When

After a task is committed, after a migration pilot, after a bug that took several rounds, or whenever the user asks. Skip it for a task that went exactly as planned, and say so.

## Team

lead. In full mode, three reviewer subagents and one synthesizer subagent. git for the commit.

## Steps

Copy these into the task list. A step you skip stays in the list with `skip: <reason>`.

1. **lead** Choose the mode. Light is the default. For full mode, raise D10 with `team-decision`, stating the rough cost of four extra agents.
2. **lead** Copy `.agents/templates/retro.md` to `.agents/work/<task-id>/retro.md`.
3. **lead** Apply the three lenses from `team-reflect` to the task's records. In full mode, spawn one subagent per lens with its `references/` prompt and the task directory, then one synthesizer subagent with all three outputs.
4. **lead** Fill `retro.md` with the synthesizer's Accepted, Standing decision proposals, Backlog, and Rejected sections. Read each target file first and reject rows it already covers.
5. **GATE G1 (D11)** **lead** Present the Accepted rows and the standing decision proposals to the user with `team-decision`, one row at a time or as a multi-select. Record each answer in `retro.md` with the user's words.
6. **lead** Apply only the approved rows to `.agents/`, add each approved rule to `.agents/rules.json`, add approved standing decisions to `.agents/standing-decisions.md` with the user's words and scope, run `python3 .agents/scripts/sync_claude.py`, then `python3 .agents/scripts/check_team.py --installed`.
7. **git** Stage the changed team files and send the staged file list to the lead. Draft one commit with the final line `Retro: <task-id>`.
8. **GATE G2 (D8)** **lead** Send the commit request with `retro.md`, the approved rows, and the `check_team.py` output. git commits only through the approval prompt.

## Gates

| Gate | Code | User sees | Blocks |
|---|---|---|---|
| G1 | D11 | Each proposed change with its evidence, and each standing decision proposal | Step 6 |
| G2 | D8 | The approved rows, the check output, staged files, commit message | `git commit` |

## Done when

- Every approved row is applied, every rejected row stays unapplied, and `retro.md` records which is which with the user's words.
- `check_team.py --installed` passes.
- The user approved the commit at the prompt.
