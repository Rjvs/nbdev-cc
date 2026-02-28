"""Project setup — install nbdev plugin into a target project.

Copies skill, CLAUDE.md, hooks from bundled package assets. Patches
.mcp.json, pyproject.toml, and .gitignore. Replaces the old
setup_jupyter_agent.py template system.

Usage:
    nbdev-mcp init /path/to/project
    nbdev-mcp init /path/to/project --dry-run
    nbdev-mcp init /path/to/project --force
"""

import argparse
import json
import os
import shutil
import sys
import textwrap
from importlib import resources
from pathlib import Path


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

# What to copy from package assets to target project
ASSET_COPIES = [
    # (source path relative to assets/, dest path relative to project root)
    ('skill', os.path.join('.claude', 'skills', 'nbdev')),
    ('fastcore-skill', os.path.join('.claude', 'skills', 'fastcore')),
    ('CLAUDE.md', os.path.join('.claude', 'CLAUDE.md')),
    ('settings.json', os.path.join('.claude', 'settings.json')),
    (os.path.join('hooks', 'session-start.sh'), os.path.join('.claude', 'hooks', 'session-start.sh')),
    (os.path.join('hooks', 'auto-read-notebooks.sh'), os.path.join('.claude', 'hooks', 'auto-read-notebooks.sh')),
]

EXECUTABLE_FILES = [
    os.path.join('.claude', 'hooks', 'session-start.sh'),
    os.path.join('.claude', 'hooks', 'auto-read-notebooks.sh'),
]


def _log(msg, dry_run=False):
    prefix = '[dry-run] ' if dry_run else ''
    print(f'  {prefix}{msg}', file=sys.stderr)


def _assets_path():
    """Get the path to bundled assets."""
    return resources.files('nbdev_mcp') / 'assets'


def _copy_asset_tree(src_traversable, dst, force=False, dry_run=False):
    """Copy a directory tree from package resources to filesystem."""
    if src_traversable.is_file():
        _copy_asset_file(src_traversable, dst, force=force, dry_run=dry_run)
        return

    for item in src_traversable.iterdir():
        item_dst = os.path.join(dst, item.name)
        if item.is_dir():
            _copy_asset_tree(item, item_dst, force=force, dry_run=dry_run)
        else:
            _copy_asset_file(item, item_dst, force=force, dry_run=dry_run)


def _copy_asset_file(src_traversable, dst, force=False, dry_run=False):
    """Copy a single file from package resources to filesystem."""
    exists = os.path.exists(dst)
    if exists and not force:
        _log(f'skip (exists): {dst}', dry_run)
        return

    verb = 'overwrite' if exists else 'copy'
    _log(f'{verb}: {dst}', dry_run)

    if not dry_run:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        content = src_traversable.read_bytes()
        with open(dst, 'wb') as f:
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
            import re as _re
            # A TOML section header is a line whose non-whitespace content is
            # [name] or [[name]] — not an array literal which starts inside
            # a value position. We match only top-level section lines.
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
    """Add jupyter.log to .gitignore if not present."""
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
            f.write('\n# Jupyter MCP collaboration\n')
            for entry in to_add:
                f.write(entry + '\n')


def _is_nbdev_project(project_dir):
    """Return True if the directory looks like an nbdev project."""
    has_settings = os.path.exists(os.path.join(project_dir, 'settings.ini'))
    has_nbs = os.path.isdir(os.path.join(project_dir, 'nbs'))
    has_pyproject = os.path.exists(os.path.join(project_dir, 'pyproject.toml'))
    # Accept if settings.ini exists OR if both nbs/ and pyproject.toml exist
    return has_settings or (has_nbs and has_pyproject)


def run_init(argv):
    """Run the init command."""
    parser = argparse.ArgumentParser(
        prog='nbdev-mcp init',
        description='Install nbdev plugin into a project.',
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
        print('Continuing anyway — pass --force to suppress this warning next time.', file=sys.stderr)

    print(f'Installing nbdev plugin into {project}', file=sys.stderr)
    if args.dry_run:
        print('(dry run — no changes will be made)\n', file=sys.stderr)

    # Copy assets from package
    assets = _assets_path()
    for src_rel, dst_rel in ASSET_COPIES:
        src = assets / src_rel.replace(os.sep, '/')
        dst = os.path.join(project, dst_rel)
        _copy_asset_tree(src, dst, force=args.force, dry_run=args.dry_run)

    # Set executable permissions
    for rel_path in EXECUTABLE_FILES:
        path = os.path.join(project, rel_path)
        if os.path.exists(path) and not args.dry_run:
            os.chmod(path, 0o755)

    # Create/merge .mcp.json (optionally skip jupyter-mcp server)
    _write_mcp_json(project, force=args.force, dry_run=args.dry_run,
                    no_jupyter=args.no_jupyter)

    # Patch pyproject.toml (optionally skip jupyter dependency group)
    if not args.no_jupyter:
        _patch_pyproject(project, dry_run=args.dry_run)
    else:
        _log('skip: jupyter dependency group (--no-jupyter)', args.dry_run)

    # Patch .gitignore
    _patch_gitignore(project, dry_run=args.dry_run)

    if not args.dry_run:
        print(f'\nDone. Next steps:', file=sys.stderr)
        print(f'  1. Edit .claude/CLAUDE.md to match your project', file=sys.stderr)
        if not args.no_jupyter:
            print(f'  2. uv sync --group jupyter', file=sys.stderr)
            print(f'  3. Start JupyterLab and set JUPYTER_TOKEN', file=sys.stderr)
            print(f'  4. Run: claude  (with JUPYTER_TOKEN in env)', file=sys.stderr)
        else:
            print(f'  2. Run: claude', file=sys.stderr)
