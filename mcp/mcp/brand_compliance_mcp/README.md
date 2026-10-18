# Brand Compliance MCP

An [MCP](https://modelcontextprotocol.io) server that takes **one brand guide** and **one HTML
artifact** (a web page or a marketing email), restyles a **copy** of the artifact to match the guide,
and writes a report that says exactly what it changed, what it could not apply, and why.

It runs **fully automatically and fully locally**. There is no approval step, no cloud service and
no AI model: guides are read by deterministic code, so the same input always gives the same output.

## What you get from one call

| File (in `output/<run_id>/`) | What it is |
|---|---|
| `branded.html` | The restyled copy. The original file is never touched |
| `report.md` | The human-readable report (see below) |
| `report.json` | The same report, machine-readable |
| `guide_rules.json` | Every rule found in the guide and its final status, so you can audit how the guide was read |

The report separates, for every rule in the guide:

- **Applied**: understood and acted on (or enforced by a check), with before/after for every edit
- **Understood but not applied**: with the reason (no such element, logo asset missing, undone to keep text readable, not supported in email…)
- **Could not interpret**: subjective or unsupported wording; nothing is guessed
- **Contradictions**: where the guide disagrees with itself; neither side is applied
- **Reference definitions**: palette tokens and variables that other rules use

## Quick start

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt

# start the server (HTTP + SSE on 127.0.0.1; refuses to start without a secret token)
export BRAND_MCP_AUTH_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
PYTHONPATH=src .venv/bin/python -m brand_compliance.server      # http://127.0.0.1:8000/sse
```

Point any MCP client at `http://127.0.0.1:8000/sse` with the header
`Authorization: Bearer <your token>`, then call the `apply_brand` tool. See
[docs/tools.md](docs/tools.md) for every tool and example calls.

To try it without an MCP client, run the whole workflow from Python:

```python
from brand_compliance.core.settings import load_settings
from brand_compliance.pipeline.bootstrap import build_registry
from brand_compliance.pipeline.orchestrator import Orchestrator
from brand_compliance.rules.vocabulary import load_vocabulary

settings, vocabulary = load_settings(), load_vocabulary()
summary = Orchestrator(build_registry(settings, vocabulary), settings, vocabulary).run(
    "myridius-brand-guide.md",
    "eval/artifacts/mcp-servers-report-simple-v2.html",
    "output",
)
print(summary.message, summary.output_dir)
```

## The tools

| Tool | Purpose |
|---|---|
| `apply_brand` | Apply a guide to one artifact; writes the four files above |
| `extract_rules` | Show how a guide is read, without touching any artifact |
| `classify_artifact` | Static page or email, and the evidence |
| `get_report` | Fetch a saved report (Markdown or JSON) |
| `list_plugins` | Show what is loaded |

## How it stays safe

- **The original is never modified.** Output goes to a new folder; the source file's SHA-256 is checked before and after.
- **Output is verified, not assumed.** Text contrast, structure (same elements, text, scripts, comments), assets (images, links, anchors) and idempotence are checked. A change that would make text unreadable is undone and reported. If a structural check fails, `branded.html` is withheld.
- **Nothing is guessed.** Vague or subjective guidance is reported as "could not interpret"; contradictions are reported, never silently resolved.
- **The server is hardened.** Loopback only by default, a bearer token is required, wrong `Host`/`Origin` headers are rejected, file paths are limited to allowed folders, and internal errors never leak details to clients.

## Results

On the evaluation set (`eval/`, 12 hand-written cases) the tool passes all 12: 75 of 75 hand-labelled
rules end in the right status, 100 of 100 expected edits are made and **none of 360 changes is
unexpected**; text, links, images, scripts and comments are preserved and runs are idempotent.
Details and the honest limits are in [docs/approach.md](docs/approach.md); the scorecard and sample
reports are in [`eval/reports/`](eval/reports/scorecard.md).

Run it yourself: `PYTHONPATH=src .venv/bin/python -m brand_compliance.evaluation`

## Project layout

```
config/       settings.toml · vocabulary.toml · roles.toml · email_support.toml   (behaviour, no code)
src/brand_compliance/
  models/     plain data shapes          core/      shared helpers, plugin interfaces, registry
  rules/      guide → rules, conflicts   plugins/   readers, finders, handlers, appliers, writers, verifiers, reporters
  pipeline/   orchestrator, planning, verification, final statuses
  server/     the MCP tools              evaluation/  scoring against hand-written expectations
tests/        unit/ (mirrors src/) and integration/        eval/   guides, artifacts, expected results, reports
docs/         the documents listed below
```

## Documentation

| Document | For |
|---|---|
| [docs/approach.md](docs/approach.md) | The short write-up: approach, limitations, how success was measured |
| [docs/tools.md](docs/tools.md) | Connecting a client; every tool, input, output and error code |
| [docs/architecture.md](docs/architecture.md) | How it is built: layers, data flow, design decisions |
| [docs/plugin-guide.md](docs/plugin-guide.md) | Adding a guide format, rule finder, check or report format |
| [docs/DEVELOPMENT-GUIDE.md](docs/DEVELOPMENT-GUIDE.md) | The step-by-step story of the build: every file, why, and where it is used |

## Current limits (the important ones)

- Guides: Markdown only today (PDF, JSON, URL readers plug in; see the plugin guide).
- No visual rendering check: layout effects of the guide's type scale are not measured.
- Content inside Outlook conditional comments (including VML buttons) is left untouched.
- Only one case in the evaluation set uses real material; real client guides and emails would strengthen it.

Developed to the standards in `custom-best-practices.txt`: Python 3.12, type hints, `ruff`, strict
`mypy`, `pytest` with ≥ 80% coverage (currently ~98%).
