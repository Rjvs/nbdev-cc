"""Execute notebook cells in batch.

Starts a fresh kernel, executes cells sequentially, and reports outputs.
Uses subprocess to run in the project's Python environment (since the
MCP server runs in its own isolated env via uvx).

The execution logic lives in _runner.py — a standalone script that is
passed to the project's Python interpreter via subprocess. This avoids
the previous approach of generating a Python script as an f-string.

Security note: This tool executes arbitrary code from notebook cells with
the full permissions of the user's Python environment. There is no
sandboxing — cell code can read/write files, make network requests, and
run shell commands. Only run notebooks you trust. The MCP client (Claude
Code) is expected to confirm execution with the user before calling this
tool.
"""

import os
import subprocess
from pathlib import Path

from ._common import validate_notebook_path

# Path to the standalone runner script (same directory as this file)
_RUNNER_SCRIPT = str(Path(__file__).parent / '_runner.py')


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

    SECURITY: This executes arbitrary code with user-level permissions.
    No sandboxing is applied. Only run trusted notebooks.

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
    p, err = validate_notebook_path(path)
    if err:
        return err

    # Build command-line arguments for the runner script
    args = [str(p.resolve())]
    if cell is not None:
        args.extend(['--cell', str(cell)])
    elif upto is not None:
        args.extend(['--upto', str(upto)])
    elif range is not None:
        args.extend(['--range', range])
    if save:
        args.append('--save')
    if allow_errors:
        args.append('--allow-errors')
    if timeout != 600:
        args.extend(['--timeout', str(timeout)])
    if kernel:
        args.extend(['--kernel', kernel])

    # Run in the notebook's directory (or cwd if notebook is in current dir)
    cwd = str(p.parent.resolve()) if p.parent != Path('.') else os.getcwd()

    # Try uv run first (project env), fall back to plain python
    for cmd_prefix in [
        ['uv', 'run', 'python'],
        ['python3'],
        ['python'],
    ]:
        try:
            result = subprocess.run(
                cmd_prefix + [_RUNNER_SCRIPT] + args,
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
