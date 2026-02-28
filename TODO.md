# TODO

## Status: Early alpha (v0.1.0)

The core plugin works — 8 MCP tools, nbdev/fastcore skills, hooks, and `init` command are functional. The official Claude Code plugin structure (`.claude-plugin/plugin.json`, `skills/`, `hooks/hooks.json`, `.mcp.json`) is in place. The gaps below are what's needed to make this reliable and publishable.

---

## Bugs & correctness issues

These should be fixed before any release.

- [x] **`generate_cell_id` is not deterministic** (`_common.py:87`): ~~Docstring says "deterministic" but the seed includes `time.time_ns()`, making IDs different on every call.~~ Removed timestamp from seed — IDs are now deterministic based on index and content.
- [x] **`_parse_spec` is copy-pasted** between `create.py:59` and `cells.py:16`: ~~identical 30-line function.~~ Moved to `_common.py` as `parse_spec()`, both modules now import it.
- [x] **`nb_run` falls back to `sys.executable`** (`run.py:58`): ~~The MCP server runs in its own uvx sandbox, so `sys.executable` is the MCP server's Python.~~ Fallback now tries `python3` then `python` from PATH.
- [x] **`nb_create` hardcodes Python 3.11.0** in notebook metadata (`create.py:48`): ~~`'version': '3.11.0'` baked in.~~ Now uses `platform.python_version()`.
- [x] **`save_notebook` may produce noisy diffs against nbdev** (`_common.py:16`): ~~Doesn't set `sort_keys=True`.~~ Added `sort_keys=True` to match nbdev's formatting.
- [x] **`nb_cells` action dispatching is in `server.py`** (`server.py:113-137`): ~~Business logic lived in the server layer.~~ Moved to `nb_cells_dispatch()` in `cells.py`.
- [x] **`_make_diff` is naive** (`edit.py:40-60`): ~~Line-by-line positional comparison.~~ Replaced with `difflib.unified_diff`.

## Shell injection & security

- [x] **`auto-read-notebooks.sh` has shell injection** (lines 54-55): ~~`$MODIFIED` interpolated into a Python triple-quoted string.~~ Now passes data via environment variables (`NB_MARKER`, `NB_FILES`) and uses single-quoted Python to prevent shell interpolation.
- [x] **No path validation on MCP tool inputs**: ~~All tools accept raw `path: str` with no sanitization.~~ Added `validate_notebook_path()` and `validate_path()` helpers to `_common.py`. All tools now validate `.ipynb` extension and reject paths outside the project directory.
- [x] **`nb_run` executes arbitrary notebook code**: ~~No documentation of security implications.~~ Added security documentation to both the module docstring and the tool function docstring.

## `nb_run` tool

~~The entire tool is a ~190-line Python script built as an f-string (`run.py:104-292`). This is the weakest tool implementation.~~

- [x] **Duplicates `get_source`, `get_directives`, `classify_cell`** from `_common.py` inside the generated script string. ~~If the shared code is updated, `nb_run` will silently diverge.~~ Extracted to standalone `_runner.py` file — a proper Python module with its own utility functions, invoked via `subprocess.run(['python', _runner.py, ...])` instead of `python -c <f-string>`.
- [x] **F-string with double-braces everywhere** makes the script hard to read and maintain. ~~Extract to a standalone `.py` file bundled as a package resource and executed via subprocess.~~ Done — `_runner.py` is a clean, readable Python script with no f-string escaping.
- [x] **Can't be unit-tested** in its current form since it only runs as a subprocess. ~~`_runner.py` functions (`get_source`, `classify_cell`, `format_outputs`, etc.) can now be imported and tested directly.~~
- [x] **Error messages reference `uv pip install`** but the user may not have uv. ~~Now shows generic `pip install nbformat nbclient` with `uv add` as an alternative.~~

## Skill deduplication

Skills exist in 3 separate locations with no single source of truth:

1. `skills/` — plugin root (used by `claude --plugin-dir`)
2. `.claude/skills/` — repo-local (used when developing this plugin itself)
3. `packages/nbdev-mcp/src/nbdev_mcp/assets/` — bundled in PyPI package (used by `init`)

- [x] **Verify content is identical** across all 3 copies — ~~they may have already diverged~~ Verified: all files are byte-identical across all 3 locations.
- [ ] **Pick one canonical location** and derive the others. Options:
  - Make `skills/` the source of truth, symlink `.claude/skills/` to it, and have a build/sync step for `assets/`
  - Or remove `.claude/skills/` entirely since this repo should use its own plugin system

