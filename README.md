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

## Quick start

Install into an existing nbdev project:

```bash
# Preview what will be installed
uvx nbdev-mcp init /path/to/project --dry-run

# Install
uvx nbdev-mcp init /path/to/project

# Overwrite existing files
uvx nbdev-mcp init /path/to/project --force
```

This copies the skill, CLAUDE.md, hooks, and settings into `.claude/`, creates `.mcp.json` with the nbdev MCP server (and optionally jupyter-mcp for live collaboration), patches `pyproject.toml` with Jupyter dependencies, and updates `.gitignore`.

Then start Claude Code in your project — the skill loads automatically when working with `.ipynb` files.

## Using the skills standalone

The skills in `.claude/skills/` work without the MCP server. Copy them into any nbdev project's `.claude/skills/` directory:

```bash
cp -r .claude/skills/nbdev /path/to/project/.claude/skills/
cp -r .claude/skills/fastcore /path/to/project/.claude/skills/
```

Claude Code will load them when relevant based on the skill description.

## Repository structure

```
nbdev-cc/
├── .claude/skills/          # Skills (also bundled in the package)
│   ├── nbdev/               # nbdev development skill + references
│   └── fastcore/            # fastcore API skill + references
└── packages/
    └── nbdev-mcp/           # Installable package
        ├── src/nbdev_mcp/
        │   ├── cli.py       # Entry point: `nbdev-mcp` / `nbdev-mcp init`
        │   ├── init.py      # Project setup logic
        │   ├── server.py    # MCP server (FastMCP)
        │   ├── tools/       # Tool implementations
        │   └── assets/      # Files copied by `init`
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
