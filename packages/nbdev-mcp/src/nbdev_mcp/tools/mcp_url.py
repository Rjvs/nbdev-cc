"""Get the Jupyter MCP server URL for the current project.

Parses `uv run jupyter server list` to find a running Jupyter server
whose root directory is inside the current working directory.
"""

import os
import subprocess


def _get_running_servers():
    """Run `uv run jupyter server list` and parse the output."""
    try:
        result = subprocess.run(
            ['uv', 'run', 'jupyter', 'server', 'list'],
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError:
        return None  # uv not found
    except subprocess.TimeoutExpired:
        return None

    servers = []
    for line in result.stdout.splitlines() + result.stderr.splitlines():
        line = line.strip()
        if not line or line.startswith('Currently running'):
            continue
        if ' :: ' in line:
            url, root_dir = line.split(' :: ', 1)
            servers.append((url.strip(), root_dir.strip()))
    return servers


def _resolve_path(path):
    """Resolve a path to its real absolute form."""
    return os.path.realpath(os.path.abspath(path))


def _is_subpath(child, parent):
    """Check if child is inside parent (or equal to parent)."""
    child = _resolve_path(child)
    parent = _resolve_path(parent)
    if child == parent:
        return True
    return child.startswith(parent + os.sep)


def _find_server(servers, project_path, hierarchical=False):
    """Find the best matching server for a project path."""
    project_path = _resolve_path(project_path)
    matches = []

    for url, root_dir in servers:
        root_dir_resolved = _resolve_path(root_dir)

        if _is_subpath(root_dir_resolved, project_path):
            depth = root_dir_resolved.count(os.sep)
            matches.append((url, root_dir, depth, 'inside'))
        elif hierarchical and _is_subpath(project_path, root_dir_resolved):
            depth = root_dir_resolved.count(os.sep)
            matches.append((url, root_dir, depth, 'contains'))

    if not matches:
        return None, None

    matches.sort(key=lambda m: (0 if m[3] == 'inside' else 1, -m[2]))
    return matches[0][0], matches[0][1]


def nb_mcp_url(
    path: str | None = None,
    hierarchical: bool = False,
    all: bool = False,
) -> str:
    """Get the Jupyter server URL for the current project.

    Args:
        path: Project path to match against (default: current directory).
        hierarchical: Also match servers whose root contains the project path.
        all: List all running Jupyter servers.

    Returns:
        Server URL, token, and root directory, or an error message.
    """
    servers = _get_running_servers()
    if servers is None:
        return "Error: 'uv' not found or `uv run jupyter server list` timed out."

    if all:
        if not servers:
            return 'No running Jupyter servers found.\nStart one with: uv run jupyter lab --notebook-dir=nbs'
        return '\n'.join(f'{url} :: {root}' for url, root in servers)

    if not servers:
        return (
            'No running Jupyter servers found.\n\n'
            'To start a Jupyter server for this project:\n'
            '  export JUPYTER_TOKEN=$(uv run python -c "import secrets; print(secrets.token_urlsafe(32))")\n'
            '  uv run jupyter lab --notebook-dir=nbs --port 8888 \\\n'
            '    --IdentityProvider.token "$JUPYTER_TOKEN" > jupyter.log 2>&1 &'
        )

    project_path = path or os.getcwd()
    url, root_dir = _find_server(servers, project_path, hierarchical=hierarchical)

    if url is None:
        lines = [f'No Jupyter server found for: {_resolve_path(project_path)}']
        lines.append('\nRunning servers:')
        for s_url, s_root in servers:
            lines.append(f'  {s_root}')
        return '\n'.join(lines)

    base_url = url.split('?')[0].rstrip('/')
    token = ''
    if 'token=' in url:
        token = url.split('token=', 1)[1].split('&')[0]

    return f'url: {base_url}\ntoken: {token}\nroot: {root_dir}'
