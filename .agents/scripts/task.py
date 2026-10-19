#!/usr/bin/env python3
"""Move a task through its states. Each move names who makes it and the evidence for it.

    todo -> in_progress -> implemented -> spec_ok -> verified -> committed
                 ^               |            |          |
                 +--- fix task --+------------+----------+

    task.py list <job>
    task.py set <job> T-01 in_progress  --by backend [--decision D-n]   (round 4+ needs a user decision)
    task.py set <job> T-01 implemented  --by backend
    task.py set <job> T-01 spec_ok      --by spec-reviewer --review reviews/T-01-r1.md
    task.py set <job> T-01 todo         --by spec-reviewer|qa --fix fixes/F-01.md
    task.py set <job> T-01 implemented  --by qa --note "<why>"          (Bruno changed: back to spec review, same round)
    task.py set <job> T-01 verified     --by qa [--bruno evidence/x.json] [--db evidence/x.md] [--test-log evidence/x.log]
    task.py set <job> T-01 committed    --by git --sha <commit>

Paths are relative to the job directory. The guard_task hook checks that --by is the
agent actually running the command. The revision is computed here from git, never
taken from a report.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import teamlib as t  # noqa: E402

OWNER = "<owner>"
MOVES = {
    ("todo", "in_progress"): (OWNER,),
    ("in_progress", "implemented"): (OWNER,),
    ("implemented", "spec_ok"): ("spec-reviewer",),
    ("implemented", "todo"): ("spec-reviewer",),
    ("spec_ok", "verified"): ("qa",),
    ("spec_ok", "todo"): ("qa",),
    ("spec_ok", "implemented"): ("qa",),
    ("verified", "todo"): ("qa", "spec-reviewer"),
    ("verified", "committed"): ("git",),
}


def job_path(job_id, rel, what):
    if not rel:
        raise t.GateError(f"{what} is required for this move")
    d = t.job_dir(job_id)
    path = os.path.realpath(os.path.join(d, rel))
    if not path.startswith(os.path.realpath(d) + os.sep):
        raise t.GateError(f"{what} must be inside the job directory {d}")
    return path


def to_in_progress(job, task, a):
    if job["status"] != "approved":
        raise t.GateError("the user has not approved the spec (gate G1)")
    t.worktree_of(job)
    nxt = task["round"] + 1
    if nxt > t.MAX_ROUNDS:
        if not a.decision:
            raise t.GateError(f"round {nxt} exceeds the budget of {t.MAX_ROUNDS}; raise a decision to the user, "
                              "then pass --decision D-n once the lead records the answer")
        decisions = t.read_text(os.path.join(t.job_dir(job["id"]), "decisions.md"))
        if f"## {a.decision}\n" not in decisions:
            raise t.GateError(f"{a.decision} is not recorded in decisions.md")
    task["round"] = nxt


def to_implemented(job, task, a):
    if task["status"] == "spec_ok":
        if not a.note:
            raise t.GateError("--note is required: say what changed in the Bruno collection")
        task.setdefault("notes", []).append(a.note)
        return
    wt = t.worktree_of(job)
    changed = set(t.git(wt, "diff", "--name-only", job["base"]).splitlines())
    changed |= set(t.git(wt, "ls-files", "--others", "--exclude-standard").splitlines())
    if not any(t.matches_any(p, task["scope"]) for p in changed):
        raise t.GateError(f"no file in this task's scope {task['scope']} differs from the base commit")


def to_spec_ok(job, task, a):
    path = job_path(job["id"], a.review, "--review")
    text = t.require_filled(path, "spec review")
    if t.field(text, "Task") != task["id"]:
        raise t.GateError(f"the review is for task {t.field(text, 'Task')!r}, not {task['id']}")
    if (t.field(text, "Verdict") or "").upper() != "PASS":
        raise t.GateError("the review verdict is not PASS; send a fix task instead")
    missing = [ac for ac in task["acs"] if ac not in text]
    if missing:
        raise t.GateError(f"the review does not cover {', '.join(missing)}")
    wt = t.worktree_of(job)
    tree = t.staged_tree(wt)
    if "bruno" in task["verify"]:
        if (t.field(text, "Bruno coverage") or "").upper() != "PASS":
            raise t.GateError("the review must say 'Bruno coverage: PASS' after checking the collection against the spec")
        t.check_bruno_collection(os.path.join(wt, t.bruno_dir(job["id"])), task["acs"])
    if t.field(text, "Revision") != tree:
        raise t.GateError(f"the review names revision {t.field(text, 'Revision')!r}, but the staged tree is {tree}")
    task["reviewed_revision"], task["review"] = tree, a.review


def to_todo(job, task, a):
    path = job_path(job["id"], a.fix, "--fix")
    text = t.require_filled(path, "fix task")
    if t.field(text, "Task") != task["id"]:
        raise t.GateError(f"the fix task is for {t.field(text, 'Task')!r}, not {task['id']}")
    if not t.ac_ids(text):
        raise t.GateError("the fix task must name the acceptance criterion it breaks")
    task.setdefault("fixes", []).append(a.fix)


def to_verified(job, task, a):
    wt = t.worktree_of(job)
    tree = t.staged_tree(wt)
    vouched = t.review_paths(job["id"], task)
    changed = [p for p in t.changed_between(wt, task["reviewed_revision"], tree) if t.matches_any(p, vouched)]
    if changed:
        raise t.GateError(f"files the spec review vouched for changed since ({', '.join(changed[:5])}); "
                          "send the task back for review (qa: move it to implemented with --note)")
    evidence = {}
    if "bruno" in task["verify"]:
        evidence["bruno"] = a.bruno
        path = job_path(job["id"], a.bruno, "--bruno")
        t.bruno_summary(path)
        t.check_bruno_collection(os.path.join(wt, t.bruno_dir(job["id"])), task["acs"])
    if "db" in task["verify"]:
        evidence["db"] = a.db
        t.check_db_evidence(job_path(job["id"], a.db, "--db"), tree)
    if "test" in task["verify"]:
        evidence["test"] = a.test_log
        text = t.read_text(job_path(job["id"], a.test_log, "--test-log"))
        if t.field(text, "Revision") != tree:
            raise t.GateError(f"the test log must start with 'Revision: {tree}' and the output of the run")
    for rel in evidence.values():
        t.require_no_secrets(job_path(job["id"], rel, "evidence"))
    task["verified_revision"], task["evidence"] = tree, evidence


def to_committed(job, task, a):
    if not a.sha:
        raise t.GateError("--sha is required")
    wt = t.worktree_of(job)
    commit_tree = t.git(wt, "rev-parse", f"{a.sha}^{{tree}}")
    report = t.read_text(os.path.join(t.job_dir(job["id"]), "test-report.md"))
    if t.field(report, "Revision") != commit_tree:
        raise t.GateError("the commit's tree differs from the revision in the test report")
    try:
        t.git(wt, "merge-base", "--is-ancestor", a.sha, job["branch"])
    except t.GateError:
        raise t.GateError(f"{a.sha} is not on {job['branch']}")
    task["commit"] = a.sha


CHECKS = {"in_progress": to_in_progress, "implemented": to_implemented, "spec_ok": to_spec_ok,
          "todo": to_todo, "verified": to_verified, "committed": to_committed}


def cmd_set(a):
    job = t.load_job(a.job)
    task = t.load_task(a.job, a.task)
    move = (task["status"], a.status)
    if move not in MOVES:
        raise t.GateError(f"cannot move {a.task} from {task['status']} to {a.status}")
    allowed = [task["owner"] if r == OWNER else r for r in MOVES[move]]
    if a.by not in allowed:
        raise t.GateError(f"only {' or '.join(allowed)} may move {a.task} from {task['status']} to {a.status}")
    CHECKS[a.status](job, task, a)
    task["history"].append({"at": t.now(), "by": a.by, "from": task["status"], "to": a.status, "round": task["round"]})
    task["status"] = a.status
    t.save_task(a.job, task)
    t.log_row(a.job, a.by, f"{a.task} {move[0]}->{a.status}", f"round {task['round']}")
    print(f"{a.task}: {move[0]} -> {a.status} (round {task['round']})")


def cmd_list(a):
    for tid in t.task_ids(a.job):
        task = t.load_task(a.job, tid)
        print(f"{tid}\t{task['status']}\tround {task['round']}\t{task['owner']}\t{','.join(task['acs'])}\t{task['title']}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("job")
    s = sub.add_parser("set"); s.add_argument("job"); s.add_argument("task"); s.add_argument("status")
    s.add_argument("--by", required=True, choices=t.ROLES)
    for opt in ("--review", "--fix", "--bruno", "--db", "--test-log", "--sha", "--decision", "--note"):
        s.add_argument(opt)
    a = p.parse_args(argv)
    try:
        cmd_set(a) if a.cmd == "set" else cmd_list(a)
    except t.GateError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
