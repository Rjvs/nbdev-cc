# nbdev-mcp Tool Reference

19 tools across three groups, designed so their UX mirrors Claude's built-in tools (Read, Write, Edit, Bash, Glob, Grep).

## Quick Reference

| Tool | Built-in parallel | Description |
|---|---|---|
| **Jupyter** | | |
| `jupy_connect` | `Bash` | Connect/reconnect MCP to Jupyter server |
| `jupy_info` | `Read` (metadata) | Server URL, token, open notebooks, packages |
| `jupy_kernels` | `Glob` (discovery) | List available kernel specs |
| `jupy_install` | `Bash` | Install packages via uv |
| **Notebook** | | |
| `nb_open` | `Bash` (resource lifecycle) | Open notebook session — required before other nb_* ops |
| `nb_close` | `Bash` (resource lifecycle) | Close notebook and release resources |
| `nb_glob` | `Glob` | List .ipynb files at a path |
| `nb_read` | `Read` | Read notebook (full / outline / info / cell-partial modes) |
| `nb_grep` | `Grep` | Search notebooks — path scope: dir=all, file=one, file+cell=cell |
| `nb_create` | `Write` | Create a new empty notebook |
| `nb_run` | `Bash` | Execute cells (full / to-cell / range / single-cell modes) |
| `nb_kernel_restart` | `Bash` | Restart Jupyter kernel |
| **Cell** | | |
| `nb_edit` | `Edit` | Find-and-replace within a cell; supports insert and delete patterns |
| `nb_cell_move` | `Edit` (structural) | Move cell(s) to a new position |
| `nb_cell_copy` | `Edit` (structural) | Copy cell(s) to a new position |
| `nb_cell_add` | `Write` / `Edit` (insert) | Add a new cell to the notebook |
| `nb_cell_split` | `Edit` (structural) | Split one cell into two at a line number |
| `nb_cell_merge` | `Edit` (structural) | Merge multiple cells into one |
| `nb_cell_delete` | `Edit` (structural remove) | Remove a cell from the notebook |

---

## Group 1: Jupyter (Server-Level)

These four tools require a running Jupyter server. Call `jupy_connect` if others fail with a connection error.

---

### `jupy_connect` — *mirrors `Bash` (connection management)*

Connect or reconnect the MCP server to a running Jupyter server. Use when the connection drops, when switching projects, or when the Jupyter server URL/token changes. Normally established automatically on startup; this tool lets the agent re-establish it without restarting the MCP server.

```
url: str | None = None      # Jupyter server base URL (default: auto-detect from JUPYTER_URL env)
token: str | None = None    # Auth token (default: from JUPYTER_TOKEN env)
path: str | None = None     # Project path to help locate the right server (default: cwd)
```

Returns:
```
Connected to Jupyter server
  url:   http://localhost:8888
  token: abc123...
  root:  /home/user/myproject/nbs
```

---

### `jupy_info` — *mirrors `Read` (metadata mode)*

Get info about the running Jupyter server: base URL, token, root directory, open notebooks, and visible Python packages. Use to verify the environment or to construct Jupyter API URLs. Call `jupy_connect` first if this fails.

```
path: str | None = None   # Project path to match against (default: cwd)
```

Returns:
```
url:   http://localhost:8888
token: abc123...
root:  /home/user/myproject/nbs

Open notebooks (3):
  00_core.ipynb
  01_utils.ipynb
  02_api.ipynb

Python packages (selected):
  fastcore 1.7.8
  nbdev    2.3.13
  torch    2.2.0
```

---

### `jupy_kernels` — *conceptually like `Glob` (discovery listing), for kernel specs*

List available Jupyter kernel specs. Not a filesystem glob, but serves the same "what's available?" discovery role as `Glob`. Call before `nb_run` when you need to pick or verify a kernel.

```
path: str | None = None   # Project path to find the right Jupyter server (default: cwd)
```

Returns:
```
Available kernels:
  python3    Python 3 (ipykernel)  [default]
  pypy3      PyPy 3
  ir         R
```

---

### `jupy_install` — *mirrors `Bash` (package management)*

Install Python packages into the project environment using `uv`. Use `add=True` to also update `pyproject.toml`.

```
packages: str | list[str]    # Package(s) to install, e.g. "pandas>=2.0" or ["numpy", "scipy"]
path: str | None = None      # Project path for finding the right environment (default: cwd)
add: bool = False            # Use `uv add` (updates pyproject.toml) instead of `uv pip install`
```

