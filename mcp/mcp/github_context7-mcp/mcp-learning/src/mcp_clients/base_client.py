"""Shared asynchronous client for remote MCP servers over streamable HTTP."""

import logging
import os
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

import httpx2
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT_SECONDS = 30.0
READ_TIMEOUT_SECONDS = 300.0


class BaseMCPClient:
    """Reusable async MCP client; subclasses set the name and env variables."""

    server_name: str = "MCP"
    url_env_var: str = ""
    token_env_var: str = ""

    def __init__(
        self, url: Optional[str] = None, token: Optional[str] = None
    ) -> None:
        """Resolve the URL and token from arguments or environment variables."""
        load_dotenv()

        self.url = url or os.getenv(self.url_env_var)
        self.token = token or os.getenv(self.token_env_var)

        if not self.url:
            raise ValueError(f"{self.server_name} MCP URL is not configured")
        if not self.token:
            raise ValueError(f"{self.server_name} token is not configured")

        self._stack: Optional[AsyncExitStack] = None
        self.session: Optional[ClientSession] = None
        self.tools: Dict[str, Any] = {}

    async def connect(self) -> "BaseMCPClient":
        """Open the HTTP transport and initialize the MCP session."""
        if self.session is not None:
            return self

        stack = AsyncExitStack()
        try:
            http_client = await stack.enter_async_context(
                httpx2.AsyncClient(
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=httpx2.Timeout(
                        CONNECT_TIMEOUT_SECONDS, read=READ_TIMEOUT_SECONDS
                    ),
                )
            )
            read_stream, write_stream = await stack.enter_async_context(
                streamable_http_client(self.url, http_client=http_client)
            )
            session = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()
        except (httpx2.HTTPError, OSError, RuntimeError):
            logger.exception("Failed to connect to %s MCP", self.server_name)
            await stack.aclose()
            raise

        self._stack = stack
        self.session = session
        logger.info("Connected to %s MCP", self.server_name)
        return self

    async def list_tools(self) -> List[Any]:
        """Return and cache the tools exposed by the server."""
        if self.session is None:
            raise RuntimeError("Call connect() before list_tools()")

        response = await self.session.list_tools()
        self.tools = {tool.name: tool for tool in response.tools}
        logger.debug("Discovered %d tools", len(self.tools))
        return response.tools

    async def call_tool(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Call a discovered tool using its supplied arguments."""
        if self.session is None:
            raise RuntimeError("Call connect() before call_tool()")
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}. Call list_tools() first.")

        return await self.session.call_tool(name, arguments=arguments or {})

    async def close(self) -> None:
        """Release all resources safely."""
        if self._stack is None:
            return

        stack = self._stack
        self._stack = None
        self.session = None
        self.tools = {}
        await stack.aclose()

    async def __aenter__(self) -> "BaseMCPClient":
        return await self.connect()

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()
