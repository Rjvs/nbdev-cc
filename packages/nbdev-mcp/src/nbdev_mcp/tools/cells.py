"""Bulk cell operations for notebooks.

Higher-level operations beyond single-cell edits: insert multiple cells,
move cells, find cells by content or directive, remove cells.
"""

import re
from pathlib import Path

from ._common import (
    load_notebook, save_notebook, get_source, source_to_array,
    generate_cell_id, parse_spec,
)


def _make_cell(cell_type, source, index=0):
    """Create a cell dict from type and source."""
    cell = {
        'cell_type': cell_type,
        'id': generate_cell_id(index, source),
        'metadata': {},
        'source': source_to_array(source),
    }
    if cell_type == 'code':
        cell['outputs'] = []
        cell['execution_count'] = None
    return cell


def _parse_spec_file(path):
    """Parse a spec file and return cell dicts."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    specs = parse_spec(content)
    return [_make_cell(ct, src, i) for i, (ct, src) in enumerate(specs)]


def _format_cell_preview(idx, cell):
    """Format a cell preview."""
    cell_type = cell.get('cell_type', '?').upper()
    source = get_source(cell)
    source_lines = source.split('\n')
    preview_lines = source_lines[:3]

    parts = [f'[{idx}] {cell_type}']
    for line_num, line in enumerate(preview_lines, 1):
        parts.append(f'    {line_num:3d}  {line}')
    if len(source_lines) > 3:
        parts.append(f'         ... ({len(source_lines) - 3} more lines)')
    return '\n'.join(parts)


def nb_cells_insert(
    path: str,
    from_spec: str,
    at: int | None = None,
    dry_run: bool = False,
) -> str:
    """Insert cells from a spec file at a position.

    Args:
        path: Path to .ipynb file.
        from_spec: Path to spec file with cells to insert.
        at: Position to insert at (default: end).
        dry_run: Preview changes without writing.

    Returns:
        Status message.
    """
    p = Path(path)
    if not p.exists():
        return f'Error: {p} not found'

    spec_path = Path(from_spec)
    if not spec_path.exists():
        return f'Error: spec file {spec_path} not found'

    nb = load_notebook(p)
    new_cells = _parse_spec_file(from_spec)
    if not new_cells:
        return 'Error: no cells parsed from spec file'

    cells = nb['cells']
    pos = min(at, len(cells)) if at is not None else len(cells)

    lines = [f'Insert {len(new_cells)} cells at position [{pos}]:']
    for i, cell in enumerate(new_cells):
        lines.append(_format_cell_preview(pos + i, cell))
        lines.append('')

    if dry_run:
        lines.append('(dry run, no changes written)')
        return '\n'.join(lines)

    for i, cell in enumerate(new_cells):
        cells.insert(pos + i, cell)

    save_notebook(nb, p)
    lines.append(f'Saved {p}')
    return '\n'.join(lines)


def nb_cells_append(
    path: str,
    from_spec: str,
    dry_run: bool = False,
) -> str:
    """Append cells from a spec file to end of notebook.

    Args:
        path: Path to .ipynb file.
        from_spec: Path to spec file with cells to append.
        dry_run: Preview changes without writing.

    Returns:
        Status message.
    """
    p = Path(path)
    if not p.exists():
        return f'Error: {p} not found'

    spec_path = Path(from_spec)
    if not spec_path.exists():
        return f'Error: spec file {spec_path} not found'

    nb = load_notebook(p)
    new_cells = _parse_spec_file(from_spec)
    if not new_cells:
        return 'Error: no cells parsed from spec file'

    start_pos = len(nb['cells'])

    lines = [f'Append {len(new_cells)} cells (starting at position [{start_pos}]):']
    for i, cell in enumerate(new_cells):
        lines.append(_format_cell_preview(start_pos + i, cell))
        lines.append('')

    if dry_run:
        lines.append('(dry run, no changes written)')
        return '\n'.join(lines)

    nb['cells'].extend(new_cells)
    save_notebook(nb, p)
    lines.append(f'Saved {p}')
    return '\n'.join(lines)


def nb_cells_move(
    path: str,
    from_pos: int,
    to_pos: int,
    dry_run: bool = False,
) -> str:
    """Move a cell from one position to another.

    Args:
        path: Path to .ipynb file.
        from_pos: Source cell position.
        to_pos: Target cell position.
        dry_run: Preview changes without writing.

    Returns:
        Status message.
    """
    p = Path(path)
    if not p.exists():
        return f'Error: {p} not found'

    nb = load_notebook(p)
    cells = nb['cells']

    if from_pos < 0 or from_pos >= len(cells):
        return f'Error: from_pos {from_pos} out of range (0-{len(cells)-1})'
    if to_pos < 0 or to_pos >= len(cells):
        return f'Error: to_pos {to_pos} out of range (0-{len(cells)-1})'
    if from_pos == to_pos:
        return f'Error: from_pos and to_pos are the same ({from_pos}), nothing to move'

    cell = cells[from_pos]

    lines = [f'Move cell [{from_pos}] -> [{to_pos}]:']
    lines.append(_format_cell_preview(from_pos, cell))
    lines.append('')

    if dry_run:
        lines.append('(dry run, no changes written)')
        return '\n'.join(lines)

    cells.pop(from_pos)
    cells.insert(to_pos, cell)
    save_notebook(nb, p)
    lines.append(f'Saved {p}')
    return '\n'.join(lines)


def nb_cells_find(
    path: str,
    pattern: str | None = None,
    directive: str | None = None,
) -> str:
    """Find cells matching a pattern or directive.

    Args:
        path: Path to .ipynb file.
        pattern: Regex pattern to search for.
        directive: nbdev directive to search for (e.g. 'export').

    Returns:
        Formatted search results.
    """
    if not pattern and not directive:
        return 'Error: provide pattern or directive'

    p = Path(path)
    if not p.exists():
        return f'Error: {p} not found'

    nb = load_notebook(p)
    cells = nb['cells']
    matches = []

    for idx, cell in enumerate(cells):
        source = get_source(cell)

        if pattern:
            if re.search(pattern, source):
                matches.append((idx, cell))
        elif directive:
            d = directive
            if not d.startswith('#|'):
                d = f'#| {d}'
            if d in source or f'#|{directive}' in source:
                matches.append((idx, cell))

    if not matches:
        return 'No matching cells found.'

    lines = [f'Found {len(matches)} matching cells:\n']
    for idx, cell in matches:
        lines.append(_format_cell_preview(idx, cell))
        lines.append('')

    return '\n'.join(lines)


def nb_cells_remove(
    path: str,
    cells: str,
    dry_run: bool = False,
) -> str:
    """Remove cells by index.

    Args:
        path: Path to .ipynb file.
        cells: Comma-separated cell indices to remove.
        dry_run: Preview what would be removed.

    Returns:
        Status message.
    """
    p = Path(path)
    if not p.exists():
        return f'Error: {p} not found'

    try:
        indices = sorted(set(int(x.strip()) for x in cells.split(',')), reverse=True)
    except ValueError:
        return f'Error: invalid cell indices: {cells}'

    nb = load_notebook(p)
    nb_cells = nb['cells']

    bad_indices = [idx for idx in indices if idx < 0 or idx >= len(nb_cells)]
    if bad_indices:
        return (
            f'Error: cell indices out of range (0-{len(nb_cells)-1}): '
            f'{", ".join(str(i) for i in bad_indices)}'
        )

    lines = [f'Remove {len(indices)} cells:']
    for idx in sorted(indices):
        lines.append(_format_cell_preview(idx, nb_cells[idx]))
        lines.append('')

    if dry_run:
        lines.append('(dry run, no changes written)')
        return '\n'.join(lines)

    for idx in indices:  # Already sorted reverse
        nb_cells.pop(idx)

    save_notebook(nb, p)
    lines.append(f'Saved {p}')
    return '\n'.join(lines)


def nb_cells_dispatch(
    path: str,
    action: str,
    at: int | None = None,
    from_spec: str | None = None,
    from_pos: int | None = None,
    to_pos: int | None = None,
    cells: str | None = None,
    pattern: str | None = None,
    directive: str | None = None,
    dry_run: bool = False,
) -> str:
    """Dispatch bulk cell operations by action name.

    Actions: insert, append, move, find, remove.
    """
    if action == 'insert':
        if not from_spec:
            return 'Error: from_spec is required for insert'
        return nb_cells_insert(path, from_spec=from_spec, at=at, dry_run=dry_run)
    elif action == 'append':
        if not from_spec:
            return 'Error: from_spec is required for append'
        return nb_cells_append(path, from_spec=from_spec, dry_run=dry_run)
    elif action == 'move':
        if from_pos is None or to_pos is None:
            return 'Error: from_pos and to_pos are required for move'
        return nb_cells_move(path, from_pos=from_pos, to_pos=to_pos, dry_run=dry_run)
    elif action == 'find':
        return nb_cells_find(path, pattern=pattern, directive=directive)
    elif action == 'remove':
        if not cells:
            return 'Error: cells (comma-separated indices) is required for remove'
        return nb_cells_remove(path, cells=cells, dry_run=dry_run)
    else:
        return f'Error: unknown action "{action}". Use: insert, append, move, find, remove'
