"""Configure a project for use with the nbdev Claude Code plugin.

Writes project-specific config that cannot come from the plugin itself:
  - .claude/CLAUDE.md  — parameterized with lib name and nbs path
  - .mcp.json          — MCP server config (nbdev + optionally jupyter-mcp)
  - pyproject.toml     — jupyter dependency group (unless --no-jupyter)
  - .gitignore         — jupyter.log, .claude/.last-nb-read

Skills and hooks are provided by the plugin at load time via
`claude --plugin-dir path/to/nbdev-cc` and are NOT copied into the project.

Usage:
    nbdev-mcp init /path/to/project
    nbdev-mcp init /path/to/project --dry-run
    nbdev-mcp init /path/to/project --force
    nbdev-mcp init /path/to/project --no-jupyter
"""

import argparse
import json
import os
import sys
import textwrap
from importlib import resources


MCP_CONFIG = {
    'mcpServers': {
        'nbdev': {
            'command': 'uvx',
            'args': ['nbdev-mcp'],
        },
        'jupyter-mcp': {
            'command': 'uvx',
            'args': ['jupyter-mcp-server@latest'],
            'env': {
                'JUPYTER_URL': '${JUPYTER_URL:-http://localhost:8888}',
                'JUPYTER_TOKEN': '${JUPYTER_TOKEN}',
                'ALLOW_IMG_OUTPUT': 'true',
            },
        },
    }
}

JUPYTER_DEPS = textwrap.dedent("""\
    [dependency-groups]
    jupyter = [
        "jupyterlab==4.4.1",
        "jupyter-collaboration>=4.0.2",
        "jupyter-mcp-tools>=0.1.4",
        "ipykernel",
    ]
""")

GITIGNORE_ENTRIES = ['jupyter.log', '.claude/.last-nb-read']


def _log(msg, dry_run=False):
    prefix = '[dry-run] ' if dry_run else ''
    print(f'  {prefix}{msg}', file=sys.stderr)


def _assets_path():
    """Get the path to bundled assets."""
    return resources.files('nbdev_mcp') / 'assets'


