"""Tests for the FastMCP server construction and CLI (no network)."""

import json

import pytest

from deeptutor.mcp_server import server


def _text_of(result):
    """Extract the first TextContent string from FastMCP call_tool output."""
    content = result[0] if isinstance(result, tuple) else result
    return content[0].text


@pytest.mark.asyncio
async def test_build_server_registers_exactly_four_tools():
    mcp = server.build_server()
    tools = await mcp.list_tools()
    assert {tool.name for tool in tools} == {
        "deeptutor_list_tools",
        "deeptutor_call_tool",
        "deeptutor_list_skills",
        "deeptutor_read_skill",
    }
    assert len(tools) == 4


@pytest.mark.asyncio
async def test_call_tool_bridge_real_code_denies_unlisted_tool(monkeypatch):
    """No fake of the code under test: real FastMCP dispatch + real policy."""
    monkeypatch.delenv("DEEPTUTOR_MCP_ALLOW", raising=False)
    mcp = server.build_server()
    result = await mcp.call_tool("deeptutor_call_tool", {"name": "delete_all"})
    assert json.loads(_text_of(result))["ok"] is False


@pytest.mark.asyncio
async def test_native_skill_tools_are_allowlist_gated(monkeypatch):
    monkeypatch.setenv("DEEPTUTOR_MCP_ALLOW", "rag")
    mcp = server.build_server()
    for tool_name in ("deeptutor_list_skills", "deeptutor_read_skill"):
        args = {} if tool_name == "deeptutor_list_skills" else {"name": "docx"}
        result = await mcp.call_tool(tool_name, args)
        assert json.loads(_text_of(result))["ok"] is False


@pytest.mark.asyncio
async def test_stdout_stays_clean(monkeypatch, capsys):
    """stdout is the MCP JSON-RPC channel; no handler may print to it."""
    monkeypatch.delenv("DEEPTUTOR_MCP_ALLOW", raising=False)
    mcp = server.build_server()
    await mcp.call_tool("deeptutor_list_tools", {})
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "audit tool=deeptutor_list_tools" not in captured.out


@pytest.mark.asyncio
async def test_list_tools_bridge(monkeypatch):
    monkeypatch.delenv("DEEPTUTOR_MCP_ALLOW", raising=False)
    mcp = server.build_server()
    result = await mcp.call_tool("deeptutor_list_tools", {})
    assert json.loads(_text_of(result))["ok"] is True


def test_cli_rejects_non_stdio_transport():
    from deeptutor.mcp_server.cli import main

    with pytest.raises(SystemExit) as exc:
        main(["--transport", "sse"])
    assert exc.value.code != 0


def test_cli_accepts_stdio(monkeypatch):
    from deeptutor.mcp_server.cli import main

    called = {}
    monkeypatch.setattr(server, "run_stdio", lambda: called.setdefault("run", True))
    # main imports run_stdio lazily from server, so patch there.
    assert main(["--transport", "stdio"]) == 0
    assert called.get("run") is True
