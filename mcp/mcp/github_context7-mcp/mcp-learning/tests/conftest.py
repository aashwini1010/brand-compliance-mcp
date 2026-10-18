"""Shared fixtures for the test suite."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    """Prevent real credentials from leaking into tests."""
    for name in (
        "GITHUB_MCP_URL",
        "GITHUB_TOKEN",
        "CONTEXT_MCP_URL",
        "CONTEXT_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("mcp_clients.base_client.load_dotenv", lambda: False)


@pytest.fixture
def fake_session():
    """A mock MCP session exposing one tool named 'echo'."""
    tool = MagicMock()
    tool.name = "echo"
    session = AsyncMock()
    session.list_tools.return_value = MagicMock(tools=[tool])
    return session
