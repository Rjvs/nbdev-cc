#!/bin/bash
# Session start hook for nbdev projects.
# Installs dependencies so nbdev commands, tests, and linters work in
# Claude Code on the web.
#
# Part of the nbdev-mcp plugin. Installed into target projects by
# `nbdev-mcp init` (copies to .claude/hooks/session-start.sh).
set -euo pipefail

# Only run in remote (web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# Idempotency: skip if already run this session
MARKER_FILE="$CLAUDE_PROJECT_DIR/.claude/.session-setup-done"
if [ -f "$MARKER_FILE" ]; then
  exit 0
fi

# Install uv if not present (fast Python package manager)
if ! command -v uv &> /dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
  export PATH="$HOME/.local/bin:$PATH"
fi

# Install project dependencies
if [ -f "pyproject.toml" ]; then
  uv sync
elif [ -f "settings.ini" ] && [ -f "setup.py" ]; then
  # Older nbdev projects without pyproject.toml
  uv pip install -e ".[dev]" 2>/dev/null || uv pip install -e .
fi

# Install nbdev if not already available
if ! uv run python -c "import nbdev" 2>/dev/null; then
  uv pip install nbdev 2>/dev/null || true
fi

# Install quarto only if the project has a _quarto.yml or docs-related config
if ! command -v quarto &> /dev/null; then
  if [ -f "_quarto.yml" ] || [ -f "nbs/_quarto.yml" ] || grep -q 'doc_path' settings.ini 2>/dev/null; then
    uv run nbdev_install_quarto 2>/dev/null || true
  fi
fi

# Install git hooks for notebook cleaning
uv run nbdev_install_hooks 2>/dev/null || true

# Export modules so imports work
uv run nbdev_export 2>/dev/null || true

# Set PYTHONPATH so the library is importable
echo "export PYTHONPATH=\"$CLAUDE_PROJECT_DIR:\$PYTHONPATH\"" >> "$CLAUDE_ENV_FILE"

# Mark setup as done for this session
mkdir -p "$(dirname "$MARKER_FILE")"
touch "$MARKER_FILE"

# Remind the agent about available notebook tools
echo ""
echo "Notebook MCP tools available:"
echo "  jupyter-mcp (live): use_notebook, read_notebook, overwrite_cell_source, execute_cell, insert_cell, delete_cell"
echo "  nbdev MCP (file):   nb_read, nb_search, nb_edit, nb_cells, nb_run, nb_create, nb_validate, nb_mcp_url"
echo ""
echo "Use jupyter-mcp tools by default for live editing and executing cells."
echo "Use nbdev MCP tools: nb_search for searching, nb_read for quick reads, nb_run for batch execution."
echo "If jupyter-mcp connection fails, use nb_mcp_url to check the Jupyter server URL and token."
