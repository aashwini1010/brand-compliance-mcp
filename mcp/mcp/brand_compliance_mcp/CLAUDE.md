# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Read this first
`README.md` is the entry point and `docs/DEVELOPMENT-GUIDE.md` is the full, plain-language story of the project: every step, every file,
why it exists, where it is used, decisions, bugs caught, limits, and what is next. Keep it updated after
every step (see its "Maintenance checklist"); this file is the short version.

## Project status
All 14 build steps are done (HTTP + SSE server, email support, evaluation set, final docs), plus
post-V1 fixes from review (Step 15: page colour variables). The step history is in
`docs/DEVELOPMENT-GUIDE.md` section 4; suggested improvements are in section 9.

## Commands
Run everything from this folder (`evoq_R-D/`, the git root), not its parent: `.venv/bin/...` and the
default guide/artifact/output paths are relative. Python 3.12 (`requires-python = ">=3.12,<3.13"`) with a local venv at `.venv/` (uv is not installed;
use venv + pip). The package is not pip-installed: pytest gets `src` from `pythonpath` in
`pyproject.toml`, everything else needs `PYTHONPATH=src`.
Two venvs are referenced: `.venv/` (dev tools; used by the commands below, README and the
pre-commit hooks) and `myenv/` (runtime deps only, no pytest/ruff/mypy; used by
`scripts/start-mcp-server.sh`). Check which exists before running anything; if `.venv/` is
missing, create it (`python3.12 -m venv .venv`) and install `requirements-dev.txt`.
```
.venv/bin/pip install -r requirements-dev.txt   # setup (requirements.txt is runtime only)
.venv/bin/pytest                                # all tests; fails below 80% coverage
.venv/bin/pytest tests/unit/core/test_logging.py::test_configure_logging_sets_root_level   # single test
.venv/bin/ruff check . && .venv/bin/ruff format .
.venv/bin/mypy                                  # strict; checks package brand_compliance
```
Dependencies are pinned in `requirements*.txt`; update the pin when adding a library.

Evaluate (12 hand-written cases; exit code 0 only if all pass; writes `eval/reports/`):
```
PYTHONPATH=src .venv/bin/python -m brand_compliance.evaluation
```

Run the server (HTTP + SSE, loopback only; it refuses to start without a token of >= 16 characters):
```
./scripts/start-mcp-server.sh     # reads (or first creates) the token in .env; uses myenv/
# or by hand:
export BRAND_MCP_AUTH_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
PYTHONPATH=src .venv/bin/python -m brand_compliance.server     # endpoint: http://127.0.0.1:8000/sse
```
Claude Code connects by URL with `claude mcp add --transport sse ... --header "Authorization:
Bearer <token>"` (exact command in `docs/tools.md`); it does not start the server. If `.env` is
deleted the script makes a new token and the client must be re-registered. Tool paths are resolved
on the server against `allowed_input_dirs = ["."]` / `allowed_output_dirs = ["output"]`, i.e.
relative to this folder; client files go in `inputs/` (gitignored, may be confidential).
Settings come from `config/settings.toml`; override with `BRAND_MCP_<SECTION>__<NAME>` env vars.
FastMCP 4 uses `httpx2` (not `httpx`); `pytest -p no:logging` disables the `caplog` fixture.
A `GET / 404` in the server log is harmless: only `/sse` is served.

## What this is
A FastMCP server that takes one brand guide plus one HTML artifact (static page or email), writes a
restyled **copy**, and returns a report of every change and every rule not applied. Served over
**HTTP + SSE** (not stdio) on `127.0.0.1`, local-only, no cloud calls.

## Architecture rules that span many files
- **Plugin architecture.** Every format and capability is a plugin behind a `typing.Protocol` in
  `core/contracts.py`, found through `core/registry.py` (built-ins plus `importlib.metadata` entry points).
  Core code must never branch on a format name; add a plugin instead.
