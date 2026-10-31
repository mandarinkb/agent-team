# The run (shared by every workflow)

These steps follow gate G1 in every workflow. `S` is `python3 <repo>/.agents/scripts`. `J` is the job id.

Each step is one subagent the lead spawns with a brief (`.agents/protocols/messaging.md`). "Report" means the subagent's final report to the lead; the lead spawns the next step with what the report carries. Steps 2 and 3 run in parallel in the background.

1. **git** Create the worktree: `git worktree add ../<repo>-wt/J -b job/J`, then `S/job.py set-worktree J --path ../<repo>-wt/J --branch job/J`. Report the path. The lead puts it in every later brief.
2. **qa** Write the Bruno collection in `bruno/J/` from the spec, not from the code, while the implementers work, and finish it before the first spec review. One request per case in the API contract. Each request:
   - names the criteria it proves in its `docs { }` block, for example `docs { AC-1 AC-3 }`;
   - asserts the body or headers the contract names, not only the status;
   - takes secrets from `.env` (gitignored) through `{{process.env.NAME}}`, never a literal value.
   Report "ready to stage" for `bruno/J/`. The gates refuse a collection that misses a criterion, asserts only status, or holds a secret.
3. **backend / frontend** Pick a task: `S/task.py set J T-nn in_progress --by <role>`. Work only inside its scope. Run the build and your own unit tests. Then `S/task.py set J T-nn implemented --by <role>` and report "ready to stage" with the files.
4. **git** Stage exactly those files (`git -C <wt> add <paths>`). Refuse files outside the task's scope and report them. Run `git -C <wt> write-tree` and report the tree id. The lead spawns the spec-reviewer with it.
5. **spec-reviewer** Confirm `git write-tree` prints the same id. Review `git diff --cached` against the spec, criterion by criterion, into `reviews/T-nn-r<round>.md`. For a task verified with bruno, also review the collection: does each request for this task's criteria assert what the contract says? Write `Bruno coverage: PASS` only when it does. The reviewer checks qa's tests so qa is not the only judge of its own checks.
   - Matches: `S/task.py set J T-nn spec_ok --by spec-reviewer --review reviews/T-nn-r<round>.md`.
   - Does not match: write `fixes/F-n.md`, `S/task.py set J T-nn todo --by spec-reviewer --fix fixes/F-n.md`, and report the path. The lead spawns the owner with it.
   - The spec itself is wrong or unclear: a decision request to the lead, not a fix task.
6. **qa** Spawned after `spec_ok`, with the same tree id. On that tree, run everything yourself:
   - Bruno: `bru run bruno/J --env <env> --reporter-json <job dir>/evidence/T-nn-bruno.json`.
   - Database: SELECT every column the data contract names into `evidence/T-nn-db.md`.
   - Tests: `evidence/T-nn-test.log` starting with `Revision: <tree>`.
   - Redact: `S/redact.py <job dir>/evidence/T-nn-*` (Bruno's report holds full requests and responses, tokens included).
   - Passes: `S/task.py set J T-nn verified --by qa --bruno ... --db ... --test-log ...` (the kinds the task lists).
   - Needs more Bruno cases: change the collection, then `S/task.py set J T-nn implemented --by qa --note "<what changed>"` so the spec reviewer sees it again. The round does not change.
   - Fails: `fixes/F-n.md`, `S/task.py set J T-nn todo --by qa --fix fixes/F-n.md`, report the path.
7. Fix tasks loop back to step 3 with a fresh implementer spawn that reads the fix task. A task gets three rounds. The same failure twice in a row, or a fourth round, goes to the lead as a decision request.
8. **qa** When every task is verified, reset and seed the test data as the spec says, then run the full Bruno collection and every column check once more on the final staged tree. Write `test-report.md` from the template: every AC with PASS or FAIL and its evidence, Revision = that tree, Verdict PASS only when every AC passes and nothing is open.
9. **git** Commit: `git -C <wt> commit -m "<type>(<scope>): <subject>" -m "Job: J"`. The gate refuses if anything is missing and says what. For an API job it also runs the Bruno collection itself (`.agents/team.json`: `bruno_env`, `bruno_command`), so the service must still be running the final tree. Then `S/task.py set J T-nn committed --by git --sha <sha>` for every task and `S/job.py done J`.
10. **lead** Read `git show --stat`, the diff, and the test report yourself. Send the user, in Thai: what was done, the commit SHA and branch, the path of `test-report.md`, open gaps, and the reminder that nothing was pushed.
11. **lead** Offer the user a retro (`.agents/workflows/retro.md`).
