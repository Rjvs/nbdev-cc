"""Shared utilities for notebook tools."""

import hashlib
import json
from pathlib import Path


def load_notebook(path):
    """Load and return notebook dict from .ipynb file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_notebook(nb, path):
    """Save notebook to file, matching nbdev's JSON formatting."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write('\n')


def get_source(cell):
    """Extract source text from a cell, handling both string and array formats."""
    source = cell.get('source', '')
    if isinstance(source, list):
        return ''.join(source)
    return source


def source_to_array(source):
    """Convert source text to the array-of-lines format.

    Each line ends with \\n except the last.
    """
    if not source:
        return []
    lines = source.split('\n')
    result = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            result.append(line + '\n')
        else:
            if line:  # Don't add empty trailing line
                result.append(line)
    return result


def get_directives(source):
    """Extract nbdev directives from cell source."""
    directives = []
    for line in source.split('\n'):
        stripped = line.strip()
        if stripped.startswith('#|'):
            directives.append(stripped)
        elif stripped and not stripped.startswith('#'):
            break  # Non-comment, non-empty line ends directive block
    return directives


def classify_cell(cell):
    """Classify a code cell as export, test, hidden, or other."""
    if cell.get('cell_type') != 'code':
        return cell.get('cell_type', 'unknown')

    source = get_source(cell)
    directives = get_directives(source)

    for d in directives:
        directive_text = d[2:].strip()  # Remove #|
        if directive_text.startswith('default_exp'):
            return 'default_exp'
        if directive_text.startswith('export'):
            if directive_text.startswith('exporti'):
                return 'exporti'
            if directive_text.startswith('exports'):
                return 'exports'
            return 'export'
        if directive_text.startswith('hide'):
            return 'hidden'

    # Non-exported code cell = test
    return 'test'


def generate_cell_id(index=0, content=''):
    """Generate a deterministic cell ID from index and content."""
    seed = f'{index}:{content[:50]}'
    return hashlib.sha256(seed.encode()).hexdigest()[:8]


def parse_spec(content):
    """Parse cell spec text into (cell_type, source) tuples.

    Spec format: cells separated by ``\\n---``, each starting with a type
    line (``code``, ``markdown``, or ``raw``) followed by the source.
    """
    cells = []
    parts = content.split('\n---')

    for part in parts:
        part = part.strip()
        if not part:
            continue

        lines = part.split('\n', 1)
        cell_type = lines[0].strip().lower()

        if cell_type not in ('code', 'markdown', 'raw'):
            if ' ' in cell_type:
                parts2 = cell_type.split(None, 1)
                if parts2[0] == '---':
                    cell_type = parts2[1] if len(parts2) > 1 else ''
                else:
                    continue
            else:
                continue

        if cell_type not in ('code', 'markdown', 'raw'):
            continue

        source = lines[1] if len(lines) > 1 else ''
        if source.startswith('\n'):
            source = source[1:]

        cells.append((cell_type, source))

    return cells


def find_notebooks(path):
    """Find all .ipynb files under a path. Skips checkpoint directories."""
    p = Path(path)
    if p.is_file():
        if p.suffix == '.ipynb':
            return [p]
        return []
    elif p.is_dir():
        notebooks = sorted(p.rglob('*.ipynb'))
        return [nb for nb in notebooks if '.ipynb_checkpoints' not in str(nb)]
    else:
        return []
