#!/usr/bin/env python3
"""PreToolUse hook on MCP tools: the database may be read with one SELECT and nothing else.

Which MCP tools reach a database is read from .agents/db-mcp.json:
    {"servers": ["postgres"], "sql_fields": ["sql", "query", "statement"]}
Without that file, any MCP tool whose input carries one of the sql_fields is treated as
a database tool. A database user with read-only grants is still the first line of
defense; this hook is the second.
"""
import json
import os
import re

from hooklib import deny, read_input, teamlib

CONFIG = os.path.join(teamlib.AGENTS, "db-mcp.json")
DEFAULT_FIELDS = ("sql", "query", "statement", "sql_query")
WRITE_TOOL = re.compile(r"(execute|exec|write|insert|update|delete|upsert|create|alter|drop|truncate|run_sql|migrate)", re.I)
READ_TOOL = re.compile(r"(select|read|query|list|describe|schema|show|get)", re.I)
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|merge|upsert|replace|create|alter|drop|truncate|rename|grant|revoke|comment|copy|"
    r"call|exec|execute|do|set|reset|lock|unlock|vacuum|analyze|reindex|cluster|refresh|attach|detach|pragma|"
    r"into|outfile|dumpfile|load|handler|begin|commit|rollback|savepoint|prepare|deallocate|listen|notify|"
    r"pg_sleep|sleep|benchmark|pg_read_file|pg_read_binary_file|pg_ls_dir|pg_stat_file|lo_import|lo_export|"
    r"dblink\w*|pg_terminate_backend|pg_cancel_backend|set_config|nextval|setval|load_file|xp_cmdshell|"
    r"pg_advisory\w*|current_setting|query_to_xml|sys_exec|sys_eval)\b", re.I)
LOCKING = re.compile(r"\bfor\s+(update|share|no\s+key\s+update|key\s+share)\b", re.I)


def load_config():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        cfg = {}
    return cfg.get("servers") or [], tuple(cfg.get("sql_fields") or DEFAULT_FIELDS)


def strip_sql(sql, backslash_escapes, dash_needs_space, dollar_quotes=True):
    """Remove comments, string literals, and quoted identifiers, keeping the statement shape.

    Databases disagree on backslash escapes and on '--' comments, and a statement hidden
    in what one dialect calls a string is live code in another. check_sql runs every
    reading and refuses when any of them fails.
    """
    out, i, n = [], 0, len(sql)
    while i < n:
        c, two = sql[i], sql[i:i + 2]
        if two == "--" and (not dash_needs_space or sql[i + 2:i + 3] in ("", " ", "\t", "\n", "\r")):
            j = sql.find("\n", i)
            i = n if j < 0 else j
        elif two == "/*":
            j = sql.find("*/", i + 2)
            if j < 0:
                return None
            i = j + 2
            out.append(" ")
        elif c in "'\"`":
            j = i + 1
            while j < n:
                if backslash_escapes and sql[j] == "\\" and c != "`":
                    j += 2
                    continue
                if sql[j] == c:
                    if j + 1 < n and sql[j + 1] == c:
                        j += 2
                        continue
                    break
                j += 1
            if j >= n:
                return None
            out.append(" '' ")
            i = j + 1
        elif c == "$" and dollar_quotes:
            m = re.match(r"\$[A-Za-z_]*\$", sql[i:])
            if m:
                j = sql.find(m.group(0), i + len(m.group(0)))
                if j < 0:
                    return None
                out.append(" '' ")
                i = j + len(m.group(0))
            else:
                out.append(c)
                i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def check_sql(sql):
    """None when the SQL is one read-only SELECT under every dialect reading, otherwise why not."""
    if re.search(r"/\*[!+]", sql):
        return "executable or hint comments (/*! */, /*+ */) are not allowed"
    for backslash in (False, True):
        for dash in (False, True):
            for dollar in (False, True):
                reason = check_reading(strip_sql(sql, backslash, dash, dollar))
                if reason:
                    return reason
    return None


def check_reading(body):
    if body is None:
        return "the SQL has an unterminated comment or string"
    statements = [s for s in body.split(";") if s.strip()]
    if len(statements) != 1:
        return "send exactly one statement"
    stmt = statements[0].strip().lstrip("(").strip()
    first = stmt.split(None, 1)[0].lower() if stmt else ""
    if first not in ("select", "with"):
        return f"only SELECT is allowed, this statement starts with {first.upper() or 'nothing'}"
    bad = FORBIDDEN.search(stmt)
    if bad:
        return f"'{bad.group(0)}' is not allowed in a read-only query"
    if LOCKING.search(stmt):
        return "locking reads (FOR UPDATE / FOR SHARE) are not allowed"
    return None


def main():
    event = read_input()
    tool = event.get("tool_name", "")
    if not tool.startswith("mcp__"):
        return
    parts = tool.split("__")
    server, name = (parts[1], "__".join(parts[2:])) if len(parts) >= 3 else ("", tool)
    servers, fields = load_config()
    inp = event.get("tool_input") or {}
    sql_values = [v for k, v in inp.items() if k.lower() in fields and isinstance(v, str)]
    is_db = server in servers if servers else bool(sql_values)
    if not is_db:
        return
    if WRITE_TOOL.search(name) and not READ_TOOL.search(name):
        deny(f"{tool} can change the database. The team reads the database with SELECT only.")
    for sql in sql_values:
        reason = check_sql(sql)
        if reason:
            deny(f"database access is SELECT only: {reason}.")


if __name__ == "__main__":
    main()
