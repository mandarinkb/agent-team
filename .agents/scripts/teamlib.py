"""Shared helpers for job.py, task.py, and the hooks.

Everything a gate decides is recomputed from files and git here, never taken from a
teammate's report. Standard library only.
"""
import datetime
import fnmatch
import json
import os
import re
import subprocess
import sys
import unicodedata

def _root():
    """The project that holds .agents/. In an installed project .agents/scripts is a symlink,
    and Python resolves it when it imports, so look at the path that was invoked first."""
    if os.environ.get("TEAM_ROOT"):
        return os.environ["TEAM_ROOT"]
    for path in (sys.argv[0] if sys.argv else "", __file__):
        parts = os.path.abspath(path).split(os.sep) if path else []
        if ".agents" in parts:
            i = len(parts) - 1 - parts[::-1].index(".agents")
            return os.sep.join(parts[:i]) or os.sep
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


ROOT = _root()
AGENTS = os.path.join(ROOT, ".agents")
WORK = os.path.join(AGENTS, "work")
TEMPLATES = os.path.join(AGENTS, "templates")
USER_LOG = os.path.join(WORK, ".user-prompts.jsonl")

PLACEHOLDER = "<fill"
LEAD = "lead"
IMPLEMENTERS = ("backend", "frontend")
ROLES = ("lead", "analyst", "backend", "frontend", "spec-reviewer", "qa", "git")
VERIFY_KINDS = ("bruno", "db", "test")
MAX_ROUNDS = 3


class GateError(Exception):
    """A gate refused. The message tells the agent what evidence is missing."""


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="microseconds")


def job_dir(job_id):
    if not re.fullmatch(r"J-\d{8}-[a-z0-9-]+", job_id or ""):
        raise GateError(f"invalid job id {job_id!r}")
    path = os.path.join(WORK, job_id)
    if not os.path.isdir(path):
        raise GateError(f"job {job_id} does not exist under {WORK}")
    return path


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_job(job_id):
    return read_json(os.path.join(job_dir(job_id), "job.json"))


def save_job(job_id, job):
    write_json(os.path.join(job_dir(job_id), "job.json"), job)


def task_ids(job_id):
    state = os.path.join(job_dir(job_id), "state")
    if not os.path.isdir(state):
        return []
    return sorted(f[:-5] for f in os.listdir(state) if re.fullmatch(r"T-\d{2,}\.json", f))


def load_task(job_id, task_id):
    path = os.path.join(job_dir(job_id), "state", f"{task_id}.json")
    if not os.path.exists(path):
        raise GateError(f"task {task_id} does not exist in {job_id}")
    return read_json(path)


def save_task(job_id, task):
    write_json(os.path.join(job_dir(job_id), "state", f"{task['id']}.json"), task)


def log_row(job_id, actor, action, detail):
    path = os.path.join(job_dir(job_id), "log.tsv")
    new = not os.path.exists(path)
    clean = [re.sub(r"[\t\r\n]+", " ", str(v)) for v in (now(), actor, action, detail)]
    clean = ["'" + v if v[:1] in "=+-@\"" else v for v in clean]
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write("ts\tactor\taction\tdetail\n")
        f.write("\t".join(clean) + "\n")


def require_filled(path, what):
    if not os.path.isfile(path):
        raise GateError(f"{what} not found: {path}")
    text = read_text(path)
    if PLACEHOLDER in text:
        raise GateError(f"{what} still has '{PLACEHOLDER}' placeholders: {path}")
    return text


def field(text, name):
    """Value of a '**Name:** value' or 'Name: value' line, or None."""
    m = re.search(rf"^\W*{re.escape(name)}\W*:\**\s*`?([^`\n]*?)`?\s*$", text, re.M | re.I)
    return m.group(1).strip() if m else None


def ac_ids(text):
    return sorted(set(re.findall(r"\bAC-\d+\b", text)), key=lambda a: int(a[3:]))


