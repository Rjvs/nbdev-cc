# nbdev-mcp

MCP server and Claude Code plugin for [nbdev](https://nbdev.fast.ai/) notebook development.

## What it does

Gives Claude Code everything it needs to work effectively on nbdev projects:

- **8 MCP tools** for reading, editing, searching, creating, validating, and executing notebooks — without touching raw JSON
- **nbdev skill** — teaches Claude the literate programming philosophy, directives, `@patch`, testing patterns, project structure
- **fastcore skill** — reference for `@patch`, `store_attr`, `@delegates`, `L`, `@typedispatch`, and other utilities
- **CLAUDE.md** — project-level instructions covering tool selection, development rules, and the `todo:` marker system
- **Hooks** — `SessionStart` installs dependencies in remote/web environments; `UserPromptSubmit` surfaces `todo:`-flagged notebook cells

## Install

```bash
uvx nbdev-mcp init /path/to/project
```

This installs everything into the target project:

| Destination | Contents |
|-------------|----------|
| `.claude/skills/nbdev/` | Skill + reference docs |
| `.claude/CLAUDE.md` | Tool selection rules, dev workflow, `todo:` system |
| `.claude/settings.json` | Hook registration |
| `.claude/hooks/` | `session-start.sh`, `auto-read-notebooks.sh` |
| `.mcp.json` | MCP server config (nbdev + jupyter-mcp) |
| `pyproject.toml` | Jupyter dependency group (patched) |
| `.gitignore` | `jupyter.log`, `.claude/.last-nb-read` (patched) |

Options:

```bash
uvx nbdev-mcp init /path --dry-run   # preview without changes
uvx nbdev-mcp init /path --force     # overwrite existing files
```

After init:

1. Edit `.claude/CLAUDE.md` to match your project
2. `uv sync --group jupyter` (if you want live Jupyter collaboration)
3. Start Claude Code in your project

## MCP tools

All tools are exposed via the `nbdev` MCP server (configured in `.mcp.json`).

| Tool | Purpose |
|------|---------|
| `nb_read` | Human-readable notebook viewer — outline, cell filtering, exports, tests |
| `nb_edit` | Find-and-replace within cells (by index or content match) |
| `nb_create` | Scaffold notebooks from spec files or module templates |
| `nb_validate` | Validate structure and nbdev conventions before commit |
| `nb_cells` | Bulk operations — insert, append, move, find, remove cells |
| `nb_search` | Search across notebooks for content, directives, or cell types |
| `nb_run` | Batch execute cells (all, up-to-N, range, single) in a fresh kernel |
| `nb_mcp_url` | Find running Jupyter server URL and token |

### Tool selection (nbdev MCP vs jupyter-mcp)

The plugin configures two MCP servers. Use each where it's strongest:

| Operation | Use | Why |
|-----------|-----|-----|
| Search across notebooks | `nb_search` | jupyter-mcp has no search |
| Quick-read a notebook | `nb_read` | Faster than `use_notebook` + `read_notebook` |
| Batch execute | `nb_run` | One call vs many `execute_cell` calls |
| Create new notebook | `nb_create` | Correct metadata, unique cell IDs |
| Validate before commit | `nb_validate` | Catches structural errors |
| Edit cells (live) | jupyter-mcp `overwrite_cell_source` | Real-time browser sync |
| Execute cells (live) | jupyter-mcp `execute_cell` | Runs in live kernel |

## .mcp.json

After init, your project gets:

```json
{
  "mcpServers": {
    "nbdev": {
      "command": "uvx",
      "args": ["nbdev-mcp"]
    },
    "jupyter-mcp": {
      "command": "uvx",
      "args": ["jupyter-mcp-server@latest"],
      "env": {
        "JUPYTER_URL": "${JUPYTER_URL:-http://localhost:8888}",
        "JUPYTER_TOKEN": "${JUPYTER_TOKEN}",
        "ALLOW_IMG_OUTPUT": "true"
      }
    }
  }
}
```

- **nbdev** MCP — file-based notebook tools (always works, no running Jupyter needed)
- **jupyter-mcp** — live collaboration with JupyterLab (requires running server + token)

## Hooks

### SessionStart (`session-start.sh`)

Runs when Claude Code starts in a remote/web environment. Installs `uv`, project dependencies, nbdev, quarto, git hooks, and exports modules so the project is ready to use.

Only runs when `CLAUDE_CODE_REMOTE=true` (web sessions). Does nothing locally.

### UserPromptSubmit (`auto-read-notebooks.sh`)

Runs on every prompt. Scans recently-modified notebooks for cells flagged with `todo:` and injects only those cells into the conversation. Avoids dumping entire notebooks into context.

Usage in notebooks:

```python
# Code cell
# todo: should this use async?
def connect(host: str, port: int = 5432): ...
```

```markdown
<!-- Markdown cell -->
todo: is this explanation clear enough?
```

## Manual MCP setup

If you only want the MCP tools without the full plugin:

```bash
claude mcp add nbdev -- uvx nbdev-mcp
```

## Development

```bash
cd packages/nbdev-mcp
uv sync
uv run nbdev-mcp              # start MCP server
uv run nbdev-mcp init /path   # test init
```
