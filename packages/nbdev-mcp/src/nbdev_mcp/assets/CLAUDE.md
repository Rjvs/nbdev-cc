# Project Instructions

This is an nbdev project. Notebooks in `nbs/` are the source of truth.
Generated `.py` files are outputs — never edit them directly.

IMPORTANT: Do NOT use generic tools (`Read`, `Grep`, `Edit`, `Write`) on `.ipynb` files. Notebooks are structured JSON — generic tools produce broken, unreadable results. Use notebook-aware tools instead:

- Do NOT use `Read` or `cat` on `.ipynb` — use MCP `nb_read` or jupyter-mcp `read_notebook`
- Do NOT use `Grep` or `grep` on `.ipynb` — use MCP `nb_search`
- Do NOT use `Edit` or `Write` on `.ipynb` — use jupyter-mcp `overwrite_cell_source` or MCP `nb_edit`
- Do NOT write Python scripts to parse/edit notebooks — the MCP tools already handle this

Both `nbdev` and `jupyter-mcp` MCP servers provide notebook tools. Use jupyter-mcp for live editing/execution and nbdev MCP tools when they're more efficient:

| Operation | Use this | Why it's better |
|-----------|----------|-----------------|
| Search across notebooks | `nb_search` (nbdev MCP) | jupyter-mcp has no search tool |
| Quick-read a notebook | `nb_read` (nbdev MCP) | Faster than `use_notebook` + `read_notebook` |
| Batch execute cells | `nb_run` (nbdev MCP) | One call vs many `execute_cell` calls |
| Create a new notebook | `nb_create` (nbdev MCP) | Correct metadata, unique cell IDs |
| Validate before commit | `nb_validate` (nbdev MCP) | Catches structural errors |
| Edit cells (live session) | `overwrite_cell_source` (jupyter-mcp) | Real-time sync with browser |
| Execute cells (live session) | `execute_cell` (jupyter-mcp) | Runs in the live kernel |
| Add/remove cells (live) | `insert_cell` / `delete_cell` (jupyter-mcp) | Syncs instantly |

Generic tools (`Read`, `Edit`, `Grep`) are the last resort — only for non-notebook files or debugging raw JSON structure. See `references/collaboration.md` for tool workflows and troubleshooting.

## Development Rules

1. **Edit notebooks, not `.py` files** — generated modules are overwritten on export
2. **Run `uv run nbdev_prepare` before every commit** — exports, tests, and cleans in one step
3. **Notebooks tell a story** — cells build understanding progressively; prose between code explains the *why*
4. **One concept per cell** — split complex logic across cells with explanation between them
5. **Use `@patch`** to split class definitions across cells with prose between methods
6. **Fix in place** — when a cell has an error, fix it rather than appending a new one
7. **Use `test_eq` over `assert`** — `test_eq(a, b)` shows both values on failure
8. **Document parameters with docments** — inline comments in signatures, not docstring param sections
9. **Use `@delegates`** to pass parameters through to wrapped functions
10. **Keep imports in their own cell** — separate from export cells

See the **nbdev** skill for philosophy, patterns, and detailed reference.

## The `todo:` Marker

A hook runs on every prompt and injects cells flagged with `todo:` from recently-modified notebooks.

**Code cells** — `# todo: message`:
```python
# todo: should this use async?
def connect(host: str, port: int = 5432): ...
```

**Markdown cells** — `todo: message` on its own line:
```markdown
todo: is this explanation clear enough?

The `connect` function establishes a TCP connection...
```

You see flagged cells in `<flagged-notebook-cells>` tags. If no tags appear, nothing was flagged. Address the `todo:` message directly, read surrounding cells for context if needed, and remove the `todo:` comment when done.

## Quick Reference

```bash
# Setup (once after clone)
uv run nbdev_install_hooks
uv run nbdev_export

# Before every commit
uv run nbdev_prepare

# Testing
uv run nbdev_test                          # All notebooks
uv run nbdev_test --path nbs/00_core.ipynb # Single notebook
uv run nbdev_test --flags slow             # Include slow tests
```

| Path | Contents |
|------|----------|
| `nbs/` | Source notebooks (the source of truth) |
| `nbs/index.ipynb` | Becomes README.md and docs homepage |
| `settings.ini` | nbdev configuration |
