# Collaboration Patterns for nbdev Projects

How to effectively work on nbdev projects using Claude Code's tools.

**MCP tools are the default** for editing, executing, and managing cells in notebooks.
Use `./tools/nb_*` scripts when they are more efficient than MCP:

- **`nb_search`** for searching across notebooks (MCP has no search equivalent)
- **`nb_read`** for quickly reading a notebook or specific cells (faster than `use_notebook` + `read_notebook`)
- **`nb_run --upto N`** for batch execution (one call instead of many `execute_cell` calls)
- **`nb_create`** for scaffolding new notebooks
- **`nb_validate`** before commits

When MCP is unavailable, first use `nb_mcp_url` to ensure the MCP is connecting with the correct URL and token.
If there is no server or a persistent issue, you should fall back to `./tools/nb_*` for all operations — but only
after the user approves the switch. Never silently switch to offline mode.

## Quick Reference: Tool Redirects

IMPORTANT: You SHOULD NOT use generic tools on `.ipynb` files when you can use a notebook-aware tool. Prefer to  use
the more powerful notebook-aware equivalent:

| You are about to... | Stop. Use this instead |
|---|---|
| `Grep`/`grep` a `.ipynb` file | `./tools/nb_search nbs/ --pattern "..."` (preferred — MCP has no search) |
| `Read`/`cat` a `.ipynb` file | `./tools/nb_read notebook.ipynb` (preferred) or MCP `read_notebook` |
| `Edit` a `.ipynb` file's JSON | MCP `overwrite_cell_source` (preferred for live sessions) or `./tools/nb_edit` |
| `Write` a new `.ipynb` from scratch | `./tools/nb_create --module name --out path` |
| Write Python to parse/edit `.ipynb` | Use `nb_read`, `nb_edit`, `nb_cells`, or `nb_search` — they already do it well! |
| Loop over `execute_cell` calls | `./tools/nb_run notebook.ipynb --upto N` or `--range` (one call, one kernel) |

The only time to use generic tools on `.ipynb` files is when debugging the JSON structure itself.

---

## Live Collaboration (Jupyter MCP) — Default Mode

When `jupyter-mcp` is available, **all notebook editing must go through MCP tools**.
Changes sync instantly to the browser via Y.js CRDTs, and you can execute cells to
verify your work.

See `templates/nbdev-jupyter/jupyter-mcp-setup.md` for setup.

### Live tool selection

| Situation | MCP Tool |
|-----------|----------|
| Connect to a notebook | `use_notebook` |
| Read current state | `read_notebook`, `read_cell` |
| Edit a cell | `overwrite_cell_source` |
| Add a cell | `insert_cell` |
| Remove a cell | `delete_cell` |
| Run a cell | `execute_cell` |
| Add + run in one step | `insert_execute_code_cell` |
| Run code without creating a cell | `execute_code` |
| Disconnect | `unuse_notebook` |

### Live workflow

1. `use_notebook` — connect to the notebook
2. `read_notebook` — understand the current state
3. Make changes with `overwrite_cell_source`, `insert_cell`, etc.
4. `execute_cell` — run and verify
5. Before committing: `uv run nbdev_prepare` (file-based, works on auto-saved state)

---

## Troubleshooting Live Sessions

When MCP tools fail during a live session, diagnose the problem and help the user
choose the best path forward.

### Diagnostic Steps

Run these in order to narrow down the issue:

1. **Check MCP connection**: Run `/mcp` — is `jupyter-mcp` listed and connected?
2. **Check server is running**: `./tools/nb_mcp_url` (preferred) or if necessary `uv run jupyter server list`
3. **Check notebook connection**: `list_notebooks` — does it show the notebook?
4. **Check kernel**: `list_kernels` — is a kernel running for the notebook?
5. **Test a simple operation**: `read_notebook` — can you read anything?

