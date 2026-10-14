"""Tests for loop handling: loop_guard.py, the round budget in gate_reports.py, and team_health.py.

    python3 tests/test_loops.py
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

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(KIT, ".agents", "scripts", "hooks", "loop_guard.py")
GATE = os.path.join(KIT, ".agents", "scripts", "hooks", "gate_reports.py")
TEMPLATE = os.path.join(KIT, ".agents", "templates", "test-report.md")


def run(script, payload, env):
    proc = subprocess.run([sys.executable, script], input=json.dumps(payload), capture_output=True,
                          text=True, env={**os.environ, **env})
    return proc.returncode, proc.stdout, proc.stderr


class LoopGuardTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        subprocess.run(["git", "init", "-q", self.root], check=True)
        self.env = {"CLAUDE_PROJECT_DIR": self.root, "LOOP_GUARD_MAX": "4", "LOOP_GUARD_WINDOW": "600"}

    def call(self, command, agent="agent-qa"):
        code, out, _ = run(GUARD, {"tool_name": "Bash", "tool_input": {"command": command},
                                   "cwd": self.root, "agent_id": agent, "session_id": "s1"}, self.env)
        self.assertEqual(code, 0)
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else "pass"

    def test_same_command_without_progress_is_denied_at_the_limit(self):
        results = [self.call("go test ./internal/orders/...") for _ in range(4)]
        self.assertEqual(results, ["pass", "pass", "pass", "deny"])

    def test_editing_a_file_between_runs_resets_the_count(self):
        for i in range(6):
            with open(os.path.join(self.root, "handler.go"), "w") as f:
                f.write(f"package orders // attempt {i}\n")
            os.utime(os.path.join(self.root, "handler.go"), ns=(time.time_ns() + i, time.time_ns() + i))
            self.assertEqual(self.call("go test ./internal/orders/..."), "pass", f"attempt {i}")

    def test_agents_are_counted_separately(self):
        for _ in range(3):
            self.call("curl -fsS localhost:8081/health", agent="agent-qa")
        self.assertEqual(self.call("curl -fsS localhost:8081/health", agent="agent-backend"), "pass")
        self.assertEqual(self.call("curl -fsS localhost:8081/health", agent="agent-qa"), "deny")

    def test_whitespace_does_not_hide_a_repeat(self):
        for cmd in ["go  test ./...", "go test ./...", "go test   ./...", "go test ./..."]:
            last = self.call(cmd)
        self.assertEqual(last, "deny")

    def test_old_calls_fall_out_of_the_window(self):
        self.env["LOOP_GUARD_WINDOW"] = "1"
        for _ in range(3):
            self.call("make lint")
        time.sleep(1.2)
        self.assertEqual(self.call("make lint"), "pass")

    def test_other_tools_are_ignored(self):
        code, out, _ = run(GUARD, {"tool_name": "Read", "tool_input": {"file_path": "x"}, "cwd": self.root}, self.env)
        self.assertEqual((code, out), (0, ""))


class RoundBudgetTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.dir = os.path.join(self.root, ".agents", "work", "T-1")
        os.makedirs(self.dir)

    def report(self, round_no, approval="ไม่ต้อง"):
        text = open(TEMPLATE, encoding="utf-8").read()
        text = text.replace("<fill: PASS | ISSUES | BLOCKED | INCONCLUSIVE>", "ISSUES")
        text = re.sub(r"<fill: tree id[^>]*>", "3f2a9c1", text)
        text = re.sub(r"<fill: 1, 2 หรือ 3[^>]*>", str(round_no), text)
        text = re.sub(r"<fill: ไม่ต้อง หรืออ้าง D9[^>]*>", approval, text)
        text = re.sub(r"<fill(?::[^>]*)?>", "done", text)
        with open(os.path.join(self.dir, "test-report.md"), "w", encoding="utf-8") as f:
            f.write(text)

    def complete(self):
        return run(GATE, {"task_subject": "[T-1] verify: round", "cwd": self.root}, {"CLAUDE_PROJECT_DIR": self.root})

    def test_rounds_within_budget_complete(self):
        self.report(3)
        self.assertEqual(self.complete()[0], 0)

    def test_round_four_without_d9_is_blocked(self):
        self.report(4)
        code, _, err = self.complete()
        self.assertEqual(code, 2)
        self.assertIn("past the budget of 3", err)

    def test_round_four_with_approved_d9_completes(self):
        self.report(4, approval="D9 ใน decisions.md 2026-10-09: ผู้ใช้อนุมัติอีก 1 รอบ")
        self.assertEqual(self.complete()[0], 0)

    def test_missing_round_is_blocked(self):
        self.report("done")
        code, _, err = self.complete()
        self.assertEqual(code, 2)
        self.assertIn("Round line", err)


class TeamHealthTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.kit = os.path.join(self.tmp, "kit")
        shutil.copytree(KIT, self.kit, ignore=shutil.ignore_patterns("tests", "__pycache__"))
        self.work = os.path.join(self.kit, ".agents", "work")
        self.script = os.path.join(self.kit, ".agents", "scripts", "team_health.py")

    def health(self):
        r = subprocess.run([sys.executable, self.script, "--json"], capture_output=True, text=True)
        return r.returncode, json.loads(r.stdout)["warnings"]

    def test_clean_team_has_no_warnings(self):
        self.assertEqual(self.health(), (0, []))

    def test_each_loop_signal_is_reported(self):
        os.makedirs(os.path.join(self.work, ".loop-guard"))
        now = time.time()
        with open(os.path.join(self.work, ".loop-guard", "agent-qa.json"), "w") as f:
            json.dump({"agent": "agent-qa", "calls": {"k": {"command": "go test ./...", "times": [now] * 5}}}, f)
        task = os.path.join(self.work, "T-1")
        os.makedirs(task)
        with open(os.path.join(task, "test-report.md"), "w", encoding="utf-8") as f:
            f.write("- **Round:** 3\n")
        with open(os.path.join(task, "log.tsv"), "w", encoding="utf-8") as f:
            f.write("ts\tphase\tdecision\twhy\tevidence\tresult\n")
            f.write("t1\tverify\tran parity\tcheck\tlog\tDIFF\n")
            f.write("t2\tverify\tran parity\tcheck again\tlog\tDIFF\n")
        code, warnings = self.health()
        self.assertEqual(code, 1)
        text = "\n".join(warnings)
        self.assertIn("agent-qa: repeated `go test ./...` 5 times", text)
        self.assertIn("T-1: test-report.md is at round 3", text)
        self.assertIn("T-1: log.tsv repeats 'verify / ran parity / DIFF'", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
