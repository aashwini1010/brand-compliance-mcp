"""Tests for the JSON, Markdown and guide-rules reporters."""

import json
from pathlib import Path

from brand_compliance.core.contracts import Reporter
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.models.artifact import ArtifactType
from brand_compliance.models.change import Change, Skip
from brand_compliance.models.conflict import Conflict, ConflictKind
from brand_compliance.models.report import CheckResult, Report, RunResult, RunStatus
from brand_compliance.models.rule import Rule, RuleStatus, Scope
from brand_compliance.models.source import SourceSpan
from brand_compliance.plugins.reporters import register_reporters
from brand_compliance.plugins.reporters.base import cell, table, what
from brand_compliance.plugins.reporters.guide_rules import GuideRulesReporter
from brand_compliance.plugins.reporters.json_report import JsonReporter
from brand_compliance.plugins.reporters.markdown_report import (
    MarkdownReporter,
    build_markdown,
)


def _rule(rule_id: str, status: RuleStatus, line: int = 3, **kw: object) -> Rule:
    return Rule(
        id=rule_id,
        category=str(kw.pop("category", "typography")),
        status=status,
        reason=str(kw.pop("reason", "because")),
        source_span=SourceSpan(file="g.md", line_start=line),
        **kw,  # type: ignore[arg-type]
    )


def _result(**overrides: object) -> RunResult:
    rules = [
        _rule(
            "R1",
            RuleStatus.APPLIED,
            target_role="heading.h1",
            property="font-size",
            value="3rem",
            reason="1 change(s) made",
        ),
        _rule(
            "R2",
            RuleStatus.NOT_APPLICABLE,
            4,
            target_role="logo",
            property="x",
            value="y",
            reason="no logo asset",
        ),
        _rule(
            "R3",
            RuleStatus.UNINTERPRETABLE,
            5,
            category="unmatched",
            value="Be calm",
            reason="Subjective",
        ),
        _rule(
            "R4",
            RuleStatus.CONFLICT_UNRESOLVED,
            6,
            category="forbid_effect",
            value="gradient",
            reason="C001",
        ),
        _rule(
            "R5",
            RuleStatus.REFERENCE,
            7,
            category="color_token",
            property="--a",
            value="#fff",
        ),
    ]
    base: dict[str, object] = {
        "run_id": "run-1",
        "guide_name": "g.md",
        "artifact_name": "a.html",
        "artifact_type": ArtifactType.STATIC,
        "started_at": "2026-01-01T00:00:00+00:00",
        "detection_signals": ["static +3: 1 script"],
        "source_sha256_before": "ab" * 32,
        "source_sha256_after": "ab" * 32,
        "rules": rules,
        "conflicts": [
            Conflict(
                id="C001",
                kind=ConflictKind.FORBIDDEN_EFFECT,
                rule_ids=["R4", "R1"],
                description="gradient clash",
            )
        ],
        "changes": [
            Change(
                id="CH001",
                rule_id="R1",
                location="/html/body/h1",
                property="font-size",
                before="2rem",
                after="3rem",
            )
        ],
        "skipped": [
            Skip(
                rule_id="R1",
                location="/html/body/p",
                reason="Rolled back: contrast 2.7:1",
            ),
            Skip(rule_id="R2", reason="No element has the role 'logo'"),
        ],
        "checks": [
            CheckResult(
                name="contrast", passed=True, details=["81 checked", "0 failed"]
            )
        ],
        "unmapped_elements": [f"/html/body/div[{i}] <div> line {i}" for i in range(30)],
        "notes": ["media queries not evaluated"],
    }
    return RunResult(**{**base, **overrides})  # type: ignore[arg-type]


def test_reporters_implement_the_contract_and_register() -> None:
    registry = PluginRegistry()
    register_reporters(registry)
    assert sorted(r.name for r in registry.plugins(Reporter)) == [
        "guide-rules",
        "json",
        "markdown",
    ]
    assert all(isinstance(r, Reporter) for r in registry.plugins(Reporter))


def test_json_report_round_trips_through_the_report_model(tmp_path: Path) -> None:
    path = JsonReporter().render(_result(), tmp_path)
    loaded = Report.model_validate_json(path.read_text(encoding="utf-8"))
    assert path.name == "report.json"
    assert loaded.run.run_id == "run-1"
    assert loaded.schema_version == "1.0"
    assert len(loaded.run.rules) == 5


