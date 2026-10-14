"""Tests for new_task.py, log_row.py, check_team.py, and install.py, run against temporary copies.

    python3 tests/test_team_kit.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def py(*args, cwd=None):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=cwd)


class KitCopy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.kit = os.path.join(self.tmp, "kit")
        shutil.copytree(KIT, self.kit, ignore=shutil.ignore_patterns("tests", "__pycache__"))

    def path(self, *parts):
        return os.path.join(self.kit, *parts)


class NewTaskTest(KitCopy):
    def test_creates_a_filled_task_directory(self):
        r = py(self.path(".agents", "scripts", "new_task.py"), "migration", "GET /api/orders", "--id", "T-1-orders")
        self.assertEqual(r.returncode, 0, r.stderr)
        work = self.path(".agents", "work", "T-1-orders")
        self.assertEqual(sorted(os.listdir(work)),
                         ["brief.md", "decisions.md", "log.tsv", "parity", "review-report.md", "test-report.md"])
        brief = open(os.path.join(work, "brief.md"), encoding="utf-8").read()
        self.assertIn("# Brief: GET /api/orders", brief)
        self.assertIn("`.agents/workflows/migration.md`", brief)
        self.assertNotIn("{{", brief)
        self.assertIn("<fill", open(os.path.join(work, "test-report.md"), encoding="utf-8").read())

    def test_refuses_to_overwrite_and_rejects_bad_ids(self):
        script = self.path(".agents", "scripts", "new_task.py")
        self.assertEqual(py(script, "bug", "x", "--id", "T-2").returncode, 0)
        self.assertEqual(py(script, "bug", "x", "--id", "T-2").returncode, 2)
        self.assertEqual(py(script, "bug", "x", "--id", "../escape").returncode, 2)

    def test_thai_title_gets_a_time_based_id(self):
        r = py(self.path(".agents", "scripts", "new_task.py"), "bug", "ตัวกรองค้นหารีเซ็ต")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout.splitlines()[0], r"^T-\d{8}-\d{6}$")


class LogRowTest(KitCopy):
    def test_appends_sanitized_rows(self):
        py(self.path(".agents", "scripts", "new_task.py"), "bug", "x", "--id", "T-3")
        r = py(self.path(".agents", "scripts", "log_row.py"), "T-3", "verify", "=HYPERLINK(1)",
               "line one\nline two", "a\tb", "PASS")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = open(self.path(".agents", "work", "T-3", "log.tsv"), encoding="utf-8").read().splitlines()
        self.assertEqual(rows[0], "ts\tphase\tdecision\twhy\tevidence\tresult")
        cells = rows[1].split("\t")
        self.assertEqual(cells[1:], ["verify", "'=HYPERLINK(1)", "line one line two", "a b", "PASS"])


class CheckTeamTest(KitCopy):
    def check(self, *extra):
        return py(self.path(".agents", "scripts", "check_team.py"), self.kit, *extra)

    def test_clean_kit_passes(self):
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_each_mutation_is_caught(self):
        mutations = [
            (".agents/AGENTS.md", "never answers a decision", "may answer a decision", "no longer says"),
            (".agents/agents/qa.md", "model: opus", "", "frontmatter needs model"),
            (".agents/workflows/feature.md", "GATE G2", "GATE G9", "missing GATE G2"),
            (".agents/skills/team-verify/SKILL.md", "name: team-verify", "name: verify", "frontmatter needs name"),
            (".agents/workflows/bug-fix.md", "`.agents/protocols/commit-approval.md`",
             "`.agents/protocols/missing.md`", "does not exist"),
            (".agents/settings.example.json", "Bash(git commit *)", "Bash(git status *)", "Bash(git commit *)"),
            (".agents/agents/backend.md", "## Choosing skills", "## Skills", "Choosing skills"),
            (".agents/skills/team-review/SKILL.md", "when_to_use:", "notes:", "when_to_use"),
            (".agents/AGENTS.md", "Choose skills yourself", "Use the listed skills", "no longer says"),
            (".agents/workflows/feature.md", "**reviewer** Use `team-review`", "**qa** Use `team-review`", "needs a reviewer step"),
            (".agents/templates/review-report.md", "## การคัดกรองของ lead", "## Lead", "hooks rely on"),
        ]
        for rel, old, new, expected in mutations:
            with self.subTest(rel=rel, change=new):
                p = self.path(*rel.split("/"))
                original = open(p, encoding="utf-8").read()
                self.assertIn(old, original)
                open(p, "w", encoding="utf-8").write(original.replace(old, new, 1))
                r = self.check()
                open(p, "w", encoding="utf-8").write(original)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(expected, r.stderr)


class InstallTest(KitCopy):
    def test_install_into_empty_project_then_check(self):
        project = os.path.join(self.tmp, "project")
        os.makedirs(project)
        r = py(self.path("install.py"), project)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for rel in [".claude/agents/qa.md", ".claude/skills/team-verify/SKILL.md", ".claude/settings.json",
                    ".agents/AGENTS.md", "CLAUDE.md"]:
            self.assertTrue(os.path.isfile(os.path.join(project, rel)), rel)
        self.assertIn("@.agents/AGENTS.md", open(os.path.join(project, "CLAUDE.md"), encoding="utf-8").read())

    def test_existing_claude_md_and_settings_are_kept(self):
        project = os.path.join(self.tmp, "project2")
        os.makedirs(os.path.join(project, ".claude"))
        open(os.path.join(project, "CLAUDE.md"), "w").write("# Mine\n")
        open(os.path.join(project, ".claude", "settings.json"), "w").write("{}\n")
        r = py(self.path("install.py"), project)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(open(os.path.join(project, "CLAUDE.md")).read(), "# Mine\n\n@.agents/AGENTS.md\n")
        self.assertEqual(open(os.path.join(project, ".claude", "settings.json")).read(), "{}\n")
        self.assertIn("merge permissions", r.stdout)

    def test_drifted_copy_is_reported(self):
        project = os.path.join(self.tmp, "project3")
        os.makedirs(project)
        py(self.path("install.py"), project)
        with open(os.path.join(project, ".claude", "agents", "qa.md"), "a") as f:
            f.write("\nlocal edit\n")
        r = py(os.path.join(project, ".agents", "scripts", "check_team.py"), project, "--installed")
        self.assertEqual(r.returncode, 1)
        self.assertIn(".claude/agents/qa.md", r.stderr)


class VendoredSkillsTest(KitCopy):
    NEEDED = ["tdd", "deslop", "blast-radius", "benchmark-checklist", "typescript-best-practices",
              "thermo-nuclear-code-quality-review", "create-verification-skill", "maintain-verification-skill",
              "principle-explain-the-number",
              "principle-type-system-discipline", "principle-boundary-discipline"]

    def fake_pstack(self):
        repo = os.path.dirname(KIT)
        root = os.path.join(self.tmp, "pstack")
        for name in self.NEEDED:
            shutil.copytree(os.path.join(repo, "plugins", "pstack", "skills", name),
                            os.path.join(root, "plugins", "pstack", "skills", name))
        for lic in ("LICENSE", "LICENSE-cursor-team-kit"):
            shutil.copy(os.path.join(repo, lic), os.path.join(root, lic))
        return root

    def vendor(self, *args):
        return py(self.path(".agents", "scripts", "vendor_pstack_skills.py"), *args)

    def test_vendored_files_are_current(self):
        r = self.vendor("--pstack", self.fake_pstack(), "--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_upstream_drift_fails_loudly(self):
        root = self.fake_pstack()
        p = os.path.join(root, "plugins", "pstack", "skills", "blast-radius", "SKILL.md")
        text = open(p, encoding="utf-8").read().replace("Use `why` step 2", "Use the why skill")
        open(p, "w", encoding="utf-8").write(text)
        r = self.vendor("--pstack", root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("upstream drift", r.stderr)

    def test_hand_edited_vendored_file_is_reported_stale(self):
        p = self.path(".agents", "skills", "tdd", "SKILL.md")
        with open(p, "a", encoding="utf-8") as f:
            f.write("\nlocal edit\n")
        r = self.vendor("--pstack", self.fake_pstack(), "--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("stale .agents/skills/tdd/SKILL.md", r.stdout)

    def test_install_copies_skill_references(self):
        project = os.path.join(self.tmp, "project")
        os.makedirs(project)
        r = py(self.path("install.py"), project)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for rel in ["typescript-best-practices/references/patterns.md",
                    "benchmark-checklist/references/explain-the-number.md", "blast-radius/SKILL.md"]:
            self.assertTrue(os.path.isfile(os.path.join(project, ".claude", "skills", rel)), rel)
        self.assertFalse(os.path.exists(os.path.join(project, ".claude", "skills", "licenses")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
