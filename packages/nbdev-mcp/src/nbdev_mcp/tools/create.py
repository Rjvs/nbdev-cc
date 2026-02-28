"""Create notebooks from plain text.

Generates valid .ipynb files with proper metadata, unique cell IDs, and
correct structure. Avoids error-prone manual JSON construction.
"""

import json
import platform
from pathlib import Path

from ._common import source_to_array, generate_cell_id, parse_spec, validate_notebook_path, validate_path


def _make_code_cell(source, index=0):
    """Create a code cell dict."""
    return {
        'cell_type': 'code',
        'id': generate_cell_id(index, source),
        'metadata': {},
        'source': source_to_array(source),
        'outputs': [],
        'execution_count': None,
    }


def _make_markdown_cell(source, index=0):
    """Create a markdown cell dict."""
    return {
        'cell_type': 'markdown',
        'id': generate_cell_id(index, source),
        'metadata': {},
        'source': source_to_array(source),
    }


def _make_notebook(cells):
    """Create a complete notebook dict."""
    return {
        'nbformat': 4,
        'nbformat_minor': 5,
        'metadata': {
            'kernelspec': {
                'name': 'python3',
                'display_name': 'Python 3',
                'language': 'python',
            },
            'language_info': {
                'name': 'python',
                'version': platform.python_version(),
                'codemirror_mode': {'name': 'ipython', 'version': 3},
                'file_extension': '.py',
                'mimetype': 'text/x-python',
                'pygments_lexer': 'ipython3',
            },
        },
        'cells': cells,
    }


def _validate_notebook(nb):
    """Quick structural validation. Returns list of error strings."""
    errors = []
    if not isinstance(nb.get('cells'), list):
        errors.append('cells is not a list')
        return errors

    seen_ids = set()
    for idx, cell in enumerate(nb['cells']):
        ct = cell.get('cell_type')
        if ct not in ('code', 'markdown', 'raw'):
            errors.append(f'cell [{idx}]: invalid cell_type {ct!r}')
        if 'source' not in cell:
            errors.append(f'cell [{idx}]: missing source')
        if 'id' not in cell:
            errors.append(f'cell [{idx}]: missing id')
        elif cell['id'] in seen_ids:
            errors.append(f'cell [{idx}]: duplicate id {cell["id"]!r}')
        else:
            seen_ids.add(cell['id'])
        if ct == 'code':
            if 'outputs' not in cell:
                errors.append(f'cell [{idx}]: code cell missing outputs')
            if 'execution_count' not in cell:
                errors.append(f'cell [{idx}]: code cell missing execution_count')
    return errors


def nb_create(
    out: str,
    module: str | None = None,
    title: str | None = None,
    from_spec: str | None = None,
    force: bool = False,
) -> str:
    """Create a notebook from a spec file or minimal module template.

    Args:
        out: Output .ipynb path.
        module: Module name for default_exp (creates minimal notebook).
        title: Notebook title (used with module).
        from_spec: Path to spec file to create from.
        force: Overwrite existing file.

    Returns:
        Status message.
    """
    out_path, err = validate_notebook_path(out, must_exist=False)
    if err:
        return err
    if out_path.exists() and not force:
        return f'Error: {out_path} already exists. Use force=True to overwrite.'

    if from_spec:
        spec_path, err = validate_path(from_spec)
        if err:
            return err
        with open(spec_path, 'r', encoding='utf-8') as f:
            content = f.read()
        cell_specs = parse_spec(content)
        cells = []
        for i, (cell_type, source) in enumerate(cell_specs):
            if cell_type == 'code':
                cells.append(_make_code_cell(source, index=i))
            elif cell_type == 'markdown':
                cells.append(_make_markdown_cell(source, index=i))
            elif cell_type == 'raw':
                cells.append({
                    'cell_type': 'raw',
                    'id': generate_cell_id(i, source),
                    'metadata': {},
                    'source': source_to_array(source),
                })
    elif module:
        cells = []
        cells.append(_make_code_cell(f'#| default_exp {module}', index=0))
        pretty = title or module.replace('_', ' ').title()
        cells.append(_make_markdown_cell(f'# {pretty}', index=1))
        cells.append(_make_code_cell('#| export\n', index=2))
    else:
        return 'Error: provide either from_spec or module'

    if not cells:
        return 'Error: no cells generated'

    nb = _make_notebook(cells)

    errors = _validate_notebook(nb)
    if errors:
        return 'Error: generated notebook has structural problems:\n' + '\n'.join(f'  {e}' for e in errors)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write('\n')

    return f'Created {out_path} with {len(cells)} cells'
