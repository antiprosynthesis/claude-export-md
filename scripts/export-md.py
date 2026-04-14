#!/usr/bin/env python3
"""Export a Claude Code session JSONL as raw markdown.

Resolves the current session automatically via ~/.claude/sessions/<pid>.json
(matched by cwd).

Modes:
  (no args)      write to stdout
  --clipboard    copy to the system clipboard
  --auto         save to the current working directory with a timestamped name
  <path>         save to <path>

User turns become blockquotes; assistant text passes through verbatim. Tool
calls, tool results, and thinking blocks are omitted. The current /export-md
invocation is excluded so each call is idempotent.
"""
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from signal import signal, SIGPIPE, SIG_DFL

signal(SIGPIPE, SIG_DFL)  # die quietly on broken pipe (e.g. `| head`)


def resolve_jsonl() -> Path:
    sessions = Path("~/.claude/sessions").expanduser()
    cwd = str(Path.cwd())
    for s in sorted(sessions.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        info = json.loads(s.read_text())
        if info.get("cwd") == cwd:
            slug = cwd.replace("/", "-")
            return Path("~/.claude/projects").expanduser() / slug / f"{info['sessionId']}.jsonl"
    sys.exit(f"export-session: no Claude Code session found for cwd: {cwd}")


def write_clipboard(text: str) -> None:
    system = platform.system()
    if system == "Darwin":
        cmd = ["pbcopy"]
    elif system == "Windows":
        cmd = ["clip"]
    else:
        cmd = None
        for candidate in (
            ["wl-copy"],
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
        ):
            if shutil.which(candidate[0]):
                cmd = candidate
                break
        if cmd is None:
            sys.exit("export-session: no clipboard tool found (install wl-copy, xclip, or xsel)")
    subprocess.run(cmd, input=text, text=True, check=True)


def export(src: Path) -> str:
    records = list(map(json.loads, src.read_text().splitlines()))
    stop = next(
        (i for i in range(len(records) - 1, -1, -1)
         if "<command-name>/export-md</command-name>" in
            str((records[i].get("message") or {}).get("content", ""))),
        len(records),
    )
    out = []
    for r in records[:stop]:
        c = (r.get("message") or {}).get("content")
        if r.get("type") == "user" and isinstance(c, str) and not r.get("isMeta"):
            out.append("\n".join(f"> {ln}" if ln else ">" for ln in c.strip().splitlines()))
        elif r.get("type") == "assistant" and isinstance(c, list):
            for b in c:
                if b.get("type") == "text" and b.get("text", "").strip():
                    out.append(b["text"].rstrip())
    return "\n\n".join(out) + "\n"


argv = sys.argv[1:]
text = export(resolve_jsonl())

if not argv:
    sys.stdout.write(text)
elif argv[0] == "--clipboard":
    write_clipboard(text)
else:
    if argv[0] == "--auto":
        stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        path = Path.cwd() / f"claude-session-{stamp}.md"
    else:
        path = Path(argv[0]).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print(path)
