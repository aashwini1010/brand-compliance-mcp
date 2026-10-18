---
title: MCP Basics
last_verified: 2026-10-06
applies_to: [github-mcp, context7-mcp]
---

# MCP Basics

Shared background for [github-mcp.md](github-mcp.md) and [context7-mcp.md](context7-mcp.md).

## What is MCP?

**MCP (Model Context Protocol)** is a standard way for software to use outside services.

Think of it like **USB-C**. Before USB-C, every device needed its own cable. With USB-C, one plug fits many devices. In the same way, before MCP every app had to write its own connection to GitHub, to a documentation site, and so on. With MCP, any app that "speaks MCP" can connect to any MCP server the same way.

Every MCP server does the same three things:

1. **Says hello** and agrees on the rules (called *initialize*).
2. **Shows its menu** of tools when asked (*list tools*).
3. **Runs a tool** when asked, with the inputs you give it (*call tool*).

## The three roles

| Role | Everyday comparison | In this workspace |
|---|---|---|
| **Host** | The person ordering food | The Jupyter notebook `github_mcp_client.ipynb` |
| **Client** | The waiter who carries orders | `GitHubMCPClient` and `Context7MCPClient` (Python) |
| **Server** | The kitchen | GitHub's MCP server and Context7's MCP server (both online, run by those companies) |

Nothing runs locally except the client code. Both servers are remote services.

## Architecture in this workspace

```
┌──────────────────────── Your computer ───────────────────────┐
│                                                              │
│   Jupyter notebook (host)                                    │
│        │                                                     │
│        ├── GitHubMCPClient ──┐      .env file                │
│        │                     ├──►  (addresses + secret keys) │
│        └── Context7MCPClient ┘                               │
│              │   both built on one shared BaseMCPClient      │
└──────────────┼───────────────────────────────────────────────┘
               │  secure web requests (HTTPS), each with its own key
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌───────────────┐
│ GitHub MCP   │  │ Context7 MCP  │
│ server       │  │ server        │
│ (46 tools)   │  │ (2 tools)     │
└──────┬───────┘  └──────┬────────┘
       ▼                 ▼
  Your GitHub        Context7's library
  account & repos    documentation index
```

**In words:** the notebook asks a client to do something. The client reads the address and secret key from `.env`, sends a secure web request to the right server, and passes the answer back. Each client has its own key, so the GitHub key is never sent to Context7, or the other way round.

## Transport: how messages travel

Both servers use **Streamable HTTP**:

- Every message is an ordinary **HTTPS POST** request, the same technology web pages use.
- The message body follows a simple format called **JSON-RPC**: "please run tool X with these inputs, and here's a request number".
- Answers can **stream back** in pieces, which helps with slow tasks.
- The secret key travels in a header: `Authorization: Bearer <key>`.
- One connection can carry several requests at once (each has its own number).

Settings used by this workspace's client: 30 seconds to connect, up to 300 seconds to wait for an answer.

## The reusable client (programmatic basics)

All the connection logic lives in **one** class, `BaseMCPClient` (`mcp-learning/src/mcp_clients/base_client.py`). Each server gets a tiny subclass that only sets three settings:

```python
class GitHubMCPClient(BaseMCPClient):
    server_name = "GitHub"
    url_env_var = "GITHUB_MCP_URL"
    token_env_var = "GITHUB_TOKEN"
```

**Adding a new MCP server takes three lines:** make a subclass and set those three values.

### The four steps every program follows

```python
async with GitHubMCPClient() as client:          # 1. connect + say hello
    tools = await client.list_tools()            # 2. get the menu (required!)
    result = await client.call_tool(             # 3. run one tool
        "tool_name", {"input": "value"}
    )
    print(result.content[0].text)                # 4. read the answer
# leaving the "with" block closes everything safely
```

Rules to remember:

| Rule | Why |
|---|---|
| Always call `list_tools()` before `call_tool()` | The client refuses tool names it hasn't seen on the menu. This catches typos early |
| Use `async with` | It closes the connection even if something fails |
| Read answers from `result.content` | Answers come back as a list of pieces. Usually the first is text, often containing JSON |
| Check `result.is_error` | A tool can fail "politely" and return an error message instead of crashing |

### Running the code

- **In Jupyter** (as the notebook does): you can write `await` directly in a cell. The notebook's working folder must be `mcp-learning/`.
- **As a normal Python script:** wrap the code in `async def main(): ...` and call `asyncio.run(main())`. Run it from `mcp-learning/` with `PYTHONPATH=src`.

```python
import asyncio
from mcp_clients import GitHubMCPClient

async def main() -> None:
    async with GitHubMCPClient() as gh:
        await gh.list_tools()
        me = await gh.call_tool("get_me")
        print(me.content[0].text)

asyncio.run(main())
```

### Using both servers at the same time

Because each client is independent, you can ask both servers at once and wait for both answers together:

```python
import asyncio
from mcp_clients import GitHubMCPClient, Context7MCPClient

async with GitHubMCPClient() as gh, Context7MCPClient() as c7:
    await asyncio.gather(gh.list_tools(), c7.list_tools())
    me, libs = await asyncio.gather(
        gh.call_tool("get_me"),
        c7.call_tool("resolve-library-id",
                     {"libraryName": "Next.js", "query": "middleware JWT cookie"}),
    )
```

Measured on 2026-10-05: doing the full connect, menu and one-call routine on both servers took **9.4 s one after another** but **4.9 s in parallel**, about 1.9 times faster.

## Configuration

Four settings, kept in `/home/aashwini/usecase1/.env` (never in the code):

| Setting | Meaning |
|---|---|
| `GITHUB_MCP_URL` | GitHub MCP address, e.g. `https://api.githubcopilot.com/mcp/` |
| `GITHUB_TOKEN` | Your GitHub personal access token (secret) |
| `CONTEXT_MCP_URL` | Context7 MCP address, e.g. `https://mcp.context7.com/mcp` |
| `CONTEXT_TOKEN` | Your Context7 API key (secret) |

You can also pass them directly: `GitHubMCPClient(url="...", token="...")`.
