"""Tests for evaluation cases and metrics: each metric must pass AND fail."""

import json
from pathlib import Path

import pytest

from brand_compliance.core.errors import InvalidInputError
from brand_compliance.evaluation import metrics as m
from brand_compliance.evaluation.cases import (
    ChangeExpectation,
    ConflictExpectation,
    Expectations,
    RuleExpectation,
    RuleSelector,
    load_case,
    load_cases,
)
from brand_compliance.models.artifact import ArtifactType
from brand_compliance.models.change import Change, Skip
from brand_compliance.models.conflict import Conflict, ConflictKind
from brand_compliance.models.report import RunResult, RunStatus
from brand_compliance.models.rule import Rule, RuleStatus, Scope
from brand_compliance.models.source import SourceSpan


def _rule(rule_id: str, status: RuleStatus, line: int = 1, **kw: object) -> Rule:
    return Rule(
        id=rule_id,
        category=str(kw.pop("category", "typography")),
        status=status,
        source_span=SourceSpan(file="g.md", line_start=line),
        **kw,  # type: ignore[arg-type]
    )


def _change(
    change_id: str,
    rule_id: str,
    location: str = "/html/body/p",
    prop: str = "color",
    after: str = "#111",
) -> Change:
    return Change(
        id=change_id, rule_id=rule_id, location=location, property=prop, after=after
    )


def _result(**kw: object) -> RunResult:
    base: dict[str, object] = {
        "run_id": "r",
        "guide_name": "g.md",
        "artifact_name": "a.html",
        "artifact_type": ArtifactType.STATIC,
        "source_sha256_before": "a",
        "source_sha256_after": "a",
    }
    return RunResult(**{**base, **kw})  # type: ignore[arg-type]


# ---- selectors and files -----------------------------------------------------


def test_selector_matches_only_when_every_given_field_matches() -> None:
    rule = _rule(
        "R1",
        RuleStatus.APPLIED,
        7,
        target_role="text.body",
        property="color",
        value="#ABC",
        scope=Scope.LIGHT,
    )
    assert RuleSelector(
        role="text.body", guide_line=7, value="#abc", scope="light"
    ).matches(rule)
    assert not RuleSelector(role="text.body", guide_line=8).matches(rule)
    assert not RuleSelector(value="#fff").matches(rule)
    assert RuleSelector().matches(rule)


def test_case_files_are_validated_and_ids_must_be_unique(tmp_path: Path) -> None:
    good = {"id": "a", "description": "d", "guide": "g", "artifact": "x", "expect": {}}
    (tmp_path / "a.json").write_text(json.dumps(good))
    assert load_case(tmp_path / "a.json").id == "a"
    (tmp_path / "b.json").write_text(json.dumps(good))
    with pytest.raises(InvalidInputError, match="unique"):
        load_cases(tmp_path)


@pytest.mark.parametrize("text", ["not json", json.dumps({"id": "x"})])
def test_a_malformed_case_file_is_rejected(tmp_path: Path, text: str) -> None:
    (tmp_path / "bad.json").write_text(text)
    with pytest.raises(InvalidInputError, match="Cannot read evaluation case"):
        load_case(tmp_path / "bad.json")


def test_an_empty_case_folder_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(InvalidInputError, match="No evaluation cases"):
        load_cases(tmp_path)


# ---- rule status accuracy ----------------------------------------------------


def _labels(*items: tuple[RuleSelector, RuleStatus]) -> Expectations:
    return Expectations(
        rules=[RuleExpectation(selector=s, status=st) for s, st in items]
    )


def test_rule_accuracy_passes_when_every_label_matches() -> None:
    result = _result(
        rules=[
            _rule("R1", RuleStatus.APPLIED, 1),
            _rule("R2", RuleStatus.UNINTERPRETABLE, 2),
        ]
    )
    metric = m.rule_status_accuracy(
        result,
        _labels(
            (RuleSelector(guide_line=1), RuleStatus.APPLIED),
            (RuleSelector(guide_line=2), RuleStatus.UNINTERPRETABLE),
        ),
    )
    assert metric and metric.passed and metric.score == 1.0


def test_rule_accuracy_fails_on_a_wrong_status_and_says_which() -> None:
    result = _result(rules=[_rule("R1", RuleStatus.APPLIED, 1)])
    metric = m.rule_status_accuracy(
        result, _labels((RuleSelector(guide_line=1), RuleStatus.NOT_APPLICABLE))
    )
    assert metric and not metric.passed
    assert "expected understood_not_applicable" in metric.detail
    assert metric.score == 0.0