# ---- the user's own words -------------------------------------------------

def _norm(s):
    return " ".join(unicodedata.normalize("NFC", s).split())


def quote_from_user(quote, since):
    """True when `quote` appears in one prompt the UserPromptSubmit hook logged after `since`."""
    q = _norm(quote or "")
    if len(q) < 2:
        raise GateError("the user's words are required (--quote), copied exactly from what the user typed")
    if not os.path.exists(USER_LOG):
        raise GateError("no user prompt log yet; the log_user_prompt hook must be installed")
    with open(USER_LOG, encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("ts", "") > since and q in _norm(row.get("prompt", "")):
                return True
    raise GateError("that quote is not in anything the user typed since the job started; "
                    "ask the user and copy their words exactly")


# ---- git -------------------------------------------------------------------

def git(worktree, *args, check=True):
    p = subprocess.run(["git", "-C", worktree, *args], capture_output=True, text=True)
    if check and p.returncode != 0:
        raise GateError(f"git {' '.join(args)} failed in {worktree}: {p.stderr.strip()}")
    return p.stdout.strip()


def worktree_of(job):
    wt = job.get("worktree")
    if not wt or not os.path.isdir(wt):
        raise GateError("the job has no worktree yet; the git teammate runs job.py set-worktree")
    return wt


def staged_tree(worktree):
    """Tree id of the index, after proving nothing outside the index can change the result."""
    if git(worktree, "diff", "--name-only"):
        raise GateError("the worktree has unstaged changes; ask git to stage them, then review or test again")
    untracked = git(worktree, "ls-files", "--others", "--exclude-standard")
    if untracked:
        raise GateError(f"the worktree has untracked files ({untracked.splitlines()[0]} ...); stage or remove them first")
    return git(worktree, "write-tree")


def changed_between(worktree, old_tree, new_tree):
    if old_tree == new_tree:
        return []
    return git(worktree, "diff", "--name-only", old_tree, new_tree).splitlines()


def matches_any(path, globs):
    return any(fnmatch.fnmatch(path, g) for g in globs)


# ---- evidence files --------------------------------------------------------

def bruno_summary(path):
    """Sum every 'summary' object in a `bru run --reporter-json` file."""
    if not os.path.isfile(path):
        raise GateError(f"Bruno result not found: {path}")
    try:
        data = read_json(path)
    except ValueError as e:
        raise GateError(f"Bruno result is not JSON: {e}")
    totals = {}

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("summary"), dict):
                for k, v in node["summary"].items():
                    if isinstance(v, (int, float)):
                        totals[k] = totals.get(k, 0) + v
            else:
                for v in node.values():
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    if not totals:
        raise GateError(f"no summary in Bruno result {path}; run bru with --reporter-json")
    failed = sum(v for k, v in totals.items() if k.startswith(("failed", "error")))
    if totals.get("totalRequests", 0) <= 0:
        raise GateError(f"Bruno ran no requests: {path}")
    if failed:
        raise GateError(f"Bruno reports {failed} failed or errored requests, assertions, or tests: {path}")
    return totals


def check_db_evidence(path, revision):
    text = require_filled(path, "database check")
    if field(text, "Revision") != revision:
        raise GateError(f"database check names revision {field(text, 'Revision')!r}, expected {revision}")
    if re.search(r"\|\s*FAIL\s*\|", text):
        raise GateError(f"database check has FAIL rows: {path}")
    if not re.search(r"\|\s*PASS\s*\|", text):
        raise GateError(f"database check has no PASS rows: {path}")
    return text


# ---- team configuration ----------------------------------------------------

TEAM_CONFIG = os.path.join(AGENTS, "team.json")
DEFAULT_CONFIG = {
    "bruno_env": "local",
    "commit_rerun_bruno": True,
    "bruno_command": ["bru", "run", "--env", "{env}", "--reporter-json", "{out}"],
    "bruno_timeout": 300,
    "limit_threshold": 95,
}


