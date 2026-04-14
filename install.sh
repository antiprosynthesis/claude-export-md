#!/usr/bin/env bash
# Installer for the /export-md Claude Code slash command.
# Copies commands/export-md.md and scripts/export-md.py into ~/.claude/.
# Existing files at those paths are overwritten without backup.
set -euo pipefail

REPO="antiprosynthesis/claude-export-md"
BRANCH="main"
RAW="https://raw.githubusercontent.com/${REPO}/${BRANCH}"

CLAUDE_DIR="${HOME}/.claude"
COMMANDS_DIR="${CLAUDE_DIR}/commands"
SCRIPTS_DIR="${CLAUDE_DIR}/scripts"

mkdir -p "${COMMANDS_DIR}" "${SCRIPTS_DIR}"

fetch() {
    local src="$1" dst="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "${src}" -o "${dst}"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "${dst}" "${src}"
    else
        echo "install.sh: need curl or wget" >&2
        exit 1
    fi
}

# Support running from a local clone as well as curl | bash.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
if [[ -n "${SCRIPT_DIR}" && -f "${SCRIPT_DIR}/commands/export-md.md" && -f "${SCRIPT_DIR}/scripts/export-md.py" ]]; then
    install -m 0644 "${SCRIPT_DIR}/commands/export-md.md" "${COMMANDS_DIR}/export-md.md"
    install -m 0755 "${SCRIPT_DIR}/scripts/export-md.py" "${SCRIPTS_DIR}/export-md.py"
else
    fetch "${RAW}/commands/export-md.md" "${COMMANDS_DIR}/export-md.md"
    fetch "${RAW}/scripts/export-md.py" "${SCRIPTS_DIR}/export-md.py"
    chmod 0755 "${SCRIPTS_DIR}/export-md.py"
fi

echo "Installed /export-md:"
echo "  ${COMMANDS_DIR}/export-md.md"
echo "  ${SCRIPTS_DIR}/export-md.py"
echo "Run /export-md in Claude Code to try it."