Returns: stdout/stderr of the install command — version confirmation on success, error details on failure.

---

## Group 2: Notebook-Level

These tools operate on `.ipynb` files. `nb_glob`, `nb_read`, `nb_grep`, and `nb_create` are file-based and work without a running Jupyter server. `nb_open`, `nb_close`, `nb_run`, and `nb_kernel_restart` require Jupyter.

---

### `nb_open` — *Bash resource lifecycle — required before other `nb_*` operations*

Open a notebook in the Jupyter server session, initializing the kernel connection and RTC tracking. **Must be called before any other `nb_*` operation on a notebook.**

Follows the same resource lifecycle pattern as Bash: just as Claude tracks temp files created with `mktemp` and removes them when done, it must track every notebook opened with `nb_open` and close it with `nb_close` when finished. Session end triggers automatic `nb_close` with save.

Does not return notebook content — use `nb_read` for that.

```
path: str                    # Path to .ipynb file
kernel: str | None = None    # Kernel to use (default: from notebook metadata)
```

Returns:
```
Opened nbs/00_core.ipynb
  kernel: python3 (Python 3)
  cells:  42
  module: mylib.core
```

---

### `nb_close` — *Bash resource lifecycle — auto-triggered on session end*

Close a notebook, saving outputs to disk first. Pair with `nb_open`: like how Claude kills a background process or removes a temp file it created, it must close every notebook it opened. Called automatically when the session ends.

```
path: str              # Path to .ipynb file
save: bool = True      # Save outputs to disk before closing (default: True)
```

Returns:
```
Closed nbs/00_core.ipynb (saved)
```

---

### `nb_glob` — *mirrors `Glob`*

List `.ipynb` files under a path. File-based equivalent of `Glob("**/*.ipynb")` — does not require Jupyter running. Excludes `.ipynb_checkpoints`. Use to discover notebooks in a project before working on them.

```
path: str = "."           # Directory to list notebooks in
recursive: bool = True    # Recurse into subdirectories (default: True)
```

Returns: Sorted list of notebook paths relative to `path`, one per line. Number-prefixed nbdev notebooks sorted by prefix.
```
nbs/00_core.ipynb
nbs/01_utils.ipynb
nbs/02_api.ipynb
nbs/index.ipynb
```

---

### `nb_read` — *mirrors `Read`*

Read a notebook in human-readable form. Use instead of `Read`/`cat` on `.ipynb` files — renders cell content with cell numbers, types, nbdev directives, and output previews. Supports four modes via the same tool, parallel to how `Read` handles full files, partial reads, and metadata mode:

| Mode | How to invoke | `Read` parallel |
|---|---|---|
| Full notebook | `nb_read path` | `Read file_path` |
| Outline (structure only) | `nb_read path outline=True` | `Read` with minimal limit |
| Info (metadata only) | `nb_read path info=True` | `Read` metadata mode (images, PDFs) |
| Single cell | `nb_read path cell=N` | `Read file_path offset=N limit=1` |
| Cell range | `nb_read path range='2-5'` | `Read file_path offset=2 limit=4` |

```
path: str                    # Path to .ipynb file
cell: int | None = None      # Read only this cell (partial mode, like Read offset)
range: str | None = None     # Read cell range, e.g. '2-5' (like Read offset+limit)
outline: bool = False        # Structure only: one line per cell
info: bool = False           # Metadata only: cell counts, kernel, module name
exports: bool = False        # [full/partial] Show only #| export cells
tests: bool = False          # [full/partial] Show only test cells (non-exported code)
markdown: bool = False       # [full/partial] Show only markdown cells
flag: str | None = None      # [full/partial] Show only cells containing this text marker
```

*Full mode:*
```
=== 00_core.ipynb (42 cells)  Module: mylib.core ===

[3] CODE (export)  id=a1b2c3d4
      1  #| export
      2  def tokenize(text: str) -> list[str]:
      3      "Split text into tokens"
      4      return text.split()

    --- outputs (1) ---
    [result] ['hello', 'world']
```

*Outline mode (`outline=True`):*
```
[0] CODE (default_exp)  #| default_exp mylib.core
[1] MARKDOWN            # Core module
[2] CODE (export)       def tokenize(text: str) -> list[str]:
[3] CODE (test)         tokenize("hello world")
```

*Info mode (`info=True`):*
```
Notebook: nbs/00_core.ipynb
  Cells: 42 (18 export, 12 test, 6 hidden, 6 markdown)
  Module: mylib.core  (#| default_exp)
  Kernel: python3 (IPython)
  Last executed: cell 41 of 42
```

