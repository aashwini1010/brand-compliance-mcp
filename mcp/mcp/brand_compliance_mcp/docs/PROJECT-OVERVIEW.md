# Brand Compliance MCP: New Developer Onboarding Guide

> Written for: a developer who just joined the team and knows nothing about this project.
> Read this first. Then use the other files in `docs/` for depth (they are listed in section 16).
> All diagrams are plain text, so they render in any editor, terminal or Git viewer.

---

## Table of contents

1. [The project in one minute](#1-the-project-in-one-minute)
2. [Why was it built?](#2-why-was-it-built)
3. [Who uses it, and how?](#3-who-uses-it-and-how)
4. [Inputs and outputs](#4-inputs-and-outputs)
5. [End-to-end workflow, in detail](#5-end-to-end-workflow-in-detail)
6. [Which file starts the application?](#6-which-file-starts-the-application)
7. [How a request flows through the system](#7-how-a-request-flows-through-the-system)
8. [Which functions call which functions](#8-which-functions-call-which-functions)
9. [Which files depend on which files](#9-which-files-depend-on-which-files)
10. [Folder and file guide](#10-folder-and-file-guide)
11. [The most important classes, functions and plugins](#11-the-most-important-classes-functions-and-plugins)
12. [How all components connect](#12-how-all-components-connect)
13. [Reading order: what to study first, second, third](#13-reading-order)
14. [Safe changes vs risky areas](#14-safe-changes-vs-risky-areas)
15. [MCP servers, clients, tools, APIs, pipelines, agents](#15-mcp-servers-clients-tools-apis-pipelines-agents)
16. [Commands cheat sheet and further reading](#16-commands-cheat-sheet-and-further-reading)
17. [Glossary](#17-glossary)

---

## 1. The project in one minute

**What it is:** a small server (an *MCP server*, built with the Python library **FastMCP**) that does one job:

> You give it **one brand guide** (a Markdown document that says "our colours are X, our font is Y,
> buttons look like Z") and **one HTML file** (a web page or a marketing email).
> It makes a **restyled copy** of the HTML that follows the guide, and writes a **report** saying
> exactly what it changed, what it could not change, and why.

Three things to remember about it:

| Property | What it means |
|---|---|
| **Deterministic** | No AI model is used. Same input gives the same output, every time. |
| **Local** | Runs on your machine (`127.0.0.1`). No cloud calls. Client documents can be confidential. |
| **Honest** | It never guesses. If a rule is vague, contradictory, or cannot be applied, the report says so. |

The project folder is `evoq_R-D/` (the git root). The Python package is `src/brand_compliance/`.

---

## 2. Why was it built?

The origin is `problem-statement.txt`. In plain words:

**The problem today:** teams make HTML content (web pages, reports, marketing emails) and each must
follow a client's design rules. People do this by hand: read the guide, interpret it, edit the HTML,
and hope nothing was missed. It is slow, inconsistent, and nobody records what was changed or why.

**What the assignment asked for:**

1. An MCP server (FastMCP) with documented tools.
2. It accepts a design guide and HTML artifacts and applies the branding **with no human approval step**.
3. It produces a report: every change (what, where, before/after, which rule), and every rule *not* applied, with the reason.
4. A sample evaluation set, sample reports, and a short write-up (approach, limits, how success was measured).

**The hard constraints that shaped the design:**

| Constraint from the problem | How the project answers it |
|---|---|
| Output must stay usable (readable, nothing broken) | Verifiers check contrast, structure, assets; bad changes are rolled back |
| Original must not be destroyed | Output goes to a new folder; the source file's SHA-256 is checked before and after |
| Guides may be confidential | Fully local, no AI/cloud; logs never contain guide or page content |
| Static pages and emails render very differently | Two separate paths: a `<style>` block for pages, inline `style=""` for emails |
| Guides are ambiguous / contradictory | Every rule ends as applied / not-applied / could-not-interpret / conflict, never guessed |

---

## 3. Who uses it, and how?

```
 Human users                              Software users
 -----------                              --------------
 Designer / marketer / developer          Claude Code, Claude Desktop, or any MCP client
 asks an AI assistant:                    (or the Python `fastmcp.Client` in a script)
 "Brand this email with our guide"        calls the tool `apply_brand`
              |                                          |
              +------------------+-----------------------+
                                 v
                    Brand Compliance MCP server
                    http://127.0.0.1:8000/sse
```

**Typical user story**

1. An operator starts the server once (`./scripts/start-mcp-server.sh`).
2. They register it in their MCP client (e.g. Claude Code) with the bearer token.
3. They put the guide and the HTML file in an allowed folder.
4. They ask the assistant to call `classify_artifact`, then `apply_brand`, then `get_report`.
5. They open `output/<run_id>/branded.html` and `report.md`.

**Roles of people around the project**

| Person | What they do with it |
|---|---|
| End user (designer/marketer) | Runs `apply_brand`, reads the report |
| Reviewer / brand owner | Reads `report.md` to see which rules were skipped and why |
| Developer (you) | Adds new guide formats, rule types, checks, report formats via plugins |
| Evaluator | Runs the evaluation set to measure accuracy |

---

## 4. Inputs and outputs

### 4.1 Inputs

| Input | Form | Notes |
|---|---|---|
| **Brand guide** | A Markdown file (`.md`) on the *server's* machine | Only Markdown today. Other formats (PDF, JSON, URL) plug in as new "source adapters". Max 5 MB. |
| **HTML artifact** | A `.html` / `.htm` file on the server's machine | A static page or a marketing email. UTF-8 only. Max 5 MB. |
| `output_dir` (optional) | Folder name | Must be inside the allowed output folders (default `output`). |
| `artifact_type` (optional) | `"static"` or `"email"` | Force the type; otherwise it is detected. |
| **Config files** (`config/*.toml`) | Behaviour settings | Vocabulary, role mapping, token mapping, email support, server settings. |
| **Env var** `BRAND_MCP_AUTH_TOKEN` | Secret, 16+ chars | Required to start the server. |

Paths are **paths on the server's machine**. File contents are never uploaded over the connection.

### 4.2 Outputs (one folder per run: `output/run-<UTC time>-<6 hex>/`)

| File | What it is |
|---|---|
| `branded.html` | The restyled **copy**. Withheld if an output check fails. |
| `report.md` | Human-readable report |
| `report.json` | Same report, machine-readable |
| `guide_rules.json` | Every rule found in the guide and its final status (audit trail of how the guide was read) |

The tool call itself returns a short `RunSummary` (run id, status, file paths, rule counts, change count, conflict count, which checks passed).

### 4.3 The five possible fates of every rule

```
                        +--> APPLIED                  (understood and acted on, or enforced by a check)
                        |
  every rule in the --> +--> UNDERSTOOD, NOT APPLIED   (e.g. no such element, not supported in email, undone for readability)
  guide                 |
                        +--> COULD NOT INTERPRET      (subjective or unsupported wording; nothing guessed)
                        |
                        +--> CONFLICT UNRESOLVED      (guide contradicts itself; neither side applied)
                        |
                        +--> REFERENCE                (definitions such as palette tokens that other rules use)
```

No rule may stay `pending` (`pipeline/finalize.py` raises an error if one does).

---

## 5. End-to-end workflow, in detail

### 5.1 The big picture: Input → Processing → Output

```
  INPUT                          PROCESSING                                      OUTPUT
  -----                          ----------                                      ------
  brand-guide.md  ------+
                        |    1. Validate paths & sizes
  page-or-email.html ---+--> 2. Read guide -> tree -> candidates -> RULES
                        |    3. Classify HTML: static page or email?
  (optional)            |    4. Parse HTML twice (pristine + working)
  artifact_type  -------+    5. PLAN changes (appliers + overlap resolution)
                             6. VERIFY plan, ROLL BACK harmful changes (loop)
                             7. WRITE changes (stylesheet writer or inline writer)
                             8. Output checks: structure, assets, original intact, idempotence
                             9. Give every rule a final status
                            10. Render reports                                  --> branded.html
                                                                                --> report.md
                                                                                --> report.json
                                                                                --> guide_rules.json
```

### 5.2 Start-to-end trace: which file, which function, in what order

Read this top to bottom. Each line is `file → function()` and says what it does and who it calls next.
Line numbers are from the current code (they may drift by a few lines after edits).

#### PART A: Starting the server (happens once)

```
A1  scripts/start-mcp-server.sh
      creates .env token if missing, loads it, runs:  python -m brand_compliance.server
        |
A2  src/brand_compliance/server/__main__.py  →  main()                         [line 13]
      calls configure_logging()                       core/logging.py
      calls serve()
        |
A3  src/brand_compliance/server/app.py  →  serve()                             [line 94]
      calls load_settings()                           core/settings.py        (reads config/settings.toml + BRAND_MCP_* env vars)
      calls load_vocabulary()                         rules/vocabulary.py     (reads config/vocabulary.toml)
      calls create_server(settings, vocabulary)
        |
A4  server/app.py  →  create_server()                                          [line 34]
      calls build_registry(settings, vocabulary)      pipeline/bootstrap.py   [line 22]
          → register_sources()      plugins/sources/__init__.py      (Markdown reader)
          → register_extractors()   plugins/extractors/__init__.py   (6 rule finders)
          → register_artifacts()    plugins/artifacts/__init__.py    (static + email handlers)
          → register_appliers()     plugins/appliers/__init__.py     (7 appliers)
          → register_writers()      plugins/writers/__init__.py      (stylesheet + inline)
          → register_verifiers()    plugins/verifiers/__init__.py    (contrast, forbidden, structure, assets)
          → register_reporters()    plugins/reporters/__init__.py    (md, json, guide_rules)
          → load_entry_point_plugins()  core/registry.py             (external plugins, optional)
      creates Orchestrator(registry, settings, vocabulary)   pipeline/orchestrator.py  [line 77]
      creates BearerTokenVerifier(token)                     server/auth.py
      creates FastMCP("brand-compliance", auth=..., mask_error_details=True)
      calls register_tools(server, orchestrator, registry)   server/tools.py  [line 59]
          → defines and registers the tools: apply_brand, extract_rules, classify_artifact,
            get_report, list_plugins, and the resource report://{run_id}
        |
A5  server/app.py  →  build_http_app()                                         [line 83]
      calls validate_startup(settings)                [line 53]  (refuses to start without a good token)
      calls server.http_app(transport="sse", host_origin_protection=True)
        |
A6  server/app.py  →  serve() continues:  uvicorn.run(app, 127.0.0.1, 8000)
      SERVER IS NOW LISTENING at http://127.0.0.1:8000/sse
```

#### PART B: One `apply_brand` request (happens on every call)

```
B1  MCP client (Claude Code or fastmcp.Client)
      opens http://127.0.0.1:8000/sse with header  Authorization: Bearer <token>
      sends tool call: apply_brand(guide_path, artifact_path, output_dir, artifact_type)
        |
B2  FastMCP + uvicorn (library code, not ours)
      checks Host (421), Origin (403), token → server/auth.py → BearerTokenVerifier.verify_token() (401)
        |
B3  server/error_mapping.py  →  guarded("apply_brand") wrapper                 [line 41]
      calls the real function inside try/except
      (BrandComplianceError → "[CODE] message", anything else → "[INTERNAL_ERROR]")
        |
B4  server/tools.py  →  apply_brand()                                          [line 66]   <-- THE TOOL FUNCTION
      converts artifact_type string → ArtifactType
      calls orchestrator.run(guide_path, artifact_path, output_dir, forced)
        |
B5  pipeline/orchestrator.py  →  Orchestrator.run()                            [line 93]   <-- THE WORKFLOW
      makes run_id "run-YYYYMMDD-HHMMSS-xxxxxx"
      and then calls, in this exact order, steps B6 to B18 below
```

```
B6  orchestrator.py → _validate_inputs()                                       [line 174]
      → _resolve_guide()                                                       [line 160]  → core/paths.py → resolve_within()
      → _resolve_artifact()                                                    [line 166]  → core/paths.py → validate_input_file()
      Result: safe, resolved Path for the guide and the HTML file.

B7  orchestrator.py → _prepare_output()                                        [line 192]
      → core/paths.py → validate_output_dir()
      creates output/<run_id>/ (mkdir, never reused)

B8  core/hashing.py → sha256_file(artifact)
      orchestrator.py → _read_text(artifact)                                   [line 410]
      Result: fingerprint of the original, and the HTML as text.

B9  orchestrator.py → _interpret(guide)                                        [line 205]   READ THE GUIDE
      │
      ├─ registry.find(SourceAdapter, can_handle)                              core/registry.py
      ├─ plugins/sources/markdown.py → MarkdownSourceAdapter.load()            [line 31]
      │     builds GuideDocument tree (each node keeps its line number)
      │     uses _TreeBuilder.build()                                          [line 50]
      │
      └─ rules/interpret.py → interpret_guide()                                [line 26]
            ├─ for each extractor: extractor.extract(document)                 plugins/extractors/*
            │     TokenTableExtractor, TypographyExtractor, ComponentExtractor,
            │     CssBlockExtractor, BulletSpecExtractor, DirectiveExtractor
            ├─ rules/leftovers.py → collect_unmatched()                        [line 43]
            ├─ rules/normalize.py → normalize()                                [line 37]
            │     → _interpret() [52] → _palette / _typography / _component /
            │       _css_declaration / _css_import / _directive / _bullet_spec
            │       (the last two call rules/directives.py and rules/bullet_specs.py)
            └─ rules/conflicts.py → detect_conflicts()                         [line 54]
      Result: GuideInterpretation(rules, conflicts)

B10 orchestrator.py → _classify()                                              [line 213]   STATIC OR EMAIL?
      → plugins/artifacts/classifier.py → classify_text() [114] → classify_html() [27]
      Result: Classification + chosen ArtifactType (ambiguous → email path).

B11 orchestrator.py → _find_handler()                                          [line 228]
      → registry.find(ArtifactHandler, ...)
      Result: StaticArtifactHandler or EmailArtifactHandler
              (plugins/artifacts/static.py or email.py, both subclasses of html_handler.py)

B12 orchestrator.py → _transform()                                             [line 261]   THE MAIN CHANGE ENGINE
      │
      ├─ handler.parse(text, name)  called TWICE (pristine + working)
      │     plugins/artifacts/html_handler.py → HtmlArtifactHandler.parse()    [line 48]
      │       → plugins/artifacts/base.py → parse_artifact_html()              (lxml tree)
      │       → core/cascade.py → StyleIndex.build()                           (CSS reading)
      │       → plugins/artifacts/roles.py → map_roles()                       [line 62]  (config/roles.toml)
      │       Result: ArtifactModel (tree, styles, roles, surfaces)
      │
      ├─ pipeline/planning.py → plan_changes()                                 [line 62]   WHAT TO CHANGE
      │       for each pending rule: applier.plan(rule, artifact)
      │         plugins/appliers/base.py → RoleStyleApplier.plan()             [line 69]
      │            (Typography/Color/Component/Surface appliers)
      │         plugins/appliers/tokens.py → TokenApplier.plan()
      │         plugins/appliers/font.py → FontFamilyApplier / FontSourceApplier
      │       → _resolve_overlaps() [107] → _specificity() [101]
      │       → _number() [142]  → _outcomes() [158]
      │       Result: PlanResult(changes CH001..., skips, outcomes)
      │
      ├─ pipeline/verification.py → verify_and_roll_back()                     [line 35]   CHECK + UNDO
      │       loop (max 6 rounds):
      │         verifier.check()   plugins/verifiers/contrast.py [56]  and  forbidden.py [16]
      │         if a change is blamed → PlanResult.rolled_back()               planning.py [38]
      │       Result: VerifiedPlan (clean plan, check results, what was undone)
      │
      └─ writer.write(changes, working)                                        HOW TO WRITE
            static page → plugins/writers/static.py → StylesheetWriter.write() [line 43]
                          adds one <style id="brand-compliance"> block
            email       → plugins/writers/inline.py → InlineWriter.write()     [line 36]
                          edits inline style="" attributes only
            Result: output ArtifactModel (the branded HTML tree)

B13 orchestrator.py → _final_checks()                                          [line 281]   CHECK THE OUTPUT
      → pipeline/verification.py → verify_output()                             [line 73]
            plugins/verifiers/structure.py → StructureVerifier.check()         [line 35]
            plugins/verifiers/assets.py → AssetsVerifier.check()               [line 27]
      → plugins/verifiers/original.py → OriginalIntactVerifier.check()         [line 24]
      → plugins/verifiers/idempotence.py → IdempotenceVerifier.check()         [line 23]
            calls rerun() [orchestrator line 301] → _transform() again on the branded HTML
      Result: list of CheckResult; any failure → RunStatus.FAILED_VERIFICATION

B14 core/hashing.py → sha256_file(artifact) again
      (proves the original file was not changed)

B15 orchestrator.py → _result()                                                [line 316]
      → pipeline/finalize.py → finalize_rules()                                [line 24]
            → _decide() [46] → _from_check() [73]
      Result: RunResult, with every rule in a final status (none left "pending").

B16 orchestrator.py → _write_outputs()                                         [line 355]
      → plugins/artifacts/base.py → serialize_html()    writes branded.html (only if COMPLETED)
      → plugins/reporters/markdown_report.py → MarkdownReporter.render()       [line 28]  → report.md
      → plugins/reporters/json_report.py → JsonReporter.render()               [line 15]  → report.json
      → plugins/reporters/guide_rules.py → GuideRulesReporter.render()         [line 16]  → guide_rules.json

B17 orchestrator.py → _summary()                                               [line 383]
      Result: RunSummary (run_id, status, files, rule_counts, change_count, checks, message)

B18 Orchestrator.run() returns RunSummary
        ↑ back to server/tools.py apply_brand()  (logs it, returns it)
        ↑ back to the guarded wrapper (error_mapping.py)
        ↑ back to FastMCP, which sends it to the MCP client
        ↑ the client shows it to the user; files are in output/<run_id>/
```

#### The whole thing on one page

```
scripts/start-mcp-server.sh
  └─► server/__main__.py :: main()
        └─► server/app.py :: serve()
              ├─► create_server() ── build_registry() (pipeline/bootstrap.py) + register_tools() (server/tools.py)
              ├─► build_http_app() ── validate_startup()
              └─► uvicorn.run()                         ◄── server waits here

MCP client ── apply_brand(...) ──► FastMCP (auth/Host/Origin)
                                     └─► error_mapping.py :: guarded wrapper
                                           └─► server/tools.py :: apply_brand()
                                                 └─► pipeline/orchestrator.py :: Orchestrator.run()
                                                       ├─ _validate_inputs()  → core/paths.py
                                                       ├─ _prepare_output()   → core/paths.py
                                                       ├─ sha256_file()       → core/hashing.py
                                                       ├─ _interpret()        → plugins/sources/markdown.py
                                                       │                      → rules/interpret.py → extractors, leftovers, normalize, conflicts
                                                       ├─ _classify()         → plugins/artifacts/classifier.py
                                                       ├─ _find_handler()     → core/registry.py
                                                       ├─ _transform()        → html_handler.parse() ×2
                                                       │                      → pipeline/planning.py :: plan_changes() → appliers
                                                       │                      → pipeline/verification.py :: verify_and_roll_back() → contrast/forbidden
                                                       │                      → writers/static.py or inline.py :: write()
                                                       ├─ _final_checks()     → structure, assets, original, idempotence
                                                       ├─ _result()           → pipeline/finalize.py :: finalize_rules()
                                                       ├─ _write_outputs()    → serialize_html + 3 reporters
                                                       └─ _summary()          → RunSummary
```

---

## 6. Which file starts the application?

**`src/brand_compliance/server/__main__.py`**, run as a module:

```bash
PYTHONPATH=src python -m brand_compliance.server
```

The usual way is the helper script **`scripts/start-mcp-server.sh`**, which creates the auth token in `.env`
if missing, loads it, and runs exactly the command above.

There is a second entry point for scoring: `src/brand_compliance/evaluation/__main__.py`
(`python -m brand_compliance.evaluation`), which runs the 12 hand-written test cases without a server.

### 6.1 Startup sequence

```
 Operator
    |  ./scripts/start-mcp-server.sh
    v
 scripts/start-mcp-server.sh
    |  1. cd to project root
    |  2. if .env missing: create BRAND_MCP_AUTH_TOKEN (random 32 bytes)
    |  3. source .env  (exports the token)
    |  4. exec python -m brand_compliance.server   (PYTHONPATH=src, uses myenv/)
    v
 server/__main__.py :: main()
    |  configure_logging()                          (core/logging.py)
    |  serve()
    v
 server/app.py :: serve()
    |  settings   = load_settings()                 (core/settings.py: config/settings.toml + BRAND_MCP_* env vars)
    |  vocabulary = load_vocabulary()               (rules/vocabulary.py: config/vocabulary.toml)
    |  server     = create_server(settings, vocabulary)
    |        |
    |        |  registry = build_registry(settings, vocabulary)       (pipeline/bootstrap.py)
    |        |       register_sources / extractors / artifacts /
    |        |       appliers / writers / verifiers / reporters
    |        |       load_entry_point_plugins()   (external plugins, optional)
    |        |  orchestrator = Orchestrator(registry, settings, vocabulary)
    |        |  verifier     = BearerTokenVerifier(settings.auth_token)
    |        |  server       = FastMCP("brand-compliance", auth=verifier, mask_error_details=True)
    |        |  register_tools(server, orchestrator, registry)        (server/tools.py: 5 tools + 1 resource)
    |        v
    |  app = build_http_app(server, settings)
    |        |  validate_startup(settings)   <-- refuses: missing/short token, exposed host w/o auth
    |        |  server.http_app(transport="sse", host_origin_protection=True)
    |        v
    |  uvicorn.run(app, host=127.0.0.1, port=8000)
    v
 SERVER LISTENING  ->  http://127.0.0.1:8000/sse   (bearer token required)
 (on failure: BrandComplianceError -> log "[CODE] message" -> exit code 2)
```

---

## 7. How a request flows through the system

### 7.1 Layers (the rule that keeps the code tidy)

```
   server/        thin MCP tools: validate, delegate, map errors
      |
      v
   pipeline/      orchestrator: only sequences the stages
      |
      v
   rules/  +  models/       guide -> rules ; plain data shapes
      |
      v
   plugins/       readers, finders, handlers, appliers, writers, verifiers, reporters
      |
      v
   core/          shared helpers, plugin interfaces, registry, settings, errors
```

Hard rules: `models/` imports nothing from the app (it is the leaf); `core/` imports only `models/`.
Core code never branches on a format name ("if email..."); you add a plugin instead.

### 7.2 Detailed request flow (one `apply_brand` call)

```
 User
  |  "Brand this email with our guide"
  v
 MCP Client  (Claude Code / Claude Desktop / fastmcp.Client)
  |  HTTP GET /sse  +  header  Authorization: Bearer <token>
  v
 Uvicorn (ASGI server)
  v
 FastMCP HTTP app
  |-- Host header wrong?        -> 421
  |-- Origin header wrong?      -> 403
  |-- Token missing/wrong?      -> 401   (server/auth.py: BearerTokenVerifier, hmac.compare_digest)
  v
 MCP tool dispatch:  apply_brand(guide_path, artifact_path, output_dir, artifact_type)
  v
 @guarded("apply_brand")               server/error_mapping.py
  |   BrandComplianceError  -> ToolError("[CODE] message")
  |   anything else         -> ToolError("[INTERNAL_ERROR] ...")   (details only in server log)
  v
 server/tools.py :: apply_brand()
  |  forced = ArtifactType(artifact_type) if given
  v
 Orchestrator.run(...)                 pipeline/orchestrator.py
  |
  |--> core/paths.py            path checks
  |--> SourceAdapter            plugins/sources/markdown.py        -> GuideDocument
  |--> interpret_guide()        rules/interpret.py                 -> rules + conflicts
  |        |-- RuleExtractor x6      plugins/extractors/*
  |        |-- collect_unmatched     rules/leftovers.py
  |        |-- normalize             rules/normalize.py  (+ rules/directives.py, bullet_specs.py, context.py, vocabulary.py)
  |        '-- detect_conflicts      rules/conflicts.py
  |--> classify_text()          plugins/artifacts/classifier.py    -> static | email
  |--> ArtifactHandler.parse()  plugins/artifacts/html_handler.py  -> ArtifactModel (x2)
  |        |-- StyleIndex.build        core/cascade.py
  |        '-- map_roles               plugins/artifacts/roles.py  (config/roles.toml)
  |--> plan_changes()           pipeline/planning.py
  |        '-- RuleApplier.plan x N    plugins/appliers/*
  |--> verify_and_roll_back()   pipeline/verification.py
  |        '-- Verifier.check          plugins/verifiers/contrast.py, forbidden.py
  |--> StyleWriter.write()      plugins/writers/static.py | inline.py
  |--> _final_checks()          structure, assets, original-intact, idempotence
  |--> finalize_rules()         pipeline/finalize.py
  '--> Reporter.render() x3     plugins/reporters/*
  v
 RunSummary  (pydantic model)  ->  returned through the MCP connection
  v
 MCP Client  ->  shows result to User  ->  User opens output/<run_id>/branded.html + report.md
```

### 7.3 The other tools (shorter flows)

```
 extract_rules(guide_path)   -> Orchestrator.extract_rules -> adapter.load -> interpret_guide   -> rules (no HTML touched)
 classify_artifact(path)     -> Orchestrator.classify_file -> classify_text                     -> {type, confidence, signals}
 get_report(run_id, format)  -> Orchestrator.read_report   -> validates run_id regex, finds output/**/<run_id>/report.*
 list_plugins()              -> registry.describe()                                             -> names per plugin kind
 resource report://{run_id}  -> Orchestrator.read_report(run_id, "markdown")
```

---

## 8. Which functions call which functions

### 8.1 Top-level call tree

```
main()                                         server/__main__.py
 └─ serve()                                    server/app.py
     ├─ load_settings()                        core/settings.py
     ├─ load_vocabulary()                      rules/vocabulary.py
     ├─ create_server()                        server/app.py
     │   ├─ build_registry()                   pipeline/bootstrap.py
     │   │   ├─ register_sources()             plugins/sources/__init__.py
     │   │   ├─ register_extractors()          plugins/extractors/__init__.py
     │   │   ├─ register_artifacts()           plugins/artifacts/__init__.py
     │   │   ├─ register_appliers()            plugins/appliers/__init__.py
     │   │   ├─ register_writers()             plugins/writers/__init__.py
     │   │   ├─ register_verifiers()           plugins/verifiers/__init__.py
     │   │   ├─ register_reporters()           plugins/reporters/__init__.py
     │   │   └─ load_entry_point_plugins()     core/registry.py
     │   ├─ Orchestrator(...)                  pipeline/orchestrator.py
     │   ├─ BearerTokenVerifier(...)           server/auth.py
     │   ├─ FastMCP(...)
     │   └─ register_tools()                   server/tools.py
     ├─ build_http_app()  └─ validate_startup()   server/app.py
     └─ uvicorn.run(app)
```

### 8.2 The main workflow call tree: `Orchestrator.run()`

```
Orchestrator.run()
 ├─ _validate_inputs() ─ _resolve_guide() / _resolve_artifact()
 │                        └─ resolve_within(), validate_input_file()      core/paths.py
 ├─ _prepare_output() ──── validate_output_dir()                          core/paths.py
 ├─ sha256_file()                                                         core/hashing.py
 ├─ _read_text()
 ├─ _interpret(guide)
 │   ├─ registry.find(SourceAdapter, can_handle)
 │   ├─ adapter.load()                      MarkdownSourceAdapter.load → _TreeBuilder.build
 │   └─ interpret_guide()                   rules/interpret.py
 │       ├─ extractor.extract()  (each)     TokenTable / Typography / Component / CssBlock / BulletSpec / Directive
 │       ├─ collect_unmatched()             rules/leftovers.py
 │       ├─ normalize()                     rules/normalize.py
 │       │   └─ _palette / _typography / _component / _css_declaration / _css_import /
 │       │      _directive (→ interpret_directive) / _bullet_spec (→ interpret_bullet)
 │       └─ detect_conflicts()              rules/conflicts.py
 ├─ _classify() ── classify_text() ── classify_html()                     plugins/artifacts/classifier.py
 ├─ _find_handler()
 ├─ _transform()
 │   ├─ handler.parse()  x2                 html_handler.py → StyleIndex.build, map_roles
 │   ├─ plan_changes()                      pipeline/planning.py
 │   │   ├─ applier.plan()  (each rule)     RoleStyleApplier.plan → _elements, _change
 │   │   ├─ _resolve_overlaps()  └─ _specificity()
 │   │   ├─ _number()
 │   │   └─ _outcomes()
 │   ├─ verify_and_roll_back()              pipeline/verification.py
 │   │   ├─ verifier.check()  (change scope)   ContrastVerifier, ForbiddenColorVerifier
 │   │   └─ PlanResult.rolled_back()
 │   └─ writer.write()                      StylesheetWriter.write | InlineWriter.write
 ├─ _final_checks()
 │   ├─ verify_output()                     StructureVerifier, AssetsVerifier
 │   ├─ OriginalIntactVerifier.check()
 │   └─ IdempotenceVerifier.check()  ── rerun() ── _transform() again on the branded output
 ├─ _result() ── finalize_rules() ── _decide() / _from_check()             pipeline/finalize.py
 ├─ _write_outputs() ── serialize_html(), reporter.render() x3
 └─ _summary()
```

### 8.3 Function call flow (condensed picture)

```
 apply_brand()
     │
     ▼
 Orchestrator.run()
     │
     ├──► _interpret() ──► interpret_guide() ──► extractors ──► normalize() ──► detect_conflicts()
     │
     ├──► _classify()  ──► classify_text()
     │
     ├──► _transform() ──► handler.parse()
     │                 ├─► plan_changes() ──► applier.plan()
     │                 ├─► verify_and_roll_back() ──► verifier.check() ◄─┐ loop
     │                 │                              rolled_back() ─────┘
     │                 └─► writer.write()
     │
     ├──► _final_checks() ──► verify_output() / OriginalIntact / Idempotence (re-runs _transform)
     │
     ├──► finalize_rules()
     │
     └──► _write_outputs() ──► reporters
```

---

## 9. Which files depend on which files

### 9.1 Package-level dependency diagram (measured from the real imports)

```
                         ┌───────────────────────┐
                         │   server/             │   MCP tools, auth, error mapping
                         └───────────┬───────────┘
                                     │ imports
                         ┌───────────▼───────────┐
                         │   pipeline/           │   orchestrator, planning, verification, finalize, bootstrap
                         └─────┬──────┬──────────┘
                               │      │
                ┌──────────────▼┐   ┌─▼─────────────┐
                │   rules/      │   │   plugins/    │   (bootstrap registers every plugin)
                └──────┬────────┘   └──────┬────────┘
                       │                   │
                       └────────┬──────────┘
                                │
                         ┌──────▼──────┐
                         │   core/     │   contracts, registry, settings, errors, cascade, color, paths ...
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │   models/   │   pure data (pydantic): Rule, Change, ArtifactModel, RunResult ...
                         └─────────────┘

  evaluation/  ──►  core, models, pipeline, plugins, rules        (test harness; sits beside server/)
```

Real measured edges:

```
core        -> models
rules       -> core, models
plugins     -> core, models
pipeline    -> core, models, plugins, rules
server      -> core, models, pipeline, rules
evaluation  -> core, models, pipeline, plugins, rules
models      -> (nothing)
```

### 9.2 Key file-to-file dependencies

```
server/__main__.py ──► server/app.py ──┬─► server/tools.py ──► server/error_mapping.py
                                       │                  └─► server/schemas.py
                                       ├─► server/auth.py
                                       ├─► pipeline/bootstrap.py ──► every plugins/*/__init__.py
                                       ├─► pipeline/orchestrator.py
                                       ├─► core/settings.py
                                       └─► rules/vocabulary.py

pipeline/orchestrator.py ──┬─► core/contracts.py      (plugin interfaces)
                           ├─► core/registry.py       (finds plugins)
                           ├─► core/paths.py, hashing.py, errors.py, settings.py
                           ├─► rules/interpret.py ──► rules/normalize.py ──► rules/{directives,bullet_specs,context,vocabulary}.py
                           │                     ├─► rules/leftovers.py
                           │                     └─► rules/conflicts.py
                           ├─► pipeline/planning.py ──► plugins/artifacts/base.py
                           ├─► pipeline/verification.py
                           ├─► pipeline/finalize.py
                           ├─► plugins/artifacts/{base,classifier}.py
                           └─► plugins/verifiers/{idempotence,original}.py

plugins/artifacts/html_handler.py ──► core/cascade.py ──► core/{color,css,units}.py
                                  ├─► plugins/artifacts/{base,classifier,roles}.py ──► config/roles.toml
                                  └─► core/contrast.py

plugins/appliers/base.py ──► core/{color,css}.py, plugins/appliers/support.py ──► config/email_support.toml
plugins/appliers/tokens.py ──► config/token_map.toml
plugins/writers/static.py ──► core/markers.py, plugins/writers/base.py, plugins/appliers/font.py
plugins/verifiers/contrast.py ──► core/{cascade,color,contrast}.py, plugins/artifacts/base.py

models/*   (leaf: only pydantic and each other)
```

### 9.3 The contracts hub

Almost everything plugin-shaped depends on **`core/contracts.py`** (the 7 interfaces) and is found via
**`core/registry.py`**. If you want to know "what kinds of things can I plug in?", read that one file.

---

## 10. Folder and file guide

### 10.1 Top level (`evoq_R-D/`)

| Path | Purpose |
|---|---|
| `README.md` | Entry point: what it is, quick start, tools, limits |
| `CLAUDE.md` | Short architecture rules for AI assistants working in the repo (also a great cheat sheet for humans) |
| `problem-statement.txt` | The original assignment |
| `custom-best-practices.txt` | The coding standards the project follows (88 columns, type hints, docstrings, tests...) |
| `myridius-brand-guide.md` | The **reference guide** and main test input. Deliberately contains contradictions, web-only CSS and subjective rules |
| `pyproject.toml` | Python 3.12, ruff, strict mypy, pytest (needs ≥ 80% coverage) |
| `requirements.txt` / `requirements-dev.txt` | Pinned dependencies (runtime / plus dev tools) |
| `.env` | Holds `BRAND_MCP_AUTH_TOKEN` (gitignored, secret) |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `scripts/start-mcp-server.sh` | Starts the server with the token from `.env` |
| `config/` | Behaviour without code (see 10.3) |
| `src/brand_compliance/` | All the code (see 10.2) |
| `tests/` | `unit/` (mirrors `src/`) and `integration/` (real guide, real pages, real HTTP server) |
| `eval/` | Evaluation set: `guides/`, `artifacts/`, `expected/` (hand-written answers), `reports/` (scorecard + sample reports) |
| `output/` | Results of runs (one `run-...` folder per run). Safe to delete. |
| `docs/` | Documentation (section 16) |
| `.venv/`, `myenv/` | Virtual envs: `.venv` = dev tools, `myenv` = runtime only (used by the start script) |

### 10.2 Source code (`src/brand_compliance/`)

#### `models/` — plain data shapes (leaf layer)

| File | Contains |
|---|---|
| `guide.py` | `GuideDocument`, `GuideNode`, `NodeKind` — the format-neutral guide tree |
| `source.py` | `SourceSpan` — file + line numbers + heading path ("where in the guide did this come from") |
| `rule.py` | `RuleCandidate` (raw finding), `Rule` (clean rule), `RuleStatus`, `Severity`, `Scope` |
| `artifact.py` | `ArtifactModel` (parsed HTML + roles + surfaces), `ArtifactType`, `Detection`, `Classification` |
| `change.py` | `Change` (one edit with before/after), `Skip` (one thing not done + reason), `ApplyResult` |
| `conflict.py` | `Conflict` — a detected contradiction |
| `report.py` | `CheckResult`, `RunResult` (everything about a run), `RunSummary` (what the tool returns), `Report` |

#### `core/` — shared building blocks

| File | Purpose |
|---|---|
| `contracts.py` | **The 7 plugin interfaces** (`typing.Protocol`) |
| `registry.py` | `PluginRegistry`: register / find / list plugins; loads external plugins from entry points |
| `settings.py` | `Settings` from `config/settings.toml` + `BRAND_MCP_*` env vars |
| `errors.py` | Typed errors with stable codes: `INVALID_INPUT`, `UNSUPPORTED_FORMAT`, `PARSE_FAILED`, `PATH_NOT_ALLOWED`, `PLUGIN_ERROR`, `CONFIGURATION_ERROR`, `INTERNAL_ERROR` |
| `paths.py` | Safe path handling (blocks escaping the allowed folders) |
| `cascade.py` | `StyleIndex`: a small CSS cascade reader (base styles, variables, backgrounds, text colours; `@media` counted, not evaluated; undeterminable → `unknown`, never guessed) |
| `color.py`, `contrast.py`, `units.py`, `css.py`, `svg.py`, `text.py` | Colour parsing, WCAG contrast ratio, unit conversion (rem→px), CSS declaration parsing, SVG attribute-case repair, text helpers |
| `markers.py` | Names of the attributes/ids the tool writes (`data-brand-*`, `brand-compliance` style id) |
| `hashing.py`, `logging.py` | SHA-256 helpers, logging setup |

#### `rules/` — turning a guide into rules

| File | Purpose |
|---|---|
| `interpret.py` | `interpret_guide()` — the entry: extractors → leftovers → normalize → conflicts |
| `normalize.py` | **The brain of interpretation.** Decides meaning and status of every candidate |
| `vocabulary.py` | Loads `config/vocabulary.toml` (wording → roles/scopes/statuses) |
| `directives.py` | Interprets "must / never / avoid" sentences |
| `bullet_specs.py` | Interprets "Label: value" bullet specs |
| `context.py` | Tracks section context (e.g. dark-mode section → dark scope) |
| `conflicts.py` | Finds contradictions; leaves both sides unapplied |
| `leftovers.py` | Keeps every unclaimed part of the guide so nothing is lost |

#### `plugins/` — the actual capabilities (each folder = one plugin kind)

| Folder | Interface | Built-ins |
|---|---|---|
| `sources/` | `SourceAdapter` — read a guide format | `markdown.py` (Markdown via markdown-it-py) |
| `extractors/` | `RuleExtractor` — find one kind of rule | `token_table`, `typography`, `component`, `css_block`, `bullet_spec`, `directive` |
| `artifacts/` | `ArtifactHandler` — detect and parse HTML | `static.py`, `email.py` (both thin subclasses of `html_handler.py`), plus `classifier.py`, `roles.py`, `base.py` (lxml helpers) |
| `appliers/` | `RuleApplier` — decide WHAT to change | `typography`, `color`, `component`, `surface` (all via `base.RoleStyleApplier`), `tokens.py` (page colour variables), `font.py` (font family + font source), `support.py` (what email clients cannot show) |
| `writers/` | `StyleWriter` — decide HOW to write it | `static.py` (`StylesheetWriter`), `inline.py` (`InlineWriter`) |
| `verifiers/` | `Verifier` — check the result | `contrast`, `forbidden`, `structure`, `assets` (registered); `original`, `idempotence` (built per run) |
| `reporters/` | `Reporter` — render a report | `markdown_report`, `json_report`, `guide_rules` |

#### `pipeline/` — sequencing

| File | Purpose |
|---|---|
| `bootstrap.py` | `build_registry()` — registers every built-in plugin |
| `orchestrator.py` | `Orchestrator` — runs the stages in order |
| `planning.py` | `plan_changes()`, overlap resolution, per-rule outcomes, `PlanResult.rolled_back()` |
| `verification.py` | `verify_and_roll_back()` loop, `verify_output()` |
| `finalize.py` | `finalize_rules()` — final status for every rule |

#### `server/` — the MCP layer

| File | Purpose |
|---|---|
| `__main__.py` | **Entry point** |
| `app.py` | Builds the FastMCP server, `validate_startup`, runs uvicorn |
| `tools.py` | The 5 tools + `report://{run_id}` resource |
| `auth.py` | `BearerTokenVerifier` (constant-time token compare) |
| `error_mapping.py` | `@guarded` decorator: typed errors → `[CODE] message`; unknown errors → generic message |
| `schemas.py` | Return types: `ExtractedRules`, `RuleView`, `ReportText`, `PluginList` |

#### `evaluation/` — measuring quality

`cases.py` (load `eval/expected/*.json`), `runner.py` (run each case), `metrics.py` (independent scoring — deliberately does *not* reuse the verifiers), `scorecard.py` (writes `eval/reports/scorecard.*`), `__main__.py` (CLI).

### 10.3 `config/` — change behaviour without touching code

| File | Controls |
|---|---|
| `settings.toml` | Host/port/transport, auth required, size limits, allowed input/output folders |
| `vocabulary.toml` | How guide wording maps to roles, scopes, section statuses, directive keywords, bullet specs. **Edit this to teach the tool a client's wording** |
| `roles.toml` | Which HTML elements get which role (`button.primary`, `heading.h1`, ...). First match wins |
| `token_map.toml` | Which page CSS variables (`--accent`...) get which palette token, per light/dark surface |
| `email_support.toml` | What email clients can't display (`clamp()`, `var()`, `vw`...) |

---

## 11. The most important classes, functions and plugins

### 11.1 The seven plugin kinds (the heart of the design)

```
 interface        question it answers                     example implementations
 ---------------  --------------------------------------  ------------------------------------------
 SourceAdapter    "How do I read this guide format?"       MarkdownSourceAdapter
 RuleExtractor    "Which rules of type X are in the tree?" TokenTable/Typography/Component/CssBlock/BulletSpec/Directive
 ArtifactHandler  "Is this HTML mine? parse it"            StaticArtifactHandler, EmailArtifactHandler
 RuleApplier      "WHAT should change for this rule?"      Typography/Color/Component/Surface/Token/FontFamily/FontSource
 StyleWriter      "HOW do I write the changes?"            StylesheetWriter (static), InlineWriter (email)
 Verifier         "Is the result still OK?"                Contrast, ForbiddenColor, Structure, Assets, OriginalIntact, Idempotence
 Reporter         "How do I render the report?"            Markdown, JSON, GuideRules
```

A plugin must implement **exactly one** interface and have a unique non-empty `name`
(the registry enforces this). Adding a capability = write one class + add one `registry.register(...)` line.

### 11.2 Key classes

| Class | File | Why it matters |
|---|---|---|
| `Orchestrator` | `pipeline/orchestrator.py` | Runs the whole workflow |
| `PluginRegistry` | `core/registry.py` | Finds every plugin; no code branches on format names |
| `Rule` / `RuleCandidate` | `models/rule.py` | The central data: what the guide says |
| `Change` / `Skip` | `models/change.py` | One edit / one non-edit with a reason |
| `ArtifactModel` | `models/artifact.py` | Parsed HTML + role per element + surface per element |
| `StyleIndex` | `core/cascade.py` | Answers "what is this element's colour/background?" |
| `RoleStyleApplier` | `plugins/appliers/base.py` | Shared logic for typography/color/component/surface rules |
| `StylesheetWriter` / `InlineWriter` | `plugins/writers/` | The two ways to write output |
| `RunResult` / `RunSummary` | `models/report.py` | Everything about a run / what the tool returns |

### 11.3 Key functions

| Function | File | What it does |
|---|---|---|
| `Orchestrator.run` | orchestrator.py | The whole workflow |
| `interpret_guide` | rules/interpret.py | Guide → rules + conflicts |
| `normalize` | rules/normalize.py | Candidates → clean rules (never guesses) |
| `detect_conflicts` | rules/conflicts.py | Finds contradictions |
| `classify_html` | plugins/artifacts/classifier.py | Static vs email, with evidence |
| `plan_changes` | pipeline/planning.py | Appliers → resolved, numbered changes |
| `verify_and_roll_back` | pipeline/verification.py | Undo changes that break readability |
| `finalize_rules` | pipeline/finalize.py | Final status for every rule |
| `guarded` | server/error_mapping.py | Safe error handling for every tool |
| `resolve_within` | core/paths.py | Path-traversal protection |

### 11.4 Key design ideas (read once, remember always)

| Idea | Meaning |
|---|---|
| **Extract, then normalize** | Extractors only *find*; `normalize.py` alone *decides* meaning and status. |
| **Appliers decide WHAT, writers decide HOW** | One applier serves both pages and emails. |
| **Dotted roles** | A rule for `button` applies to `button.primary` too; the more specific role wins for the properties it sets. |
| **Verify then roll back** | Contrast check blames a change; it is undone and reported as a skip. |
| **Two parses** | A pristine copy for verifiers, a working copy that the writer mutates. |
| **Never guess** | Unknown background → `unknown`; vague rule → `could_not_interpret`; contradiction → both unapplied. |
| **Idempotent** | Re-running on `branded.html` changes nothing (the tool ignores its own markers). |
| **Static output** | One `<style id="brand-compliance">` block with id-boosted selectors, so brand beats page CSS without `!important`. |
| **Email output** | Inline `style` only; Outlook conditional comments untouched; unsupported values (`clamp`, `var`, `vw`) become reported skips. |

---

## 12. How all components connect

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                      CONFIG (toml)                                       │
│  settings.toml   vocabulary.toml   roles.toml   token_map.toml   email_support.toml      │
└───────┬───────────────┬────────────────┬──────────────┬───────────────────┬──────────────┘
        │               │                │              │                   │
        ▼               ▼                ▼              ▼                   ▼
 ┌────────────┐  ┌────────────┐  ┌─────────────┐  ┌───────────┐     ┌──────────────┐
 │  Settings  │  │ Vocabulary │  │ role rules  │  │ TokenMap  │     │ EmailSupport │
 └─────┬──────┘  └─────┬──────┘  └──────┬──────┘  └─────┬─────┘     └──────┬───────┘
       │               │                │               │                  │
       │      ┌────────▼────────────────▼───────────────▼──────────────────▼────────┐
       │      │ pipeline/bootstrap.build_registry()  ->  PluginRegistry (7 kinds)    │
       │      └────────────────────────────────┬─────────────────────────────────────┘
       │                                       │
       ▼                                       ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │                          Orchestrator                               │
 │  guide ─► [SourceAdapter] ─► GuideDocument ─► [Extractors] ─►       │
 │  candidates ─► normalize ─► Rules ─► conflicts                      │
 │                                                                     │
 │  html ─► classify ─► [ArtifactHandler] ─► ArtifactModel (x2)        │
 │                                                                     │
 │  Rules + ArtifactModel ─► [Appliers] ─► Changes/Skips ─► resolve    │
 │  ─► [Verifiers: change scope] ◄─► rollback ─► [StyleWriter]         │
 │  ─► [Verifiers: output scope] ─► finalize ─► [Reporters]            │
 └──────────────────────────────▲──────────────────────────────────────┘
                                │ called by
                      ┌─────────┴─────────┐
                      │ server/tools.py   │ ◄── @guarded ◄── FastMCP ◄── auth/Host/Origin checks
                      └─────────┬─────────┘
                                │ HTTP + SSE  (127.0.0.1:8000/sse)
                                ▼
                         MCP client  ◄──── User
```

**Data shapes passed between stages**

```
 file ─► GuideDocument ─► list[RuleCandidate] ─► list[Rule] (+ list[Conflict])
 html ─► ArtifactModel ──┐
                         ├─► PlanResult(list[Change], list[Skip], outcomes) ─► VerifiedPlan(+CheckResult, rolled_back)
 list[Rule] ─────────────┘                                                      │
                                                                                ▼
                     ArtifactModel(output) ─► branded.html        RunResult ─► report.md / report.json / guide_rules.json
                                                                       └─► RunSummary (returned to the client)
```

---

## 13. Reading order

Study in this order. Each step should take roughly 20-60 minutes.

### First (understand what and why)

1. `README.md` — the product in 5 minutes.
2. `problem-statement.txt` — why it exists.
3. `docs/approach.md` — approach, limits, how success was measured.
4. `CLAUDE.md` — dense but excellent list of the architecture rules.

### Second (understand the skeleton)

5. `src/brand_compliance/core/contracts.py` — the 7 plugin interfaces. **Read this fully.**
6. `src/brand_compliance/models/` (`rule.py`, `change.py`, `artifact.py`, `report.py`) — the data vocabulary.
7. `src/brand_compliance/server/__main__.py` → `app.py` → `tools.py` — how a call enters.
8. `src/brand_compliance/pipeline/orchestrator.py` — **the most important file.** Follow `run()` line by line.
9. `src/brand_compliance/pipeline/bootstrap.py` and `core/registry.py` — how plugins are wired.

### Third (understand each stage)

10. `rules/interpret.py` → `plugins/sources/markdown.py` → one extractor (`token_table.py`) → `rules/normalize.py`.
11. `plugins/artifacts/classifier.py`, `html_handler.py`, `roles.py` and `config/roles.toml`.
12. `plugins/appliers/base.py` → `pipeline/planning.py`.
13. `plugins/verifiers/contrast.py` → `pipeline/verification.py` → `pipeline/finalize.py`.
14. `plugins/writers/static.py` and `inline.py` (compare them).

### Fourth (hands-on)

15. Run the evaluation: `PYTHONPATH=src .venv/bin/python -m brand_compliance.evaluation`, then open `eval/reports/mini-clean-page/report.md` and `branded.html`.
16. Read `tests/integration/test_orchestrator_real.py` and `test_server_http.py`.
17. Skim `docs/plugin-guide.md`, then try adding a tiny plugin.
18. Reference only when needed: `core/cascade.py`, `rules/bullet_specs.py`, `rules/directives.py` (large and detailed), `docs/DEVELOPMENT-GUIDE.md` (the full build story).

---

## 14. Safe changes vs risky areas

### 14.1 Generally safe

| Change | Why it is safe |
|---|---|
| Edit `config/vocabulary.toml` to teach new wording | Designed for this; no code. Re-run the evaluation after. |
| Edit `config/roles.toml` (new element → role mappings) | Config only; keep specific roles above general ones (first match wins) |
| Edit `config/settings.toml` (port, limits, folders) | Config; keep loopback + auth on |
| Add a new plugin (reader, extractor, verifier, reporter) | One class + one `register(...)` line; no core changes |
| Add a new `Reporter` format | Declares its own `filename`; orchestrator picks it up |
| Add a new `Verifier` | Declare `scope`; orchestrator runs it automatically |
| Add tests, docs, evaluation cases | No behaviour change |
| Improve log messages (without content) | Keep the "ids and counts only" rule |

### 14.2 Handle with care

| Area | Risk | Guard |
|---|---|---|
| `rules/normalize.py`, `rules/conflicts.py` | Changing meaning of rules changes every report | Run the evaluation set; expected outcomes are hand-written |
| `plugins/appliers/*` | New edits may collide with overlap logic | Keep appliers read-only (they return `Change`s, never edit the DOM) |
| `pipeline/planning.py` (overlap resolution) | Wrong winner = wrong styling | Unit tests + evaluation |
| `plugins/writers/*` | Output markup and idempotence | Idempotence verifier + `core/markers.py` |
| `config/token_map.toml` | A wrong mapping changes many colours; never add a variable the page doesn't define | Contrast verifier catches readability |
| `config/email_support.toml` | Too permissive = broken emails | Test in the email cases |

### 14.3 Risky: avoid unless you really know why

| Area | Why it is risky |
|---|---|
| `server/auth.py`, `server/app.py::validate_startup`, Host/Origin protection | Security: this server edits files on the host, so weakening auth/loopback is dangerous |
| `core/paths.py` (`resolve_within`) | The path-traversal guard; bugs allow reading/writing outside allowed folders |
| `server/error_mapping.py` | Prevents leaking paths/stack traces to clients |
| `OriginalIntactVerifier` and output-dir validation | "Never destroy the original" is a core promise |
| `core/cascade.py` | Subtle CSS logic; many verifiers depend on it; "unknown, never guess" must remain true |
| `core/contracts.py` | Changing an interface breaks every plugin |
| `core/registry.py` | "Exactly one interface per plugin" rule |
| Adding `if artifact_type == "email"` branches in core/pipeline | Breaks the plugin architecture; add a plugin instead |
| Adding AI/LLM calls | Breaks determinism and confidentiality; if ever added, only as a flagged `ai_assisted` extractor that never edits HTML |
| Logging guide/page content | Violates confidentiality |
| Editing `myridius-brand-guide.md` | Eval cases depend on its deliberate contradictions and subjective rules |

### 14.4 Rules of thumb

1. Don't edit `output/` or `eval/reports/` by hand: regenerate them.
2. If you change behaviour on purpose, `tests/integration/test_evaluation_set.py` will fail. Update `eval/expected/*.json` **by hand from the guide** (never copy the tool's output), then rerun the evaluation.
3. Keep `models/` free of app imports and `core/` importing only `models/`.
4. Before every commit: `ruff check . && ruff format .`, `mypy`, `pytest` (≥ 80% coverage).

---

## 15. MCP servers, clients, tools, APIs, pipelines, agents

### 15.1 What is MCP, quickly

**MCP (Model Context Protocol)** is a standard way for AI assistants (clients) to call external programs (servers) that expose **tools**.
Here, this project is the **server**; Claude Code (or another AI app) is the **client**.

```
  AI assistant (MCP client)  ──tool call──►  MCP server (this project)  ──►  does real work on files
         ▲                                                                       │
         └─────────────────────────── structured result ◄────────────────────────┘
```

### 15.2 The one MCP server in this repo

| Item | Value |
|---|---|
| Name | `brand-compliance` |
| Library | FastMCP (v4; uses `httpx2`) |
| Transport | **HTTP + Server-Sent Events (SSE)**, not stdio |
| Endpoint | `http://127.0.0.1:8000/sse` (`/mcp` if transport is set to `http`) |
| Auth | Bearer token (`BRAND_MCP_AUTH_TOKEN`, ≥ 16 chars), checked in constant time |
| Protections | Host header check (421), Origin check (403), loopback-only default, refuses unsafe config at startup, `mask_error_details=True` |
| Server instructions (shown to clients) | "call classify_artifact, then apply_brand, then read the report with get_report" |

### 15.3 MCP clients

This repo contains **no client code of its own**. Clients are:

| Client | How it connects |
|---|---|
| Claude Code | `claude mcp add --transport sse ... --header "Authorization: Bearer <token>"` (exact command in `docs/tools.md`). Claude Code connects by URL; it does **not** start the server. |
| Python script | `fastmcp.Client("http://127.0.0.1:8000/sse", auth="<token>")` (example in `docs/tools.md`) |
| Tests | `tests/integration/test_server_http.py` starts the real HTTP app and talks to it |

### 15.4 The tools (and the resource)

| Tool | Read-only? | Inputs | Output | Purpose |
|---|---|---|---|---|
| `apply_brand` | writes files | `guide_path`, `artifact_path`, `output_dir="output"`, `artifact_type?` | `RunSummary` | Main tool: brand one artifact |
| `extract_rules` | read-only | `guide_path`, `status?`, `limit` (1-1000, default 500) | `ExtractedRules` | See how a guide is read (no HTML touched) |
| `classify_artifact` | read-only | `artifact_path` | `Classification` | Static page or email, and evidence |
| `get_report` | read-only | `run_id`, `format` = markdown or json | `ReportText` | Fetch a saved report |
| `list_plugins` | read-only | none | `PluginList` | What is loaded |
| resource `report://{run_id}` | read-only | `run_id` | Markdown text | Same as `get_report`, as an MCP resource |

**Error format:** `[CODE] message`, with codes `INVALID_INPUT`, `UNSUPPORTED_FORMAT`, `PARSE_FAILED`, `PATH_NOT_ALLOWED`, `PLUGIN_ERROR`, `CONFIGURATION_ERROR`, `INTERNAL_ERROR`.

### 15.5 Pipelines

The project has two pipelines:

1. **The branding pipeline** — the 18-step workflow in section 5 (guide → rules → plan → verify → write → check → report).
2. **The evaluation pipeline** (`evaluation/`) — runs each case in `eval/expected/*.json` through the same `Orchestrator`, then scores the results with independent code (rule-status accuracy, expected edits made, unexpected changes, content/fidelity/idempotence). Results go to `eval/reports/scorecard.md`. Current result per README: 12/12 cases pass, 75/75 rules in the right status, 100/100 expected edits, 0 of 360 changes unexpected.

### 15.6 Agents, AI, external APIs

| Question | Answer |
|---|---|
| Does it use an LLM or AI agent? | **No.** Everything is deterministic code. |
| Cloud/external API calls? | **None.** Fully local. |
| Any future AI hook? | Allowed only as a plugin flagged `ai_assisted` (the field exists on `Rule`/`RuleCandidate`) that proposes rules and **never edits HTML**. |
| External plugin mechanism | Python entry points, group `brand_compliance.plugins` (loaded in `load_entry_point_plugins`; a broken plugin is logged and skipped) |

### 15.7 Third-party libraries (what each is for)

| Library | Used for |
|---|---|
| `fastmcp` | The MCP server framework |
| `uvicorn` | Runs the ASGI app |
| `pydantic` / `pydantic-settings` | Data models and settings |
| `lxml` | HTML parsing and editing |
| `tinycss2` | CSS parsing |
| `markdown-it-py` | Markdown guide parsing |

---

## 16. Commands cheat sheet and further reading

Run from `evoq_R-D/`.

```bash
# Setup
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt

# Start the server (creates .env token on first run; uses myenv/)
./scripts/start-mcp-server.sh
# or by hand
export BRAND_MCP_AUTH_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
PYTHONPATH=src .venv/bin/python -m brand_compliance.server     # http://127.0.0.1:8000/sse

# Quality
.venv/bin/pytest                      # all tests, fails under 80% coverage
.venv/bin/ruff check . && .venv/bin/ruff format .
.venv/bin/mypy                        # strict

# Evaluation (12 cases; exit 0 only if all pass; writes eval/reports/)
PYTHONPATH=src .venv/bin/python -m brand_compliance.evaluation
```

Run the workflow without a server (Python):

```python
from brand_compliance.core.settings import load_settings
from brand_compliance.pipeline.bootstrap import build_registry
from brand_compliance.pipeline.orchestrator import Orchestrator
from brand_compliance.rules.vocabulary import load_vocabulary

settings, vocabulary = load_settings(), load_vocabulary()
summary = Orchestrator(build_registry(settings, vocabulary), settings, vocabulary).run(
    "myridius-brand-guide.md", "eval/artifacts/mcp-servers-report-simple-v2.html", "output")
print(summary.message, summary.output_dir)
```

Gotchas:

- Settings override: `BRAND_MCP_<SECTION>__<NAME>` environment variables.
- `GET / 404` in the server log is harmless; only `/sse` is served.
- If `.env` is deleted, a new token is generated and clients must be re-registered.
- Two venvs exist: `.venv/` (dev tools) and `myenv/` (runtime only). Check which exists before running.
- Python must be 3.12 (`>=3.12,<3.13`).

Other docs:

| Document | For |
|---|---|
| [approach.md](approach.md) | Approach, limitations, how success was measured |
| [tools.md](tools.md) | Connecting a client; every tool, input, output, error code |
| [architecture.md](architecture.md) | Layers, data flow, design decisions |
| [plugin-guide.md](plugin-guide.md) | Adding a guide format, rule finder, check or report format |
| [DEVELOPMENT-GUIDE.md](DEVELOPMENT-GUIDE.md) | The full step-by-step build story |

Known limits (from the README): Markdown guides only; no visual rendering check; Outlook conditional comments
(including VML buttons) are left untouched; only one evaluation case uses real material.

---

## 17. Glossary

| Term | Meaning |
|---|---|
| **MCP** | Model Context Protocol: how AI apps call external tools |
| **FastMCP** | Python library for building MCP servers |
| **SSE** | Server-Sent Events: the streaming HTTP transport used here |
| **Artifact** | The HTML file being branded (static page or email) |
| **Guide** | The brand guide (Markdown) |
| **Source adapter** | Reader that turns a guide format into a `GuideDocument` tree |
| **Extractor** | Finds one kind of rule candidate in that tree |
| **Candidate** | A raw finding with exact guide lines, not yet interpreted |
| **Rule** | A cleaned rule with category, role, property, value, scope, status, reason |
| **Role** | A label for an HTML element, e.g. `button.primary`, `heading.h1` (from `config/roles.toml`) |
| **Surface** | The background an element sits on: light, dark or unknown |
| **Applier** | Plans WHAT to change for a rule category |
| **Writer** | Decides HOW to write the changes (stylesheet vs inline) |
| **Verifier** | A check on the plan or the output |
| **Rollback** | Undoing a planned change that a verifier blames |
| **Idempotent** | Running twice gives the same result as running once |
| **Token** | A named palette value from the guide, e.g. `--digital-pavo` |
| **Run** | One `apply_brand` call; results live in `output/run-<time>-<hex>/` |
| **Contrast ratio** | WCAG readability measure; 4.5:1 is the minimum for normal text here |
