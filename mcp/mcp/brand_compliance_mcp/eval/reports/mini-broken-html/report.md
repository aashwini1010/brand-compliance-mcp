# Brand compliance report

**Run:** `run-20261011-050425-1efabb`  ·  **Status:** completed

|  |  |
|---|---|
| Brand guide | mini-brand.md |
| Artifact | mini-broken.html (static) |
| Original file | unchanged |
| Fingerprint (sha256) | 7d22bfa9068c60ee56e5cb01b9ad8451ceff168224efc62852e88de08bf7e71e |
| Started | 2026-10-11T05:04:25+00:00 |

Why it was treated as static:

- static +1: no layout tables and no Outlook markup
- no email markup found

## Summary

| Rules | Count |
|---|---|
| Applied | 13 |
| Understood but not applied | 8 |
| Could not interpret | 5 |
| Conflict (unresolved) | 0 |
| Reference definition | 5 |
| **Total rules** | 31 |

Changes made: **21**  ·  changes rolled back: **0**  ·  contradictions in the guide: **0**

## Verification

- **contrast**: pass
  - 10 text element(s) checked against 4.5:1
  - 0 could not be checked (background or colour unknown)
  - 0 already failed before any change (not caused by this tool)
  - 0 change(s) caused a failure
- **forbidden-color**: pass
  - 0 colour ban(s) checked, 0 violation(s)
- **structure**: pass
  - 18 nodes identical, in the same order
- **assets**: pass
  - 1 asset reference(s) preserved, anchors intact
- **original-intact**: pass
  - source unchanged (sha256 7d22bfa9068c...)
- **idempotence**: pass
  - a second run gives identical output

## 1. Rules applied

| Rule | What the guide says | Scope | Guide line | Result |
|---|---|---|---|---|
| R008 | text.body contrast must be at least 4.5:1 | all | mini-brand.md:23 | Enforced by the contrast check: 10 text element(s) checked against 4.5:1 |
| R009 | document font-family: "Lato", Arial, sans-serif | all | mini-brand.md:30 | 1 change(s) made |
| R010 | heading.h1 font-size: 2.5rem | all | mini-brand.md:37 | 1 change(s) made |
| R011 | heading.h1 font-weight: 700 | all | mini-brand.md:37 | 1 change(s) made |
| R012 | heading.h1 line-height: 1.15 | all | mini-brand.md:37 | 1 change(s) made |
| R013 | heading.h1 letter-spacing: 0 | all | mini-brand.md:37 | 1 change(s) made |
| R018 | text.body font-size: 1rem | all | mini-brand.md:39 | 3 change(s) made |
| R019 | text.body font-weight: 400 | all | mini-brand.md:39 | 3 change(s) made |
| R020 | text.body line-height: 1.6 | all | mini-brand.md:39 | 3 change(s) made |
| R021 | text.body letter-spacing: 0 | all | mini-brand.md:39 | 3 change(s) made |
| R022 | text.body color: #1b2a41 | light | mini-brand.md:43 | 3 change(s) made |
| R028 | page.surface background: #faf7f2 | all | mini-brand.md:57 | 1 change(s) made |
| R030 | Only the font Lato may be used | all | mini-brand.md:58 | Enforced through the font-family changes |

## 2. Change log

Every edit: which element, before and after, and the guideline behind it.

### R009 · document font-family: "Lato", Arial, sans-serif (guide line mini-brand.md:30)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH002 | /html/body | font-family | (not set) | "Lato", Arial, sans-serif |  |

### R010 · heading.h1 font-size: 2.5rem (guide line mini-brand.md:37)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH003 | /html/body/h1 | font-size | 2rem | 2.5rem |  |

### R011 · heading.h1 font-weight: 700 (guide line mini-brand.md:37)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH004 | /html/body/h1 | font-weight | (not set) | 700 |  |

### R012 · heading.h1 line-height: 1.15 (guide line mini-brand.md:37)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH006 | /html/body/h1 | line-height | (not set) | 1.15 |  |

### R013 · heading.h1 letter-spacing: 0 (guide line mini-brand.md:37)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH005 | /html/body/h1 | letter-spacing | (not set) | 0 |  |

### R018 · text.body font-size: 1rem (guide line mini-brand.md:39)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH008 | /html/body/p[1] | font-size | (not set) | 1rem |  |
| CH013 | /html/body/p[2] | font-size | (not set) | 1rem |  |
| CH018 | /html/body/p[3] | font-size | (not set) | 1rem |  |

