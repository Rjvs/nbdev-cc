# TODO

## Status: Early alpha (v0.1.0)

The core plugin works — 8 MCP tools, nbdev/fastcore skills, hooks, and `init` command are functional. The official Claude Code plugin structure (`.claude-plugin/plugin.json`, `skills/`, `hooks/hooks.json`, `.mcp.json`) is in place. The gaps below are what's needed to make this reliable and publishable.

---

## Bugs & correctness issues

These should be fixed before any release.

- [ ] **`generate_cell_id` is not deterministic** (`_common.py:87`): Docstring says "deterministic" but the seed includes `time.time_ns()`, making IDs different on every call. This breaks reproducibility and would make tests flaky. Remove the timestamp or rename to drop the "deterministic" claim.
- [ ] **`_parse_spec` is copy-pasted** between `create.py:59` and `cells.py:16` — identical 30-line function. Move to `_common.py`.
- [ ] **`nb_run` falls back to `sys.executable`** (`run.py:58`): The MCP server runs in its own uvx sandbox, so `sys.executable` is the MCP server's Python, not the project's. The fallback should try `python3` or `python` from PATH instead.
- [ ] **`nb_create` hardcodes Python 3.11.0** in notebook metadata (`create.py:48`): `'version': '3.11.0'` is baked into every created notebook regardless of the actual Python version. Either detect it or omit the field.
- [ ] **`save_notebook` may produce noisy diffs against nbdev** (`_common.py:16`): Uses `indent=1` (correct) but doesn't set `sort_keys=True`, which nbdev does. Notebooks saved by the MCP tools will have different key ordering than `nbdev_export`, causing spurious git diffs.
- [ ] **`nb_cells` action dispatching is in `server.py`** (`server.py:113-137`): Business logic (action routing, parameter validation, error messages) lives in the server layer instead of the tool module. Should be a single `nb_cells()` dispatcher in `cells.py`.
- [ ] **`_make_diff` is naive** (`edit.py:40-60`): Line-by-line positional comparison — if lines are inserted or deleted, all subsequent lines show as changed. Consider using `difflib`.

## Shell injection & security

- [ ] **`auto-read-notebooks.sh` has shell injection** (lines 54-55): `$MODIFIED` (filenames from `find`) is interpolated into a Python triple-quoted string `'''$MODIFIED'''`. Filenames containing quotes, backslashes, or triple-quotes will break or execute arbitrary code. Use a temporary file or pass filenames via environment variable.
- [ ] **No path validation on MCP tool inputs**: All tools accept raw `path: str` with no sanitization. An MCP client could read/write files outside the project via path traversal (`../../etc/passwd`). Consider restricting paths to the project directory.
- [ ] **`nb_run` executes arbitrary notebook code**: Inherent to the tool's purpose, but there's no sandboxing, confirmation, or scope restriction. Document the security implications.

## `nb_run` tool

The entire tool is a ~190-line Python script built as an f-string (`run.py:104-292`). This is the weakest tool implementation.

- [ ] **Duplicates `get_source`, `get_directives`, `classify_cell`** from `_common.py` inside the generated script string. If the shared code is updated, `nb_run` will silently diverge.
- [ ] **F-string with double-braces everywhere** makes the script hard to read and maintain. Extract to a standalone `.py` file bundled as a package resource and executed via subprocess.
- [ ] **Can't be unit-tested** in its current form since it only runs as a subprocess.
- [ ] **Error messages reference `uv pip install`** but the user may not have uv.

## Skill deduplication

Skills exist in 3 separate locations with no single source of truth:

1. `skills/` — plugin root (used by `claude --plugin-dir`)
2. `.claude/skills/` — repo-local (used when developing this plugin itself)
3. `packages/nbdev-mcp/src/nbdev_mcp/assets/` — bundled in PyPI package (used by `init`)

- [ ] **Pick one canonical location** and derive the others. Options:
  - Make `skills/` the source of truth, symlink `.claude/skills/` to it, and have a build/sync step for `assets/`
  - Or remove `.claude/skills/` entirely since this repo should use its own plugin system
- [ ] **Verify content is identical** across all 3 copies — they may have already diverged

## Testing

