#!/usr/bin/env python3
"""Standalone notebook execution script.

This script runs in the *project's* Python environment (not the MCP
server's), so it must be self-contained — no imports from nbdev_mcp.

It duplicates a few small helpers (get_source, get_directives, classify_cell)
that also exist in _common.py, but that's intentional: this file executes
as a subprocess in a completely different interpreter.

Invoked by run.py via:
    python /path/to/_runner.py /path/to/notebook.ipynb [--cell N] [--upto N] ...
"""

import argparse
import re
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Utility functions (self-contained copies for subprocess isolation)
# ---------------------------------------------------------------------------

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')


def get_source(cell):
    """Extract source text from a cell."""
    source = cell.get('source', '')
    return ''.join(source) if isinstance(source, list) else source


def get_directives(source):
    """Extract #| directive lines from cell source."""
    directives = []
    for line in source.split('\n'):
        stripped = line.strip()
        if stripped.startswith('#|'):
            directives.append(stripped)
        elif stripped and not stripped.startswith('#'):
            break
    return directives


def should_skip(cell):
    """Return True if the cell should not be executed."""
    if cell.cell_type != 'code':
        return True
    source = get_source(cell)
    if not source.strip():
        return True
    for d in get_directives(source):
        text = d[2:].strip()
        if text.startswith('eval:') and 'false' in text:
            return True
    return False


def classify_cell(cell):
    """Classify a cell as export, test, hidden, etc."""
    if cell.cell_type != 'code':
        return cell.cell_type
    source = get_source(cell)
    for d in get_directives(source):
        text = d[2:].strip()
        if text.startswith('default_exp'):
            return 'default_exp'
        if text.startswith('export'):
            if text.startswith('exporti'):
                return 'exporti'
            if text.startswith('exports'):
                return 'exports'
            return 'export'
        if text.startswith('hide'):
            return 'hidden'
    return 'test'


def format_tag(classification):
    """Return a parenthesized tag for display, or empty string."""
    if classification in ('export', 'exporti', 'exports', 'default_exp', 'test', 'hidden'):
        return f' ({classification})'
    return ''


def format_outputs(cell):
    """Format cell outputs for display."""
    lines = []
    for out in cell.get('outputs', []):
        out_type = out.get('output_type', 'unknown')
        if out_type == 'stream':
            name = out.get('name', 'stdout')
            text = ''.join(out.get('text', []))
            if text.strip():
                prefix = '' if name == 'stdout' else f'[{name}] '
                for line in text.rstrip('\n').split('\n'):
                    lines.append(f'    {prefix}{line}')
        elif out_type in ('execute_result', 'display_data'):
            data = out.get('data', {})
            if 'text/plain' in data:
                text = data['text/plain']
                if isinstance(text, list):
                    text = ''.join(text)
                for line in text.rstrip('\n').split('\n'):
                    lines.append(f'    {line}')
            else:
                mime_types = list(data.keys())
                lines.append(f'    [output: {", ".join(mime_types)}]')
        elif out_type == 'error':
            ename = out.get('ename', 'Error')
            evalue = out.get('evalue', '')
            tb = out.get('traceback', [])
            if tb:
                for tb_entry in tb[-3:]:
                    clean = ANSI_ESCAPE.sub('', tb_entry)
                    for part in clean.split('\n'):
                        if part.strip():
                            lines.append(f'    {part}')
            else:
                lines.append(f'    {ename}: {evalue}')
    return lines


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main():
    try:
        import nbformat
        from nbclient import NotebookClient
        from nbclient.exceptions import CellExecutionError
    except ImportError:
        print("Error: nbformat and nbclient are required for nb_run.")
        print("Install with:  pip install nbformat nbclient")
        print("  or:          uv add nbformat nbclient")
        sys.exit(2)

    parser = argparse.ArgumentParser(description='Execute notebook cells in batch.')
    parser.add_argument('notebook', help='Path to .ipynb file')
    range_group = parser.add_mutually_exclusive_group()
    range_group.add_argument('--cell', type=int, default=None, help='Execute a single cell')
    range_group.add_argument('--upto', type=int, default=None, help='Execute cells 0..N')
    range_group.add_argument('--range', type=str, default=None, help='Cell range like 2-5')
    parser.add_argument('--allow-errors', action='store_true', help='Continue after cell errors')
    parser.add_argument('--save', action='store_true', help='Write outputs back to notebook')
    parser.add_argument('--timeout', type=int, default=600, help='Per-cell timeout in seconds')
    parser.add_argument('--kernel', type=str, default=None, help='Kernel name override')
    args = parser.parse_args()

    path = Path(args.notebook)
    nb = nbformat.read(str(path), as_version=4)
    cells = nb.cells
    total = len(cells)

    if total == 0:
        print(f'=== {path.name} — No cells ===')
        sys.exit(0)

    # Resolve cell indices
    if args.cell is not None:
        visit = [args.cell]
    elif args.upto is not None:
        visit = list(range(0, min(args.upto, total - 1) + 1))
    elif args.range:
        parts = args.range.split('-')
        start, end = max(0, int(parts[0])), min(int(parts[1]), total - 1)
        visit = list(range(start, end + 1))
    else:
        visit = list(range(total))

    kernel_name = args.kernel or nb.metadata.get('kernelspec', {}).get('name', 'python3')
    print(f'=== {path.name} — Executing (kernel: {kernel_name}) ===')
    print()

    client = NotebookClient(nb, timeout=args.timeout, kernel_name=kernel_name)
    passed = failed = 0

    try:
        with client.setup_kernel():
            for idx in visit:
                cell = cells[idx]
                classification = classify_cell(cell)
                source = get_source(cell)
                tag = format_tag(classification)

                if should_skip(cell):
                    if cell.cell_type != 'code':
                        first_line = source.strip().split('\n')[0][:80] if source.strip() else '(empty)'
                        print(f'[{idx}] {cell.cell_type.upper()} — {first_line}')
                    elif not source.strip():
                        print(f'[{idx}] CODE{tag} — (empty, skipped)')
                    else:
                        print(f'[{idx}] CODE{tag} — (eval: false, skipped)')
                    continue

                source_lines = source.strip().split('\n')
                num_lines = len(source_lines)
                print(f'[{idx}] CODE{tag} ({num_lines} line{"s" if num_lines != 1 else ""})')
                for line in source_lines[:5]:
                    print(f'    {line}')
                if len(source_lines) > 5:
                    print(f'    ... ({len(source_lines) - 5} more lines)')

                start_time = time.time()
                try:
                    client.execute_cell(cell, idx)
                    elapsed = time.time() - start_time
                    output_lines = format_outputs(cell)
                    for line in output_lines:
                        print(line)
                    print(f'  -> ok ({elapsed:.1f}s)')
                    passed += 1
                except CellExecutionError:
                    elapsed = time.time() - start_time
                    output_lines = format_outputs(cell)
                    for line in output_lines:
                        print(line)
                    print(f'  -> FAILED ({elapsed:.1f}s)')
                    failed += 1
                    if not args.allow_errors:
                        print(f'\nStopping at cell {idx} (use allow_errors to continue)')
                        break
                print()
    except Exception as e:
        print(f'\nKernel error: {e}', file=sys.stderr)
        sys.exit(2)

    executed = passed + failed
    parts = [f'{passed} passed', f'{failed} failed'] if failed else [f'{passed} passed']
    print(f'=== {executed} cells executed: {", ".join(parts)} ===')

    if args.save:
        nbformat.write(nb, str(path))
        print(f'Outputs saved to {path}')

    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
