---
title: Context7 MCP
server_url: https://mcp.context7.com/mcp
provider: Upstash (Context7)
auth: API key (Bearer)
tool_count: 2
tool_groups: {read: 2, write: 0, both: 0, others: 0}
last_verified: 2026-10-06
related: [mcp-basics.md, github-mcp.md, decision-guide.md, data/tools-catalog.json]
---

# Context7 MCP

## 1. Overview

| Question | Short answer |
|---|---|
| What | An online service that gives programs and AI assistants **current documentation and code examples** for programming libraries |
| Who runs it | Upstash, the company behind Context7 (remote, nothing to install on the server side) |
| Address | `https://mcp.context7.com/mcp` |
| Login | Context7 API key (a free tier exists) |
| Size | 2 tools, both read-only |
| Risk | **Low.** It never changes anything. The only care needed is not putting secrets in your questions |
| Tested here | Both tools (see section 7) |

## 2. What is it?

Programmers build on **libraries**: ready-made code such as Next.js, React or pandas. Libraries change often, and their instructions (documentation) change with them.

AI assistants learn from old snapshots of the internet, so they often suggest outdated or made-up instructions. **Context7 fixes this by fetching the current documentation on demand.** You ask "how do I set up middleware in Next.js?" and it returns the relevant, up-to-date snippets from the official docs.

It works like a **librarian with two steps**:

1. "Which book do you mean?" → find the exact library.
2. "What do you want to know?" → return the right pages from that book.

## 3. Why use it?

- **Up-to-date answers:** documentation is current, and can even be for a specific version.
- **Fewer made-up instructions:** an AI assistant answers from real docs instead of memory.
- **Safe:** both tools only read, so nothing can be broken.
- **Small and cheap to describe:** the whole menu is about 1,300 AI tokens, about 27 times smaller than GitHub MCP's.
- **Same plug as GitHub MCP:** the same client code works (see [mcp-basics.md](mcp-basics.md)).

## 4. Architecture

```
  You / AI assistant
        │  "How do I check a JWT cookie in Next.js middleware?"
        ▼
┌────────────────────┐
│ Notebook (host)    │
│  Context7MCPClient │  reads CONTEXT_MCP_URL + CONTEXT_TOKEN from .env
└────────┬───────────┘
         │ HTTPS POST  (Authorization: Bearer <API key>)
         ▼
┌────────────────────────────┐
│ Context7 MCP server        │
│ mcp.context7.com/mcp       │
│                            │
│  step 1 resolve-library-id │──► "Next.js" → /vercel/next.js
│  step 2 query-docs         │──► matching doc snippets
└────────┬───────────────────┘
         │ searches
         ▼
┌────────────────────────────┐
│ Context7 documentation     │  library docs collected and indexed
│ index (private backend)    │  by Context7
└────────────────────────────┘
```

**In words:** you name a library and ask a question. Context7 first finds the library's exact ID, then searches that library's docs for your question and returns the best snippets as text.

## 5. Capabilities

| Capability | Example |
|---|---|
| Find a library by name | "Next.js" → `/vercel/next.js` and similar matches |
| Rank matches | Each match shows the number of code snippets, a source reputation (High, Medium, Low) and a quality score out of 100 |
| Pick a version | Lists available versions, e.g. `/vercel/next.js/v16.2.9` |
| Answer a docs question | Returns the relevant documentation text and code examples |
| Works for many libraries | Any library in Context7's index, both popular frameworks and smaller packages |

What it **can't** do: change anything, read your own code, or read your company's internal documents (unless they were added to Context7).

## 6. Tool categories

| Area | # tools | Read | Write | Both | Others |
|---|---|---|---|---|---|
| Documentation lookup | 2 | 2 | 0 | 0 | 0 |
| **Total** | **2** | **2** | **0** | **0** | **0** |

The server itself marks both tools as **read-only** and **not destructive**.

## 7. Individual tools

### 7.1 Read tools (2)

