# MCP tools reference

How to connect to the Brand Compliance MCP server and what each tool accepts and returns.

## Connecting

The server speaks MCP over **HTTP with Server-Sent Events (SSE)**.

| | |
|---|---|
| Endpoint | `http://127.0.0.1:8000/sse` (host, port and transport come from `config/settings.toml`; with `transport = "http"` the endpoint is `/mcp`) |
| Authentication | `Authorization: Bearer <token>`: the value of `BRAND_MCP_AUTH_TOKEN` |
| Start | `PYTHONPATH=src python -m brand_compliance.server` |

The server **refuses to start** without a token of at least 16 characters (it prints a command to generate
one) and never listens beyond localhost without one. Requests with a missing or wrong token get `401`; a wrong
`Host` header gets `421` and a wrong `Origin` header gets `403`.

Any MCP client that supports SSE with custom headers can connect. A Python example using the client that ships
with FastMCP:

```python
import asyncio
from fastmcp import Client


async def main() -> None:
    async with Client("http://127.0.0.1:8000/sse", auth="<your token>") as client:
        result = await client.call_tool(
            "apply_brand",
            {
                "guide_path": "myridius-brand-guide.md",
                "artifact_path": "eval/artifacts/mcp-servers-report-simple-v2.html",
                "output_dir": "output",
            },
        )
        print(result.data.message, result.data.output_dir)


asyncio.run(main())
```

**Paths are paths on the server's machine**, and must lie inside the allowed folders
(`[paths]` in `config/settings.toml`; default: the working directory for inputs, `output/` for results).
Uploading file contents over the connection is not supported.

### Connecting Claude Code

Claude Code connects by URL and does not start an SSE server itself, so start the server first.
`scripts/start-mcp-server.sh` creates a token in `.env` (gitignored) on first run and starts the server
with it:

```bash
./scripts/start-mcp-server.sh            # leave this running
```

Register it once, reading the same token from `.env`:

```bash
TOKEN=$(sed -n 's/^BRAND_MCP_AUTH_TOKEN=//p' .env)
claude mcp add --transport sse --scope user brand-compliance http://127.0.0.1:8000/sse \
  --header "Authorization: Bearer $TOKEN"
claude mcp list                          # brand-compliance ... ✔ Connected
```

Start a new Claude Code session; `/mcp` lists `brand-compliance` and its five tools. Put input files
inside the project folder (for example `inputs/`, which is gitignored) and give Claude their paths.
If `.env` is deleted, the script makes a new token: run `claude mcp remove brand-compliance -s user`
and register again.

### Driving Claude Code from Python

`scripts/run_claude_brand.py` uses the Claude Agent SDK (`claude-agent-sdk`, pinned in
`requirements-dev.txt`) to start Claude Code, connect it to this server and ask it to classify, brand
and summarise one artifact. It reads the token from `.env`, so nothing is registered with
`claude mcp add`.

```bash
./scripts/start-mcp-server.sh                       # terminal 1, leave running
myenv/bin/python scripts/run_claude_brand.py myridius-brand-guide.md mcp-servers-report-simple-v2.html
```

Each argument is a path inside the project folder, or a bare file name that the script finds in
`eval/artifacts/`, `inputs/` or the project folder. Only the three needed tools are allowed.

## Tools

### `apply_brand`: apply a guide to one artifact
Writes a new run folder; **never modifies the inputs**.

| Input | Type | Notes |
|---|---|---|
| `guide_path` * | string | The brand guide (Markdown today) |
| `artifact_path` * | string | An `.html` / `.htm` file |
| `output_dir` | string | Default `output`. Must be an allowed output folder; the run folder `run-<UTC time>-<6 hex>` is created inside it |
| `artifact_type` | `"static"` \| `"email"` | Omit to detect it. Forcing it is recorded in the report |

Returns a `RunSummary`:

