#!/usr/bin/env python3
"""Job lifecycle: grill -> spec -> G1 approval -> tasks run -> commit.

    job.py new <bug|feature|migration> "<title>" [--api]      lead
    job.py grill-done <job> --quote "<user's words>"          lead
    job.py add-task <job> --owner backend --title "..." --ac AC-1,AC-2 \
           --scope "internal/orders/**,cmd/api/routes.go" --verify bruno,db   lead
    job.py approve <job> --quote "<user's words>"             lead   (gate G1)
    job.py decide <job> D-1 --quote "<user's words>"          lead
    job.py set-worktree <job> --path <dir> --branch job/<job> git
    job.py status <job>                                       anyone
    job.py resume <job>                                       anyone (after a session ends)
    job.py done <job>                                         git
    job.py retro <job>                                        lead   (after done)
    job.py retro-approve <job> R-1 --quote "<user's words>"   lead

Who may run each command is enforced by the guard_task hook. Every gate here checks
files and the user prompt log itself.
"""
import argparse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import teamlib as t  # noqa: E402

KINDS = ("bug", "feature", "migration")


def copy_template(name, dst, **values):
    text = t.read_text(os.path.join(t.TEMPLATES, name))
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)


def require_status(job, *allowed):
    if job["status"] not in allowed:
        raise t.GateError(f"job is '{job['status']}', this step needs {' or '.join(allowed)}")


def cmd_new(a):
    if a.kind not in KINDS:
        raise t.GateError(f"kind must be one of {', '.join(KINDS)}")
    slug = re.sub(r"[^a-z0-9]+", "-", a.title.lower()).strip("-")[:40] or a.kind
    base = f"J-{datetime.date.today():%Y%m%d}-{slug}"
    job_id, n = base, 2
    while os.path.exists(os.path.join(t.WORK, job_id)):
        job_id, n = f"{base}-{n}", n + 1
    d = os.path.join(t.WORK, job_id)
    os.makedirs(os.path.join(d, "state"))
    for sub in ("tasks", "reviews", "fixes", "evidence", "decisions"):
        os.makedirs(os.path.join(d, sub))
    job = {"id": job_id, "kind": a.kind, "title": a.title, "api": a.api, "status": "grilling",
           "created": t.now(), "worktree": None, "branch": None, "base": None}
    t.write_json(os.path.join(d, "job.json"), job)
    copy_template("grill-notes.md", os.path.join(d, "grill-notes.md"), JOB=job_id, TITLE=a.title, KIND=a.kind)
    t.log_row(job_id, "lead", "new", f"{a.kind}: {a.title}")
    print(f"{job_id}\n{d}/grill-notes.md")


def cmd_grill_done(a):
    job = t.load_job(a.job)
    require_status(job, "grilling")
    t.require_filled(os.path.join(t.job_dir(a.job), "grill-notes.md"), "grill notes")
    t.quote_from_user(a.quote, job["created"])
    job["status"], job["grill_confirmed"] = "spec", {"at": t.now(), "quote": a.quote}
    t.save_job(a.job, job)
    d = t.job_dir(a.job)
    copy_template("spec.md", os.path.join(d, "spec.md"), JOB=a.job, TITLE=job["title"], KIND=job["kind"])
    copy_template("decisions.md", os.path.join(d, "decisions.md"), JOB=a.job)
    t.log_row(a.job, "lead", "grill-done", a.quote)
    print(f"spec template: {d}/spec.md")