def test_guide_rules_file_lists_rules_with_final_status_and_conflicts(
    tmp_path: Path,
) -> None:
    path = GuideRulesReporter().render(_result(), tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == "guide_rules.json"
    assert [r["status"] for r in data["rules"]][:2] == [
        "applied",
        "understood_not_applicable",
    ]
    assert data["conflicts"][0]["id"] == "C001"
    assert data["guide"] == "g.md"


def test_markdown_report_answers_each_question_in_its_own_section() -> None:
    text = build_markdown(_result())
    for heading in (
        "## Summary",
        "## Verification",
        "## 1. Rules applied",
        "## 2. Change log",
        "## 3. Understood but not applied",
        "## 4. Could not interpret",
        "## 5. Contradictions in the guide",
        "## 6. Reference definitions",
        "## 7. Changes rolled back",
        "## 8. Other places a rule was skipped",
        "## 9. Elements with text but no role",
        "## Notes and limits",
    ):
        assert heading in text


def test_markdown_change_log_names_element_before_after_and_guide_line() -> None:
    text = build_markdown(_result())
    assert "### R1 · heading.h1 font-size: 3rem (guide line g.md:3)" in text
    assert "| CH001 | /html/body/h1 | font-size | 2rem | 3rem |" in text


def test_markdown_separates_not_applied_from_not_interpreted_with_reasons() -> None:
    text = build_markdown(_result())
    not_applied = text.split("## 3.")[1].split("## 4.")[0]
    not_interpreted = text.split("## 4.")[1].split("## 5.")[0]
    assert "no logo asset" in not_applied
    assert "Be calm" in not_interpreted
    assert "Subjective" in not_interpreted
    assert "no logo asset" not in not_interpreted


def test_markdown_reports_conflicts_with_both_sides_and_rolled_back_changes() -> None:
    text = build_markdown(_result())
    assert "### C001 · UNRESOLVED: neither side applied" in text
    assert "Never use the 'gradient' effect" in text
    assert "contrast 2.7:1" in text.split("## 7.")[1].split("## 8.")[0]


def test_markdown_counts_every_status_in_the_summary() -> None:
    summary = (
        build_markdown(_result()).split("## Summary")[1].split("## Verification")[0]
    )
    for label, count in (
        ("Applied", 1),
        ("Understood but not applied", 1),
        ("Could not interpret", 1),
        ("Conflict (unresolved)", 1),
        ("Reference definition", 1),
    ):
        assert f"| {label} | {count} |" in summary
    assert "| **Total rules** | 5 |" in summary


def test_markdown_limits_the_unmapped_list_and_says_how_many_more() -> None:
    text = build_markdown(_result())
    assert "30 element(s) have text but match no role" in text
    assert "… and 5 more" in text


def test_markdown_withholding_notice_appears_when_verification_failed() -> None:
    text = build_markdown(_result(status=RunStatus.FAILED_VERIFICATION))
    assert "FAILED VERIFICATION" in text
    assert "branded file was withheld" in text


def test_markdown_flags_a_changed_original_and_an_ambiguous_type() -> None:
    text = build_markdown(
        _result(source_sha256_after="cd" * 32, classification_ambiguous=True)
    )
    assert "CHANGED (this must never happen)" in text
    assert "could not be classified with confidence" in text


def test_markdown_report_with_no_changes_says_so() -> None:
    assert "_No changes were made._" in build_markdown(_result(changes=[]))


def test_markdown_reporter_writes_report_md(tmp_path: Path) -> None:
    path = MarkdownReporter().render(_result(), tmp_path)
    assert path.name == "report.md"
    assert path.read_text(encoding="utf-8").startswith("# Brand compliance report")


def test_cell_escapes_pipes_backticks_and_truncates() -> None:
    assert cell("a|b`c") == "a\\|b'c"
    assert cell("x" * 500).endswith("…")
    assert len(cell("x" * 500)) == 160
    assert cell(None) == ""


def test_table_without_rows_says_none() -> None:
    assert table(["A"], []) == "_None._\n"


def test_what_describes_restrictions_in_plain_words() -> None:
    forbid = _rule(
        "R",
        RuleStatus.APPLIED,
        category="forbid_color",
        target_role="text.body",
        value="#52e081",
        scope=Scope.LIGHT,
    )
    assert what(forbid) == "Never use #52e081 as text.body colour on light surfaces"
    contrast = _rule(
        "R",
        RuleStatus.APPLIED,
        category="min_contrast",
        target_role="text.body",
        value="4.5",
    )
    assert what(contrast) == "text.body contrast must be at least 4.5:1"
    only = _rule("R", RuleStatus.APPLIED, category="font_only", value="Montserrat")
    assert what(only) == "Only the font Montserrat may be used"
    exception = _rule(
        "R",
        RuleStatus.REFERENCE,
        category="font_exception",
        value="Caveat",
        notes=["docs only"],
    )
    assert what(exception) == "The font Caveat is allowed, but only in: docs only"
    plain = _rule(
        "R",
        RuleStatus.APPLIED,
        target_role="button",
        property="border-radius",
        value="999px",
    )
    assert what(plain) == "button border-radius: 999px"