def _read_settings(project_dir):
    """Read lib_name and nbs_path from settings.ini; return defaults if absent."""
    lib_name = 'mylib'
    nbs_path = 'nbs'
    settings_path = os.path.join(project_dir, 'settings.ini')
    if not os.path.exists(settings_path):
        return lib_name, nbs_path
    with open(settings_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, val = line.partition('=')
            key, val = key.strip(), val.strip()
            if key == 'lib_name':
                lib_name = val
            elif key == 'nbs_path':
                nbs_path = val
    return lib_name, nbs_path


def _patch_claude_md(project_dir, force=False, dry_run=False):
    """Write .claude/CLAUDE.md with lib_name and nbs_path substituted."""
    dst = os.path.join(project_dir, '.claude', 'CLAUDE.md')
    if os.path.exists(dst) and not force:
        _log(f'skip (exists): {dst}', dry_run)
        return

    lib_name, nbs_path = _read_settings(project_dir)
    verb = 'overwrite' if os.path.exists(dst) else 'create'
    _log(f'{verb}: {dst}  (lib={lib_name}, nbs={nbs_path})', dry_run)

    if not dry_run:
        template = (_assets_path() / 'CLAUDE.md').read_text()
        content = template.replace('{{LIB_NAME}}', lib_name).replace('{{NBS_PATH}}', nbs_path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'w') as f:
            f.write(content)


def _write_mcp_json(project_dir, force=False, dry_run=False, no_jupyter=False):
    """Create or merge .mcp.json in the project root."""
    servers_to_add = dict(MCP_CONFIG['mcpServers'])
    if no_jupyter:
        servers_to_add.pop('jupyter-mcp', None)

    path = os.path.join(project_dir, '.mcp.json')
    if os.path.exists(path):
        with open(path) as f:
            existing = json.load(f)
        servers = existing.get('mcpServers', {})
        needs_update = any(name not in servers or force for name in servers_to_add)
        if not needs_update:
            _log(f'skip (exists): {path} already has required MCP servers', dry_run)
            return
        servers.update(servers_to_add)
        existing['mcpServers'] = servers
        config = existing
        _log(f'merge MCP servers into: {path}', dry_run)
    else:
        config = {'mcpServers': servers_to_add}
        _log(f'create: {path}', dry_run)

    if not dry_run:
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
            f.write('\n')


def _patch_pyproject(project_dir, dry_run=False):
    """Add jupyter dependency group to pyproject.toml if not present."""
    import re as _re

    path = os.path.join(project_dir, 'pyproject.toml')
    if not os.path.exists(path):
        _log(f'skip: {path} not found (create it first)', dry_run)
        return

    with open(path) as f:
        content = f.read()

    if '[dependency-groups]' in content and 'jupyter' in content:
        _log(f'skip: {path} already has jupyter dependency group', dry_run)
        return

    if '[dependency-groups]' in content:
        _log(f'patch: add jupyter group to {path}', dry_run)
        if not dry_run:
            # A TOML section header is [name] or [[name]] on its own line —
            # not an array literal inside a value. Match only section lines.
            _section_re = _re.compile(r'^\s*\[\[?[A-Za-z0-9_\-.]+\]?\]\s*$')
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == '[dependency-groups]':
                    j = i + 1
                    while j < len(lines) and not (
                        _section_re.match(lines[j]) and lines[j].strip() != '[dependency-groups]'
                    ):
                        j += 1
                    jupyter_lines = [
                        'jupyter = [',
                        '    "jupyterlab==4.4.1",',
                        '    "jupyter-collaboration>=4.0.2",',
                        '    "jupyter-mcp-tools>=0.1.4",',
                        '    "ipykernel",',
                        ']',
                        '',
                    ]
                    for k, jl in enumerate(jupyter_lines):
                        lines.insert(j + k, jl)
                    break
            with open(path, 'w') as f:
                f.write('\n'.join(lines))
    else:
        _log(f'patch: add [dependency-groups] to {path}', dry_run)
        if not dry_run:
            with open(path, 'a') as f:
                f.write('\n' + JUPYTER_DEPS)


def _patch_gitignore(project_dir, dry_run=False):
    """Add jupyter.log and .claude/.last-nb-read to .gitignore if not present."""
    path = os.path.join(project_dir, '.gitignore')
    if not os.path.exists(path):
        _log(f'create: {path}', dry_run)
        if not dry_run:
            with open(path, 'w') as f:
                f.write('\n'.join(GITIGNORE_ENTRIES) + '\n')
        return

    with open(path) as f:
        content = f.read()

    to_add = [e for e in GITIGNORE_ENTRIES if e not in content]
    if not to_add:
        _log(f'skip: {path} already has entries', dry_run)
        return

    _log(f'patch: add {", ".join(to_add)} to {path}', dry_run)
    if not dry_run:
        with open(path, 'a') as f:
            f.write('\n# nbdev-mcp\n')
            for entry in to_add:
                f.write(entry + '\n')


def _is_nbdev_project(project_dir):
    """Return True if the directory looks like an nbdev project."""
    has_settings = os.path.exists(os.path.join(project_dir, 'settings.ini'))
    has_nbs = os.path.isdir(os.path.join(project_dir, 'nbs'))
    has_pyproject = os.path.exists(os.path.join(project_dir, 'pyproject.toml'))
    return has_settings or (has_nbs and has_pyproject)


def run_init(argv):
    """Run the init command."""
    parser = argparse.ArgumentParser(
        prog='nbdev-mcp init',
        description='Configure a project for use with the nbdev Claude Code plugin.',
    )
    parser.add_argument('project', help='Path to the target project root')
    parser.add_argument('--force', action='store_true',
                        help='Overwrite existing files (default: skip)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--no-jupyter', action='store_true',
                        help='Skip jupyter-mcp config and dependency group')
    args = parser.parse_args(argv)

    project = os.path.abspath(args.project)
    if not os.path.isdir(project):
        print(f'Error: {project} is not a directory', file=sys.stderr)
        sys.exit(1)

    if not _is_nbdev_project(project):
        print(
            f'Warning: {project} does not look like an nbdev project '
            f'(no settings.ini or nbs/ directory found).',
            file=sys.stderr,
        )

    print(f'Configuring nbdev plugin for {project}', file=sys.stderr)
    if args.dry_run:
        print('(dry run — no changes will be made)\n', file=sys.stderr)

    _patch_claude_md(project, force=args.force, dry_run=args.dry_run)
    _write_mcp_json(project, force=args.force, dry_run=args.dry_run,
                    no_jupyter=args.no_jupyter)

    if not args.no_jupyter:
        _patch_pyproject(project, dry_run=args.dry_run)
    else:
        _log('skip: jupyter dependency group (--no-jupyter)', args.dry_run)

    _patch_gitignore(project, dry_run=args.dry_run)

    if not args.dry_run:
        print(f'\nDone. Next steps:', file=sys.stderr)
        print(f'  1. Review .claude/CLAUDE.md and adjust for your project', file=sys.stderr)
        print(f'  2. Load the plugin: claude --plugin-dir path/to/nbdev-cc', file=sys.stderr)
        if not args.no_jupyter:
            print(f'  3. uv sync --group jupyter', file=sys.stderr)
            print(f'  4. Start JupyterLab and set JUPYTER_TOKEN', file=sys.stderr)
            print(f'  5. Run: JUPYTER_TOKEN=... claude --plugin-dir path/to/nbdev-cc', file=sys.stderr)
