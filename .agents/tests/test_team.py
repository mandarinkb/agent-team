#!/usr/bin/env python3
"""Tests for the team's scripts and hooks. Every gate has a case that must trip it.

    python3 .agents/tests/test_team.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

AGENTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(AGENTS, "scripts")
HOOKS = os.path.join(SCRIPTS, "hooks")
sys.path.insert(0, HOOKS)
sys.path.insert(0, SCRIPTS)
from guard_sql import check_sql  # noqa: E402


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=True).stdout.strip()


class Env:
    """A throwaway team root with the real templates, and a project repo with a job worktree."""

    def __init__(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, "team")
        shutil.copytree(os.path.join(AGENTS, "templates"), os.path.join(self.root, ".agents", "templates"))
        self.env = dict(os.environ, TEAM_ROOT=self.root)
        self.env.pop("TEAM_IDENTITY", None)
        self.project = os.path.join(self.tmp, "project")
        os.makedirs(self.project)
        git(self.project, "init", "-q", "-b", "main")
        git(self.project, "config", "user.email", "t@example.com")
        git(self.project, "config", "user.name", "t")
        open(os.path.join(self.project, "README"), "w").write("x\n")
        git(self.project, "add", "README")
        git(self.project, "commit", "-qm", "init")

    def run(self, script, *args):
        return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args],
                              capture_output=True, text=True, env=self.env)

    def hook(self, name, event, env=None):
        p = subprocess.run([sys.executable, os.path.join(HOOKS, name)], input=json.dumps(event),
                           capture_output=True, text=True, env=env or self.env)
        if not p.stdout.strip():
            return None, ""
        out = json.loads(p.stdout)["hookSpecificOutput"]
        return out["permissionDecision"], out["permissionDecisionReason"]

    def user_says(self, text):
        self.hook("log_user_prompt.py", {"hook_event_name": "UserPromptSubmit", "prompt": text})

    def path(self, job, *parts):
        return os.path.join(self.root, ".agents", "work", job, *parts)

    def fill(self, job, rel, text):
        with open(self.path(job, rel), "w", encoding="utf-8") as f:
            f.write(text)


def filled(path, extra=""):
    text = open(path, encoding="utf-8").read()
    return re.sub(r"<fill[^>\n]*>", "x", text) + extra


class JobFlowTest(unittest.TestCase):
    def setUp(self):
        self.e = Env()

    def tearDown(self):
        shutil.rmtree(self.e.tmp)

    def ok(self, p):
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        return p.stdout

    def refused(self, p, pattern):
        self.assertEqual(p.returncode, 1, f"expected a refusal, got: {p.stdout}")
        self.assertRegex(p.stderr, pattern)

    def task(self, *args):
        return self.e.run("task.py", "set", self.job, *args)

    def stage(self):
        git(self.wt, "add", "-A")
        return git(self.wt, "write-tree")

    def review(self, task, tree, verdict="PASS", acs="AC-1", coverage="PASS"):
        rel = f"reviews/{task}-{tree[:6]}-{verdict}-{coverage.replace('/', '')}.md"
        self.e.fill(self.job, rel, f"- **Task:** {task}\n- **Revision:** {tree}\n- **Verdict:** {verdict}\n"
                                   f"- **Bruno coverage:** {coverage}\n\n{acs} ok\n")
        return rel

    def fix(self, task, n):
        rel = f"fixes/F-{n}.md"
        self.e.fill(self.job, rel, f"- **Task:** {task}\n- **Criteria:** AC-2\n\nwrong\n")
        return rel

    def bruno(self, failed=0, total=2, token=None):
        rel = "evidence/bruno.json"
        results = [{"request": {"headers": {"authorization": f"Bearer {token}"}}}] if token else []
        self.e.fill(self.job, rel, json.dumps([{"iterationIndex": 0, "results": results, "summary": {
            "totalRequests": total, "passedRequests": total - failed, "failedRequests": failed,
            "totalAssertions": 4, "failedAssertions": 0, "totalTests": 0, "failedTests": 0}}]))
        return rel

    def db(self, tree, row="PASS"):
        rel = "evidence/db.md"
        self.e.fill(self.job, rel, f"- **Task:** T-01\n- **Revision:** {tree}\n\n| c | orders | status | = paid | paid | {row} |\n")
        return rel

    def approved_job(self):
        out = self.ok(self.e.run("job.py", "new", "feature", "Orders filter", "--api"))
        self.job = out.splitlines()[0]
        self.e.fill(self.job, "grill-notes.md", filled(self.e.path(self.job, "grill-notes.md")))
        self.e.user_says("ใช่ เข้าใจตรงกันแล้ว")
        self.ok(self.e.run("job.py", "grill-done", self.job, "--quote", "เข้าใจตรงกันแล้ว"))
        self.ok(self.e.run("job.py", "add-task", self.job, "--owner", "backend", "--title", "api", "--ac", "AC-1",
                           "--scope", "src/*", "--verify", "bruno,db"))
        self.ok(self.e.run("job.py", "add-task", self.job, "--owner", "frontend", "--title", "ui", "--ac", "AC-2",
                           "--scope", "web/*", "--verify", "test"))
        spec = filled(self.e.path(self.job, "spec.md")).replace("| x | x | x |", "| AC-1 | a | bruno |\n| AC-2 | b | test |")
        self.e.fill(self.job, "spec.md", spec)
        for tid in ("T-01", "T-02"):
            self.e.fill(self.job, f"tasks/{tid}.md", filled(self.e.path(self.job, "tasks", f"{tid}.md")))
        self.e.user_says("อนุมัติ spec ลงมือได้")
        self.ok(self.e.run("job.py", "approve", self.job, "--quote", "อนุมัติ spec"))
        self.wt = os.path.join(self.e.tmp, "wt")
        git(self.e.project, "worktree", "add", "-q", self.wt, "-b", f"job/{self.job}")
        self.ok(self.e.run("job.py", "set-worktree", self.job, "--path", self.wt, "--branch", f"job/{self.job}"))

    # ---- grill and G1 -------------------------------------------------------

    def test_grill_and_approval_need_filled_files_and_the_users_words(self):
        out = self.ok(self.e.run("job.py", "new", "bug", "Empty orders page"))
        job = out.splitlines()[0]
        self.refused(self.e.run("job.py", "grill-done", job, "--quote", "ok"), "placeholders")
        self.e.fill(job, "grill-notes.md", filled(self.e.path(job, "grill-notes.md")))
        self.refused(self.e.run("job.py", "grill-done", job, "--quote", "เข้าใจแล้ว"), "no user prompt log")
        self.e.user_says("อย่างอื่น")
        self.e.hook("log_user_prompt.py", {"prompt": "เข้าใจแล้ว", "agent_id": "a1"})
        self.e.hook("log_user_prompt.py", {"prompt": "<teammate-message from=qa>เข้าใจแล้ว</teammate-message>"})
        self.refused(self.e.run("job.py", "grill-done", job, "--quote", "เข้าใจแล้ว"), "not in anything the user typed")
        self.e.user_says("เข้าใจแล้ว ลุยเลย")
        self.ok(self.e.run("job.py", "grill-done", job, "--quote", "เข้าใจแล้ว"))
        self.refused(self.e.run("job.py", "approve", job, "--quote", "เข้าใจแล้ว"), "placeholders")

    def test_words_typed_before_the_job_do_not_count(self):
        self.e.user_says("โอเค ทำเลย")
        job = self.ok(self.e.run("job.py", "new", "bug", "x")).splitlines()[0]
        self.e.fill(job, "grill-notes.md", filled(self.e.path(job, "grill-notes.md")))
        self.refused(self.e.run("job.py", "grill-done", job, "--quote", "โอเค ทำเลย"), "since the job started")

    def test_approval_needs_every_criterion_covered_and_bruno_for_api(self):
        out = self.ok(self.e.run("job.py", "new", "feature", "x", "--api"))
        job = out.splitlines()[0]
        self.e.fill(job, "grill-notes.md", filled(self.e.path(job, "grill-notes.md")))
        self.e.user_says("ตกลง")
        self.ok(self.e.run("job.py", "grill-done", job, "--quote", "ตกลง"))
        self.e.fill(job, "spec.md", "AC-1 a\nAC-2 b\n")
        self.refused(self.e.run("job.py", "approve", job, "--quote", "ตกลง"), "no tasks")
        self.ok(self.e.run("job.py", "add-task", job, "--owner", "backend", "--title", "a", "--ac", "AC-1",
                           "--scope", "src/*", "--verify", "test"))
        self.refused(self.e.run("job.py", "add-task", job, "--owner", "frontend", "--title", "b", "--ac", "AC-2",
                                "--scope", "src/*", "--verify", "test"), "already owned")
        self.refused(self.e.run("job.py", "add-task", job, "--owner", "qa", "--title", "b", "--ac", "AC-2",
                                "--scope", "web/*", "--verify", "test"), "owner must be")
        self.e.fill(job, "tasks/T-01.md", "done\n")
        self.refused(self.e.run("job.py", "approve", job, "--quote", "ตกลง"), "no task covers AC-2")
        self.ok(self.e.run("job.py", "add-task", job, "--owner", "frontend", "--title", "b", "--ac", "AC-2",
                           "--scope", "web/*", "--verify", "test"))
        self.e.fill(job, "tasks/T-02.md", "done\n")
        self.refused(self.e.run("job.py", "approve", job, "--quote", "ตกลง"), "verified with bruno")

    # ---- task moves ----------------------------------------------------------

    def write(self, rel, text):
        path = os.path.join(self.wt, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def collection(self, body_assert=True, acs="AC-1", env_token="{{process.env.TOKEN}}"):
        b = f"bruno/{self.job}"
        self.write(f"{b}/bruno.json", '{"version": "1", "name": "t", "type": "collection"}\n')
        self.write(f"{b}/environments/local.bru", f"vars {{\n  baseUrl: http://localhost:8080\n  token: {env_token}\n}}\n")
        extra = "  res.body.items: isArray\n" if body_assert else ""
        self.write(f"{b}/orders/list.bru", f"meta {{\n  name: list\n}}\n\nget {{\n  url: {{{{baseUrl}}}}/orders\n}}\n\n"
                                           f"assert {{\n  res.status: eq 200\n{extra}}}\n\ndocs {{\n  {acs}\n}}\n")

    def fake_bru(self, failed=0):
        script = os.path.join(self.e.tmp, "fake_bru.py")
        with open(script, "w") as f:
            f.write("import json, sys\nout = sys.argv[sys.argv.index('--reporter-json') + 1]\n"
                    f"json.dump([{{'summary': {{'totalRequests': 1, 'passedRequests': {1 - failed}, 'failedRequests': {failed}}}}}],"
                    " open(out, 'w'))\n")
        with open(os.path.join(self.e.root, ".agents", "team.json"), "w") as f:
            json.dump({"bruno_command": [sys.executable, script, "--env", "{env}", "--reporter-json", "{out}"]}, f)

    def test_full_flow_with_every_gate_tripped_once(self):
        self.approved_job()
        self.refused(self.task("T-01", "in_progress", "--by", "frontend"), "only backend")
        self.refused(self.task("T-01", "implemented", "--by", "backend"), "cannot move")
        self.ok(self.task("T-01", "in_progress", "--by", "backend"))
        self.refused(self.task("T-01", "implemented", "--by", "backend"), "no file in this task's scope")
        self.write("src/a.py", "a = 1\n")
        self.ok(self.task("T-01", "implemented", "--by", "backend"))

        # Spec review, including qa's Bruno collection.
        self.refused(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review", "reviews/none.md"), "not found")
        rel = self.review("T-01", "0" * 40)
        self.refused(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review", rel), "untracked")
        tree = self.stage()
        self.refused(self.task("T-01", "spec_ok", "--by", "qa", "--review", rel), "only spec-reviewer")
        self.refused(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review",
                               self.review("T-01", tree, coverage="FAIL")), "Bruno coverage: PASS")
        self.refused(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review", self.review("T-01", tree)),
                     "no Bruno collection")
        self.collection(body_assert=False)
        tree = self.stage()
        self.refused(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review", self.review("T-01", tree)),
                     "asserts only the status")
        self.collection(acs="none")
        tree = self.stage()
        self.refused(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review", self.review("T-01", tree)),
                     "no request names AC-1")
        self.collection(env_token="s3cr3tvalue99")
        tree = self.stage()
        self.refused(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review", self.review("T-01", tree)),
                     "credential variable")
        self.collection()
        stale = self.review("T-01", tree)
        tree = self.stage()
        self.refused(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review", stale), "staged tree is")
        self.refused(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review",
                               self.review("T-01", tree, verdict="FAIL")), "not PASS")
        self.refused(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review",
                               self.review("T-01", tree, acs="")), "does not cover AC-1")
        self.refused(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review", "../../../etc/passwd"),
                     "inside the job directory")
        self.ok(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review", self.review("T-01", tree)))

        # Another task's work landing in the shared index must not block T-01.
        self.write("web/early.js", "e = 1\n")
        tree = self.stage()
        self.refused(self.task("T-01", "verified", "--by", "qa", "--bruno", self.bruno(failed=1), "--db", self.db(tree)),
                     "failed or errored")
        self.refused(self.task("T-01", "verified", "--by", "qa", "--bruno", self.bruno(total=0), "--db", self.db(tree)),
                     "ran no requests")
        self.refused(self.task("T-01", "verified", "--by", "qa", "--bruno", self.bruno(), "--db", self.db(tree, "FAIL")),
                     "FAIL rows")
        self.refused(self.task("T-01", "verified", "--by", "qa", "--bruno", self.bruno(), "--db", self.db("abc")),
                     "expected")
        leaky = self.bruno(token="eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9P")
        self.refused(self.task("T-01", "verified", "--by", "qa", "--bruno", leaky, "--db", self.db(tree)), "JWT")
        red = self.e.run("redact.py", self.e.path(self.job, leaky))
        self.assertIn("1 redacted", red.stdout)

        # Code or Bruno that the review vouched for changes: back to review, same round.
        self.write("src/a.py", "a = 2\n")
        tree2 = self.stage()
        self.refused(self.task("T-01", "verified", "--by", "qa", "--bruno", leaky, "--db", self.db(tree2)),
                     "vouched for changed")
        self.write("src/a.py", "a = 1\n")
        self.write(f"bruno/{self.job}/orders/extra.bru", "get {\n}\n\nassert {\n  res.body.id: isNumber\n}\n\ndocs {\n  AC-1\n}\n")
        tree = self.stage()
        self.refused(self.task("T-01", "verified", "--by", "qa", "--bruno", leaky, "--db", self.db(tree)),
                     "vouched for changed")
        self.refused(self.task("T-01", "implemented", "--by", "qa"), "--note is required")
        self.ok(self.task("T-01", "implemented", "--by", "qa", "--note", "added extra.bru"))
        self.ok(self.task("T-01", "spec_ok", "--by", "spec-reviewer", "--review", self.review("T-01", tree)))
        self.ok(self.task("T-01", "verified", "--by", "qa", "--bruno", leaky, "--db", self.db(tree)))
        self.assertEqual(json.load(open(self.e.path(self.job, "state", "T-01.json")))["round"], 1)

        # T-02 goes around the fix loop until the round budget stops it.
        for n in range(1, 4):
            self.ok(self.task("T-02", "in_progress", "--by", "frontend"))
            self.write("web/b.js", f"b = {n}\n")
            self.ok(self.task("T-02", "implemented", "--by", "frontend"))
            self.refused(self.task("T-02", "todo", "--by", "spec-reviewer"), "--fix is required")
            self.ok(self.task("T-02", "todo", "--by", "spec-reviewer", "--fix", self.fix("T-02", n)))
        self.refused(self.task("T-02", "in_progress", "--by", "frontend"), "exceeds the budget")
        self.refused(self.task("T-02", "in_progress", "--by", "frontend", "--decision", "D-1"), "not recorded")
        self.e.fill(self.job, "decisions/D-1.md", "เลือก A หรือ B\n")
        self.assertIn("Waiting for the user: D-1", self.ok(self.e.run("job.py", "resume", self.job)))
        self.e.user_says("เอาทางเลือก A ทำต่ออีกรอบ")
        self.refused(self.e.run("job.py", "decide", self.job, "D-1", "--quote", "ทางเลือก B"), "not in anything")
        self.ok(self.e.run("job.py", "decide", self.job, "D-1", "--quote", "เอาทางเลือก A"))
        self.ok(self.task("T-02", "in_progress", "--by", "frontend", "--decision", "D-1"))
        resume = self.ok(self.e.run("job.py", "resume", self.job))
        self.assertIn("| T-02 | in_progress | 4 | frontend | frontend |", resume)
        self.assertIn("Spawn fresh teammates: frontend, git, qa, spec-reviewer", resume)
        self.assertNotIn("Waiting for the user", resume)
        self.assertIn("T-02: web/b.js", resume)
        self.ok(self.task("T-02", "implemented", "--by", "frontend"))
        tree = self.stage()
        self.ok(self.task("T-02", "spec_ok", "--by", "spec-reviewer", "--review",
                          self.review("T-02", tree, acs="AC-2", coverage="n/a")))
        log = "evidence/T-02-test.log"
        self.e.fill(self.job, log, "ran tests\n")
        self.refused(self.task("T-02", "verified", "--by", "qa", "--test-log", log), "must start with")
        self.e.fill(self.job, log, f"Revision: {tree}\nok\n")
        self.ok(self.task("T-02", "verified", "--by", "qa", "--test-log", log))

        # Commit gate.
        commit = {"tool_name": "Bash", "cwd": self.wt, "agent_type": "git",
                  "tool_input": {"command": f'git commit -m "feat(orders): filter" -m "Job: {self.job}"'}}
        gate = lambda ev=commit: self.e.hook("guard_git.py", ev)
        decision, reason = gate()
        self.assertEqual((decision, "test report not found" in reason), ("deny", True), reason)
        report = filled(os.path.join(self.e.root, ".agents", "templates", "test-report.md"))
        report = report.replace("- **Verdict:** x", "- **Verdict:** PASS").replace("- **Revision:** x", f"- **Revision:** {tree}")
        self.e.fill(self.job, "test-report.md", report + "| AC-1 | bruno | PASS | e |\n")
        decision, reason = gate()
        self.assertEqual((decision, "no PASS row for AC-2" in reason), ("deny", True), reason)
        self.e.fill(self.job, "test-report.md", report.replace("- **Reset:** x\n", "") +
                    "| AC-1 | bruno | PASS | e |\n| AC-2 | test | PASS | e |\n")
        decision, reason = gate()
        self.assertEqual((decision, "no 'Reset:' line" in reason), ("deny", True), reason)
        full = report + "| AC-1 | bruno | PASS | e |\n| AC-2 | test | PASS | e |\n"
        self.e.fill(self.job, "test-report.md", full + 'token used: "password": "hunter22"\n')
        decision, reason = gate()
        self.assertEqual((decision, "credential field" in reason), ("deny", True), reason)
        self.e.fill(self.job, "test-report.md", full)
        for who in ("qa", "backend"):
            decision, reason = gate(dict(commit, agent_type=who))
            self.assertEqual((decision, "only the git teammate" in reason), ("deny", True), reason)
        self.write("README", "changed\n")
        git(self.wt, "add", "README")
        decision, reason = gate()
        self.assertEqual((decision, "staged tree is" in reason), ("deny", True), reason)
        git(self.wt, "reset", "-q", "HEAD", "README")
        git(self.wt, "checkout", "README")
        decision, reason = gate(dict(commit, tool_input={"command": f'git commit -a -m "Job: {self.job}"'}))
        self.assertEqual(decision, "deny")
        with open(os.path.join(self.e.root, ".agents", "team.json"), "w") as f:
            json.dump({"bruno_command": ["no-such-bru-binary", "run"]}, f)
        decision, reason = gate()
        self.assertEqual((decision, "not installed" in reason), ("deny", True), reason)
        self.fake_bru(failed=1)
        decision, reason = gate()
        self.assertEqual((decision, "failed or errored" in reason), ("deny", True), reason)
        self.fake_bru()
        decision, reason = gate()
        self.assertEqual(decision, "allow", reason)
        self.assertIn("fresh Bruno run 1/1", reason)

        git(self.wt, "commit", "-qm", f"feat: x\n\nJob: {self.job}")
        sha = git(self.wt, "rev-parse", "HEAD")
        self.refused(self.task("T-01", "committed", "--by", "git", "--sha", git(self.wt, "rev-parse", "HEAD~1")),
                     "differs from the revision")
        self.refused(self.e.run("job.py", "retro", self.job), "needs done")
        for tid in ("T-01", "T-02"):
            self.ok(self.task(tid, "committed", "--by", "git", "--sha", sha))
        self.ok(self.e.run("job.py", "done", self.job))
        self.assertIn(sha[:12], self.ok(self.e.run("job.py", "status", self.job)))
        log = open(self.e.path(self.job, "log.tsv"), encoding="utf-8").read()
        self.assertIn("T-02 todo->in_progress", log)

        # Retro: only rows the user approved, in their words, after the job ended.
        self.ok(self.e.run("job.py", "retro", self.job))
        self.refused(self.e.run("job.py", "retro-approve", self.job, "R-1", "--quote", "ok"), "placeholders")
        retro = filled(self.e.path(self.job, "retro.md")).replace("| x | x | x | x | x |", "| R-1 | a | b | c | gate |")
        self.e.fill(self.job, "retro.md", retro)
        self.refused(self.e.run("job.py", "retro-approve", self.job, "R-2", "--quote", "ok"), "no row R-2")
        self.refused(self.e.run("job.py", "retro-approve", self.job, "R-1", "--quote", "เอาทางเลือก A"), "not in anything")
        self.e.user_says("อนุมัติ R-1 ครับ")
        self.ok(self.e.run("job.py", "retro-approve", self.job, "R-1", "--quote", "อนุมัติ R-1"))
        self.assertIn("R-1 approved", open(self.e.path(self.job, "retro-approvals.md"), encoding="utf-8").read())

class GitGuardTest(unittest.TestCase):
    def setUp(self):
        self.e = Env()

    def tearDown(self):
        shutil.rmtree(self.e.tmp)

    def decide(self, command, agent_type=None):
        event = {"tool_name": "Bash", "cwd": self.e.project, "tool_input": {"command": command}}
        if agent_type:
            event.update(agent_type=agent_type, agent_id="x")
        return self.e.hook("guard_git.py", event)[0]

    def test_push_and_destruction_are_denied_in_every_form(self):
        for cmd in ("git push", "git push origin main", "git -C . push", "cd x && git push -f",
                    "bash -c 'git push'", "sh -c \"git -c a=b push\"", "eval git push",
                    "git reset --hard HEAD~1", "git clean -fd", "git branch -D x", "git commit --no-verify -m x",
                    "git filter-branch", "gh pr create", "gh pr merge 3"):
            self.assertEqual(self.decide(cmd, "git"), "deny", cmd)
            self.assertEqual(self.decide(cmd), "deny", cmd)

    def test_ordinary_commands_pass_through(self):
        for cmd in ("git status", "git log --oneline", "git add src/a.py", "git diff --cached", "ls", "git write-tree"):
            self.assertIsNone(self.decide(cmd, "git"), cmd)

    def test_commit_without_job_asks_the_lead_and_denies_teammates(self):
        self.assertEqual(self.decide('git commit -m "chore: x"'), "ask")
        self.assertEqual(self.decide('git commit -m "chore: x"', "git"), "deny")


class TaskGuardTest(unittest.TestCase):
    def setUp(self):
        self.e = Env()

    def tearDown(self):
        shutil.rmtree(self.e.tmp)

    def bash(self, command, agent_type=None, agent_id=None, env=None):
        event = {"tool_name": "Bash", "tool_input": {"command": command}}
        if agent_type:
            event["agent_type"] = agent_type
        if agent_id or agent_type:
            event["agent_id"] = agent_id or "a1"
        return self.e.hook("guard_task.py", event, env)[0]

    def edit(self, path, agent_type=None):
        event = {"tool_name": "Edit", "tool_input": {"file_path": path}}
        if agent_type:
            event.update(agent_type=agent_type, agent_id="a1")
        return self.e.hook("guard_task.py", event)[0]

    def test_by_must_be_the_agent_running_it(self):
        cmd = "python3 /r/.agents/scripts/task.py set J-20261017-x T-01 verified --by qa"
        self.assertIsNone(self.bash(cmd, "qa"))
        self.assertIsNone(self.bash(cmd, "pstack:qa"))
        self.assertEqual(self.bash(cmd, "backend"), "deny")
        self.assertEqual(self.bash(cmd), "deny")
        self.assertEqual(self.bash(cmd, agent_id="a9"), "deny")
        self.assertIsNone(self.bash(cmd, agent_id="a9", env=dict(self.e.env, TEAM_IDENTITY="lenient")))

    def test_job_steps_belong_to_their_role(self):
        self.assertIsNone(self.bash("python3 .agents/scripts/job.py approve J-20261017-x --quote ok"))
        self.assertEqual(self.bash("python3 .agents/scripts/job.py approve J-20261017-x --quote ok", "qa"), "deny")
        self.assertEqual(self.bash("python3 .agents/scripts/job.py set-worktree J --path a --branch b"), "deny")
        self.assertIsNone(self.bash("python3 .agents/scripts/job.py set-worktree J --path a --branch b", "git"))
        self.assertIsNone(self.bash("python3 .agents/scripts/job.py status J", "backend"))

    def test_state_and_gates_are_protected(self):
        self.assertEqual(self.edit("/r/.agents/work/J-1/state/T-01.json"), "deny")
        self.assertEqual(self.edit("/r/.agents/work/J-1/job.json", "qa"), "deny")
        self.assertEqual(self.edit("/r/.agents/work/.user-prompts.jsonl"), "deny")
        self.assertEqual(self.edit("/r/.agents/scripts/task.py", "backend"), "deny")
        self.assertEqual(self.edit("/r/.claude/settings.json", "qa"), "deny")
        self.assertIsNone(self.edit("/r/.agents/scripts/task.py"))
        self.assertIsNone(self.edit("/r/.agents/work/J-1/reviews/T-01-r1.md", "spec-reviewer"))
        self.assertEqual(self.bash("echo '{}' > .agents/work/J-1/state/T-01.json", "qa"), "deny")
        self.assertEqual(self.bash("sed -i '' s/a/b/ .agents/scripts/teamlib.py", "backend"), "deny")
        self.assertIsNone(self.bash("cat .agents/work/J-1/state/T-01.json", "qa"))
        self.assertIsNone(self.bash("ls .agents/work/ 2>/dev/null; cat .agents/work/.user-prompts.jsonl 2>&1", "qa"))


class InstallTest(unittest.TestCase):
    def test_installed_project_keeps_its_own_work_and_user_log(self):
        tmp = tempfile.mkdtemp()
        try:
            project = os.path.join(tmp, "app")
            os.makedirs(project)
            env = {k: v for k, v in os.environ.items() if k != "TEAM_ROOT"}
            out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "install.py"), project],
                                 capture_output=True, text=True, env=env)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertTrue(os.path.islink(os.path.join(project, ".agents", "scripts")))
            self.assertTrue(os.path.islink(os.path.join(project, ".claude", "agents")))
            self.assertIn("@../.agents/AGENTS.md", open(os.path.join(project, ".claude", "CLAUDE.md")).read())
            settings = json.load(open(os.path.join(project, ".claude", "settings.json")))
            self.assertIn("Bash(git push *)", settings["permissions"]["deny"])
            linked = os.path.join(project, ".agents", "scripts")
            source_log = os.path.join(AGENTS, "work", ".user-prompts.jsonl")
            before = os.path.getsize(source_log) if os.path.exists(source_log) else 0
            subprocess.run([sys.executable, os.path.join(linked, "hooks", "log_user_prompt.py")],
                           input=json.dumps({"prompt": "install-test"}), text=True, env=env, check=True)
            job = subprocess.run([sys.executable, os.path.join(linked, "job.py"), "new", "bug", "install test"],
                                 capture_output=True, text=True, env=env, cwd=project)
            self.assertEqual(job.returncode, 0, job.stderr)
            work = os.path.join(project, ".agents", "work")
            self.assertTrue(os.path.exists(os.path.join(work, ".user-prompts.jsonl")))
            self.assertTrue(os.path.isdir(os.path.join(work, job.stdout.splitlines()[0])))
            after = os.path.getsize(source_log) if os.path.exists(source_log) else 0
            self.assertEqual(before, after, "the installed project's hook wrote into the source repo's log")
        finally:
            shutil.rmtree(tmp)


class SqlGuardTest(unittest.TestCase):
    ALLOWED = ["SELECT id, updated_at FROM orders WHERE note = 'please delete'", "select * from t;",
               "WITH x AS (SELECT 1) SELECT * FROM x", "(SELECT 1)", "SELECT $tag$ x $tag$",
               "SELECT created_at, deleted_at FROM t -- trailing comment"]
    DENIED = ["DELETE FROM t", "SELECT 1; DELETE FROM t", "SELECT 'a\\'; DELETE FROM t; SELECT '",
              "SELECT 1--1; DELETE FROM t", "WITH d AS (DELETE FROM t RETURNING *) SELECT * FROM d",
              "SELECT * FROM t FOR UPDATE", "SELECT pg_sleep(10)", "SELECT * INTO new_t FROM t",
              "SELECT 1 /*!; DROP TABLE t */", "SELECT $$; drop$$", "EXPLAIN ANALYZE DELETE FROM t",
              "SELECT nextval('s')", "UPDATE t SET a = 1", "INSERT INTO t VALUES (1)", "TRUNCATE t", "",
              "SELECT 'unterminated", "/* SELECT */ DROP TABLE t", "SELECT 1 # ; DELETE FROM t"]

    def test_only_one_read_only_select_passes(self):
        for sql in self.ALLOWED:
            self.assertIsNone(check_sql(sql), sql)
        for sql in self.DENIED:
            self.assertIsNotNone(check_sql(sql), sql)

    def test_hook_reads_mcp_input(self):
        e = Env()
        try:
            ev = {"tool_name": "mcp__postgres__query", "tool_input": {"sql": "DELETE FROM t"}}
            self.assertEqual(e.hook("guard_sql.py", ev)[0], "deny")
            self.assertIsNone(e.hook("guard_sql.py", dict(ev, tool_input={"sql": "SELECT 1"}))[0])
            self.assertIsNone(e.hook("guard_sql.py", {"tool_name": "mcp__github__get_issue", "tool_input": {"id": 1}})[0])
            self.assertEqual(e.hook("guard_sql.py", {"tool_name": "mcp__postgres__execute", "tool_input": {"sql": "SELECT 1"}})[0],
                             "deny")
        finally:
            shutil.rmtree(e.tmp)


class WriteScopeTest(unittest.TestCase):
    """Writes inside a job worktree follow the tasks each role holds."""

    def setUp(self):
        self.e = Env()
        self.job = "J-20261017-scope"
        self.wt = os.path.join(self.e.tmp, "wt")
        os.makedirs(self.wt)
        d = self.e.path(self.job)
        os.makedirs(os.path.join(d, "state"))
        with open(os.path.join(d, "job.json"), "w") as f:
            json.dump({"id": self.job, "status": "approved", "worktree": self.wt}, f)
        for tid, owner, status, scope in (("T-01", "backend", "in_progress", ["src/*"]),
                                          ("T-02", "frontend", "todo", ["web/*"])):
            with open(os.path.join(d, "state", f"{tid}.json"), "w") as f:
                json.dump({"id": tid, "owner": owner, "status": status, "scope": scope}, f)

    def tearDown(self):
        shutil.rmtree(self.e.tmp)

    def edit(self, rel, agent_type=None, env=None):
        event = {"tool_name": "Write", "tool_input": {"file_path": os.path.join(self.wt, rel)}}
        if agent_type:
            event.update(agent_type=agent_type, agent_id="a1")
        return self.e.hook("guard_task.py", event, env)[0]

    def test_each_role_writes_only_what_it_holds(self):
        self.assertIsNone(self.edit("src/orders/handler.go", "backend"))
        self.assertEqual(self.edit("web/app.js", "backend"), "deny")
        self.assertEqual(self.edit("web/app.js", "frontend"), "deny")  # T-02 is not in progress
        self.assertIsNone(self.edit(f"bruno/{self.job}/orders/list.bru", "qa"))
        self.assertEqual(self.edit("src/a.go", "qa"), "deny")
        self.assertEqual(self.edit("bruno/other-job/x.bru", "qa"), "deny")
        for role in ("spec-reviewer", "analyst", "git"):
            self.assertEqual(self.edit("src/a.go", role), "deny", role)
        self.assertEqual(self.edit("src/a.go"), "deny")  # the lead never writes code
        unidentified = {"tool_name": "Write", "agent_id": "x", "tool_input": {"file_path": os.path.join(self.wt, "src/a.go")}}
        self.assertEqual(self.e.hook("guard_task.py", unidentified)[0], "deny")
        outside = {"tool_name": "Write", "agent_type": "backend", "agent_id": "a1",
                   "tool_input": {"file_path": os.path.join(self.e.tmp, "elsewhere", "x.py")}}
        self.assertIsNone(self.e.hook("guard_task.py", outside)[0])

    def test_teammates_cannot_change_team_settings(self):
        for path in ("/r/.agents/team.json", "/r/.agents/models.json", "/r/.agents/db-mcp.json"):
            event = {"tool_name": "Edit", "agent_type": "qa", "agent_id": "a1", "tool_input": {"file_path": path}}
            self.assertEqual(self.e.hook("guard_task.py", event)[0], "deny", path)


class HeredocTest(unittest.TestCase):
    def test_data_heredocs_are_not_commands_but_shell_heredocs_are(self):
        e = Env()
        try:
            def bash(command, agent_type="backend"):
                return e.hook("guard_task.py", {"tool_name": "Bash", "agent_type": agent_type, "agent_id": "a1",
                                                "tool_input": {"command": command}})[0]
            doc = "cat > notes.md <<'EOF'\nthen `task.py set J T-01 verified --by qa`\nEOF"
            self.assertIsNone(bash(doc))
            self.assertIsNone(bash("python3 - <<'EOF'\nprint('job.py done J')\nEOF"))
            self.assertEqual(bash("cd x && bash <<'EOF'\npython3 .agents/scripts/task.py set J T-01 verified --by qa\nEOF"), "deny")
            self.assertEqual(bash("cd wt; python3 .agents/scripts/task.py set J T-01 verified --by qa"), "deny")
            self.assertIsNone(bash("grep -n task.py README.md"))
        finally:
            shutil.rmtree(e.tmp)


class LoopGuardTest(unittest.TestCase):
    def test_sixth_identical_command_without_progress_is_denied(self):
        e = Env()
        try:
            event = {"tool_name": "Bash", "agent_id": "a1", "cwd": e.project, "tool_input": {"command": "curl -s localhost:1"}}
            results = [e.hook("loop_guard.py", event)[0] for _ in range(6)]
            self.assertEqual(results[:5], [None] * 5)
            self.assertEqual(results[5], "deny")
            with open(os.path.join(e.project, "new.txt"), "w") as f:
                f.write("progress\n")
            self.assertIsNone(e.hook("loop_guard.py", event)[0])
            other = dict(event, agent_id="a2")
            self.assertIsNone(e.hook("loop_guard.py", other)[0])
        finally:
            shutil.rmtree(e.tmp)


class ProbeTest(unittest.TestCase):
    def test_probe_is_silent_by_default_and_reports_missing_agent_type(self):
        e = Env()
        try:
            log = os.path.join(e.root, ".agents", "work", ".identity-probe.jsonl")
            e.hook("probe_identity.py", {"tool_name": "Bash", "agent_id": "a1"})
            self.assertFalse(os.path.exists(log))
            env = dict(e.env, TEAM_PROBE="1")
            e.hook("probe_identity.py", {"tool_name": "Bash", "agent_id": "a1", "agent_type": "qa"}, env)
            report = lambda: subprocess.run([sys.executable, os.path.join(HOOKS, "probe_identity.py"), "--report"],
                                            capture_output=True, text=True, env=e.env)
            self.assertIn("PASS", report().stdout)
            e.hook("probe_identity.py", {"tool_name": "Bash", "agent_id": "a2"}, env)
            r = report()
            self.assertEqual(r.returncode, 1)
            self.assertIn("FAIL", r.stdout)
        finally:
            shutil.rmtree(e.tmp)


class ModelsTest(unittest.TestCase):
    def test_role_files_match_models_json_and_drift_is_caught(self):
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "models.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        tmp = tempfile.mkdtemp()
        try:
            copy = os.path.join(tmp, ".agents")
            for name in ("scripts", "agents", "models.json"):
                src = os.path.join(AGENTS, name)
                (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, os.path.join(copy, name))
            models = os.path.join(copy, "scripts", "models.py")
            run = lambda *a: subprocess.run([sys.executable, models, *a], capture_output=True, text=True)
            self.assertEqual(run("--profile", "economy").returncode, 0)
            self.assertIn("model: sonnet", open(os.path.join(copy, "agents", "analyst.md")).read())
            self.assertIn("model: opus", open(os.path.join(copy, "agents", "qa.md")).read())
            path = os.path.join(copy, "agents", "qa.md")
            with open(path) as f:
                text = f.read()
            with open(path, "w") as f:
                f.write(text.replace("model: opus", "model: haiku"))
            self.assertEqual(run("--check").returncode, 1)
            self.assertEqual(run("--profile", "nope").returncode, 1)
        finally:
            shutil.rmtree(tmp)


class SecretTest(unittest.TestCase):
    def test_find_and_redact(self):
        import teamlib as t
        leaks = ['{"authorization": "Bearer abcdef123456789"}', '{"password": "hunter22"}', "token: s3cr3tvalue99",
                 "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9P",
                 "postgres://app:pa55word@db/x", "AKIAABCDEFGHIJKLMNOP", "-----BEGIN RSA PRIVATE KEY-----"]
        clean = ["token: {{process.env.TOKEN}}", "postgres://app:{{process.env.PW}}@db/x", '{"token_count": 3}',
                 '{"authorization": "Bearer <redacted>"}', "baseUrl: http://localhost:8080"]
        for text in leaks:
            self.assertTrue(t.find_secrets(text), text)
            redacted, n = t.redact_text(text)
            self.assertGreater(n, 0, text)
            self.assertEqual(t.find_secrets(redacted), [], redacted)
        for text in clean:
            self.assertEqual(t.find_secrets(text), [], text)


class LimitGuardTest(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.limits = os.path.join(self.e.root, ".agents", "work", ".rate-limits.json")

    def tearDown(self):
        shutil.rmtree(self.e.tmp)

    def status_line_sends(self, five=None, seven=None, reset_in=3600):
        windows = {}
        for key, used in (("five_hour", five), ("seven_day", seven)):
            if used is not None:
                windows[key] = {"used_percentage": used, "resets_at": int(time.time()) + reset_in}
        data = {"model": {"display_name": "x"}, **({"rate_limits": windows} if windows else {})}
        subprocess.run([sys.executable, os.path.join(HOOKS, "record_limits.py")], input=json.dumps(data),
                       text=True, env=self.e.env, check=True)

    def decide(self, command):
        return self.e.hook("limit_guard.py", {"tool_name": "Bash", "agent_type": "backend", "agent_id": "a1",
                                              "tool_input": {"command": command}})

    def test_no_new_task_at_or_above_the_threshold(self):
        start = "python3 .agents/scripts/task.py set J-20261017-x T-01 in_progress --by backend"
        finish = "python3 .agents/scripts/task.py set J-20261017-x T-01 implemented --by backend"
        self.assertIsNone(self.decide(start)[0])  # no data yet: an API key, or before the first response
        self.status_line_sends()  # no rate_limits field: nothing recorded
        self.assertFalse(os.path.exists(self.limits))
        self.status_line_sends(five=94.9, seven=10)
        self.assertIsNone(self.decide(start)[0])
        self.status_line_sends(five=95, seven=10)
        decision, reason = self.decide(start)
        self.assertEqual(decision, "deny")
        self.assertIn("5-hour window at 95%", reason)
        self.assertIsNone(self.decide(finish)[0])  # finishing the current step is allowed
        self.assertIsNone(self.decide("git status")[0])
        self.status_line_sends(five=20, seven=97)
        self.assertIn("7-day window at 97%", self.decide(start)[1])
        self.status_line_sends(five=99, reset_in=-10)  # the window already reset
        self.assertIsNone(self.decide(start)[0])
        with open(os.path.join(self.e.root, ".agents", "team.json"), "w") as f:
            json.dump({"limit_threshold": 50}, f)
        self.status_line_sends(five=60)
        self.assertEqual(self.decide(start)[0], "deny")

if __name__ == "__main__":
    import warnings
    warnings.simplefilter("ignore", ResourceWarning)
    unittest.main(verbosity=1)
