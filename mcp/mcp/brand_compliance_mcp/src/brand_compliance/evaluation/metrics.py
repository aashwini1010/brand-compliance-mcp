"""Metrics: each compares a result with what a person expected.

The content and fidelity metrics read the original and branded files with their
own small parsing code. They do not reuse the verifiers, so a bug in a verifier
cannot hide itself here.
"""

import re
from collections import Counter
from dataclasses import dataclass
from typing import Final

from lxml import html

from brand_compliance.evaluation.cases import (
    ChangeExpectation,
    ConflictExpectation,
    Expectations,
)
from brand_compliance.models.change import Change
from brand_compliance.models.report import RunResult
from brand_compliance.models.rule import Rule, RuleStatus
from brand_compliance.plugins.appliers.base import same_value

_SPACES: Final = re.compile(r"\s+")
_FONT_SOURCE: Final = "@font-source"
_OUR_STYLE_ID: Final = "brand-compliance"
_OUR_FONT_ATTRIBUTE: Final = "data-brand-compliance"


@dataclass(frozen=True)
class Metric:
    """One measurement. ``score`` is 0..1 where a ratio makes sense."""

    name: str
    passed: bool
    detail: str
    score: float | None = None
    numerator: int = 0
    denominator: int = 0


def _ratio(
    name: str, good: int, total: int, detail: str, must_be_total: bool = True
) -> Metric:
    score = 1.0 if total == 0 else good / total
    return Metric(
        name, (good == total) if must_be_total else True, detail, score, good, total
    )


# ---- outcome -------------------------------------------------------------


def run_outcome(result: RunResult, expect: Expectations) -> list[Metric]:
    """The run ended as expected (status, type, rollbacks, notes, zero changes)."""
    metrics = [
        Metric(
            "run status",
            result.status is expect.run_status,
            f"expected {expect.run_status.value}, got {result.status.value}",
        )
    ]
    if expect.artifact_type is not None:
        metrics.append(
            Metric(
                "artifact type",
                result.artifact_type is expect.artifact_type,
                f"expected {expect.artifact_type.value}, "
                f"got {result.artifact_type.value}",
            )
        )
    if expect.zero_changes:
        metrics.append(
            Metric(
                "zero changes",
                not result.changes,
                f"{len(result.changes)} change(s) made",
            )
        )
    if expect.rolled_back_at_least:
        metrics.append(
            Metric(
                "rollbacks",
                len(result.rolled_back) >= expect.rolled_back_at_least,
                f"expected at least {expect.rolled_back_at_least}, "
                f"got {len(result.rolled_back)}",
            )
        )
    if expect.notes_contain:
        text = " ".join(_all_text(result))
        missing = [n for n in expect.notes_contain if n not in text]
        metrics.append(
            Metric(
                "notes mention what they should",
                not missing,
                "all present" if not missing else f"missing: {missing}",
            )
        )
    return metrics


def _all_text(result: RunResult) -> list[str]:
    parts = [*result.notes, *(s.reason for s in result.skipped)]
    parts += [r.reason for r in result.rules]
    parts += [d for c in result.checks for d in c.details]
    parts += [c.note or "" for c in result.changes]
    return parts


# ---- rules ---------------------------------------------------------------


def rule_status_accuracy(result: RunResult, expect: Expectations) -> Metric | None:
    """Share of hand-labelled rules that ended in the labelled status."""
    if not expect.rules:
        return None
    wrong: list[str] = []
    for item in expect.rules:
        matched = [r for r in result.rules if item.selector.matches(r)]
        if not matched:
            wrong.append(f"{item.selector.model_dump(exclude_none=True)}: no such rule")
        elif any(r.status is not item.status for r in matched):
            actual = sorted({r.status.value for r in matched})
            wrong.append(
                f"{item.selector.model_dump(exclude_none=True)}: expected "
                f"{item.status.value}, got {actual}"
            )
    good = len(expect.rules) - len(wrong)
    detail = f"{good}/{len(expect.rules)} labelled rules correct"
    if wrong:
        detail += "; wrong: " + " | ".join(wrong[:6])
    return _ratio("rule status accuracy", good, len(expect.rules), detail)


