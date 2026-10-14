#!/usr/bin/env python3
"""Append one row to a task's decision log. Adapted from pstack's show-me-your-work log.sh.

    python3 .agents/scripts/log_row.py <task-id> <phase> <decision> <why> <evidence> <result>

The log is append-only. A wrong row gets a new row that supersedes it.
Cells are flattened to one line, and a cell a spreadsheet would read as a formula gets a leading quote.
"""
import datetime
import os
import sys

AGENTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEADER = "ts\tphase\tdecision\twhy\tevidence\tresult\n"


def clean(cell):
    cell = " ".join(cell.replace("\t", " ").splitlines()).strip()
    return "'" + cell if cell[:1] in ("=", "+", "-", "@", '"') else cell


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 6:
        print("usage: log_row.py <task-id> <phase> <decision> <why> <evidence> <result>", file=sys.stderr)
        return 2
    path = os.path.join(AGENTS, "work", argv[0], "log.tsv")
    if not os.path.isdir(os.path.dirname(path)):
        print(f"log_row: no task directory for {argv[0]}", file=sys.stderr)
        return 2
    new = not os.path.exists(path) or os.path.getsize(path) == 0
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write(HEADER)
        f.write("\t".join([ts] + [clean(c) for c in argv[1:]]) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