| Tool | What it does | Required inputs | Tested |
|---|---|---|---|
| `resolve-library-id` | Turns a library name into Context7's exact library ID, with a ranked list of matches | `libraryName`, `query` | ✅ |
| `query-docs` | Returns documentation snippets and code examples for one library and one question | `libraryId`, `query` | ✅ |

### 7.2 Write, Both, Others

None. Context7 cannot change anything.

### 7.3 What was tested in this workspace

| # | Tool | Where | What happened |
|---|---|---|---|
| 0 | *list tools* | Notebook | Returned the 2 tools with full instructions |
| 1 | `resolve-library-id` | Notebook + benchmark | `"next.js"` + a JWT-middleware question → 5 matches. Best: `/vercel/next.js` (5,143 snippets, High reputation, score 90.67, 16 versions). About 2.3 s, about 2.2 KB |
| 2 | `query-docs` | Benchmark (2026-10-05) | `/vercel/next.js` + "middleware JWT cookie" → doc snippets. About 2.6 s, about 7.1 KB |

## 8. Inputs and outputs

### Inputs

| Tool | Input | Meaning | Good example |
|---|---|---|---|
| `resolve-library-id` | `libraryName` | The library's **official** name, punctuation included | `"Next.js"`, not `"nextjs"`. `"Three.js"`, not `"threejs"` |
| | `query` | What you're trying to do. Used to rank the matches | `"set up middleware to check a JWT cookie"` |
| `query-docs` | `libraryId` | The exact ID from step 1, optionally with a version | `"/vercel/next.js"` or `"/vercel/next.js/v16.2.9"` |
| | `query` | **One** topic per call. Split multi-part questions | `"middleware JWT cookie validation"` |

⚠️ Your question text is **sent to Context7**. Never include passwords, keys or private information.

### Outputs

Plain readable text (Markdown), not JSON.

`resolve-library-id` returns a list like this (real output, shortened):

```
- Title: Next.js
- Context7-compatible library ID: /vercel/next.js
- Description: Next.js enables you to create full-stack web applications…
- Code Snippets: 5143
- Source Reputation: High
- Benchmark Score: 90.67
- Versions: v16.2.9, v16.1.6, v15.1.8, …
----------
- Title: Next.js
- Context7-compatible library ID: /websites/nextjs
…
```

`query-docs` returns documentation passages and code examples as text, ready to read or to hand to an AI.

## 9. Transport

| Item | Value |
|---|---|
| Method | Streamable HTTP (HTTPS POST, JSON-RPC messages) |
| Address | `https://mcp.context7.com/mcp` |
| Login | `Authorization: Bearer <Context7 API key>` |
| Timeouts in this client | 30 s connect, 300 s read |
| Measured speed (2026-10-05) | Connect about 0.69 s · tool list about 1.39 s · resolve about 2.3 s · query-docs about 2.6 s |
| Parallel calls | 8 calls at once took about 3.4 s in total, against about 2.8 s for one, so parallel calls work well |
| Menu size | About 5 KB, roughly 1,300 AI tokens |

Context7 calls are about **2 to 3 times slower** than simple GitHub reads, because they search a large docs index.

## 10. Example use cases

| Use case | Steps |
|---|---|
| "How do I set up middleware to check a JWT cookie in Next.js?" (tested) | `resolve-library-id("Next.js", …)` → `query-docs("/vercel/next.js", …)` |
| "Show me the v14 way to do routing, not the newest" | Resolve, pick `/vercel/next.js/v14.x` from the versions, then query |
| "Give an AI assistant real docs before it writes code" | Run both steps, then put the snippets into the AI's prompt |
| "Which library is the most trusted for X?" | `resolve-library-id` and compare reputation, snippet count and score |
| "Check whether an API call I remember still exists" | Query the docs for that function name |

## 11. Limitations

