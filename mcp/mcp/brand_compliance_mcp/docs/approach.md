# Approach, limitations and how success was measured

## The problem in one paragraph

Teams restyle HTML pages and emails to client brand guides by hand: slowly, inconsistently, and without a record.
Guides arrive in awkward forms and mix precise rules ("`#09A78D`", "Montserrat") with subjective direction
("confident, calm") and sometimes contradict themselves. The service must apply what can be applied,
automatically, keep the output usable and the original intact, treat static pages and emails differently,
respect possibly confidential material, and **say exactly** what it did, what it could not do, and why, without
silently guessing.

## The approach

**1. Deterministic, local, auditable.** Guides and artifacts may be confidential, results must be reproducible,
and "never guess" must be enforceable, so the tool uses no AI model and no network. The guide is parsed into a
format-neutral tree; small finders locate rules and record their exact guide line; one normaliser decides what
each finding means, driven by an editable vocabulary file. Anything outside the known shapes is *reported* as
"could not interpret", never approximated.

**2. Every rule ends in one honest status.** *Applied* (or enforced by a check, with the evidence), *understood
but not applied* (with the reason), *could not interpret*, *conflict (unresolved)*, or *reference* (definitions
such as palette tokens). This is the three-way distinction the problem asks for, plus the two cases real guides
force: contradictions, and definitions that are neither applied nor skipped.

**3. Contradictions are reported, never resolved by guessing.** A forbidden effect used elsewhere, "only font X"
broken elsewhere, or the same property set two ways cause **both sides to be left unapplied**. A contradiction is
resolved only when the guide itself states the exception (the report cites the line).

**4. Changes are planned, verified, then written.** Appliers decide *what* to change per element and property
(roles come from a config file; a button counts as primary only if its markup says so; the more specific role
wins). Verifiers then check the *plan* against the pristine original: text must stay readable (the guide's own
4.5:1 minimum, measured as the page would look after the edits) and no banned colour may appear. A failing change
is **undone and reported**, text colour before background; a failure the page already had is reported, not blamed.
Only then are the edits written.

**5. Static pages and emails are handled differently, on purpose.** A page gets one `<style>` block whose
selectors are boosted so brand rules win without `!important`; a page with a dark theme gets its brand styles in
light mode only. An email gets inline styles with plain values: anything email clients cannot display (`clamp()`,
`var()`, `calc()`, viewport units…) is **skipped and reported with the reason**, `rem` becomes px, Outlook
conditional comments are left untouched, and Montserrat is written with its fallback stack plus the web-font link,
with the limitation stated in the report. The classifier chooses the type from evidence and, when evidence is
close, takes the safer email path and says so.

**6. The original is never touched and unusable output is never returned.** Output goes to a new run folder; the
source fingerprint is checked before and after. After writing, structure (same elements, attributes, text,
scripts, comments), assets (images, links, anchors) and idempotence are verified. If one fails, `branded.html` is
withheld and the reports explain why.

**7. The report is the product.** `report.md` lists every edit with element, before, after and the guideline
behind it; every rule not applied and why; what could not be interpreted; contradictions; rollbacks; and text
elements no role matched. `report.json` and `guide_rules.json` make the same facts machine-readable.

**8. Built to grow.** Guide readers, finders, handlers, appliers, writers, verifiers and reporters are plugins
behind small interfaces. A new guide format needs only a reader (a JSON-token reader is demonstrated in
[plugin-guide.md](plugin-guide.md) with **no change** to any other component).

## How correctness is measured

A unit-test suite (691 tests, ~98% coverage) shows the code does what it was written to do. The **evaluation**
asks the different question: *given this guide and this file, is the outcome what a careful person expects?*
Twelve cases (`eval/expected/*.json`), each with expectations written from the guide: the real guide on a real page,
the real guide on an email, low-contrast brand colours, a self-contradicting guide, a purely subjective guide,
broken HTML, an Outlook-style email, an already-compliant page, a dark page, and two refusals.

