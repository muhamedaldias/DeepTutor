"""Safety policy for the MCP bridge.

Only a small allowlist of read-oriented DeepTutor tools may be invoked across
the MCP boundary. The allowlist can be narrowed further with the
``DEEPTUTOR_MCP_ALLOW`` environment variable, but never widened.
"""

from __future__ import annotations

import os
from typing import Any

#: Tools that are safe to expose to an untrusted MCP client.
SAFE_TOOLS: frozenset[str] = frozenset(
    {
        "rag",
        "read_skill",
        "kb_files",
        "read_memory",
        "list_notebook",
        "brainstorm",
        "reason",
        "paper_search",
        "zotero_search",
    }
)

_ALLOW_ENV = "DEEPTUTOR_MCP_ALLOW"
_REDACT_FRAGMENTS = (
    "key",
    "token",
    "secret",
    "password",
    "credential",
    "authorization",
)
_MAX_STRING = 2000
_MAX_KEYS = 20


def allowed_tools() -> frozenset[str]:
    """Return the tool names permitted through MCP.

    Defaults to :data:`SAFE_TOOLS`. ``DEEPTUTOR_MCP_ALLOW`` is a comma
    separated list that may only *narrow* this set: names outside
    ``SAFE_TOOLS`` and unknown names are ignored.
    """
    raw = os.environ.get(_ALLOW_ENV, "")
    if not raw.strip():
        return SAFE_TOOLS
    requested = {part.strip() for part in raw.split(",") if part.strip()}
    if not requested:
        return SAFE_TOOLS
    return frozenset(SAFE_TOOLS & requested)


def is_allowed(name: str) -> bool:
    """Return whether ``name`` may be called through the MCP bridge."""
    return isinstance(name, str) and name in allowed_tools()


def _is_sensitive(key: Any) -> bool:
    lowered = str(key).lower()
    return any(fragment in lowered for fragment in _REDACT_FRAGMENTS)


def _redact(value: Any) -> Any:
    if isinstance(value, str):
        return value[:_MAX_STRING]
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= _MAX_KEYS:
                break
            if _is_sensitive(key):
                continue
            cleaned[key] = _redact(item)
        return cleaned
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


def redact_args(args: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe copy with sensitive keys dropped and values capped.

    Keys whose name contains a credential-like fragment are removed entirely;
    strings are truncated to 2000 characters and dictionaries to 20 keys.
    Used for audit lines and for nested result payloads, never for changing
    the arguments actually passed to a tool.
    """
    if not isinstance(args, dict):
        return {}
    cleaned = _redact(args)
    return cleaned if isinstance(cleaned, dict) else {}


def redact_value(value: Any) -> Any:
    """Return a redacted, JSON-safe copy of any nested payload."""
    return _redact(value)
