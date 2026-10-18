# Development Guide: Brand Compliance MCP

> **Who this is for:** anyone (including a future version of the assistant that has lost the
> chat history) who needs to understand *what was built, step by step, which file does what, why it
> exists, and where it is used*.
> **How it is written:** plain language first, technical names second.
> **Keep it alive:** this file is updated after every step. **All 14 steps are done and this guide
> had its final full pass after Step 14**; keep it in sync with any later change (see
> [Maintenance](#maintenance-checklist)). Reader's map of the other documents: `README.md` (start here),
> `docs/approach.md` (the short write-up), `docs/tools.md`, `docs/architecture.md`, `docs/plugin-guide.md`.

---

## 1. The project in one minute

**The business problem.** Teams make HTML pages and marketing emails. Each client has brand rules
(colours, fonts, button shapes, logo placement). Today a person reads the brand guide and restyles
the HTML by hand. That is slow, inconsistent, and leaves no record of what changed or why.

**The solution.** A service, exposed as an **MCP server** (built with FastMCP), that takes
**one brand guide + one HTML file**, restyles a *copy* of the HTML automatically, and writes a report
that says exactly:

1. what it changed (where, before, after, and which guideline caused it);
2. what it understood but **could not apply**, and why;
3. what it **could not interpret**;
4. where the guide **contradicts itself**.

**The promises the system keeps (never break these):**

| Promise | How it is enforced |
|---|---|
| **Never guess.** If a rule is unclear, say so. | Every rule ends in a status with a reason; nothing is "best-guessed" |
| **The original is never modified.** | Output goes to a new folder; the source file's SHA-256 is checked before and after |
| **Output stays usable.** | Verifiers check contrast, structure, assets; bad changes are undone; unusable output is withheld |
| **Everything is local.** | No cloud calls, no AI model: all parsing and editing is deterministic code |
| **Everything is traceable.** | Each change names its rule, the rule names its line in the guide |
| **No invented logo.** | A logo is only ever applied from a supplied asset (V1: none, so it is reported as not applied) |

**Decisions the project owner made** (do not revisit without asking):

| Topic | Decision |
|---|---|
| Python | 3.12 |
| Where data is processed | Local only |
| Ambiguity | Say "could not interpret / could not apply"; never guess |
| Transport | **HTTP + SSE** (a URL), *not* stdio |
| Per operation | One guide + one HTML artifact |
| Logo | Do not invent one |
| Fonts | Montserrat everywhere, with a fallback stack |
| Outputs | A local folder |
| Priority | Get the V1 end-to-end workflow working first |
| Code style | `custom-best-practices.txt` (PEP 8, 88 cols, type hints, pytest, `src/` layout, tests mirror `src/`) |
| Communication | Explain every step in simple language: what is being built, where, why |

---

## 2. Status at a glance

| Step | What | Status |
|---|---|---|
| 1 | Project skeleton, tooling | ✅ Done |
| 2 | Data models, plugin interfaces, registry, errors | ✅ Done |
| 3 | Shared utilities (colour, contrast, CSS, units, paths, hashing, settings) | ✅ Done |
| 4 | Markdown guide reader | ✅ Done |
| 5 | Rule finders + normalizer (+ bullet-spec extension) | ✅ Done |
| 6 | Conflict detector | ✅ Done |
| 7 | Artifact side: parse, classify, roles, surfaces | ✅ Done |
| 8 | Appliers, overlap resolution, stylesheet writer | ✅ Done |
| 9 | Verifiers + rollback | ✅ Done |
| 10 | Orchestrator, final statuses, reporters (first end-to-end run) | ✅ Done |
| 11 | MCP server over HTTP + SSE | ✅ Done |
| 12 | Email support (handler, inline writer, email-support table) | ✅ Done |
| 13 | Evaluation set, metrics, sample reports | ✅ Done |
| 14 | Final docs and the short write-up (approach, limits, how success is measured) | ✅ Done |

**Final quality numbers:** 695 tests collected (694 pass, 1 conditional skip), 98% coverage, `ruff` and strict `mypy` clean; **evaluation: 12 of 12 cases pass**.
**All steps are complete.** Nothing has been committed to git yet.

---

## 3. The big picture

### 3.1 How data flows (one `apply_brand` call)

```
MCP client (e.g. Claude Code)
   │  HTTP + SSE, bearer token
   ▼
server/tools.py  ── validates input, maps errors ──►  pipeline/orchestrator.py
                                                              │
   ┌──────────────────────────────────────────────────────────┤
   ▼                                                          ▼
GUIDE SIDE                                               ARTIFACT SIDE
plugins/sources      read guide → GuideDocument tree     plugins/artifacts   classify static|email,
plugins/extractors   find rules  → RuleCandidates                            parse, label roles, find surfaces
rules/normalize      clean rules → Rules (+statuses)
rules/conflicts      find contradictions
   └───────────────────────────────┬──────────────────────────┘
                                   ▼
                plugins/appliers   decide WHAT to change   → Changes (+ skips)
                pipeline/planning  resolve overlaps        → one change per element+property
                plugins/verifiers  contrast / forbidden colour → undo bad changes (rollback loop)
                plugins/writers    decide HOW to write it  → branded copy
                plugins/verifiers  structure / assets / original / idempotence
                pipeline/finalize  give every rule its final status
                plugins/reporters  report.md, report.json, guide_rules.json
                                   ▼
        output/<run_id>/  branded.html · report.md · report.json · guide_rules.json
```

### 3.2 The layers (a layer may only use layers below it)

```
1. server/      MCP tools, token + Host/Origin checks, error mapping     (thin: no logic)
2. pipeline/    orchestrator, planning, verification loop, final statuses
3. rules/       turn candidates into rules, detect contradictions
4. plugins/     everything that can grow: sources, extractors, artifacts, appliers,
                writers, verifiers, reporters
5. core/        shared helpers + plugin interfaces + registry
   models/      pure data shapes (imports nothing else from the app)
```

`models/` is a leaf. `core/` may import only `models/`. Plugins never import from `pipeline/` or
`server/`. (One slip against this rule was caught and fixed in Step 10.)

### 3.3 The plugin idea (why new features need no rewrites)

Every kind of "thing that can grow" is a **plugin** that implements one small interface (a
`typing.Protocol` in `core/contracts.py`) and is found through `core/registry.py`. Core code never
says `if format == "pdf"`; it asks the registry "who can handle this?". Adding PDF support later =
add one reader file; nothing else changes.

The seven plugin kinds: `SourceAdapter` (guide readers), `RuleExtractor` (rule finders),
`ArtifactHandler` (static/email), `RuleApplier` (decide *what* to change), `StyleWriter` (decide
*how* to write it), `Verifier` (checks), `Reporter` (report formats).

### 3.4 The final status of every rule

After a run, **every** rule has exactly one status (never "pending"):

| Status | Meaning |
|---|---|
| `applied` | Understood and acted on, or enforced by a check (with the evidence as the reason) |
| `understood_not_applicable` | Understood but could not be applied here (no such element, rolled back for contrast, deferred in V1, logo with no asset…) |
| `could_not_interpret` | Subjective, vague, or unsupported wording |
| `conflict_unresolved` | The guide contradicts itself; **neither side is applied** |
| `reference` | A definition (palette token, variable) used by other rules; nothing to apply by itself |
| `pending` | Internal only, before the final decision. Must not survive a run |

---

## 4. Step-by-step journal

Each step lists: **what & why**, **files** (what each does, where it is used), **decisions**, and
**problems found along the way** (because they explain odd-looking code).

### Step 1 — Project skeleton

**What & why.** An empty but fully working Python 3.12 project where lint, type checks and tests
already run, so every later step is checked automatically from day one.

| File | What it does / where it is used |
|---|---|
| `pyproject.toml` | Project definition. Configures `ruff` (PEP 8, 88 columns), strict `mypy`, `pytest` (fails below 80% coverage). Also disables mypy's `type-abstract` check: plugin lookup passes Protocol classes as `type[T]` and mypy wrongly objects |
| `requirements.txt` | Pinned **runtime** libraries (fastmcp, pydantic, lxml, tinycss2, markdown-it-py, css-inline, uvicorn, …) |
| `requirements-dev.txt` | Pinned dev tools (pytest, ruff, mypy, pre-commit, httpx2) + includes the runtime file |
| `.gitignore`, `.pre-commit-config.yaml` | Keep venv/output/caches out of git; run ruff + mypy before commits |
| `config/settings.toml` | Default settings (server host/port/transport, size limits, allowed folders). See Step 3 |
| `src/brand_compliance/core/logging.py` | `configure_logging()`: one logging format for the whole app. Rule: logs never contain guide or artifact content |
| `tests/conftest.py` | Shared test fixtures (the only place fixtures may live) |
| `CLAUDE.md` | Guidance for future assistant sessions (commands, architecture rules). Written after Step 1 as agreed |

**Decisions.** `uv` was not installed, so a normal `python3.12 -m venv .venv` + `pip` is used.

---

### Step 2 — Data models, plugin interfaces, registry, errors

**What & why.** The shared "language" of the system. Components only talk to each other through
these shapes, which keeps them independent and testable.

| File | What it does / where it is used |
|---|---|
| `models/source.py` | `SourceSpan`: exactly where a fact came from (file, line/page, heading path). Gives every rule and change a pointer back to the guide |
| `models/guide.py` | `GuideDocument` / `GuideNode`: the **format-neutral tree** every guide format is converted into (sections, paragraphs, list items, tables with per-row line numbers, code blocks) |
| `models/rule.py` | `Rule`, `RuleCandidate`, `RuleStatus`, `Scope`, `Severity`. `RuleStatus` deliberately has no "guessed" value |
| `models/artifact.py` | `ArtifactModel` (the parsed HTML copy + roles + surfaces), `ArtifactType`, `Detection`, `Classification` |
| `models/change.py` | `Change` (one edit: where, before, after, rule), `Skip` (a place a rule was skipped, with a reason), `ApplyResult` (changes + skips + `satisfied` count), `ROLLED_BACK_PREFIX` |
| `models/conflict.py` | `Conflict` (a contradiction between rules; `resolved` only if the guide itself states the exception) |
| `models/report.py` | `CheckResult`, `RunResult`, `RunStatus`, `RunSummary`, `Report`; `SCHEMA_VERSION` |
| `core/contracts.py` | The seven plugin interfaces |
| `core/registry.py` | `PluginRegistry`: register / find / get / describe; `register(..., replace=True)` to override a built-in; loads external plugins through Python entry points (`brand_compliance.plugins`); a broken plugin is logged and skipped |
| `core/errors.py` | Typed errors with stable codes: `INVALID_INPUT`, `UNSUPPORTED_FORMAT`, `PARSE_FAILED`, `PATH_NOT_ALLOWED`, `PLUGIN_ERROR`, `CONFIGURATION_ERROR` |

**Decisions.** `models/` is a leaf package; `core/` may import `models/`. Contracts changed twice
later on purpose: `RuleApplier.plan()` returns `ApplyResult` (Step 8) and `Reporter` gained
`filename` (Step 10).

---

### Step 3 — Shared utilities

**What & why.** Small reusable helpers written once (DRY) because many plugins need them.

| File | What it does / where it is used |
|---|---|
| `core/color.py` | Reads `#hex`, `rgb()`, `hsl()` and a few names into one `Color`. Unknown notation raises an error (never guessed). Used by the normalizer, cascade, contrast |
| `core/contrast.py` | WCAG contrast ratio, `meets_aa`, `is_light_surface`. Used by the contrast verifier and surface detection |
| `core/css.py` | Parse/format/merge `style="…"` declarations. Used by appliers and the cascade |
| `core/units.py` | Convert `rem/em/pt` to px; refuses `clamp()`/`vw`/`%` instead of guessing. Needed for the email path |
| `core/paths.py` | `resolve_within`, `validate_input_file`, `validate_output_dir`: allowed folders, size, type, symlink/`../` safe, never overwrite inputs. Used by the orchestrator |
| `core/hashing.py` | SHA-256 of files/bytes: proves the original is unchanged |
| `core/settings.py` | `Settings` (pydantic-settings): defaults from `config/settings.toml`, overridden by `BRAND_MCP_<SECTION>__<NAME>` env vars; the auth token comes from env only (`BRAND_MCP_AUTH_TOKEN`) |

**Finding.** The guide's HSL values are rounded; hex is the source of truth.

---

### Step 4 — Markdown guide reader

**What & why.** The first guide reader: turns `myridius-brand-guide.md` into the `GuideDocument`
tree, keeping a line number for every piece. Later PDF/JSON/URL readers must produce the same tree.

| File | What it does / where it is used |
|---|---|
| `plugins/sources/base.py` | `read_source_text`: checks type, size, UTF-8 for any text-based reader |
| `plugins/sources/markdown.py` | `MarkdownSourceAdapter` using `markdown-it-py`: nested sections by heading, tables with header/rows/**row line numbers**, code blocks with language, list items (read once, nested lists included) |
| `plugins/sources/__init__.py` | `register_sources()`: add one line per new format |

**Real guide result:** 39 sections, 8 tables, 12 code blocks. **Bug caught:** list items could be
read twice (a hidden paragraph inside tight lists); fixed.

---

### Step 5 — Rule finders and the normalizer

**What & why.** Turn the tree into **rules**. Two stages: *extractors* only **find** things and
record the exact guide line; the *normalizer* alone **decides what they mean** and their status.

| File | What it does / where it is used |
|---|---|
| `core/text.py` | `clean_text` (strip Markdown marks), `split_top_level` (split on commas outside parentheses) |
| `config/vocabulary.toml` | **The word list**: guide wording → standard roles (`"primary (cta)"` → `button.primary`), type tokens → roles, selectors → roles, effect words, scope words, "sections that cannot be applied" with reasons, and the **bullet-spec table**. Edit this to teach the system a new client's wording; no code change |
| `rules/vocabulary.py` | Loads/validates the vocabulary (a typo in a spec kind fails at load) |
| `plugins/extractors/base.py` | `column_index`, `row_span`, `CandidateFactory` shared by finders |
| `plugins/extractors/token_table.py` | Colour tables (Token + Hex) |
| `plugins/extractors/typography.py` | The type-scale table |
| `plugins/extractors/component.py` | Component tables whose first column is `Variant` (buttons) |
| `plugins/extractors/css_block.py` | Declarations/imports in `css` code blocks and inline `style="…"` in `html` blocks, with exact line numbers |
| `plugins/extractors/directive.py` | NEVER/ALWAYS/MUST sentences, Do/Don't tables, and (Step 6) keyword lines inside untagged code blocks |
| `plugins/extractors/bullet_spec.py` | `Label: value` bullets that the vocabulary lists (see "extension" below) |
| `plugins/extractors/__init__.py` | `register_extractors()` |
| `rules/context.py` | The normalizer's notebook: palette so far, font stack, CSS variables; resolves values like `--leaf (on light) / --linen (on dark)`; border/shadow/colour readers |
| `rules/normalize.py` | Turns candidates into `Rule`s, merges duplicates (with an "also stated at…" note), applies section statuses from the vocabulary, numbers rules `R001…` |
| `rules/directives.py` | Reads supported sentence shapes: min contrast, forbidden colour on a role, "use X exclusively", "no other font families", forbidden effect, default surface, focus ring, font exception. Anything else is *reported*, not guessed |
| `rules/leftovers.py` | Keeps **every** paragraph/bullet/row/code line nobody claimed, so nothing is silently dropped (a test enforces this) |
| `rules/interpret.py` | `interpret_guide()`: extractors → leftovers → normalizer → conflicts. Returns `GuideInterpretation(rules, conflicts)` |

**Extension done in this step (bullet specs).** Specs written as bullets (button padding/shape/font,
input styles, label/helper fonts, section 3.3 text styles with colours per light/dark) became
exact rules via `rules/bullet_specs.py`, which has seven readers: `radius_variable`, `size_padding`,
`font_spec`, `box_pairs`, `declarations`, `padding_axes`, `variants_unresolved`, plus `text_style`
(Step 8). Honest limits remain: "12px (modern) or 8px (compact)", "sits above input", "Bold (700+)",
ranges and vague phrases stay *could not interpret*.

**Problems caught.** An HSL "inconsistency" was only rounding (now noted only if beyond rounding;
only `--neural-beam` genuinely disagrees). "No gradients" was wrongly read from the *logo* table
(topic-specific rows are no longer made global). Several edits silently failed because `ruff format`
had reshaped the target text; the rule since: bound every edit and assert it applied.

---

### Step 6 — Conflict detector

**What & why.** Find contradictions inside the guide and **never pick a winner**.

| File | What it does |
|---|---|
| `models/conflict.py` | The `Conflict` shape |
| `rules/conflicts.py` | `detect_conflicts()`: (1) a forbidden effect used elsewhere, (2) "only font X" broken elsewhere, (3) same role + property + overlapping scope with different values. Unresolved ⇒ both applicable sides become `conflict_unresolved` and are not applied. Rules with no target role are not compared (except named tokens) |

**Real guide result — 3 contradictions:**

| Id | What | Outcome |
|---|---|---|
| C001 | "No gradients" (line 394) vs the gradient card (line 202) | **Unresolved** |
| C002 | "Montserrat only" vs Caveat | **Resolved by the guide itself** (line 194 says Caveat only in developer docs/templates) |
| C003 | Focus-ring offset 2px (line 228) vs 4px (line 460, in the Master Prompt) | **Unresolved** |

Not detected: logo "bottom-left" vs nav "logomark left" (both prose; the logo is not applied in V1).
To catch C003 the directive finder now reads keyword lines inside untagged code blocks (the Master
Prompt), and the leftover collector keeps unclaimed code lines as grouped runs.

---

### Step 7 — The artifact side (parse, classify, roles, surfaces)

**What & why.** Answer three questions about the HTML: *what kind is it* (web page or email), *what
is each element* (heading, body text, primary button…), *what colour is behind each piece of text*.

| File | What it does / where it is used |
|---|---|
| `eval/artifacts/mcp-servers-report-simple-v2.html` | **The user's real sample page** (static; 71 CSS variables, 3 Google fonts, SVG icons, scripts, JSON data, dark theme) |
| `eval/artifacts/sample-marketing-email.html` | **Synthetic** sample email I wrote (table layout, Outlook conditionals). *Replace/add real emails for a proper evaluation* |
| `core/svg.py` | `restore_svg_case`: lxml lowercases `viewBox`; this restores SVG attribute/tag case so we hand back the author's markup |
| `core/cascade.py` | `StyleIndex`: a small CSS cascade reader. Reads **base** styles only (`@media` is counted, not evaluated); resolves `var()` from `:root`; finds the colour behind an element and where it came from; blends translucent backgrounds; `with_overrides` answers "what would it look like after these edits?"; unresolvable ⇒ `unknown`, never a guess; ignores the tool's own `<style id="brand-compliance">` |
| `plugins/artifacts/base.py` | Parse/serialize HTML (keeps doctype), `element_path`, `describe_element`, `is_content_element`, `has_own_text` |
| `plugins/artifacts/classifier.py` | Static vs email from weighted signals (layout tables, Outlook comments, scripts, landmarks…). Close calls are flagged **ambiguous** and take the safer email path. `classify_text()` helper |
| `config/roles.toml` | Priority-ordered selector→role list (first match wins) + `[[aliases]]` (rule role → element role). A button is `button.primary` only if its markup says so |
| `plugins/artifacts/roles.py` | `map_roles`, `load_role_rules`, `load_role_aliases`; lists text elements with no role as "unmapped" |
| `plugins/artifacts/static.py` | `StaticArtifactHandler`: builds the `ArtifactModel` (tree, styles, roles, surfaces light/dark/unknown, notes) |
| `plugins/artifacts/__init__.py` | `register_artifacts()` |

**Real page result:** classified static (6 signals); roles: 4 `h1`, 9 `h2`, 2 primary buttons,
7 plain buttons, 4 eyebrows, 14 body-text; 34 text elements left unmapped and listed.

---

### Step 8 — Appliers, overlap resolution, stylesheet writer

**What & why.** The first step that changes HTML. *Appliers* decide **what** to change; the *writer*
decides **how** to write it. Chosen approach: **brand rules per role** (not remapping the page's own
CSS variables, which would mean guessing what `--accent` means).

| File | What it does / where it is used |
|---|---|
| `plugins/appliers/base.py` | `RoleStyleApplier`: dotted roles (`button` rule reaches `button.primary`), aliases, surface scope, "already matches" (`satisfied`), inline-style detection (⇒ `important`), honest skip reasons |
| `plugins/appliers/typography.py`, `color.py`, `component.py`, `surface.py` | Thin subclasses that claim rule categories |
| `plugins/appliers/font.py` | `FontFamilyApplier` (brand font on the body **and every element declaring another font**), `FontSourceApplier` (web-font stylesheet as a normal change) |
| `plugins/appliers/__init__.py` | `register_appliers(registry, aliases)` |
| `pipeline/planning.py` | `plan_changes()`: runs appliers, **one change per element+property** (more specific role wins, then scoped, then later rule; the loser is recorded as a skip), numbers changes `CH001…` in document order, decides each rule's outcome; `PlanResult.rolled_back()` (Step 9) |
| `plugins/writers/static.py` | `StylesheetWriter`: marks elements with `data-brand-role` / `data-brand-surface` / `data-brand-force`, writes one `<style id="brand-compliance">` with an id-boosted selector (`html:not(#brand-compliance) [data-brand-role="…"]`) so brand rules beat page CSS **without `!important`**; `!important` only on the one element with an inline style; font `<link>`; light-mode-only wrapper + `:not([data-theme="dark"])` when the page has dark variants; replaces its own earlier output (re-runs are byte-identical) |
| `core/markers.py` | The names the tool writes into artifacts, so it can recognise its own output |
| `plugins/writers/__init__.py` | `register_writers()` |

**Problems caught.** Running the tool on its own output would have **deleted the branding** (zero
changes ⇒ old block removed); fixed by ignoring our own block/link when planning and by never
removing output unless something new is written. `!important` leaked onto a whole role; fixed with
per-element `data-brand-force`. A "text colour on light" gap was closed by reading section 3.3.

---

### Step 9 — Verifiers and rollback

**What & why.** Prove the output is still usable and undo changes that are not.

| File | What it checks |
|---|---|
| `plugins/verifiers/contrast.py` | Every text element ≥ the guide's minimum (4.5:1) **as it would look after the edits** (uses the cascade overlay). Blames the change to undo: text colour first, then background. A failure the page **already had** is reported, not blamed |
| `plugins/verifiers/forbidden.py` | No banned colour on the role/surface the guide names |
| `plugins/verifiers/structure.py` | Same elements, attributes, text, comments (Outlook conditionals), scripts, doctype, in order; only the tool's own additions allowed |
| `plugins/verifiers/assets.py` | No image/link/srcset/CSS-url lost or unexpectedly added; every `#anchor` still has its target |
| `plugins/verifiers/original.py` | Source file fingerprint unchanged (built per run) |
| `plugins/verifiers/idempotence.py` | Running on its own output gives the same output (built per run) |
| `plugins/verifiers/__init__.py` | `register_verifiers()` (the stateless four). Each verifier declares a `scope`: `"changes"` (judges the plan; may name changes to undo) or `"output"` (the default; judges the written file). The orchestrator runs **every registered verifier of each scope**, so a new verifier needs no orchestrator change (added in Step 14) |
| `pipeline/verification.py` | `verify_and_roll_back()` (loop until clean) and `verify_output()` |

**Real result:** of 205 planned changes, **6 undone**: 4 teal eyebrows on linen (**2.74:1**) and
2 white-on-teal primary buttons (**3.03:1**). The guide's own brand teal fails its own 4.5:1 rule;
this is handled automatically and explained in the report.

---

### Step 10 — Orchestrator, final statuses, reporters

**What & why.** The first complete product: one call runs every stage and writes the outputs.

| File | What it does / where it is used |
|---|---|
| `pipeline/orchestrator.py` | `Orchestrator.run()` plus read-only `extract_rules()`, `classify_file()`, `read_report()`. Validates paths, names runs `run-<UTC time>-<6 hex>`, never reuses a run folder, works on **two parses** (pristine for verifiers, working for the writer), withholds `branded.html` if an output check fails (reports still written); gives a clear error if no handler/writer exists for the artifact type (email was refused until Step 12) |
| `pipeline/finalize.py` | Final status for every rule; definitions ⇒ `reference`; rules enforced by a check ⇒ `applied` with the check's evidence; unsupported categories ⇒ not applicable "deferred" |
| `pipeline/bootstrap.py` | `build_registry()`: registers every built-in plugin + external entry points |
| `plugins/reporters/markdown_report.py` | `report.md`: summary, verification, applied rules, **change log**, not applied, could not interpret, contradictions, reference definitions, rolled back, other skips, unmapped elements, notes |
| `plugins/reporters/json_report.py` | `report.json` (machine-readable; `schema_version`) |
| `plugins/reporters/guide_rules.py` | `guide_rules.json`: every rule with its final status + conflicts, so a person can audit how the guide was read |
| `plugins/reporters/base.py`, `__init__.py` | Table/escape helpers, plain-words descriptions (`what()`), `register_reporters()` |

**Real result (329 rules, final):** applied 33 · understood-not-applied 162 · could-not-interpret 95 ·
conflict 4 · reference 35; 199 changes; all 6 checks pass. (When Step 10 first ran, the counts were 149 and 108;
Step 13 moved 13 logo/wave/icon lines from "could not interpret" to "understood but not applied".) **Decision to confirm with the owner:**
a fifth status `reference` was added so definitions are not counted as "applied".
**Bug caught:** `report.json` listed reporter *names* instead of file names; reporters now declare `filename`.

---

### Step 11 — MCP server over HTTP + SSE

**What & why.** Expose everything as MCP tools.

| File | What it does / where it is used |
|---|---|
| `server/app.py` | `create_server()` (FastMCP with `mask_error_details=True`), `validate_startup()` (refuses missing/short token, never an open server beyond localhost), `build_http_app()` (Host/Origin protection on), `endpoint_url()`, `serve()` |
| `server/tools.py` | Five tools — `apply_brand`, `extract_rules`, `classify_artifact`, `get_report`, `list_plugins` — and the `report://{run_id}` resource; each wrapped by `@guarded` |
| `server/auth.py` | `BearerTokenVerifier`: one pre-shared token, constant-time comparison |
| `server/error_mapping.py` | `@guarded`: typed error ⇒ `ToolError("[CODE] message")`; anything unexpected ⇒ generic `[INTERNAL_ERROR]` (details only in the server log) |
| `server/schemas.py` | Output shapes (`RuleView`, `ExtractedRules`, `PluginList`, `ReportText`) |
| `server/__main__.py` | `python -m brand_compliance.server` (exit code 2 on a configuration error) |

**Verified on a real socket:** no/wrong token ⇒ 401; wrong `Host` ⇒ 421; wrong `Origin` ⇒ 403;
`guide_path=/etc/passwd` ⇒ `[PATH_NOT_ALLOWED]`; `run_id=../../etc/passwd` ⇒ `[INVALID_INPUT]`.
**FastMCP 4 facts:** SSE endpoint `/sse`, messages `/messages`; uses `httpx2` (not `httpx`); the
annotation attribute is `read_only_hint`. Tool paths refer to the **server's** machine.

---

### Step 12 — Email support

**What & why.** Emails are not browsers: Outlook renders with Word's engine, Gmail strips markup, and
almost nothing supports modern CSS. So an email gets the **same rules, appliers, planner, verifiers
and reporters**, but a different *handler* (parsing notes), *writer* (inline styles) and a *support
table* (what email clients cannot do). Nothing existing was rewritten, which is the payoff of the plugin design.

| File | What it does / where it is used |
|---|---|
| `config/email_support.toml` | **What email clients cannot do**: unsupported values (`clamp(`, `var(`, `calc(`, `vw`, `vh`), unsupported properties (`backdrop-filter`, `gap`, `outline-offset`), *partial* properties applied with a note (`border-radius`, `box-shadow`, `letter-spacing`, `font-family`), and `rem_base_px = 16`. Edit as client support changes |
| `plugins/appliers/support.py` | `EmailSupport.adapt(property, value)` returns the value to write, or why it cannot be written. Converts `rem` to px, rejects unsupported features **with the reason** (never approximates), writes a plain `background` colour as `background-color` (Outlook is unreliable with the shorthand). `load_email_support()` |
| `plugins/appliers/base.py` | Appliers now take the support table; **only when the artifact is an email** do they adapt values. A rejected value becomes a per-element `Skip` carrying the table's reason (so the rule shows as "not applied" with that reason) |
| `plugins/artifacts/html_handler.py` | `HtmlArtifactHandler`: the shared parsing (tree, styles, roles, surfaces, notes) that used to live in the static handler |
| `plugins/artifacts/static.py`, `email.py` | Thin subclasses. `EmailArtifactHandler` additionally notes how many Outlook conditional comments were left untouched |
| `plugins/writers/base.py` | Shared writer helpers: `ensure_head`, `add_font_links`, `remove_font_links` (also now used by the static writer) |
| `plugins/writers/inline.py` | `InlineWriter`: merges each element's changes into its own `style="…"`; font names use single quotes (safe inside the attribute); adds only the optional font `<link>`; **no `<style>` block, no marker attributes**; Outlook conditional comments untouched; a re-run replaces its own font link |
| `plugins/verifiers/structure.py` | **Email-aware**: for emails each changed element's `style` must equal its original declarations updated by *exactly* the planned changes (formatting differences in untouched styles are ignored); for web pages any `style` change is still a failure |
| `core/registry.py` | New `unregister(kind, name)` (used by tests to simulate a missing handler/writer) |
| `pipeline/orchestrator.py` | The "email not supported" refusal is gone; a missing handler/writer gives a clear error (`_find_writer`) |

**Real sample result (synthetic email + Myridius guide):** classified email, **all 6 checks pass**,
45 changes, 5 of 5 Outlook conditional comments preserved, no `rem`/`clamp()`/`var()` left in any
inline style. The guide's `clamp()` heading sizes are **skipped and reported** ("clamp() is not
supported by most email clients"), so the email keeps its own `30px` heading size. The header text
became light on the dark navy header, and the body background is a single `background-color`.

**Decisions.** Web fonts: the full Montserrat stack is written inline (clients without web fonts fall
back) *and* the font `<link>` is added for clients that support it; the report says the rest will show the
fallback. `rem` is converted at 16px. Only the inline `style` attribute is touched.

**Problems caught.** (1) The structure check first **failed** on an untouched hidden preheader
because it normalised the original's style text but compared the output's raw text; both sides are now
normalised (the safety net worked: `branded.html` was withheld). (2) A plain `background` rule left the body
with both `background-color` and `background`; fixed by writing `background-color`. (3) One of my own
tests was too strict about the intentional `data-brand-compliance="font"` link marker. (4) An orchestrator edit
silently did not apply (ruff-reformat trap again) and was redone.

---

### Step 13 — Evaluation set, metrics and sample reports

**What & why.** A test suite says "the code does what I coded". An *evaluation* asks "given this guide
and this file, is the outcome what a careful person expects?". Each case is a guide + an artifact + a
hand-written `expected/<id>.json`. **Rule of the evaluator: do not grade your own homework**, so the
content, fidelity and idempotence metrics are recomputed by the evaluator's own code from the original and
branded files, not copied from the tool's verifiers.

| File | What it does / where it is used |
|---|---|
| `evaluation/cases.py` | The case format: `RuleSelector` (pick rules by category/role/property/value/scope/guide line), `RuleExpectation` (hand label), `ChangeExpectation`, `ConflictExpectation`, `Expectations`, `EvalCase`; `load_cases()` (ids must be unique) |
| `evaluation/metrics.py` | The metrics (below). Each returns a `Metric` (name, passed, detail, numerator/denominator) |
| `evaluation/runner.py` | `EvalRunner.run_case()` runs the **real orchestrator**, scores it, does a **real second run** on the output for idempotence, keeps `report.md`, `report.json`, `branded.html` per case. Refusal cases are scored on the typed error code |
| `evaluation/scorecard.py` | `to_markdown()` / `to_json()` / `aggregate()` (per metric: cases passing, items) |
| `evaluation/__main__.py` | `python -m brand_compliance.evaluation [--root --cases --reports]`; exit 0 only if every case passes; writes `eval/reports/scorecard.md` + `.json` |
| `eval/expected/*.json` | The **12 cases** (hand-written expectations) |
| `eval/guides/` | `mini-brand.md` (clean), `mini-low-contrast.md`, `mini-conflicting.md`, `mini-subjective.md`, `plain-notes.txt` (unsupported format). All synthetic. They reuse the Myridius section titles because `config/vocabulary.toml` bullet specs are keyed to section titles |
| `eval/artifacts/` | `mini-clean`, `mini-broken` (malformed HTML), `mini-outlook-email` (VML, `<center>`, `<font>`), `mini-already-branded`, `mini-dark`, `invalid-encoding` (not UTF-8), plus the real page and the sample email |
| `eval/reports/` | **Sample reports** per case + `scorecard.md` / `scorecard.json` (a required deliverable) |
| `tests/unit/evaluation/` | Prove every metric can **pass and fail**, including a **sabotage test** (output corrupted *and* the structure verifier disabled: only the evaluator's own check can notice) |
| `tests/integration/test_evaluation_set.py` | The quality gate: every shipped case must pass |

**The metrics.** Rule status accuracy (hand-labelled) · expected changes made · **unexpected changes (target 0)** ·
expected contradictions found / no invented ones · contradicting rules never applied · run status and artifact type ·
rollbacks · notes mention what they should · **visible text, links, images, scripts, comments preserved** (own parsing) ·
original untouched (sha256) · **idempotent** (real second run) · **report matches the file** (every edited element is
logged and every logged change shows in the file) · refusals carry the right typed error.

**The 12 cases:** real guide + real page · real guide + synthetic email · low-contrast brand colours (rolled back) ·
self-contradicting guide (neither side applied) · purely subjective guide (zero changes) · broken HTML · Outlook-heavy
email · already-branded page (zero changes) · dark-surface page (the light "default surface" edit is undone) ·
unsupported guide format (typed refusal) · invalid UTF-8 artifact (typed refusal) · clean happy path.

**Result:** **12 of 12 cases pass.** 75/75 hand-labelled rules correct, 100/100 expected edits made,
**0 of 360 changes unexpected**, content preserved and idempotent in all 10 non-refusal cases, report matches file 10/10.

**What the evaluation found (and what was done):**
1. **Plain static pages were treated as emails.** The "too little evidence, be conservative" fallback treated a *lack of web
   signals* as email evidence. Email markup is a positive signature, so with **no** email markup a page is now static
   (`classifier.py`); the email fallback applies only when some email evidence exists.
2. **"Place logo bottom-left" (in the Do/Don't table) was "could not interpret".** A logo rule is clear but impossible
   without an asset, so it must be "understood but not applied". Added **`[[phrase_status]]`** to `vocabulary.toml`
   (logo, wave ornament, icons) applied anywhere in the guide (`rules/normalize.py`).
3. **Comments outside `<html>` were silently dropped** (found only by the evaluator's independent comment check; the
   structure verifier could not see them). `serialize_html` now writes the whole tree; `top_level_nodes()` lets the structure
   verifier compare them too.
4. **lxml invents a doctype for pages that have none.** Writing the whole tree would have injected
   `HTML 4.0 Transitional` (changing rendering mode); an empty doctype argument suppresses it. Regression tests added.
5. Two of **my own expectations** were wrong (a label that lumped a prose hover rule in with a real rule; an email `h2`
   `font-weight` the email legitimately lacked). I fixed the expectations, not the tool.

**Honest limits of this evaluation.** The expectations were written by the same author as the tool, so shared blind spots are
possible. Only **one** case uses real material (the real page); the emails and edge cases are synthetic. The evaluator does
not independently recompute contrast (it relies on the contrast check), and nothing measures the visual result. Adding real
client guides/emails to `eval/` is the best next improvement.

---

### Step 14 — Final documentation and the write-up

**What & why.** The documents a new reader needs, each for a different reader, plus the short write-up the
problem statement requires. Everything stated as fact in them was checked against the code or the evaluation.

| File | For | Contents |
|---|---|---|
| `README.md` | Anyone arriving at the repo | What it is, what one call produces, quick start, the five tools, how it stays safe, results, layout, links, current limits |
| `docs/approach.md` | A reviewer | **The short write-up**: the approach, how correctness is measured (with the real numbers), limitations stated plainly, what is in scope and deferred |
| `docs/tools.md` | A person connecting an MCP client | Connecting (URL, token, security responses), every tool with inputs/outputs, rule statuses, error codes, output files |
| `docs/architecture.md` | Engineers | Layers and dependency rules, data flow, plugin table, the data models, **design decisions and trade-offs**, configuration files, security model |
| `docs/plugin-guide.md` | Contributors | How to add a guide format, check, report format and the other plugin kinds, with working examples; shipping a plugin as a package; a checklist |
| `tests/unit/plugins/test_documented_examples.py` | The build | Runs the plugin guide's examples through the real orchestrator, so the guide cannot drift from the code |
| `docs/DEVELOPMENT-GUIDE.md` | Whoever continues the work | This file: the step-by-step story, final pass done |

**Two things writing the docs exposed:**
1. The orchestrator ran verifiers from a **hard-coded list of names**, so a newly registered verifier would never have
   run, contradicting "add a check = write one `Verifier`". Verifiers now declare a `scope` and the orchestrator runs all
   registered ones; the plugin guide's example proves it.
2. A mechanical check that every file path named in the docs exists (200 paths checked; only run-time output file names
   such as `branded.html` are not source files).

---

### Step 15 — Page colour variables follow the palette (post-V1 fix)

**Problem found in review.** The Myridius guide has no blue, yet the branded page still showed blue links,
buttons and charts. Cause: the page keeps its colours in CSS variables (`--accent`, `--bar`, `--s-*`), and
role rules (button, heading, text) never reach those. The guide's accent rules were reference definitions
only, and the one accent change tried on buttons was rolled back by the contrast check (`#09A78D` is 2.7:1 on
linen).

**What was added.** `config/token_map.toml` says which page variable takes which guide token, per surface.
`plugins/appliers/tokens.py` (`TokenApplier`, category `color_token`, *passive*) turns the palette-token rules
into `--variable: colour` changes on `/html`; it only overrides variables the page already defines and skips
emails. `plugins/writers/static.py` writes them as root-level blocks (light, `@media` dark, and the page's own
`[data-theme="dark"]` scope). `core/cascade.py` now also reads dark-scope variables and lets
`with_overrides` replace a root variable, so the contrast verifier judges text that gets its colour from a
remapped variable (and can blame and undo it). `pipeline/planning.py` keeps light and dark variable edits
apart and leaves a passive applier's idle rules as plain references.

**Decision.** Accent text on light surfaces uses `--digital-pavo` (`#337077`, ~5:1), not `--virtual-tide`,
because the guide's own 4.5:1 rule forbids the latter as text or under white text. Dark surfaces use the
guide's dark-mode accents.

**Still unmapped (guide defines no equivalent):** blue-grey neutrals (`--ink-2`, `--muted`, `--line`, `--ref`,
`--grid`, `--axis`), status colours, and hard-coded colours outside variables.

## 5. File index by folder (quick lookup)

```
config/                 settings.toml · vocabulary.toml · roles.toml · email_support.toml   (edit behaviour here)
eval/artifacts/         real page + synthetic email + edge-case pages/emails
eval/guides/            small synthetic guides   eval/expected/  12 case files   eval/reports/  sample reports + scorecard
src/brand_compliance/
  models/               source · guide · rule · artifact · change · conflict · report
  core/                 contracts · registry · errors · settings · logging · markers
                        color · contrast · css · units · text · paths · hashing · svg · cascade
  rules/                vocabulary · context · normalize · directives · bullet_specs
                        leftovers · interpret · conflicts
  plugins/
    sources/            base · markdown
    extractors/         base · token_table · typography · component · css_block · directive · bullet_spec
    artifacts/          base · classifier · roles · html_handler · static · email
    appliers/           base · typography · color · component · surface · font · support
    writers/            base · static · inline
    verifiers/          contrast · forbidden · structure · assets · original · idempotence
    reporters/          base · json_report · markdown_report · guide_rules
  pipeline/             bootstrap · planning · verification · finalize · orchestrator
  evaluation/           cases · metrics · runner · scorecard · __main__
  server/               app · tools · auth · error_mapping · schemas · __main__
tests/
  conftest.py           ALL shared fixtures (small guide/page, in-memory MCP, real HTTP server)
  unit/                 mirrors src/ (core, models, rules, plugins/*, pipeline, server)
  integration/          real guide + real page end to end; real HTTP + SSE server
docs/                   approach · tools · architecture · plugin-guide · DEVELOPMENT-GUIDE (this file)
README.md               start here
CLAUDE.md               short guidance for future assistant sessions
```

### What the tests prove

| Test area | Proves |
|---|---|
| `tests/unit/core` | Helpers are correct (WCAG values match published references, safe paths reject `../` and symlinks…) |
| `tests/unit/rules` | Each guide wording becomes the right rule; unsupported wording is *reported*; conflicts are found and resolved only by the guide's own exception |
| `tests/unit/plugins/*` | Each plugin works alone and satisfies its contract |
| `tests/unit/pipeline` | Overlap resolution, rollback, final statuses, orchestrator success and every failure path |
| `tests/unit/server` | Tool behaviour via an in-memory MCP client, startup safety checks |
| `tests/integration/test_*_real_*` | The real Myridius guide and real page: counts, "nothing silently dropped", 6 rollbacks, original untouched, idempotent output |
| `tests/integration/test_orchestrator_email.py` | The sample email end to end: inline styles only, Outlook comments kept, `clamp()` skipped with reason, rem→px, all 6 checks, original untouched |
| `tests/unit/evaluation`, `tests/integration/test_evaluation_set.py` | The metrics can pass *and* fail; the sabotage test; every shipped case passes (quality gate) |
| `tests/integration/test_server_http.py` | The security promises on a real port (401/421/403, masked errors, full workflow) |

---

## 6. How to run, test and extend

```bash
# setup (uv is not installed here; plain venv + pip)
python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt

# checks
.venv/bin/pytest                      # all tests; fails below 80% coverage
.venv/bin/ruff check . && .venv/bin/ruff format .
.venv/bin/mypy                        # strict

# run the server (HTTP + SSE, loopback; refuses to start without a token >= 16 chars)
export BRAND_MCP_AUTH_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
PYTHONPATH=src .venv/bin/python -m brand_compliance.server     # http://127.0.0.1:8000/sse
```
Clients send `Authorization: Bearer <token>`. Output goes to `output/<run_id>/` (git-ignored).

**Drive it from Python (post-V1 helper):** with the server running, `myenv/bin/python
scripts/run_claude_brand.py <guide.md> <artifact.html>` starts Claude Code through the Claude Agent SDK,
connects it to the server with the token from `.env`, and prints a summary. Details in `docs/tools.md`.
Scripts outside the package need `PYTHONPATH=src`.

**Add a new guide format (e.g. PDF):** write one `SourceAdapter` (turn the file into a
`GuideDocument` with source spans), register it in `plugins/sources/__init__.py`. No extractor changes.
**Add a rule finder:** one `RuleExtractor`; add its meaning to `rules/normalize.py`; teach wording in `config/vocabulary.toml`.
**Add a check:** one `Verifier`. **Add a report format:** one `Reporter` with a `filename`.
**Teach a new client's wording:** edit `config/vocabulary.toml` / `config/roles.toml`.
**Third-party plugin:** expose a zero-argument callable under the entry-point group `brand_compliance.plugins`.

---

## 7. Lessons and gotchas (so they are not repeated)

1. **`ruff format` reshapes code,** so a later scripted string-replace may silently not match.
   Always assert the replacement applied; bound edits to the exact block (a careless "replace to end of
   file" once deleted five tests, which were restored).
2. **`pytest -p no:logging` disables the `caplog` fixture.**
3. **A test module cannot import from `conftest`**; use `TYPE_CHECKING` imports for type hints only.
4. **`cssselect` accepts `:hover` and simply never matches it** (that is correct for base styles).
5. **FastMCP 4:** `httpx2`, `read_only_hint`, built-in Host/Origin protection, `mask_error_details`.
6. **Never trust a green test blindly:** several tests were weakened by `or` clauses or wrong
   scenarios and were rewritten; test names should state a real, checkable behaviour.
7. **Honesty over coverage:** when the guide is vague, report it. The count of "could not interpret"
   (95 of 329 rules for the Myridius guide) is correct, not a failure.

---

## 8. Known limits (final)

- **Email limits:** only the inline `style` attribute is written. Content *inside* Outlook conditional comments (including VML buttons) is untouched, so Outlook desktop may keep the original styling there. Bulletproof buttons keep their background on a parent `<td>`; only what the markup exposes is styled. Layout tables with their own backgrounds are not restyled. Montserrat shows only in clients that support web fonts. Guide values that need `clamp()`, `var()`, `calc()` or viewport units are skipped (reported), not approximated.
- **The only email samples are synthetic**; real emails and guides are needed for a proper evaluation.
- **Vocabulary is keyed to guide wording and section titles** (`bullet_specs`, `section_status`): a guide with a different structure needs vocabulary entries (config, not code).
- **No visual check.** There is no browser rendering/screenshot comparison; the guide's type scale
  (e.g. `clamp()` headings) could change a page's layout and nothing measures that.
- **`@media` rules are not evaluated** (counted and noted). A page with a dark theme gets brand
  styles in light mode only.
- **Large-text contrast** uses the strict 4.5:1 everywhere; element `opacity` and text over
  gradients/images cannot be evaluated (gradient cases are counted as "could not be checked").
- **Unmapped elements** (e.g. `<b>`, `<span>`, panels) keep their own styling except font family.
- **Deferred rules:** focus ring (also in contradiction), no-glow/no-glassmorphism effects, cards,
  nav, icons (CSS without selectors), logo/wave/photo/charts/layout restructuring.
- **Tool paths are server-side paths;** uploading file content over HTTP is not supported.
- **SSE is the older MCP transport;** `transport = "http"` in `config/settings.toml` switches to
  streamable HTTP (`/mcp`).
- **Real material is thin:** one real guide and one real page; emails and edge cases are synthetic (see `docs/approach.md`).
- Nothing has been committed to git yet.

---

## 9. What is next (suggested improvements, not required for V1)

| Idea | Why it helps |
|---|---|
| **Real client guides and emails in `eval/`** | The evaluation is only as strong as its material; this is the most valuable addition |
| More guide readers: PDF, JSON tokens, URL | The design needs only a `SourceAdapter` each (a JSON-token reader is shown in `docs/plugin-guide.md`) |
| A visual render comparison (for example headless Chromium) | Nothing measures layout effects of the guide's type scale yet |
| Evaluate `@media` rules and large-text contrast | Closes known gaps in contrast checking |
| Focus-ring and effect checks (no glow / glassmorphism) | Currently deferred (the sample guide also contradicts itself on the focus offset) |
| Bulletproof/VML button handling for Outlook; email-safe web-font fallbacks per client | Email fidelity beyond inline styles |
| An optional local AI rule finder (flagged `ai_assisted`, never editing HTML) | More guide coverage without breaking "never guess" |

**Open items for the owner:** supply real guides and emails; confirm the extra `reference` rule status; try a real
Claude Code (or other MCP client) connection to the server over SSE (verified here only with the FastMCP client);
decide about committing to git.

---

## 10. Glossary

| Term | Meaning |
|---|---|
| **Artifact** | The HTML file being restyled (static page or email) |
| **Guide** | The brand design guide (V1: Markdown) |
| **Role** | What an element *is*: `heading.h1`, `text.body`, `button.primary`… Rules talk about roles, not tags |
| **Dotted roles** | A rule for `button` also reaches `button.primary`; the more specific role wins per property |
| **Surface** | Light or dark background behind text (or `unknown`) |
| **Extractor / Normalizer** | Extractors *find* things; the normalizer *decides what they mean* |
| **Applier / Writer** | Applier decides *what* to change; writer decides *how* to write it |
| **Rollback** | Undoing a planned change that a verifier proved harmful |
| **Satisfied** | The artifact already matches a rule, so no edit was needed |
| **Reference** | A definition used by other rules (palette token, variable) |
| **Idempotent** | Running the tool on its own output changes nothing |
| **Verifier scope** | `changes` (judges the plan and may name changes to undo) or `output` (judges the written file) |
| **Phrase status** | A vocabulary entry that files unreadable text mentioning, say, a logo as "understood but not applied" |
| **Evaluation case** | A guide + artifact + hand-written expectations scored by `python -m brand_compliance.evaluation` |
| **MCP / FastMCP / SSE** | The protocol for AI tools / the Python library implementing it / the HTTP streaming transport used |

---

## Maintenance checklist

When a step is finished: (1) add its section in §4 (files, purpose, where used, decisions, problems);
(2) update the status table in §2 and the quality numbers; (3) update §5 (file index) and §8 (limits);
(4) move items from §9 into §4; (5) keep `CLAUDE.md` in sync (it is the short version of this guide).
**The final full pass after Step 14 is done**; repeat it whenever behaviour, numbers or files change.
