# claude-export-md

A `/export-md` slash command for [Claude Code](https://claude.com/claude-code) that exports the current session as clean markdown — user turns as blockquotes, assistant text verbatim, tool calls and thinking blocks stripped.

## What it does

Running `/export-md` in a Claude Code session gives you three destinations:

- **Clipboard** — copies the rendered markdown to your system clipboard.
- **Current folder** — writes `claude-session-YYYY-MM-DD-HHMMSS.md` in the cwd.
- **Custom path** — `/export-md path/to/file.md` writes directly to that path.

The `/export-md` invocation itself is excluded from the output, so exporting is idempotent: re-running never accumulates the command into the transcript.

## Requirements

- Claude Code (uses `~/.claude/sessions/` and `~/.claude/projects/`)
- Python 3
- A clipboard tool for the clipboard mode:
  - macOS: `pbcopy` (built in)
  - Windows: `clip` (built in)
  - Linux: `wl-copy`, `xclip`, or `xsel`

## Install

### One-liner (curl)

```sh
curl -fsSL https://raw.githubusercontent.com/antiprosynthesis/claude-export-md/main/install.sh | bash
```

This downloads `commands/export-md.md` and `scripts/export-md.py` into `~/.claude/commands/` and `~/.claude/scripts/`, overwriting any files already at those paths.

If piping to `bash` makes you uneasy, clone first and inspect:

```sh
git clone https://github.com/antiprosynthesis/claude-export-md.git
cd claude-export-md
less install.sh
./install.sh
```

### Manual

Copy the two files into place yourself:

```sh
mkdir -p ~/.claude/commands ~/.claude/scripts
cp commands/export-md.md ~/.claude/commands/export-md.md
cp scripts/export-md.py  ~/.claude/scripts/export-md.py
chmod +x ~/.claude/scripts/export-md.py
```

## Usage

Inside a Claude Code session:

```
/export-md                    # prompts for destination
/export-md notes/chat.md      # writes directly to notes/chat.md
```

You can also run the script standalone from a Claude Code cwd:

```sh
python3 ~/.claude/scripts/export-md.py             # stdout
python3 ~/.claude/scripts/export-md.py --clipboard
python3 ~/.claude/scripts/export-md.py --auto      # timestamped file in cwd
python3 ~/.claude/scripts/export-md.py ./chat.md
```

## How it works

1. Scans `~/.claude/sessions/*.json` for a session whose `cwd` matches the current directory, newest first.
2. Loads the corresponding JSONL from `~/.claude/projects/<slug>/<sessionId>.jsonl`.
3. Walks records in order:
   - `type: user` with string content → rendered as a blockquote (meta messages skipped).
   - `type: assistant` with a content list → `text` blocks pass through verbatim.
   - Tool calls, tool results, and thinking blocks are dropped.
4. Truncates at the most recent `/export-md` command so the export never contains itself.

## Uninstall

```sh
rm ~/.claude/commands/export-md.md ~/.claude/scripts/export-md.py
```

## License

MIT — see [LICENSE](LICENSE).
