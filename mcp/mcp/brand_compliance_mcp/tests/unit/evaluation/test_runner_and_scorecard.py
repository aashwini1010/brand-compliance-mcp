"""Tests for the evaluation runner, scorecard and command line."""

import json
from pathlib import Path

import pytest

from brand_compliance.evaluation.__main__ import main
from brand_compliance.evaluation.cases import (
    EvalCase,
    Expectations,
    RuleExpectation,
    RuleSelector,
)
from brand_compliance.evaluation.runner import EvalRunner
from brand_compliance.evaluation.scorecard import aggregate, to_json, to_markdown
from brand_compliance.models.artifact import ArtifactType
from brand_compliance.models.rule import RuleStatus
from brand_compliance.plugins.verifiers.structure import StructureVerifier
from brand_compliance.plugins.writers.static import StylesheetWriter


def _case(
    case_id: str = "demo",
    guide: str = "guide.md",
    artifact: str = "page.html",
    **expect: object,
) -> EvalCase:
    return EvalCase(
        id=case_id,
        description="d",
        synthetic=True,
        guide=guide,
        artifact=artifact,
        expect=Expectations(**expect),
    )  # type: ignore[arg-type]


def _runner(workspace: Path) -> EvalRunner:
    return EvalRunner(workspace, workspace / "work")


def _label(status: RuleStatus, **selector: object) -> RuleExpectation:
    return RuleExpectation(selector=RuleSelector(**selector), status=status)  # type: ignore[arg-type]


def test_a_correct_case_passes_every_metric(workspace: Path) -> None:
    case = _case(
        artifact_type=ArtifactType.STATIC,
        exact_conflict_count=0,
        rules=[_label(RuleStatus.APPLIED, category="min_contrast")],
    )
    result = _runner(workspace).run_case(case)
    assert result.passed, [m for m in result.metrics if not m.passed]
    names = {m.name for m in result.metrics}
    assert {
        "rule status accuracy",
        "idempotent",
        "visible text preserved",
        "report matches the file",
    } <= names


def test_a_wrong_label_fails_the_case(workspace: Path) -> None:
    case = _case(rules=[_label(RuleStatus.UNINTERPRETABLE, category="min_contrast")])
    result = _runner(workspace).run_case(case)
    assert not result.passed
    assert [m.name for m in result.metrics if not m.passed] == ["rule status accuracy"]


def test_a_refusal_case_passes_when_the_error_code_matches(workspace: Path) -> None:
    (workspace / "guide.xyz").write_text("rules")
    result = _runner(workspace).run_case(
        _case(guide="guide.xyz", error_code="UNSUPPORTED_FORMAT")
    )
    assert result.passed
    assert result.error_code == "UNSUPPORTED_FORMAT"
    assert {m.name for m in result.metrics} == {
        "refused with the right error",
        "original untouched",
    }


def test_a_refusal_with_the_wrong_code_fails(workspace: Path) -> None:
    (workspace / "guide.xyz").write_text("rules")
    assert (
        not _runner(workspace)
        .run_case(_case(guide="guide.xyz", error_code="PARSE_FAILED"))
        .passed
    )


def test_an_unexpected_refusal_fails(workspace: Path) -> None:
    (workspace / "guide.xyz").write_text("rules")
    assert not _runner(workspace).run_case(_case(guide="guide.xyz")).passed


def test_expecting_an_error_when_the_run_succeeds_fails(workspace: Path) -> None:
    result = _runner(workspace).run_case(_case(error_code="UNSUPPORTED_FORMAT"))
    assert not result.passed
    assert not next(m for m in result.metrics if m.name == "no error expected").passed


def test_outputs_are_kept_per_case_when_a_reports_folder_is_given(
    workspace: Path,
) -> None:
    reports = workspace / "reports"
    _runner(workspace).run_all([_case("one"), _case("two")], reports)
    for case_id in ("one", "two"):
        assert {p.name for p in (reports / case_id).iterdir()} == {
            "branded.html",
            "report.md",
            "report.json",
        }


def test_the_evaluator_catches_a_broken_verifier_by_itself(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sabotage: corrupt the text AND switch the structure check off.

    Only the evaluator's own independent check can notice.
    """
    original_write = StylesheetWriter.write

    def corrupt(self: StylesheetWriter, changes, artifact):  # type: ignore[no-untyped-def]
        written = original_write(self, changes, artifact)
        paragraph = written.tree.find(".//p")
        paragraph.text = "TAMPERED"
        return written

    from brand_compliance.models.report import CheckResult

    monkeypatch.setattr(StylesheetWriter, "write", corrupt)
    monkeypatch.setattr(
        StructureVerifier,
        "check",
        lambda self, *a, **k: CheckResult(
            name="structure", passed=True, details=["(disabled)"]
        ),
    )
    result = _runner(workspace).run_case(_case())
    failed = {m.name for m in result.metrics if not m.passed}
    assert "visible text preserved" in failed
    assert not result.passed


def test_the_evaluator_catches_an_extra_edit_nobody_expected(workspace: Path) -> None:
    case = _case(zero_changes=True)
    result = _runner(workspace).run_case(case)
    assert not next(m for m in result.metrics if m.name == "unexpected changes").passed


def test_scorecard_markdown_and_json_summarise_results(workspace: Path) -> None:
    results = _runner(workspace).run_all([_case("ok"), _case("bad", zero_changes=True)])
    text, data = to_markdown(results), json.loads(to_json(results))
    assert "# Evaluation scorecard" in text
    assert "**1 of 2 cases passed.**" in text
    assert "[ok](#ok)" in text and "synthetic" in text
    assert (
        data["cases_passed"] == 1
        and data["cases_total"] == 2
        and not data["all_passed"]
    )
    assert {row["metric"] for row in data["aggregate"]} >= {
        "idempotent",
        "unexpected changes",
    }


def test_aggregate_counts_passing_cases_per_metric(workspace: Path) -> None:
    results = _runner(workspace).run_all([_case("a"), _case("b")])
    row = next(r for r in aggregate(results) if r["metric"] == "idempotent")
    assert (row["cases_passed"], row["cases_total"]) == (2, 2)


def _write_case(folder: Path, case: EvalCase) -> None:
    folder.mkdir(exist_ok=True)
    (folder / f"{case.id}.json").write_text(case.model_dump_json(), encoding="utf-8")


def test_command_line_returns_zero_and_writes_the_scorecard_when_all_pass(
    workspace: Path,
) -> None:
    _write_case(workspace / "cases", _case("ok"))
    code = main(
        [
            "--root",
            str(workspace),
            "--cases",
            str(workspace / "cases"),
            "--reports",
            str(workspace / "rep"),
        ]
    )
    assert code == 0
    assert (workspace / "rep" / "scorecard.md").is_file()
    assert json.loads((workspace / "rep" / "scorecard.json").read_text())["all_passed"]


def test_command_line_returns_one_when_a_case_fails(workspace: Path) -> None:
    _write_case(workspace / "cases", _case("bad", zero_changes=True))
    code = main(
        [
            "--root",
            str(workspace),
            "--cases",
            str(workspace / "cases"),
            "--reports",
            str(workspace / "rep"),
        ]
    )
    assert code == 1


def test_command_line_returns_two_when_there_are_no_cases(workspace: Path) -> None:
    (workspace / "empty").mkdir()
    assert (
        main(
            [
                "--root",
                str(workspace),
                "--cases",
                str(workspace / "empty"),
                "--reports",
                str(workspace / "rep"),
            ]
        )
        == 2
    )
