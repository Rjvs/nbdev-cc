"""CLI entry point for nbdev-mcp.

Dispatches between MCP server mode (default) and init command.

Usage:
    nbdev-mcp              # Start MCP server (stdio mode, for .mcp.json)
    nbdev-mcp init /path   # Set up a project with nbdev plugin
    nbdev-mcp init /path --dry-run
    nbdev-mcp init /path --force
"""

import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        from .init import run_init
        run_init(sys.argv[2:])
    else:
        try:
            from .server import mcp
            mcp.run()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f'Error: MCP server failed to start: {e}', file=sys.stderr)
            sys.exit(1)