The evaluator **does not grade its own homework**: content, fidelity and idempotence are recomputed by its own
code from the original and branded files, not read from the tool's verifiers, and a test sabotages the output
while switching a verifier off to prove the evaluator still catches it.

| Measure | Result |
|---|---|
| Cases passed | **12 / 12** |
| Hand-labelled rules ending in the right status | **75 / 75** |
| Expected edits actually made | **100 / 100** |
| Edits nobody expected (target 0) | **0 of 360** |
| Contradictions found as expected (kind, resolved or not, guide lines) / invented | 8 / 8 · 0 invented |
| Visible text, links, images, scripts, comments identical | 10 / 10 processed cases |
| Second run on the output is byte-identical | 10 / 10 |
| Every edited element is logged and every logged change is in the file | 10 / 10 |
| Original file unchanged | 12 / 12 |
| Bad input refused with the right typed error | 2 / 2 |

On the real guide and page the tool reads 329 rules (33 applied, 162 understood but not applied, 95 could not be
interpreted, 4 in contradiction, 35 reference definitions), makes 199 edits, undoes 6 because they would have made text
unreadable (the guide's own brand teal fails its own 4.5:1 rule at 2.74:1 and 3.03:1), and reports 3 contradictions
(one of them resolved by the guide itself). The scorecard and every case's reports are in
[`eval/reports/`](../eval/reports/scorecard.md).

**What the evaluation caught:** plain web pages being mistaken for emails; logo, icon and wave-ornament lines being
filed as "could not interpret" instead of "understood but not applied"; comments outside `<html>` being silently
dropped (only the evaluator's independent check noticed); and an invented doctype. All were fixed and have regression tests.

## Limitations (stated plainly)

- **Coverage is deliberately partial.** Just under a third of the Myridius rules (95 of 329) could not be interpreted: subjective
  voice and imagery guidance, prose without a known rule shape, CSS blocks with no selector. This is correct
  behaviour under "never guess", but it means much of a guide still needs a person.
- **Guides: Markdown only today.** Other readers (PDF, JSON, URL) are designed for but not built, and the vocabulary
  is keyed to guide wording and section titles, so a differently structured guide needs configuration additions.
- **No visual verification.** Nothing renders the result. The guide's type scale can change a page's layout and the
  tool does not measure that. Contrast is computed from base styles only; `@media` rules are counted, not evaluated;
  element opacity and text over images or gradients cannot be assessed (counted as "could not be checked").
- **Email is best-effort at the markup level.** Content inside Outlook conditional comments (including VML buttons)
  is untouched, so Outlook desktop may keep the original look there; bulletproof buttons keep their background on a
  parent `<td>`; layout tables with their own backgrounds are not restyled; Montserrat shows only in clients that
  support web fonts. Email behaviour has been exercised on **synthetic** emails only.
- **Unmapped elements** (for example `<b>`, `<span>`, panels) are listed but keep their styling apart from the font family.
- **The evidence is thinner than it looks.** The expectations were written by the same author as the tool, so shared
  blind spots are possible, and only one case uses real material. Real client guides and emails would be the most
  valuable addition to the evaluation.
- **Paths are server-side paths**; uploading content over the connection is not supported. SSE is the older MCP
  transport (streamable HTTP is one setting away).

## In scope for the first version, and deferred

| In scope (built) | Deferred |
|---|---|
| Markdown guides; colours, typography, buttons, links, surfaces, font family; per-surface text colour; contrast and banned-colour enforcement | PDF / JSON / URL / mixed guides |
| Static pages and emails; conflict detection; rollback; full reports | Logo placement (needs an asset), wave ornament, cards, navigation, icons, charts, photo treatment |
| Hardened local MCP server over HTTP + SSE | Focus-ring styling (also contradicted in the sample guide), no-glow / no-glassmorphism checks |
| Evaluation set with independent metrics | Visual rendering comparison; media-query evaluation; an optional local AI finder (flagged, never editing HTML) |
