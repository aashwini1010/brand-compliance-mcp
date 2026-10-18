# Architecture

How the system is built and why. For the step-by-step build history and a file-by-file index, see
[DEVELOPMENT-GUIDE.md](DEVELOPMENT-GUIDE.md); for adding features see [plugin-guide.md](plugin-guide.md).

## 1. Shape of the system

One MCP call (`apply_brand`) runs a fixed pipeline over **one guide** and **one artifact**:

```
MCP client ──HTTP+SSE, bearer token──►  server/tools.py   (validate, map errors; no logic)
                                              │
                                              ▼
                                   pipeline/orchestrator.py
        ┌─────────────────────────────────────┴─────────────────────────────────────┐
  GUIDE SIDE                                                                  ARTIFACT SIDE
  plugins/sources     any format → GuideDocument tree (every node keeps its      plugins/artifacts   classify static|email,
                      source line)                                                                   parse, label roles,
  plugins/extractors  find rules → RuleCandidates (+ exact guide lines)                              find the surface behind text
  rules/normalize     decide meaning + status → Rules (vocabulary-driven)
  rules/conflicts     find contradictions → both sides left unapplied
        └─────────────────────────────────────┬─────────────────────────────────────┘
                                              ▼
  plugins/appliers   decide WHAT to change per element/property     ─► Changes + Skips
  pipeline/planning  one change per element+property (specific role wins); outcome per rule
  plugins/verifiers  contrast, forbidden colour: name the change that broke it
  pipeline/verification  undo it, re-check, repeat until clean
  plugins/writers    decide HOW to write it (static: one <style> block; email: inline style)
  plugins/verifiers  structure, assets, original-intact, idempotence on the written output
  pipeline/finalize  every rule gets exactly one final status
  plugins/reporters  report.md · report.json · guide_rules.json
                                              ▼
                        output/<run_id>/  (branded.html is withheld if an output check fails)
```

## 2. Layers and dependency rules

```
server/     MCP tools, auth, error mapping
pipeline/   orchestrator, planning, verification loop, final statuses
rules/      candidates → rules, vocabulary, conflict detection
plugins/    sources · extractors · artifacts · appliers · writers · verifiers · reporters
core/       interfaces (contracts), registry, shared helpers (colour, contrast, CSS cascade, paths…)
models/     pure data (imports nothing else from the app)
evaluation/ scores results against hand-written expectations (uses the layers above)
```

A layer may import only layers below it; `models/` is a leaf and `core/` may import only `models/`. Plugins
never import from `pipeline/` or `server/`. This is what keeps plugins swappable and independently testable.

## 3. Plugins

Anything that can grow is a **plugin**: an object with a `name` that satisfies one `typing.Protocol` in
`core/contracts.py`. `core/registry.py` holds them and answers "who can handle this?"; core code never
branches on a format name. External packages can add plugins through the entry-point group
`brand_compliance.plugins`; a broken external plugin is logged and skipped, never fatal.

| Interface | Decides | Built-ins |
|---|---|---|
| `SourceAdapter` | how a guide format becomes a `GuideDocument` | Markdown |
| `RuleExtractor` | where rules are in the tree | token tables, type scale, component tables, CSS blocks, directives, bullet specs |
| `ArtifactHandler` | how an HTML kind is parsed and labelled | static, email (share `HtmlArtifactHandler`) |
| `RuleApplier` | **what** to change for a category of rule | typography, color, component, surface, font family, font source |
| `StyleWriter` | **how** changes are written for an artifact type | stylesheet (static), inline (email) |
| `Verifier` | one check | contrast, forbidden colour, structure, assets, original-intact, idempotence |
| `Reporter` | one report format | Markdown, JSON, guide rules |

Splitting *what* (appliers) from *how* (writers) is deliberate: the same "primary buttons are teal" applier
serves a web page (a stylesheet rule) and an email (an inline style).

## 4. The data that flows between stages

| Model | Role |
|---|---|
| `GuideDocument` / `GuideNode` | Format-neutral guide tree; every node carries a `SourceSpan` (file, line, heading path) |
| `RuleCandidate` → `Rule` | A finding, then a normalised rule: category, target role, property, value, scope (light/dark/static/email), severity, **status**, reason, source span |
| `ArtifactModel` | The parsed HTML copy, its type, element → role map, element → surface (`light`/`dark`/`unknown`), notes |
| `Change` / `Skip` / `ApplyResult` | An edit (element, property, before, after, rule); a place a rule was understood but skipped, with a reason; an applier's answer |
| `Conflict` | A contradiction between rules; `resolved` only if the guide itself states the exception |
| `CheckResult`, `RunResult`, `Report`, `RunSummary` | Verification results and the final run record |

## 5. Design decisions and trade-offs

**Deterministic, not AI.** Guides and artifacts may be confidential, results must be reproducible, and "never
guess" must be enforceable. So extraction and editing are plain code; wording is taught through
`config/vocabulary.toml`, not inferred. The cost is coverage: anything outside the known shapes is *reported*
as "could not interpret". A local AI extractor could be added later as one more `RuleExtractor` (flagged
`ai_assisted`, never allowed to edit HTML).

**Extract, then normalise.** Extractors only find things and record exact lines; `rules/normalize.py` alone
decides meaning and status. `rules/leftovers.py` keeps every unclaimed paragraph, row and code line, so
nothing in a guide is silently dropped (a test enforces this on the real guide).

