"""Tests for the migration program pieces: new_task kinds and migration_status.py.

    python3 tests/test_migration.py
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
HEADER = "unit\tkind\tmethod\tpath\trisk\torder\tdepends_on\ttask_id\tstate\tnotes\n"


def py(*args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True)


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.kit = os.path.join(self.tmp, "kit")
        shutil.copytree(KIT, self.kit, ignore=shutil.ignore_patterns("tests", "__pycache__"))
        self.work = os.path.join(self.kit, ".agents", "work")
        self.template = open(os.path.join(KIT, ".agents", "templates", "test-report.md"), encoding="utf-8").read()

    def script(self, name):
        return os.path.join(self.kit, ".agents", "scripts", name)

    def report(self, task_id, verdict="PASS", parity="5 / 0 / 0", commit=True):
        text = self.template.replace("<fill: PASS | ISSUES | BLOCKED | INCONCLUSIVE>", verdict)
        text = text.replace("<fill: tree id จาก git write-tree ที่ git ส่งมา>", "3f2a9c1")
        text = text.replace('<fill: ตัวเลขจาก parity.py ในรูปแบบ "12 / 0 / 0" หรือ "ไม่เกี่ยวข้อง">', parity)
        text = re.sub(r"<fill: 1, 2 หรือ 3[^>]*>", "1", text)
        text = re.sub(r"<fill(?::[^>]*)?>", "done", text)
        if commit:
            text += "| 9b8c7d6 | feat(orders): port GET /api/orders | 2026-10-09 |\n"
        os.makedirs(os.path.join(self.work, task_id), exist_ok=True)
        with open(os.path.join(self.work, task_id, "test-report.md"), "w", encoding="utf-8") as f:
            f.write(text)

    def program(self, rows):
        r = py(self.script("new_task.py"), "program", "PHP API to Go", "--id", "T-prog")
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.work, "T-prog", "inventory.tsv"), "w", encoding="utf-8") as f:
            f.write(HEADER + "".join("\t".join(row) + "\n" for row in rows))
        r = py(self.script("migration_status.py"), "T-prog", "--json")
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else None
        return r.returncode, out, r

    def test_program_task_gets_plan_and_inventory(self):
        r = py(self.script("new_task.py"), "program", "PHP API to Go", "--id", "T-p1")
        self.assertEqual(r.returncode, 0, r.stderr)
        files = sorted(os.listdir(os.path.join(self.work, "T-p1")))
        self.assertEqual(files, ["decisions.md", "inventory.tsv", "log.tsv", "migration-plan.md"])
        self.assertEqual(open(os.path.join(self.work, "T-p1", "inventory.tsv")).read(), HEADER)
        self.assertIn("migration-retire.md", py(self.script("new_task.py"), "retire", "orders", "--id", "T-r1").stdout)

    def test_consistent_program_is_done(self):
        self.report("T-auth")
        self.report("T-orders")
        code, out, r = self.program([
            ["auth", "primitive", "-", "-", "high", "1", "", "T-auth", "committed", ""],
            ["orders-list", "endpoint", "GET", "/api/orders", "low", "2", "auth", "T-orders", "traffic", "pilot"],
            ["orders-create", "endpoint", "POST", "/api/orders", "high", "3", "auth", "", "planned", ""],
        ])
        self.assertEqual(code, 0, r.stdout + r.stderr)
        self.assertEqual((out["done"], out["total"], out["problems"]), (2, 3, []))
        status = open(os.path.join(self.work, "T-prog", "STATUS.md"), encoding="utf-8").read()
        self.assertIn("**Done:** 2 of 3 units", status)
        self.assertIn("| 2 | orders-list | endpoint | low | traffic | T-orders | PASS | 3f2a9c1 | 5/0/0 | yes |", status)

    def test_each_inconsistency_is_reported(self):
        self.report("T-a", verdict="ISSUES")
        self.report("T-b", parity="4 / 1 / 0")
        self.report("T-c", commit=False)
        self.report("T-d", parity="3 / 0 / 2")
        code, out, _ = self.program([
            ["auth", "primitive", "-", "-", "high", "1", "", "T-a", "verified", ""],
            ["orders", "endpoint", "GET", "/o", "low", "2", "", "T-b", "verified", ""],
            ["users", "endpoint", "GET", "/u", "low", "3", "", "T-c", "committed", ""],
            ["items", "endpoint", "GET", "/i", "low", "4", "", "T-d", "verified", ""],
            ["carts", "endpoint", "GET", "/c", "low", "5", "auth", "T-e", "porting", ""],
            ["tags", "endpoint", "GET", "/t", "low", "6", "", "", "baseline", ""],
            ["notes", "endpoint", "GET", "/n", "low", "7", "", "T-missing", "verified", ""],
        ])
        self.assertEqual(code, 1)
        problems = "\n".join(out["problems"])
        for expected in ["auth: claims verified but report verdict is ISSUES",
                         "orders: parity shows 1 DIFF and 0 UNREACHABLE",
                         "users: claims committed but the report lists no commit",
                         "items: parity shows 0 DIFF and 2 UNREACHABLE",
                         "carts: started before dependency auth was committed",
                         "tags: state is past planned but no task_id",
                         "notes: claims verified but has no test report"]:
            self.assertIn(expected, problems)
        self.assertEqual(out["done"], 0)

    def test_bad_inventory_is_an_input_error(self):
        code, _, r = self.program([["auth", "primitive", "-", "-", "high", "1", "", "T-a", "almost-done", ""]])
        self.assertEqual(code, 2)
        self.assertIn("state 'almost-done'", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