def config():
    """Defaults overlaid with .agents/team.json. Changing a gate setting is the user's decision."""
    cfg = dict(DEFAULT_CONFIG)
    try:
        cfg.update(read_json(TEAM_CONFIG))
    except (OSError, ValueError):
        pass
    return cfg


def bruno_dir(job_id):
    return f"bruno/{job_id}"


def review_paths(job_id, task):
    """The paths a spec review vouches for: the task's scope and the job's Bruno collection."""
    return list(task["scope"]) + [f"{bruno_dir(job_id)}/*", f"{bruno_dir(job_id)}/**"]


# ---- secrets ---------------------------------------------------------------

_KEEP = r"(?!\{\{|<redacted>|process\.env|\*\*\*)"
SECRET_PATTERNS = [
    ("authorization header", re.compile(
        r"(?i)\bauthorization\b[\"']?\s*[:=]\s*[\"']?(?:bearer|basic|token)\s+(?P<s>" + _KEEP + r"[A-Za-z0-9._~+/=-]{8,})")),
    ("credential field", re.compile(
        r"(?i)[\"'](?:password|passwd|pwd|secret|api[_-]?key|apikey|access[_-]?token|refresh[_-]?token|id[_-]?token|"
        r"client[_-]?secret|private[_-]?key|token)[\"']\s*:\s*[\"'](?P<s>" + _KEEP + r"[^\"']{4,})[\"']")),
    ("credential variable", re.compile(
        r"(?im)^\s*(?:password|passwd|secret|api[_-]?key|apikey|access[_-]?token|refresh[_-]?token|client[_-]?secret|"
        r"token|auth[_-]?token)\s*[:=]\s*(?P<s>" + _KEEP + r"[^\s{][^\s]{5,})\s*$")),
    ("JWT", re.compile(r"(?P<s>\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})")),
    ("AWS access key", re.compile(r"(?P<s>\b(?:AKIA|ASIA)[0-9A-Z]{16}\b)")),
    ("private key", re.compile(r"(?P<s>-----BEGIN [A-Z ]*PRIVATE KEY-----)")),
    ("password in a URL", re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s:/@]+:(?P<s>" + _KEEP + r"[^\s@/]{3,})@")),
]


def find_secrets(text):
    found = []
    for label, pattern in SECRET_PATTERNS:
        for m in pattern.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            found.append(f"{label} on line {line}")
    return found


def redact_text(text):
    count = 0
    for _, pattern in SECRET_PATTERNS:
        def repl(m):
            nonlocal count
            count += 1
            s, e = m.span("s")
            return m.group(0)[:s - m.start()] + "<redacted>" + m.group(0)[e - m.start():]
        text = pattern.sub(repl, text)
    return text, count


def require_no_secrets(path, text=None):
    text = read_text(path) if text is None else text
    found = find_secrets(text)
    if found:
        raise GateError(f"{path} contains what looks like a secret ({'; '.join(found[:3])}). "
                        f"Run redact.py on evidence, or move the value to .env and use {{{{process.env.NAME}}}}")


# ---- Bruno collection --------------------------------------------------------