**Honest statuses.** Every rule ends as `applied`, `understood_not_applicable`, `could_not_interpret`,
`conflict_unresolved` or `reference` (definitions). There is no "guessed" status. Rules enforced as *checks*
(minimum contrast, forbidden colours) are `applied` with the check's evidence as the reason. A rule whose edits
were all undone becomes `understood_not_applicable` with the measured reason.

**Contradictions: never pick a winner.** `rules/conflicts.py` finds three kinds: a forbidden effect used
elsewhere, "only font X" broken elsewhere, and the same role+property set to different values in overlapping
scopes. An unresolved contradiction leaves **both** applicable sides unapplied. It counts as resolved only
when the guide states the exception itself (the Caveat font case), and the report points to that line.

**Per-role brand rules, not variable remapping.** A real page may define its whole design through CSS
variables (`--accent`, `--ink`). Remapping them would require deciding what each variable *means*, which is a
guess. Instead each element gets a **role** (`config/roles.toml`: first match wins; a button is
`button.primary` only if its markup says so) and brand rules apply per role. Roles are *dotted*: a rule for
`button` reaches `button.primary`, and the more specific role wins for a property.

**Beating the page's CSS without `!important` (static).** The writer marks styled elements with
`data-brand-role` (and `data-brand-surface`) and writes one `<style id="brand-compliance">` whose selectors
carry an id boost (`html:not(#brand-compliance) [data-brand-role="…"]`). `!important` is used only on a single
element that has an inline style for the same property (`data-brand-force`). If the page has dark-theme
styles, the block is limited to light mode and excludes `[data-theme="dark"]`, so the page's dark theme keeps
its own look. Re-running on its own output is byte-identical because the tool recognises and ignores its own
block.

**Email is a different strategy, same pipeline.** Email clients ignore most CSS, so changes are written as
inline `style` attributes with plain values. `config/email_support.toml` lists what cannot be used (`clamp()`,
`var()`, `calc()`, viewport units, `backdrop-filter`…): a rule needing one is *skipped with the table's reason*,
never approximated. `rem` becomes px; a plain `background` becomes `background-color`; font names use single
quotes. Outlook conditional comments are left byte-for-byte. The classifier treats close calls as ambiguous
and picks the safer email handling; email markup (layout tables, Outlook comments, inline-style-heavy markup) is a
*positive* signature, so a page with none of it is static.

**A small CSS cascade reader (`core/cascade.py`).** It answers "what is the declared value here?" and "what
colour is behind this text?" from the page's **base** styles: `var()` is resolved from `:root`, `@media`
blocks are counted but not evaluated, translucent backgrounds are blended, and anything it cannot determine is
`unknown`. `with_overrides()` lets a verifier ask what the page would look like *after* planned edits without
touching the document. Colour sources are traced to the element, which is how a failure is blamed on a change.

**Verify, then undo.** Change-level verifiers (contrast, forbidden colour) judge the *plan* against the pristine
original and name the change to undo (text colour first, then background; a failure the page already had is
reported, not blamed). The loop undoes and re-checks until clean. Output-level verifiers (structure, assets,
original-intact, idempotence) judge the written file; they cannot be fixed by undoing one change, so a failure
withholds `branded.html` while the reports are still written. The orchestrator therefore works on **two parses**
of the artifact: a pristine one for verifiers and a working one that the writer edits.

**Whole-document serialisation.** The writer serialises the whole tree (comments before `<html>` and after
`</html>` survive) and suppresses the doctype lxml would otherwise invent. SVG attribute case lost by the HTML
parser is restored (`core/svg.py`).

## 6. Configuration (behaviour without code)

| File | Controls |
|---|---|
| `config/settings.toml` | Server host/port/transport, auth requirement, allowed hosts/origins, size limits, allowed folders. Override any value with `BRAND_MCP_<SECTION>__<NAME>`; the token only via `BRAND_MCP_AUTH_TOKEN` |
| `config/vocabulary.toml` | Guide wording → roles; type tokens; selectors; bullet specs; sections and phrases that map to a status and reason |
| `config/roles.toml` | Which elements get which roles (first match wins) and role aliases |
| `config/email_support.toml` | What email clients cannot do; partial-support notes; rem base size |

## 7. Security model

Local-only processing; no outbound calls. HTTP server binds to loopback by default, requires a bearer token
(constant-time comparison, minimum length enforced at start-up), and rejects wrong `Host`/`Origin`
headers (DNS-rebinding protection). Tool paths are resolved (symlinks and `..` included) and must lie in allowed
folders; an output folder may not contain an input; a run folder is never reused; `run_id` must match a strict
pattern. Typed errors reach clients as `[CODE] message`; anything unexpected is `[INTERNAL_ERROR]` with details
only in the server log, and logs never contain guide or artifact content. HTML is parsed, never executed.

## 8. Testing and evaluation

`tests/unit` mirrors `src/`; `tests/integration` runs the real guide and page, the real HTTP server, and the
evaluation set. Fixtures live only in `tests/conftest.py`. The `evaluation/` package scores the tool against
hand-written expectations, recomputing safety metrics with its own code so it cannot inherit a verifier's bug
(see [approach.md](approach.md)).

## 9. Known structural limits

Artifact handling is per-artifact and base-style only (no media-query evaluation, no rendering). Appliers set
properties on elements that have a role; unmapped elements keep their styling apart from the font family.
Vocabulary entries are keyed to guide wording and section titles, so a differently structured guide needs
config additions. Guides are Markdown only until further readers are added.