def test_rule_accuracy_fails_when_the_labelled_rule_does_not_exist() -> None:
    metric = m.rule_status_accuracy(
        _result(), _labels((RuleSelector(guide_line=9), RuleStatus.APPLIED))
    )
    assert metric and not metric.passed
    assert "no such rule" in metric.detail


def test_rule_accuracy_is_skipped_without_labels() -> None:
    assert m.rule_status_accuracy(_result(), Expectations()) is None


# ---- changes -----------------------------------------------------------------


def _with_change(after: str = "#111") -> RunResult:
    return _result(
        rules=[_rule("R1", RuleStatus.APPLIED, target_role="text.body")],
        changes=[_change("C1", "R1", after=after)],
    )


def test_expected_changes_are_made_and_nothing_unexpected_remains() -> None:
    expect = Expectations(
        changes=[
            ChangeExpectation(
                rule=RuleSelector(role="text.body"), property="color", after="#111"
            )
        ]
    )
    found = {x.name: x for x in m.change_metrics(_with_change(), expect)}
    assert found["expected changes made"].passed
    assert found["unexpected changes"].passed


def test_a_missing_expected_change_fails_and_is_named() -> None:
    expect = Expectations(
        changes=[
            ChangeExpectation(
                rule=RuleSelector(role="heading.h1"), property="font-size"
            )
        ]
    )
    found = {x.name: x for x in m.change_metrics(_with_change(), expect)}
    assert not found["expected changes made"].passed
    assert "heading.h1" in found["expected changes made"].detail


def test_an_unexpected_change_fails_the_metric() -> None:
    expect = Expectations(
        changes=[
            ChangeExpectation(
                rule=RuleSelector(role="text.body"), property="color", after="#999"
            )
        ]
    )
    found = {x.name: x for x in m.change_metrics(_with_change("#111"), expect)}
    assert not found["unexpected changes"].passed
    assert "1 of 1" in found["unexpected changes"].detail


def test_allowed_changes_explain_a_change_without_requiring_it() -> None:
    expect = Expectations(
        allowed_changes=[ChangeExpectation(rule=RuleSelector(category="typography"))]
    )
    found = {x.name: x for x in m.change_metrics(_with_change(), expect)}
    assert found["unexpected changes"].passed
    assert "expected changes made" not in found


def test_zero_changes_is_checked_through_the_unexpected_metric() -> None:
    found = {
        x.name: x
        for x in m.change_metrics(_with_change(), Expectations(zero_changes=True))
    }
    assert not found["unexpected changes"].passed


# ---- conflicts ---------------------------------------------------------------


def _conflicted() -> RunResult:
    rules = [
        _rule("R1", RuleStatus.CONFLICT_UNRESOLVED, 10),
        _rule("R2", RuleStatus.CONFLICT_UNRESOLVED, 20),
    ]
    conflict = Conflict(
        id="C1", kind=ConflictKind.VALUE_CLASH, rule_ids=["R1", "R2"], description="d"
    )
    return _result(rules=rules, conflicts=[conflict])


def test_expected_contradictions_are_found_by_kind_resolution_and_lines() -> None:
    ok = Expectations(
        conflicts=[
            ConflictExpectation(
                kind="value_clash", resolved=False, guide_lines=[10, 20]
            )
        ],
        exact_conflict_count=1,
    )
    assert all(x.passed for x in m.conflict_metrics(_conflicted(), ok))


@pytest.mark.parametrize(
    "item",
    [
        ConflictExpectation(kind="font_restriction", resolved=False, guide_lines=[10]),
        ConflictExpectation(kind="value_clash", resolved=True, guide_lines=[10]),
        ConflictExpectation(kind="value_clash", resolved=False, guide_lines=[99]),
    ],
)
def test_a_contradiction_with_the_wrong_kind_resolution_or_lines_is_not_found(
    item: ConflictExpectation,
) -> None:
    metric = m.conflict_metrics(_conflicted(), Expectations(conflicts=[item]))[0]
    assert not metric.passed


def test_an_invented_contradiction_fails_the_exact_count() -> None:
    metric = m.conflict_metrics(_conflicted(), Expectations(exact_conflict_count=0))[0]
    assert not metric.passed


def test_a_conflicted_rule_that_still_drove_a_change_is_caught() -> None:
    result = _conflicted()
    assert m.conflicts_never_applied(result).passed
    result.changes.append(_change("C1", "R1"))
    assert not m.conflicts_never_applied(result).passed


# ---- outcome -----------------------------------------------------------------


