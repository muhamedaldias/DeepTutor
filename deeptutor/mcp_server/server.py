"""FastMCP stdio server exposing a safe subset of DeepTutor.

Logging goes to stderr only: stdout is reserved for the JSON-RPC channel.
"""

from __future__ import annotations

import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from .tools import call_tool, list_skills_json, list_tools_json, read_skill_text

SERVER_NAME = "deeptutor"
SERVER_INSTRUCTIONS = (
    "A safe, read-oriented bridge to DeepTutor. Use deeptutor_list_tools to "
    "discover callable tools, deeptutor_call_tool to invoke an allowlisted "
    "tool, and the skill helpers to inspect available skills."
)


def _log(message: str) -> None:
    """Log to stderr so stdout stays a clean JSON-RPC channel."""
    print(f"[deeptutor-mcp] {message}", file=sys.stderr, flush=True)


def build_server() -> FastMCP:
    """Build a FastMCP server registering exactly the four bridge tools."""
    mcp = FastMCP(name=SERVER_NAME, instructions=SERVER_INSTRUCTIONS)

    @mcp.tool()
    async def deeptutor_list_tools() -> str:
        """List the DeepTutor tools available through this MCP bridge."""
        return await list_tools_json()

    @mcp.tool()
    async def deeptutor_call_tool(name: str, arguments: dict[str, Any] | None = None) -> str:
        """Call an allowlisted DeepTutor tool by name with its arguments."""
        return await call_tool(name, arguments)

    @mcp.tool()
    async def deeptutor_list_skills() -> str:
        """List the DeepTutor skills available in this workspace."""
        return await list_skills_json()

    @mcp.tool()
    async def deeptutor_read_skill(name: str, file: str = "SKILL.md") -> str:
        """Read a DeepTutor skill's SKILL.md or a named reference file."""
        return await read_skill_text(name, file)

    return mcp


def run_stdio() -> None:
    """Run the MCP server over the stdio transport."""
    _log("starting DeepTutor MCP server (stdio)")
    server = build_server()
    server.run(transport="stdio")
