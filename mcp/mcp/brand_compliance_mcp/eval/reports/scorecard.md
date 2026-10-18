# Evaluation scorecard

**12 of 12 cases passed.** All metrics are green.

## How to read this

Each case is a guide and an artifact with **hand-written expectations** (`eval/expected/*.json`). The content, fidelity and idempotence metrics are computed by the evaluator's own code from the original and branded files, not taken from the tool's verifiers. Cases marked *synthetic* were written for testing; real client material should be added for a proper evaluation.

## Overall by metric

| Metric | Cases passing | Items |
|---|---|---|
| artifact type | 10/10 |  |
| comments preserved | 10/10 |  |
| contradicting rules never applied | 10/10 |  |
| expected changes made | 8/8 | 124/124 |
| expected contradictions found | 3/3 | 8/8 |
| idempotent | 10/10 |  |
| images preserved | 10/10 |  |
| links preserved | 10/10 |  |
| no error expected | 10/10 |  |
| no invented contradictions | 10/10 |  |
| notes mention what they should | 5/5 |  |
| original untouched | 12/12 |  |
| refused with the right error | 2/2 |  |
| report matches the file | 10/10 |  |
| rollbacks | 3/3 |  |
| rule status accuracy | 10/10 | 75/75 |
| run status | 10/10 |  |
| scripts preserved | 10/10 |  |
| unexpected changes | 10/10 | 0/386 |
| visible text preserved | 10/10 |  |
| zero changes | 2/2 |  |

## Cases