# ---- changes -------------------------------------------------------------


def _change_matches(
    change: Change, rules: dict[str, Rule], item: ChangeExpectation
) -> bool:
    rule = rules.get(change.rule_id)
    if rule is None or not item.rule.matches(rule):
        return False
    if item.property is not None and item.property != change.property:
        return False
    return item.after is None or same_value(change.after, item.after)


def change_metrics(result: RunResult, expect: Expectations) -> list[Metric]:
    """Expected edits happened; no unexpected edit happened."""
    rules = {r.id: r for r in result.rules}
    explainers = [*expect.changes, *expect.allowed_changes]
    metrics: list[Metric] = []
    if expect.changes:
        unmet = [
            item
            for item in expect.changes
            if not any(_change_matches(c, rules, item) for c in result.changes)
        ]
        good = len(expect.changes) - len(unmet)
        shown = [
            i.rule.model_dump(exclude_none=True) | {"property": i.property}
            for i in unmet[:4]
        ]
        metrics.append(
            _ratio(
                "expected changes made",
                good,
                len(expect.changes),
                f"{good}/{len(expect.changes)} expected edit(s) found"
                + (f"; missing: {shown}" if unmet else ""),
            )
        )
    if explainers or expect.zero_changes:
        unexpected = [
            c
            for c in result.changes
            if not any(_change_matches(c, rules, item) for item in explainers)
        ]
        detail = (
            f"{len(unexpected)} of {len(result.changes)} change(s) were not expected"
        )
        if unexpected:
            detail += ": " + ", ".join(
                f"{c.id} {c.property}={c.after}" for c in unexpected[:5]
            )
        metrics.append(
            Metric(
                "unexpected changes",
                not unexpected,
                detail,
                1.0 - _share(len(unexpected), len(result.changes)),
                len(unexpected),
                len(result.changes),
            )
        )
    return metrics


def _share(part: int, whole: int) -> float:
    return 0.0 if whole == 0 else part / whole


# ---- conflicts -----------------------------------------------------------


def conflict_metrics(result: RunResult, expect: Expectations) -> list[Metric]:
    """Expected contradictions are found; none are invented."""
    rules = {r.id: r for r in result.rules}
    metrics: list[Metric] = []
    if expect.conflicts:
        found = sum(
            1 for item in expect.conflicts if _find_conflict(result, rules, item)
        )
        metrics.append(
            _ratio(
                "expected contradictions found",
                found,
                len(expect.conflicts),
                f"{found}/{len(expect.conflicts)} expected contradiction(s) found",
            )
        )
    if expect.exact_conflict_count is not None:
        actual = len(result.conflicts)
        metrics.append(
            Metric(
                "no invented contradictions",
                actual == expect.exact_conflict_count,
                f"expected exactly {expect.exact_conflict_count}, reported {actual}",
            )
        )
    return metrics


def _find_conflict(
    result: RunResult, rules: dict[str, Rule], item: ConflictExpectation
) -> bool:
    for conflict in result.conflicts:
        if conflict.kind.value != item.kind or conflict.resolved != item.resolved:
            continue
        lines = {
            rules[i].source_span.line_start for i in conflict.rule_ids if i in rules
        }
        if set(item.guide_lines) <= lines:
            return True
    return False


def conflicts_never_applied(result: RunResult) -> Metric:
    """No edit may be driven by a rule that is in an unresolved contradiction."""
    conflicted = {
        r.id for r in result.rules if r.status is RuleStatus.CONFLICT_UNRESOLVED
    }
    leaked = sorted({c.rule_id for c in result.changes} & conflicted)
    return Metric(
        "contradicting rules never applied",
        not leaked,
        f"{len(conflicted)} rule(s) in conflict, {len(leaked)} of them applied",
    )


# ---- content and fidelity (computed independently of the verifiers) -------