def cmd_add_task(a):
    job = t.load_job(a.job)
    require_status(job, "spec")
    if a.owner not in t.IMPLEMENTERS:
        raise t.GateError(f"owner must be one of {', '.join(t.IMPLEMENTERS)}")
    acs = [x.strip() for x in a.ac.split(",") if x.strip()]
    if not acs or any(not re.fullmatch(r"AC-\d+", x) for x in acs):
        raise t.GateError("--ac needs spec ids such as AC-1,AC-2")
    scope = [x.strip() for x in a.scope.split(",") if x.strip()]
    if not scope:
        raise t.GateError("--scope needs at least one path or glob")
    verify = [x.strip() for x in a.verify.split(",") if x.strip()]
    if not verify or any(v not in t.VERIFY_KINDS for v in verify):
        raise t.GateError(f"--verify needs one or more of {', '.join(t.VERIFY_KINDS)}")
    for tid in t.task_ids(a.job):
        other = t.load_task(a.job, tid)
        overlap = [g for g in scope if g in other["scope"]]
        if overlap:
            raise t.GateError(f"scope {overlap} is already owned by {tid}; two tasks never write the same path")
    task_id = f"T-{len(t.task_ids(a.job)) + 1:02d}"
    task = {"id": task_id, "title": a.title, "owner": a.owner, "acs": acs, "scope": scope, "verify": verify,
            "status": "todo", "round": 0, "history": []}
    t.save_task(a.job, task)
    copy_template("task.md", os.path.join(t.job_dir(a.job), "tasks", f"{task_id}.md"), JOB=a.job, TASK=task_id,
                  TITLE=a.title, OWNER=a.owner, ACS=", ".join(acs), SCOPE=", ".join(scope), VERIFY=", ".join(verify))
    t.log_row(a.job, "lead", "add-task", f"{task_id} {a.owner} {','.join(acs)}")
    print(f"{task_id}: {t.job_dir(a.job)}/tasks/{task_id}.md")


def cmd_approve(a):
    job = t.load_job(a.job)
    require_status(job, "spec")
    d = t.job_dir(a.job)
    spec = t.require_filled(os.path.join(d, "spec.md"), "spec")
    acs = t.ac_ids(spec)
    if not acs:
        raise t.GateError("the spec has no acceptance criteria (AC-1, AC-2, ...)")
    tasks = [t.load_task(a.job, tid) for tid in t.task_ids(a.job)]
    if not tasks:
        raise t.GateError("the job has no tasks; add them with job.py add-task")
    covered = {ac for task in tasks for ac in task["acs"]}
    missing = [ac for ac in acs if ac not in covered]
    unknown = sorted(covered - set(acs))
    if missing:
        raise t.GateError(f"no task covers {', '.join(missing)}")
    if unknown:
        raise t.GateError(f"tasks name criteria the spec does not have: {', '.join(unknown)}")
    for task in tasks:
        t.require_filled(os.path.join(d, "tasks", f"{task['id']}.md"), f"task {task['id']}")
    if job["api"] and not any("bruno" in task["verify"] for task in tasks):
        raise t.GateError("this is an API job; at least one task must be verified with bruno")
    t.quote_from_user(a.quote, job["grill_confirmed"]["at"])
    job["status"], job["approved"] = "approved", {"at": t.now(), "quote": a.quote}
    t.save_job(a.job, job)
    t.log_row(a.job, "lead", "approve G1", a.quote)
    print(f"G1 approved: {len(acs)} criteria, {len(tasks)} tasks")


def cmd_decide(a):
    job = t.load_job(a.job)
    if not re.fullmatch(r"D-\d+", a.decision):
        raise t.GateError("decision id looks like D-1")
    d = t.job_dir(a.job)
    request = os.path.join(d, "decisions", f"{a.decision}.md")
    t.require_filled(request, f"decision request {a.decision}")
    t.quote_from_user(a.quote, job["created"])
    with open(os.path.join(d, "decisions.md"), "a", encoding="utf-8") as f:
        f.write(f"\n## {a.decision}\n\n- **Request:** decisions/{a.decision}.md\n- **Decided:** {t.now()}\n"
                f"- **User's words:** \"{a.quote}\"\n")
    t.log_row(a.job, "lead", "decide", f"{a.decision}: {a.quote}")
    print(f"{a.decision} recorded")


def cmd_set_worktree(a):
    job = t.load_job(a.job)
    require_status(job, "approved")
    if a.branch != f"job/{a.job}":
        raise t.GateError(f"branch must be job/{a.job}")
    path = os.path.abspath(a.path)
    if t.git(path, "rev-parse", "--abbrev-ref", "HEAD") != a.branch:
        raise t.GateError(f"{path} is not on branch {a.branch}")
    job.update(worktree=path, branch=a.branch, base=t.git(path, "rev-parse", "HEAD"))
    t.save_job(a.job, job)
    t.log_row(a.job, "git", "set-worktree", f"{path} {a.branch} base {job['base']}")
    print(f"worktree {path} on {a.branch}, base {job['base'][:12]}")


