"""Unit tests for the MCP client wrappers."""

import pytest

from src.mcp_clients import Context7MCPClient, GitHubMCPClient


@pytest.mark.parametrize(
    "client_cls, url_var, token_var",
    [
        (GitHubMCPClient, "GITHUB_MCP_URL", "GITHUB_TOKEN"),
        (Context7MCPClient, "CONTEXT_MCP_URL", "CONTEXT_TOKEN"),
    ],
)
def test_init_reads_environment(monkeypatch, client_cls, url_var, token_var):
    monkeypatch.setenv(url_var, "https://example.test/mcp")
    monkeypatch.setenv(token_var, "secret")

    client = client_cls()

    assert client.url == "https://example.test/mcp"
    assert client.token == "secret"


@pytest.mark.parametrize("client_cls", [GitHubMCPClient, Context7MCPClient])
def test_init_missing_url_raises(client_cls):
    with pytest.raises(ValueError, match="URL is not configured"):
        client_cls(token="secret")


@pytest.mark.parametrize("client_cls", [GitHubMCPClient, Context7MCPClient])
def test_init_missing_token_raises(client_cls):
    with pytest.raises(ValueError, match="token is not configured"):
        client_cls(url="https://example.test/mcp")


async def test_list_tools_before_connect_raises():
    client = GitHubMCPClient(url="u", token="t")

    with pytest.raises(RuntimeError):
        await client.list_tools()


async def test_call_tool_before_connect_raises():
    client = GitHubMCPClient(url="u", token="t")

    with pytest.raises(RuntimeError):
        await client.call_tool("echo")


async def test_call_tool_unknown_name_raises(fake_session):
    client = GitHubMCPClient(url="u", token="t")
    client.session = fake_session

    with pytest.raises(ValueError, match="Unknown tool"):
        await client.call_tool("missing")


async def test_call_tool_known_name_delegates(fake_session):
    client = GitHubMCPClient(url="u", token="t")
    client.session = fake_session
    await client.list_tools()

    await client.call_tool("echo", {"a": 1})

    fake_session.call_tool.assert_awaited_once_with("echo", arguments={"a": 1})


async def test_close_without_connect_is_noop():
    client = GitHubMCPClient(url="u", token="t")

    await client.close()

    assert client.session is None


@pytest.fixture
def patched_transport(monkeypatch, fake_session):
    """Replace the HTTP transport and session with async context mocks."""
    from contextlib import asynccontextmanager
    from unittest.mock import MagicMock

    @asynccontextmanager
    async def _http_client(**_kwargs):
        yield MagicMock()

    @asynccontextmanager
    async def _transport(_url, http_client=None):
        yield ("read", "write")

    @asynccontextmanager
    async def _session(_read, _write):
        yield fake_session

    monkeypatch.setattr("mcp_clients.base_client.httpx2.AsyncClient", _http_client)
    monkeypatch.setattr("mcp_clients.base_client.streamable_http_client", _transport)
    monkeypatch.setattr("mcp_clients.base_client.ClientSession", _session)
    return fake_session


async def test_context_manager_connects_and_closes(patched_transport):
    async with GitHubMCPClient(url="u", token="t") as client:
        tools = await client.list_tools()

        assert client.session is patched_transport
        assert [tool.name for tool in tools] == ["echo"]

    assert client.session is None
    assert client.tools == {}


async def test_connect_twice_reuses_session(patched_transport):
    client = GitHubMCPClient(url="u", token="t")

    first = await client.connect()
    second = await client.connect()

    assert first is second
    await client.close()


async def test_connect_failure_propagates_and_leaves_closed(patched_transport):
    patched_transport.initialize.side_effect = RuntimeError("boom")
    client = GitHubMCPClient(url="u", token="t")

    with pytest.raises(RuntimeError, match="boom"):
        await client.connect()

    assert client.session is None
