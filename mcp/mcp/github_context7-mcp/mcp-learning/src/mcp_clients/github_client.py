"""Async client for the GitHub MCP server."""

from mcp_clients.base_client import BaseMCPClient


class GitHubMCPClient(BaseMCPClient):
    """Reusable asynchronous client for GitHub MCP."""

    server_name = "GitHub"
    url_env_var = "GITHUB_MCP_URL"
    token_env_var = "GITHUB_TOKEN"