def cmd_status(a):
    job = t.load_job(a.job)
    print(f"{job['id']}  {job['kind']}  {job['status']}  {job['title']}")
    if job.get("worktree"):
        print(f"worktree {job['worktree']}  branch {job['branch']}")
    for tid in t.task_ids(a.job):
        task = t.load_task(a.job, tid)
        print(f"  {tid}  {task['status']:<12} round {task['round']}  {task['owner']:<9} "
              f"{','.join(task['acs']):<12} {task['title']}" + (f"  commit {task['commit'][:12]}" if task.get("commit") else ""))


def cmd_done(a):
    job = t.load_job(a.job)
    require_status(job, "approved")
    open_tasks = [tid for tid in t.task_ids(a.job) if t.load_task(a.job, tid)["status"] != "committed"]
    if open_tasks:
        raise t.GateError(f"tasks not committed yet: {', '.join(open_tasks)}")
    job["status"], job["done"] = "done", t.now()
    t.save_job(a.job, job)
    t.log_row(a.job, "git", "done", "")
    print(f"{a.job} done")


NEXT = {
    "todo": ("{owner}", "pick it up with task.py in_progress{budget}"),
    "in_progress": ("{owner}", "finish it, or restart it from the task file if the old teammate is gone"),
    "implemented": ("git, then spec-reviewer", "stage the task's files, send the tree id, review against the spec"),
    "spec_ok": ("qa", "verify on the reviewed tree"),
    "verified": ("qa, then git", "final run and test report once every task is verified, then commit"),
    "committed": ("nobody", "done"),
}
NEXT_ROLES = {"implemented": ["git", "spec-reviewer"], "spec_ok": ["qa"], "verified": ["qa", "git"]}
JOB_NEXT = {
    "grilling": "lead: reread grill-notes.md and continue the grill until the user confirms",
    "spec": "lead: finish spec.md and the tasks, then ask the user for G1",
    "approved": "the team: continue the run below (.agents/workflows/_run.md)",
    "done": "lead: offer the user a retro (job.py retro)",
}


def open_decisions(job_id):
    d = t.job_dir(job_id)
    path = os.path.join(d, "decisions.md")
    recorded = t.read_text(path) if os.path.exists(path) else ""
    return [f[:-3] for f in sorted(os.listdir(os.path.join(d, "decisions")))
            if re.fullmatch(r"D-\d+\.md", f) and f"## {f[:-3]}\n" not in recorded]


