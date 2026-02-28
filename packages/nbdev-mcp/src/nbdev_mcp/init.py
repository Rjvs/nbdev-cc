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
import configparser
import json
import os
import re
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

GITIGNORE_ENTRIES = ['jupyter.log', '.claude/.last-nb-read', '.claude/.session-setup-done']

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

# Files that need template variable substitution
TEMPLATE_FILES = {
    os.path.join('.claude', 'CLAUDE.md'),
}

EXECUTABLE_FILES = [
    os.path.join('.claude', 'hooks', 'session-start.sh'),
    os.path.join('.claude', 'hooks', 'auto-read-notebooks.sh'),
]

# Regex matching a TOML section header (e.g. [project]) but NOT an
# inline array literal (e.g. dependencies = ["foo"]).  A section header
# starts at column 0 with `[` followed by a bare key, not `"` or `'`.
_TOML_SECTION_RE = re.compile(r'^\[([A-Za-z0-9._-]+)\]\s*$')


def _log(msg, dry_run=False):
    prefix = '[dry-run] ' if dry_run else ''
    print(f'  {prefix}{msg}', file=sys.stderr)


def _assets_path():
    """Get the path to bundled assets."""
    return resources.files('nbdev_mcp') / 'assets'


def _detect_project_settings(project_dir):
    """Read settings.ini to detect lib_name and nbs_path.

    Returns a dict with keys 'lib_name' and 'nbs_path', using
    defaults when settings.ini is absent or incomplete.
    """
    defaults = {'lib_name': 'my_lib', 'nbs_path': 'nbs'}
    ini_path = os.path.join(project_dir, 'settings.ini')
    if not os.path.exists(ini_path):
        return defaults

    config = configparser.ConfigParser()
    config.read(ini_path)
    section = 'DEFAULT'
    return {
        'lib_name': config.get(section, 'lib_name', fallback=defaults['lib_name']),
        'nbs_path': config.get(section, 'nbs_path', fallback=defaults['nbs_path']),
    }


def _render_template(content, settings):
    """Replace {{NBS_PATH}} and {{LIB_NAME}} placeholders in template content."""
    content = content.replace('{{NBS_PATH}}', settings['nbs_path'])
    content = content.replace('{{LIB_NAME}}', settings['lib_name'])
    return content


def _copy_asset_tree(src_traversable, dst, force=False, dry_run=False, settings=None):
    """Copy a directory tree from package resources to filesystem."""
    if src_traversable.is_file():
        _copy_asset_file(src_traversable, dst, force=force, dry_run=dry_run, settings=settings)
        return

    for item in src_traversable.iterdir():
        item_dst = os.path.join(dst, item.name)
        if item.is_dir():
            _copy_asset_tree(item, item_dst, force=force, dry_run=dry_run, settings=settings)
        else:
            _copy_asset_file(item, item_dst, force=force, dry_run=dry_run, settings=settings)


def _copy_asset_file(src_traversable, dst, force=False, dry_run=False, settings=None):
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

        # Apply template substitution for CLAUDE.md and similar files
        if settings and any(dst.endswith(t.replace(os.sep, '/')) or dst.endswith(t) for t in TEMPLATE_FILES):
            content = _render_template(content.decode('utf-8'), settings).encode('utf-8')

        with open(dst, 'wb') as f:
            f.write(content)


def _write_mcp_json(project_dir, force=False, dry_run=False):
    """Create or merge .mcp.json in the project root."""
    path = os.path.join(project_dir, '.mcp.json')
    if os.path.exists(path):
        with open(path) as f:
            existing = json.load(f)
        servers = existing.get('mcpServers', {})
        needs_update = False
        for name in MCP_CONFIG['mcpServers']:
            if name not in servers or force:
                needs_update = True
                break
        if not needs_update:
            _log(f'skip (exists): {path} already has nbdev and jupyter-mcp', dry_run)
            return
        servers.update(MCP_CONFIG['mcpServers'])
        existing['mcpServers'] = servers
        config = existing
        _log(f'merge MCP servers into: {path}', dry_run)
    else:
        config = MCP_CONFIG
        _log(f'create: {path}', dry_run)

    if not dry_run:
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
            f.write('\n')


def _is_toml_section_header(line):
    """Return True if the line is a TOML section header like [project].

    Returns False for inline array literals like ``deps = ["foo"]``.
    """
    return bool(_TOML_SECTION_RE.match(line.strip()))


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
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == '[dependency-groups]':
                    j = i + 1
                    # Find the next section header (skip array literals)
                    while j < len(lines) and not _is_toml_section_header(lines[j]):
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
    args = parser.parse_args(argv)

    project = os.path.abspath(args.project)
    if not os.path.isdir(project):
        print(f'Error: {project} is not a directory', file=sys.stderr)
        sys.exit(1)

    # Warn if this doesn't look like an nbdev project
    has_settings_ini = os.path.exists(os.path.join(project, 'settings.ini'))
    has_nbs = os.path.isdir(os.path.join(project, 'nbs'))
    if not has_settings_ini and not has_nbs:
        print('Warning: no settings.ini or nbs/ directory found.', file=sys.stderr)
        print('         This may not be an nbdev project. Continuing anyway.\n', file=sys.stderr)

    # Detect project settings for template rendering
    settings = _detect_project_settings(project)

    print(f'Installing nbdev plugin into {project}', file=sys.stderr)
    if args.dry_run:
        print('(dry run — no changes will be made)\n', file=sys.stderr)

    # Copy assets from package
    assets = _assets_path()
    for src_rel, dst_rel in ASSET_COPIES:
        src = assets / src_rel.replace(os.sep, '/')
        dst = os.path.join(project, dst_rel)
        _copy_asset_tree(src, dst, force=args.force, dry_run=args.dry_run, settings=settings)

    # Set executable permissions
    for rel_path in EXECUTABLE_FILES:
        path = os.path.join(project, rel_path)
        if os.path.exists(path) and not args.dry_run:
            os.chmod(path, 0o755)

    # Create/merge .mcp.json
    _write_mcp_json(project, force=args.force, dry_run=args.dry_run)

    # Patch pyproject.toml
    _patch_pyproject(project, dry_run=args.dry_run)

    # Patch .gitignore
    _patch_gitignore(project, dry_run=args.dry_run)

    if not args.dry_run:
        print(f'\nDone. Next steps:', file=sys.stderr)
        print(f'  1. Review .claude/CLAUDE.md (paths auto-detected from settings.ini)', file=sys.stderr)
        print(f'  2. uv sync --group jupyter', file=sys.stderr)
        print(f'  3. Start JupyterLab and set JUPYTER_TOKEN', file=sys.stderr)
        print(f'  4. Run: claude  (with JUPYTER_TOKEN in env)', file=sys.stderr)
