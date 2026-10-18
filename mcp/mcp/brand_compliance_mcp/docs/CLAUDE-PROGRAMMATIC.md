# Driving Claude Code from Python (`scripts/run_claude_brand.py`)

## 1. What
A small Python script that starts Claude Code through the **Claude Agent SDK**, connects it to this
project's MCP server (`brand-compliance`), and asks it to brand one HTML file with one brand guide.
You give it two inputs, a guide (`.md`) and an artifact (`.html`); it prints a summary of the run.
The branded copy and reports are written by the server to `output/<run_id>/`.

## 2. Why
- Claude Code normally runs in a chat. A script lets you run the same workflow without typing
  prompts: repeatable, easy to loop over many files, usable from other programs.
- The prompt is fixed and the files are arguments, so the script never needs editing.
- The token is read from `.env`, so no secret is written in the code or committed.
- No `claude mcp add` is needed: the server URL and token are passed in code for this run only.

## 3. Where
| Item | Location |
|---|---|
| Script | `scripts/run_claude_brand.py` |
| Server start script | `scripts/start-mcp-server.sh` |
| Token | `.env` (gitignored), key `BRAND_MCP_AUTH_TOKEN` |
| SDK pin | `requirements-dev.txt` (`claude-agent-sdk==0.2.165`), installed in `myenv/` |
| Inputs searched by bare name | `eval/artifacts/`, `inputs/`, project folder |
| Results | `output/run-<UTC time>-<6 hex>/` (`branded.html`, `report.md`, `report.json`) |

Paths must be inside the project folder (the server only allows `.` for inputs).

## 4. How to run
Run both commands from the project folder, in two terminals.

Terminal 1 (leave running):
```bash
./scripts/start-mcp-server.sh
```
Terminal 2:
```bash
myenv/bin/python scripts/run_claude_brand.py myridius-brand-guide.md mcp-servers-report-simple-v2.html
```
Each argument is a path, or a bare file name. A full path also works:
```bash
myenv/bin/python scripts/run_claude_brand.py myridius-brand-guide.md eval/artifacts/mcp-servers-report-simple-v2.html
```
Start the server first. If it is not running, the script fails with a connection error.
If `.env` is missing, run the start script once to create it.

## 5. How the script works
| Part | What | Why |
|---|---|---|
| Imports | `asyncio`, `sys`, `Path`, SDK `query`, `ClaudeAgentOptions`, message types | The SDK streams results asynchronously |
| `SERVER_NAME`, `SERVER_URL` | Name and endpoint of the server | Tool names are `mcp__<server>__<tool>` |
| `SEARCH_DIRS` | Folders searched for a bare file name | So you can type just the file name |
| `ALLOWED_TOOLS` | The five server tools, pre-approved | A script cannot answer a permission prompt; an unlisted tool is blocked |
| `read_token()` | Reads `BRAND_MCP_AUTH_TOKEN` from `.env` | The server answers 401 without it |
| `resolve(name)` | Path as given, else search `SEARCH_DIRS`; error if missing or ambiguous | Clear errors instead of server failures |
| `run()` | Builds the options (SSE url + `Authorization: Bearer` header), sends the fixed prompt, prints Claude's text and the final cost/error flag | Does the actual work |
| `main()` | Checks for exactly two arguments, resolves both, starts `run()` | A wrong call prints usage, not a stack trace |

## 6. Limits and notes
- Each run makes a real model call and costs money (the script prints the cost at the end).
- Claude only calls the tools the prompt needs (classify, apply, report); the other two are allowed
  but unused unless the prompt changes.
- Paths are on the server's machine and must be inside the allowed folders.

## 7. Step by step: running the project
The server must be running **every time**, before you use the tools from the Claude Code CLI
or from the script. Neither of them starts the server; they only connect to it.

```
Terminal 1: start-mcp-server.sh  (server on http://127.0.0.1:8010/sse, leave running)
                 ▲                                ▲
                 │ connects                       │ connects
Terminal 2: Claude Code CLI (chat)    or    run_claude_brand.py (script)
```

Run every command from the project folder, `~/evoq_R-D/mcp/mcp/brand_compliance_mcp`,
not from `scripts/`.

### Step 1: start the server (every time, terminal 1)
```bash
cd ~/evoq_R-D/mcp/mcp/brand_compliance_mcp
./scripts/start-mcp-server.sh
```
Wait for `Application startup complete`, then leave this terminal open. Stop it with Ctrl+C.
Start it with `./` or `bash`, never with `python`: it is a bash script.

### Step 2: use it, in one of two ways (terminal 2)

**Way A: Claude Code CLI (chat).** Register the server once; it is remembered after that.
```bash
cd ~/evoq_R-D/mcp/mcp/brand_compliance_mcp
TOKEN=$(sed -n 's/^BRAND_MCP_AUTH_TOKEN=//p' .env)
claude mcp add --transport sse --scope user brand-compliance http://127.0.0.1:8010/sse \
  --header "Authorization: Bearer $TOKEN"
claude mcp list        # brand-compliance ... ✓ Connected
```
Then start a new Claude Code session and ask, for example: *"Use brand-compliance to apply
myridius-brand-guide.md to eval/artifacts/mini-broken.html and show me the report."*

**Way B: the script (no chat, no registration needed).**
```bash
cd ~/evoq_R-D/mcp/mcp/brand_compliance_mcp
myenv/bin/python scripts/run_claude_brand.py myridius-brand-guide.md mini-broken.html
```

### Step 3: look at the result
Open the newest `output/run-<UTC time>-<6 hex>/` folder: `branded.html` in a browser, `report.md`
for what changed and why.

### Common problems
| You see | Cause | Fix |
|---|---|---|
| `SyntaxError ... umask 077` | Started the `.sh` with `python` | `./scripts/start-mcp-server.sh` |
| `address already in use` | Another program uses the port | Port is set in `config/settings.toml` (`port = 8010`); this file must exist |
| `sed: can't read .env` and then `401` | Commands run from `scripts/`, so the token was empty | `cd` to the project folder and register again |
| `✗ Failed to connect` in `claude mcp list` | Server not running, or registered with an old port/token | Start the server; `claude mcp remove brand-compliance -s user`, then register again |
| Connection error from the script | Server not running | Do Step 1 first |
| Code change not showing in new reports | The server still runs the old code | Ctrl+C in terminal 1 and start it again |
| `.env` was deleted | The start script made a new token | Register Way A again (the script reads `.env` itself) |
