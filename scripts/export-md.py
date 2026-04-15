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
import tempfile
from datetime import datetime
from pathlib import Path
# Die quietly on broken pipe (e.g. `| head`). SIGPIPE is POSIX-only — Windows
# doesn't have it, and broken-pipe handling isn't relevant there anyway.
try:
    from signal import signal, SIGPIPE, SIG_DFL
    signal(SIGPIPE, SIG_DFL)
except ImportError:
    pass


def resolve_jsonl() -> Path:
    sessions = Path("~/.claude/sessions").expanduser()
    cwd = str(Path.cwd())
    for s in sorted(sessions.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        info = json.loads(s.read_text(encoding="utf-8"))
        if info.get("cwd") == cwd:
            # Slug format used by Claude Code's project dir naming.
            # POSIX: "/home/user/project" -> "-home-user-project".
            # Windows: "C:\VSL\repos\vsl" -> "C--VSL-repos-vsl"
            # (both the drive-letter ":" and the "\" separator become "-").
            if sys.platform == "win32":
                slug = cwd.replace("\\", "-").replace(":", "-")
            else:
                slug = cwd.replace("/", "-")
            return Path("~/.claude/projects").expanduser() / slug / f"{info['sessionId']}.jsonl"
    sys.exit(f"export-session: no Claude Code session found for cwd: {cwd}")


def write_clipboard(text: str) -> None:
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["pbcopy"], input=text, text=True, check=True)
        return
    if system == "Windows":
        # Piping text through stdin to either clip.exe or PowerShell is
        # unreliable for Unicode: clip.exe decodes stdin as the console code
        # page (cp437/cp1252), and PowerShell opens its stdin stream with the
        # default encoding before any in-script [Console]::InputEncoding change
        # takes effect, so our UTF-8 bytes get mangled (e.g. "★" shows up as
        # "Γÿà" after a round trip). The only reliable path is to round-trip
        # through a temp file with an explicit encoding on both sides.
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            f.write(text)
            tmp_path = f.name
        try:
            # Escape single quotes for PowerShell single-quoted string (double
            # them). Tempfile paths won't contain newlines or single quotes on
            # Windows, but we defend against the latter anyway.
            escaped = tmp_path.replace("'", "''")
            ps_cmd = f"Get-Content -Path '{escaped}' -Raw -Encoding UTF8 | Set-Clipboard"
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd], check=True,
            )
        finally:
            Path(tmp_path).unlink()
        return
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
    records = list(map(json.loads, src.read_text(encoding="utf-8").splitlines()))
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
    # Write UTF-8 bytes directly to the binary buffer. sys.stdout.write would
    # encode via the locale, which is cp1252 on Windows and fails on any byte
    # outside Latin-1. POSIX systems with UTF-8 locale also accept this form.
    sys.stdout.buffer.write(text.encode("utf-8"))
elif argv[0] == "--clipboard":
    write_clipboard(text)
else:
    if argv[0] == "--auto":
        stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        path = Path.cwd() / f"claude-session-{stamp}.md"
    else:
        path = Path(argv[0]).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(path)
