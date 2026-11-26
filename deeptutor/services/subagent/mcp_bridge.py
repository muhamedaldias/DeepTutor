"""Opt-in MCP bridge descriptor for ACP subagent sessions.

By default ACP sessions are launched with ``mcpServers: []`` — no tools are
exposed to the agent. Setting :data:`ENV_FLAG` to a truthy spelling offers
DeepTutor's own MCP server over stdio in the ``session/new`` / ``session/load``
request instead. The descriptor is deliberately static: it references the
server by ``python -m`` argv and carries an empty ``env`` array so no ambient
credentials are forwarded to the agent process. The descriptor follows the
authoritative ACP v1 ``McpServerStdio`` schema: exactly ``name``, ``command``,
``args`` and ``env`` (an array of ``{name, value}`` objects), with no ``type``
field. ``command`` is an absolute interpreter path (``sys.executable``).
"""

from __future__ import annotations

import os
import sys
from typing import Any

#: Enable the bridge only when this variable is ``1``, ``true`` or ``yes``.
ENV_FLAG = "DEEPTUTOR_SUBAGENT_MCP_BRIDGE"

_TRUE_VALUES = frozenset({"1", "true", "yes"})


def enabled() -> bool:
    """Return whether the opt-in flag is set to a recognised true spelling."""
    return os.environ.get(ENV_FLAG, "").lower() in _TRUE_VALUES


def build_mcp_servers() -> list[dict[str, Any]]:
    """Return the ACP ``mcpServers`` value: empty unless the bridge is enabled."""
    if not enabled():
        return []
    return [
        {
            "name": "deeptutor",
            "command": sys.executable,
            "args": ["-m", "deeptutor.mcp_server", "--transport", "stdio"],
            "env": [],
        }
    ]
