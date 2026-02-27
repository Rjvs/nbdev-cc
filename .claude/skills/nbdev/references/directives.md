# nbdev Directives Reference

Directives are special comments that control how nbdev processes notebook cells. They start with `#|` followed by the directive name and optional arguments.

## Directive Syntax

```python
#| directive_name argument
#| another_directive
```

Directives must appear at the start of a cell, before any code. Multiple directives can be stacked. A blank line or non-comment line ends the directive block.

---

## Export Directives

Control how code is exported to Python modules.

### `#| default_exp`

Specifies the default module for exports in this notebook.

```python
#| default_exp core
```

- Place in the first code cell of each notebook
- Creates/updates `lib_path/core.py`
- All `#| export` cells go to this module unless overridden

### `#| export`

Export cell contents to the module and documentation.

```python
#| export
def my_function():
    """This function is exported."""
    pass
```

- Function/class added to module's `__all__`
- Included in generated documentation
- Can specify alternate module: `#| export utils`

### `#| exporti`

Internal export - to module but NOT to `__all__` or docs.

```python
#| exporti
def _internal_helper():
    """Not part of public API."""
    pass
```

Use for:
- Helper functions used within the module
- Implementation details not meant for external use

### `#| exports`

Source export - like `#| export` but shows source code in docs.

```python
#| exports
def example_function():
    """Docstring shown, AND source code displayed."""
    return 42
```

Use when the implementation itself is educational.

---

## Documentation Directives

Control how cells appear in generated documentation.

### `#| hide`

Completely hide cell from module AND documentation.

```python
#| hide
# Setup code, debugging, temporary experiments
import pdb; pdb.set_trace()
```

### `#| hide_input`

Hide the code but show the output.

```python
#| hide_input
df.head()  # Only the table output appears in docs
```

Note: Cells with `#| export` auto-hide input in docs.

### `#| hide_line`

Hide a specific line within a cell.

```python
#| export
def process(data):
    debug_print(data)  #| hide_line
    return transform(data)
```

### `#| filter_stream`

Filter output lines containing specified keywords from cell results. Useful for suppressing noisy warnings in documentation output.

```python
#| filter_stream UserWarning FutureWarning
# Lines containing "UserWarning" or "FutureWarning" are removed from output
model.fit(data)
```

Multiple keywords can be listed, space-separated. Any output line containing any of the keywords is removed from the rendered documentation.

### `#| output`

Control output visibility:

```python
#| output: false
# Output completely hidden
print("This won't appear in docs")
```

```python
#| output: asis
# Output rendered as raw markdown
print("## This becomes a heading")
```

### `#| include`

Hide both input AND output.

```python
#| include: false
# Cell executes but nothing shows in docs
setup_environment()
```

### `#| echo`

Control code visibility (Quarto directive):

```python
#| echo: false
# Same as hide_input
```

```python
#| echo: fenced
# Show code in fenced code block
```

---

## Execution Directives

Control when and how cells execute.

### `#| eval`

Control cell execution:

```python
#| eval: false
# Never executed (testing, docs, or notebooks)
hypothetical_code()
```

```python
#| eval: true
# Always executed when building docs
ensure_this_runs()
```

Default behavior: cells execute during docs build unless they have errors.

### `#| exec_doc`

Ensure a cell executes every time documentation is generated. Useful for dynamic content that must be fresh on each docs build.

```python
#| exec_doc
print(f"Documentation generated: {datetime.now()}")
```

### `#| skip_exec`

Skip execution during nbdev operations but keep in docs.

```python
#| skip_exec
# Shown in docs but not run during nbdev_test
long_running_demo()
```

---

## Test Directives

Control testing behavior.

### Test Flags

Configure custom flags in `settings.ini`:

```ini
tst_flags = slow|cuda|integration
```

Then use in cells:

```python
#| slow
def test_slow_operation():
    # Only runs with: nbdev_test --flags slow
    time.sleep(60)
```

```python
#| cuda
def test_gpu_operation():
    # Only runs with: nbdev_test --flags cuda
    torch.cuda.is_available()
```

### `#| all_slow` (notebook-wide)

Apply flag to entire notebook:

```python
#| all_slow
# All tests in this notebook require --flags slow
```

---

## Quarto Directives

nbdev uses Quarto for documentation. These Quarto directives work in nbdev:

### `#| fig-cap`

Add figure captions:

```python
#| fig-cap: "Training loss over epochs"
plt.plot(losses)
```

### `#| fig-width` / `#| fig-height`

Control figure dimensions:

```python
#| fig-width: 8
#| fig-height: 6
plot_large_figure()
```

### `#| layout-ncol`

Multiple outputs in columns:

```python
#| layout-ncol: 2
display(fig1)
display(fig2)
```

### `#| column`

Control content width:

```python
#| column: page
# Content spans full page width
wide_table
```

