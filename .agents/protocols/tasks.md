# Task states and moves

Every move goes through `python3 .agents/scripts/task.py set <job> <task> <state> --by <your-role> ...`. Paths are relative to `.agents/work/<job>/`.

```
todo -> in_progress -> implemented -> spec_ok -> verified -> committed
  ^                         |            |          |
  +------- fix task --------+------------+----------+
```

| From | To | Who | Needs |
|---|---|---|---|
| todo | in_progress | the task's owner | G1 approved, a worktree. Round 4+ needs `--decision D-n` recorded by the lead |
| in_progress | implemented | owner | at least one changed file inside the task's scope |
| implemented | spec_ok | spec-reviewer | `--review reviews/T-nn-r<round>.md`: Verdict PASS, every AC of the task, Revision = staged tree. For a bruno task also `Bruno coverage: PASS` and a collection that passes the mechanical check below |
| implemented | todo | spec-reviewer | `--fix fixes/F-n.md` naming the task and the broken AC |
| spec_ok | verified | qa | nothing in the task's scope or in `bruno/<job>/` changed since the review; `--bruno`, `--db`, `--test-log` for each verify kind of the task; no evidence file holds a secret |
| spec_ok | implemented | qa | `--note` saying what changed in the Bruno collection. Back to spec review, same round |
| spec_ok or verified | todo | qa (spec-reviewer from verified) | `--fix fixes/F-n.md` |
| verified | committed | git | `--sha` of a commit on the job branch whose tree is the test report's revision |

A move back to `todo` starts the next round when the owner picks it up again.

## The Bruno collection check

Run at spec review, at verify, and at commit. It refuses when the job's collection is missing, a request has no `assert` or `tests` block, a request asserts only `res.status` or `res.responseTime`, a criterion is named by no request's text (put the ids in `docs { }`), or a request or environment file holds a literal secret.

## Writing inside the worktree

The `guard_task.py` hook refuses Write and Edit inside a job worktree unless:
- an implementer holds a task `in_progress` whose scope covers the path,
- qa writes inside `bruno/<job>/`.
Everyone else, the lead included, writes nothing there.

## Evidence formats

- **Bruno:** `bru run <folder> --env <env> --reporter-json ../.agents/work/<job>/evidence/<task>-bruno.json` from the collection root. Zero failed requests, assertions, or tests, and at least one request.
- **Database:** `evidence/<task>-db.md` from `.agents/templates/db-check.md`, with the Revision line and one PASS row per checked column.
- **Secrets:** run `python3 .agents/scripts/redact.py <files>` on every evidence file first. `task.py` and the commit gate refuse anything that still looks like a token, password, key, or JWT.
- **Tests:** `evidence/<task>-test.log` whose first line is `Revision: <tree id>`, followed by the full output of the run.
