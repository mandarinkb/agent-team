#!/usr/bin/env python3
"""PreToolUse hook on Bash: no push ever, no history destruction, and the commit gate.

A commit with a 'Job: <id>' line goes through without asking the user, but only when
this hook can prove, from git and the job files, that:
  - the git teammate runs it, on the job's branch, in the job's worktree;
  - every task is verified;
  - the test report says PASS for every acceptance criterion, with no placeholders;
  - the staged tree is exactly the revision the test report names;
  - every staged path belongs to a task's scope or to the job's Bruno collection;
  - no evidence file and no staged Bruno file holds a secret;
  - the Bruno collection asserts bodies and names every criterion, and for an API job
    a fresh run of it, made here, passes (see team.json to configure the command).
A commit without a Job line asks the user.
"""
import os
import re
import shlex

from hooklib import allow, ask, deny, lenient_identity, read_input, role_of, teamlib as t

SHELLS = ("bash", "sh", "zsh", "dash")


def tokens_of(command):
    lex = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lex.whitespace_split = True
    try:
        return list(lex)
    except ValueError:
        return command.split()


def git_calls(command, depth=0):
    """Yield (global_opts, subcommand, args) for every git call, looking inside sh -c and eval."""
    toks = tokens_of(command)
    for i, tok in enumerate(toks):
        name = tok.rsplit("/", 1)[-1]
        if depth < 3 and name in SHELLS and i + 2 < len(toks) and toks[i + 1] == "-c":
            yield from git_calls(toks[i + 2], depth + 1)
        if depth < 3 and name == "eval":
            yield from git_calls(" ".join(toks[i + 1:]), depth + 1)
        if name != "git":
            continue
        opts, j = {}, i + 1
        while j < len(toks) and toks[j].startswith("-"):
            if toks[j] in ("-C", "-c", "--git-dir", "--work-tree") and j + 1 < len(toks):
                opts[toks[j]] = toks[j + 1]
                j += 2
            else:
                j += 1
        if j < len(toks):
            end = j + 1
            while end < len(toks) and toks[end] not in (";", "&&", "||", "|", "&", "(", ")"):
                end += 1
            yield opts, toks[j], toks[j + 1:end]


def check_destructive(sub, args):
    joined = " ".join(args)
    if sub == "push":
        deny("pushing is never allowed for this team. The user pushes.")
    if "--no-verify" in args:
        deny("--no-verify skips the checks.")
    if sub == "reset" and "--hard" in args:
        deny("git reset --hard destroys work.")
    if sub == "clean" and re.search(r"(^|\s)(-[a-zA-Z]*f|--force)", joined):
        deny("git clean -f destroys untracked work.")
    if sub == "branch" and re.search(r"(^|\s)(-D|--delete\s+--force|--force\s+--delete)", joined):
        deny("git branch -D deletes unmerged work.")
    if sub in ("filter-branch", "filter-repo"):
        deny("rewriting history is not allowed.")


def commit_message(args, cwd):
    msgs, i = [], 0
    while i < len(args):
        a = args[i]
        if a in ("-a", "--all", "--amend", "--allow-empty", "-o", "--only", "-i", "--include", "-p", "--patch"):
            deny(f"git commit {a} is not allowed; commit exactly what git staged and the reports checked.")
        if a in ("-m", "--message") and i + 1 < len(args):
            msgs.append(args[i + 1]); i += 2; continue
        if a.startswith("--message="):
            msgs.append(a.split("=", 1)[1])
        elif a.startswith("-m") and len(a) > 2:
            msgs.append(a[2:])
        elif a in ("-F", "--file") and i + 1 < len(args):
            msgs.append(t.read_text(os.path.join(cwd, args[i + 1]))); i += 2; continue
        elif not a.startswith("-"):
            deny("git commit with paths is not allowed; commit exactly what git staged.")
        i += 1
    return "\n".join(msgs)


