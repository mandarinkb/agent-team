#!/usr/bin/env python3
"""Replace secrets in evidence files with <redacted>, in place.

    redact.py <file> [<file> ...]

qa runs it on every evidence file before task.py verified, because Bruno's JSON report
holds full requests and responses, including tokens. The gates refuse a file that still
looks like it holds a secret.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import teamlib as t  # noqa: E402


def main(paths):
    if not paths:
        print(__doc__, file=sys.stderr)
        return 2
    for path in paths:
        text, count = t.redact_text(t.read_text(path))
        if count:
            tmp = f"{path}.{os.getpid()}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp, path)
        left = t.find_secrets(text)
        print(f"{path}: {count} redacted" + (f", still suspicious: {'; '.join(left)}" if left else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
