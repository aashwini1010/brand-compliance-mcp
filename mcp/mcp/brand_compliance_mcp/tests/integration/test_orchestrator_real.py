"""The full workflow on the real guide and the real page, through the orchestrator."""

from pathlib import Path

import pytest

from brand_compliance.core.hashing import sha256_file
from brand_compliance.core.settings import PathSettings, Settings
from brand_compliance.models.report import Report, RunStatus, RunSummary
from brand_compliance.models.rule import RuleStatus
from brand_compliance.pipeline.bootstrap import build_registry
from brand_compliance.pipeline.orchestrator import Orchestrator
from brand_compliance.rules.vocabulary import load_vocabulary

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "myridius-brand-guide.md"
PAGE = ROOT / "eval" / "artifacts" / "mcp-servers-report-simple-v2.html"


@pytest.fixture(scope="module")
def run(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[RunSummary, Report, str, str]:
    if not (GUIDE.is_file() and PAGE.is_file()):
        pytest.skip("sample guide or page not present")
    out = tmp_path_factory.mktemp("real-output")
    settings = Settings(
        paths=PathSettings(
            allowed_input_dirs=[str(ROOT)], allowed_output_dirs=[str(out)]
        )
    )
    vocabulary = load_vocabulary()
    orchestrator = Orchestrator(
        build_registry(settings, vocabulary), settings, vocabulary
    )
    before = sha256_file(PAGE)
    summary = orchestrator.run(GUIDE, PAGE, out)
    report = Report.model_validate_json(
        Path(summary.files["report.json"]).read_text(encoding="utf-8")
    )
    markdown = Path(summary.files["report.md"]).read_text(encoding="utf-8")
    return summary, report, markdown, before


def test_run_completes_with_every_check_passing(run) -> None:  # type: ignore[no-untyped-def]
    summary, _, _, _ = run
    assert summary.status is RunStatus.COMPLETED
    assert all(summary.checks.values())
    assert len(summary.checks) == 6


def test_original_page_is_untouched(run) -> None:  # type: ignore[no-untyped-def]
    _, report, _, before = run
    assert sha256_file(PAGE) == before
    assert report.run.source_sha256_before == before == report.run.source_sha256_after


def test_every_rule_ends_in_exactly_one_known_status(run) -> None:  # type: ignore[no-untyped-def]
    summary, report, _, _ = run
    assert report.run.rules
    assert all(r.status is not RuleStatus.PENDING for r in report.run.rules)
    assert sum(summary.rule_counts.values()) == len(report.run.rules)
    assert summary.rule_counts["applied"] > 0
    assert summary.rule_counts["could_not_interpret"] > 0
    assert summary.rule_counts["understood_not_applicable"] > 0


def test_the_guides_contradictions_are_reported_not_applied(run) -> None:  # type: ignore[no-untyped-def]
    summary, report, markdown, _ = run
    assert summary.conflict_count == 2
    assert len(report.run.conflicts) == 3
    assert "C002 · resolved by the guide itself" in markdown
    unresolved = [
        r for r in report.run.rules if r.status is RuleStatus.CONFLICT_UNRESOLVED
    ]
    changed_rules = {c.rule_id for c in report.run.changes}
    assert unresolved
    assert not (changed_rules & {r.id for r in unresolved})


def test_the_six_unreadable_changes_are_listed_with_measured_ratios(run) -> None:  # type: ignore[no-untyped-def]
    _, report, markdown, _ = run
    assert len(report.run.rolled_back) == 6
    section = markdown.split("## 7. Changes rolled back")[1].split("## 8.")[0]
    assert "2.74:1" in section
    assert "3.03:1" in section


def test_the_report_names_the_logo_policy_and_the_subjective_guidance(run) -> None:  # type: ignore[no-untyped-def]
    _, _, markdown, _ = run
    assert "never invents a logo" in markdown
    assert "Subjective guidance about tone" in markdown


def test_changes_always_say_where_before_after_and_which_rule(run) -> None:  # type: ignore[no-untyped-def]
    _, report, _, _ = run
    rule_ids = {r.id for r in report.run.rules}
    assert report.run.changes
    for change in report.run.changes:
        assert change.rule_id in rule_ids
        assert change.location.startswith("/html")
        assert change.after


def test_branded_file_is_written_only_in_the_run_folder(run) -> None:  # type: ignore[no-untyped-def]
    summary, _, _, _ = run
    branded = Path(summary.files["branded.html"])
    assert branded.parent == Path(summary.output_dir)
    assert branded.read_text(encoding="utf-8").count('id="brand-compliance"') == 1
