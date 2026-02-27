# nbdev CLI Commands Reference

Use `uv run` to execute nbdev commands.  All nbdev commands start with `nbdev_`, so the first part of any command is `uv run nbdev_` e.g. `uv run nbdev_clean`. Run any command with `--help` for detailed options.

Commands must be run from within the project directory (or a subdirectory, such as the `nbs` subdir) - they locate `settings.ini` by searching parent directories.

---

## Essential Commands

### `nbdev_prepare`

**The most important command** - run before every commit.

```bash
nbdev_prepare
```

Performs:
1. `nbdev_export` - Export notebooks to Python modules
2. `nbdev_test` - Run all tests
3. `nbdev_clean` - Clean notebook metadata
4. Render README if needed

### `nbdev_export`

Export notebooks to Python modules.

```bash
nbdev_export                    # Export all notebooks
nbdev_export --path nbs/core.ipynb  # Export specific notebook
```

- Creates/updates files in `lib_path`
- Updates `__init__.py` with exports
- Only processes cells with `#| export` directives

### `nbdev_test`

Run tests in notebooks.

```bash
nbdev_test                      # Test all notebooks
nbdev_test --path nbs/core.ipynb    # Test specific notebook
nbdev_test --flags "slow"       # Include slow tests
nbdev_test --flags "slow|cuda"  # Include multiple flags
nbdev_test --n_workers 4        # Parallel testing
nbdev_test --pause 0.5          # Pause between tests (seconds)
```

Tests are all non-exported code cells. They run in order within each notebook.

### `nbdev_docs`

Generate Quarto documentation.

```bash
nbdev_docs                      # Generate all docs
nbdev_docs --path nbs/core.ipynb    # Generate for specific notebook
```

Creates documentation in `doc_path` (default: `_docs`).

### `nbdev_preview`

Preview documentation locally.

```bash
nbdev_preview                   # Start local preview server
```

Opens browser with live-reloading documentation preview.

---

## Project Setup Commands

### `nbdev_new`

Create a new nbdev project.

```bash
nbdev_new                       # Interactive setup
```

Creates:
- `settings.ini` configuration
- `nbs/` directory with index notebook
- `.github/workflows/` for CI/CD
- Basic project structure

### `nbdev_create_config`

Create or update `settings.ini`.

```bash
nbdev_create_config --lib_name myproject --user myusername
```

Key options:
- `--lib_name` - Package name
- `--user` - GitHub username
- `--author` - Author name
- `--description` - Package description
- `--nbs_path` - Notebooks directory
- `--lib_path` - Generated library directory

### `nbdev_install_hooks`

Install git hooks for notebook cleaning.

```bash
nbdev_install_hooks
```

Installs:
- Pre-commit hook to clean notebooks
- Merge driver for notebook conflicts
- Trust hooks for notebook security

**Run this once after cloning a project.**

### `nbdev_install_quarto`

Install Quarto (required for documentation).

```bash
nbdev_install_quarto            # macOS/Linux
```

Windows users should install Quarto manually from quarto.org.

---

## Notebook Maintenance Commands

### `nbdev_clean`

Clean notebook metadata to prevent merge conflicts.

```bash
nbdev_clean                     # Clean all notebooks
nbdev_clean --path nbs/core.ipynb   # Clean specific notebook
```

Removes:
- Execution counts
- Cell outputs (optional)
- Unnecessary metadata

### `nbdev_trust`

Trust notebooks (mark as safe to execute).

```bash
nbdev_trust                     # Trust all notebooks
nbdev_trust --path nbs/core.ipynb   # Trust specific notebook
```

### `nbdev_fix`

Fix merge conflicts in notebooks.

```bash
nbdev_fix nbs/conflicted.ipynb
```

Creates a working notebook from a conflicted one. Manual review still recommended.

### `nbdev_merge`

Git merge driver for notebooks.

```bash
# Usually configured automatically via nbdev_install_hooks
# Manual usage:
git config merge.nbdev.driver "nbdev_merge %O %A %B %P"
```

---

## Sync Commands

### `nbdev_update`

Sync changes from `.py` files back to notebooks.

