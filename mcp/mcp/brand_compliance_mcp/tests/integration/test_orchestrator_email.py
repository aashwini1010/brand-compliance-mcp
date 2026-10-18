"""The full workflow on the real guide and the sample email."""

import re
from pathlib import Path

import pytest
from lxml import html

from brand_compliance.core.hashing import sha256_file
from brand_compliance.core.settings import PathSettings, Settings
from brand_compliance.models.artifact import ArtifactType
from brand_compliance.models.report import Report, RunStatus, RunSummary
from brand_compliance.models.rule import RuleStatus
from brand_compliance.pipeline.bootstrap import build_registry
from brand_compliance.pipeline.orchestrator import Orchestrator
from brand_compliance.rules.vocabulary import load_vocabulary

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "myridius-brand-guide.md"
EMAIL = ROOT / "eval" / "artifacts" / "sample-marketing-email.html"


@pytest.fixture(scope="module")
def run(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[RunSummary, Report, str, str]:
    if not (GUIDE.is_file() and EMAIL.is_file()):
        pytest.skip("sample guide or email not present")
    out = tmp_path_factory.mktemp("email-output")
    settings = Settings(
        paths=PathSettings(
            allowed_input_dirs=[str(ROOT)], allowed_output_dirs=[str(out)]
        )
    )
    vocabulary = load_vocabulary()
    orchestrator = Orchestrator(
        build_registry(settings, vocabulary), settings, vocabulary
    )
    before = sha256_file(EMAIL)
    summary = orchestrator.run(GUIDE, EMAIL, out)
    report = Report.model_validate_json(
        Path(summary.files["report.json"]).read_text(encoding="utf-8")
    )
    branded = Path(summary.files["branded.html"]).read_text(encoding="utf-8")
    return summary, report, branded, before


def test_the_email_is_detected_and_branded_with_every_check_passing(run) -> None:  # type: ignore[no-untyped-def]
    summary, _, _, _ = run
    assert summary.artifact_type is ArtifactType.EMAIL
    assert summary.status is RunStatus.COMPLETED
    assert all(summary.checks.values())
    assert len(summary.checks) == 6


def test_the_original_email_is_untouched(run) -> None:  # type: ignore[no-untyped-def]
    _, report, _, before = run
    assert sha256_file(EMAIL) == before == report.run.source_sha256_after


def test_styles_are_inline_and_nothing_web_only_is_added(run) -> None:  # type: ignore[no-untyped-def]
    _, _, branded, _ = run
    assert 'id="brand-compliance"' not in branded
    assert not re.search(r"data-brand-(role|surface|force)", branded)
    assert not re.search(r'style="[^"]*(var\(|clamp\(|backdrop-filter)', branded)
    assert not re.search(r'style="[^"]*\drem', branded)


def test_outlook_conditional_comments_all_survive(run) -> None:  # type: ignore[no-untyped-def]
    _, _, branded, _ = run
    original = EMAIL.read_text(encoding="utf-8")
    assert branded.count("<!--[if") == original.count("<!--[if")
    assert branded.count("<![endif]-->") == original.count("<![endif]-->")


def test_text_links_images_and_table_layout_are_unchanged(run) -> None:  # type: ignore[no-untyped-def]
    _, _, branded, _ = run
    original = EMAIL.read_text(encoding="utf-8")

    def visible(markup: str) -> str:
        return re.sub(r"\s+", " ", html.fromstring(markup).text_content()).strip()

    assert visible(branded) == visible(original)
    assert branded.count("<table") == original.count("<table")
    assert branded.count("<img") == original.count("<img")
    assert (
        sorted(re.findall(r'href="([^"]+)"', branded))
        == sorted(re.findall(r'href="([^"]+)"', original))
        or branded.count("href=") == original.count("href=") + 1
    )


def test_the_brand_font_stack_is_written_with_fallbacks_and_single_quotes(run) -> None:  # type: ignore[no-untyped-def]
    _, _, branded, _ = run
    assert "font-family: 'Montserrat', -apple-system" in branded
    assert "Georgia" not in re.sub(r"<!--.*?-->", "", branded, flags=re.S)


def test_clamp_sizes_are_skipped_and_reported_not_approximated(run) -> None:  # type: ignore[no-untyped-def]
    _, report, branded, _ = run
    reasons = {s.reason for s in report.run.skipped}
    assert "clamp() is not supported by most email clients" in reasons
    assert re.search(
        r"<h1[^>]*font-size: 30px", branded
    )  # the email's own size is kept


def test_rem_values_become_px_and_the_change_says_so(run) -> None:  # type: ignore[no-untyped-def]
    _, report, branded, _ = run
    converted = [
        c for c in report.run.changes if "rem converted to px" in (c.note or "")
    ]
    assert converted
    assert re.search(r"<p[^>]*font-size: 16px", branded)


def test_the_report_explains_the_email_specific_limits(run) -> None:  # type: ignore[no-untyped-def]
    _, report, _, _ = run
    notes = " ".join(report.run.notes)
    assert "Outlook conditional comment(s) were left untouched" in notes
    assert "Montserrat loads only in email clients that support web fonts" in notes
    assert any("Outlook desktop ignores" in (c.note or "") for c in report.run.changes)


def test_text_stays_readable_on_the_emails_dark_header_and_light_body(run) -> None:  # type: ignore[no-untyped-def]
    _, report, branded, _ = run
    header = re.search(r"<p[^>]*>Acme Cloud", branded)
    assert header and "color: #f6f3f0" in header.group(0)
    assert not re.search(r"background-color:[^;\"]*;[^\"]*\bbackground:", branded)
    contrast = next(c for c in report.run.checks if c.name == "contrast")
    assert contrast.passed


def test_no_rule_ends_pending_and_contradictions_are_still_reported(run) -> None:  # type: ignore[no-untyped-def]
    summary, report, _, _ = run
    assert all(r.status is not RuleStatus.PENDING for r in report.run.rules)
    assert summary.conflict_count == 2