### R019 · text.body font-weight: 400 (guide line mini-brand.md:39)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH009 | /html/body/p[1] | font-weight | (not set) | 400 |  |
| CH014 | /html/body/p[2] | font-weight | (not set) | 400 |  |
| CH019 | /html/body/p[3] | font-weight | (not set) | 400 |  |

### R020 · text.body line-height: 1.6 (guide line mini-brand.md:39)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH011 | /html/body/p[1] | line-height | (not set) | 1.6 |  |
| CH016 | /html/body/p[2] | line-height | (not set) | 1.6 |  |
| CH021 | /html/body/p[3] | line-height | (not set) | 1.6 |  |

### R021 · text.body letter-spacing: 0 (guide line mini-brand.md:39)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH010 | /html/body/p[1] | letter-spacing | (not set) | 0 |  |
| CH015 | /html/body/p[2] | letter-spacing | (not set) | 0 |  |
| CH020 | /html/body/p[3] | letter-spacing | (not set) | 0 |  |

### R022 · text.body color: #1b2a41 (guide line mini-brand.md:43)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH007 | /html/body/p[1] | color | (not set) | #1b2a41 |  |
| CH012 | /html/body/p[2] | color | (not set) | #1b2a41 |  |
| CH017 | /html/body/p[3] | color | (not set) | #1b2a41 |  |

### R028 · page.surface background: #faf7f2 (guide line mini-brand.md:57)

| Change | Element | Property | Before | After | Note |
|---|---|---|---|---|---|
| CH001 | /html/body | background | #ffffff | #faf7f2 |  |

## 3. Understood but not applied

The guide's rule was understood, but could not be applied here.

| Rule | What the guide says | Guide line | Why not |
|---|---|---|---|
| R023 | text.body color: #f2efe8 | mini-brand.md:43 | No 'text.body' element sits on a dark surface |
| R024 | button.primary background: #b23a22 | mini-brand.md:51 | No element in the artifact has the role 'button.primary' |
| R025 | button.primary color: #faf7f2 | mini-brand.md:51 | No element in the artifact has the role 'button.primary' |
| R026 | button.primary border: none | mini-brand.md:51 | No element in the artifact has the role 'button.primary' |
| R014 | heading.h2 font-size: 1.75rem | mini-brand.md:38 | No element in the artifact has the role 'heading.h2' |
| R015 | heading.h2 font-weight: 700 | mini-brand.md:38 | No element in the artifact has the role 'heading.h2' |
| R016 | heading.h2 line-height: 1.2 | mini-brand.md:38 | No element in the artifact has the role 'heading.h2' |
| R017 | heading.h2 letter-spacing: 0 | mini-brand.md:38 | No element in the artifact has the role 'heading.h2' |

## 4. Could not interpret

Guidance the tool could not turn into a checkable rule. Nothing here was guessed or applied.

| Reason | Count |
|---|---|
| No extractor understood this text. | 2 |
| Directive wording is not one of the supported patterns. | 2 |
| Hover behaviour is described in prose, not as property values. | 1 |

| Rule | Guide line | Text | Reason |
|---|---|---|---|
| R029 | mini-brand.md:57 | Make the entire site dark | Directive wording is not one of the supported patterns. |
| R031 | mini-brand.md:58 | Mix in other typefaces | Directive wording is not one of the supported patterns. |
| R027 | mini-brand.md:51 | darken 8% | Hover behaviour is described in prose, not as property values. |
| R001 | mini-brand.md:3 | A small, complete guide used to evaluate the brand compliance tool. Synthetic. | No extractor understood this text. |
| R002 | mini-brand.md:7 | Acme's voice is warm, plain and helpful. | No extractor understood this text. |

## 5. Contradictions in the guide

_None found._

## 6. Reference definitions

Understood and used as input by other rules; nothing to apply on their own: 5 × color_token. Full list in `guide_rules.json`.

## 7. Changes rolled back

Edits that were planned, then undone because they would have broken the result. The page keeps its own value there.

_None._

## 8. Other places a rule was skipped

| Times | Reason |
|---|---|
| 4 | No element in the artifact has the role 'heading.h2' |
| 3 | No element in the artifact has the role 'button.primary' |
| 1 | No 'text.body' element sits on a dark surface |

## 9. Elements with text but no role

5 element(s) have text but match no role, so brand rules did not target them (only the font family was enforced).

- `/html/body/p[1]/b <b> line 8`
- `/html/body/p[1]/b/i <i> line 8`
- `/html/body/table/tr/td[1] <td> line 10`
- `/html/body/table/tr/td[2] <td> line 10`
- `/html/body/p[3]/a/div/span <span> line 12`

## Notes and limits

- Marked 5 element(s) with data-brand-role so brand rules target them exactly

