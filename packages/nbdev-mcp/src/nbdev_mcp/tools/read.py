"""Human-readable notebook viewer.

Use instead of Read/cat on .ipynb files. Renders cell content with cell
numbers, types, directives, and structure — ready to act on without
mental JSON parsing.
"""

import json
from pathlib import Path

from ._common import load_notebook, get_source, get_directives, classify_cell

_range = range  # preserve built-in before parameter shadowing


def _get_default_exp(nb):
    """Find the default_exp module name from the notebook."""
    for cell in nb.get('cells', []):
        if cell.get('cell_type') != 'code':
            continue
        source = get_source(cell)
        for line in source.split('\n'):
            stripped = line.strip()
            if stripped.startswith('#| default_exp'):
                parts = stripped.split(None, 2)
                if len(parts) >= 3:
                    return parts[2]
    return None


def _format_cell_header(idx, cell, classification):
    """Format the header line for a cell."""
    cell_type = cell.get('cell_type', 'unknown').upper()

    tag = ''
    if classification in ('export', 'exporti', 'exports', 'default_exp'):
        tag = f' ({classification})'
    elif classification == 'test':
        tag = ' (test)'
    elif classification == 'hidden':
        tag = ' (hidden)'

    cell_id = cell.get('id', '')
    id_str = f'  id={cell_id}' if cell_id else ''

    return f'[{idx}] {cell_type}{tag}{id_str}'


def _format_cell_full(idx, cell, classification):
    """Format a complete cell view with line numbers."""
    header = _format_cell_header(idx, cell, classification)
    source = get_source(cell)
    lines = [header]

    if source.strip():
        source_lines = source.split('\n')
        for line_num, line in enumerate(source_lines, 1):
            lines.append(f'    {line_num:3d}  {line}')
    else:
        lines.append('    (empty)')

    # Show outputs summary for code cells
    if cell.get('cell_type') == 'code':
        outputs = cell.get('outputs', [])
        if outputs:
            lines.append('')
            lines.append(f'    --- outputs ({len(outputs)}) ---')
            for out in outputs:
                out_type = out.get('output_type', 'unknown')
                if out_type == 'stream':
                    name = out.get('name', 'stdout')
                    text = ''.join(out.get('text', []))
                    preview = text.strip()[:100]
                    lines.append(f'    [{name}] {preview}')
                elif out_type in ('execute_result', 'display_data'):
                    data = out.get('data', {})
                    if 'text/plain' in data:
                        text = ''.join(data['text/plain']) if isinstance(data['text/plain'], list) else data['text/plain']
                        preview = text.strip()[:100]
                        lines.append(f'    [result] {preview}')
                    else:
                        mime_types = list(data.keys())
                        lines.append(f'    [result] MIME types: {", ".join(mime_types)}')
                elif out_type == 'error':
                    ename = out.get('ename', 'Error')
                    evalue = out.get('evalue', '')
                    lines.append(f'    [error] {ename}: {evalue}')

    return '\n'.join(lines)


def _format_cell_outline(idx, cell, classification):
    """Format a brief outline view of a cell."""
    header = _format_cell_header(idx, cell, classification)
    source = get_source(cell)

    first_line = ''
    for i, line in enumerate(source.split('\n')):
        stripped = line.strip()
        if stripped and not stripped.startswith('#|'):
            first_line = stripped[:80]
            if first_line.startswith('@'):
                for next_line in source.split('\n')[i+1:]:
                    next_stripped = next_line.strip()
                    if next_stripped and not next_stripped.startswith('#|'):
                        first_line = f'{first_line}; {next_stripped}'[:80]
                        break
            break

    if not first_line:
        directives = get_directives(source)
        if directives:
            first_line = directives[0]
        elif source.strip():
            first_line = source.strip().split('\n')[0][:80]

    if first_line:
        return f'{header}\n    {first_line}'
    return header


def _parse_range(range_str):
    """Parse a range string like '2-5' into (start, end) tuple."""
    parts = range_str.split('-')
    return (int(parts[0]), int(parts[1]))


def nb_read(
    path: str,
    outline: bool = False,
    cell: int | None = None,
    exports: bool = False,
    tests: bool = False,
    markdown: bool = False,
    range: str | None = None,
    flag: str | None = None,
) -> str:
    """Read a notebook in human-readable format.

    Args:
        path: Path to .ipynb file.
        outline: Show structure only (cell types + first line).
        cell: Show single cell by index.
        exports: Show only exported cells.
        tests: Show only test cells (non-exported code).
        markdown: Show only markdown cells.
        range: Cell range like '2-5'.
        flag: Show only cells containing this marker (e.g. 'todo:').

    Returns:
        Human-readable notebook text.
    """
    p = Path(path)
    if not p.exists():
        return f'Error: {p} not found'
    if p.suffix != '.ipynb':
        return f'Error: {p} is not a .ipynb file'

    try:
        nb = load_notebook(p)
    except json.JSONDecodeError as e:
        return f'Error: Invalid JSON in {p}: {e}'

    cells = nb.get('cells', [])
    default_exp = _get_default_exp(nb)

    mode = 'outline' if outline else 'full'

    cell_filter = None
    if exports:
        cell_filter = 'exports'
    elif tests:
        cell_filter = 'tests'
    elif markdown:
        cell_filter = 'markdown'
    elif flag:
        cell_filter = f'flag:{flag}'

    cell_range = None
    if range:
        try:
            cell_range = _parse_range(range)
        except (ValueError, IndexError):
            return f'Error: Invalid range format "{range}". Use e.g. 2-5'

    # Build output
    lines = []
    name = p.name
    module_info = f'  Module: {default_exp}' if default_exp else ''
    lines.append(f'=== {name} ({len(cells)} cells){module_info} ===')
    lines.append('')

    indices = _range(len(cells))
    if cell is not None:
        if 0 <= cell < len(cells):
            indices = [cell]
        else:
            return f'Error: cell index {cell} out of range (0-{len(cells)-1})'
    elif cell_range is not None:
        start, end = cell_range
        start = max(0, start)
        end = min(len(cells) - 1, end)
        indices = _range(start, end + 1)

    for idx in indices:
        c = cells[idx]
        classification = classify_cell(c)

        if cell_filter:
            if cell_filter == 'exports' and classification not in ('export', 'exporti', 'exports'):
                continue
            elif cell_filter == 'tests' and classification != 'test':
                continue
            elif cell_filter == 'markdown' and c.get('cell_type') != 'markdown':
                continue
            elif cell_filter.startswith('flag:'):
                marker = cell_filter[5:]
                if marker not in get_source(c):
                    continue

        if mode == 'outline':
            lines.append(_format_cell_outline(idx, c, classification))
        else:
            lines.append(_format_cell_full(idx, c, classification))
        lines.append('')

    return '\n'.join(lines)