def commit_gate(job_id, cwd):
    job = t.load_job(job_id)
    if job["status"] != "approved":
        raise t.GateError(f"job {job_id} is '{job['status']}', not approved")
    wt = t.worktree_of(job)
    top = t.git(cwd, "rev-parse", "--show-toplevel")
    if os.path.realpath(top) != os.path.realpath(wt):
        raise t.GateError(f"commit from the job worktree {wt}, not {top}")
    branch = t.git(wt, "rev-parse", "--abbrev-ref", "HEAD")
    if branch != job["branch"]:
        raise t.GateError(f"the worktree is on {branch}, not {job['branch']}")
    tasks = [t.load_task(job_id, tid) for tid in t.task_ids(job_id)]
    open_tasks = [x["id"] for x in tasks if x["status"] != "verified"]
    if not tasks or open_tasks:
        raise t.GateError(f"tasks not verified: {', '.join(open_tasks) or 'none exist'}")
    d = t.job_dir(job_id)
    report = t.require_filled(os.path.join(d, "test-report.md"), "test report")
    if (t.field(report, "Verdict") or "").upper() != "PASS":
        raise t.GateError("the test report verdict is not PASS")
    tree = t.staged_tree(wt)
    if t.field(report, "Revision") != tree:
        raise t.GateError(f"the test report names revision {t.field(report, 'Revision')!r}, staged tree is {tree}")
    if not t.field(report, "Reset"):
        raise t.GateError("the test report has no 'Reset:' line saying how test data was reset before the final run")
    spec = t.read_text(os.path.join(d, "spec.md"))
    lines = report.splitlines()
    unproven = [ac for ac in t.ac_ids(spec)
                if not any(re.search(rf"\b{ac}\b", ln) and re.search(r"\bPASS\b", ln) for ln in lines)]
    if unproven:
        raise t.GateError(f"the test report has no PASS row for {', '.join(unproven)}")
    bruno = t.bruno_dir(job_id)
    scopes = [g for x in tasks for g in x["scope"]] + [f"{bruno}/*", f"{bruno}/**"]
    staged = t.git(wt, "diff", "--cached", "--name-only", "HEAD").splitlines()
    if not staged:
        raise t.GateError("nothing is staged")
    stray = [p for p in staged if not t.matches_any(p, scopes)]
    if stray:
        raise t.GateError(f"staged paths outside every task's scope: {', '.join(stray[:5])}")
    t.require_no_secrets(os.path.join(d, "test-report.md"), report)
    evidence = os.path.join(d, "evidence")
    for name in sorted(os.listdir(evidence)) if os.path.isdir(evidence) else []:
        t.require_no_secrets(os.path.join(evidence, name))
    for path in staged:
        if path.startswith(bruno + "/"):
            t.require_no_secrets(path, t.git(wt, "show", f":{path}", check=False))
    bruno_acs = sorted({ac for x in tasks if "bruno" in x["verify"] for ac in x["acs"]})
    note = ""
    if bruno_acs:
        t.check_bruno_collection(os.path.join(wt, bruno), bruno_acs)
    if job["api"] and t.config()["commit_rerun_bruno"]:
        out = os.path.join(evidence, "commit-gate-bruno.json")
        os.makedirs(evidence, exist_ok=True)
        if os.path.exists(out):
            os.remove(out)
        summary = t.run_bruno(wt, job_id, out)
        with open(out + ".tmp", "w", encoding="utf-8") as f:
            f.write(t.redact_text(t.read_text(out))[0])
        os.replace(out + ".tmp", out)
        note = f", fresh Bruno run {summary.get('passedRequests', '?')}/{summary.get('totalRequests')} requests passed"
    return tree, len(staged), note


def main():
    event = read_input()
    if event.get("tool_name") != "Bash":
        return
    command = (event.get("tool_input") or {}).get("command", "")
    if re.search(r"\bgh\s+(pr\s+(create|merge|ready)|repo\s+(sync|delete)|release\s+create)\b", command):
        deny("opening, merging, or publishing through gh is the user's call.")
    role = role_of(event)
    for opts, sub, args in git_calls(command):
        check_destructive(sub, args)
        if sub != "commit":
            continue
        cwd = os.path.join(event.get("cwd") or os.getcwd(), opts.get("-C", ""))
        message = commit_message(args, cwd)
        m = re.search(r"^Job:\s*(J-\S+)\s*$", message, re.M)
        if not m:
            if role == "lead":
                ask("This commit has no 'Job:' line, so no gate checked it. Approve only if you meant it.")
            deny("a teammate commits only job work, with a final 'Job: <job-id>' line.")
        if role != "git" and not (role is None and lenient_identity()):
            deny(f"only the git teammate commits job work; this agent is {role or 'unidentified'}.")
        try:
            tree, count, note = commit_gate(m.group(1), cwd)
        except t.GateError as e:
            deny(f"commit gate: {e}.")
        allow(f"commit gate passed for {m.group(1)}: {count} staged files, tree {tree[:12]} matches the PASS test report{note}")


if __name__ == "__main__":
    main()
