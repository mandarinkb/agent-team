"""Behavior tests for the two hooks. Each hook runs as a subprocess with real hook JSON on stdin.

    python3 tests/test_hooks.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(KIT, ".agents", "scripts", "hooks", "guard_git.py")
GATE = os.path.join(KIT, ".agents", "scripts", "hooks", "gate_reports.py")
TEMPLATE = os.path.join(KIT, ".agents", "templates", "test-report.md")
REVIEW_TEMPLATE = os.path.join(KIT, ".agents", "templates", "review-report.md")


def run(script, payload, env=None):
    proc = subprocess.run([sys.executable, script], input=json.dumps(payload), capture_output=True,
                          text=True, env={**os.environ, **(env or {})})
    return proc.returncode, proc.stdout, proc.stderr


def guard(command):
    code, out, _ = run(GUARD, {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                               "tool_input": {"command": command}})
    assert code == 0
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else "pass"


class GuardGitTest(unittest.TestCase):
    def test_commit_asks_the_user_in_every_spelling(self):
        for cmd in ['git commit -m "fix(orders): keep empty list"',
                    "git -C . commit -m x",
                    "git -c user.name=a commit -am x",
                    "npm test && git commit -m x",
                    'bash -c "git status; git commit -m x"',
                    "GIT_AUTHOR_NAME=x git commit -m y"]:
            self.assertEqual(guard(cmd), "ask", cmd)

    def test_push_and_pr_create_ask(self):
        self.assertEqual(guard("git push origin fix/orders"), "ask")
        self.assertEqual(guard("gh pr create --base main"), "ask")

    def test_destructive_commands_are_denied(self):
        for cmd in ["git push --force origin main", "git push -f", "git push origin +main",
                    "git push --force-with-lease", "git push origin :old-branch", "git push -d origin x",
                    "git reset --hard HEAD~1", "git clean -fd", "git clean -xdf", "git branch -D feature",
                    "gh pr merge 12", "git commit --no-verify -m x", "git commit -nm x",
                    "git status && git reset --hard"]:
            self.assertEqual(guard(cmd), "deny", cmd)

    def test_read_only_and_normal_work_pass_through(self):
        for cmd in ["git status", "git diff --cached --stat", "git log --oneline -5", "git add internal/orders",
                    "git switch -c fix/orders", "git worktree add ../wt fix/orders", "go test ./...",
                    "echo 'git commit is approved by the user'", "git branch -d merged-branch"]:
            self.assertEqual(guard(cmd), "pass", cmd)

    def test_other_tools_are_ignored(self):
        code, out, _ = run(GUARD, {"tool_name": "Edit", "tool_input": {"file_path": "x"}})
        self.assertEqual((code, out), (0, ""))


class GateReportsTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.task = "T-20261009-orders"
        self.dir = os.path.join(self.root, ".agents", "work", self.task)
        os.makedirs(self.dir)

    def complete(self, subject):
        return run(GATE, {"hook_event_name": "TaskCompleted", "task_id": "1", "task_subject": subject,
                          "cwd": self.root}, env={"CLAUDE_PROJECT_DIR": self.root})

    def write_report(self, text):
        with open(os.path.join(self.dir, "test-report.md"), "w", encoding="utf-8") as f:
            f.write(text)

    def filled_report(self, verdict="PASS", revision="3f2a9c1", round_no=1):
        text = open(TEMPLATE, encoding="utf-8").read()
        text = text.replace("<fill: PASS | ISSUES | BLOCKED | INCONCLUSIVE>", verdict)
        text = text.replace("<fill: tree id จาก git write-tree ที่ git ส่งมา>", revision)
        text = re.sub(r"<fill: 1, 2 หรือ 3[^>]*>", str(round_no), text)
        return re.sub(r"<fill(?::[^>]*)?>", "done", text)

    def test_non_verify_tasks_pass(self):
        self.assertEqual(self.complete(f"[{self.task}] implement: port handler")[0], 0)
        self.assertEqual(self.complete("Write the onboarding doc")[0], 0)

    def test_verify_without_report_is_blocked(self):
        code, _, err = self.complete(f"[{self.task}] verify: parity and regression")
        self.assertEqual(code, 2)
        self.assertIn("missing", err)

    def test_unfilled_template_is_blocked(self):
        self.write_report(open(TEMPLATE, encoding="utf-8").read())
        code, _, err = self.complete(f"[{self.task}] verify: parity")
        self.assertEqual(code, 2)
        self.assertIn("placeholder", err)

    def test_filled_report_completes(self):
        self.write_report(self.filled_report())
        self.assertEqual(self.complete(f"[{self.task}] Verify: parity")[0], 0)

    def test_inconclusive_is_a_valid_verdict_to_report(self):
        self.write_report(self.filled_report(verdict="INCONCLUSIVE"))
        self.assertEqual(self.complete(f"[{self.task}] verify: parity")[0], 0)

    def test_bad_verdict_or_revision_is_blocked(self):
        self.write_report(self.filled_report(verdict="LOOKS GOOD"))
        code, _, err = self.complete(f"[{self.task}] verify: x")
        self.assertEqual(code, 2)
        self.assertIn("Verdict", err)
        self.write_report(self.filled_report(revision="latest"))
        code, _, err = self.complete(f"[{self.task}] verify: x")
        self.assertEqual(code, 2)
        self.assertIn("Revision", err)


    def filled_review(self, verdict="FINDINGS", revision="3f2a9c1", lead_done=False):
        text = open(REVIEW_TEMPLATE, encoding="utf-8").read()
        text = text.replace("<fill: NO_FINDINGS | FINDINGS | BLOCKED>", verdict)
        text = re.sub(r"<fill: tree id[^>]*>", revision, text)
        text = re.sub(r"<fill: 1, 2 หรือ 3[^>]*>", "1", text)
        text = re.sub(r"<fill(?::[^>]*)?>", "done", text)
        if lead_done:
            text = re.sub(r"<lead(?::[^>]*)?>", "ไม่มี", text)
        return text

    def write_review(self, text):
        with open(os.path.join(self.dir, "review-report.md"), "w", encoding="utf-8") as f:
            f.write(text)

    def test_review_without_report_is_blocked(self):
        code, _, err = self.complete(f"[{self.task}] review: staged change")
        self.assertEqual(code, 2)
        self.assertIn("review-report.md", err)

    def test_reviewer_part_done_completes_even_before_lead_triage(self):
        self.write_review(self.filled_review())
        self.assertEqual(self.complete(f"[{self.task}] review: staged change")[0], 0)

    def test_review_verdict_must_be_a_review_verdict(self):
        self.write_review(self.filled_review(verdict="PASS"))
        code, _, err = self.complete(f"[{self.task}] review: x")
        self.assertEqual(code, 2)
        self.assertIn("NO_FINDINGS", err)


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout.strip()


class CommitGateTest(unittest.TestCase):
    """guard_git.py on `git commit` with a Task line checks the reports and the staged tree."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.repo = os.path.join(self.root, "wt")
        os.makedirs(self.repo)
        git(self.repo, "init", "-q")
        with open(os.path.join(self.repo, "handler.go"), "w") as f:
            f.write("package orders\n")
        git(self.repo, "add", "handler.go")
        self.tree = git(self.repo, "write-tree")
        self.task = "T-20261009-orders"
        self.dir = os.path.join(self.root, ".agents", "work", self.task)
        os.makedirs(self.dir)
        reports = GateReportsTest()
        reports.dir = self.dir
        self.reports = reports

    def commit(self, command):
        code, out, _ = run(GUARD, {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": self.root},
                           env={"CLAUDE_PROJECT_DIR": self.root})
        self.assertEqual(code, 0)
        decision = json.loads(out)["hookSpecificOutput"]
        return decision["permissionDecision"], decision["permissionDecisionReason"]

    def msg(self):
        return f'git -C wt commit -m "fix(orders): keep empty list" -m "Task: {self.task}"'

    def write(self, name, text):
        with open(os.path.join(self.dir, name), "w", encoding="utf-8") as f:
            f.write(text)

    def test_missing_test_report_denies(self):
        decision, reason = self.commit(self.msg())
        self.assertEqual(decision, "deny")
        self.assertIn("no test-report.md", reason)

    def test_unfinished_test_report_denies(self):
        self.write("test-report.md", open(TEMPLATE, encoding="utf-8").read())
        self.assertEqual(self.commit(self.msg())[0], "deny")

    def test_unfinished_lead_triage_denies(self):
        self.write("test-report.md", self.reports.filled_report(revision=self.tree))
        self.write("review-report.md", self.reports.filled_review(revision=self.tree))
        decision, reason = self.commit(self.msg())
        self.assertEqual(decision, "deny")
        self.assertIn("lead triage", reason)

    def test_matching_reports_ask_with_confirmation(self):
        self.write("test-report.md", self.reports.filled_report(revision=self.tree))
        self.write("review-report.md", self.reports.filled_review(revision=self.tree, lead_done=True))
        decision, reason = self.commit(self.msg())
        self.assertEqual(decision, "ask")
        self.assertIn("matches the reports", reason)
        self.assertIn("Test report: PASS", reason)

    def test_changed_staged_content_asks_with_warning(self):
        self.write("test-report.md", self.reports.filled_report(revision=self.tree))
        self.write("review-report.md", self.reports.filled_review(revision=self.tree, lead_done=True))
        with open(os.path.join(self.repo, "handler.go"), "a") as f:
            f.write("// changed after review\n")
        git(self.repo, "add", "handler.go")
        decision, reason = self.commit(self.msg())
        self.assertEqual(decision, "ask")
        self.assertIn("WARNING", reason)
        self.assertIn("differs from what qa tested", reason)
        self.assertIn("differs from what the reviewer reviewed", reason)

    def test_heredoc_message_and_cd_are_understood(self):
        self.write("test-report.md", self.reports.filled_report(revision=self.tree))
        command = ("cd wt && git commit -m \"$(cat <<'EOF'\nfix(orders): keep empty list; really\n\n"
                   f"Task: {self.task}\nEOF\n)\"")
        decision, reason = self.commit(command)
        self.assertEqual(decision, "ask")
        self.assertIn("Review: no review report.", reason)
        self.assertIn("matches the reports", reason)

    def test_without_task_line_it_still_asks(self):
        decision, reason = self.commit('git -C wt commit -m "chore: tidy"')
        self.assertEqual(decision, "ask")
        self.assertIn("no 'Task: <task-id>' line", reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)
