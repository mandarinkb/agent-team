"""Tests for checkpoint.py, standing decisions validation, sync_claude.py, and template comments.

    python3 tests/test_continuity.py
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


def py(*args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True)


class KitCopy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.kit = os.path.join(self.tmp, "kit")
        shutil.copytree(KIT, self.kit, ignore=shutil.ignore_patterns("tests", "__pycache__"))

    def path(self, *parts):
        return os.path.join(self.kit, *parts)

    def script(self, name):
        return self.path(".agents", "scripts", name)


class CheckpointTest(KitCopy):
    def setUp(self):
        super().setUp()
        subprocess.run(["git", "init", "-q", self.kit], check=True)
        with open(self.path("handler.go"), "w") as f:
            f.write("package orders\n")
        subprocess.run(["git", "-C", self.kit, "add", "handler.go"], check=True)
        self.assertEqual(py(self.script("new_task.py"), "bug", "orders", "--id", "T-1").returncode, 0)
        self.task = self.path(".agents", "work", "T-1")

    def write_note(self, extra=""):
        text = open(self.path(".agents", "templates", "checkpoint-note.md"), encoding="utf-8").read()
        text = re.sub(r"<fill(?::[^>]*)?>", "done", text) + extra
        text = text.replace("## ไฟล์ที่เกี่ยวข้อง\n\ndone", "## ไฟล์ที่เกี่ยวข้อง\n\n- `.agents/work/T-1/brief.md`")
        with open(os.path.join(self.task, "checkpoint-note.md"), "w", encoding="utf-8") as f:
            f.write(text)

    def test_round_trip_without_drift(self):
        self.write_note()
        r = py(self.script("checkpoint.py"), "save", "T-1")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = py(self.script("checkpoint.py"), "read")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("# Checkpoint T-1", r.stdout)
        self.assertIn("## Drift since the save\n\n- none", r.stdout)

    def test_drift_in_files_and_staged_tree_is_reported(self):
        self.write_note()
        py(self.script("checkpoint.py"), "save", "T-1")
        with open(os.path.join(self.task, "brief.md"), "a") as f:
            f.write("\nedited after the pause\n")
        with open(self.path("handler.go"), "a") as f:
            f.write("// more\n")
        subprocess.run(["git", "-C", self.kit, "add", "handler.go"], check=True)
        r = py(self.script("checkpoint.py"), "read", "T-1")
        self.assertEqual(r.returncode, 1)
        self.assertIn(".agents/work/T-1/brief.md changed since the save", r.stdout)
        self.assertIn("staged tree was", r.stdout)

    def test_unfinished_note_or_missing_path_is_refused(self):
        shutil.copy(self.path(".agents", "templates", "checkpoint-note.md"), os.path.join(self.task, "checkpoint-note.md"))
        r = py(self.script("checkpoint.py"), "save", "T-1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("placeholder", r.stderr)
        self.write_note(extra="\nSee `.agents/work/T-1/missing.md`\n")
        r = py(self.script("checkpoint.py"), "save", "T-1")
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not exist: .agents/work/T-1/missing.md", r.stderr)

    def test_no_checkpoint_is_exit_2(self):
        r = py(self.script("checkpoint.py"), "read")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout), {"kind": "missing"})


class StandingDecisionsTest(KitCopy):
    ENTRY = """
## SD-{n}: {title}
- **Codes:** {codes}
- **Scope:** migration program T-prog
- **Ruling:** {ruling}
- **Recorded:** 2026-10-09, lead, from T-1
- **Status:** {status}
"""

    def add(self, n=1, title="ignore request id", codes="D3", ruling='"ignore request_id ได้"', status="active"):
        with open(self.path(".agents", "standing-decisions.md"), "a", encoding="utf-8") as f:
            f.write(self.ENTRY.format(n=n, title=title, codes=codes, ruling=ruling, status=status))

    def check(self):
        return py(self.script("check_team.py"), self.kit)

    def test_valid_entries_pass(self):
        self.add(1)
        self.add(2, status='revoked 2026-10-10 "ไม่ใช้แล้ว"')
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_invalid_entries_are_caught(self):
        cases = [
            (dict(codes="D8"), "D8 can never be a standing decision"),
            (dict(codes="D3, D7"), "D7 can never be a standing decision"),
            (dict(ruling="ignore request id"), "must quote the user's own words"),
            (dict(status="paused"), "Status must be"),
            (dict(codes="none"), "Codes must name decision codes"),
        ]
        for kwargs, expected in cases:
            with self.subTest(expected=expected):
                path = self.path(".agents", "standing-decisions.md")
                original = open(path, encoding="utf-8").read()
                self.add(**kwargs)
                r = self.check()
                open(path, "w", encoding="utf-8").write(original)
                self.assertEqual(r.returncode, 1)
                self.assertIn(expected, r.stderr)

    def test_duplicate_ids_are_caught(self):
        self.add(1)
        self.add(1, title="other")
        r = self.check()
        self.assertIn("SD-1: duplicate id", r.stderr)


class SyncClaudeTest(KitCopy):
    def test_sync_then_check_then_drift(self):
        r = py(self.script("sync_claude.py"), "--check")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(py(self.script("sync_claude.py")).returncode, 0)
        self.assertTrue(os.path.isfile(self.path(".claude", "skills", "team-reflect", "references", "synthesizer.md")))
        self.assertFalse(os.path.exists(self.path(".claude", "skills", "licenses")))
        self.assertEqual(py(self.script("sync_claude.py"), "--check").returncode, 0)
        with open(self.path(".agents", "agents", "qa.md"), "a") as f:
            f.write("\nretro edit\n")
        r = py(self.script("sync_claude.py"), "--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("stale .claude/agents/qa.md", r.stdout)

    def test_orphan_team_skill_is_reported_not_deleted(self):
        py(self.script("sync_claude.py"))
        orphan = self.path(".claude", "skills", "team-old")
        os.makedirs(orphan)
        r = py(self.script("sync_claude.py"))
        self.assertIn("orphan .claude/skills/team-old", r.stdout)
        self.assertTrue(os.path.isdir(orphan))


class TemplateCommentTest(KitCopy):
    def test_placeholder_token_in_a_template_comment_is_caught(self):
        p = self.path(".agents", "templates", "test-report.md")
        text = open(p, encoding="utf-8").read().replace("<!--", "<!-- ห้ามมี \"<fill\" เหลือ", 1)
        open(p, "w", encoding="utf-8").write(text)
        r = py(self.script("check_team.py"), self.kit)
        self.assertEqual(r.returncode, 1)
        self.assertIn("a comment contains a placeholder token", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
