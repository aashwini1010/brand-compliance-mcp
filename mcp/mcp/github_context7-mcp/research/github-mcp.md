---
title: GitHub MCP
server_url: https://api.githubcopilot.com/mcp/
provider: GitHub
auth: Personal access token (Bearer)
tool_count: 46
tool_groups: {read: 26, write: 13, both: 4, others: 3}
last_verified: 2026-10-06
related: [mcp-basics.md, context7-mcp.md, decision-guide.md, data/tools-catalog.json]
---

# GitHub MCP

## 1. Overview

| Question | Short answer |
|---|---|
| What | An online service from GitHub that lets programs and AI assistants work with GitHub through MCP |
| Who runs it | GitHub (remote, nothing to install on the server side) |
| Address | `https://api.githubcopilot.com/mcp/` |
| Login | Your GitHub personal access token |
| Size | 46 tools with default settings (26 read, 13 write, 4 both, 3 others) |
| Risk | **High if misused.** It can create, change, merge and delete real things on your account |
| Tested here | 7 tools plus tool discovery (see section 7) |

## 2. What is it?

GitHub is where programmers store and share code. Normally a person clicks through the GitHub website to read files, report bugs or approve changes.

**GitHub MCP lets a program do those same clicks for you.** You send it a request like "show me the open bugs in this project" or "create a new repository called my-repo". It does the work on GitHub and sends back the result.

It acts **as you**: it can only see and change what your token is allowed to.

## 3. Why use it?

- **Automate repetitive GitHub work:** create repos, add files, open issues, without clicking.
- **Let an AI assistant help with GitHub:** "summarise the open pull requests" becomes possible because the assistant can actually read them.
- **One standard plug:** the same client code that talks to Context7 also talks to GitHub (see [mcp-basics.md](mcp-basics.md)).
- **Self-describing:** the server publishes its own menu, with the inputs each tool needs, so programs can discover what's possible.
- **No server to host:** GitHub runs it. You only need the client and a token.

## 4. Architecture

```
  You / AI assistant
        │  "create a repo called my-repo"
        ▼
┌───────────────────┐
│ Notebook (host)   │
│  GitHubMCPClient  │  reads GITHUB_MCP_URL + GITHUB_TOKEN from .env
└────────┬──────────┘
         │ HTTPS POST  (Authorization: Bearer <your token>)
         ▼
┌───────────────────────────────┐
│ GitHub MCP server             │  checks the token, picks the tool
│ api.githubcopilot.com/mcp/    │
└────────┬──────────────────────┘
         │ normal GitHub API calls, as you
         ▼
┌───────────────────────────────┐
│ GitHub: your repos, issues,   │
│ pull requests, releases …     │
└───────────────────────────────┘
         │ result travels back the same way
         ▼
  {"id": "1407054450", "url": "https://github.com/aashwini1010/my-repo"}
```

**In words:** your request goes to GitHub's MCP server, which turns it into ordinary GitHub actions performed with your permissions. The answer comes back as text.

## 5. Capabilities

What it can do, in plain terms:

| Capability | Examples |
|---|---|
| Know who you are | Your profile, your teams |
| Find things | Search all of GitHub for code, repositories, users, issues, pull requests, commits |
| Read projects | Read files and folders, list branches, commits, tags and releases |
| Manage repositories | Create a repo, fork (copy) one, add, change or delete files, push several files at once |
| Manage issues | Create, update or close issues, comment, react, organise sub-issues |
| Manage pull requests | Open, edit, review, comment, merge, update with the latest changes, ask Copilot to review |
| Security check | Scan text or files for leaked secrets such as passwords or API keys |

**Turned off by default** (available by changing settings, not tested here): GitHub Actions, code security alerts, Dependabot, discussions, gists, notifications, projects, and more. These are called *toolsets*; see section 11.

## 6. Tool categories

Tools grouped by what part of GitHub they touch:

| Area | # tools | Read | Write | Both | Others |
|---|---|---|---|---|---|
| Account & people | 5 | 5 | 0 | 0 | 0 |
| Repositories & files | 8 | 3 | 4 | 1 | 0 |
| Branches, commits, tags & releases | 10 | 9 | 0 | 1 | 0 |
| Issues | 10 | 6 | 4 | 0 | 0 |
| Pull requests | 11 | 3 | 5 | 2 | 1 |
| Security | 1 | 0 | 0 | 0 | 1 |
| App helpers | 1 | 0 | 0 | 0 | 1 |
| **Total** | **46** | **26** | **13** | **4** | **3** |