| Limitation | What it means for you |
|---|---|
| **Only libraries in its index** | If a library isn't covered, there's no answer. Your company's private docs are usually not there |
| **No accuracy guarantee** | Context7 says listed projects are community-contributed, with no guarantee of accuracy, completeness or security. Treat it as a strong hint, and check important details |
| **Always two steps** | You need the library ID first, unless you already know it (format `/org/project`) |
| **Similar names compete** | "Next.js" gave both `/vercel/next.js` and `/websites/nextjs`. Pick by reputation, snippet count and score |
| **Slower than simple lookups** | About 2.3 to 2.6 s per call |
| **Usage limits** | An API key gives higher limits, but exact numbers aren't published in the docs reviewed |
| **Text, not structured data** | Programs must pull the ID out of the text |
| **Questions leave your machine** | Never put secrets in `query` |
| **Call budget** | The tool's own instructions say: no more than 3 calls of each tool per question |
| **Closed backend** | How docs are collected and ranked isn't public |

## 12. When to use it

**Use Context7 when:**

- you or an AI assistant need **current documentation** for a programming library;
- you need docs for a **specific version**;
- you want to **reduce outdated or made-up code** from an AI;
- you want a quick "what's the right way to do X with library Y?".

**Don't use it when:**

- the task is about **GitHub repos, issues or pull requests**: use [GitHub MCP](github-mcp.md);
- you need **your own or your company's internal** documentation;
- the question isn't about a programming library (general knowledge, news, and so on);
- your question would contain **secrets**.

## 13. Programmatic usage

All examples use this workspace's client (see [mcp-basics.md](mcp-basics.md)). Run them in the notebook, or wrap them in `asyncio.run(...)`.

### Step 1: find the library ID

```python
from mcp_clients import Context7MCPClient

async with Context7MCPClient() as c7:
    await c7.list_tools()
    result = await c7.call_tool("resolve-library-id", {
        "libraryName": "Next.js",
        "query": "How do I set up middleware to check for a valid JWT cookie?",
    })
    print(result.content[0].text)    # ranked list of matching libraries
```

### Step 2: ask the docs

```python
async with Context7MCPClient() as c7:
    await c7.list_tools()
    docs = await c7.call_tool("query-docs", {
        "libraryId": "/vercel/next.js",
        "query": "middleware JWT cookie validation",
    })
    print(docs.content[0].text)
```

### Reusable helper: both steps in one function

```python
import re
from typing import Optional

from mcp_clients import Context7MCPClient

ID_PATTERN = re.compile(r"Context7-compatible library ID:\s*(\S+)")


async def ask_docs(library: str, question: str,
                   library_id: Optional[str] = None) -> str:
    """Return documentation text for one library and one question."""
    async with Context7MCPClient() as c7:
        await c7.list_tools()
        if library_id is None:
            found = await c7.call_tool("resolve-library-id",
                                       {"libraryName": library, "query": question})
            match = ID_PATTERN.search(found.content[0].text)
            if match is None:
                raise LookupError(f"No Context7 library found for {library!r}")
            library_id = match.group(1)   # first listed match
        docs = await c7.call_tool("query-docs",
                                  {"libraryId": library_id, "query": question})
        return docs.content[0].text

# text = await ask_docs("Next.js", "middleware JWT cookie validation")
# text = await ask_docs("", "routing", library_id="/vercel/next.js/v14.3.0-canary.87")
```

Notes: the helper takes the **first** match. For important work, read the list and choose by reputation, snippet count and score. If you already know the ID, pass `library_id` to skip step 1.

## 14. Decision guide

| If you want to… | Do this |
|---|---|
| get docs and don't know the ID | `resolve-library-id` → `query-docs` |
| get docs and already know the ID | `query-docs` directly |
| get docs for an older version | Resolve, pick the version ID (`/org/project/vX`), then query |
| compare candidate libraries | `resolve-library-id` only, then compare the rankings |
| ask a question about several topics | One `query-docs` call per topic |
| get nothing useful after 3 tries | Stop, rephrase, or check the library's own website |

**Before calling, ask:**

1. Is this about a programming library? If not, Context7 isn't the right tool.
2. Am I using the official library name?
3. Is my question one topic, with no secrets in it?

For choosing between Context7 and GitHub MCP, see [decision-guide.md](decision-guide.md).
