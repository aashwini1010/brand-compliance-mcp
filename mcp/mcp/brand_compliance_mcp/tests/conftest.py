"""Shared pytest fixtures."""

import asyncio
import socket
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import uvicorn
from fastmcp import Client, FastMCP
from pydantic import SecretStr

from brand_compliance.core.contracts import RuleExtractor
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.core.settings import PathSettings, ServerSettings, Settings
from brand_compliance.models.guide import GuideDocument
from brand_compliance.models.rule import Rule
from brand_compliance.plugins.extractors import register_extractors
from brand_compliance.plugins.sources.markdown import MarkdownSourceAdapter
from brand_compliance.rules.interpret import interpret_guide
from brand_compliance.rules.vocabulary import load_vocabulary
from brand_compliance.server.app import build_http_app, create_server

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def write_file(tmp_path: Path) -> Callable[[str, str], Path]:
    """Return a helper that writes text to a named file in a temp folder."""

    def _write(name: str, content: str) -> Path:
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        return path

    return _write


@pytest.fixture
def myridius_guide_path() -> Path:
    """Path to the real Myridius brand guide used as the main test input."""
    path = PROJECT_ROOT / "myridius-brand-guide.md"
    if not path.is_file():
        pytest.skip("myridius-brand-guide.md not present")
    return path


@pytest.fixture
def load_guide(
    write_file: Callable[[str, str], Path],
) -> Callable[[str], GuideDocument]:
    """Return a helper that parses Markdown text into a ``GuideDocument``."""

    def _load(text: str) -> GuideDocument:
        return MarkdownSourceAdapter().load(write_file("guide.md", text))

    return _load


@pytest.fixture
def interpret(
    load_guide: Callable[[str], GuideDocument],
) -> Callable[[str], list[Rule]]:
    """Return a helper running the full interpretation on Markdown text."""
    registry = PluginRegistry()
    vocabulary = load_vocabulary()
    register_extractors(
        registry, bullet_specs=[(s.section, s.label) for s in vocabulary.bullet_specs]
    )

    def _interpret(text: str) -> list[Rule]:
        return interpret_guide(
            load_guide(text), registry.plugins(RuleExtractor), vocabulary
        ).rules

    return _interpret


@pytest.fixture(scope="module")
def myridius_guide_path_module() -> Path:
    """Module-scoped path to the Myridius guide (for expensive shared parsing)."""
    path = PROJECT_ROOT / "myridius-brand-guide.md"
    if not path.is_file():
        pytest.skip("myridius-brand-guide.md not present")
    return path


SMALL_GUIDE = """\
## 2.1 Core Tokens

| Token | Hex |
|---|---|
| `--ink` | `#111111` |

## 3.1 Font Stack

```css
--font-sans: "Montserrat", Arial, sans-serif;
```

## 3.2 Scale

| Token | Size | Weight | Line-height | Letter-spacing | Use |
|---|---|---|---|---|---|
| `--fs-h1` | 2rem | 700 | 1.1 | 0 | Title |

## 2.5 Rules

- Body text minimum contrast ratio: **4.5:1** against its surface.

## 9. Voice

Be calm and clear.
"""

SMALL_PAGE = """<!doctype html><html><head><title>t</title><style>
body{background:#ffffff;font-family:Georgia,serif} h1{font-size:3rem;color:#222222}
</style></head><body><main><h1>Hello</h1><p>World</p></main></body></html>"""


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A folder with a small guide, a small page and an output folder."""
    (tmp_path / "guide.md").write_text(SMALL_GUIDE, encoding="utf-8")
    (tmp_path / "page.html").write_text(SMALL_PAGE, encoding="utf-8")
    (tmp_path / "out").mkdir()
    return tmp_path


TEST_TOKEN = "t" * 32


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _server_settings(root: Path, port: int = 8000) -> Settings:
    return Settings(
        server=ServerSettings(port=port),
        auth_token=SecretStr(TEST_TOKEN),
        paths=PathSettings(
            allowed_input_dirs=[str(root)], allowed_output_dirs=[str(root / "out")]
        ),
    )


@pytest.fixture
def mcp_server(workspace: Path) -> FastMCP:
    """The real MCP server over a temporary workspace (used in memory)."""
    return create_server(_server_settings(workspace), load_vocabulary())


@pytest.fixture
def call_tool() -> Callable[[FastMCP, str, dict[str, Any]], Any]:
    """Return a helper that calls a tool in memory and returns the result."""

    def _call(server: FastMCP, name: str, arguments: dict[str, Any]) -> Any:
        async def go() -> Any:
            async with Client(server) as client:
                return await client.call_tool(name, arguments)

        return asyncio.run(go())

    return _call


@dataclass
class HttpServer:
    """A running server: where it listens and the token it accepts."""

    base_url: str
    token: str
    port: int


@pytest.fixture
def http_server(workspace: Path) -> Iterator[HttpServer]:
    """The real server on a real local port (HTTP + SSE), stopped afterwards."""
    port = _free_port()
    settings = _server_settings(workspace, port)
    app = build_http_app(create_server(settings, load_vocabulary()), settings)
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.02)
    assert server.started, "the test server did not start"
    yield HttpServer(f"http://127.0.0.1:{port}", TEST_TOKEN, port)
    server.should_exit = True
    thread.join(timeout=10)
