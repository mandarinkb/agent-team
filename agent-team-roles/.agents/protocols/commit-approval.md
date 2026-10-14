# Stage, verify, review, and commit

The user approves every commit, and the approval must cover exactly what qa tested and the reviewer reviewed. Code enforces most of this. These steps make the approval informed.

## The revision every report names

Implementers never commit, so there is no commit SHA to test. Instead, the git teammate stages the task's files and runs `git write-tree`. The tree id it prints identifies the staged content exactly. qa tests that content, the reviewer reviews that content, and both reports name that tree id as their **Revision**. Any later change to a staged file produces a new tree id, and the reports must be redone for it.

## What enforces it

- `.claude/settings.json` has ask rules for `git commit`, `git push`, and `gh pr create`. An ask rule prompts the user in every permission mode, including auto mode and bypass mode. A teammate's prompt appears in the lead's session for the user.
- The `guard_git.py` PreToolUse hook catches commit and push commands written in forms the ask rule misses, such as `git -C . commit`, and denies force-push, `reset --hard`, `clean -f`, `branch -D`, and `gh pr merge`.
- For `git commit`, the same hook reads the task id from the commit message (`Task: <task-id>`). It **denies** the commit while the test report is missing or unfinished, or while a review report exists with unfinished reviewer or lead sections. Otherwise it **asks** the user and puts in the prompt whether the staged tree matches the Revision in both reports.
- The `gate_reports.py` TaskCompleted hook stops a `verify` or `review` task from completing until its report exists, has a valid verdict, and names the revision.

## Steps

1. **backend/frontend** Finish the change in its worktree and message git: "ready to stage", with the worktree path and the files. qa does the same for test files it wrote for this task.
2. **git** Stage only the files in the brief's scope (`git add <paths>`), check `git status --short` for anything outside the scope, run `git write-tree`, and send the tree id to qa, the reviewer, and the lead.
3. **qa** Verify with `team-verify` at that tree id. First confirm `git write-tree` in the worktree prints the same id and that `git diff --stat` shows no unstaged change in the scope. Write the test report and complete the `verify` task.
4. **reviewer** Review `git diff --cached` in the worktree with `team-review` at the same tree id. Write the review report and complete the `review` task.
5. **lead** Triage the review report with `team-review` (section "As the lead"). Findings marked "fix before commit" go back to the implementer. After the fix, repeat from step 2: git restages and sends the new tree id, qa reverifies, and the reviewer reviews the change since the last tree id. Both reports then name the new tree id.
6. **git** Draft one commit for the task in the form `type(scope): subject`, with a final line `Task: <task-id>`. One commit per task keeps the staged tree equal to the reviewed tree. If the user asked for several commits, the hook will warn on each partial commit, and the user decides.
7. **lead** Send the user a commit request in Thai:
   - the test report path, its verdict, and its Revision,
   - the review report path, its verdict, its Revision, and the lead's triage (fix before commit, consider, noted, dismissed with reasons),
   - the staged file list from `git diff --cached --stat`,
   - the commit message,
   - every open gap and accepted difference from `decisions.md`.
8. **git** Run `git commit`. The hook checks the reports, and the permission prompt shows the user whether the staged tree matches them. The user approves or rejects at the prompt.
9. On rejection, git changes nothing until the lead asks the user what to change and records the answer in `decisions.md`.
10. **git** Reports the new commit SHA to the lead. The lead adds it to the commit table in the test report and to `log.tsv`.

## When review may be skipped

Review is required in the feature, migration, and retire workflows. In the bug-fix workflow it is required when the change touches more than one file or a high-risk area (auth, money, personal data, permissions, data migrations). Otherwise the lead may skip it with `skip: <reason>` in the task list and a row in `log.tsv`. The commit request then says "no review" in plain words.

## Never

- Never commit with `--no-verify`, never amend a commit the user already approved without a new approval, and never batch unrelated tasks into one commit.
- Never change a staged file after the reports are written without restaging and redoing both reports.
- Never push. Pushing and opening a pull request are separate approvals (D7).