- **Layers.** `server/` (thin MCP tools) → `pipeline/` (orchestrator) → `rules/` + `models/` → `plugins/` →
  `core/`. `models/` is a leaf (imports nothing from the app); `core/` may import only `models/`.
- **Two-layer guide parsing.** Source adapters turn any guide format into one `GuideDocument` tree
  (each node keeps a `SourceSpan`); extractors read only that tree, never raw files.
- **Extract, then normalize.** Extractors only report findings (`RuleCandidate` with exact guide lines);
  `rules/normalize.py` alone decides meaning and status. Wording lives in `config/vocabulary.toml`, not in
  code. `rules/leftovers.py` (a function, not a plugin) keeps every unclaimed paragraph/row/code block, so
  nothing in a guide is silently dropped; an integration test enforces this on the Myridius guide.
- **Dotted roles.** A rule for role `button` applies to every `button.*` variant; a more specific role
  (`button.primary`) wins for the properties it sets. Size-specific rules (`button.medium`) apply only when
  the artifact marks the size; the tool never assumes a default size.
- **Artifact side.** HTML is parsed with lxml (`plugins/artifacts/base.py`); `core/svg.py` restores the SVG
  attribute case libxml2 lowercases, and the original doctype is kept. `core/cascade.py` reads *base* styles
  only (`@media` is counted, not evaluated) and reports an undeterminable background as `unknown`, never a
  guess. Elements get roles from `config/roles.toml` (first match wins); a button is `button.primary` only
  when its markup says so. Classification that is close is flagged ambiguous and uses the safer email path.
- **Applying (static).** `plugins/appliers/` return an `ApplyResult` (changes, per-element skips, `satisfied`
  count) and never edit the DOM. `pipeline/planning.py` resolves overlaps (more specific role wins, then
  later rule) and sets each rule's outcome. `plugins/writers/static.py` marks elements with `data-brand-*`
  attributes and writes one `<style id="brand-compliance">` whose selectors carry an id boost, so brand
  rules beat page CSS without `!important` (forced only per element via `data-brand-force`). If the page has
  dark variants the block is scoped to light mode and excludes `[data-theme="dark"]`. Names the tool writes
  live in `core/markers.py`; the cascade and font applier ignore the tool's own output so re-runs are
  byte-identical.
- **Page colour variables.** Role rules cannot reach a page's own `--accent`/`--bar`-style variables, so
  `plugins/appliers/tokens.py` (a *passive* applier on `color_token` rules) overrides the ones listed in
  `config/token_map.toml` with guide tokens, per light/dark surface; the writer emits them as root-level
  blocks and the contrast verifier sees them through `StyleIndex.with_overrides`. Never add a variable the
  page does not define. Light accent text uses `--digital-pavo` because `--virtual-tide` fails 4.5:1.
- **Orchestrator** (`pipeline/orchestrator.py`) only sequences stages and finds every plugin through the
  registry (`pipeline/bootstrap.py` builds it). It works on two parses of the artifact (pristine + working),
  validates every path against the settings' allowed folders, names runs `run-<UTC time>-<6 hex>`, and
  never reuses a run folder. If an output-level check fails, `branded.html` is withheld but all reports are
  still written. A missing handler/writer for an artifact type gives a clear UNSUPPORTED_FORMAT error.
- **Final statuses** (`pipeline/finalize.py`): applied, understood-not-applied, could-not-interpret,
  conflict-unresolved, or `reference` (definitions such as palette tokens). No rule may stay `pending`.
  Rules enforced by a check (contrast, forbidden colour) are *applied* with the check's evidence.
