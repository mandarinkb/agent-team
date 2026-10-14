---
name: team-parity
description: Record the old implementation's responses as a baseline and prove the new implementation matches, using .agents/scripts/parity.py. Use for every migration or port task, such as PHP to Go.
when_to_use: Required for qa on every migration baseline and parity check. Triggers: record baseline, compare old and new endpoint, PHP to Go, parity, port matches.
---

# Team parity

Adapted from pstack's Refactoring playbook step "pin the behavior contract first" and the PHP-to-Go starter kit.

## Record the baseline (before any new code)

1. Write `.agents/work/<task-id>/parity/cases.jsonl`, one request per line with a unique `id`:
   ```json
   {"id": "list-empty", "method": "GET", "path": "/api/orders?user_id=1002", "headers": {"Authorization": "Bearer ${PARITY_TOKEN}"}}
   ```
   Cover the happy path, empty results, not-found, validation errors, auth failures, and each item on the PHP-to-Go checklist in the brief.
2. Use synthetic accounts only. Put credentials in `${ENV_VAR}` references, never in the file.
3. Record:
   ```bash
   python3 .agents/scripts/parity.py record --base-url <old-url> \
     --cases .agents/work/<task-id>/parity/cases.jsonl \
     --out .agents/work/<task-id>/parity/baseline.jsonl
   ```
4. Never edit `baseline.jsonl` after recording. To change it, re-record from the old system and log why.

## Check the new implementation

```bash
python3 .agents/scripts/parity.py check --base-url <new-url> \
  --baseline .agents/work/<task-id>/parity/baseline.jsonl \
  --config .agents/work/<task-id>/parity/parity.json --json
```

| Exit | Meaning |
|---|---|
| 0 | Every case matches. The only pass |
| 1 | At least one DIFF. Send each to backend with the path and both values |
| 2 | Input error, such as a duplicate id or a missing environment variable |
| 3 | No DIFF, but a case was unreachable. `INCONCLUSIVE`, not a pass |

The check compares status, the headers listed in `compare_headers`, and the JSON body exactly, including types (`"1"` and `1` differ) and array order. Object key order does not matter.

## Ignored paths

`parity.json` may list `ignore_paths` such as `$.meta.request_id` or `$.data[*].updated_at`. Each one is a decision (D3). Propose it with a reason, and add it only after the user approves it in `decisions.md`.

## What parity cannot see

Raw JSON text (`"é"` versus `"é"`), side effects such as database writes and messages, and non-deterministic data. Check those separately with `team-verify`.
