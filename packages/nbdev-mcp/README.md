# nbdev-mcp

MCP server and plugin for [nbdev](https://nbdev.fast.ai/) notebook development with [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

Exposes 8 notebook tools as first-class MCP tools, and bundles an nbdev skill, project configuration, and hooks for a complete development setup.

## Install into a project

```bash
uvx nbdev-mcp init /path/to/project          # install
uvx nbdev-mcp init /path/to/project --dry-run # preview
uvx nbdev-mcp init /path/to/project --force   # overwrite existing
```

This copies the nbdev skill, CLAUDE.md, hooks into your project and creates `.mcp.json` with both `nbdev` and `jupyter-mcp` servers configured.

## MCP Tools

| Tool | Description |
|------|-------------|
| `nb_read` | Human-readable notebook viewer (outline, cell filtering, exports, tests) |
| `nb_edit` | Find-and-replace within cells (by index or content match) |
| `nb_create` | Scaffold new nbdev notebooks from spec files or module templates |
| `nb_validate` | Validate notebook structure and nbdev conventions |
| `nb_cells` | Bulk operations: insert, append, move, find, remove cells |
| `nb_search` | Search across notebooks for content, directives, or cell types |
| `nb_run` | Batch execute cells (all, up-to-N, range, single) |
| `nb_mcp_url` | Find Jupyter server URL and token for MCP configuration |

## .mcp.json

After `init`, your project's `.mcp.json` will contain:

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

- **nbdev** MCP: File-based notebook tools (always available)
- **jupyter-mcp**: Live collaboration with JupyterLab (requires running Jupyter server)

## Manual MCP setup

If you prefer to set up the MCP server without running `init`:

```bash
claude mcp add nbdev -- uvx nbdev-mcp
```

## Development

```bash
cd packages/nbdev-mcp
uv sync
uv run nbdev-mcp  # start MCP server locally
```