Group meanings: **Read** only looks · **Write** creates, changes or deletes · **Both** copies or combines existing content into something new · **Others** are special helpers. The server's own label is shown in each table below ("Server says read-only").

## 7. Individual tools

✅ = tested in this workspace. Required inputs are listed; most tools also take optional ones (see [data/tools-catalog.json](data/tools-catalog.json)).

### 7.1 Read tools (26): safe, nothing changes

| Tool | What it does | Required inputs | Area | Tested |
|---|---|---|---|---|
| `get_me` | Shows your own GitHub profile | none | Account & people | ✅ |
| `get_teams` | Lists the teams you belong to | none | Account & people | |
| `get_team_members` | Lists the people in one team | `org`, `team_slug` | Account & people | |
| `search_users` | Finds GitHub users by name or username | `query` | Account & people | ✅ |
| `list_repository_collaborators` | Lists who has access to a repo | `owner`, `repo` | Account & people | |
| `get_file_contents` | Reads a file, or lists a folder | `owner`, `repo` (+ `path`) | Repositories & files | ✅ |
| `search_repositories` | Finds repositories by name, topic and so on | `query` | Repositories & files | ✅ |
| `search_code` | Searches code across **all** of GitHub | `query` | Repositories & files | ✅ |
| `list_branches` | Lists a repo's branches | `owner`, `repo` | Branches… | |
| `get_commit` | Details of one saved change (commit) | `owner`, `repo`, `sha` | Branches… | |
| `list_commits` | History of changes on a branch | `owner`, `repo` | Branches… | |
| `search_commits` | Searches commit messages and authors | `query` | Branches… | |
| `get_tag` | Details of one version tag | `owner`, `repo`, `tag` | Branches… | |
| `list_tags` | Lists version tags | `owner`, `repo` | Branches… | |
| `get_latest_release` | The newest published release | `owner`, `repo` | Branches… | |
| `get_release_by_tag` | One release, by its tag | `owner`, `repo`, `tag` | Branches… | |
| `list_releases` | All releases | `owner`, `repo` | Branches… | |
| `issue_read` | One issue's details, comments, sub-issues, parent or labels | `method`, `owner`, `repo`, `issue_number` | Issues | |
| `list_issues` | Lists issues in a repo, with filters | `owner`, `repo` | Issues | |
| `search_issues` | Finds issues by meaning ("login fails after reset") | `query` | Issues | |
| `get_label` | One label's details | `owner`, `repo`, `name` | Issues | |
| `list_issue_types` | Which issue types exist (bug, task…) | `owner` | Issues | |
| `list_issue_fields` | Which custom issue fields exist | `owner` | Issues | |
| `list_pull_requests` | Lists pull requests in a repo | `owner`, `repo` | Pull requests | |
| `pull_request_read` | One PR's details, changes, files, reviews, comments or checks | `method`, `owner`, `repo`, `pullNumber` | Pull requests | |
| `search_pull_requests` | Finds pull requests | `query` | Pull requests | |

### 7.2 Write tools (13): these change real things