- **Reporters** declare their `filename`, so `report.json` can list every file of the run.
- **MCP server** (`server/`): `app.py` builds a FastMCP server with `mask_error_details=True` and a
  constant-time `BearerTokenVerifier`, mounts `http_app(transport="sse", host_origin_protection=True)`
  (wrong Host -> 421, wrong Origin -> 403, no token -> 401) and refuses unsafe settings at startup
  (`validate_startup`). `tools.py` holds the five tools plus the `report://{run_id}` resource; each is
  wrapped by `@guarded`, which turns typed errors into `ToolError("[CODE] message")` and anything unexpected
  into a generic `[INTERNAL_ERROR]` (details only in the server log). Tools take paths on the *server's*
  machine, checked against the allowed folders; `run_id` is validated against a strict pattern.
- **Email path:** same rules/appliers/verifiers, different handler + writer. `plugins/appliers/support.py`
  reads `config/email_support.toml`; for emails an unsupported value (`clamp()`, `var()`, `vw`...) becomes a
  reported skip (never approximated), `rem` becomes px, a plain `background` becomes `background-color`.
  `plugins/writers/inline.py` writes only the inline `style` attribute (no `<style>` block, no marker
  attributes) and leaves Outlook conditional comments untouched; the structure verifier checks an email's
  `style` equals the original declarations plus exactly the planned changes.
- **Evaluation** (`evaluation/`, cases in `eval/expected/*.json`): expectations are hand-written from the
  guide, never copied from the tool's output. Content/fidelity/idempotence metrics are recomputed by the
  evaluator's own code (do not reuse the verifiers). A sabotage test proves it catches corruption even with
  a verifier disabled. `serialize_html` writes the whole tree (outer comments kept; no invented doctype).
  An intended behaviour change makes `tests/integration/test_evaluation_set.py` fail (unexpected changes,
  rule status accuracy); update the case JSON by hand from the guide, then rerun the evaluation so
  `eval/reports/` matches.
- **Appliers decide WHAT, writers decide HOW.** The same applier serves static pages (stylesheet writer)
  and emails (inline writer).
- **Deterministic editing.** No generated markup. An AI extractor may be added later as a plugin, flagged
  `ai_assisted`, and must never edit HTML.
- **Never guess.** Every rule ends as Applied, Understood-but-not-applicable, Could-not-interpret, or
  Conflict-unresolved, with a reason and a guide source line. Contradictory rules are both left unapplied
  (`rules/conflicts.py`); a contradiction counts as resolved only when the guide itself states the exception.
- **Verifiers declare a `scope`** (`changes` judges the plan and may name changes to undo; `output`, the
  default, judges the written file); the orchestrator runs every registered verifier of each scope, so a new
  verifier needs no orchestrator change.
- **Verify then roll back** (`pipeline/verification.py`). Two phases. *Change-level* verifiers (contrast,
  forbidden-colour) judge the planned edits against the pristine original, name the change to undo (text
  colour first, then background) and the loop repeats until clean; a failure the page already had is
  reported, not blamed. *Output-level* verifiers (structure, assets) judge the written output and cannot be
  fixed by one rollback, so they fail the run. Original-intact and idempotence verifiers are built per run
  (they need a path / a re-run callable). The orchestrator needs two parses of the input: a pristine one
  for verifiers and a working one the writer mutates.
- **Original artifact is never modified.** Outputs go to `output/<run_id>/`; the source SHA-256 is recorded.
- **Never invent a logo.** No supplied asset means the logo rule is reported as not applicable.
- **Confidentiality.** Logs carry run ids, rule ids and counts only, never guide or artifact content.
  Bind to `127.0.0.1`, require a bearer token and check `Origin`/`Host`.

## Conventions
Follow `custom-best-practices.txt` (88 columns, type hints, docstrings, `src/` layout, tests in
`tests/unit` and `tests/integration` mirroring `src/`, shared fixtures only in `tests/conftest.py`,
config in `config/`, not in `src/`). Test names: `test_<function>_<scenario>`.

## Input files
`myridius-brand-guide.md` is the reference guide and the main test input. It deliberately contains
contradictions, web-only CSS features and subjective rules; eval cases depend on these.
