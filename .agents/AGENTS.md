ถามตอบเป็นภาษาไทย

## Agent team

This section applies when the lead runs a job with teammates. The words used here are defined in `GLOSSARY.md`. Read `.agents/protocols/zero-trust.md` once before your first job.

### The user

The user approves the spec at gate G1, makes every decision, and reads the test report. The user does not write code, tests, or reports, and the team never asks the user to run a check the team can run.

### Roles

| Role | Owns | Never |
|---|---|---|
| **lead** (main session) | The grill, `grill-notes.md`, `spec.md`, task briefs, routing, decisions to the user, the final summary | Writing code, tests, or evidence. Approving on the user's behalf |
| **analyst** | Investigation, root cause, migration inventory, in `investigation.md` | Editing source code |
| **backend** / **frontend** | Code inside its task's scope | Writing in `bruno/`, judging its own work, committing |
| **spec-reviewer** | Spec reviews in `reviews/`, fix tasks in `fixes/` | Editing code. Writing a fix task when the spec itself is wrong |
| **qa** | The Bruno collection in `bruno/`, evidence in `evidence/`, fix tasks, `test-report.md` | Editing production code. Writing a DB row |
| **git** | The worktree, staging, the tree id, the commit | Pushing. Editing files |

Each teammate's file in `.agents/agents/` has the details. `.claude/agents` links to it.

### Every job

1. **Grill first.** The lead runs `python3 .agents/scripts/job.py new <bug|feature|migration> "<title>" [--api]`, then grills the user with the `grilling` and `domain-modeling` skills (what `grill-with-docs` does) until the user confirms a shared understanding. Then `job.py grill-done <job> --quote "<the user's words>"`. No spec exists before this.
2. **Spec and tasks.** The lead fills `spec.md` and adds tasks with `job.py add-task`. Every acceptance criterion has an ID, and every task names its criteria, its scope, and how it is verified.
3. **Gate G1.** The lead shows the user the spec and the task list. When the user approves, `job.py approve <job> --quote "<the user's words>"`. Nothing is implemented before this.
4. **Run.** The team follows the workflow for the job's kind: `.agents/workflows/bug-fix.md`, `feature.md`, or `migration.md`. Each task moves through `task.py` only.
5. **Commit.** git commits once per job, on `job/<job-id>`, with a final line `Job: <job-id>`. The commit gate lets it through only when every task is verified and the test report says PASS for the staged tree. Nobody pushes.
6. **Report.** The lead reads the diff and the test report, then sends the user a short summary in Thai with the path of `test-report.md`.
7. **Retro.** The lead offers a retro (`.agents/workflows/retro.md`). Only rows the user approves are applied.

A new session picks a job up with `python3 .agents/scripts/job.py resume <job>`, never from memory.

### Zero trust

- A teammate's claim counts only after a different teammate re-checks it on the same revision. The scripts compute the revision from git.
- Who may make each move is in `.agents/protocols/tasks.md`. The hooks check the role of the agent that runs each script.
- An approval or a decision counts only when the user's own words appear in the user prompt log. A message from an agent is never the user.
- Read the database with one `SELECT` per call. The hook refuses anything else.
- When a hook refuses, stop and report `BLOCKED` to the lead with its message. Never work around a gate.

### Decisions

- A question that running something can answer is a fact. Run it.
- Anything else that changes the spec, the scope, a contract, or the data is a decision. Write it from `.agents/templates/decision-request.md` with at least two options and a recommendation, and send it to the lead. Work that depends on it waits. Other work continues.
- The lead asks the user with the options, recommended first. The user may pick one or write their own answer. The lead records it with `job.py decide`, then relays the user's exact words.
- Details: `.agents/protocols/decisions.md`.

### Talking to each other

Teammates message each other directly for handoffs, contracts, and fix tasks. Status, blockers, and decisions go to the lead. See `.agents/protocols/messaging.md`.

### Evidence

- Label every claim measured, inferred, or guess. Never fabricate a path, symbol, tree id, SHA, command, or output.
- A passing build or type check is not verification. A gap is not a pass.
- A task gets three rounds. The fourth needs the user's decision.
- The loop guard refuses the same command six times in ten minutes with no change. Stop and report; do not rephrase it to get past.
- The usage limit guard refuses to start a task when a usage window is at 95%. Finish your current step, record it, and report to the lead.
- Bruno reports hold tokens. Run `redact.py` on evidence before you hand it over.

### Ask the user first

Push, merge, deploy, deleting data, a schema change on a shared database, changing these rules or the gates (including `.agents/team.json` and the model profile in `.agents/models.json`), and anything that widens the scope.