def _blocks(text, name):
    """Bodies of every top-level `name { ... }` block in a .bru file."""
    bodies = []
    for m in re.finditer(rf"(?m)^{re.escape(name)}\s*\{{", text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        bodies.append(text[m.end():i - 1])
    return bodies


def bruno_requests(collection):
    """Request files in a collection, skipping environments, collection.bru, and folder.bru."""
    files = []
    for dirpath, dirnames, filenames in os.walk(collection):
        dirnames[:] = [d for d in dirnames if d not in ("environments", "node_modules")]
        for f in filenames:
            if f.endswith(".bru") and f not in ("collection.bru", "folder.bru"):
                files.append(os.path.join(dirpath, f))
    return sorted(files)


def request_assertion_problem(text):
    """None when a request asserts something about the body or headers, otherwise what is missing."""
    keys = []
    for body in _blocks(text, "assert"):
        for line in body.splitlines():
            key = line.split(":", 1)[0].strip().lstrip("~")
            if key and ":" in line:
                keys.append(key)
    meaningful = [k for k in keys if not re.fullmatch(r"res\.(status|responseTime)", k)]
    tests = "\n".join(_blocks(text, "tests"))
    if meaningful or ("expect(" in tests and re.search(r"getBody|res\.body|getHeader|res\.headers", tests)):
        return None
    if keys or tests.strip():
        return "asserts only the status or timing, never the body or headers"
    return "has no assert or tests block"


def check_bruno_collection(collection, acs):
    """Every request asserts the body or headers, and every criterion is named by some request."""
    if not os.path.isdir(collection):
        raise GateError(f"no Bruno collection at {collection}; qa writes it before the spec review")
    requests = bruno_requests(collection)
    if not requests:
        raise GateError(f"the Bruno collection {collection} has no requests")
    problems, covered = [], set()
    for path in requests:
        text = read_text(path)
        problem = request_assertion_problem(text)
        if problem:
            problems.append(f"{os.path.relpath(path, collection)} {problem}")
        covered |= set(ac_ids(text))
        for secret in find_secrets(text):
            problems.append(f"{os.path.relpath(path, collection)} has {secret}")
    for env in sorted(glob_bru(os.path.join(collection, "environments"))):
        for secret in find_secrets(read_text(env)):
            problems.append(f"{os.path.relpath(env, collection)} has {secret}")
    missing = [ac for ac in acs if ac not in covered]
    if missing:
        problems.append(f"no request names {', '.join(missing)} (put the AC ids in its docs block)")
    if problems:
        raise GateError("Bruno collection: " + "; ".join(problems[:6]))
    return requests


def glob_bru(directory):
    if not os.path.isdir(directory):
        return []
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".bru")]


def run_bruno(worktree, job_id, out_path):
    """Run the job's collection with the configured command and return its summary."""
    cfg = config()
    collection = os.path.join(worktree, bruno_dir(job_id))
    cmd = [part.replace("{env}", cfg["bruno_env"]).replace("{out}", out_path) for part in cfg["bruno_command"]]
    try:
        p = subprocess.run(cmd, cwd=collection, capture_output=True, text=True, timeout=cfg["bruno_timeout"])
    except FileNotFoundError:
        raise GateError(f"{cmd[0]} is not installed; install Bruno CLI (npm i -g @usebruno/cli)")
    except subprocess.TimeoutExpired:
        raise GateError(f"Bruno did not finish within {cfg['bruno_timeout']} seconds")
    if not os.path.exists(out_path):
        raise GateError(f"Bruno wrote no result (exit {p.returncode}): {(p.stderr or p.stdout).strip()[:300]}")
    return bruno_summary(out_path)


def active_jobs():
    """Approved jobs that have a worktree, read straight from disk."""
    jobs = []
    if not os.path.isdir(WORK):
        return jobs
    for name in sorted(os.listdir(WORK)):
        path = os.path.join(WORK, name, "job.json")
        if name.startswith("J-") and os.path.isfile(path):
            try:
                job = read_json(path)
            except ValueError:
                continue
            if job.get("status") == "approved" and job.get("worktree"):
                jobs.append(job)
    return jobs


def writable_paths(job, role):
    """What `role` may write in the job's worktree right now."""
    if role == "qa":
        return [f"{bruno_dir(job['id'])}/*", f"{bruno_dir(job['id'])}/**"]
    if role in IMPLEMENTERS:
        globs = []
        for tid in task_ids(job["id"]):
            task = load_task(job["id"], tid)
            if task["owner"] == role and task["status"] == "in_progress":
                globs += task["scope"]
        return globs
    return []
