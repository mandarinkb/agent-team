---
name: team-investigate
description: Map how a subsystem works, why it is shaped that way, and what a change could break, before anyone changes it. Use for "how does X work", tracing a code path, finding callers, or the investigate step of a team workflow.
when_to_use: Used mostly by analyst, also by implementers before touching shared code. Triggers: how does this work, where is this called, what calls this, why is it written this way, what could this change break.
---

# Team investigate

Adapted from pstack's `how`, `why`, and `blast-radius` skills. Read the code. Do not guess from names.

## How it works

1. **Find the entry point.** What triggers the behavior: a route, a job, a user action. Record the `file:line`.
2. **Trace the flow.** Follow the call chain from the entry point. Note what data passes between steps and how it changes shape.
3. **Map the key types and boundaries.** Which types carry the data, where external input is parsed, and where the code talks to databases, queues, or other services.
4. **Find the non-obvious.** Defaults, type coercion, caching, retries, feature flags, and code that looks defensive. Defensive code often exists because of a past incident.

## Why it is this way

When the reason for a shape matters to the change, read the history for the lines you will touch:

```bash
git log --follow --oneline -20 -- <file>
git blame -L <start>,<end> <file>
git log -1 --format=%B <commit>
gh pr view <number> --json title,body,comments   # when the commit names a PR
```

Separate what the record says from what you infer. "The PR says X" is measured. "It looks like X" is inferred. "We searched A and B and found nothing" is a valid result.

## What could break

Listing callers with grep is the start, not the job. Find the breakage grep will not show:

- Callers in other services, clients, cron jobs, and scripts that read the same API or table.
- Wire formats: JSON field names and types, database columns, queue messages.
- Timing: initialization order, caches, and teardown.
- The one fact the change is safe because of. State it, and prove it by running code when you can.

## Output

Write the findings to the task directory as `investigation.md`:

- **Overview.** What the subsystem does, in two or three sentences.
- **Flow.** Entry point to output, step by step, with `file:line`.
- **Key types and boundaries.**
- **Callers and blast radius.** Each caller with evidence, and the open risks.
- **Non-obvious behavior.**
- **Open questions.** What you could not trace. Do not fill gaps with guesses.
