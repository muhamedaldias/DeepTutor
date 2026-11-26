"""Opt-in MCP bridge descriptor: flag semantics, shape, and ACP wire usage."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from types import SimpleNamespace

import pytest

from deeptutor.services.subagent import mcp_bridge
from deeptutor.services.subagent.acp import _establish_session
from deeptutor.services.subagent.mcp_bridge import ENV_FLAG

# The exact descriptor promised to ACP agents when the bridge is enabled.
# Authoritative ACP v1 McpServerStdio: no ``type``, ``env`` is an array.
_EXPECTED = {
    "name": "deeptutor",
    "command": sys.executable,
    "args": ["-m", "deeptutor.mcp_server", "--transport", "stdio"],
    "env": [],
}


def _set_flag(monkeypatch, value: str | None) -> None:
    if value is None:
        monkeypatch.delenv(ENV_FLAG, raising=False)
    else:
        monkeypatch.setenv(ENV_FLAG, value)


def _expected(value: str | None) -> list[dict]:
    return [_EXPECTED] if value is not None and value.lower() in {"1", "true", "yes"} else []


class _RecordingSession:
    """Minimal stand-in for acp._HostSession that records outgoing requests."""

    def __init__(self) -> None:
        self.frames: asyncio.Queue = asyncio.Queue()
        self.process = SimpleNamespace(returncode=0)
        self.requests: list[tuple[str, dict]] = []
        self._seq = 0

    async def emit(self, *_args, **_kwargs) -> None:
        return None

    async def send_request(self, method: str, params: dict) -> int:
        self.requests.append((method, params))
        self._seq += 1
        request_id = self._seq
        if method == "initialize":
            result = {"protocolVersion": 1, "agentCapabilities": {"loadSession": True}}
        elif method == "session/new":
            result = {"sessionId": "s-1"}
        else:
            result = {}
        self.frames.put_nowait(("frame", {"jsonrpc": "2.0", "id": request_id, "result": result}))
        return request_id


async def _handshake_params(monkeypatch, *, resume: str | None = None) -> tuple[str, dict]:
    session = _RecordingSession()
    session_id = await _establish_session(session, resume=resume, cwd="/tmp/deeptutor-bridge")
    assert session.requests[-1][0] == ("session/load" if resume else "session/new")
    return session_id, session.requests[-1][1]


# ---- flag semantics ---------------------------------------------------------------


def test_disabled_by_default(monkeypatch) -> None:
    _set_flag(monkeypatch, None)
    assert mcp_bridge.enabled() is False
    assert mcp_bridge.build_mcp_servers() == []


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "True", "yes", "YES", "YeS"])
def test_enabled_true_spellings(monkeypatch, value: str) -> None:
    _set_flag(monkeypatch, value)
    assert mcp_bridge.enabled() is True
    assert mcp_bridge.build_mcp_servers() == [_EXPECTED]


@pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "NO", "", "on", "true-ish"])
def test_disabled_other_spellings(monkeypatch, value: str) -> None:
    _set_flag(monkeypatch, value)
    assert mcp_bridge.enabled() is False
    assert mcp_bridge.build_mcp_servers() == []


def test_descriptor_shape(monkeypatch) -> None:
    _set_flag(monkeypatch, "1")
    servers = mcp_bridge.build_mcp_servers()

    assert isinstance(servers, list)
    assert len(servers) == 1
    assert servers[0] == _EXPECTED
    assert set(servers[0]) == {"name", "command", "args", "env"}


def test_descriptor_matches_acp_v1_stdio_schema(monkeypatch) -> None:
    """The descriptor must satisfy the authoritative ACP v1 McpServerStdio shape:
    exactly name/command/args/env, no ``type``, env is an array, and command is
    an absolute path (see acp-schema/v1-schema.json)."""
    _set_flag(monkeypatch, "1")
    descriptor = mcp_bridge.build_mcp_servers()[0]

    assert set(descriptor) == {"name", "command", "args", "env"}
    assert "type" not in descriptor
    assert isinstance(descriptor["env"], list)
    assert os.path.isabs(descriptor["command"])
    assert isinstance(descriptor["args"], list)


def test_default_off_returns_empty_list(monkeypatch) -> None:
    """With the opt-in flag absent, no MCP server is offered to the agent."""
    _set_flag(monkeypatch, None)
    assert mcp_bridge.build_mcp_servers() == []


def test_descriptor_carries_no_secret_values(monkeypatch) -> None:
    secrets = {
        "DEEPTUTOR_API_KEY": "sk-deeptutor-bridge-secret-123",
        "OPENAI_API_KEY": "sk-openai-bridge-secret-456",
        "AWS_SECRET_ACCESS_KEY": "aws-bridge-secret-789",
    }
    for key, value in secrets.items():
        monkeypatch.setenv(key, value)
    _set_flag(monkeypatch, "yes")

    servers = mcp_bridge.build_mcp_servers()
    payload = json.dumps(servers)
    assert servers[0]["env"] == []
    for value in secrets.values():
        assert value not in payload
    for key in secrets:
        assert key not in payload
    assert ENV_FLAG not in payload


# ---- ACP handshake wiring ---------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("flag", [None, "0", "false", "1", "TRUE", "yes"])
async def test_session_new_carries_descriptor(monkeypatch, flag: str | None) -> None:
    _set_flag(monkeypatch, flag)
    session_id, params = await _handshake_params(monkeypatch)

    assert session_id == "s-1"
    assert params["cwd"] == "/tmp/deeptutor-bridge"
    assert params["mcpServers"] == _expected(flag)


@pytest.mark.asyncio
@pytest.mark.parametrize("flag", [None, "false", "1", "yes"])
async def test_session_load_carries_descriptor(monkeypatch, flag: str | None) -> None:
    _set_flag(monkeypatch, flag)
    session_id, params = await _handshake_params(monkeypatch, resume="resume-me")

    assert session_id == "resume-me"
    assert params["sessionId"] == "resume-me"
    assert params["cwd"] == "/tmp/deeptutor-bridge"
    assert params["mcpServers"] == _expected(flag)


@pytest.mark.asyncio
async def test_acp_uses_lazy_build_mcp_servers(monkeypatch) -> None:
    """The handshake obtains the list through mcp_bridge, not a hard-coded literal."""
    sentinel = [{"name": "patched", "command": "x", "args": [], "env": []}]
    monkeypatch.setattr(mcp_bridge, "build_mcp_servers", lambda: sentinel)
    _set_flag(monkeypatch, "1")

    _, params = await _handshake_params(monkeypatch)
    assert params["mcpServers"] == sentinel
