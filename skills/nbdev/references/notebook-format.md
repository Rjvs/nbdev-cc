# Jupyter Notebook (.ipynb) File Format

Complete reference for the Jupyter Notebook v4.5 JSON structure. Essential for programmatically editing notebooks.

## Overview

Jupyter notebooks are JSON files with the `.ipynb` extension. They contain:
- Metadata about the kernel and notebook
- An ordered array of cells (code, markdown, or raw)
- Outputs from code execution

---

## Top-Level Structure

```json
{
  "nbformat": 4,
  "nbformat_minor": 5,
  "metadata": {
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    },
    "language_info": {
      "name": "python",
      "version": "3.9.0",
      "codemirror_mode": {"name": "ipython", "version": 3},
      "file_extension": ".py",
      "mimetype": "text/x-python",
      "pygments_lexer": "ipython3"
    }
  },
  "cells": []
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `nbformat` | int | Major version (always 4 for current format) |
| `nbformat_minor` | int | Minor version (5+ for cell IDs) |
| `metadata` | object | Notebook-level metadata |
| `cells` | array | Ordered list of cell objects |

### Metadata Fields

| Field | Required | Description |
|-------|----------|-------------|
| `kernelspec.name` | Yes | Kernel identifier (e.g., "python3") |
| `kernelspec.display_name` | Yes | Human-readable kernel name |
| `language_info.name` | Yes | Programming language name |
| `language_info.version` | No | Language version |
| `title` | No | Notebook title |
| `authors` | No | Array of `{name: string}` objects |

---

## Cell Types

All cells share these common fields:

| Field | Type | Description |
|-------|------|-------------|
| `cell_type` | string | "code", "markdown", or "raw" |
| `id` | string | Unique identifier (1-64 alphanumeric chars, hyphens, underscores) |
| `metadata` | object | Cell-specific metadata |
| `source` | string or array | Cell content (string or array of line strings) |

### Code Cells

```json
{
  "cell_type": "code",
  "id": "abc123",
  "metadata": {},
  "source": [
    "#| export\n",
    "def hello(name):\n",
    "    \"\"\"Say hello.\"\"\"\n",
    "    return f'Hello, {name}!'"
  ],
  "outputs": [],
  "execution_count": null
}
```

**Additional Required Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `outputs` | array | Execution outputs (see Output Types below) |
| `execution_count` | int or null | Execution order number |

**Code Cell Metadata:**

| Field | Description |
|-------|-------------|
| `metadata.collapsed` | Boolean - output collapsed state |
| `metadata.scrolled` | Boolean or "auto" - output scrolling |
| `metadata.jupyter.source_hidden` | Hide input in UI |
| `metadata.jupyter.outputs_hidden` | Hide outputs in UI |
| `metadata.execution` | Timing information |

### Markdown Cells

```json
{
  "cell_type": "markdown",
  "id": "def456",
  "metadata": {},
  "source": [
    "# Section Title\n",
    "\n",
    "This is **markdown** content with `code formatting`."
  ]
}
```

Markdown cells support:
- GitHub-flavored markdown
- LaTeX math (`$inline$` and `$$block$$`)
- Attachments (embedded images)

**Attachments:**

```json
{
  "cell_type": "markdown",
  "id": "ghi789",
  "metadata": {},
  "source": ["![alt text](attachment:image.png)"],
  "attachments": {
    "image.png": {
      "image/png": "base64-encoded-data..."
    }
  }
}
```

### Raw Cells

```json
{
  "cell_type": "raw",
  "id": "jkl012",
  "metadata": {
    "format": "text/restructuredtext"
  },
  "source": [".. note::\n", "   This is reST content."]
}
```

Raw cells pass content unchanged to nbconvert. Use `metadata.format` to specify the target format.

---

## Output Types

Outputs appear only in code cells.

### Stream Output (stdout/stderr)

```json
{
  "output_type": "stream",
  "name": "stdout",
  "text": ["Hello, World!\n"]
}
```

### Execution Result

```json
{
  "output_type": "execute_result",
  "execution_count": 1,
  "data": {
    "text/plain": ["42"]
  },
  "metadata": {}
}
```

### Display Data

```json
{
  "output_type": "display_data",
  "data": {
    "text/plain": ["<Figure size 640x480>"],
    "image/png": "base64-encoded-image-data..."
  },
  "metadata": {}
}
```

### Error Output

```json
{
  "output_type": "error",
  "ename": "ValueError",
  "evalue": "invalid literal for int()",
  "traceback": [
    "\u001b[0;31m---------------------------------------------------------------------------\u001b[0m",
    "\u001b[0;31mValueError\u001b[0m: invalid literal for int()"
  ]
}
```

---

## MIME Bundles

Rich outputs use MIME type keys:

```json
{
  "data": {
    "text/plain": ["DataFrame summary"],
    "text/html": ["<table>...</table>"],
    "application/json": {"key": "value"}
  }
}
```

Common MIME types:
- `text/plain` - Plain text (always present as fallback)
- `text/html` - HTML content
- `text/markdown` - Markdown content
- `image/png` - Base64-encoded PNG
- `image/jpeg` - Base64-encoded JPEG
- `image/svg+xml` - SVG content
- `application/json` - JSON data
- `application/javascript` - JavaScript code

---

## Source Field Format

The `source` field can be:

**Single string:**
```json
"source": "#| export\ndef foo(): pass"
```

**Array of strings (line-by-line):**
```json
"source": [
  "#| export\n",
  "def foo():\n",
  "    pass"
]
```

When reading, either format is valid. When writing, use array format for easier line-by-line manipulation.

Note: Lines typically end with `\n` except the last line.

---

## Cell ID Requirements

- Pattern: `^[a-zA-Z0-9-_]+$` (alphanumeric, hyphens, underscores)
- Length: 1-64 characters
- Must be unique within the notebook
- Required for nbformat 4.5+

Generate IDs with:
```python
import uuid
cell_id = str(uuid.uuid4())[:8]  # e.g., "a1b2c3d4"
```

---

## Complete Example

```json
{
  "nbformat": 4,
  "nbformat_minor": 5,
  "metadata": {
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "cells": [
    {
      "cell_type": "code",
      "id": "module-def",
      "metadata": {},
      "source": ["#| default_exp core"],
      "outputs": [],
      "execution_count": null
    },
    {
      "cell_type": "markdown",
      "id": "intro",
      "metadata": {},
      "source": ["# Core Module\n", "\n", "Core functionality."]
    },
    {
      "cell_type": "code",
      "id": "export-fn",
      "metadata": {},
      "source": [
        "#| export\n",
        "def greet(name: str) -> str:\n",
        "    \"\"\"Return a greeting.\"\"\"\n",
        "    return f'Hello, {name}!'"
      ],
      "outputs": [],
      "execution_count": 1
    },
    {
      "cell_type": "code",
      "id": "test-fn",
      "metadata": {},
      "source": [
        "# Test the function\n",
        "assert greet('World') == 'Hello, World!'"
      ],
      "outputs": [],
      "execution_count": 2
    }
  ]
}
```

---

## Editing Tips

### Adding a Cell

1. Create cell object with all required fields
2. Generate unique `id`
3. For code cells: include empty `outputs: []` and `execution_count: null`
4. Insert into `cells` array at desired position

### Modifying Cell Content

1. Locate cell by `id` or position
2. Update `source` field
3. For code cells: optionally clear `outputs` and reset `execution_count` to null

### Removing a Cell

1. Remove the cell object from the `cells` array
2. No other cleanup needed (IDs don't need to be sequential)

### Preserving Format

When editing with text tools (Edit, Write):
- Maintain proper JSON formatting
- Preserve newlines in source arrays (`\n` at end of lines)
- Keep metadata fields even if empty (`{}`)
- Maintain `execution_count` as integer or `null` (not string)

### Using NotebookEdit Tool

The `NotebookEdit` tool handles JSON structure automatically:
- Use `edit_mode: "replace"` to modify existing cells
- Use `edit_mode: "insert"` to add new cells
- Use `edit_mode: "delete"` to remove cells
- Specify `cell_type` for new cells
