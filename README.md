# nbdev-cc

Claude Code plugin for [nbdev](https://nbdev.fast.ai/) projects.

Gives Claude Code deep understanding of nbdev's literate programming workflow — notebooks as source of truth, directives, exports, testing patterns, and fastcore utilities — plus MCP tools for reading, editing, searching, and executing notebooks without touching raw JSON.

## What's in the box

| Component | What it does |
|-----------|-------------|
| **nbdev skill** | Teaches Claude nbdev philosophy, directives, project structure, `@patch`, `@delegates`, testing patterns, and common workflows |
| **fastcore skill** | Reference for fastcore utilities (`@patch`, `store_attr`, `L`, `@delegates`, `@typedispatch`, etc.) |
| **CLAUDE.md** | Project-level instructions: tool selection rules, development workflow, `todo:` marker system |
| **MCP server** (8 tools) | `nb_read`, `nb_edit`, `nb_create`, `nb_validate`, `nb_cells`, `nb_search`, `nb_run`, `nb_mcp_url` |
| **Hooks** | `SessionStart` — installs deps in remote environments; `UserPromptSubmit` — surfaces `todo:`-flagged cells |
| **Settings** | Hook registration via `.claude/settings.json` |

## Install

### Option 1: Claude Code plugin (recommended)

Install as a Claude Code plugin — skills, hooks, and MCP tools load automatically:

```bash
# From a marketplace (once published):
claude plugin install nbdev

# From this repo directly:
claude --plugin-dir /path/to/nbdev-cc
```

### Option 2: Init into a project

Copy all plugin files directly into your project (vendors them, good for version control):

```bash
uvx nbdev-mcp init /path/to/project            # install
uvx nbdev-mcp init /path/to/project --dry-run   # preview
uvx nbdev-mcp init /path/to/project --force     # overwrite
```

This copies skills, CLAUDE.md, hooks, and settings into `.claude/`, creates `.mcp.json` with the nbdev MCP server (and jupyter-mcp for live collaboration), patches `pyproject.toml` with Jupyter dependencies, and updates `.gitignore`.

### Option 3: Skills only

Copy the skills without MCP tools or hooks:

```bash
cp -r skills/nbdev /path/to/project/.claude/skills/
cp -r skills/fastcore /path/to/project/.claude/skills/
```

Claude Code loads them automatically when working with `.ipynb` files.

## Repository structure

```
nbdev-cc/                        # This repo IS a Claude Code plugin
├── .claude-plugin/plugin.json   # Plugin manifest
├── skills/                      # Skills (auto-discovered by plugin system)
│   ├── nbdev/                   # nbdev development skill + references
│   └── fastcore/                # fastcore API skill + references
├── hooks/                       # Hooks (auto-discovered by plugin system)
│   ├── hooks.json               # Hook config with ${CLAUDE_PLUGIN_ROOT}
│   ├── session-start.sh         # Remote environment setup
│   └── auto-read-notebooks.sh   # todo: cell surfacing
├── .mcp.json                    # MCP server config (nbdev + jupyter-mcp)
└── packages/
    └── nbdev-mcp/               # PyPI package (MCP server + init command)
        ├── src/nbdev_mcp/
        │   ├── cli.py           # Entry point: `nbdev-mcp` / `nbdev-mcp init`
        │   ├── init.py          # Project setup (vendors assets)
        │   ├── server.py        # MCP server (FastMCP)
        │   ├── tools/           # Tool implementations
        │   └── assets/          # Files copied by `init`
        └── pyproject.toml
```

## Development

```bash
cd packages/nbdev-mcp
uv sync
uv run nbdev-mcp              # start MCP server
uv run nbdev-mcp init ../..   # test init on this repo
```

## License

Apache-2.0
