"""Search across Jupyter notebooks.

Use instead of grep/Grep on .ipynb files. Searches actual cell content
and understands notebook structure — showing results with notebook path,
cell index, type, and classification.
"""

import re
from pathlib import Path

from ._common import load_notebook, get_source, get_directives, classify_cell, find_notebooks


def _match_directive(source, directive):
    """Check if a cell's source contains the given directive."""
    if not directive.startswith('#|'):
        directive_pattern = f'#| {directive}'
        directive_compact = f'#|{directive}'
    else:
        directive_pattern = directive
        directive_compact = directive.replace('#| ', '#|')

    return directive_pattern in source or directive_compact in source


def _first_meaningful_line(source):
    """Get the first non-directive, non-empty line from cell source."""
    for line in source.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('#|'):
            return stripped
    first = source.strip().split('\n')[0] if source.strip() else ''
    return first


def _format_cell_tag(cell_type, classification):
    """Format the TYPE (classification) tag."""
    ct = cell_type.upper()
    if classification in ('unknown',):
        return ct
    return f'{ct} ({classification})'


def _format_compact(nb_path, idx, cell_type, classification, source, compiled):
    """Format a single compact result line."""
    tag = _format_cell_tag(cell_type, classification)

    if compiled:
        for line in source.split('\n'):
            if compiled.search(line):
                preview = line.strip()[:80]
                return f'{nb_path}:[{idx}] {tag}: {preview}'

    preview = _first_meaningful_line(source)[:80]
    return f'{nb_path}:[{idx}] {tag}: {preview}'


def _format_context(nb_path, idx, cell_type, classification, source, compiled, context_lines):
    """Format a match with context lines around matching lines."""
    tag = _format_cell_tag(cell_type, classification)
    header = f'{nb_path}:[{idx}] {tag}'

    lines = source.split('\n')

    if compiled:
        matching_indices = {i for i, line in enumerate(lines) if compiled.search(line)}
    else:
        matching_indices = set(range(min(3, len(lines))))

    if not matching_indices and not compiled:
        return header

    show_indices = set()
    for mi in matching_indices:
        for c in range(max(0, mi - context_lines), min(len(lines), mi + context_lines + 1)):
            show_indices.add(c)

    result = [header]
    prev_idx = -2
    for i in sorted(show_indices):
        if i > prev_idx + 1 and prev_idx >= 0:
            result.append('       ...')
        marker = '  > ' if i in matching_indices else '    '
        result.append(f'{marker}{i + 1:3d}  {lines[i]}')
        prev_idx = i

    return '\n'.join(result)


def nb_search(
    path: str,
    pattern: str | None = None,
    directive: str | None = None,
    cell_type: str | None = None,
    ignore_case: bool = False,
    files_only: bool = False,
    context: int = 0,
) -> str:
    """Search across notebooks for content, directives, or cell types.

    Args:
        path: Notebook file or directory to search.
        pattern: Regex pattern to search for in cell content.
        directive: nbdev directive to search for (e.g. 'export', 'hide').
        cell_type: Only search cells of this type ('code', 'markdown', 'raw').
        ignore_case: Case-insensitive pattern matching.
        files_only: Show only notebook paths with matches (like grep -l).
        context: Lines of context around matches (0 = compact mode).

    Returns:
        Search results text.
    """
    if not pattern and not directive and not cell_type:
        return 'Error: provide at least one of pattern, directive, or cell_type'

    notebooks = find_notebooks(path)
    if not notebooks:
        return f'Error: no .ipynb files found at {path}'

    flags = re.IGNORECASE if ignore_case else 0
    compiled = None
    if pattern:
        try:
            compiled = re.compile(pattern, flags)
        except re.error as e:
            return f'Error: invalid regex pattern: {e}'

    all_results = []
    files_with_matches = 0

    for nb_path in notebooks:
        try:
            nb = load_notebook(nb_path)
        except Exception:
            continue

        cells = nb.get('cells', [])
        matches = []

        for idx, cell in enumerate(cells):
            ct = cell.get('cell_type', 'unknown')

            if cell_type and ct != cell_type:
                continue

            source = get_source(cell)
            classification = classify_cell(cell)

            if directive and not _match_directive(source, directive):
                continue

            if pattern and not compiled.search(source):
                continue

            if files_only:
                all_results.append(str(nb_path))
                files_with_matches += 1
                break

            if context > 0:
                matches.append(_format_context(
                    nb_path, idx, ct, classification, source, compiled, context))
            else:
                matches.append(_format_compact(
                    nb_path, idx, ct, classification, source, compiled))

        if matches:
            files_with_matches += 1
            all_results.extend(matches)
            if context > 0:
                all_results.append('')

    if not all_results:
        return 'No matches found.'

    return '\n'.join(all_results)
