#!/usr/bin/env python3
"""Copy selected pstack skills into .agents/skills/ and adapt them to this team.

    python3 .agents/scripts/vendor_pstack_skills.py [--pstack <pstack-claude checkout>] [--check]

Each edit names the exact upstream text it replaces. If upstream changed that text, the run
fails and names the edit, so an upgrade never ships a half-adapted skill. --check writes nothing
and exits 1 when the vendored files differ from what this script would produce.
Edit this script, not the generated files.
"""
import argparse
import os
import re
import sys

KIT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(KIT, ".agents", "skills")
DEFAULT_PSTACK = os.path.dirname(KIT)

PSTACK_LICENSE = "MIT, (c) 2026 Lauren Tan and (c) 2026 Michael Denyer"
CURSOR_LICENSE = "MIT, (c) 2026 Cursor"

SKILLS = {
    "tdd": {
        "license": PSTACK_LICENSE,
        "when": "Used by qa for a bug with a cheap local test path, and by backend or frontend for unit tests in their own package. Triggers: failing test first, regression test, TDD, test that fails before the fix.",
        "changes": "added when_to_use",
        "edits": [],
    },
    "deslop": {
        "license": CURSOR_LICENSE,
        "when": "Used by backend or frontend on their own diff before handing off to qa, and by reviewer as a lens. Triggers: clean up AI clutter, remove unnecessary comments, defensive checks, any casts, deep nesting.",
        "changes": "added when_to_use",
        "edits": [],
    },
    "blast-radius": {
        "license": PSTACK_LICENSE,
        "when": "Used by analyst before a design, by backend or frontend before changing code other modules call, and by reviewer on a risky diff. Triggers: what could this break, who calls this, is it safe to change, blast radius.",
        "changes": "pointed how and why at team-investigate, replaced the arena fan-out with asking the lead, dropped the unslop reference",
        "edits": [
            ("Companion to `how` and `why`. `how` tells you what the code does. `why` tells you why it's shaped that way. Blast radius tells you what it breaks somewhere else.",
             "Companion to `team-investigate`, which tells you what the code does and why it is shaped that way. Blast radius tells you what it breaks somewhere else."),
            ("Use `why` step 2 to pull the PR and commits.",
             "Pull the PR and commits with the history commands in `team-investigate`."),
            ("Same rules as `why`.",
             "Same evidence rules as the team: label each claim measured, inferred, or guess."),
            ("6. For a big or wide change, run it as an `arena`. Ask several models the same question and merge the answers. Different models catch different real bugs.",
             "6. For a big or wide change, ask the lead whether a second teammate or model should check it too. Different models catch different real bugs, and the lead weighs the cost."),
            ("Write it through `unslop`, cite real code,",
             "Write it in plain language, cite real code,"),
        ],
    },
    "benchmark-checklist": {
        "license": PSTACK_LICENSE,
        "when": "Used by qa or analyst before a performance number goes into a test report, a decision request, or a commit message, and by backend when it claims a speedup. Triggers: benchmark, faster, slower, latency, throughput, regression, PHP versus Go performance.",
        "changes": "linked the bundled copy of Explain the Number, replaced the pstack playbook references with how the team uses it",
        "edits": [
            ("[Explain the Number](../principle-explain-the-number/SKILL.md) says why.",
             "[Explain the Number](references/explain-the-number.md) says why."),
            ("- Keep a PR body to one primary number, per the **Opening a PR** playbook. Put the runs,",
             "- Keep a commit message or test report summary to one primary number. Put the runs,"),
        ],
        "tail": ("## How this fits the other perf material",
                 "## How this fits the team\n\n"
                 "- qa and the analyst run this before a performance number goes into a test report or a decision request.\n"
                 "- For a migration, compare the old and new implementation on the same machine and the same data, with the sides interleaved.\n"
                 "- A performance trade-off the user must weigh is a decision (D1). Raise it with `team-decision`.\n"),
        "refs": {
            "references/explain-the-number.md": ("principle-explain-the-number/SKILL.md", [
                ("run the full procedure with the [benchmark-checklist](../benchmark-checklist/SKILL.md) skill.",
                 "run the full procedure with the benchmark-checklist skill ([SKILL.md](../SKILL.md))."),
                ("Distinct from [Prove It Works](../principle-prove-it-works/SKILL.md), which checks",
                 "Distinct from Prove It Works, which checks"),
            ]),
        },
    },
    "typescript-best-practices": {
        "license": PSTACK_LICENSE,
        "when": "Loaded for .ts and .tsx files. Used by frontend, and by reviewer on TypeScript diffs. Triggers: TypeScript types, any, as casts, discriminated unions, zod schemas.",
        "changes": "bundled the two principles it depends on as references",
        "edits": [
            ("Apply the **type-system-discipline** principle skill first.",
             "Apply [Type System Discipline](references/type-system-discipline.md) first."),
            ("Trust types inside. See the **boundary-discipline** principle skill. |",
             "Trust types inside. See [Boundary Discipline](references/boundary-discipline.md). |"),
        ],
        "refs": {
            "references/patterns.md": ("typescript-best-practices/references/patterns.md", [
                ("See the **type-system-discipline** and **boundary-discipline** principle skills.",
                 "See [Type System Discipline](type-system-discipline.md) and [Boundary Discipline](boundary-discipline.md)."),
                ("Validate once where data crosses in. Trust types inside. See the **boundary-discipline** principle skill.",
                 "Validate once where data crosses in. Trust types inside. See [Boundary Discipline](boundary-discipline.md)."),
            ]),
            "references/type-system-discipline.md": ("principle-type-system-discipline/SKILL.md", [
                ("See the **boundary-discipline** principle skill for where to put validation.",
                 "See [Boundary Discipline](boundary-discipline.md) for where to put validation."),
                ("See the **encode-lessons-in-structure** principle skill.",
                 "Encode the rule in a type, lint, or check rather than in prose."),
            ]),
            "references/boundary-discipline.md": ("principle-boundary-discipline/SKILL.md", []),
        },
    },
    "create-verification-skill": {
        "license": PSTACK_LICENSE,
        "when": "Used once per project by qa, after the user approves it (D4), when there is no project `verify` skill. Triggers: no scripted way to run the app, qa keeps getting BLOCKED, set up verification, make a driver skill for this repo.",
        "changes": "dropped the Codex note, routed the work through qa with the user's approval, and pointed the maintenance loop at the team skill",
        "edits": [
            ("On Codex, read the [platform mapping](../poteto-mode/references/codex-tools.md), including its per-skill notes, before following this skill.\n\n", ""),
            ("Point the user at `/maintain-verification-skill` for keeping the map honest as the app changes. Suggest a cadence only if they ask.",
             "Tell the lead the skill is ready, with the evidence path from step 4. The lead tells the user that `maintain-verification-skill` keeps the map honest as the app changes. The new files go through the team's stage, review, and commit approval like any other change."),
        ],
        "refs": {
            "references/feature-map-example/README.md": ("create-verification-skill/references/feature-map-example/README.md", []),
            "references/feature-map-example/create-note.md": ("create-verification-skill/references/feature-map-example/create-note.md", []),
            "references/feature-map-example/search.md": ("create-verification-skill/references/feature-map-example/search.md", []),
        },
    },
    "maintain-verification-skill": {
        "license": PSTACK_LICENSE,
        "when": "Used by qa, with the lead's go-ahead, after the app changed or when the verify skill fails on a feature that exists. Triggers: audit the verify skill, feature map out of date, verify skill drifted.",
        "changes": "dropped the Codex note, replaced parallel helper agents with the lead's approval, and replaced the pull request with the team's commit approval",
        "edits": [
            ("at most one PR of proven corrections.", "at most one commit of proven corrections."),
            ("On Codex, read the [platform mapping](../poteto-mode/references/codex-tools.md), including its per-skill notes, before following this skill.\n\n", ""),
            ("No branch, no PR.", "Nothing to stage, no commit."),
            ("record it for the user, keep it out of this PR.", "record it for the lead to raise with the user, and keep it out of this commit."),
            ("- **changed** — one PR ships proven doc, harness, or map corrections.",
             "- **changed** — one commit, through the team's stage, review, and commit approval, ships proven doc, harness, or map corrections."),
            ("2. **Source wave.** One read-only subagent per feature file, launched concurrently.",
             "2. **Source wave.** Read each feature file against the source yourself. Parallel read-only helpers, one per feature file, are faster but cost more: ask the lead first, who raises it with the user when the map is large (D10)."),
            ("6. **Ship or stop.** For changed: one PR of proven corrections, re-read every changed file first. For clean or blocked: no PR, report the outcome and the coverage honestly.",
             "6. **Ship or stop.** For changed: re-read every changed file, then tell git it is ready to stage, and the corrections go through review and the user's commit approval. For clean or blocked: no commit, report the outcome and the coverage honestly."),
        ],
    },
    "thermo-nuclear-code-quality-review": {
        "license": CURSOR_LICENSE,
        "when": "Used by reviewer for a large restructuring, a migration pilot, or a file growing past about 1,000 lines. Triggers: deep code quality audit, harsh maintainability review, code judo, spaghetti conditions.",
        "changes": "wrote reports to the task directory, replaced the swarm fan-out with asking the lead",
        "edits": [
            ("Write the review to its own directory (for example `/tmp/<project>-thermo/`):",
             "Write the review to its own directory (for example `.agents/work/<task-id>/review/`):"),
            ("When the review fans out parallel reviewers via the **swarm** skill, this section overrides swarm's aggregation rules:",
             "When the lead approves more reviewers for a large review, this section governs how their reports combine:"),
        ],
    },
}


