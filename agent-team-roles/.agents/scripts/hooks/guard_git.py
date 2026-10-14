#!/usr/bin/env python3
"""PreToolUse hook for Bash: route commit-class git commands to the user, deny destructive ones.

The settings ask rules match commands as written. This hook also catches forms they miss,
such as `git -C . commit`, `git -c x=y push`, and commands inside `bash -c "..."`.

For `git commit` it reads `Task: <task-id>` from the message and checks the task's reports:
- deny while the test report is missing or unfinished, or a review report has unfinished sections;
- otherwise ask, and tell the user whether the staged tree matches the Revision in both reports.
It never allows a commit by itself. The user decides at the prompt.

Reads the hook JSON on stdin. Prints a PreToolUse decision on stdout, or nothing to stay out of the way.
"""
import json
import os
import re
import shlex
import subprocess
import sys

WRAPPERS = {"sudo", "env", "command", "nohup", "time", "nice", "exec"}
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
ASK_GIT = {"push", "merge", "rebase", "tag", "am", "cherry-pick", "revert"}
TASK = re.compile(r"^\s*Task:\s*(T-[A-Za-z0-9._-]+)\s*$", re.M)
VERDICT = re.compile(r"^- \*\*Verdict:\*\*\s*([A-Z_]+)\s*$", re.M)
PLACEHOLDER = re.compile(r"<(fill|lead)(?::[^>]*)?>")
REVISION = re.compile(r"^- \*\*Revision:\*\*\s*`?([0-9a-f]{7,40})`?\s*$", re.M)

DENY, ASK, ALLOW = 2, 1, 0


class Context:
    def __init__(self, cwd, root):
        self.cwd = cwd
        self.root = root


def split_commands(command):
    """Split on ; & | && || and newlines that sit outside quotes, keeping quoted text whole."""
    parts, buf, quote, i = [], [], None, 0
    while i < len(command):
        c = command[i]
        if quote:
            buf.append(c)
            if c == "\\" and quote == '"' and i + 1 < len(command):
                buf.append(command[i + 1])
                i += 1
            elif c == quote:
                quote = None
        elif c in "'\"":
            quote = c
            buf.append(c)
        elif c == "\\" and i + 1 < len(command):
            buf.append(c + command[i + 1])
            i += 1
        elif c in ";&|\n":
            parts.append("".join(buf))
            buf = []
            if i + 1 < len(command) and command[i + 1] == c and c in "&|":
                i += 1
        else:
            buf.append(c)
        i += 1
    parts.append("".join(buf))
    return parts


def tokens(segment):
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def strip_prefix(toks):
    i = 0
    while i < len(toks) and (toks[i] in WRAPPERS or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[i])):
        i += 1
    return toks[i:]


def git_subcommand(toks):
    i, repo = 1, None
    while i < len(toks):
        t = toks[i]
        if t in GIT_OPTS_WITH_VALUE:
            if t == "-C" and i + 1 < len(toks):
                repo = toks[i + 1]
            i += 2
        elif t.startswith("-"):
            i += 1
        else:
            return t, toks[i + 1:], repo
    return None, [], repo


def short_flags(args):
    return {c for a in args if re.match(r"^-[A-Za-z]+$", a) for c in a[1:]}


def commit_message(args, repo_dir):
    parts, i = [], 0
    while i < len(args):
        a = args[i]
        if a in ("-m", "--message") and i + 1 < len(args):
            parts.append(args[i + 1])
            i += 2
            continue
        if a.startswith("--message="):
            parts.append(a.split("=", 1)[1])
        elif re.match(r"^-[a-zA-Z]*m$", a) and i + 1 < len(args):
            parts.append(args[i + 1])
            i += 2
            continue
        elif a in ("-F", "--file") and i + 1 < len(args):
            path = os.path.join(repo_dir, args[i + 1])
            if os.path.isfile(path):
                parts.append(open(path, encoding="utf-8", errors="replace").read())
            i += 2
            continue
        i += 1
    return "\n".join(parts)