- [ ] **No tests exist.** Need pytest tests for every tool (`nb_read`, `nb_edit`, `nb_create`, `nb_validate`, `nb_cells`, `nb_search`, `nb_run`, `nb_mcp_url`)
- [ ] Need tests for `init.py` — asset copying, `.mcp.json` merging, `pyproject.toml` patching, `.gitignore` patching, `--dry-run`, `--force`
- [ ] Need tests for `_common.py` — `load_notebook`, `save_notebook`, `get_source`, `source_to_array`, `get_directives`, `classify_cell`, `generate_cell_id`, `find_notebooks`
- [ ] Need a test notebook fixture (`.ipynb` file with known cells, directives, outputs) for tool tests
- [ ] Add pytest to dev dependencies in `pyproject.toml`
- [ ] Hook syntax validation — at least `bash -n` on `session-start.sh` and `auto-read-notebooks.sh`

## Hooks

- [ ] **`auto-read-notebooks.sh` runs on every prompt** via `UserPromptSubmit` — adds latency even when no notebooks are modified. The fast-path exit exists but still runs `find` every time.
- [ ] `session-start.sh` installs quarto unconditionally — slow and may not be needed
- [ ] `session-start.sh` has no idempotency checks — re-does everything on every session start
- [ ] `session-start.sh` comment says "Copy to your project" (line 6-7) but this is now the plugin version, not a template — misleading
- [ ] `auto-read-notebooks.sh` hardcodes `maxdepth 2` — deeply nested notebook directories will be missed

## Plugin format & distribution

Plugin structure is in place. Remaining:

- [x] ~~Create `.claude-plugin/plugin.json` manifest~~
- [x] ~~Restructure to match plugin layout — `skills/`, `hooks/hooks.json`, `.mcp.json` at plugin root~~
- [x] ~~Move hooks to `hooks.json` format with `${CLAUDE_PLUGIN_ROOT}` paths~~
- [ ] **Decide on distribution model**: marketplace, PyPI (MCP server only), or both
- [ ] **Submit to marketplace** at `github.com/anthropics/claude-plugins-official` once stable
- [ ] **Keep `init` command?** — still useful for vendoring, but maintaining 3 copies of skills is expensive
- [ ] Run `claude plugin validate .` to check plugin structure
- [ ] Test with `claude --plugin-dir .` to verify loading end-to-end
- [ ] **`.mcp.json` references `uvx nbdev-mcp`** but the package isn't published to PyPI — MCP server won't start for plugin users until published

## Packaging (PyPI)

- [ ] **Not published to PyPI.** `uvx nbdev-mcp` won't work until published
- [ ] Add `[project.urls]` to `pyproject.toml` (homepage, repository, issues)
- [ ] Add `[project.readme]` and `[project.classifiers]` to `pyproject.toml`
- [ ] Consider whether `mcp>=1.0` is the right dependency pin (currently the only dep)
- [ ] The `nb_run` tool requires `nbformat` and `nbclient` at runtime in the *target project* — document this or handle the import error more gracefully

## init command improvements

- [x] ~~`init` doesn't install the fastcore skill — only the nbdev skill is in assets~~
- [x] ~~`init` has a bug: `while` condition contradicts itself (always false)~~
- [ ] `init` doesn't validate that the target is actually an nbdev project (no check for `settings.ini` or `nbs/`)
- [ ] No `uninstall` or `update` command — if the plugin evolves, users have no clean upgrade path
- [ ] `init` always installs jupyter-mcp config even if the user doesn't want live collaboration — add `--no-jupyter` flag
- [ ] `_patch_pyproject` section-header detection (`init.py:161`) may match TOML array literals (`[item]`) as section headers

## MCP server

- [ ] No error handling around `mcp.run()` in `cli.py` — if FastMCP fails to start, the error may be opaque
- [ ] No logging — hard to debug when tools return unexpected results
- [ ] `range` parameter shadows the Python built-in in `server.py` tool signatures (`nb_read`, `nb_run`) — `read.py` works around this with `_range = range` but it's fragile

## CLAUDE.md template

- [ ] Template says "This is an nbdev project" but it's installed into every project regardless
- [ ] Template references paths like `nbs/` which may not match the target project's `nbs_path` setting
- [ ] Template should be parameterized by `init` (at minimum: lib name, nbs path)

## Documentation & CI/CD

- [ ] No CHANGELOG
- [ ] No CONTRIBUTING guide
- [ ] No examples or demo project showing the plugin in action
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
- [ ] `classify_cell` doesn't handle less-common nbdev directives like `#| exec_doc` — extend if needed