Options: `body`, `page`, `screen`, `margin`

### `#| tbl-cap`

Table captions:

```python
#| tbl-cap: "Summary Statistics"
df.describe()
```

### `#| code-fold`

Collapsible code:

```python
#| code-fold: true
# Code hidden by default, click to expand
long_code_block()
```

```python
#| code-fold: show
# Code shown by default, click to collapse
```

### `#| code-summary`

Label for collapsed code:

```python
#| code-fold: true
#| code-summary: "Show the plotting code"
complex_visualization()
```

---

## Content-Hidden Divs (Markdown Cells)

Quarto's fenced div syntax hides markdown content from generated documentation while keeping it visible and editable in the notebook. This is the primary mechanism for excluding prose, notes, or draft documentation from docs output.

### Unconditional Hiding

```markdown
::: {.content-hidden}

## Draft: API Redesign Notes

These notes are visible in the notebook but will NOT appear in the
generated documentation site. Use this for:
- Work-in-progress documentation
- Internal team notes
- Rough drafts not ready for readers

:::
```

Everything between the `:::` fences is excluded from documentation output. The content remains fully visible and editable in the notebook interface.

### Conditional Hiding by Format

Hide content only for specific output formats:

```markdown
::: {.content-hidden when-format="html"}
This paragraph is hidden from HTML docs but appears in other formats (e.g., PDF).
:::
```

```markdown
::: {.content-hidden unless-format="pdf"}
This only appears in PDF output.
:::
```

### Content-Visible (Inverse)

Show content only in specific formats:

```markdown
::: {.content-visible when-format="html"}
This interactive widget explanation only makes sense on the web.
:::
```

### Inline Hidden Spans

Hide a short run of text within a paragraph:

```markdown
This sentence is visible [but this part is hidden]{.content-hidden} in docs.
```

### Important Notes

- These div fences go in **markdown cells**, not code cells
- The space in `::: {.content-hidden}` is optional — `:::{.content-hidden}` also works
- Nesting is supported: other Quarto divs can go inside a content-hidden block
- Processed by Quarto during `nbdev_docs` / `nbdev_preview` — no effect on module export or test execution
- Available condition attributes: `when-format`, `unless-format`, `when-profile`, `unless-profile`

---

## Cell Tags

Some behaviors use cell metadata tags rather than directives:

### In Jupyter Interface

Add tags via: View > Cell Toolbar > Tags

Common tags:
- `hide-input` - Same as `#| hide_input`
- `hide-output` - Same as `#| output: false`
- `remove-cell` - Same as `#| hide`

### In Cell Metadata (JSON)

```json
{
  "cell_type": "code",
  "metadata": {
    "tags": ["hide-input"]
  },
  ...
}
```

---

## Directive Quick Reference

| Directive | Module | Docs | Description |
|-----------|--------|------|-------------|
| `#\| default_exp name` | - | - | Set default export module |
| `#\| export` | Yes | Yes | Export to module and docs |
| `#\| exporti` | Yes | No | Internal export (not in `__all__`) |
| `#\| exports` | Yes | Yes | Export with source code shown |
| `#\| hide` | No | No | Hide completely |
| `#\| hide_input` | - | Code hidden | Hide code, show output |
| `#\| hide_line` | - | Line hidden | Hide specific line |
| `#\| filter_stream kw` | - | Lines filtered | Remove output lines containing keyword |
| `#\| output: false` | - | Output hidden | Hide output |
| `#\| output: asis` | - | Raw markdown | Render output as markdown |
| `#\| include: false` | - | All hidden | Hide input and output |
| `#\| eval: false` | - | Not run | Skip execution entirely |
| `#\| exec_doc` | - | Re-run | Execute every docs build |
| `#\| slow` | - | - | Requires `--flags slow` to test |
| `:::{.content-hidden}` | - | Hidden | Hide markdown from docs (Quarto div) |
| `:::{.content-visible}` | - | Conditional | Show markdown conditionally (Quarto div) |

---

## Common Patterns

### Standard Exported Function

```python
#| export
def process_data(data: list) -> dict:
    """
    Process the input data.

    Parameters
    ----------
    data : list
        Input data to process

    Returns
    -------
    dict
        Processed results
    """
    return {item: transform(item) for item in data}
```

### Test with Output Shown

```python
result = process_data([1, 2, 3])
result
```

(No directive - it's a test, output shown in docs)

### Test Hidden from Docs

```python
#| hide
# Extensive testing not needed in docs
for i in range(1000):
    assert process_data([i]) == {i: transform(i)}
```

### Setup Code

```python
#| hide
import warnings
warnings.filterwarnings('ignore')
%matplotlib inline
```

### Demonstration with Visible Code

```python
#| echo: true
#| output: true
# Both code and output visible (explicit)
demo_function()
```