def cmd_resume(a):
    """Everything a fresh lead needs to pick the job up, read from disk, never from memory."""
    job = t.load_job(a.job)
    d = t.job_dir(a.job)
    print(f"# Resume {a.job}: {job['title']} ({job['kind']})\n")
    print(f"Job status: {job['status']}. Next: {JOB_NEXT[job['status']]}.")
    wt = job.get("worktree")
    if wt and os.path.isdir(wt):
        unstaged = t.git(wt, "diff", "--name-only", check=False).splitlines()
        untracked = t.git(wt, "ls-files", "--others", "--exclude-standard", check=False).splitlines()
        print(f"Worktree: {wt} on {t.git(wt, 'rev-parse', '--abbrev-ref', 'HEAD', check=False)}, "
              f"index tree {t.git(wt, 'write-tree', check=False)[:12]}, "
              f"{len(unstaged)} unstaged, {len(untracked)} untracked")
    elif wt:
        print(f"Worktree: {wt} is missing. git must recreate it on job/{a.job} before anyone continues.")
    roles, half_done = set(), []
    print("\n| Task | Status | Round | Owner | Who acts next | What |\n|---|---|---|---|---|---|")
    for tid in t.task_ids(a.job):
        task = t.load_task(a.job, tid)
        who, what = NEXT[task["status"]]
        budget = f" (round {task['round'] + 1} needs a user decision)" if task["round"] + 1 > t.MAX_ROUNDS else ""
        print(f"| {tid} | {task['status']} | {task['round']} | {task['owner']} | "
              f"{who.format(owner=task['owner'])} | {what.format(budget=budget)} |")
        if task["status"] in ("todo", "in_progress"):
            roles.add(task["owner"])
        if task["status"] == "in_progress" and wt and os.path.isdir(wt):
            dirty = t.git(wt, "diff", "--name-only", check=False).splitlines()
            dirty += t.git(wt, "ls-files", "--others", "--exclude-standard", check=False).splitlines()
            mine = [p for p in dirty if t.matches_any(p, task["scope"])]
            if mine:
                half_done.append(f"{tid}: {', '.join(mine[:5])}")
        roles.update(NEXT_ROLES.get(task["status"], []))
    if half_done:
        print("\nUnfinished edits from before the stop (possibly half written). The new owner reads "
              "`git diff` and finishes or reverts them before anything else:")
        for line in half_done:
            print(f"  {line}")
    if job["status"] == "approved" and roles:
        roles |= {"spec-reviewer", "qa", "git"}
        print(f"\nSpawn fresh teammates: {', '.join(sorted(roles))}. Give each its task files and this output.")
        print("Do not redo a task that is spec_ok or verified; task.py refuses if its files changed since.")
    pending = open_decisions(a.job)
    if pending:
        print(f"\nWaiting for the user: {', '.join(pending)} (in {d}/decisions/). Dependent work waits.")
    log = os.path.join(d, "log.tsv")
    print("\nLast log rows:")
    for line in (t.read_text(log).splitlines()[-5:] if os.path.exists(log) else []):
        print(f"  {line}")


def cmd_retro(a):
    job = t.load_job(a.job)
    require_status(job, "done")
    path = os.path.join(t.job_dir(a.job), "retro.md")
    if os.path.exists(path):
        raise t.GateError(f"{path} already exists")
    copy_template("retro.md", path, JOB=a.job, TITLE=job["title"])
    t.log_row(a.job, "lead", "retro", "started")
    print(path)


def cmd_retro_approve(a):
    job = t.load_job(a.job)
    require_status(job, "done")
    if not re.fullmatch(r"R-\d+", a.row):
        raise t.GateError("row id looks like R-1")
    d = t.job_dir(a.job)
    retro = t.require_filled(os.path.join(d, "retro.md"), "retro")
    if not re.search(rf"^\|\s*{a.row}\s*\|", retro, re.M):
        raise t.GateError(f"retro.md has no row {a.row}")
    t.quote_from_user(a.quote, job["done"])
    with open(os.path.join(d, "retro-approvals.md"), "a", encoding="utf-8") as f:
        f.write(f"- {a.row} approved {t.now()}: \"{a.quote}\"\n")
    t.log_row(a.job, "lead", "retro-approve", f"{a.row}: {a.quote}")
    print(f"{a.row} approved; apply only this row, then run the tests")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new"); s.add_argument("kind"); s.add_argument("title"); s.add_argument("--api", action="store_true")
    s = sub.add_parser("grill-done"); s.add_argument("job"); s.add_argument("--quote", required=True)
    s = sub.add_parser("add-task"); s.add_argument("job")
    for opt in ("--owner", "--title", "--ac", "--scope", "--verify"):
        s.add_argument(opt, required=True)
    s = sub.add_parser("approve"); s.add_argument("job"); s.add_argument("--quote", required=True)
    s = sub.add_parser("decide"); s.add_argument("job"); s.add_argument("decision"); s.add_argument("--quote", required=True)
    s = sub.add_parser("set-worktree"); s.add_argument("job"); s.add_argument("--path", required=True); s.add_argument("--branch", required=True)
    s = sub.add_parser("status"); s.add_argument("job")
    s = sub.add_parser("done"); s.add_argument("job")
    s = sub.add_parser("resume"); s.add_argument("job")
    s = sub.add_parser("retro"); s.add_argument("job")
    s = sub.add_parser("retro-approve"); s.add_argument("job"); s.add_argument("row"); s.add_argument("--quote", required=True)
    a = p.parse_args(argv)
    try:
        globals()["cmd_" + a.cmd.replace("-", "_")](a)
    except t.GateError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