class DriftError(Exception):
    pass


def apply_edits(text, edits, where):
    for old, new in edits:
        if text.count(old) != 1:
            raise DriftError(f"{where}: expected exactly one occurrence of: {old[:70]}...")
        text = text.replace(old, new)
    return text


def strip_frontmatter(text):
    return re.sub(r"\A---\n.*?\n---\n+", "", text, count=1, flags=re.DOTALL)


def build(pstack_skills):
    files = {}
    for name, spec in SKILLS.items():
        src = os.path.join(pstack_skills, name, "SKILL.md")
        text = open(src, encoding="utf-8").read()
        text = apply_edits(text, spec["edits"], src)
        if "tail" in spec:
            marker, replacement = spec["tail"]
            if text.count(marker) != 1:
                raise DriftError(f"{src}: expected exactly one occurrence of: {marker}")
            text = text[: text.index(marker)] + replacement
        if "when_to_use:" in text.split("---", 2)[1]:
            raise DriftError(f"{src}: upstream now has when_to_use; review the override")
        text = re.sub(r"^(description: .*\n)", lambda m: m.group(1) + f"when_to_use: {spec['when']}\n",
                      text, count=1, flags=re.M)
        note = (f"> Vendored from pstack-claude `plugins/pstack/skills/{name}/` ({spec['license']}). "
                f"Team changes: {spec['changes']}. Generated by `.agents/scripts/vendor_pstack_skills.py`; "
                f"edit that script, not this file. Notices: `.agents/skills/THIRD_PARTY_NOTICES.md`.\n")
        text = re.sub(r"^(# .+\n)", lambda m: m.group(1) + "\n" + note, text, count=1, flags=re.M)
        files[os.path.join(name, "SKILL.md")] = text
        for rel, (src_rel, edits) in spec.get("refs", {}).items():
            ref_src = os.path.join(pstack_skills, src_rel)
            ref = apply_edits(open(ref_src, encoding="utf-8").read(), edits, ref_src)
            files[os.path.join(name, rel)] = strip_frontmatter(ref) if src_rel.startswith("principle-") else ref
    return files


