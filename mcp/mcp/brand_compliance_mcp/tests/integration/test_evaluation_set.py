"""The shipped evaluation set must pass: this is the project's quality gate."""

from pathlib import Path

import pytest

from brand_compliance.evaluation.cases import load_cases
from brand_compliance.evaluation.runner import CaseResult, EvalRunner
from brand_compliance.evaluation.scorecard import aggregate

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "eval" / "expected"


@pytest.fixture(scope="module")
def results(tmp_path_factory: pytest.TempPathFactory) -> list[CaseResult]:
    if not CASES.is_dir():
        pytest.skip("evaluation cases not present")
    work = tmp_path_factory.mktemp("eval-work")
    return EvalRunner(ROOT, work).run_all(load_cases(CASES))


def test_every_shipped_case_passes(results: list[CaseResult]) -> None:
    failures = {
        r.case.id: [f"{m.name}: {m.detail}" for m in r.metrics if not m.passed]
        for r in results
        if not r.passed
    }
    assert failures == {}


def test_the_set_covers_the_scenarios_the_problem_statement_names(
    results: list[CaseResult],
) -> None:
    ids = {r.case.id for r in results}
    assert {
        "myridius-real-page",
        "myridius-sample-email",
        "mini-low-contrast",
        "mini-conflicting",
        "mini-subjective",
        "mini-broken-html",
        "mini-outlook-email",
        "mini-already-branded",
        "mini-dark-surface",
        "refuse-unsupported-guide-format",
        "refuse-invalid-utf8-artifact",
    } <= ids


def test_only_one_case_uses_real_client_style_material(
    results: list[CaseResult],
) -> None:
    """Honesty check: most cases are synthetic and the scorecard says so."""
    real = [r.case.id for r in results if not r.case.synthetic]
    assert real == ["myridius-real-page"]


def test_headline_numbers_are_perfect(results: list[CaseResult]) -> None:
    rows = {str(r["metric"]): r for r in aggregate(results)}
    assert rows["unexpected changes"]["items"].startswith("0/")
    assert rows["rule status accuracy"]["ratio"] == 1.0
    assert rows["expected changes made"]["ratio"] == 1.0
    assert (
        rows["original untouched"]["cases_passed"]
        == rows["original untouched"]["cases_total"]
    )
    assert rows["idempotent"]["cases_passed"] == rows["idempotent"]["cases_total"]
    assert (
        rows["report matches the file"]["cases_passed"]
        == rows["report matches the file"]["cases_total"]
    )
