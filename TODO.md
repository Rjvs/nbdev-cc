# TODO

## Status: Early alpha (v0.1.0)

The core plugin works — 8 MCP tools, nbdev/fastcore skills, CLAUDE.md, hooks, and `init` command are all functional. The official Claude Code plugin structure (`.claude-plugin/plugin.json`, `skills/`, `hooks/hooks.json`, `.mcp.json`) is in place. The gaps below are what's needed to make this a reliable, publishable plugin.

---

## Testing

- [ ] **No tests exist.** Need tests for every tool (`nb_read`, `nb_edit`, `nb_create`, `nb_validate`, `nb_cells`, `nb_search`, `nb_run`, `nb_mcp_url`)
- [ ] Need tests for `init.py` — asset copying, `.mcp.json` merging, `pyproject.toml` patching, `.gitignore` patching, `--dry-run`, `--force`
- [ ] Need tests for `_common.py` — `load_notebook`, `save_notebook`, `get_source`, `source_to_array`, `get_directives`, `classify_cell`, `generate_cell_id`, `find_notebooks`
- [ ] Need a test notebook fixture (`.ipynb` file with known content) for tool tests
- [ ] Need to decide on test framework — pytest is standard; add it to dev dependencies
- [ ] Hook tests — at least validate `session-start.sh` and `auto-read-notebooks.sh` are syntactically valid bash (`bash -n`)

## Plugin format & distribution

Plugin structure is in place (`.claude-plugin/plugin.json`, `skills/`, `hooks/hooks.json`, `.mcp.json`). Remaining:

- [x] ~~Create `.claude-plugin/plugin.json` manifest~~
- [x] ~~Restructure to match plugin layout — `skills/`, `hooks/hooks.json`, `.mcp.json` at plugin root~~
- [x] ~~Move hooks to `hooks.json` format with `${CLAUDE_PLUGIN_ROOT}` paths~~
- [ ] **Decide on distribution model**: marketplace, PyPI (for MCP server only), or both
- [ ] **Submit to official marketplace** at `github.com/anthropics/claude-plugins-official` once stable
- [ ] **Keep `init` command?** — may still be useful for projects that want to vendor the files rather than use plugin install, or for injecting project-specific config
- [ ] **Deduplicate skills** — skills now exist in 3 places: `skills/` (plugin root), `.claude/skills/` (repo-local), `packages/nbdev-mcp/src/nbdev_mcp/assets/` (bundled in package). Should be one source of truth with symlinks or a build step
- [ ] Run `claude plugin validate .` to check the plugin structure
- [ ] Test with `claude --plugin-dir .` to verify loading

## Packaging (PyPI)

- [ ] **Not published to PyPI.** `uvx nbdev-mcp` won't work until published
- [ ] Add `[project.urls]` to `pyproject.toml` (homepage, repository, issues)
- [ ] Add `[project.readme]` and `[project.classifiers]` to `pyproject.toml`
- [ ] Add a `py.typed` marker if we want type checking support
- [ ] Consider whether `mcp>=1.0` is the right dependency pin (currently the only dep)
- [ ] The `nb_run` tool requires `nbformat` and `nbclient` at runtime in the *target project* — document this or handle the import error more gracefully

## init command improvements

- [x] ~~`init` doesn't install the fastcore skill — only the nbdev skill is in assets~~
- [x] ~~`init` has a bug: `while` condition contradicts itself (always false)~~
- [ ] `init` doesn't validate that the target is actually an nbdev project (no check for `settings.ini` or `nbs/`)
- [ ] No `uninstall` or `update` command — if the plugin evolves, users have no clean upgrade path
- [ ] `init` always installs jupyter-mcp config even if the user doesn't want live collaboration
- [ ] No `--no-jupyter` flag to skip jupyter-mcp setup

## MCP server

- [ ] No error handling around `mcp.run()` in `cli.py` — if FastMCP fails to start, the error may be opaque
- [ ] `nb_run` builds a large inline Python script string — fragile, hard to test, and the f-string interpolation is complex. Consider extracting to a standalone script file
- [ ] `nb_cells` dispatches on `action` string — could use sub-tools or better validation
- [ ] No logging — hard to debug when tools return unexpected results
- [ ] `nb_edit` and `nb_cells` share a `_parse_spec` function but have independent implementations — should share from `_common.py`

## CLAUDE.md template

- [ ] Template says "This is an nbdev project" but it's installed into every project regardless
- [ ] Template references paths like `nbs/` which may not match the target project's `nbs_path` setting
- [ ] Template should be parameterized by `init` (at minimum: lib name, nbs path)

## Hooks

- [ ] `session-start.sh` installs quarto unconditionally — this is slow and may not be needed for all projects
- [ ] `session-start.sh` has no idempotency check — if run multiple times it re-does everything
- [ ] `auto-read-notebooks.sh` uses inline Python with string interpolation (`$MODIFIED` injected into Python string) — this breaks if filenames contain quotes or special characters
- [ ] `auto-read-notebooks.sh` hardcodes `maxdepth 2` — deeply nested notebook directories will be missed

## Documentation

- [ ] No CHANGELOG
- [ ] No CONTRIBUTING guide
- [ ] No examples or demo project showing the plugin in action
- [ ] No docs on how to develop/modify the skills themselves

## CI/CD

- [ ] No GitHub Actions workflows
- [ ] No automated testing on PR
- [ ] No automated PyPI publishing
- [ ] No linting (ruff, mypy, etc.)

## Future ideas

- [ ] `nbdev-mcp check` command — run `nb_validate` on all notebooks from CLI
- [ ] `nbdev-mcp doctor` command — diagnose common setup issues
- [ ] Support for custom skill extensions (user-defined reference files)
- [ ] Integration testing with a real nbdev project
- [ ] Consider making tools work without MCP (direct CLI: `nbdev-mcp read nbs/00_core.ipynb --outline`)
