"""The real server on a real port: HTTP + SSE, token, Host and Origin checks."""

from __future__ import annotations

import asyncio
import socket
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx2 as httpx
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from brand_compliance.pipeline.orchestrator import Orchestrator

if TYPE_CHECKING:
    from conftest import HttpServer


def _status(url: str, headers: dict[str, str]) -> int:
    """GET the SSE endpoint and return the status without reading the stream."""
    with httpx.stream("GET", url, headers=headers, timeout=5) as response:
        return int(response.status_code)


def _run(server: HttpServer, action: Any) -> Any:
    async def go() -> Any:
        async with Client(f"{server.base_url}/sse", auth=server.token) as client:
            return await action(client)

    return asyncio.run(go())


def test_connection_without_a_token_is_refused(http_server: HttpServer) -> None:
    assert _status(f"{http_server.base_url}/sse", {}) == 401


def test_connection_with_a_wrong_token_is_refused(http_server: HttpServer) -> None:
    headers = {"Authorization": "Bearer not-the-token"}
    assert _status(f"{http_server.base_url}/sse", headers) == 401


def test_a_request_aimed_at_another_host_name_is_refused(
    http_server: HttpServer,
) -> None:
    headers = {"Authorization": f"Bearer {http_server.token}", "Host": "evil.example"}
    assert _status(f"{http_server.base_url}/sse", headers) == 421


def test_a_request_from_a_foreign_web_page_origin_is_refused(
    http_server: HttpServer,
) -> None:
    headers = {
        "Authorization": f"Bearer {http_server.token}",
        "Origin": "http://evil.example",
    }
    assert _status(f"{http_server.base_url}/sse", headers) == 403


def test_message_endpoint_also_requires_the_token(http_server: HttpServer) -> None:
    response = httpx.post(
        f"{http_server.base_url}/messages/?session_id=x", json={}, timeout=5
    )
    assert response.status_code == 401


def test_client_with_the_token_lists_the_five_tools(http_server: HttpServer) -> None:
    async def action(client: Client) -> list[str]:
        return sorted(t.name for t in await client.list_tools())

    assert _run(http_server, action) == [
        "apply_brand",
        "classify_artifact",
        "extract_rules",
        "get_report",
        "list_plugins",
    ]


def test_full_workflow_over_http_writes_files_and_the_report_can_be_fetched(
    http_server: HttpServer, workspace: Path
) -> None:
    async def action(client: Client) -> tuple[Any, Any]:
        run = await client.call_tool(
            "apply_brand",
            {
                "guide_path": str(workspace / "guide.md"),
                "artifact_path": str(workspace / "page.html"),
                "output_dir": str(workspace / "out"),
            },
        )
        report = await client.call_tool("get_report", {"run_id": run.data.run_id})
        return run.data, report.data

    summary, report = _run(http_server, action)
    assert str(summary.status).endswith("completed")
    assert all(summary.checks.values())
    assert (Path(summary.output_dir) / "branded.html").is_file()
    assert report.content.startswith("# Brand compliance report")


def test_typed_error_codes_reach_the_client(
    http_server: HttpServer, workspace: Path
) -> None:
    async def action(client: Client) -> None:
        await client.call_tool(
            "apply_brand",
            {
                "guide_path": "/etc/passwd",
                "artifact_path": str(workspace / "page.html"),
                "output_dir": str(workspace / "out"),
            },
        )

    with pytest.raises(ToolError, match=r"\[PATH_NOT_ALLOWED\]"):
        _run(http_server, action)


def test_unexpected_server_errors_are_masked_for_the_client(
    http_server: HttpServer, workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(*args: object, **kwargs: object) -> None:
        raise RuntimeError("internal secret: /home/someone/client-material.html")

    monkeypatch.setattr(Orchestrator, "run", explode)

    async def action(client: Client) -> None:
        await client.call_tool(
            "apply_brand",
            {
                "guide_path": str(workspace / "guide.md"),
                "artifact_path": str(workspace / "page.html"),
                "output_dir": str(workspace / "out"),
            },
        )

    with pytest.raises(ToolError) as info:
        _run(http_server, action)
    assert "internal secret" not in str(info.value)
    assert "client-material" not in str(info.value)
    assert "INTERNAL_ERROR" in str(info.value)


def test_the_server_listens_only_on_loopback(http_server: HttpServer) -> None:
    outside = socket.gethostbyname(socket.gethostname())
    if outside.startswith("127."):
        pytest.skip("no non-loopback address to probe on this machine")
    with (
        pytest.raises(OSError),
        socket.create_connection((outside, http_server.port), timeout=1),
    ):
        pass