---

### `nb_grep` — *mirrors `Grep`*

Search for a regex pattern in notebooks. Exactly mirrors `Grep`: the `path` argument determines scope — a directory searches all notebooks within it, a `.ipynb` file searches within that notebook. Optional `cell`/`range` narrows further to specific cells within a single notebook.

```
pattern: str                    # Regex pattern to search for (required)
path: str = "."                 # Directory → all notebooks; .ipynb file → single notebook
ignore_case: bool = False       # Case-insensitive matching (like Grep -i)
files_only: bool = False        # Return only paths with matches (like Grep files_with_matches)
context: int = 0                # Lines of context around matches (like Grep -C)
cell_type: str | None = None    # Filter to 'code', 'markdown', or 'raw' cells only
directive: str | None = None    # Filter by nbdev directive (e.g. 'export', 'hide')
cell: int | None = None         # Scope to single cell (only valid with .ipynb path)
range: str | None = None        # Scope to cell range, e.g. '2-5' (only valid with .ipynb path)
```

Returns: grep-style output with notebook path, cell index, and matching content:
```
nbs/00_core.ipynb:[3] CODE (export):  def tokenize(text: str) -> list[str]:
nbs/01_utils.ipynb:[7] MARKDOWN:       ## tokenize usage
```

With `context > 0`, shows surrounding lines with `>` markers on matching lines. With `files_only=True`, returns only notebook paths.

---

### `nb_create` — *mirrors `Write`*

Create a new empty notebook with valid structure (nbformat 4, unique cell IDs, correct metadata). Use instead of `Write` for `.ipynb` files — avoids malformed JSON and missing required fields.

