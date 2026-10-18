"""Run Claude Code from Python to brand one HTML file with one brand guide.

Usage (from the project folder, with ./scripts/start-mcp-server.sh already running):

    myenv/bin/python scripts/run_claude_brand.py <guide.md> <artifact.html>

Each argument is a path inside the project folder, or just a file name that exists in
eval/artifacts/, inputs/ or the project folder.
"""

import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

SERVER_NAME = "brand-compliance"
SERVER_URL = "http://127.0.0.1:8010/sse"
SEARCH_DIRS = ("eval/artifacts", "inputs", ".")
ALLOWED_TOOLS = [
    f"mcp__{SERVER_NAME}__classify_artifact",
    f"mcp__{SERVER_NAME}__apply_brand",
    f"mcp__{SERVER_NAME}__get_report",
    f"mcp__{SERVER_NAME}__extract_rules",
    f"mcp__{SERVER_NAME}__list_plugins",
]


def read_token(env_file: Path = Path(".env")) -> str:
    """Return the server's bearer token from the .env file."""
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            if line.startswith("BRAND_MCP_AUTH_TOKEN="):
                return line.split("=", 1)[1].strip()
    raise SystemExit("BRAND_MCP_AUTH_TOKEN not found in .env: start the server first.")


def resolve(name: str) -> str:
    """Turn a path or a bare file name into a path relative to the project folder."""
    if Path(name).is_file():
        return name
    matches = [str(Path(d) / name) for d in SEARCH_DIRS if (Path(d) / name).is_file()]
    if not matches:
        raise SystemExit(f"File not found: {name}")
    if len(matches) > 1:
        raise SystemExit(f"{name} is ambiguous, give the full path: {matches}")
    return matches[0]


async def run(guide: str, artifact: str) -> None:
    """Ask Claude Code to classify, brand and summarise, printing what it says."""
    options = ClaudeAgentOptions(
        mcp_servers={
            SERVER_NAME: {
                "type": "sse",
                "url": SERVER_URL,
                "headers": {"Authorization": f"Bearer {read_token()}"},
            }
        },
        allowed_tools=ALLOWED_TOOLS,
    )
    prompt = (
        f"Use the {SERVER_NAME} tools. Classify {artifact}, apply the guide {guide} "
        "to it, then read the report and summarise what changed, what was not "
        "applied and where the output folder is."
    )
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"\n[done] error={message.is_error} cost=${message.total_cost_usd}")


def main() -> None:
    """Read the two arguments, resolve them and run."""
    if len(sys.argv) != 3:
        raise SystemExit("Usage: run_claude_brand.py <guide.md> <artifact.html>")
    asyncio.run(run(resolve(sys.argv[1]), resolve(sys.argv[2])))


if __name__ == "__main__":
    main()
