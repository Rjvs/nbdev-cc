"""Execute notebook cells in batch.

Starts a fresh kernel, executes cells sequentially, and reports outputs.
Uses subprocess to run in the project's Python environment (since the
MCP server runs in its own isolated env via uvx).
"""

import os
import subprocess
from pathlib import Path


def nb_run(
    path: str,
    cell: int | None = None,
    upto: int | None = None,
    range: str | None = None,
    save: bool = False,
    allow_errors: bool = False,
    timeout: int = 600,
    kernel: str | None = None,
) -> str:
    """Execute notebook cells in batch.

    Runs cells in a fresh kernel in the project's Python environment.
    Prefer --upto or --range over calling --cell in a loop.

    Args:
        path: Path to .ipynb file.
        cell: Execute a single cell by index.
        upto: Execute cells 0 through N (inclusive).
        range: Cell range like '2-5' (inclusive).
        save: Write execution outputs back to the notebook file.
        allow_errors: Continue execution after cell errors.
        timeout: Per-cell timeout in seconds (default: 600).
        kernel: Kernel name (default: from notebook metadata).

    Returns:
        Execution output text.
    """
    p = Path(path)
    if not p.exists():
        return f'Error: {p} not found'
    if p.suffix != '.ipynb':
        return f'Error: {p} is not a .ipynb file'

    # Build the command to run nb_run as a subprocess in the project env.
    # We use an inline Python script that imports nbformat/nbclient.
    script = _build_execution_script(str(p.resolve()), cell, upto, range,
                                     save, allow_errors, timeout, kernel)

    # Try uv run first (project env), fall back to plain python
    cwd = str(p.parent.resolve()) if p.parent != Path('.') else os.getcwd()

    for cmd in [
        ['uv', 'run', 'python', '-c', script],
        ['python3', '-c', script],
        ['python', '-c', script],
    ]:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 60,  # buffer beyond per-cell timeout
                cwd=cwd,
            )
            output = result.stdout
            if result.stderr and result.returncode != 0:
                output += f'\n{result.stderr}'
            return output if output.strip() else f'Execution completed (exit code {result.returncode})'
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return f'Error: execution timed out after {timeout + 60}s'

    return 'Error: could not find python or uv to execute notebook'


