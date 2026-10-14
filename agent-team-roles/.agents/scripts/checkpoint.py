#!/usr/bin/env python3
"""Save and read task checkpoints so a new session can pick up a team's work.

    python3 .agents/scripts/checkpoint.py save <task-id> [--note <file>]
    python3 .agents/scripts/checkpoint.py read [<task-id>]

Adapted from pstack's Pause safely and Session pickup playbooks and its resume.mjs. Agent teams
cannot resume teammates, so the checkpoint is what survives: the lead's note, a hash of every file
the note points at, and the git state of every worktree.

save  checks the note (all sections present, no placeholder, every referenced path exists), then
      writes an immutable checkpoint directory and atomically points LATEST at it.
read  prints the note and reports what changed since the save: edited files and worktree drift.
      Exit 0 when nothing drifted, 1 when something did or the checkpoint is damaged, 2 when there is
      no checkpoint.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

AGENTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(AGENTS)
WORK = os.path.join(AGENTS, "work")
SECTIONS = ["เป้าหมาย", "ทำเสร็จและตรวจแล้ว", "สถานะปัจจุบัน", "งานที่ค้างกลางทาง", "ขั้นต่อไป",
            "ทีมที่ต้องตั้งใหม่", "เรื่องที่รอผู้ใช้ตัดสิน", "ข้อควรระวัง", "ไฟล์ที่เกี่ยวข้อง"]
PLACEHOLDER = re.compile(r"<fill(?::[^>]*)?>")
PATH_REF = re.compile(r"`(\.agents/[^`\s]+)`")


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def git(*args, cwd=ROOT):
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def worktrees():
    listing = git("worktree", "list", "--porcelain")
    if listing is None:
        return []
    found, current = [], {}
    for line in listing.splitlines() + [""]:
        if line.startswith("worktree "):
            current = {"path": line[len("worktree "):]}
        elif line.startswith("HEAD "):
            current["head"] = line[5:]
        elif line.startswith("branch "):
            current["branch"] = line[len("branch refs/heads/"):] if line.startswith("branch refs/heads/") else line[7:]
        elif not line and current:
            path = current["path"]
            current["tree"] = git("write-tree", cwd=path) if os.path.isdir(path) else None
            status = git("status", "--porcelain", cwd=path) if os.path.isdir(path) else None
            current["changed_files"] = None if status is None else len([l for l in status.splitlines() if l.strip()])
            found.append(current)
            current = {}
    return found


def check_note(text):
    problems = []
    for name in SECTIONS:
        if not re.search(rf"^## {re.escape(name)}\s*$", text, re.M):
            problems.append(f"missing section '## {name}'")
    if PLACEHOLDER.search(text):
        problems.append(f"{len(PLACEHOLDER.findall(text))} '<fill' placeholder(s) remain")
    refs = sorted(set(r.rstrip("/.,") for r in PATH_REF.findall(text) if "<" not in r and "*" not in r))
    for ref in refs:
        if not os.path.exists(os.path.join(ROOT, ref)):
            problems.append(f"referenced path does not exist: {ref}")
    return problems, refs


def atomic_write(path, text):
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def save(task_id, note_path):
    task_dir = os.path.join(WORK, task_id)
    if not os.path.isdir(task_dir):
        print(f"checkpoint: no task directory {task_dir}", file=sys.stderr)
        return 2
    note_path = note_path or os.path.join(task_dir, "checkpoint-note.md")
    if not os.path.isfile(note_path):
        print(f"checkpoint: no note at {note_path}. Copy .agents/templates/checkpoint-note.md and fill it.", file=sys.stderr)
        return 2
    text = open(note_path, encoding="utf-8").read()
    problems, refs = check_note(text)
    if problems:
        print("checkpoint: note is not ready:", file=sys.stderr)
        for p in problems:
            print(f"- {p}", file=sys.stderr)
        return 1
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    cp_dir = os.path.join(task_dir, "checkpoints", stamp)
    os.makedirs(cp_dir)
    shutil.copy2(note_path, os.path.join(cp_dir, "note.md"))
    files = {}
    for ref in refs:
        full = os.path.join(ROOT, ref)
        if os.path.isfile(full):
            files[ref] = sha256(full)
    manifest = {"task_id": task_id, "saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "note_sha256": sha256(os.path.join(cp_dir, "note.md")), "files": files, "worktrees": worktrees()}
    atomic_write(os.path.join(cp_dir, "manifest.json"), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    pointer = {"task_id": task_id, "checkpoint": os.path.relpath(cp_dir, ROOT), "saved_at": manifest["saved_at"]}
    atomic_write(os.path.join(WORK, "LATEST.json"), json.dumps(pointer, ensure_ascii=False, indent=2) + "\n")
    print(f"saved {os.path.relpath(cp_dir, ROOT)} ({len(files)} files hashed, {len(manifest['worktrees'])} worktrees recorded)")
    return 0


def latest_for(task_id):
    if task_id is None:
        pointer = os.path.join(WORK, "LATEST.json")
        if not os.path.isfile(pointer):
            return None
        return os.path.join(ROOT, json.load(open(pointer, encoding="utf-8"))["checkpoint"])
    base = os.path.join(WORK, task_id, "checkpoints")
    if not os.path.isdir(base) or not os.listdir(base):
        return None
    return os.path.join(base, sorted(os.listdir(base))[-1])


def read(task_id):
    cp_dir = latest_for(task_id)
    if cp_dir is None:
        print(json.dumps({"kind": "missing"}))
        return 2
    try:
        manifest = json.load(open(os.path.join(cp_dir, "manifest.json"), encoding="utf-8"))
        note = open(os.path.join(cp_dir, "note.md"), encoding="utf-8").read()
    except (OSError, json.JSONDecodeError) as e:
        print(json.dumps({"kind": "unavailable", "detail": str(e)}))
        return 1
    drift = []
    if sha256(os.path.join(cp_dir, "note.md")) != manifest["note_sha256"]:
        drift.append("the saved note itself was edited after the save")
    for ref, digest in manifest["files"].items():
        full = os.path.join(ROOT, ref)
        if not os.path.isfile(full):
            drift.append(f"{ref} no longer exists")
        elif sha256(full) != digest:
            drift.append(f"{ref} changed since the save")
    now = {w["path"]: w for w in worktrees()}
    for w in manifest["worktrees"]:
        cur = now.get(w["path"])
        if cur is None:
            drift.append(f"worktree {w['path']} no longer exists")
            continue
        for key, label in (("head", "HEAD"), ("tree", "staged tree"), ("changed_files", "number of changed files")):
            if cur.get(key) != w.get(key):
                drift.append(f"worktree {w['path']}: {label} was {w.get(key)}, now {cur.get(key)}")
    print(f"# Checkpoint {manifest['task_id']} saved {manifest['saved_at']} ({os.path.relpath(cp_dir, ROOT)})\n")
    print(note)
    print("\n## Drift since the save\n")
    print("\n".join(f"- {d}" for d in drift) if drift else "- none")
    return 1 if drift else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("save")
    s.add_argument("task_id")
    s.add_argument("--note")
    r = sub.add_parser("read")
    r.add_argument("task_id", nargs="?")
    args = parser.parse_args(argv)
    if args.command == "save":
        return save(args.task_id, args.note)
    return read(args.task_id)


if __name__ == "__main__":
    sys.exit(main())
