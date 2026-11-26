"""JSON-safe wrappers around DeepTutor tools and skills.

Every public function returns a JSON-encoded ``str`` and never raises across
the MCP boundary: failures are reported as ``{"ok": false, "error": ...}``.
The allowlist is enforced on every path, including the native skill helpers.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from deeptutor.core.tool_protocol import ToolResult
from deeptutor.runtime.registry.tool_registry import get_tool_registry
from deeptutor.services.skill.service import get_skill_service

from .context import deep_context
from .policy import allowed_tools, is_allowed, redact_args, redact_value

_SKILL_TOOL = "read_skill"


def _json(value: Any) -> str:
    """Serialize ``value`` to a JSON string that is safe to cross MCP."""
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:  # pragma: no cover - defensive last resort
        return '{"ok": false, "error": "result was not JSON serializable"}'


def _error(message: str) -> str:
    return _json({"ok": False, "error": message})


def _exception_error(exc: BaseException) -> str:
    """Report the exception *type* only, never its message (may hold paths/config)."""
    return _error(f"{type(exc).__name__} while processing MCP request")


def _serialize_result(result: ToolResult) -> dict[str, Any]:
    """Serialize only the public projection of a ToolResult.

    ``metadata``, ``model_message``, ``pause_for_user`` and ``terminate_turn``
    are loop-internal and are deliberately not exported to an external agent.
    """
    payload: dict[str, Any] = {
        "content": result.content,
        "sources": redact_value(result.sources),
        "success": result.success,
    }
    if result.public_result is not None:
        payload["public_result"] = redact_value(result.public_result)
    return payload


def _audit(name: str, arguments: dict[str, Any]) -> None:
    """Emit a redacted audit line to stderr (never stdout)."""
    keys = sorted(redact_args(arguments).keys())
    print(f"[deeptutor-mcp] audit tool={name} arg_keys={keys}", file=sys.stderr, flush=True)


def _denied(name: str) -> str:
    return _error(f"tool not allowed: {name}")


async def list_tools_json() -> str:
    """List the MCP-exposed tools as a JSON string (default-deny)."""
    try:
        async with deep_context():
            allowed = allowed_tools()
            definitions = get_tool_registry().get_definitions(list(allowed))
        tools = [
            definition.to_openai_schema()
            for definition in definitions
            if definition.name in allowed
        ]
        return _json({"ok": True, "tools": tools})
    except Exception as exc:
        return _exception_error(exc)


async def call_tool(name: str, arguments: dict[str, Any] | None = None) -> str:
    """Call an allowlisted DeepTutor tool and return a JSON string."""
    if not is_allowed(name):
        return _denied(name)
    try:
        arguments = arguments or {}
        if not isinstance(arguments, dict):
            return _error("arguments must be an object")

        registry = get_tool_registry()
        # Check the resolved name too: an alias must not widen the allowlist.
        resolver = getattr(registry, "_resolve_request", None)
        if resolver is not None:
            resolved = resolver(name, {})[0]
            if not is_allowed(resolved):
                return _denied(resolved)

        async with deep_context():
            result = await registry.execute(name, **arguments)
        _audit(name, arguments)
        return _json({"ok": True, "result": _serialize_result(result)})
    except Exception as exc:
        return _exception_error(exc)


async def list_skills_json() -> str:
    """List available DeepTutor skills as a JSON string (allowlist-gated)."""
    if not is_allowed(_SKILL_TOOL):
        return _denied(_SKILL_TOOL)
    try:
        async with deep_context():
            skills = get_skill_service().list_skills()
        payload = [
            {
                "name": skill.name,
                "description": skill.description,
                "tags": skill.tags,
                "source": skill.source,
            }
            for skill in skills
        ]
        return _json({"ok": True, "skills": payload})
    except Exception as exc:
        return _exception_error(exc)


async def read_skill_text(name: str, file: str = "SKILL.md") -> str:
    """Read a skill's SKILL.md (or a reference file) as a JSON string."""
    if not is_allowed(_SKILL_TOOL):
        return _denied(_SKILL_TOOL)
    if not isinstance(name, str) or not name:
        return _error("skill name must be a non-empty string")
    try:
        async with deep_context():
            text = get_skill_service().read_skill_file(name, file)
        return _json({"ok": True, "name": name, "file": file, "text": text})
    except Exception as exc:
        return _exception_error(exc)
