"""Tests for the MCP safety policy."""

from deeptutor.mcp_server import policy


def test_default_allows_all_safe_tools(monkeypatch):
    monkeypatch.delenv("DEEPTUTOR_MCP_ALLOW", raising=False)
    assert policy.allowed_tools() == policy.SAFE_TOOLS
    assert policy.is_allowed("rag")
    assert policy.is_allowed("read_skill")


def test_env_narrows_allowed_tools(monkeypatch):
    monkeypatch.setenv("DEEPTUTOR_MCP_ALLOW", "rag, read_skill")
    assert policy.allowed_tools() == frozenset({"rag", "read_skill"})
    assert policy.is_allowed("rag")
    assert not policy.is_allowed("kb_files")


def test_env_ignores_unknown_and_cannot_widen(monkeypatch):
    monkeypatch.setenv("DEEPTUTOR_MCP_ALLOW", "rag,not_a_tool,delete_everything")
    assert policy.allowed_tools() == frozenset({"rag"})
    assert not policy.is_allowed("not_a_tool")
    assert not policy.is_allowed("delete_everything")


def test_empty_env_falls_back_to_safe_tools(monkeypatch):
    monkeypatch.setenv("DEEPTUTOR_MCP_ALLOW", "  ,  ")
    assert policy.allowed_tools() == policy.SAFE_TOOLS


def test_is_allowed_denies_unsafe_names():
    assert not policy.is_allowed("write_file")
    assert not policy.is_allowed("")
    assert not policy.is_allowed(123)  # type: ignore[arg-type]


def test_redact_args_drops_sensitive_keys():
    args = {
        "query": "hello",
        "api_key": "secret",
        "token": "t",
        "access_token": "t",
        "secret_value": "s",
        "password": "p",
        "credential": "c",
        "Authorization": "Bearer x",
    }
    out = policy.redact_args(args)
    assert out == {"query": "hello"}


def test_redact_args_caps_strings():
    out = policy.redact_args({"q": "x" * 5000, "n": 123})
    assert out["q"] == "x" * 2000
    assert out["n"] == 123


def test_redact_args_caps_dict_keys():
    out = policy.redact_args({f"k{i}": i for i in range(50)})
    assert len(out) == 20


def test_redact_args_handles_non_dict():
    assert policy.redact_args([]) == {}  # type: ignore[arg-type]
