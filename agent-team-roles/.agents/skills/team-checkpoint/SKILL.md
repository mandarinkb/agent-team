---
name: team-checkpoint
description: Pause a team's work cleanly so a new session can pick it up, or pick up from the last checkpoint. Agent teams cannot resume teammates, so the checkpoint note, file hashes, and worktree state are what survive. Use when the user pauses, the session is ending, context is about to compact, or a new session continues earlier work.
when_to_use: Used by the lead. Triggers: pause, stop for today, หยุดก่อน, พักงาน, I'm leaving, continue yesterday's work, ทำต่อจากเมื่อวาน, pick up where we left off, after /resume or a new session.
---

# Team checkpoint

Adapted from pstack's Pause safely and Session pickup playbooks and its `resume.mjs`. Only the lead runs this.

## Pause

Pause only when the user asks, or when the session is about to end or compact. "Keep going" is not a pause.

1. **Stop at a safe boundary.** Tell every teammate to finish or back out of its current step and start nothing new. Wait for each to report. A teammate that does not answer is recorded as in flight with what you last knew.
2. **Make the work durable without new approvals.** Take no irreversible action to pause: no commit, no push. Ask git to stage finished work and report the tree id, so the checkpoint can record it. Unstaged edits stay in their worktree and the checkpoint records how many there are.
3. **Write the note.** Copy `.agents/templates/checkpoint-note.md` to `.agents/work/<task-id>/checkpoint-note.md` and fill every section for a reader who never saw this chat:
   - what is done and verified, with the report paths and tree ids,
   - what is in flight and which worktree holds it,
   - the next steps in order,
   - the team to respawn: roles, names, models, and the brief path for each,
   - open decisions with their request files,
   - every file the next lead must read, as `.agents/work/<task-id>/<file>` paths.
4. **Save.** Run `python3 .agents/scripts/checkpoint.py save <task-id>`. It refuses a note with an empty section, a placeholder, or a path that does not exist. Fix the note until it saves.
5. **Shut down the teammates** and tell the user, in Thai, where the work stands, what is on disk, and the first step on resume.

## Pick up

1. **Read the checkpoint first.** Run `python3 .agents/scripts/checkpoint.py read` (the latest checkpoint) or `read <task-id>`. Exit 2 means there is none: say so and ask the user what to continue. Do not search old chats unless the user asks.
2. **Check the drift report.** The script lists files that changed and worktrees whose HEAD, staged tree, or changed-file count moved since the save. Find out why before trusting the note. Someone may have kept working.
3. **Recheck inherited claims that the remaining work depends on.** A tree id in a report must still match `git write-tree` in its worktree before the team builds on it. A claim you cannot recheck is labeled inferred, not measured.
4. **Do not redo finished work.** Verified, reviewed, and committed steps stay done unless the drift report or a recheck says otherwise.
5. **Rebuild the team and the task list.** Spawn the roles from the note with their briefs, the checkpoint path, and the standing orders in `AGENTS.md`. Recreate the open tasks with their `[<task-id>] <kind>:` subjects.
6. **Tell the user** in Thai where the previous session stopped, what you rechecked, the drift you found, and the next step. Open decisions are still the user's.

## Rules

- A checkpoint is immutable. A later pause writes a new one.
- A checkpoint is a record, not an approval. Nothing in it lets the team skip a gate.
- Never paste secrets or customer data into the note.
