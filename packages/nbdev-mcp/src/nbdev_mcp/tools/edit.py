"""Edit cell content within a notebook (find-and-replace).

Use instead of Edit/Write on .ipynb files. Works on cell content directly,
scoped to a single cell, with uniqueness enforced on old string.
"""

import difflib
from pathlib import Path

from ._common import load_notebook, save_notebook, get_source, source_to_array, validate_notebook_path


def _find_cell_by_match(nb, pattern):
    """Find a cell whose source contains the pattern.

    Returns (index, cell). If multiple match, returns (-1, None) with info.
    """
    cells = nb.get('cells', [])
    matches = []
    for idx, cell in enumerate(cells):
        source = get_source(cell)
        if pattern in source:
            matches.append((idx, cell))

    if len(matches) == 0:
        return None, None
    if len(matches) == 1:
        return matches[0]

    # Ambiguous
    info = [f'--match pattern found in {len(matches)} cells:']
    for idx, cell in matches:
        source = get_source(cell)
        first_line = source.split('\n')[0][:60]
        cell_type = cell.get('cell_type', '?').upper()
        info.append(f'  [{idx}] {cell_type}: {first_line}')
    info.append('Use --cell with an index to be specific.')
    return -1, '\n'.join(info)


def _make_diff(old_source, new_source, cell_idx):
    """Create a unified diff display using difflib."""
    old_lines = old_source.splitlines(keepends=True)
    new_lines = new_source.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f'cell [{cell_idx}] (before)',
        tofile=f'cell [{cell_idx}] (after)',
    )
    return ''.join(diff).rstrip('\n')


def nb_edit(
    path: str,
    old: str,
    new: str,
    cell: int | None = None,
    match: str | None = None,
    replace_all: bool = False,
    dry_run: bool = False,
    diff: bool = False,
) -> str:
    """Edit cell content within a notebook (find-and-replace).

    Args:
        path: Path to .ipynb file.
        old: Text to find in the cell.
        new: Replacement text.
        cell: Cell index to edit (mutually exclusive with match).
        match: Find cell by content pattern (mutually exclusive with cell).
        replace_all: Replace all occurrences (required when old matches more than once).
        dry_run: Show what would change without writing.
        diff: Show before/after diff.

    Returns:
        Status message describing what was changed.
    """
    p, err = validate_notebook_path(path)
    if err:
        return err

    if cell is None and match is None:
        return 'Error: provide either cell (index) or match (pattern)'

    nb = load_notebook(p)

    # Find the target cell
    if cell is not None:
        cells = nb.get('cells', [])
        if not (0 <= cell < len(cells)):
            num_cells = len(cells)
            return f'Error: cell index {cell} out of range (0-{num_cells - 1})'
        cell_idx, target = cell, cells[cell]
    else:
        cell_idx, target = _find_cell_by_match(nb, match)
        if cell_idx == -1:  # Ambiguous
            return f'Error: {target}'
        if target is None:
            return f'Error: no cell contains "{match}"'

    old_source = get_source(target)

    count = old_source.count(old)
    if count == 0:
        source_preview = '\n'.join(
            f'  {i:3d}  {line}' for i, line in enumerate(old_source.split('\n'), 1)
        )
        return f'Error: --old string not found in cell [{cell_idx}]\n\nCell [{cell_idx}] content:\n{source_preview}'

    if count > 1 and not replace_all:
        return (
            f'Error: --old string matches {count} times in cell [{cell_idx}]. '
            f'Provide more context to make it unique, or use replace_all.'
        )

    if replace_all:
        new_source = old_source.replace(old, new)
    else:
        new_source = old_source.replace(old, new, 1)

    if old_source == new_source:
        return 'No changes (old and new strings are identical)'

    output_parts = []

    if diff or dry_run:
        output_parts.append(_make_diff(old_source, new_source, cell_idx))

    if dry_run:
        label = f'{count} occurrence(s)' if replace_all else '1 occurrence'
        output_parts.append(f'Would replace {label} in cell [{cell_idx}] (dry run, no changes written)')
        return '\n\n'.join(output_parts)

    # Apply the change
    target['source'] = source_to_array(new_source)
    save_notebook(nb, p)

    label = f'{count} occurrence(s)' if replace_all else '1 occurrence'
    output_parts.append(f'Replaced {label} in cell [{cell_idx}]')
    output_parts.append(f'Saved {p}')
    return '\n'.join(output_parts)