def notices(pstack_root):
    rows = "\n".join(f"| `{n}` | `plugins/pstack/skills/{n}/` | {s['license']} | {s['changes']} |"
                     for n, s in SKILLS.items())
    text = ("# Third-party notices\n\n"
            "These skills are copied from pstack-claude (https://github.com/michael-denyer/pstack-claude), "
            "which ports Lauren Tan's pstack and skills from Cursor's cursor-team-kit. All are MIT-licensed. "
            "The license texts are in `licenses/`. The `team-*` skills are written for this team and adapt "
            "ideas from pstack.\n\n"
            "| Skill | Source | License | Team changes |\n|---|---|---|---|\n" + rows + "\n")
    out = {"THIRD_PARTY_NOTICES.md": text}
    for lic, dst in (("LICENSE", "licenses/LICENSE-pstack"), ("LICENSE-cursor-team-kit", "licenses/LICENSE-cursor-team-kit")):
        out[dst] = open(os.path.join(pstack_root, lic), encoding="utf-8").read()
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pstack", default=DEFAULT_PSTACK, help="root of a pstack-claude checkout")
    parser.add_argument("--check", action="store_true", help="exit 1 if vendored files are stale")
    args = parser.parse_args(argv)
    skills_dir = os.path.join(args.pstack, "plugins", "pstack", "skills")
    if not os.path.isdir(skills_dir):
        print(f"vendor: no pstack skills at {skills_dir}", file=sys.stderr)
        return 2
    try:
        files = {**build(skills_dir), **notices(args.pstack)}
    except DriftError as e:
        print(f"vendor: upstream drift, update the edit in this script: {e}", file=sys.stderr)
        return 1
    stale = []
    for rel, text in sorted(files.items()):
        path = os.path.join(OUT, rel)
        current = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if current == text:
            continue
        stale.append(rel)
        if not args.check:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
    verb = "stale" if args.check else "wrote"
    for rel in stale:
        print(f"{verb} .agents/skills/{rel}")
    print(f"{len(files)} files, {len(stale)} {verb}")
    return 1 if args.check and stale else 0


if __name__ == "__main__":
    sys.exit(main())