| Case | Result | Kind |
|---|---|---|
| [mini-already-branded](#mini-already-branded) | ✅ | synthetic |
| [mini-broken-html](#mini-broken-html) | ✅ | synthetic |
| [mini-clean-page](#mini-clean-page) | ✅ | synthetic |
| [mini-conflicting](#mini-conflicting) | ✅ | synthetic |
| [mini-dark-surface](#mini-dark-surface) | ✅ | synthetic |
| [mini-low-contrast](#mini-low-contrast) | ✅ | synthetic |
| [mini-outlook-email](#mini-outlook-email) | ✅ | synthetic |
| [mini-subjective](#mini-subjective) | ✅ | synthetic |
| [myridius-real-page](#myridius-real-page) | ✅ | real material |
| [myridius-sample-email](#myridius-sample-email) | ✅ | synthetic |
| [refuse-invalid-utf8-artifact](#refuse-invalid-utf8-artifact) | ✅ | synthetic |
| [refuse-unsupported-guide-format](#refuse-unsupported-guide-format) | ✅ | synthetic |

### mini-already-branded

A page that already follows the guide exactly. Nothing should change, and the rules should say the page already matches.

| | Metric | Detail |
|---|---|---|
| ✅ | no error expected | ran |
| ✅ | run status | expected completed, got completed |
| ✅ | artifact type | expected static, got static |
| ✅ | zero changes | 0 change(s) made |
| ✅ | notes mention what they should | all present |
| ✅ | rule status accuracy | 4/4 labelled rules correct |
| ✅ | unexpected changes | 0 of 0 change(s) were not expected |
| ✅ | no invented contradictions | expected exactly 0, reported 0 |
| ✅ | contradicting rules never applied | 0 rule(s) in conflict, 0 of them applied |
| ✅ | original untouched | sha256 3d515fa49f5f… before and after |
| ✅ | visible text preserved | identical |
| ✅ | links preserved | identical |
| ✅ | images preserved | identical |
| ✅ | scripts preserved | identical |
| ✅ | comments preserved | identical |
| ✅ | report matches the file | 0 logged location(s), 0 edited element(s) |
| ✅ | idempotent | second run identical |

### mini-broken-html

Malformed HTML (unclosed tags, misnested bold/italic, unclosed table cells, an unquoted attribute). The tool must not crash and must preserve every word and link.

| | Metric | Detail |
|---|---|---|
| ✅ | no error expected | ran |
| ✅ | run status | expected completed, got completed |
| ✅ | artifact type | expected static, got static |
| ✅ | rule status accuracy | 3/3 labelled rules correct |
| ✅ | expected changes made | 1/1 expected edit(s) found |
| ✅ | unexpected changes | 0 of 21 change(s) were not expected |
| ✅ | no invented contradictions | expected exactly 0, reported 0 |
| ✅ | contradicting rules never applied | 0 rule(s) in conflict, 0 of them applied |
| ✅ | original untouched | sha256 7d22bfa9068c… before and after |
| ✅ | visible text preserved | identical |
| ✅ | links preserved | identical |
| ✅ | images preserved | identical |
| ✅ | scripts preserved | identical |
| ✅ | comments preserved | identical |
| ✅ | report matches the file | 5 logged location(s), 5 edited element(s) |
| ✅ | idempotent | second run identical |

### mini-clean-page

The small Acme guide applied to a simple page. The reference happy path: every rule applies, nothing is rolled back.

| | Metric | Detail |
|---|---|---|
| ✅ | no error expected | ran |
| ✅ | run status | expected completed, got completed |
| ✅ | artifact type | expected static, got static |
| ✅ | rule status accuracy | 9/9 labelled rules correct |
| ✅ | expected changes made | 18/18 expected edit(s) found |
| ✅ | unexpected changes | 0 of 24 change(s) were not expected |
| ✅ | no invented contradictions | expected exactly 0, reported 0 |
| ✅ | contradicting rules never applied | 0 rule(s) in conflict, 0 of them applied |
| ✅ | original untouched | sha256 753c215e3175… before and after |
| ✅ | visible text preserved | identical |
| ✅ | links preserved | identical |
| ✅ | images preserved | identical |
| ✅ | scripts preserved | identical |
| ✅ | comments preserved | identical |
| ✅ | report matches the file | 6 logged location(s), 6 edited element(s) |
| ✅ | idempotent | second run identical |

### mini-conflicting

A guide that contradicts itself twice: two different sizes for the same heading, and 'Lato only' next to a Playfair Display style. Neither side of a contradiction may be applied.

| | Metric | Detail |
|---|---|---|
| ✅ | no error expected | ran |
| ✅ | run status | expected completed, got completed |
| ✅ | artifact type | expected static, got static |
| ✅ | rule status accuracy | 4/4 labelled rules correct |
| ✅ | expected changes made | 17/17 expected edit(s) found |
| ✅ | unexpected changes | 0 of 23 change(s) were not expected |
| ✅ | expected contradictions found | 2/2 expected contradiction(s) found |
| ✅ | no invented contradictions | expected exactly 2, reported 2 |
| ✅ | contradicting rules never applied | 3 rule(s) in conflict, 0 of them applied |
| ✅ | original untouched | sha256 753c215e3175… before and after |
| ✅ | visible text preserved | identical |
| ✅ | links preserved | identical |
| ✅ | images preserved | identical |
| ✅ | scripts preserved | identical |
| ✅ | comments preserved | identical |
| ✅ | report matches the file | 6 logged location(s), 6 edited element(s) |
| ✅ | idempotent | second run identical |

### mini-dark-surface

A page that is dark on purpose. The guide's 'default surface' is light, but forcing it would make the page unreadable, so that edit must be undone and the dark-surface text colour used.

| | Metric | Detail |
|---|---|---|
| ✅ | no error expected | ran |
| ✅ | run status | expected completed, got completed |
| ✅ | artifact type | expected static, got static |
| ✅ | rollbacks | expected at least 1, got 1 |
| ✅ | rule status accuracy | 3/3 labelled rules correct |
| ✅ | expected changes made | 1/1 expected edit(s) found |
| ✅ | unexpected changes | 0 of 13 change(s) were not expected |
| ✅ | no invented contradictions | expected exactly 0, reported 0 |
| ✅ | contradicting rules never applied | 0 rule(s) in conflict, 0 of them applied |
| ✅ | original untouched | sha256 4f17610d7821… before and after |
| ✅ | visible text preserved | identical |
| ✅ | links preserved | identical |
| ✅ | images preserved | identical |
| ✅ | scripts preserved | identical |
| ✅ | comments preserved | identical |
| ✅ | report matches the file | 4 logged location(s), 4 edited element(s) |
| ✅ | idempotent | second run identical |

### mini-low-contrast

A guide whose own brand colours fail 4.5:1 (soft grey-blue text on paper, paper text on a pale button). Those edits must be undone and explained; the page's own colours stay.

| | Metric | Detail |
|---|---|---|
| ✅ | no error expected | ran |
| ✅ | run status | expected completed, got completed |
| ✅ | artifact type | expected static, got static |
| ✅ | rollbacks | expected at least 3, got 3 |
| ✅ | notes mention what they should | all present |
| ✅ | rule status accuracy | 4/4 labelled rules correct |
| ✅ | expected changes made | 16/16 expected edit(s) found |
| ✅ | unexpected changes | 0 of 21 change(s) were not expected |
| ✅ | no invented contradictions | expected exactly 0, reported 0 |
| ✅ | contradicting rules never applied | 0 rule(s) in conflict, 0 of them applied |
| ✅ | original untouched | sha256 753c215e3175… before and after |
| ✅ | visible text preserved | identical |
| ✅ | links preserved | identical |
| ✅ | images preserved | identical |
| ✅ | scripts preserved | identical |
| ✅ | comments preserved | identical |
| ✅ | report matches the file | 6 logged location(s), 6 edited element(s) |
| ✅ | idempotent | second run identical |

### mini-outlook-email

Legacy Outlook-style email: conditional comments, VML button, <center>, <font>, bgcolor tables. Everything inside the conditional comments must survive untouched.

| | Metric | Detail |
|---|---|---|
| ✅ | no error expected | ran |
| ✅ | run status | expected completed, got completed |
| ✅ | artifact type | expected email, got email |
| ✅ | notes mention what they should | all present |
| ✅ | rule status accuracy | 2/2 labelled rules correct |
| ✅ | expected changes made | 1/1 expected edit(s) found |
| ✅ | unexpected changes | 0 of 14 change(s) were not expected |
| ✅ | no invented contradictions | expected exactly 0, reported 0 |
| ✅ | contradicting rules never applied | 0 rule(s) in conflict, 0 of them applied |
| ✅ | original untouched | sha256 83322e24ac39… before and after |
| ✅ | visible text preserved | identical |
| ✅ | links preserved | identical |
| ✅ | images preserved | identical |
| ✅ | scripts preserved | identical |
| ✅ | comments preserved | identical |
| ✅ | report matches the file | 4 logged location(s), 4 edited element(s) |
| ✅ | idempotent | second run identical |

### mini-subjective

A guide that is only feelings and tone. Nothing can be checked mechanically, so nothing may be changed and nothing guessed.

| | Metric | Detail |
|---|---|---|
| ✅ | no error expected | ran |
| ✅ | run status | expected completed, got completed |
| ✅ | artifact type | expected static, got static |
| ✅ | zero changes | 0 change(s) made |
| ✅ | rule status accuracy | 2/2 labelled rules correct |
| ✅ | unexpected changes | 0 of 0 change(s) were not expected |
| ✅ | no invented contradictions | expected exactly 0, reported 0 |
| ✅ | contradicting rules never applied | 0 rule(s) in conflict, 0 of them applied |
| ✅ | original untouched | sha256 753c215e3175… before and after |
| ✅ | visible text preserved | identical |
| ✅ | links preserved | identical |
| ✅ | images preserved | identical |
| ✅ | scripts preserved | identical |
| ✅ | comments preserved | identical |
| ✅ | report matches the file | 0 logged location(s), 0 edited element(s) |
| ✅ | idempotent | second run identical |

### myridius-real-page

The Myridius guide applied to the real 'MCP Team Briefing' page (static, variable-driven, with a dark theme). Expectations were written from the guide; every edit pattern was checked against the guide line it comes from.

| | Metric | Detail |
|---|---|---|
| ✅ | no error expected | ran |
| ✅ | run status | expected completed, got completed |
| ✅ | artifact type | expected static, got static |
| ✅ | rollbacks | expected at least 6, got 6 |
| ✅ | notes mention what they should | all present |
| ✅ | rule status accuracy | 31/31 labelled rules correct |
| ✅ | expected changes made | 49/49 expected edit(s) found |
| ✅ | unexpected changes | 0 of 225 change(s) were not expected |
| ✅ | expected contradictions found | 3/3 expected contradiction(s) found |
| ✅ | no invented contradictions | expected exactly 3, reported 3 |
| ✅ | contradicting rules never applied | 4 rule(s) in conflict, 0 of them applied |
| ✅ | original untouched | sha256 4ee3f63c96f0… before and after |
| ✅ | visible text preserved | identical |
| ✅ | links preserved | identical |
| ✅ | images preserved | identical |
| ✅ | scripts preserved | identical |
| ✅ | comments preserved | identical |
| ✅ | report matches the file | 74 logged location(s), 48 edited element(s) |
| ✅ | idempotent | second run identical |

### myridius-sample-email

The Myridius guide applied to a synthetic marketing email (tables, inline styles, Outlook conditional comments). Email clients cannot use clamp(), so those sizes must be skipped and explained; rem becomes px.

| | Metric | Detail |
|---|---|---|
| ✅ | no error expected | ran |
| ✅ | run status | expected completed, got completed |
| ✅ | artifact type | expected email, got email |
| ✅ | notes mention what they should | all present |
| ✅ | rule status accuracy | 13/13 labelled rules correct |
| ✅ | expected changes made | 21/21 expected edit(s) found |
| ✅ | unexpected changes | 0 of 45 change(s) were not expected |
| ✅ | expected contradictions found | 3/3 expected contradiction(s) found |
| ✅ | no invented contradictions | expected exactly 3, reported 3 |
| ✅ | contradicting rules never applied | 4 rule(s) in conflict, 0 of them applied |
| ✅ | original untouched | sha256 6e4da8d77a0b… before and after |
| ✅ | visible text preserved | identical |
| ✅ | links preserved | identical |
| ✅ | images preserved | identical |
| ✅ | scripts preserved | identical |
| ✅ | comments preserved | identical |
| ✅ | report matches the file | 9 logged location(s), 9 edited element(s) |
| ✅ | idempotent | second run identical |

### refuse-invalid-utf8-artifact

An HTML file that is not valid UTF-8 text. The tool must refuse with a typed parse error, not crash or guess an encoding.

| | Metric | Detail |
|---|---|---|
| ✅ | refused with the right error | expected PARSE_FAILED, got PARSE_FAILED: invalid-encoding.html is not valid UTF-8 text |
| ✅ | original untouched | sha256 a5b76b76f058… before and after |

### refuse-unsupported-guide-format

A plain-text guide: no reader exists for it. The tool must refuse with a typed error and change nothing.

| | Metric | Detail |
|---|---|---|
| ✅ | refused with the right error | expected UNSUPPORTED_FORMAT, got UNSUPPORTED_FORMAT: No SourceAdapter can handle this input |
| ✅ | original untouched | sha256 753c215e3175… before and after |
