# Endpoint brief: <METHOD> <path>

Copy this file to `parity/<endpoint>/brief.md` and fill every field. A field you cannot fill means the endpoint is not scoped yet. Hand the filled brief to the delegate as its whole context, because a delegate cannot ask you questions.

```
GOAL         Port <METHOD> <path> from <php file> to Go so the Go response matches the PHP baseline.
SCOPE        May write: <go package paths>, parity/<endpoint>/
             May not write: any PHP file, routing config that sends live traffic, other endpoints
             Worktree: <path or branch owned only by this delegate>
CONTEXT      PHP handler: <file:line>
             Callers proven by blast-radius: <list, or "open risk: ...">
             Shared Go code to reuse: <packages>
ACCEPTANCE   - parity.py check exits 0 against the Go endpoint
             - every ignore_paths entry has a reason below
             - go vet and the package tests pass
             - PHP endpoint untouched and still reachable
VERIFY       python3 scripts/parity.py check --base-url <go url> \
               --baseline parity/<endpoint>/baseline.jsonl --config parity/<endpoint>/parity.json --json
TIMEBOX      <rough cap>. On expiry, return partial findings and stop.
FORBIDDEN    No edits to baseline.jsonl. No new ignore_paths without a reason.
             No changes to PHP. No route flip. No force-push.
REPORT       PASS | ISSUES | BLOCKED, branch, head SHA, parity counts (MATCH/DIFF/UNREACHABLE),
             the commands you actually ran, deviations from this brief, follow-ups
```

## Ignored paths and why

| Path | Reason |
|---|---|
| `$.meta.request_id` | Generated per request on both sides |

## Accepted behavior changes

Behavior where Go deliberately differs from PHP. Empty until the operator accepts one.

| Case | PHP | Go | Accepted by |
|---|---|---|---|

## PHP-to-Go checklist

Write a case for each item that applies to this endpoint. These are the differences that most often break clients after a port.

- [ ] **Empty list.** PHP `[]` versus a Go nil slice, which encodes as `null`. Initialize slices, for example `items := []Item{}`.
- [ ] **Empty object.** PHP encodes an empty associative array as `[]`, not `{}`. Clients may depend on either.
- [ ] **Missing versus null.** Go `omitempty` drops a field that PHP sends as `null`, `0`, `""`, or `false`.
- [ ] **Numbers as strings.** PHP often returns database IDs and decimals as strings (`"1"`, `"10.50"`). Go structs with `int` or `float64` change the type.
- [ ] **Float formatting.** `10.50` versus `10.5`, and large integers that lose precision as `float64`.
- [ ] **Booleans.** PHP may return `1` and `0`, or `"1"` and `"0"`, where Go returns `true` and `false`.
- [ ] **Dates.** Format, timezone, and whether midnight values keep their time part.
- [ ] **Error shape and status.** Validation errors, not-found, and auth failures: status code and body shape.
- [ ] **Routing details.** Trailing slash, query parameter parsing (`a[]=1&a[]=2`), case sensitivity.
- [ ] **Headers.** `Content-Type` including charset, caching headers, CORS.
- [ ] **Encoding.** Unicode escaping (`é` versus `é`) and escaped slashes (`\/`). These are equal as JSON, but a client that compares strings will see a difference.
- [ ] **Ordering.** Array order from the database without an explicit `ORDER BY`.
