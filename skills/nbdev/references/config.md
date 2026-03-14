# settings.ini Configuration Reference

All nbdev configuration lives in `settings.ini` at the project root, using Python's [ConfigParser](https://docs.python.org/3/library/configparser.html) format. Users can also set global defaults in `~/.config/nbdev/settings.ini`.

---

## Repository Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `repo` | Repository name | — |
| `branch` | Default branch | None |
| `user` | Repository owner (GitHub username or org) | — |
| `git_url` | Repository URL | `https://github.com/%(user)s/%(repo)s` |

---

## Package Information

| Setting | Description | Default |
|---------|-------------|---------|
| `lib_name` | Package name (used in imports) | repo name |
| `version` | Release version | 0.0.1 |
| `min_python` | Minimum Python version | 3.7 |
| `license` | Package license | apache2 |
| `author` | Package author's name | — |
| `author_email` | Author's email address | — |
| `description` | Package summary (one line) | — |
| `keywords` | Package keywords | `nbdev jupyter notebook python` |
| `copyright` | Copyright notice | — |

---

## Paths

| Setting | Description | Default |
|---------|-------------|---------|
| `nbs_path` | Source notebooks directory | `nbs` |
| `lib_path` | Generated Python package root | repo name (hyphens → underscores) |
| `doc_path` | Rendered documentation output | `_docs` |

---

## Documentation

| Setting | Description | Default |
|---------|-------------|---------|
| `doc_host` | Docs hostname | `https://%(user)s.github.io` |
| `doc_baseurl` | Docs base URL path | `/%(repo)s` |
| `title` | Quarto website title | lib_name |
| `readme_nb` | Notebook exported as README.md | `index.ipynb` |
| `custom_sidebar` | Use custom `sidebar.yml` instead of auto-generated | False |

---

## Processing Options

| Setting | Description | Default |
|---------|-------------|---------|
| `tst_flags` | Test flags separated by `\|` (e.g., `slow\|cuda`) | `notest` |
| `recursive` | Include subfolders when globbing notebooks | True |
| `black_formatting` | Format generated modules with black | False |
| `clean_ids` | Remove cell IDs from plaintext representations | True |
| `clear_all` | Remove cell metadata and outputs on clean | False |
| `put_version_in_init` | Add `__version__` to `__init__.py` | True |
| `jupyter_hooks` | Run Jupyter hooks | False |
| `skip_procs` | Processors to skip (comma-separated) | — |

---

## Metadata Preservation

By default, `nbdev_clean` strips most cell and notebook metadata. Use these to preserve specific keys:

| Setting | Description | Default |
|---------|-------------|---------|
| `allowed_metadata_keys` | Notebook-level metadata keys to preserve | — |
| `allowed_cell_metadata_keys` | Cell-level metadata keys to preserve | — |

---

## PyPI Classifiers

| Setting | Description | Default |
|---------|-------------|---------|
| `status` | Development status (1–5) | 3 |
| `audience` | Intended audience | Developers |
| `language` | Language | English |

---

## Console Scripts

Define CLI entry points:

```ini
console_scripts = my_tool=my_project.cli:main
```

Multiple scripts use newline continuation:

```ini
console_scripts =
    my_tool=my_project.cli:main
    my_other=my_project.other:run
```

---

## Complete Example

```ini
[DEFAULT]
# Repository
repo = my-project
user = myusername
branch = main

# Package
lib_name = my_project
version = 0.1.0
min_python = 3.8
license = apache2

# Author
author = My Name
author_email = me@example.com
description = A great nbdev project
keywords = nbdev jupyter data science

# Paths
nbs_path = nbs
lib_path = my_project
doc_path = _docs

# Documentation
doc_host = https://%(user)s.github.io
doc_baseurl = /%(repo)s
readme_nb = index.ipynb

# Testing
tst_flags = slow|cuda

# Processing
black_formatting = False
recursive = True
put_version_in_init = True

# Console scripts
console_scripts = my_tool=my_project.cli:main
```

---

## Setup Methods

### From scratch

```bash
uv run nbdev_create_config --lib_name myproject --user myusername
```

### From existing repo (auto-detects settings)

```bash
uv run nbdev_new
```
