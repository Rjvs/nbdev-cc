"""Validate Jupyter notebook structure and nbdev conventions.

Catches structural problems before they reach nbdev commands where
errors can be cryptic.
"""

import json
import re
from pathlib import Path

from ._common import get_source, find_notebooks, validate_path

CELL_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')


class _ValidationResult:
    def __init__(self, path):
        self.path = path
        self.errors = []
        self.warnings = []

    def error(self, msg, cell_idx=None):
        prefix = f'  cell [{cell_idx}]: ' if cell_idx is not None else '  '
        self.errors.append(f'{prefix}{msg}')

    def warn(self, msg, cell_idx=None):
        prefix = f'  cell [{cell_idx}]: ' if cell_idx is not None else '  '
        self.warnings.append(f'{prefix}{msg}')

    @property
    def ok(self):
        return len(self.errors) == 0

    def report(self, strict=False):
        lines = []
        effective_errors = self.errors + (self.warnings if strict else [])
        if effective_errors:
            lines.append(f'FAIL {self.path}')
            for e in self.errors:
                lines.append(f'  ERROR {e}')
            for w in self.warnings:
                if strict:
                    lines.append(f'  ERROR {w}')
                else:
                    lines.append(f'  WARN  {w}')
        else:
            lines.append(f'OK   {self.path} ({self._summary()})')
        return '\n'.join(lines)

    def _summary(self):
        parts = []
        if self.warnings:
            parts.append(f'{len(self.warnings)} warnings')
        return ', '.join(parts) if parts else 'clean'


def _validate_one(path):
    """Validate a single notebook file. Returns _ValidationResult."""
    result = _ValidationResult(path)

    try:
        with open(path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
    except json.JSONDecodeError as e:
        result.error(f'Invalid JSON: {e}')
        return result
    except Exception as e:
        result.error(f'Cannot read file: {e}')
        return result

    if not isinstance(nb, dict):
        result.error('Notebook root must be a JSON object')
        return result

    for field in ('nbformat', 'metadata', 'cells'):
        if field not in nb:
            result.error(f'Missing required field: {field}')

    if 'nbformat' in nb and nb['nbformat'] != 4:
        result.error(f'Unsupported nbformat: {nb["nbformat"]} (expected 4)')

    if 'cells' not in nb:
        return result

    cells = nb['cells']
    if not isinstance(cells, list):
        result.error('"cells" must be an array')
        return result

    if len(cells) == 0:
        result.warn('Notebook has no cells')
        return result

    metadata = nb.get('metadata', {})
    if not isinstance(metadata, dict):
        result.error('"metadata" must be an object')
    elif 'kernelspec' not in metadata:
        result.warn('Missing kernelspec in metadata')

    seen_ids = {}
    has_default_exp = False

    for idx, cell in enumerate(cells):
        if not isinstance(cell, dict):
            result.error(f'Cell must be an object, got {type(cell).__name__}', idx)
            continue

        cell_type = cell.get('cell_type')
        if cell_type not in ('code', 'markdown', 'raw'):
            result.error(f'Invalid cell_type: {cell_type!r}', idx)
            continue

        cell_id = cell.get('id')
        if cell_id is None:
            result.warn('Missing cell id', idx)
        elif not isinstance(cell_id, str):
            result.error(f'Cell id must be string, got {type(cell_id).__name__}', idx)
        elif not CELL_ID_PATTERN.match(cell_id):
            result.error(f'Invalid cell id format: {cell_id!r}', idx)
        elif len(cell_id) > 64:
            result.error(f'Cell id too long ({len(cell_id)} chars, max 64)', idx)
        else:
            if cell_id in seen_ids:
                result.error(f'Duplicate cell id: {cell_id!r} (also at cell [{seen_ids[cell_id]}])', idx)
            seen_ids[cell_id] = idx

        source = cell.get('source')
        if source is None:
            result.error('Missing "source" field', idx)
        elif not isinstance(source, (str, list)):
            result.error(f'"source" must be string or array, got {type(source).__name__}', idx)
        elif isinstance(source, list):
            for i, item in enumerate(source):
                if not isinstance(item, str):
                    result.error(f'"source" array item [{i}] must be string, got {type(item).__name__}', idx)
                    break

        if 'metadata' not in cell:
            result.warn('Missing cell metadata (should be at least {})', idx)
        elif not isinstance(cell.get('metadata'), dict):
            result.error(f'Cell metadata must be object, got {type(cell.get("metadata")).__name__}', idx)

        if cell_type == 'code':
            if 'outputs' not in cell:
                result.error('Code cell missing "outputs" field', idx)
            elif not isinstance(cell['outputs'], list):
                result.error(f'"outputs" must be array, got {type(cell["outputs"]).__name__}', idx)

            if 'execution_count' not in cell:
                result.error('Code cell missing "execution_count" field', idx)
            else:
                ec = cell['execution_count']
                if ec is not None and not isinstance(ec, int):
                    result.error(f'"execution_count" must be int or null, got {type(ec).__name__}', idx)

            source_text = get_source(cell)
            if '#| default_exp' in source_text:
                has_default_exp = True

        if cell_type == 'code' and isinstance(cell.get('outputs'), list):
            for out_idx, output in enumerate(cell['outputs']):
                if not isinstance(output, dict):
                    result.error(f'Output [{out_idx}] must be object', idx)
                    continue
                out_type = output.get('output_type')
                if out_type not in ('stream', 'execute_result', 'display_data', 'error'):
                    result.error(f'Output [{out_idx}] invalid output_type: {out_type!r}', idx)

    if not has_default_exp:
        result.warn('No #| default_exp directive found (expected in first code cell)')

    for idx, cell in enumerate(cells):
        if cell.get('cell_type') == 'code':
            source_text = get_source(cell)
            if '#| default_exp' not in source_text and has_default_exp:
                result.warn('First code cell should contain #| default_exp', idx)
            break

    return result


def nb_validate(
    paths: str | list[str],
    strict: bool = False,
) -> str:
    """Validate notebook structure and nbdev conventions.

    Args:
        paths: Notebook file(s) or director(ies) to validate.
        strict: Treat warnings as errors.

    Returns:
        Validation report text.
    """
    if isinstance(paths, str):
        paths = [paths]

    all_results = []
    for path in paths:
        _, err = validate_path(path)
        if err:
            return err
        notebooks = find_notebooks(path)
        if not notebooks:
            continue
        for nb_path in notebooks:
            result = _validate_one(nb_path)
            all_results.append(result)

    if not all_results:
        return 'No notebooks to validate.'

    lines = []
    for result in all_results:
        lines.append(result.report(strict=strict))

    total = len(all_results)
    failed = sum(1 for r in all_results if not r.ok or (strict and r.warnings))
    passed = total - failed

    summary = f'\n{passed}/{total} passed'
    if not strict:
        total_warnings = sum(len(r.warnings) for r in all_results)
        if total_warnings:
            summary += f' ({total_warnings} warnings)'

    lines.append(summary)
    return '\n'.join(lines)
