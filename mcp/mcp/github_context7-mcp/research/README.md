---
title: MCP Research Pack
last_verified: 2026-10-06
audience: Anyone, technical or not
---

# MCP Research Pack

This folder explains two online services that let software (and AI assistants) do useful work for you:

- **GitHub MCP** lets a program work on GitHub for you: read code, open issues, create repositories.
- **Context7 MCP** lets a program look up current documentation for programming libraries.

Everything here is based on what was actually run in this workspace. Where something comes from the public docs and wasn't tested here, the text says so.

## Files

| File | What's inside | Read it when |
|---|---|---|
| [mcp-basics.md](mcp-basics.md) | What "MCP" means, how a connection works, how the Python code in this workspace talks to any MCP server | Start here. Both server documents build on it |
| [github-mcp.md](github-mcp.md) | Everything about GitHub MCP | You want to work with GitHub from code or from an AI assistant |
| [context7-mcp.md](context7-mcp.md) | Everything about Context7 MCP | You want up-to-date library documentation |
| [decision-guide.md](decision-guide.md) | Which server to use, when, and how to use both together | You have a task and aren't sure which tool fits |
| [data/tools-catalog.json](data/tools-catalog.json) | Every tool from both servers: area, read/write group, required inputs, tested or not | Building tables or charts (e.g. the HTML report) |
| [data/tool-schemas-raw.json](data/tool-schemas-raw.json) | The exact tool list each server returned on 2026-10-06 | You need full technical detail for a tool |

## How the documents are organised (for reuse)

Both server documents use the **same numbered sections in the same order**, so a report generator can take "section 6" from each and put them side by side:

1. Overview
2. What is it?
3. Why use it?
4. Architecture
5. Capabilities
6. Tool categories
7. Individual tools (Read / Write / Both / Others, plus what was tested)
8. Inputs and outputs
9. Transport
10. Example use cases
11. Limitations
12. When to use it
13. Programmatic usage
14. Decision guide

Each section stands on its own, so you can copy one section somewhere else without breaking it. Each file starts with a small metadata block (`title`, `last_verified`, and so on) that tools can read.

## The four tool groups

The same four labels are used everywhere:

| Group | Plain meaning | Risk |
|---|---|---|
| **Read** | Only looks. Nothing on GitHub changes. | Safe |
| **Write** | Creates, changes or deletes something. | Real and visible. Some can't be undone |
| **Both** | Changes something by copying or combining content that already exists (it reads one thing and writes another, e.g. forking a repository). | Real and visible |
| **Others** | Special-purpose helpers that aren't plain reads or edits (security scanning, AI review requests, data for app screens). | Varies, see the tool |

The servers also label their own tools as "read-only" or not. The tool tables show that label too, so you can always see the official answer.

## Glossary

| Word | Meaning |
|---|---|
| **MCP** | *Model Context Protocol.* A shared set of rules that lets an AI app or a program use outside services through one standard plug. |
| **MCP server** | The service you connect to (here: GitHub's or Context7's). It offers a menu of *tools*. |
| **MCP client** | The code on your side that connects to a server. In this workspace: the Python classes in `mcp-learning/src/mcp_clients/`. |
| **Host** | The app the client runs inside: here, a Jupyter notebook. In daily life it could be an AI chat app or a code editor. |
| **Tool** | One action a server offers, like "search code" or "create repository". It has a name, inputs and an output. |
| **Transport** | How messages travel between client and server. Here: normal secure web requests (HTTPS). |
| **Token / API key** | A secret password-like string that proves who you are. Kept in the `.env` file, never in code. |
| **Repository (repo)** | A project folder on GitHub that keeps all versions of its files. |
| **Issue** | A to-do, bug report or question attached to a repository. |
| **Pull request (PR)** | A proposed set of changes that others can review before it's merged in. |
| **Library** | Ready-made code that programmers reuse, like Next.js or pandas. |
| **Library ID** | Context7's name for one library, written like a path: `/vercel/next.js`. |
| **Latency** | How long you wait for an answer. |

## Sources

- The live tool lists both servers returned on 2026-10-06, captured with this workspace's own client.
- The notebook `mcp-learning/github_mcp_client.ipynb` and its saved outputs.
- The benchmark data built into `mcp-dual-client-report.html` (run on 2026-10-05).
- Public docs: [github/github-mcp-server](https://github.com/github/github-mcp-server) (remote server guide) and [upstash/context7](https://github.com/upstash/context7).
