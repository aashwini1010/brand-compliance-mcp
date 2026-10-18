---
title: MCP Decision Guide
last_verified: 2026-10-06
covers: [github-mcp, context7-mcp]
related: [mcp-basics.md, github-mcp.md, context7-mcp.md]
---

# Decision Guide: GitHub MCP or Context7 MCP?

## 1. The one-line rule

> **Working on GitHub itself → GitHub MCP.**
> **Needing to know how a programming library works → Context7 MCP.**
> **Writing code with a library and saving it to GitHub → both, Context7 first.**

## 2. Quick decision flow

```
What do you need?
│
├─ Something ON GitHub (repo, file, issue, pull request, release, user)?
│     └─► GitHub MCP
│           ├─ Only looking?            → Read tools (safe)
│           ├─ Copying or merging?      → Both tools (real change; merge is hard to undo)
│           ├─ Creating or changing?    → Write tools (real change, confirm first)
│           └─ Secret scan / AI review? → Others
│
├─ HOW TO USE a programming library (current docs, examples, versions)?
│     └─► Context7 MCP: resolve-library-id → query-docs   (always safe)
│
├─ Both (learn the right way, then save code to GitHub)?
│     └─► Context7 first, then GitHub MCP
│
└─ None of these (local files, private company docs, general questions)?
      └─► Neither. Use local tools or other sources
```

## 3. Side-by-side comparison

| | GitHub MCP | Context7 MCP |
|---|---|---|
| **Main job** | Do things on GitHub | Look up library documentation |
| **Everyday comparison** | A remote assistant with your GitHub login | A librarian for programming manuals |
| **Number of tools** | 46 | 2 |
| **Read / Write / Both / Others** | 26 / 13 / 4 / 3 | 2 / 0 / 0 / 0 |
| **Can it break things?** | Yes: create, change, merge, delete | No, read-only |
| **Login** | GitHub personal access token | Context7 API key |
| **Typical inputs** | `owner`, `repo`, numbers, filters | Library name or ID + a question |
| **Answer format** | Text containing JSON | Readable text (Markdown) |
| **Typical speed** (measured) | 0.85 to 1.2 s per call | 2.3 to 2.6 s per call |
| **Menu size for an AI** | About 34,000 tokens | About 1,300 tokens |
| **Tested here** | 7 tools + discovery | 2 tools + discovery |
| **Biggest risk** | Unintended real changes | Outdated or wrong community docs; secrets in questions |

## 4. Task → tool lookup

| I want to… | Server | Tool(s) | Group |
|---|---|---|---|
| see my GitHub profile | GitHub | `get_me` | Read |
| read a file stored on GitHub | GitHub | `get_file_contents` | Read |
| find example code on GitHub | GitHub | `search_code` (narrow with `repo:`) | Read |
| find a project or repository | GitHub | `search_repositories` | Read |
| list or understand bugs | GitHub | `list_issues`, `issue_read`, `search_issues` | Read |
| understand a pull request | GitHub | `pull_request_read` | Read |
| create a repository | GitHub | `create_repository` | Write |
| add or edit a file | GitHub | `create_or_update_file`, `push_files` | Write |
| report a bug | GitHub | `issue_write` | Write |
| propose a change | GitHub | `create_branch` → `push_files` → `create_pull_request` | Both → Write |
| accept a change | GitHub | `merge_pull_request` | Both |
| check text for leaked secrets | GitHub | `run_secret_scanning` | Others |
| learn how to do X with library Y | Context7 | `resolve-library-id` → `query-docs` | Read |
| use docs for an older library version | Context7 | `query-docs` with `/org/project/version` | Read |
| choose between similar libraries | Context7 | `resolve-library-id` (compare scores) | Read |

## 5. Using both together

A common, useful pattern: **learn the correct way, then save the result.**

```
1. Context7  resolve-library-id   "Next.js"           → /vercel/next.js
2. Context7  query-docs           "middleware JWT"     → current docs + examples
3. (you or an AI write the code using those docs)
4. GitHub    create_branch        "add-jwt-middleware"
5. GitHub    create_or_update_file  middleware.ts
6. GitHub    create_pull_request  "Add JWT middleware" → ready for review
```

Steps 1 and 2 are safe. Steps 4 to 6 make real changes, so confirm before running them.

```python
from mcp_clients import Context7MCPClient, GitHubMCPClient

async with Context7MCPClient() as c7, GitHubMCPClient() as gh:
    await c7.list_tools()
    await gh.list_tools()

    docs = await c7.call_tool("query-docs", {
        "libraryId": "/vercel/next.js", "query": "middleware JWT cookie validation",
    })
    # … write code using docs.content[0].text …

    # Real changes below: confirm before running.
    await gh.call_tool("create_branch", {
        "owner": "aashwini1010", "repo": "my-repo", "branch": "add-jwt-middleware",
    })
```

When the two lookups don't depend on each other, run them at the same time with `asyncio.gather`. On the full routine that was about 1.9 times faster in testing (see [mcp-basics.md](mcp-basics.md)).

## 6. Safety checklist by group

| Group | Before calling |
|---|---|
| **Read** (both servers) | Nothing special. For Context7: no secrets in the question |
| **Write** (GitHub) | Right account and repo? Exact input names checked? Someone has agreed? |
| **Both** (GitHub) | Same as Write. For `merge_pull_request`: assume it can't be undone |
| **Others** (GitHub) | Read the tool's description. Behaviour differs per tool |
| **Exploring only** | Point `GITHUB_MCP_URL` at `https://api.githubcopilot.com/mcp/readonly` (per GitHub's docs, not tested here) |

## 7. When to use neither

| Situation | Better choice |
|---|---|
| Files only on your computer | Local file tools, local git |
| Your company's private documentation | Internal wiki or search |
| General questions, news, non-programming topics | A web search or general assistant |
| One quick click on github.com | Just use the website |
