---
description: Export current session to markdown (clipboard or file)
---

Export the current Claude Code session as markdown.

`$ARGUMENTS` is the user's argument to /export-md (may be empty).

**If `$ARGUMENTS` is NOT empty**, treat it as the target file path:
- Run: `python3 ~/.claude/scripts/export-md.py "$ARGUMENTS"`
- Reply with exactly this single line and nothing else: `Wrote $ARGUMENTS`

**If `$ARGUMENTS` IS empty**, ask the user where to save using the `AskUserQuestion` tool:
- Question: "Where should I save the exported session?"
- Header: "Destination"
- Options (in this order):
  1. label: `Clipboard`, description: `Copy to the system clipboard`
  2. label: `Current folder`, description: `Save to the current working directory with a timestamped filename`

Based on the user's answer:
- **Clipboard** → Run `python3 ~/.claude/scripts/export-md.py --clipboard`, then reply with exactly: `Copied to clipboard`
- **Current folder** → Run `python3 ~/.claude/scripts/export-md.py --auto` (the script prints the saved path on stdout), then reply with exactly: `Wrote <path printed by the script>`
- **Other (custom path)** → Run `python3 ~/.claude/scripts/export-md.py "<user's path>"`, then reply with exactly: `Wrote <user's path>`

Keep your final reply to the exact short line specified above. Do not narrate, do not summarize, do not add insights or explanations.
