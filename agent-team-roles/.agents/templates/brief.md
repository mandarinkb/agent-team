# Brief: {{TITLE}}

- **Task:** {{TASK_ID}}
- **Workflow:** {{KIND}} (`.agents/workflows/{{WORKFLOW_FILE}}`)
- **Created:** {{DATE}}

Fill every field before a teammate starts. A field you cannot fill means the task is not scoped yet. A teammate cannot ask you questions in the middle of a run, so this brief is its whole context.

```
GOAL         <fill: one sentence a stranger could act on>
SCOPE        May write: <fill: paths>
             May not write: <fill: paths owned by other teammates or out of scope>
             Branch or worktree: <fill: owned by one writer only>
CONTEXT      <fill: file:line pointers, related tickets or PRs, reports from earlier steps>
ACCEPTANCE   - <fill: checkable criterion, one per line>
VERIFY       <fill: exact commands, or how qa drives the real surface>
DECISIONS    <fill: links to approved decisions in decisions.md that this work depends on>
FORBIDDEN    No edits outside scope. No commit, push, or merge. No irreversible action.
             <fill: task-specific bans>
REPORT       Status, branch, SHA, commands run with decisive output, not verified, decisions needed
```

## Notes

<fill: anything the teammate must know that does not fit above, or "none">

## PHP-to-Go checklist (migration only)

Write a parity case for each item that applies. Delete this section for other workflows.

- [ ] Empty list: PHP `[]` versus a Go nil slice that encodes as `null`.
- [ ] Empty object: PHP encodes an empty associative array as `[]`, not `{}`.
- [ ] Missing versus null: Go `omitempty` drops fields PHP sends as `null`, `0`, `""`, or `false`.
- [ ] Numbers as strings: PHP often returns IDs and decimals as strings (`"1"`, `"10.50"`).
- [ ] Float formatting and large integers that lose precision as `float64`.
- [ ] Booleans returned as `1`/`0` or `"1"`/`"0"`.
- [ ] Dates: format, timezone, midnight values.
- [ ] Error shape and status for validation, not-found, and auth failures.
- [ ] Routing: trailing slash, `a[]=1&a[]=2` query arrays, case sensitivity.
- [ ] Headers: `Content-Type` with charset, caching, CORS.
- [ ] Array order without an explicit `ORDER BY`.