def staged_tree(repo_dir):
    try:
        out = subprocess.run(["git", "-C", repo_dir, "write-tree"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def same(rev, tree):
    return bool(rev and tree and tree.startswith(rev))


def check_commit(args, repo_dir, ctx):
    task = TASK.search(commit_message(args, repo_dir))
    if not task:
        return ASK, ("git commit needs the user's approval. The message has no 'Task: <task-id>' line, "
                     "so the test and review reports were not checked.")
    task_id = task.group(1)
    work = os.path.join(ctx.root, ".agents", "work", task_id)
    test_path, review_path = os.path.join(work, "test-report.md"), os.path.join(work, "review-report.md")
    if not os.path.isfile(test_path):
        return DENY, f"commit blocked: {task_id} has no test-report.md. qa must verify the staged content first."
    test = open(test_path, encoding="utf-8").read()
    if any(m.group(1) == "fill" for m in PLACEHOLDER.finditer(test)):
        return DENY, f"commit blocked: {task_id} test-report.md still has placeholders."
    review = open(review_path, encoding="utf-8").read() if os.path.isfile(review_path) else None
    if review is not None and PLACEHOLDER.search(review):
        return DENY, f"commit blocked: {task_id} review-report.md has unfinished reviewer or lead triage sections."

    tree = staged_tree(repo_dir)
    t_verdict, t_rev = (VERDICT.search(test) or [None, None])[1], (REVISION.search(test) or [None, None])[1]
    lines = [f"Approve this commit for {task_id}?",
             f"Test report: {t_verdict} at {t_rev}."]
    warnings = []
    if t_verdict != "PASS":
        warnings.append(f"the test verdict is {t_verdict}, not PASS")
    if review is None:
        lines.append("Review: no review report.")
    else:
        r_verdict, r_rev = (VERDICT.search(review) or [None, None])[1], (REVISION.search(review) or [None, None])[1]
        lines.append(f"Review: {r_verdict} at {r_rev}.")
        if not same(r_rev, tree):
            warnings.append("the staged content differs from what the reviewer reviewed")
    if tree is None:
        warnings.append("could not read the staged tree to compare")
    elif not same(t_rev, tree):
        warnings.append("the staged content differs from what qa tested")
    lines.append(f"Staged tree: {tree}.")
    lines.append("WARNING: " + "; ".join(warnings) + "." if warnings else "The staged content matches the reports.")
    return ASK, " ".join(lines)


def classify_git(sub, args, repo_dir, ctx):
    flags = short_flags(args)
    if sub == "push":
        if any(a.startswith("--force") or a.startswith("--mirror") or a.startswith("--delete") for a in args) \
                or "f" in flags or "d" in flags or any(a.startswith("+") or a.startswith(":") for a in args):
            return DENY, "force-push, mirror, or remote branch deletion is never allowed for the team"
        return ASK, "git push needs the user's approval (D7)"
    if sub == "reset" and "--hard" in args:
        return DENY, "git reset --hard discards work and is not allowed for the team"
    if sub == "clean" and ("f" in flags or "--force" in args):
        return DENY, "git clean -f deletes untracked files and is not allowed for the team"
    if sub == "branch" and ("D" in flags or ("--delete" in args and "--force" in args)):
        return DENY, "git branch -D force-deletes a branch and is not allowed for the team"
    if sub == "commit":
        if "--no-verify" in args or "n" in flags:
            return DENY, "git commit --no-verify skips hooks and is not allowed"
        return check_commit(args, repo_dir, ctx)
    if sub in ASK_GIT:
        return ASK, f"git {sub} changes history and needs the user's approval"
    return ALLOW, ""


def classify_segment(segment, ctx, depth=0):
    toks = strip_prefix(tokens(segment.strip()))
    if not toks:
        return ALLOW, ""
    prog = toks[0].rsplit("/", 1)[-1]
    if prog == "cd" and len(toks) > 1:
        ctx.cwd = os.path.normpath(os.path.join(ctx.cwd, os.path.expanduser(toks[1])))
        return ALLOW, ""
    if prog in {"bash", "sh", "zsh"} and "-c" in toks and depth < 3:
        inner = toks[toks.index("-c") + 1] if toks.index("-c") + 1 < len(toks) else ""
        return classify_command(inner, ctx, depth + 1)
    if prog == "git":
        sub, args, repo = git_subcommand(toks)
        repo_dir = os.path.normpath(os.path.join(ctx.cwd, repo)) if repo else ctx.cwd
        return classify_git(sub, args, repo_dir, ctx) if sub else (ALLOW, "")
    if prog == "gh" and len(toks) >= 3 and toks[1] == "pr":
        if toks[2] == "merge":
            return DENY, "merging a pull request is the user's job"
        if toks[2] == "create":
            return ASK, "opening a pull request needs the user's approval (D7)"
    return ALLOW, ""


def classify_command(command, ctx, depth=0):
    worst, reason = ALLOW, ""
    for segment in split_commands(command or ""):
        level, why = classify_segment(segment, ctx, depth)
        if level > worst:
            worst, reason = level, why
    return worst, reason


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    cwd = data.get("cwd") or os.getcwd()
    ctx = Context(cwd, os.environ.get("CLAUDE_PROJECT_DIR") or cwd)
    level, reason = classify_command(data.get("tool_input", {}).get("command", ""), ctx)
    if level == ALLOW:
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny" if level == DENY else "ask",
        "permissionDecisionReason": reason,
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