| Tool | What it does | Required inputs | Area | Tested |
|---|---|---|---|---|
| `create_repository` | Creates a new repository | `name` | Repositories & files | ✅ |
| `create_or_update_file` | Adds one file, or changes it (changing needs the file's current `sha`) | `owner`, `repo`, `path`, `content`, `message`, `branch` | Repositories & files | ✅ |
| `push_files` | Saves several files in one change | `owner`, `repo`, `branch`, `files`, `message` | Repositories & files | |
| `delete_file` ⚠️ | Deletes a file. **The server marks this as destructive** | `owner`, `repo`, `path`, `message`, `branch` | Repositories & files | |
| `issue_write` | Creates or updates an issue (`method` = `create` / `update`) | `method`, `owner`, `repo` | Issues | |
| `add_issue_comment` | Comments or reacts on an issue or PR | `owner`, `repo`, `issue_number` | Issues | |
| `update_issue_comment` | Edits an existing comment | `owner`, `repo`, `comment_id`, `body` | Issues | |
| `sub_issue_write` | Adds, removes or reorders sub-issues | `method`, `owner`, `repo`, `issue_number`, `sub_issue_id` | Issues | |
| `create_pull_request` | Opens a pull request | `owner`, `repo`, `title`, `head`, `base` | Pull requests | |
| `update_pull_request` | Edits a PR's title, text, state or reviewers | `owner`, `repo`, `pullNumber` | Pull requests | |
| `pull_request_review_write` | Starts, submits or deletes a review; resolves comment threads | `method`, `owner`, `repo`, `pullNumber` | Pull requests | |
| `add_comment_to_pending_review` | Adds a line comment to your unfinished review | `owner`, `repo`, `pullNumber`, `path`, `body`, `subjectType` | Pull requests | |
| `add_reply_to_pull_request_comment` | Replies or reacts to a PR comment | `owner`, `repo`, `commentId` | Pull requests | |

### 7.3 Both (4): copy or combine existing content

The server marks these as **not** read-only. They change GitHub, but their job is to take something that exists and produce something new from it.

| Tool | What it does | Required inputs | Area | Tested |
|---|---|---|---|---|
| `fork_repository` | Copies someone's repository into your account | `owner`, `repo` | Repositories & files | |
| `create_branch` | Makes a new branch, copied from an existing one | `owner`, `repo`, `branch` | Branches… | |
| `update_pull_request_branch` | Brings a PR up to date with the latest base branch | `owner`, `repo`, `pullNumber` | Pull requests | |
| `merge_pull_request` | Merges a PR's changes into the main code. **Hard to undo** | `owner`, `repo`, `pullNumber` | Pull requests | |

### 7.4 Others (3): special-purpose helpers

| Tool | What it does | Server says read-only | Required inputs | Tested |
|---|---|---|---|---|
| `run_secret_scanning` | Checks text or files for leaked passwords, keys or tokens. Nothing is saved to the repo | Yes | `files`, `owner`, `repo` | |
| `request_copilot_review` | Asks GitHub's AI (Copilot) to review a pull request | No | `owner`, `repo`, `pullNumber` | |
| `ui_get` | Gets pick-list data (labels, assignees, branches…) for apps that draw screens | Yes | `method`, `owner` | |

### 7.5 What was tested in this workspace

| # | Tool | Group | Where | What happened |
|---|---|---|---|---|
| 0 | *list tools* | — | Notebook | Returned 46 tools with descriptions |
| 1 | `create_repository` | Write | Notebook | Created private repo `aashwini1010/my-repo` |
| 2 | `create_or_update_file` | Write | Notebook | Added `hello.py` to `main` and returned the new commit |
| 3 | `get_file_contents` | Read | Notebook | Read `hello.py` back: `print('Hello from GitHub MCP!')` |
| 4 | `search_users` | Read | Notebook | Found user `aashwini1010` (1 result) |
| 5 | `search_code` | Read | Notebook | "hello.py" matched **163,328** files across all of GitHub |
| 6 | `get_me` | Read | Benchmark (2026-10-05) | About 0.85 s, about 500-byte answer |
| 7 | `search_repositories` | Read | Benchmark (2026-10-05) | About 1.2 s for 5 results, about 2.7 KB |

Not tested: the remaining 39 tools, including every issue, pull request, merge and delete tool.

## 8. Inputs and outputs

### Inputs

- Inputs are a simple set of named values (a JSON object): `{"owner": "aashwini1010", "repo": "my-repo", "path": "hello.py"}`.
- Most tools need **`owner`** (user or organisation) and **`repo`** (repository name).
- Some tools combine several actions in one, chosen with **`method`**. For example `pull_request_read` with `method: "get_diff"`.
- Long lists are split into pages: `page` and `perPage`, or `after` for issues.
- ⚠️ **Name styles are mixed.** Some tools use `pullNumber`, others use `issue_number` or `comment_id`. Copy names exactly from the tool's schema.
- ⚠️ **Wrong input names are silently ignored.** The notebook sent `"auto-init"` instead of the real name `autoInit`. The repo was still created and no error was shown. The misspelled option was most likely just ignored.

### Outputs

The answer is a list of *content* pieces:

| Piece | Looks like | Example |
|---|---|---|
| Text containing JSON | A string you turn into data with `json.loads` | `{"id":"1407054450","url":"https://github.com/aashwini1010/my-repo"}` |
| Embedded file | The file's text plus its address | `get_file_contents` returned a note *and* the file text `print('Hello from GitHub MCP!')` |
| Error flag | `is_error=True` with a message | e.g. wrong repo name or missing permission |

`structured_content` came back empty in every test, so **read the text and parse the JSON yourself**.

## 9. Transport

| Item | Value |
|---|---|
| Method | Streamable HTTP (HTTPS POST, JSON-RPC messages) |
| Address | `https://api.githubcopilot.com/mcp/` |
| Login | `Authorization: Bearer <GitHub personal access token>` |
| Timeouts in this client | 30 s connect, 300 s read |
| Measured speed (2026-10-05) | Connect about 0.94 s · tool list about 2.45 s · simple read about 0.85 s · search about 1.2 s |
| Parallel calls | 4 calls at once took about the same time as 1 (about 1.05 s). 8 at once slowed to about 2.6 s |
| Menu size | About 137 KB, roughly 34,000 AI "tokens" just to describe all 46 tools |

Optional settings from GitHub's docs (**not tested here**). They are added to the address:

| Address | Effect |
|---|---|
| `…/mcp/readonly` | Only read tools are offered (safest) |
| `…/mcp/x/repos` | Only one toolset (here: repos) |
| `…/mcp/x/all` | Every toolset |

The same effects are available through headers (`X-MCP-Toolsets`, `X-MCP-Tools`, `X-MCP-Readonly`). This workspace's client currently sends only the login header, so the address form is the easy option: just change `GITHUB_MCP_URL`.

## 10. Example use cases

| Use case | Tools | Group |
|---|---|---|
| "Create a project and put a starter file in it" | `create_repository` → `create_or_update_file` | Write (tested) |
| "Show me what's in this file on GitHub" | `get_file_contents` | Read (tested) |
| "Find example code that uses X" | `search_code` (add `repo:` or `language:` to narrow it) | Read (tested) |
| "Who is this GitHub user?" | `search_users` | Read (tested) |
| "List open bugs and summarise them" | `list_issues` → `issue_read` | Read |
| "Report a bug" | `issue_write` (`method: create`) | Write |
| "Summarise this pull request's changes" | `pull_request_read` (`get`, `get_diff`, `get_files`) | Read |
| "Review and approve a PR" | `pull_request_review_write` → `add_comment_to_pending_review` → submit | Write |
| "What changed in the latest release?" | `get_latest_release`, `list_commits` | Read |
| "Did I leak a password in this text?" | `run_secret_scanning` | Others |
| "Copy an open-source project to experiment with" | `fork_repository` | Both |

## 11. Limitations

| Limitation | What it means for you |
|---|---|
| **Real changes, some permanent** | Write and Both tools act on your real account. `delete_file` and `merge_pull_request` are hard to undo. Running the notebook's `create_repository` cell again creates another real repo |
| **Only as powerful as your token** | It can't see private repos or organisations your token can't access. Too-broad tokens are a risk |
| **Big menu** | 46 tools cost about 34,000 tokens of an AI's attention before any work starts. Limit toolsets when you only need a few |
| **Text answers, not tidy data** | You must parse the JSON text yourself |
| **Inputs are easy to get wrong** | Mixed name styles. Misspelled names are ignored without a warning |
| **Search is all of GitHub** | `search_code` for "hello.py" gave 163,328 hits. Always narrow with `repo:`, `user:` or `language:` |
| **Remote GitHub only** | It doesn't touch files on your computer or your local git |
| **Many features off by default** | Actions, security alerts, discussions and others need extra toolsets |
| **GitHub's usage limits apply** | Too many calls too quickly will be slowed down or refused for a while |
| **Lockdown mode is not a security wall** | GitHub calls it "best-effort", so don't rely on it to protect secrets |
| **Menu can change** | GitHub adds and renames tools. Always discover tools with `list_tools()` rather than hard-coding them |

## 12. When to use it

**Use GitHub MCP when:**

- the task is about **GitHub content**: repos, files on GitHub, issues, pull requests, releases;
- you want an **AI assistant** to read or act on GitHub for you;
- you want to **automate** a repeated GitHub routine from Python.

**Don't use it when:**

- you need **library documentation**: use [Context7](context7-mcp.md);
- the files are **only on your computer**: use local file tools or git;
- you only need **read access** but have a full-power token: switch to the `/readonly` address first;
- a one-off click on the website is faster than writing code.

## 13. Programmatic usage

All examples use this workspace's client (see [mcp-basics.md](mcp-basics.md)). Run them in the notebook, or wrap them in `asyncio.run(...)`.

### Read: who am I?

```python
import json
from mcp_clients import GitHubMCPClient

async with GitHubMCPClient() as gh:
    await gh.list_tools()
    result = await gh.call_tool("get_me")
    me = json.loads(result.content[0].text)
    print(me["login"])
```

### Read: get a file's text

```python
async with GitHubMCPClient() as gh:
    await gh.list_tools()
    result = await gh.call_tool("get_file_contents", {
        "owner": "aashwini1010", "repo": "my-repo", "path": "hello.py",
    })
    print(result.content[0].text)           # "successfully downloaded text file (SHA: …)"
    print(result.content[1].resource.text)  # the file itself
```

### Read: focused code search

```python
async with GitHubMCPClient() as gh:
    await gh.list_tools()
    result = await gh.call_tool("search_code", {
        "query": "ClientSession repo:modelcontextprotocol/python-sdk", "perPage": 5,
    })
    hits = json.loads(result.content[0].text)
    for item in hits["items"]:
        print(item["repository"], item["path"])
```

### Write: create a repo, then add a file (makes real changes!)

```python
async with GitHubMCPClient() as gh:
    await gh.list_tools()
    repo = await gh.call_tool("create_repository", {
        "name": "my-repo", "description": "Created via MCP",
        "private": True, "autoInit": True,      # note: autoInit, not "auto-init"
    })
    if repo.is_error:
        raise RuntimeError(repo.content[0].text)

    await gh.call_tool("create_or_update_file", {
        "owner": "aashwini1010", "repo": "my-repo", "branch": "main",
        "path": "hello.py", "message": "Add hello.py",
        "content": "print('Hello from GitHub MCP!')",
    })
```

### Check a tool's exact inputs before calling it

```python
async with GitHubMCPClient() as gh:
    await gh.list_tools()
    schema = gh.tools["create_repository"].input_schema   # snake_case in mcp 2.2
    print(schema["required"], list(schema["properties"]))
    print(gh.tools["delete_file"].annotations)            # read_only_hint, destructive_hint
```

### Safety pattern: only allow read tools

```python
async with GitHubMCPClient() as gh:
    await gh.list_tools()
    safe = {name for name, t in gh.tools.items()
            if t.annotations and t.annotations.read_only_hint}
    # 28 tools on 2026-10-06 (the 26 Read tools plus run_secret_scanning and ui_get)
```

## 14. Decision guide

| If you want to… | Use | Group |
|---|---|---|
| know your own account | `get_me` | Read |
| find a repository | `search_repositories` | Read |
| find code or a function | `search_code`, narrowed with `repo:` | Read |
| read a file on GitHub | `get_file_contents` | Read |
| see project history | `list_commits` → `get_commit` | Read |
| see open bugs | `list_issues` (one repo) or `search_issues` (by meaning) | Read |
| understand a pull request | `pull_request_read` | Read |
| start a new project | `create_repository` | Write |
| add or change one file | `create_or_update_file` | Write |
| add many files at once | `push_files` | Write |
| report or update a bug | `issue_write` | Write |
| propose changes | `create_branch` → `push_files` → `create_pull_request` | Both → Write |
| accept changes | `merge_pull_request` | Both |
| check for leaked secrets | `run_secret_scanning` | Others |

**Before any Write or Both tool, ask:**

1. Is this the right account and repo?
2. Can it be undone? (Delete and merge: assume no.)
3. Would read-only mode be enough?
4. Did I check the exact input names with `input_schema`?

For choosing between GitHub MCP and Context7, see [decision-guide.md](decision-guide.md).