| Field | Meaning |
|---|---|
| `run_id`, `output_dir` | Where the results are |
| `status` | `completed`, or `failed_verification` (then `branded.html` is **withheld**; the reports are still written) |
| `artifact_type` | `static` or `email` |
| `files` | Map of file name → path (`branded.html`, `report.md`, `report.json`, `guide_rules.json`) |
| `rule_counts` | Rules per final status (below) |
| `change_count` | Edits made |
| `conflict_count` | **Unresolved** contradictions in the guide |
| `checks` | Each check's result: `contrast`, `forbidden-color`, `structure`, `assets`, `original-intact`, `idempotence` |
| `message` | One-line summary |

### `extract_rules`: how a guide is read
Read-only. Does not need an artifact.

| Input | Type | Notes |
|---|---|---|
| `guide_path` * | string | |
| `status` | string | Only rules with this status, e.g. `could_not_interpret` |
| `limit` | integer | 1–1000, default 500; `truncated` is set if more matched |

Returns `guide`, `counts` (per status), `total`, `returned`, `truncated`, `rules` and `conflicts`. Each rule has
`id`, `status`, `category`, `role`, `property`, `value`, `scope`, `severity`, `guide_line`, `heading`, `reason`, `notes`.
Here `pending` means *understood*; whether it applies depends on the artifact it is later used with.

### `classify_artifact`: static page or email?
Read-only. Returns `artifact_type`, `confidence` (0–1), `ambiguous` and `signals` (the evidence, each
prefixed `email +n` or `static +n`). An **ambiguous** verdict means the evidence was close: the safer email
handling is chosen, and `apply_brand` records that in its report.

### `get_report`: fetch a saved report
Read-only.

| Input | Type | Notes |
|---|---|---|
| `run_id` * | string | Must match `run-YYYYMMDD-HHMMSS-xxxxxx` (anything else is rejected, which also rules out path tricks) |
| `format` | `"markdown"` \| `"json"` | Default `markdown` |

Returns `run_id`, `format` and `content`. The same Markdown report is available as the resource
**`report://{run_id}`**.

### `list_plugins`: what is loaded
Read-only. Returns `plugins`: the names of every loaded guide reader, rule finder, artifact handler, applier,
writer, verifier and reporter, grouped by interface (including any installed through entry points).

## Rule statuses

| Status | Meaning |
|---|---|
| `applied` | Understood and acted on, or enforced by a check (the reason carries the evidence) |
| `understood_not_applicable` | Understood but could not be applied here (the reason says why) |
| `could_not_interpret` | Subjective, vague or unsupported wording; nothing was guessed |
| `conflict_unresolved` | The guide contradicts itself; neither side was applied |
| `reference` | A definition (palette token, variable) used by other rules |
| `pending` | Only from `extract_rules`: understood, not yet matched to an artifact |

## Errors

Errors reach the client as `[CODE] message`. Unexpected failures are reported only as
`[INTERNAL_ERROR]`; the details stay in the server log, so no stack trace, path or content is exposed.

| Code | When |
|---|---|
| `INVALID_INPUT` | A value failed validation: missing file, wrong file type, too large, bad `run_id`, unknown `status`, run folder already exists, no such saved run |
| `PATH_NOT_ALLOWED` | A path is outside the allowed folders, or an output folder would contain an input file |
| `UNSUPPORTED_FORMAT` | No reader/handler/writer exists for the input (for example a `.txt` guide) |
| `PARSE_FAILED` | An input could not be parsed (for example an artifact that is not valid UTF-8) |
| `INTERNAL_ERROR` | Anything unexpected |

(`CONFIGURATION_ERROR` is raised only at server start-up, for example a missing token.)

## Output files in detail

- **`report.md`** answers, in order: what changed (every edit with element, before, after and the guideline behind it); what was understood but not applied; what could not be interpreted; where the guide contradicts itself; which edits were rolled back and why; which text elements matched no role.
- **`report.json`** has `schema_version` and the full run (rules, changes, skips, conflicts, checks, notes).
- **`guide_rules.json`** lists every rule with its source line in the guide.
- Element locations are XPaths in the original document, for example `/html/body/main/section[1]/h2`.