def _tree(markup: str) -> html.HtmlElement:
    return html.document_fromstring(markup)


def _ours(element: html.HtmlElement) -> bool:
    return element.get("id") == _OUR_STYLE_ID or bool(element.get(_OUR_FONT_ATTRIBUTE))


def _visible_text(root: html.HtmlElement) -> str:
    parts = root.xpath("//body//text()[not(ancestor::script) and not(ancestor::style)]")
    return _SPACES.sub(" ", " ".join(str(p) for p in parts)).strip()


def _hrefs(root: html.HtmlElement) -> Counter[str]:
    return Counter(
        str(el.get("href"))
        for el in root.iter()
        if isinstance(el.tag, str) and el.get("href") and not _ours(el)
    )


def content_preserved(original: str, branded: str) -> list[Metric]:
    """Text, links, images, scripts and comments are exactly as they were."""
    a, b = _tree(original), _tree(branded)
    checks = {
        "visible text preserved": _visible_text(a) == _visible_text(b),
        "links preserved": _hrefs(a) == _hrefs(b),
        "images preserved": Counter(map(str, a.xpath("//img/@src")))
        == Counter(map(str, b.xpath("//img/@src"))),
        "scripts preserved": [_SPACES.sub("", s.text or "") for s in a.iter("script")]
        == [_SPACES.sub("", s.text or "") for s in b.iter("script")],
        "comments preserved": [c.text for c in a.xpath("//comment()")]
        == [c.text for c in b.xpath("//comment()")],
    }
    return [
        Metric(name, ok, "identical" if ok else "DIFFERS")
        for name, ok in checks.items()
    ]


def original_untouched(before_sha: str, after_sha: str) -> Metric:
    """The source file's fingerprint did not change."""
    return Metric(
        "original untouched",
        before_sha == after_sha,
        f"sha256 {before_sha[:12]}… before and after",
    )


def idempotence(first: str, second: str) -> Metric:
    """A second run on the first run's output produces identical output."""
    return Metric(
        "idempotent",
        first == second,
        "second run identical" if first == second else "second run DIFFERS",
    )


def _style_map(style: str | None) -> dict[str, str]:
    pairs = (part.split(":", 1) for part in (style or "").split(";") if ":" in part)
    return {
        k.strip().lower(): " ".join(v.replace('"', "'").lower().split())
        for k, v in pairs
    }


def report_fidelity(original: str, branded: str, result: RunResult) -> Metric:
    """Every edited element is logged, and every logged change shows in the file."""
    own = [c for c in result.changes if c.property != _FONT_SOURCE]
    variables = [c for c in own if c.property.startswith("--")]
    logged = {c.location for c in own if not c.property.startswith("--")}
    first, second = _tree(original), _tree(branded)
    tree = second.getroottree()
    if result.artifact_type.value == "static":
        marked = {
            tree.getpath(el)
            for el in second.iter()
            if isinstance(el.tag, str) and el.get("data-brand-role") is not None
        }
    else:
        before = {
            first.getroottree().getpath(el): el.get("style")
            for el in first.iter()
            if isinstance(el.tag, str)
        }
        marked = {
            tree.getpath(el)
            for el in second.iter()
            if isinstance(el.tag, str)
            and not _ours(el)
            and _style_map(el.get("style")) != _style_map(before.get(tree.getpath(el)))
        }
    missing, extra = sorted(logged - marked), sorted(marked - logged)
    block = " ".join(
        (el.text or "").lower()
        for el in second.iter("style")
        if el.get("id") == _OUR_STYLE_ID
    )
    missing += [
        f"{c.property}: {c.after}"
        for c in variables
        if f"{c.property}: {c.after.lower()}" not in block
    ]
    logged |= {f"{c.property}@{c.surface}" for c in variables}
    detail = f"{len(logged)} logged location(s), {len(marked)} edited element(s)"
    if missing or extra:
        detail += (
            f"; logged, not edited: {missing[:3]}; edited, not logged: {extra[:3]}"
        )
    return Metric("report matches the file", not missing and not extra, detail)
