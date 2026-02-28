#!/usr/bin/env bash
# auto-read-notebooks.sh — UserPromptSubmit hook
#
# Scans modified notebooks for cells flagged with "todo:" and injects only
# those cells into the conversation. This avoids dumping entire notebooks
# into context on every prompt — only cells the human explicitly flags
# for Claude's attention are included.
#
# Usage in notebooks:
#   Code cell:     # todo: should this use async?
#   Markdown cell: todo: is this explanation clear?
#
# Keeps a timestamp file at .claude/.last-nb-read to track what's already
# been seen. On first run, checks notebooks modified in the last 5 minutes.

set -euo pipefail

MARKER="todo:"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
TIMESTAMP_FILE="$PROJECT_DIR/.claude/.last-nb-read"

# Detect nbs directory from settings.ini, fall back to nbs/
NBS_DIR="$PROJECT_DIR/nbs"
if [[ -f "$PROJECT_DIR/settings.ini" ]]; then
    configured=$(grep -E '^nbs_path\s*=' "$PROJECT_DIR/settings.ini" 2>/dev/null \
        | head -1 | sed 's/.*=\s*//' | xargs)
    [[ -n "${configured:-}" ]] && NBS_DIR="$PROJECT_DIR/$configured"
fi

# Nothing to do if the notebooks directory doesn't exist
[[ -d "$NBS_DIR" ]] || exit 0

# Find modified notebooks
if [[ -f "$TIMESTAMP_FILE" ]]; then
    # Subsequent runs: notebooks modified since last prompt
    MODIFIED=$(find "$NBS_DIR" -name '*.ipynb' \
        -not -path '*/.ipynb_checkpoints/*' \
        -not -path '*/_proc/*' \
        -newer "$TIMESTAMP_FILE" 2>/dev/null | sort) || true
else
    # First run: notebooks modified in the last 5 minutes
    MODIFIED=$(find "$NBS_DIR" -name '*.ipynb' \
        -not -path '*/.ipynb_checkpoints/*' \
        -not -path '*/_proc/*' \
        -mmin -5 2>/dev/null | sort) || true
fi

[[ -z "$MODIFIED" ]] && { mkdir -p "$(dirname "$TIMESTAMP_FILE")"; touch "$TIMESTAMP_FILE"; exit 0; }

# Pass data via environment variables to avoid shell injection
# (filenames with quotes/backslashes could break inline string interpolation)
OUTPUT=$(NB_MARKER="$MARKER" NB_FILES="$MODIFIED" python3 -c '
import json, sys, os

marker = os.environ["NB_MARKER"]
files = os.environ["NB_FILES"].strip().split("\n")

output = []
for path in files:
    path = path.strip()
    if not path:
        continue
    try:
        with open(path, "r") as f:
            nb = json.load(f)
    except Exception:
        continue
    cells = nb.get("cells", [])
    name = os.path.basename(path)
    for idx, cell in enumerate(cells):
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        if marker not in source:
            continue
        ct = cell.get("cell_type", "unknown").upper()
        # Classify
        tag = ""
        if ct == "CODE":
            for line in source.split("\n"):
                s = line.strip()
                if s.startswith("#|"):
                    d = s[2:].strip()
                    if d.startswith("export"):
                        tag = " (export)"
                        break
                elif s and not s.startswith("#"):
                    tag = " (test)"
                    break
            if not tag:
                tag = " (test)"
        header = f"=== {name} ({len(cells)} cells) ==="
        cell_header = f"[{idx}] {ct}{tag}"
        lines = [cell_header]
        for i, line in enumerate(source.split("\n"), 1):
            lines.append(f"    {i:3d}  {line}")
        output.append(header + "\n\n" + "\n".join(lines))

if output:
    print("\n\n".join(output))
' 2>/dev/null) || true

if [[ -n "$OUTPUT" ]]; then
    echo "<flagged-notebook-cells>"
    echo "Cells flagged with \"$MARKER\" in modified notebooks."
    echo "The human is asking for your attention on these specific cells."
    echo ""
    printf '%s' "$OUTPUT"
    echo ""
    echo "</flagged-notebook-cells>"
fi

# Update timestamp for next run
mkdir -p "$(dirname "$TIMESTAMP_FILE")"
touch "$TIMESTAMP_FILE"
