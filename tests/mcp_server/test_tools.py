"""Tests for the JSON-safe MCP tool wrappers (no network)."""

import asyncio
import json

import pytest

from deeptutor.core.tool_protocol import ToolResult
from deeptutor.mcp_server import tools


def _run(coro):
    return json.loads(asyncio.run(coro))


def test_list_tools_json_default_allowlist(monkeypatch):
    monkeypatch.delenv("DEEPTUTOR_MCP_ALLOW", raising=False)
    data = _run(tools.list_tools_json())
    assert data["ok"] is True
    names = {item["function"]["name"] for item in data["tools"]}
    assert names == {
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


def test_list_tools_json_respects_narrowing(monkeypatch):
    monkeypatch.setenv("DEEPTUTOR_MCP_ALLOW", "rag")
    data = _run(tools.list_tools_json())
    assert {item["function"]["name"] for item in data["tools"]} == {"rag"}


def test_call_tool_default_denies_unknown():
    data = _run(tools.call_tool("delete_everything"))
    assert data["ok"] is False
    assert "not allowed" in data["error"]


def test_call_tool_serializes_only_public_fields(monkeypatch):
    captured = {}

    class FakeRegistry:
        async def execute(self, name, **kwargs):
            captured["name"] = name
            captured["kwargs"] = kwargs
            return ToolResult(
                content="answer",
                sources=[{"path": "a", "api_key": "MUST_NOT_LEAK"}],
                metadata={"k": "v"},
                success=True,
                model_message={"secret_image": "MUST_NOT_LEAK"},
                pause_for_user={"question": "MUST_NOT_LEAK"},
                public_result={"safe": True},
            )

    monkeypatch.setattr(tools, "get_tool_registry", lambda: FakeRegistry())
    data = _run(tools.call_tool("rag", {"query": "hi"}))
    assert data["ok"] is True
    result = data["result"]
    assert set(result) == {"content", "sources", "success", "public_result"}
    assert result["content"] == "answer"
    assert result["sources"] == [{"path": "a"}]
    assert result["public_result"] == {"safe": True}
    assert captured == {"name": "rag", "kwargs": {"query": "hi"}}


def test_call_tool_does_not_leak_exception_text(monkeypatch):
    class BrokenRegistry:
        async def execute(self, name, **kwargs):
            raise RuntimeError("secret path /data/whatever")

    monkeypatch.setattr(tools, "get_tool_registry", lambda: BrokenRegistry())
    data = _run(tools.call_tool("rag"))
    assert data["ok"] is False
    assert "secret path" not in data["error"]
    assert "RuntimeError" in data["error"]


def test_call_tool_rejects_non_dict_arguments():
    data = _run(tools.call_tool("rag", ["bad"]))  # type: ignore[arg-type]
    assert data["ok"] is False


def test_native_skill_tools_respect_narrowed_allowlist(monkeypatch):
    monkeypatch.setenv("DEEPTUTOR_MCP_ALLOW", "rag")
    listed = _run(tools.list_skills_json())
    read = _run(tools.read_skill_text("docx"))
    assert listed["ok"] is False and "not allowed" in listed["error"]
    assert read["ok"] is False and "not allowed" in read["error"]


def test_list_skills_json(monkeypatch):
    monkeypatch.delenv("DEEPTUTOR_MCP_ALLOW", raising=False)
    from deeptutor.services.skill.service import SkillInfo

    class FakeService:
        def list_skills(self):
            return [
                SkillInfo(
                    name="docx",
                    description="desc",
                    tags=["tool"],
                    source="builtin",
                )
            ]

    monkeypatch.setattr(tools, "get_skill_service", lambda: FakeService())
    data = _run(tools.list_skills_json())
    assert data["ok"] is True
    assert data["skills"] == [
        {"name": "docx", "description": "desc", "tags": ["tool"], "source": "builtin"}
    ]


def test_read_skill_text(monkeypatch):
    monkeypatch.delenv("DEEPTUTOR_MCP_ALLOW", raising=False)

    class FakeService:
        def read_skill_file(self, name, rel_path="SKILL.md"):
            assert name == "docx"
            assert rel_path == "SKILL.md"
            return "# Docx skill"

    monkeypatch.setattr(tools, "get_skill_service", lambda: FakeService())
    data = _run(tools.read_skill_text("docx"))
    assert data["ok"] is True
    assert data["text"] == "# Docx skill"


def test_read_skill_text_validates_name():
    data = _run(tools.read_skill_text(""))
    assert data["ok"] is False


@pytest.mark.asyncio
async def test_real_skill_service_rejects_path_traversal(monkeypatch):
    """Exercise the real hardened service, not a mock of it."""
    monkeypatch.delenv("DEEPTUTOR_MCP_ALLOW", raising=False)
    listed = json.loads(await tools.list_skills_json())
    if not listed.get("skills"):
        pytest.skip("no real skills visible in this environment")
    name = listed["skills"][0]["name"]
    data = json.loads(await tools.read_skill_text(name, "../etc/passwd"))
    assert data["ok"] is False