```bash
nbdev_update                    # Update all
nbdev_update --path lib/core.py     # Update from specific module
```

Use when you've edited the generated Python files directly (not recommended, but sometimes necessary).

### `nbdev_migrate`

Migrate from nbdev v1 to v2.

```bash
nbdev_migrate                   # Migrate all files
```

Converts:
- `#export` to `#| export`
- Old directive syntax to new
- Updates configuration

---

## Documentation Commands

### `nbdev_sidebar`

Generate sidebar navigation.

```bash
nbdev_sidebar
```

Creates `_quarto.yml` sidebar from notebook structure.

### `nbdev_filter`

Quarto filter for notebook processing.

```bash
# Usually called automatically by Quarto
quarto render --filter nbdev_filter
```

### `nbdev_readme`

Generate README.md from index notebook.

```bash
nbdev_readme
```

Converts `nbs/index.ipynb` to `README.md`.

---

## Publishing Commands

### `nbdev_pypi`

Publish package to PyPI.

```bash
nbdev_pypi                      # Publish to PyPI
nbdev_pypi --repository testpypi    # Publish to Test PyPI
```

Requires:
- `~/.pypirc` with credentials
- or `TWINE_USERNAME`/`TWINE_PASSWORD` environment variables

### `nbdev_conda`

Create conda package.

```bash
nbdev_conda                     # Create meta.yaml
nbdev_conda --build             # Build package
nbdev_conda --upload            # Upload to anaconda.org
```

### `nbdev_bump_version`

Increment version number.

```bash
nbdev_bump_version              # Increment patch version
nbdev_bump_version --part minor     # Increment minor version
nbdev_bump_version --part major     # Increment major version
```

Updates `settings.ini` and `_version.py`.

### `nbdev_changelog`

Generate changelog from GitHub issues.

```bash
nbdev_changelog
```

Creates/updates `CHANGELOG.md` from closed GitHub issues.

---

## Utility Commands

### `nbdev_help`

Show all available commands.

```bash
nbdev_help
```

### `nbdev_install`

Install Quarto and the current library.

```bash
nbdev_install                   # Full installation
```

Combines `nbdev_install_quarto` and `pip install -e .`

### `nbdev_update_license`

Update project license.

```bash
nbdev_update_license --to mit
```

---

## Command Quick Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `nbdev_prepare` | Export + test + clean | Before every commit |
| `nbdev_export` | Generate .py files | After editing notebooks |
| `nbdev_test` | Run tests | Verify code works |
| `nbdev_docs` | Generate documentation | Before publishing docs |
| `nbdev_preview` | Preview docs locally | During docs development |
| `nbdev_clean` | Clean notebooks | Before commit (auto with hooks) |
| `nbdev_update` | Sync .py to notebooks | After editing .py files |
| `nbdev_new` | Create project | Starting new project |
| `nbdev_install_hooks` | Set up git hooks | After cloning project |

---

## Typical Workflows

### Daily Development

```bash
# Edit notebooks in Jupyter/VS Code
# Then:
nbdev_prepare
git add .
git commit -m "Add new feature"
```

### Running Specific Tests

```bash
# Test one notebook
nbdev_test --path nbs/00_core.ipynb

# Include slow tests
nbdev_test --flags slow

# Run with more workers
nbdev_test --n_workers 8
```

### Building Documentation

```bash
# Preview locally
nbdev_preview

# Generate final docs
nbdev_docs
```

### Publishing Release

```bash
nbdev_bump_version
nbdev_changelog
nbdev_prepare
git add . && git commit -m "Release v0.2.0"
git tag v0.2.0
git push && git push --tags
nbdev_pypi
```

---

## Troubleshooting

### "No module named 'your_package'"

```bash
pip install -e .
```

### Tests failing with import errors

```bash
nbdev_export
pip install -e .
```

### Merge conflicts in notebooks

```bash
nbdev_fix path/to/conflicted.ipynb
# or
git checkout --ours path/to/notebook.ipynb
nbdev_export  # Re-export your version
```

### Documentation not updating

```bash
nbdev_clean
nbdev_docs --force
```
