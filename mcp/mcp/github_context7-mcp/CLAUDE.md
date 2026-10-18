# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A learning/experiment workspace for talking to remote MCP servers (GitHub MCP and Context7 MCP) from Python over streamable HTTP. Not a git repository; there is no README or linter. Code lives in [mcp-learning/](mcp-learning/); [mcp-research-report.html](mcp-research-report.html) and [mcp-dual-client-report.html](mcp-dual-client-report.html) are standalone HTML reports (Plotly loaded from a CDN).

[custom-best-practices.txt](custom-best-practices.txt) holds the project's Python rules and applies to everything in `mcp-learning/`. The ones that shape the layout: source in `src/`, tests in `tests/` mirroring `src/` (unit tests in `tests/unit/`, integration tests in `tests/integration/`, fixtures only in `tests/conftest.py`), config files kept out of the source, type hints and docstrings on public code, `logging` instead of `print`, specific exceptions only, and 80%+ coverage. It also sets an 88-character line limit and the test naming pattern `test_<function>_<scenario>`. `tests/integration/` doesn't exist yet; create it there if you add network-backed tests.

## Environment and commands

- Python venv at `.venv/` (Python 3.12); `source .venv/bin/activate`. Jupyter/IPython are installed there.
- Run everything from `mcp-learning/`. Dependencies: `pip install -r requirements-dev.txt` (production pins are in `requirements.txt`).
- Tests: `python -m pytest`. Single test: `python -m pytest tests/unit/mcp_clients/test_clients.py::test_init_missing_url_raises`. [pytest.ini](mcp-learning/pytest.ini) sets `pythonpath = src`, `asyncio_mode = auto` and coverage reporting. The `module-not-measured` CoverageWarning, and the 0% shown for `mcp_clients/__init__.py`, are expected: the package is imported before coverage starts.
- Config comes from `github_context7-mcp/.env` (the notebook loads `../.env`) via `python-dotenv`: `GITHUB_MCP_URL`, `GITHUB_TOKEN`, `CONTEXT_MCP_URL`, `CONTEXT_TOKEN`. The file holds real secrets. Tests clear these variables and stub `load_dotenv` in `conftest.py`, so they never touch real credentials or the network.

## Architecture

[mcp-learning/src/mcp_clients/base_client.py](mcp-learning/src/mcp_clients/base_client.py) holds `BaseMCPClient`, which does all the work. [github_client.py](mcp-learning/src/mcp_clients/github_client.py) and [context7_client.py](mcp-learning/src/mcp_clients/context7_client.py) are subclasses that only set the class attributes `server_name`, `url_env_var` and `token_env_var`. To add another server, subclass the base and set those three attributes.

The base client:
- builds an `AsyncExitStack` holding an `httpx2.AsyncClient` (Bearer auth, 30s timeout, 300s read), the `streamable_http_client` transport and an `mcp.ClientSession`, then calls `session.initialize()`;
- is used as `async with GitHubMCPClient() as c:`; call `await c.list_tools()` **first**, because `call_tool` rejects any name not in the cached `self.tools`. `connect()` does nothing if a session is already open. `close()` clears the tool cache, so after reconnecting you must call `list_tools()` again.

[mcp-learning/github_mcp_client.ipynb](mcp-learning/github_mcp_client.ipynb) is the driver. It first does the flow inline (raw session, `tool_map`, `call_github_tool`), then uses the wrapper classes. Cells use top-level `await`, so run them in Jupyter, not as a script. It adds `src` to `sys.path`, so its working directory must be `mcp-learning/`.

## Gotchas

- The HTTP library is imported as `httpx2`, not `httpx`. Don't "fix" it without checking what is installed in `.venv`.
- The notebook's `create_repository` cell makes a **real** private repo on the authenticated GitHub account each time it runs. Confirm with the user before executing it. Its `"auto-init"` argument name is a placeholder; check the tool's `inputSchema` (the cell comment says to use the discovered schema).
- Context7 exposes two tools: `resolve-library-id` (args `libraryName`, `query`) then `query-docs` (library ID plus query).
- GitHub's documented remote endpoint is `https://api.githubcopilot.com/mcp/`.