## Testing

- [ ] **No tests exist.** Need pytest tests for every tool (`nb_read`, `nb_edit`, `nb_create`, `nb_validate`, `nb_cells`, `nb_search`, `nb_run`, `nb_mcp_url`)
- [ ] Need tests for `init.py` — asset copying, `.mcp.json` merging, `pyproject.toml` patching, `.gitignore` patching, `--dry-run`, `--force`
- [ ] Need tests for `_common.py` — `load_notebook`, `save_notebook`, `get_source`, `source_to_array`, `get_directives`, `classify_cell`, `generate_cell_id`, `find_notebooks`
- [ ] Need a test notebook fixture (`.ipynb` file with known cells, directives, outputs) for tool tests
- [ ] Add pytest to dev dependencies in `pyproject.toml`
- [ ] Hook syntax validation — at least `bash -n` on `session-start.sh` and `auto-read-notebooks.sh`

## Hooks

- [x] `session-start.sh` installs quarto unconditionally — ~~slow and may not be needed~~ Now only installs quarto if project has `_quarto.yml` or `doc_path` in `settings.ini`.
- [x] `session-start.sh` has no idempotency checks — ~~re-does everything on every session start~~ Added marker file `.claude/.session-setup-done` that's checked on entry; skips entire setup if already done.
- [x] `session-start.sh` comment says "Copy to your project" (line 6-7) — ~~misleading~~ Updated comment to describe plugin provenance.
- [x] `auto-read-notebooks.sh` hardcodes `maxdepth 2` — ~~deeply nested notebook directories will be missed~~ Removed `maxdepth` limit; now searches all depths.
- [ ] **`auto-read-notebooks.sh` runs on every prompt** via `UserPromptSubmit` — adds latency even when no notebooks are modified. The fast-path exit exists but still runs `find` every time.

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
- [x] Add `[project.urls]` to `pyproject.toml` (homepage, repository, issues) — ~~Done~~
- [x] Add `[project.readme]` and `[project.classifiers]` to `pyproject.toml` — ~~Done~~
- [ ] Consider whether `mcp>=1.0` is the right dependency pin (currently the only dep)
- [x] The `nb_run` tool requires `nbformat` and `nbclient` at runtime in the *target project* — ~~document this or handle the import error more gracefully~~ `_runner.py` now shows clear install instructions (`pip install` and `uv add`).

## init command improvements

- [x] ~~`init` doesn't install the fastcore skill — only the nbdev skill is in assets~~
- [x] ~~`init` has a bug: `while` condition contradicts itself (always false)~~
- [x] `init` doesn't validate that the target is actually an nbdev project — ~~no check for `settings.ini` or `nbs/`~~ Now warns (but doesn't block) if neither `settings.ini` nor `nbs/` directory is found.
- [ ] No `uninstall` or `update` command — if the plugin evolves, users have no clean upgrade path
- [ ] `init` always installs jupyter-mcp config even if the user doesn't want live collaboration — add `--no-jupyter` flag
- [x] `_patch_pyproject` section-header detection (`init.py:161`) may match TOML array literals — ~~`[item]` as section headers~~ Now uses regex `_TOML_SECTION_RE` that requires bare keys and rejects quoted values.

## MCP server

- [x] No error handling around `mcp.run()` in `cli.py` — ~~if FastMCP fails to start, the error may be opaque~~ Added try/except with clear error message.
- [ ] No logging — hard to debug when tools return unexpected results
- [x] `range` parameter shadows the Python built-in in `server.py` tool signatures — ~~`read.py` works around this with `_range = range` but it's fragile~~ Documented in `server.py` module docstring; left as-is since renaming would break the MCP API and the shadow is harmless in the thin wrapper functions.

## CLAUDE.md template

- [x] Template says "This is an nbdev project" but it's installed into every project regardless — ~~Still says "nbdev project" but~~ `init` now warns if target doesn't look like an nbdev project.
- [x] Template references paths like `nbs/` which may not match the target project's `nbs_path` setting — ~~Now uses `{{NBS_PATH}}` placeholder filled from `settings.ini`.~~
- [x] Template should be parameterized by `init` (at minimum: lib name, nbs path) — ~~Done. `init` reads `settings.ini` and fills `{{NBS_PATH}}` and `{{LIB_NAME}}` via `_render_template()`.~~

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
