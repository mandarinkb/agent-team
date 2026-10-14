#!/usr/bin/env python3
"""Record PHP API responses as a baseline, then check a Go endpoint against it.

    parity.py record --base-url URL --cases cases.jsonl --out baseline.jsonl
    parity.py check  --base-url URL --baseline baseline.jsonl [--config parity.json] [--json]

Exit codes for `check`:
    0  every case matches the baseline
    1  at least one case differs
    2  usage or input error
    3  no case differs, but at least one could not be reached (inconclusive, not a pass)

Python 3.9+, standard library only.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

DROPPED_HEADERS = {"authorization", "cookie", "set-cookie", "date", "x-request-id"}
DEFAULT_CONFIG = {"compare_headers": ["content-type"], "ignore_paths": [], "max_diffs": 20, "timeout": 10}
ENV_REF = re.compile(r"\$\{([A-Z0-9_]+)\}")


class InputError(Exception):
    pass


def read_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise InputError(f"{path}:{n}: {e.msg}")
    ids = [r.get("id") for r in rows]
    if None in ids or len(set(ids)) != len(ids):
        raise InputError(f"{path}: every row needs a unique id")
    return rows


def expand_env(value):
    def sub(m):
        if m.group(1) not in os.environ:
            raise InputError(f"environment variable {m.group(1)} is not set")
        return os.environ[m.group(1)]
    return ENV_REF.sub(sub, value)


def send(base_url, case, timeout):
    body = case.get("body")
    data = None
    headers = {k: expand_env(v) for k, v in case.get("headers", {}).items()}
    if body is not None:
        data = json.dumps(body).encode() if not isinstance(body, str) else body.encode()
        headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(base_url.rstrip("/") + case["path"], data=data,
                                 headers=headers, method=case.get("method", "GET"))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def parse_body(raw):
    text = raw.decode("utf-8", errors="replace")
    try:
        return {"json": json.loads(text)}
    except json.JSONDecodeError:
        return {"text": text}


def capture(base_url, case, timeout):
    status, headers, raw = send(base_url, case, timeout)
    kept = {k.lower(): v for k, v in headers.items() if k.lower() not in DROPPED_HEADERS}
    return {"status": status, "headers": kept, "body": parse_body(raw)}


def type_name(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "number"
    return {str: "string", list: "array", dict: "object"}[type(v)]


def diff(expected, actual, path="$"):
    """Yield (path, message). Object key order is ignored, array order is not."""
    te, ta = type_name(expected), type_name(actual)
    if te != ta:
        yield path, f"type {te} -> {ta} ({json.dumps(expected)} -> {json.dumps(actual)})"
    elif te == "object":
        for k in sorted(set(expected) | set(actual)):
            p = f"{path}.{k}"
            if k not in actual:
                yield p, "missing in Go"
            elif k not in expected:
                yield p, f"extra in Go ({json.dumps(actual[k])})"
            else:
                yield from diff(expected[k], actual[k], p)
    elif te == "array":
        if len(expected) != len(actual):
            yield path, f"length {len(expected)} -> {len(actual)}"
        for i, (e, a) in enumerate(zip(expected, actual)):
            yield from diff(e, a, f"{path}[{i}]")
    elif expected != actual:
        yield path, f"{json.dumps(expected)} -> {json.dumps(actual)}"


def ignore_matcher(patterns):
    compiled = []
    for p in patterns:
        rx = re.escape(p).replace(r"\[\*\]", r"\[\d+\]").replace(r"\*", r"[^.\[]+")
        compiled.append(re.compile(rx + r"(?:$|[.\[])"))
    return lambda path: any(c.match(path) for c in compiled)


def compare(baseline, current, config):
    problems = []
    if baseline["status"] != current["status"]:
        problems.append(("status", f"{baseline['status']} -> {current['status']}"))
    for h in config["compare_headers"]:
        e, a = baseline["headers"].get(h.lower()), current["headers"].get(h.lower())
        if e != a:
            problems.append((f"header {h}", f"{e!r} -> {a!r}"))
    eb, ab = baseline["body"], current["body"]
    if "json" in eb and "json" in ab:
        ignored = ignore_matcher(config["ignore_paths"])
        problems += [(p, m) for p, m in diff(eb["json"], ab["json"]) if not ignored(p)]
    elif eb != ab:
        problems.append(("body", "non-JSON body differs" if "text" in eb and "text" in ab
                         else "one side is JSON and the other is not"))
    return problems


def load_config(path):
    config = dict(DEFAULT_CONFIG)
    if path:
        with open(path, encoding="utf-8") as f:
            config.update(json.load(f))
    return config


def cmd_record(args):
    config = load_config(args.config)
    cases = read_jsonl(args.cases)
    with open(args.out, "w", encoding="utf-8") as out:
        for case in cases:
            result = capture(args.base_url, case, config["timeout"])
            out.write(json.dumps({"id": case["id"], "request": case, **result}, ensure_ascii=False) + "\n")
            print(f"recorded {case['id']} status={result['status']}")
    print(f"{len(cases)} cases written to {args.out}")
    return 0


def cmd_check(args):
    config = load_config(args.config)
    rows = read_jsonl(args.baseline)
    results = []
    for row in rows:
        try:
            current = capture(args.base_url, row["request"], config["timeout"])
        except (urllib.error.URLError, OSError) as e:
            results.append({"id": row["id"], "verdict": "UNREACHABLE", "detail": str(getattr(e, "reason", e))})
            continue
        problems = compare(row, current, config)
        results.append({"id": row["id"], "verdict": "DIFF" if problems else "MATCH",
                        "diffs": [{"path": p, "detail": m} for p, m in problems]})
    counts = {v: sum(r["verdict"] == v for r in results) for v in ("MATCH", "DIFF", "UNREACHABLE")}
    code = 1 if counts["DIFF"] else 3 if counts["UNREACHABLE"] else 0
    if args.json:
        print(json.dumps({"counts": counts, "exit": code, "results": results}, ensure_ascii=False, indent=2))
        return code
    for r in results:
        print(f"{r['verdict']:<11} {r['id']}" + (f"  {r['detail']}" if "detail" in r else ""))
        for d in r.get("diffs", [])[: config["max_diffs"]]:
            print(f"    {d['path']}: {d['detail']}")
        hidden = len(r.get("diffs", [])) - config["max_diffs"]
        if hidden > 0:
            print(f"    ... {hidden} more")
    print(f"\nMATCH {counts['MATCH']}  DIFF {counts['DIFF']}  UNREACHABLE {counts['UNREACHABLE']}  of {len(results)}")
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record", help="capture PHP responses as the baseline")
    rec.add_argument("--base-url", required=True)
    rec.add_argument("--cases", required=True)
    rec.add_argument("--out", required=True)
    rec.add_argument("--config")
    chk = sub.add_parser("check", help="compare a running endpoint against the baseline")
    chk.add_argument("--base-url", required=True)
    chk.add_argument("--baseline", required=True)
    chk.add_argument("--config")
    chk.add_argument("--json", action="store_true", help="print a machine-readable report")
    args = parser.parse_args(argv)
    try:
        return cmd_record(args) if args.command == "record" else cmd_check(args)
    except (InputError, OSError, json.JSONDecodeError) as e:
        print(f"parity: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
