"""MCP server exposing nbdev notebook tools.

Registers all nb_* tools as MCP tools using FastMCP. Run via:
    uvx nbdev-mcp         (in .mcp.json)
    nbdev-mcp             (if installed)
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nbdev")


@mcp.tool()
def nb_read(
    path: str,
    outline: bool = False,
    cell: int | None = None,
    exports: bool = False,
    tests: bool = False,
    markdown: bool = False,
    range: str | None = None,
    flag: str | None = None,
) -> str:
    """Human-readable notebook viewer. Use instead of Read/cat on .ipynb files.

    Shows cell content with cell numbers, types, directives, and structure.
    Use --outline for a quick structural overview, or filter to specific
    cell types (exports, tests, markdown) or flagged cells.
    """
    from .tools.read import nb_read as _nb_read
    return _nb_read(path, outline=outline, cell=cell, exports=exports,
                    tests=tests, markdown=markdown, range=range, flag=flag)


@mcp.tool()
def nb_edit(
    path: str,
    old: str,
    new: str,
    cell: int | None = None,
    match: str | None = None,
    replace_all: bool = False,
    dry_run: bool = False,
    diff: bool = False,
) -> str:
    """Edit cell content within a notebook (find-and-replace).

    Provide either cell (index) or match (content pattern) to select
    the target cell. The old string must be unique within the cell
    unless replace_all is True.
    """
    from .tools.edit import nb_edit as _nb_edit
    return _nb_edit(path, old=old, new=new, cell=cell, match=match,
                    replace_all=replace_all, dry_run=dry_run, diff=diff)


@mcp.tool()
def nb_create(
    out: str,
    module: str | None = None,
    title: str | None = None,
    from_spec: str | None = None,
    force: bool = False,
) -> str:
    """Create a notebook from a spec file or minimal module template.

    Generates valid .ipynb with proper metadata, unique cell IDs, and
    correct structure. Provide either module (for minimal notebook) or
    from_spec (for spec file).
    """
    from .tools.create import nb_create as _nb_create
    return _nb_create(out=out, module=module, title=title,
                      from_spec=from_spec, force=force)


@mcp.tool()
def nb_validate(
    paths: str | list[str],
    strict: bool = False,
) -> str:
    """Validate notebook structure and nbdev conventions.

    Catches structural problems (missing fields, duplicate IDs, invalid
    types) before they reach nbdev commands. Use strict mode to treat
    warnings as errors.
    """
    from .tools.validate import nb_validate as _nb_validate
    return _nb_validate(paths=paths, strict=strict)


@mcp.tool()
def nb_cells(
    path: str,
    action: str,
    at: int | None = None,
    from_spec: str | None = None,
    from_pos: int | None = None,
    to_pos: int | None = None,
    cells: str | None = None,
    pattern: str | None = None,
    directive: str | None = None,
    dry_run: bool = False,
) -> str:
    """Bulk cell operations: insert, append, move, find, remove.

    Actions:
    - insert: Insert cells from spec file at position (requires from_spec, optional at)
    - append: Append cells from spec file to end (requires from_spec)
    - move: Move cell between positions (requires from_pos and to_pos)
    - find: Find cells by pattern or directive
    - remove: Remove cells by index (requires cells as comma-separated indices)
    """
    if action == 'insert':
        if not from_spec:
            return 'Error: from_spec is required for insert'
        from .tools.cells import nb_cells_insert
        return nb_cells_insert(path, from_spec=from_spec, at=at, dry_run=dry_run)
    elif action == 'append':
        if not from_spec:
            return 'Error: from_spec is required for append'
        from .tools.cells import nb_cells_append
        return nb_cells_append(path, from_spec=from_spec, dry_run=dry_run)
    elif action == 'move':
        if from_pos is None or to_pos is None:
            return 'Error: from_pos and to_pos are required for move'
        from .tools.cells import nb_cells_move
        return nb_cells_move(path, from_pos=from_pos, to_pos=to_pos, dry_run=dry_run)
    elif action == 'find':
        from .tools.cells import nb_cells_find
        return nb_cells_find(path, pattern=pattern, directive=directive)
    elif action == 'remove':
        if not cells:
            return 'Error: cells (comma-separated indices) is required for remove'
        from .tools.cells import nb_cells_remove
        return nb_cells_remove(path, cells=cells, dry_run=dry_run)
    else:
        return f'Error: unknown action "{action}". Use: insert, append, move, find, remove'


@mcp.tool()
def nb_search(
    path: str,
    pattern: str | None = None,
    directive: str | None = None,
    cell_type: str | None = None,
    ignore_case: bool = False,
    files_only: bool = False,
    context: int = 0,
) -> str:
    """Search across notebooks for content, directives, or cell types.

    Use instead of grep/Grep on .ipynb files. Searches actual cell content
    and shows results with notebook path, cell index, type, and classification.
    """
    from .tools.search import nb_search as _nb_search
    return _nb_search(path, pattern=pattern, directive=directive,
                      cell_type=cell_type, ignore_case=ignore_case,
                      files_only=files_only, context=context)


@mcp.tool()
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

    Starts a fresh kernel and executes cells sequentially. Prefer --upto
    or --range over calling --cell in a loop — one call does the job.
    Runs in the project's Python environment.
    """
    from .tools.run import nb_run as _nb_run
    return _nb_run(path, cell=cell, upto=upto, range=range,
                   save=save, allow_errors=allow_errors,
                   timeout=timeout, kernel=kernel)


@mcp.tool()
def nb_mcp_url(
    path: str | None = None,
    hierarchical: bool = False,
    all: bool = False,
) -> str:
    """Get the Jupyter server URL for the current project.

    Finds a running Jupyter server whose root directory matches the
    project path. Returns the URL, token, and root directory.
    """
    from .tools.mcp_url import nb_mcp_url as _nb_mcp_url
    return _nb_mcp_url(path=path, hierarchical=hierarchical, all=all)
