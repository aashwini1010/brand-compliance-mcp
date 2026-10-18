"""Async client for the Context7 MCP server."""

from mcp_clients.base_client import BaseMCPClient


class Context7MCPClient(BaseMCPClient):
    """Reusable asynchronous client for Context7 MCP."""

    server_name = "Context7"
    url_env_var = "CONTEXT_MCP_URL"
    token_env_var = "CONTEXT_TOKEN"