### Common Failures and Fixes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| MCP server not listed in `/mcp` | `$JUPYTER_TOKEN` not set when `claude` started | Use `./tools/nb_mcp_url` to get the token |
| MCP connected but `use_notebook` fails | Jupyter server not running or wrong port | Use `./tools/nb_mcp_url` to check the URL & port or `uv run jupyter server list` to confirm; restart if needed |
| `read_notebook` works but `execute_cell` fails | Kernel died or disconnected | `restart_notebook`, then retry |
| Edits not appearing in the browser | Y.js sync corruption (#146) | Inform the user of the problem, ask if you can delete `.jupyter_ystore.db` and restart the server and wait for that approval |
| `overwrite_cell_source` returns error | Cell index changed (human added/removed cells) | `read_notebook` to get current cell layout, retry with correct index |
| Timeouts on all MCP calls | Jupyter server crashed | Check `jupyter.log`, inform the user of the problem, ask if you can restart the server and wait for that approval |

### Decision: Fix, Fall Back, or Abandon

After diagnosing, help the user choose:

**Fix within the session** when:
- The issue is a known, recoverable problem (kernel restart, ystore deletion, re-export)
- You can verify the fix worked before continuing

**Fall back to offline file tools** when ALL of these are true:
- The MCP server or Jupyter itself won't start, or Y.js sync is persistently broken
- You have provided actionable advice to the user for resolving the problem
- **The user explicitly approves switching to offline edits** (do not switch silently)

**Abandon the session** when:
- The problem is outside your ability to resolve (network, permissions, system config)
- You have provided actionable advice to the user for resolving the problem
- The user can fix the problem and start a new session
- Fixing the environment would disrupt the user's work
- Before stopping, document the state and offer to add it to `./TODO.md`:

```markdown
## Session interrupted — [date] [rounded time]

### Accomplished
- [what was completed]

### In progress
- [what was partially done — include file paths and cell numbers]

### Planned
- [what was next]

### Environment issue
- [describe the problem and what was tried]
```

### Falling Back to Offline Mode Mid-Session

When switching from live to offline mid-session:

1. Tell the user what happened, ask for approval to switch and wait for that approval
2. The Jupyter server auto-saves to disk — files are already current
3. Use `./tools/nb_read` to verify the notebook state matches what you
   last saw via MCP
4. Continue with the file tools (see [Offline Mode](#offline-mode-file-based-tools) below)
5. Remind the user to run `uv run nbdev_prepare` before committing, since you
   can no longer execute cells to verify

---

## Offline Tool Selection Guide

> **Reminder:** Only use these tools to edit a notebook when MCP is unavailable and the user has approved offline mode.

### Reading Notebooks

| Situation | Tool | Why |
|-----------|------|-----|
| Understand notebook structure | `./tools/nb_read nb.ipynb --outline` | See all cells at a glance |
| Read full notebook content | `./tools/nb_read nb.ipynb` | Human-readable, shows cell types and directives |
| Read specific cells | `./tools/nb_read nb.ipynb --cell 5` | Focus on one area |
| See what's exported | `./tools/nb_read nb.ipynb --exports` | Quick view of the module's public API |
| See test coverage | `./tools/nb_read nb.ipynb --tests` | What's being tested |
| Read raw JSON (rare) | `Read` tool | Only when debugging JSON structure issues |

### Searching Across Notebooks

| Situation | Tool | Why |
|-----------|------|-----|
| Find a class/function across notebooks | `./tools/nb_search nbs/ --pattern "class Foo"` | One line per matching cell with path and index |
| Case-insensitive search | `./tools/nb_search nbs/ --pattern "error" -i` | Flexible text matching |
| Find all exported cells | `./tools/nb_search nbs/ --directive export` | See every export across the project |
| Search only code cells | `./tools/nb_search nbs/ --pattern "import" --type code` | Filter out prose matches |
| See context around matches | `./tools/nb_search nbs/ --pattern "class Foo" -C 3` | Like `grep -C` with cell structure |
| Which notebooks mention X? | `./tools/nb_search nbs/ --pattern "MyClass" --files-only` | Like `grep -l` for notebooks |

### Executing Cells

**Prefer batch execution when running multiple cells.** A single `nb_run` call with
`--upto` or `--range` does the same work as many individual calls but in one step,
saving tool calls and context.

| Situation | Tool | Why |
|-----------|------|-----|
| Run all cells in a notebook | `./tools/nb_run nb.ipynb` | Runs everything in one call |
| Run up to a specific cell | `./tools/nb_run nb.ipynb --upto 5` | Verify state builds correctly through cell 5 |
| Run a range of cells | `./tools/nb_run nb.ipynb --range 2-5` | Execute cells 2 through 5 in one call |
| Run a single cell | `./tools/nb_run nb.ipynb --cell 5` | Quick check of one cell |
| Run and save outputs | `./tools/nb_run nb.ipynb --upto 5 --save` | Persist outputs in the notebook file |
| Debug failing cells | `./tools/nb_run nb.ipynb --allow-errors` | Continue past errors to see all failures |

**Inefficient pattern — use batch flags instead:**
```bash
# Wastes tool calls and context doing one cell at a time
./tools/nb_run nb.ipynb --cell 0
./tools/nb_run nb.ipynb --cell 1
./tools/nb_run nb.ipynb --cell 2

# One call, same result
./tools/nb_run nb.ipynb --upto 2
```

**Note**: `nb_run` starts a fresh kernel — it does not connect to a running Jupyter session so is not collaborative. 
Use it for offline verification. For live execution during collaboration, use the MCP `execute_cell` tool instead.

### Creating Notebooks

| Situation | Tool | Why |
|-----------|------|-----|
| New module notebook | `./tools/nb_create --module name --out path` | Correct metadata, structure, cell IDs |
| Complex notebook from spec | `./tools/nb_create --from spec.txt --out path` | Write content in plain text, get valid JSON |
| Quick single-cell edit | `NotebookEdit` | Built-in, handles JSON correctly |

### Editing Notebooks

| Situation | Tool | Why |
|-----------|------|-----|
| Small change within a cell | `./tools/nb_edit nb.ipynb --cell N --old "..." --new "..."` | Find-and-replace scoped to one cell, no need to rewrite the whole cell |
| Small change (find cell by content) | `./tools/nb_edit nb.ipynb --match "class Foo" --old "..." --new "..."` | When you know the content but not the index |
| Replace entire cell content | `NotebookEdit` (replace mode) | When rewriting the whole cell |
| Add one cell | `NotebookEdit` (insert mode) | Direct, built-in |
| Add multiple related cells | `./tools/nb_cells nb.ipynb insert --at N --from spec.txt` | One operation for function + prose + test |
| Append cells to end | `./tools/nb_cells nb.ipynb append --from spec.txt` | Simpler than calculating position |
| Move a cell | `./tools/nb_cells nb.ipynb move --from-pos N --to-pos M` | Reorder narrative flow |
| Remove cells | `./tools/nb_cells nb.ipynb remove --cells 3,5,7` | Batch removal |
| Find a cell to edit | `./tools/nb_cells nb.ipynb find --pattern "class Foo"` | Locate by content |
| Major restructure | `Edit` tool on raw JSON | When you need full control (use `nb_validate` after) |

### Validating

| Situation | Tool | Why |
|-----------|------|-----|
| Before committing | `./tools/nb_validate nbs/` | Catch structural errors |
| After raw JSON edits | `./tools/nb_validate notebook.ipynb` | Verify valid structure |
| Full project check | `./tools/nb_validate nbs/ --strict` | No warnings either |

---

## Common Editing Patterns

### Adding a New Function

The atomic unit of nbdev work: export cell + test cell, optionally with prose.

1. Read the notebook to understand where the new function fits in the narrative
2. Write a spec file with the cells
3. Insert at the right position

```bash
# 1. Understand the notebook structure
./tools/nb_read nbs/00_core.ipynb --outline

# 2. Write cells to a temp spec file, then insert
./tools/nb_cells nbs/00_core.ipynb insert --at 8 --from /tmp/new_fn.txt

# 3. Validate
./tools/nb_validate nbs/00_core.ipynb
```

Spec file for a new function (`/tmp/new_fn.txt`):
```
--- markdown
Now we need a way to combine greetings:
--- code
#| export
def combine_greetings(*names: str) -> str:
    """Combine multiple greetings into one."""
    return '\n'.join(greet(n) for n in names)
--- code
test_eq(
    combine_greetings('Alice', 'Bob'),
    'Hello, Alice!\nHello, Bob!'
)
```

### Adding a Method via @patch

Split across cells with explanation between each:

```
--- markdown
### The `bark` method

Dogs should be able to bark. The volume depends on their size:
--- code
#| export
@patch
def bark(self: Dog, loud: bool = False) -> str:
    """Make the dog bark."""
    sound = 'WOOF!' if loud else 'woof'
    return f'{self.name} says {sound}'
--- code
dog = Dog('Rex')
test_eq(dog.bark(), 'Rex says woof')
test_eq(dog.bark(loud=True), 'Rex says WOOF!')
```

### Adding a New Section

When the notebook needs a new conceptual section:

```
--- markdown
## Error Handling

Our functions should handle edge cases gracefully. Let's see what happens
with empty input:
--- code
# Explore the edge case first
try:
    greet('')
except Exception as e:
    print(f'Got: {e}')
--- markdown
Empty strings work but produce ugly output. Let's fix that:
--- code
#| export
def safe_greet(name: str) -> str:
    """Greet someone, handling empty names."""
    name = name.strip() or 'stranger'
    return greet(name)
--- code
test_eq(safe_greet(''), 'Hello, stranger!')
test_eq(safe_greet('  '), 'Hello, stranger!')
test_eq(safe_greet('Alice'), 'Hello, Alice!')
```

### Creating a New Module

```bash
# Create the notebook with proper structure
./tools/nb_create --module utils --title "Utility Functions" --out nbs/01_utils.ipynb

# Verify it's valid
./tools/nb_validate nbs/01_utils.ipynb

# View it
./tools/nb_read nbs/01_utils.ipynb
```

---

## Pre-commit Workflow

Before every commit, run this sequence:

```bash
# 1. Validate notebook structure
./tools/nb_validate nbs/

# 2. Run nbdev_prepare (exports, tests, cleans)
uv run nbdev_prepare

# 3. If tests fail, fix the notebook and repeat from step 1
```

---

## Anti-patterns to Avoid

### Don't edit generated .py files
The source of truth is always the notebook. If you edit `lib_name/core.py` directly, your changes will be overwritten on next `nbdev_export`.

### Don't reorder cells without understanding the narrative
Cell order matters in nbdev. Moving an export cell before its explanation breaks the progressive discovery flow. Always read the surrounding cells first.

### Don't strip prose to "clean up"
The prose between code cells IS the documentation. Removing it breaks the literate programming model. The notebook should read like a tutorial.

### Don't add cells without considering flow
Each cell should fit the narrative. A function added at the end of a notebook might belong in the middle, near related functions.

### Don't skip validation
Always run `nb_validate` after making structural changes. A missing `outputs` field or duplicate cell ID causes problems that are hard to diagnose later.

### Don't forget `nbdev_prepare` before commits
This is the single most common mistake. It exports, tests, and cleans in one step. Without it, generated `.py` files drift from notebooks.

---

## Spec File Format Reference

The cell spec format used by `nb_create` and `nb_cells`:

```
--- code
code cell content here
#| directives go at the top
def functions(): pass
--- markdown
# Markdown cell content

With **formatting** and `code`.
--- code
another code cell
```

Rules:
- Each cell starts with `--- type` where type is `code`, `markdown`, or `raw`
- Content follows on the next line (one blank line between marker and content is stripped)
- Content continues until the next `--- type` marker
- Indentation is preserved exactly as written
