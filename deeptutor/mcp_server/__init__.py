"""Safe MCP stdio bridge for DeepTutor.

Exposes a small, allowlisted subset of DeepTutor's tools and skills to MCP
clients over a JSON-RPC stdio channel.
"""

from .server import build_server, run_stdio

__all__ = ["build_server", "run_stdio"]