def test_outcome_metrics_check_status_type_rollbacks_notes_and_zero_changes() -> None:
    result = _result(
        status=RunStatus.COMPLETED,
        rolled_back={"C1": "x"},
        notes=["Outlook comments left"],
    )
    ok = Expectations(
        run_status=RunStatus.COMPLETED,
        artifact_type=ArtifactType.STATIC,
        rolled_back_at_least=1,
        notes_contain=["Outlook"],
        zero_changes=True,
    )
    assert all(x.passed for x in m.run_outcome(result, ok))
    bad = Expectations(
        run_status=RunStatus.FAILED_VERIFICATION,
        artifact_type=ArtifactType.EMAIL,
        rolled_back_at_least=2,
        notes_contain=["missing text"],
    )
    assert not any(x.passed for x in m.run_outcome(result, bad))


def test_notes_are_found_in_skip_reasons_too() -> None:
    result = _result(skipped=[Skip(rule_id="R1", reason="clamp() is not supported")])
    assert m.run_outcome(result, Expectations(notes_contain=["clamp()"]))[1].passed


# ---- independent content checks ----------------------------------------------

ORIGINAL = (
    "<!doctype html><html><body><!--[if mso]>x<![endif]-->"
    '<p>Hello <a href="/a">link</a></p>'
    '<img src="i.png"><script>var a = 1;</script></body></html>'
)


def _by_name(original: str, branded: str) -> dict[str, m.Metric]:
    return {x.name: x for x in m.content_preserved(original, branded)}


def test_identical_content_passes_every_content_metric() -> None:
    assert all(x.passed for x in m.content_preserved(ORIGINAL, ORIGINAL).__iter__())


@pytest.mark.parametrize(
    ("change", "metric"),
    [
        (("Hello", "Goodbye"), "visible text preserved"),
        ('href="/a"', "links preserved"),
        ('src="i.png"', "images preserved"),
        ("var a = 1;", "scripts preserved"),
        ("<!--[if mso]>x<![endif]-->", "comments preserved"),
    ],
)
def test_each_content_metric_fails_when_that_thing_changes(
    change: object, metric: str
) -> None:
    if isinstance(change, tuple):
        branded = ORIGINAL.replace(change[0], change[1])
    else:
        replacement = {
            'href="/a"': 'href="/b"',
            'src="i.png"': 'src="j.png"',
            "var a = 1;": "var a = 2;",
            "<!--[if mso]>x<![endif]-->": "",
        }
        branded = ORIGINAL.replace(str(change), replacement[str(change)])
    assert not _by_name(ORIGINAL, branded)[metric].passed


def test_the_tools_own_style_block_and_font_link_do_not_count_as_changes() -> None:
    ours = (
        '<head><style id="brand-compliance">p{}</style>'
        '<link rel="stylesheet" href="https://f/x.css" '
        'data-brand-compliance="font"></head>'
    )
    branded = ORIGINAL.replace("<body>", ours + "<body>")
    assert all(x.passed for x in m.content_preserved(ORIGINAL, branded))


def test_original_untouched_and_idempotence() -> None:
    assert m.original_untouched("abc", "abc").passed
    assert not m.original_untouched("abc", "abd").passed
    assert m.idempotence("x", "x").passed
    assert not m.idempotence("x", "y").passed


# ---- report fidelity ---------------------------------------------------------


def test_static_fidelity_compares_marked_elements_with_logged_locations() -> None:
    original = "<html><body><p>a</p><p>b</p></body></html>"
    branded = '<html><body><p data-brand-role="text.body">a</p><p>b</p></body></html>'
    ok = _result(changes=[_change("C1", "R", "/html/body/p[1]")])
    assert m.report_fidelity(original, branded, ok).passed
    unlogged = _result(changes=[])
    assert not m.report_fidelity(original, branded, unlogged).passed
    unedited = _result(
        changes=[
            _change("C1", "R", "/html/body/p[1]"),
            _change("C2", "R", "/html/body/p[2]"),
        ]
    )
    assert not m.report_fidelity(original, branded, unedited).passed


def test_email_fidelity_compares_changed_style_attributes_with_logged_locations() -> (
    None
):
    original = "<html><body><p style='margin:0'>a</p><p>b</p></body></html>"
    branded = '<html><body><p style="margin: 0; color: red">a</p><p>b</p></body></html>'
    result = _result(
        artifact_type=ArtifactType.EMAIL,
        changes=[_change("C1", "R", "/html/body/p[1]")],
    )
    assert m.report_fidelity(original, branded, result).passed
    assert not m.report_fidelity(
        original, branded, _result(artifact_type=ArtifactType.EMAIL)
    ).passed
