"""Command-line entry point for the DeepTutor MCP server."""

from __future__ import annotations

import argparse
from typing import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and run the server (stdio transport only)."""
    parser = argparse.ArgumentParser(
        prog="deeptutor-mcp",
        description="Run the DeepTutor MCP server.",
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio"],
        help="Transport to use. Only 'stdio' is supported (default: stdio).",
    )
    args = parser.parse_args(argv)

    if args.transport != "stdio":
        parser.error(f"unsupported transport: {args.transport!r}; only 'stdio' is supported")

    from .server import run_stdio

    run_stdio()
    return 0