```
path: str                   # Output path for the new .ipynb file
module: str | None = None   # Module name for #| default_exp directive (e.g. 'mylib.utils')
title: str | None = None    # Notebook title (rendered as first `# Heading` markdown cell)
force: bool = False         # Overwrite if file already exists (default: error if exists)
```

Returns:
```
Created nbs/03_utils.ipynb
  2 cells: 1 code (#| default_exp mylib.utils), 1 markdown (title)
```

---

### `nb_run` — *mirrors `Bash`*

Execute notebook cells. Four modes controlled by which arguments are provided. `restart` is only valid when execution starts from cell 0 (or the first code cell) — using it for a single cell or a mid-notebook range is an error.

| Mode | Arguments | `restart` default |
|---|---|---|
| Entire notebook | *(none)* | `True` — clean state |
| Run to cell | `upto=N` (cells 0–N inclusive) | `True` — starts from 0 |
| Cell range | `range='2-5'` | `True` if starts at 0; `False` otherwise |
| Single cell | `cell=N` | `False` — preserve kernel state |

```
path: str                      # Path to .ipynb file
cell: int | None = None        # [single cell mode] Run only this cell
range: str | None = None       # [range mode] Run cells in this range, e.g. '2-5' (inclusive)
upto: int | None = None        # [run-to mode] Run cells 0 through N inclusive
# No cell/range/upto → entire notebook mode
restart: bool = True           # Restart kernel first (only valid when execution starts from cell 0)
save: bool = False             # Write execution outputs back to the notebook file
allow_errors: bool = False     # Continue past cell errors (default: stop on first error)
timeout: int = 600             # Per-cell timeout in seconds
kernel: str | None = None      # Kernel name (default: from notebook metadata)
```

Returns:
```
=== 00_core.ipynb — Executing (kernel: python3) ===

[0] CODE (default_exp) (1 line)
    #| default_exp mylib.core
  -> ok (0.1s)

[2] CODE (export) (4 lines)
    def tokenize(text: str) -> list[str]:
    ...
    ['hello', 'world']
  -> ok (0.2s)

=== 3 cells executed: 3 passed ===
```

---

### `nb_kernel_restart` — *mirrors `Bash` (process management)*

Restart the Jupyter kernel for a notebook, optionally switching to a different kernel. Use when the kernel has crashed or state is stale. Prefer `nb_run restart=True` for a combined restart-and-run workflow.

```
path: str                    # Path to notebook (identifies which kernel session to restart)
kernel: str | None = None    # Switch to this kernel spec (e.g. 'python3', 'pypy3'); default: keep current
```

Returns:
```
Kernel restarted: python3
Notebook: nbs/00_core.ipynb
```

---

## Group 3: Cell-Level

These tools operate on individual cells within a notebook. `nb_edit` handles in-cell content changes; the `nb_cell_*` tools handle structural operations on the cell list.

---

### `nb_edit` — *mirrors `Edit`*

Edit cell content using exact find-and-replace. The notebook equivalent of the built-in `Edit` tool — use instead of `Edit`/`Write` on `.ipynb` files. Requires `old` to appear exactly once in the target cell (same uniqueness constraint as `Edit`'s `old_string`). Use `replace_all` when the string appears multiple times.

**Usage patterns** (same as the built-in `Edit`):

- **Replace**: `old="foo" new="bar"` — standard find-and-replace
- **Insert before anchor**: `old="anchor_line" new="new_content\nanchor_line"` — include anchor in both `old` and `new`
- **Delete content within cell**: `old="text_to_remove" new=""` — removes text from cell source
- **Change cell type only**: omit `old`/`new`, set `cell_type="markdown"` — only changes the cell type

For **structural** operations (adding or removing whole cells), use `nb_cell_add` / `nb_cell_delete`.

```
path: str                        # Path to .ipynb file
cell: int | None = None          # Cell index to edit (mutually exclusive with match)
old: str                         # Exact text to find (must be unique in the cell, like Edit's old_string)
new: str                         # Replacement text; empty string deletes the matched text
match: str | None = None         # Find cell by content pattern instead of by index
replace_all: bool = False        # Replace all occurrences (required when old appears >1 time)
cell_type: str | None = None     # Also change the cell type ('code', 'markdown', or 'raw')
dry_run: bool = False            # Show what would change without writing to disk
diff: bool = False               # Show before/after diff
```

Returns (with `diff=True`):
```
--- cell [3] (before)
+++ cell [3] (after)
  #| export
  def tokenize(text: str) -> list[str]:
-     "Split text into tokens"
+     "Tokenize text by whitespace."
  return text.split()

Replaced 1 occurrence in cell [3]
Saved nbs/00_core.ipynb
```

---

### `nb_cell_move` — *mirrors `Edit` (structural reorder)*

Move a cell (or range of cells) to a different position. Equivalent to cut-and-paste at the cell level. Use `dry_run` to preview the result before committing.

```
path: str                   # Path to .ipynb file
from_pos: int               # Source cell index (start of range if range given)
to_pos: int                 # Target position (where the cell lands after the move)
range: str | None = None    # Move a range of cells, e.g. '3-5' (from_pos is the range start)
dry_run: bool = False       # Preview the move without writing to disk
```

Returns:
```
Move cell [3] -> [7]:
[3] CODE (export)
      1  def tokenize(text: str) -> list[str]:
      2      return text.split()

Saved nbs/00_core.ipynb
```

---

### `nb_cell_copy` — *mirrors `Edit` (duplicate)*

Copy a cell (or range of cells) to another position, creating new cells with fresh IDs. Default destination is immediately below the source cell.

```
path: str                   # Path to .ipynb file
cell: int                   # Cell index to copy
to: int | None = None       # Destination index (default: cell + 1, immediately below source)
range: str | None = None    # Copy a range, e.g. '3-5' (cell is ignored if range given)
dry_run: bool = False       # Preview without writing to disk
```

Returns:
```
Copy cell [3] -> [4] (new id: new9abc):
[4] CODE (export)
      1  def tokenize(text: str) -> list[str]:
      2      return text.split()

Saved nbs/00_core.ipynb
```

---

### `nb_cell_add` — *mirrors `Write` / `Edit` (structural insert)*

Add a new cell to the notebook at a specific position (default: end). Distinct from `nb_edit`: this inserts a whole new cell into the notebook structure, not content into an existing cell.

```
path: str                       # Path to .ipynb file
source: str                     # Cell source content (code or markdown text)
cell_type: str = "code"         # Cell type: 'code', 'markdown', or 'raw' (default: 'code')
at: int | None = None           # Position to insert at (default: append to end of notebook)
dry_run: bool = False           # Preview without writing to disk
```

Returns:
```
Insert 1 cell at position [4]:
[4] CODE
      1  import pandas as pd
      2  import numpy as np

Saved nbs/00_core.ipynb
```

---

### `nb_cell_split` — *mirrors `Edit` (structural split)*

Split a cell at a given line number into two cells of the same type. Lines before the split stay in the original cell; lines from the split line onward go into a new cell inserted immediately after.

```
path: str              # Path to .ipynb file
cell: int              # Cell index to split
line: int              # Line number to split at (1-indexed; this line begins the new cell)
dry_run: bool = False  # Preview without writing to disk
```

Returns:
```
Split cell [3] at line 3:
[3] CODE (export)
      1  #| export
      2  def tokenize(text: str) -> list[str]:

[4] CODE (new)
      1      "Split text into tokens"
      2      return text.split()

Saved nbs/00_core.ipynb
```

---

### `nb_cell_merge` — *mirrors `Edit` (structural merge)*

Merge multiple cells into a single cell. Cells are joined in index order with a configurable separator between their sources. The merged cell takes the type of the first cell; all other cells are removed.

```
path: str                    # Path to .ipynb file
cells: str                   # Comma-separated cell indices to merge, e.g. '3,4,5'
separator: str = "\n"        # Text inserted between each cell's source (default: newline)
dry_run: bool = False        # Preview without writing to disk
```

Returns:
```
Merge cells [3, 4, 5] -> [3]:
[3] CODE (export)
      1  #| export
      2  def tokenize(text: str) -> list[str]:
      3      "Split text into tokens"
      4      return text.split()

Saved nbs/00_core.ipynb
```

---

### `nb_cell_delete` — *mirrors `Edit` (structural remove)*

Remove a cell from the notebook. Always shows the cell content before deleting — like `Edit` requiring `old_string`, this ensures the agent confirms what it's removing before it's gone. Distinct from `nb_edit old="..." new=""` which removes text *within* a cell; this removes the entire cell from the notebook structure.

```
path: str                   # Path to .ipynb file
cell: int | None = None     # Cell index to delete (mutually exclusive with match)
match: str | None = None    # Find and delete cell by content pattern (fails if >1 match)
dry_run: bool = False       # Preview what would be deleted without writing to disk
```

Returns (always shows content before deleting, for confirmation):
```
Remove cell [3]:
[3] CODE (test)
      1  assert tokenize("hello world") == ["hello", "world"]

Saved nbs/00_core.ipynb
```

---

## Key Constraints and Notes

**`nb_edit` uniqueness** — `old` must appear exactly once in the target cell unless `replace_all=True`. Error messages show the full cell content to help you craft a more specific `old` string. This is the same constraint as the built-in `Edit` tool.

**`nb_edit` vs `nb_cell_delete`** — `nb_edit old="..." new=""` removes text *inside* a cell (the cell still exists, now empty or shorter). `nb_cell_delete` removes the *entire cell* from the notebook's cell list.

**`nb_run` restart constraint** — `restart=True` is only valid when execution starts from cell 0: entire notebook (no args), `upto=N`, or `range='0-N'`. Using `restart=True` with `cell=N` or `range='M-N'` where M > 0 is an error — restarting and then jumping mid-notebook wipes the context you're trying to use.

**`nb_open` / `nb_close` lifecycle** — Call `nb_open` before any `nb_*` cell operation on a notebook. Call `nb_close` when done. The session automatically calls `nb_close save=True` on all open notebooks at the end, but explicit closes are preferred. This mirrors the resource-management pattern used with Bash temp files and background processes.

**`dry_run` availability** — All write operations support `dry_run=True`: `nb_edit`, `nb_cell_move`, `nb_cell_copy`, `nb_cell_add`, `nb_cell_split`, `nb_cell_merge`, `nb_cell_delete`.

**File-based vs Jupyter-dependent** — The following work without a running Jupyter server: `nb_glob`, `nb_read`, `nb_grep`, `nb_create`. All other `nb_*` and `jupy_*` tools require Jupyter.

---

## Built-in Tool Reference

The nbdev-mcp tools are designed so their UX matches Claude's built-in tools. This section documents those built-ins for readers who may not be familiar with them.

---

### `Read` — Read a file

Returns file content with line numbers. Handles plain text, source code, images (rendered visually), PDFs (with page ranges), and Jupyter notebooks.

```
file_path: str             # Absolute path to the file (required)
offset: int | None         # Line number to start reading from (default: beginning of file)
limit: int | None          # Maximum number of lines to return (default: up to 2000)
pages: str | None          # Page range for PDFs, e.g. "1-5" (PDF files only)
```

Modes:
- **Full file**: `Read file_path` — returns the whole file with `cat -n` style line numbers
- **Partial**: `Read file_path offset=50 limit=30` — returns lines 50–79, like a windowed view
- **Metadata / special types**: `Read image.png` — shows the image visually rather than raw bytes; `Read doc.pdf pages="1-3"` — renders PDF pages

`nb_read` maps to this: no args = full notebook; `cell`/`range` = partial read; `outline`/`info` = metadata-style summary.

---

### `Write` — Write a file

Creates a new file or completely overwrites an existing one. Always use `Read` before `Write` on an existing file.

```
file_path: str    # Absolute path to write (required)
content: str      # Full content to write (required)
```

No modes — always writes the entire content. For targeted edits to an existing file, use `Edit` instead.

`nb_create` maps to this: creates a new `.ipynb` file with valid notebook structure.

---

### `Edit` — Find-and-replace in a file

Replaces an exact string in a file. The key constraint: `old_string` must appear **exactly once** in the file (unless `replace_all=True`). This forces the caller to be specific enough to identify a unique location, avoiding accidental edits.

```
file_path: str        # Absolute path to the file (required)
old_string: str       # Exact text to find — must be unique in the file (required)
new_string: str       # Replacement text — can be empty to delete (required)
replace_all: bool     # Replace every occurrence instead of requiring uniqueness (default: False)
```

Usage patterns:
- **Replace**: `old_string="foo" new_string="bar"` — replaces one occurrence
- **Insert before a line**: `old_string="anchor\n" new_string="new_line\nanchor\n"` — include the anchor in both strings
- **Insert after a line**: `old_string="anchor\n" new_string="anchor\nnew_line\n"`
- **Delete content**: `old_string="text_to_remove\n" new_string=""` — empty `new_string` removes the matched text
- **Multi-replace**: set `replace_all=True` when the pattern is intentionally repeated

`nb_edit` maps to this exactly, scoped to one notebook cell. `nb_cell_delete` maps to the structural equivalent (removing the whole cell, not just its content).

---

### `Bash` — Run a shell command

Executes a shell command and returns its output. Claude uses this for anything that requires running a process: installing packages, running tests, managing git, starting/stopping services.

```
command: str                  # Shell command to execute (required)
timeout: int | None           # Timeout in milliseconds (default: 120000 / 2 minutes; max: 600000)
run_in_background: bool       # Run without waiting for output (default: False)
description: str              # Human-readable description of what the command does
```

Resource lifecycle pattern: when Claude creates a resource with Bash (a temp file with `mktemp`, a background process, a server), it tracks that resource and cleans it up when done — removing the file, killing the process, stopping the server. `nb_open`/`nb_close` follow this same pattern.

`nb_run` maps to this for cell execution. `jupy_install`, `jupy_connect`, `nb_kernel_restart`, `nb_open`, and `nb_close` also follow the Bash resource-management pattern.

---

### `Glob` — Find files by name pattern

Lists files matching a glob pattern, sorted by modification time (most recent first). Use for finding files when you know the naming pattern but not the exact path.

```
pattern: str       # Glob pattern to match, e.g. "**/*.py" or "src/**/*.ts" (required)
path: str | None   # Directory to search in (default: current working directory)
```

Returns: matching file paths, one per line, sorted by modification time descending. Returns an error if no files match.

`nb_glob` maps to this with `Glob("**/*.ipynb")` semantics, adding notebook-aware sorting and checkpoint exclusion. `jupy_kernels` serves the same *discovery* purpose but for kernel specs rather than filesystem paths.

---

### `Grep` — Search file content by regex

Searches for a regex pattern in files, returning matches with file path and line number. The `path` argument determines scope: a directory searches all files within it recursively; a file path searches within that file only.

```
pattern: str                  # Regex pattern to search for (required)
path: str | None              # File or directory to search (default: current working directory)
-i / ignore_case: bool        # Case-insensitive matching (default: False)
output_mode: str              # "content" — show matching lines (default)
                              # "files_with_matches" — show only file paths (like grep -l)
                              # "count" — show match counts per file
context: int | None           # Lines of context around each match, before and after (like grep -C)
-A: int | None                # Lines of context after each match only (like grep -A)
-B: int | None                # Lines of context before each match only (like grep -B)
glob: str | None              # Filter files by glob pattern, e.g. "*.py" (within the search path)
type: str | None              # Filter by file type, e.g. "py", "ts", "rust"
multiline: bool               # Match patterns across line boundaries (default: False)
head_limit: int               # Limit output to first N results (default: unlimited)
```

Returns: matching lines in `file:line_number:content` format, or just file paths with `files_with_matches`.

`nb_grep` maps to this exactly. The `path` scope rule is identical: directory → multi-file search, file → within-file search. The notebook-specific `cell`/`range`, `cell_type`, and `directive` parameters are additions on top of the core Grep interface.
