# Database access

Teammates read the database through an MCP server, with one `SELECT` per call. Nothing else.

## Setup (once per project)

1. Point the MCP server at a **test** database, never production.
2. Connect it with a database user that has only SELECT grants. This is the first line of defense. `guard_sql.py` is the second.
3. Write `.agents/db-mcp.json` with the server name as it appears in `mcp__<server>__<tool>`:
   ```json
   {"servers": ["postgres"], "sql_fields": ["sql", "query", "statement"]}
   ```
   Without it, any MCP tool that takes one of those fields is treated as a database tool.

## What the hook refuses

More than one statement, anything not starting with SELECT or WITH, any write or DDL keyword anywhere (including inside a WITH), `SELECT ... INTO`, locking reads, sleep and file functions, sequence calls, and executable comments. It checks every dialect reading of quotes and comments, so a statement hidden in what one database calls a string is still caught.

## Test data

Create test data through the API under test or a seed script that the brief names. Never through MCP.

## Column checks (qa)

For every case in the spec's data contract, SELECT the row and compare each listed column with its rule. Write `evidence/<task>-db.md` from the template, one row per column, with the query you ran. Columns the spec does not list go under "not checked".
