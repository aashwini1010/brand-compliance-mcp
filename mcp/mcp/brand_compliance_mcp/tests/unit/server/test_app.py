"""Tests for the server factory, startup checks and the tools (in memory)."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import SecretStr

from brand_compliance.core.errors import ConfigurationError
from brand_compliance.core.settings import ServerSettings, Settings
from brand_compliance.models.report import RunStatus
from brand_compliance.server.app import endpoint_url, validate_startup

CallTool = Callable[[FastMCP, str, dict[str, Any]], Any]
GOOD_TOKEN = "t" * 32


def _settings(**server: object) -> Settings:
    token = server.pop("token", GOOD_TOKEN)
    return Settings(
        server=ServerSettings(**server),  # type: ignore[arg-type]
        auth_token=SecretStr(token) if token else None,  # type: ignore[arg-type]
    )


def test_startup_accepts_a_loopback_server_with_a_good_token() -> None:
    validate_startup(_settings())


def test_startup_refuses_a_missing_token_and_says_how_to_make_one() -> None:
    with pytest.raises(ConfigurationError, match="BRAND_MCP_AUTH_TOKEN"):
        validate_startup(_settings(token=None))


def test_startup_refuses_a_token_that_is_too_short() -> None:
    with pytest.raises(ConfigurationError, match="too short"):
        validate_startup(_settings(token="short"))  # noqa: S106 (a deliberately bad test value)


def test_startup_allows_no_token_only_when_auth_is_off_and_loopback_only(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("WARNING"):
        validate_startup(_settings(token=None, require_auth=False))
    assert any("Authentication is turned off" in r.message for r in caplog.records)


def test_startup_never_allows_an_open_server_beyond_localhost() -> None:
    with pytest.raises(ConfigurationError, match="reachable beyond this machine"):
        validate_startup(_settings(token=None, require_auth=False, host="0.0.0.0"))  # noqa: S104


def test_startup_warns_when_listening_beyond_localhost(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("WARNING"):
        validate_startup(_settings(host="0.0.0.0"))  # noqa: S104
    assert any("put TLS in front" in r.message for r in caplog.records)


@pytest.mark.parametrize(
    ("server", "expected"),
    [
        ({}, "http://127.0.0.1:8000/sse"),
        ({"port": 9100, "host": "::1"}, "http://[::1]:9100/sse"),
        ({"transport": "http"}, "http://127.0.0.1:8000/mcp"),
    ],
)
def test_endpoint_url_names_what_clients_connect_to(
    server: dict[str, Any], expected: str
) -> None:
    assert endpoint_url(_settings(**server)) == expected


def test_server_exposes_exactly_the_five_documented_tools(mcp_server: FastMCP) -> None:
    import asyncio

    async def names() -> dict[str, Any]:
        async with Client(mcp_server) as client:
            return {t.name: t for t in await client.list_tools()}

    tools = asyncio.run(names())
    assert sorted(tools) == [
        "apply_brand",
        "classify_artifact",
        "extract_rules",
        "get_report",
        "list_plugins",
    ]
    assert all(t.description for t in tools.values())
    assert tools["apply_brand"].annotations.read_only_hint is False
    assert tools["extract_rules"].annotations.read_only_hint is True


def test_apply_brand_runs_the_workflow_and_returns_the_summary(
    mcp_server: FastMCP, call_tool: CallTool, workspace: Path
) -> None:
    result = call_tool(
        mcp_server,
        "apply_brand",
        {
            "guide_path": str(workspace / "guide.md"),
            "artifact_path": str(workspace / "page.html"),
            "output_dir": str(workspace / "out"),
        },
    )
    summary = result.data
    assert (
        summary.status == RunStatus.COMPLETED.value
        or summary.status is RunStatus.COMPLETED
    )
    assert summary.change_count > 0
    assert (Path(summary.output_dir) / "branded.html").is_file()


def test_apply_brand_refuses_a_path_outside_the_allowed_folders(
    mcp_server: FastMCP, call_tool: CallTool, workspace: Path
) -> None:
    with pytest.raises(ToolError, match=r"\[PATH_NOT_ALLOWED\]"):
        call_tool(
            mcp_server,
            "apply_brand",
            {
                "guide_path": "/etc/passwd",
                "artifact_path": str(workspace / "page.html"),
                "output_dir": str(workspace / "out"),
            },
        )


def test_apply_brand_rejects_an_unknown_artifact_type_before_running(
    mcp_server: FastMCP, call_tool: CallTool, workspace: Path
) -> None:
    with pytest.raises(ToolError):
        call_tool(
            mcp_server,
            "apply_brand",
            {
                "guide_path": str(workspace / "guide.md"),
                "artifact_path": str(workspace / "page.html"),
                "output_dir": str(workspace / "out"),
                "artifact_type": "pdf",
            },
        )


def test_extract_rules_counts_by_status_and_lists_conflicts(
    mcp_server: FastMCP, call_tool: CallTool, workspace: Path
) -> None:
    data = call_tool(
        mcp_server, "extract_rules", {"guide_path": str(workspace / "guide.md")}
    ).data
    assert data.total == sum(data.counts.values())
    assert data.returned == data.total
    assert not data.truncated
    assert {r.guide_line.split(":")[0] for r in data.rules} == {"guide.md"}


def test_extract_rules_can_filter_by_status_and_limit(
    mcp_server: FastMCP, call_tool: CallTool, workspace: Path
) -> None:
    only = call_tool(
        mcp_server,
        "extract_rules",
        {"guide_path": str(workspace / "guide.md"), "status": "could_not_interpret"},
    ).data
    assert only.returned >= 1
    assert {r.status for r in only.rules} == {"could_not_interpret"}
    limited = call_tool(
        mcp_server,
        "extract_rules",
        {"guide_path": str(workspace / "guide.md"), "limit": 1},
    ).data
    assert limited.returned == 1
    assert limited.truncated


def test_extract_rules_rejects_an_unknown_status(
    mcp_server: FastMCP, call_tool: CallTool, workspace: Path
) -> None:
    with pytest.raises(ToolError, match=r"\[INVALID_INPUT\] status must be one of"):
        call_tool(
            mcp_server,
            "extract_rules",
            {"guide_path": str(workspace / "guide.md"), "status": "great"},
        )


def test_classify_artifact_returns_the_verdict_with_signals(
    mcp_server: FastMCP, call_tool: CallTool, workspace: Path
) -> None:
    data = call_tool(
        mcp_server, "classify_artifact", {"artifact_path": str(workspace / "page.html")}
    ).data
    assert data.signals
    assert 0.0 <= data.confidence <= 1.0


def test_get_report_returns_markdown_or_json_of_a_saved_run(
    mcp_server: FastMCP, call_tool: CallTool, workspace: Path
) -> None:
    run = call_tool(
        mcp_server,
        "apply_brand",
        {
            "guide_path": str(workspace / "guide.md"),
            "artifact_path": str(workspace / "page.html"),
            "output_dir": str(workspace / "out"),
        },
    ).data
    markdown = call_tool(mcp_server, "get_report", {"run_id": run.run_id}).data
    as_json = call_tool(
        mcp_server, "get_report", {"run_id": run.run_id, "format": "json"}
    ).data
    assert markdown.content.startswith("# Brand compliance report")
    assert json.loads(as_json.content)["run"]["run_id"] == run.run_id


@pytest.mark.parametrize(
    "run_id", ["../../etc/passwd", "run-1", "", "run-20260101-000000-ZZZZZZ"]
)
def test_get_report_rejects_ids_that_are_not_run_ids(
    mcp_server: FastMCP, call_tool: CallTool, run_id: str
) -> None:
    with pytest.raises(ToolError, match=r"\[INVALID_INPUT\]"):
        call_tool(mcp_server, "get_report", {"run_id": run_id})


def test_get_report_says_so_for_a_run_that_does_not_exist(
    mcp_server: FastMCP, call_tool: CallTool
) -> None:
    with pytest.raises(ToolError, match="No saved run"):
        call_tool(mcp_server, "get_report", {"run_id": "run-20260101-000000-abcdef"})


def test_list_plugins_shows_every_loaded_interface(
    mcp_server: FastMCP, call_tool: CallTool
) -> None:
    plugins = call_tool(mcp_server, "list_plugins", {}).data.plugins
    assert plugins["SourceAdapter"] == ["markdown"]
    assert "contrast" in plugins["Verifier"]
    assert sorted(plugins["Reporter"]) == ["guide-rules", "json", "markdown"]


def test_report_is_readable_as_a_resource(
    mcp_server: FastMCP, call_tool: CallTool, workspace: Path
) -> None:
    import asyncio

    run = call_tool(
        mcp_server,
        "apply_brand",
        {
            "guide_path": str(workspace / "guide.md"),
            "artifact_path": str(workspace / "page.html"),
            "output_dir": str(workspace / "out"),
        },
    ).data

    async def read() -> str:
        async with Client(mcp_server) as client:
            return str((await client.read_resource(f"report://{run.run_id}"))[0].text)

    assert asyncio.run(read()).startswith("# Brand compliance report")