def _build_execution_script(abs_path, cell, upto, range_str, save, allow_errors, timeout, kernel):
    """Build inline Python script for subprocess execution."""
    # We construct the equivalent of the standalone nb_run tool,
    # but as a single -c script string.
    args = [abs_path]
    if cell is not None:
        args.extend(['--cell', str(cell)])
    elif upto is not None:
        args.extend(['--upto', str(upto)])
    elif range_str is not None:
        args.extend(['--range', range_str])
    if save:
        args.append('--save')
    if allow_errors:
        args.append('--allow-errors')
    if timeout != 600:
        args.extend(['--timeout', str(timeout)])
    if kernel:
        args.extend(['--kernel', kernel])

    # Encode as a quoted list for sys.argv injection
    import shlex
    argv_str = ', '.join(repr(a) for a in args)

    return f'''
import sys, re, time
from pathlib import Path

sys.argv = ['nb_run', {argv_str}]

try:
    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError
except ImportError:
    print("Error: nbformat and nbclient are required for nb_run.")
    print("Install with: uv pip install nbformat nbclient")
    sys.exit(2)

ANSI_ESCAPE = re.compile(r'\\x1b\\[[0-9;]*m')

def get_source(cell):
    source = cell.get('source', '')
    return ''.join(source) if isinstance(source, list) else source

def get_directives(source):
    directives = []
    for line in source.split('\\n'):
        stripped = line.strip()
        if stripped.startswith('#|'): directives.append(stripped)
        elif stripped and not stripped.startswith('#'): break
    return directives

def should_skip(cell):
    if cell.cell_type != 'code': return True
    source = get_source(cell)
    if not source.strip(): return True
    for d in get_directives(source):
        text = d[2:].strip()
        if text.startswith('eval:') and 'false' in text: return True
    return False

def classify_cell(cell):
    if cell.cell_type != 'code': return cell.cell_type
    source = get_source(cell)
    for d in get_directives(source):
        text = d[2:].strip()
        if text.startswith('default_exp'): return 'default_exp'
        if text.startswith('export'):
            if text.startswith('exporti'): return 'exporti'
            if text.startswith('exports'): return 'exports'
            return 'export'
        if text.startswith('hide'): return 'hidden'
    return 'test'

def format_tag(classification):
    if classification in ('export', 'exporti', 'exports', 'default_exp', 'test', 'hidden'):
        return f' ({{classification}})'
    return ''

def format_outputs(cell):
    lines = []
    for out in cell.get('outputs', []):
        out_type = out.get('output_type', 'unknown')
        if out_type == 'stream':
            name = out.get('name', 'stdout')
            text = ''.join(out.get('text', []))
            if text.strip():
                prefix = '' if name == 'stdout' else f'[{{name}}] '
                for line in text.rstrip('\\n').split('\\n'):
                    lines.append(f'    {{prefix}}{{line}}')
        elif out_type in ('execute_result', 'display_data'):
            data = out.get('data', {{}})
            if 'text/plain' in data:
                text = data['text/plain']
                if isinstance(text, list): text = ''.join(text)
                for line in text.rstrip('\\n').split('\\n'):
                    lines.append(f'    {{line}}')
            else:
                mime_types = list(data.keys())
                lines.append(f'    [output: {{", ".join(mime_types)}}]')
        elif out_type == 'error':
            ename = out.get('ename', 'Error')
            evalue = out.get('evalue', '')
            tb = out.get('traceback', [])
            if tb:
                for tb_entry in tb[-3:]:
                    clean = ANSI_ESCAPE.sub('', tb_entry)
                    for part in clean.split('\\n'):
                        if part.strip(): lines.append(f'    {{part}}')
            else:
                lines.append(f'    {{ename}}: {{evalue}}')
    return lines

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('notebook')
range_group = parser.add_mutually_exclusive_group()
range_group.add_argument('--cell', type=int, default=None)
range_group.add_argument('--upto', type=int, default=None)
range_group.add_argument('--range', type=str, default=None)
parser.add_argument('--allow-errors', action='store_true')
parser.add_argument('--save', action='store_true')
parser.add_argument('--timeout', type=int, default=600)
parser.add_argument('--kernel', type=str, default=None)
args = parser.parse_args()

path = Path(args.notebook)
nb = nbformat.read(str(path), as_version=4)
cells = nb.cells
total = len(cells)

if total == 0:
    print(f'=== {{path.name}} — No cells ===')
    sys.exit(0)

# Resolve indices
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

kernel_name = args.kernel or nb.metadata.get('kernelspec', {{}}).get('name', 'python3')
print(f'=== {{path.name}} — Executing (kernel: {{kernel_name}}) ===')
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
                    first_line = source.strip().split('\\n')[0][:80] if source.strip() else '(empty)'
                    print(f'[{{idx}}] {{cell.cell_type.upper()}} — {{first_line}}')
                elif not source.strip():
                    print(f'[{{idx}}] CODE{{tag}} — (empty, skipped)')
                else:
                    print(f'[{{idx}}] CODE{{tag}} — (eval: false, skipped)')
                continue

            source_lines = source.strip().split('\\n')
            num_lines = len(source_lines)
            print(f'[{{idx}}] CODE{{tag}} ({{num_lines}} line{{"s" if num_lines != 1 else ""}})')
            for line in source_lines[:5]:
                print(f'    {{line}}')
            if len(source_lines) > 5:
                print(f'    ... ({{len(source_lines) - 5}} more lines)')

            start_time = time.time()
            try:
                client.execute_cell(cell, idx)
                elapsed = time.time() - start_time
                output_lines = format_outputs(cell)
                for line in output_lines: print(line)
                print(f'  -> ok ({{elapsed:.1f}}s)')
                passed += 1
            except CellExecutionError:
                elapsed = time.time() - start_time
                output_lines = format_outputs(cell)
                for line in output_lines: print(line)
                print(f'  -> FAILED ({{elapsed:.1f}}s)')
                failed += 1
                if not args.allow_errors:
                    print(f'\\nStopping at cell {{idx}} (use allow_errors to continue)')
                    break
            print()
except Exception as e:
    print(f'\\nKernel error: {{e}}', file=sys.stderr)
    sys.exit(2)

executed = passed + failed
parts = [f'{{passed}} passed', f'{{failed}} failed'] if failed else [f'{{passed}} passed']
print(f'=== {{executed}} cells executed: {{", ".join(parts)}} ===')

if args.save:
    nbformat.write(nb, str(path))
    print(f'Outputs saved to {{path}}')

if failed > 0: sys.exit(1)
'''
