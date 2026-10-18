"""Tests for brand_compliance.pipeline.orchestrator."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from brand_compliance.core.contracts import ArtifactHandler, StyleWriter
from brand_compliance.core.errors import (
    InvalidInputError,
    ParseFailedError,
    PathNotAllowedError,
    UnsupportedFormatError,
)
from brand_compliance.core.hashing import sha256_file
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.core.settings import PathSettings, Settings
from brand_compliance.models.artifact import ArtifactType
from brand_compliance.models.report import CheckResult, Report, RunStatus
from brand_compliance.models.rule import RuleStatus
from brand_compliance.pipeline.bootstrap import build_registry
from brand_compliance.pipeline.orchestrator import BRANDED_FILE, Orchestrator
from brand_compliance.rules.vocabulary import Vocabulary, load_vocabulary

EMAIL = """<html xmlns:v="urn:schemas-microsoft-com:vml"><head>
<meta name="x-apple-disable-message-reformatting">
<!--[if mso]><style>td{mso-line-height-rule:exactly}</style><![endif]--></head>
<body><table role="presentation" bgcolor="#fff"><tr>
<td style="color:red">Hi</td></tr></table></body></html>"""


def _settings(root: Path) -> Settings:
    return Settings(
        paths=PathSettings(
            allowed_input_dirs=[str(root)], allowed_output_dirs=[str(root / "out")]
        )
    )


def _orchestrator(
    root: Path,
    registry: PluginRegistry | None = None,
    vocabulary: Vocabulary | None = None,
) -> Orchestrator:
    settings = _settings(root)
    vocab = vocabulary or load_vocabulary()
    return Orchestrator(
        registry or build_registry(settings, vocab),
        settings,
        vocab,
        clock=lambda: datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
        id_factory=lambda: "abc123",
    )


def _run(root: Path, **kw: object):  # type: ignore[no-untyped-def]
    return _orchestrator(root).run(
        root / "guide.md",
        root / "page.html",
        root / "out",
        **kw,  # type: ignore[arg-type]
    )


def test_run_writes_the_four_files_into_a_folder_named_by_the_run_id(
    workspace: Path,
) -> None:
    summary = _run(workspace)
    run_dir = workspace / "out" / "run-20260102-030405-abc123"
    assert summary.run_id == "run-20260102-030405-abc123"
    assert summary.output_dir == str(run_dir)
    assert sorted(p.name for p in run_dir.iterdir()) == [
        "branded.html",
        "guide_rules.json",
        "report.json",
        "report.md",
    ]
    assert sorted(summary.files) == sorted(p.name for p in run_dir.iterdir())


def test_the_original_artifact_and_guide_are_never_modified(workspace: Path) -> None:
    before = (sha256_file(workspace / "page.html"), sha256_file(workspace / "guide.md"))
    _run(workspace)
    assert (
        sha256_file(workspace / "page.html"),
        sha256_file(workspace / "guide.md"),
    ) == before


def test_summary_reports_status_counts_and_every_check(workspace: Path) -> None:
    summary = _run(workspace)
    assert summary.status is RunStatus.COMPLETED
    assert summary.artifact_type is ArtifactType.STATIC
    assert summary.change_count > 0
    assert summary.rule_counts["applied"] >= 1
    assert summary.rule_counts["could_not_interpret"] >= 1
    assert set(summary.checks) == {
        "contrast",
        "forbidden-color",
        "structure",
        "assets",
        "original-intact",
        "idempotence",
    }
    assert all(summary.checks.values())
    assert "Branded page.html" in summary.message


def test_branded_output_contains_the_brand_block_and_keeps_the_text(
    workspace: Path,
) -> None:
    summary = _run(workspace)
    html = Path(summary.files[BRANDED_FILE]).read_text(encoding="utf-8")
    assert 'id="brand-compliance"' in html
    assert "<h1" in html
    assert "Hello" in html
    assert "World" in html


def test_report_json_has_a_final_status_for_every_rule(workspace: Path) -> None:
    summary = _run(workspace)
    report = Report.model_validate_json(
        Path(summary.files["report.json"]).read_text(encoding="utf-8")
    )
    assert report.run.rules
    assert all(r.status is not RuleStatus.PENDING for r in report.run.rules)
    assert report.run.source_sha256_before == report.run.source_sha256_after
    assert report.run.outputs == sorted(summary.files)


def test_guide_rules_file_matches_the_report(workspace: Path) -> None:
    summary = _run(workspace)
    rules = json.loads(
        Path(summary.files["guide_rules.json"]).read_text(encoding="utf-8")
    )["rules"]
    report = Report.model_validate_json(
        Path(summary.files["report.json"]).read_text(encoding="utf-8")
    )
    assert [r["id"] for r in rules] == [r.id for r in report.run.rules]


def test_two_runs_get_separate_folders(workspace: Path) -> None:
    orchestrator = Orchestrator(
        build_registry(_settings(workspace), load_vocabulary()),
        _settings(workspace),
        load_vocabulary(),
    )
    first = orchestrator.run(
        workspace / "guide.md", workspace / "page.html", workspace / "out"
    )
    second = orchestrator.run(
        workspace / "guide.md", workspace / "page.html", workspace / "out"
    )
    assert first.output_dir != second.output_dir


def test_reusing_a_run_id_is_refused_instead_of_overwriting(workspace: Path) -> None:
    _run(workspace)
    with pytest.raises(InvalidInputError, match="already exists"):
        _run(workspace)


def test_guide_outside_the_allowed_folders_is_refused(
    workspace: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    elsewhere = tmp_path_factory.mktemp("elsewhere") / "guide.md"
    elsewhere.write_text("# x")
    with pytest.raises(PathNotAllowedError):
        _orchestrator(workspace).run(
            elsewhere, workspace / "page.html", workspace / "out"
        )


def test_missing_guide_and_missing_artifact_are_invalid_input(workspace: Path) -> None:
    with pytest.raises(InvalidInputError):
        _orchestrator(workspace).run(
            workspace / "nope.md", workspace / "page.html", workspace / "out"
        )
    with pytest.raises(InvalidInputError):
        _orchestrator(workspace).run(
            workspace / "guide.md", workspace / "nope.html", workspace / "out"
        )


def test_artifact_with_the_wrong_extension_is_refused(workspace: Path) -> None:
    (workspace / "page.txt").write_text("<p>x</p>")
    with pytest.raises(InvalidInputError, match="Unsupported file type"):
        _orchestrator(workspace).run(
            workspace / "guide.md", workspace / "page.txt", workspace / "out"
        )


def test_guide_in_an_unsupported_format_is_refused(workspace: Path) -> None:
    (workspace / "guide.xyz").write_text("rules")
    with pytest.raises(UnsupportedFormatError):
        _orchestrator(workspace).run(
            workspace / "guide.xyz", workspace / "page.html", workspace / "out"
        )


def test_output_folder_outside_the_allowed_folders_is_refused(workspace: Path) -> None:
    with pytest.raises(PathNotAllowedError):
        _orchestrator(workspace).run(
            workspace / "guide.md", workspace / "page.html", workspace
        )


def test_artifact_that_is_not_utf8_text_is_a_parse_error(workspace: Path) -> None:
    (workspace / "page.html").write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(ParseFailedError):
        _run(workspace)


def test_email_is_branded_with_inline_styles_and_no_style_block(
    workspace: Path,
) -> None:
    (workspace / "page.html").write_text(EMAIL, encoding="utf-8")
    summary = _run(workspace)
    html = Path(summary.files[BRANDED_FILE]).read_text(encoding="utf-8")
    assert summary.artifact_type is ArtifactType.EMAIL
    assert summary.status is RunStatus.COMPLETED
    assert all(summary.checks.values())
    assert 'id="brand-compliance"' not in html
    assert "data-brand-role" not in html
    assert "<!--[if mso]>" in html
    assert "Montserrat" in html


def test_a_missing_style_writer_gives_a_clear_error(workspace: Path) -> None:
    settings, vocab = _settings(workspace), load_vocabulary()
    registry = build_registry(settings, vocab)
    registry.unregister(StyleWriter, "inline")
    (workspace / "page.html").write_text(EMAIL, encoding="utf-8")
    with pytest.raises(
        UnsupportedFormatError, match="No style writer is available for email"
    ):
        _orchestrator(workspace, registry, vocab).run(
            workspace / "guide.md", workspace / "page.html", workspace / "out"
        )


def test_a_missing_handler_gives_a_clear_error(workspace: Path) -> None:
    settings, vocab = _settings(workspace), load_vocabulary()
    registry = build_registry(settings, vocab)
    registry.unregister(ArtifactHandler, "email")
    (workspace / "page.html").write_text(EMAIL, encoding="utf-8")
    with pytest.raises(
        UnsupportedFormatError, match="email artifacts are not supported"
    ):
        _orchestrator(workspace, registry, vocab).run(
            workspace / "guide.md", workspace / "page.html", workspace / "out"
        )


def test_caller_can_force_the_static_strategy_and_it_is_noted(workspace: Path) -> None:
    (workspace / "page.html").write_text(EMAIL, encoding="utf-8")
    summary = _run(workspace, artifact_type=ArtifactType.STATIC)
    report = Report.model_validate_json(
        Path(summary.files["report.json"]).read_text(encoding="utf-8")
    )
    assert summary.artifact_type is ArtifactType.STATIC
    assert any("set by the caller" in n for n in report.run.notes)


class _AlwaysFails:
    name = "structure"

    def check(self, original, output, rules, changes) -> CheckResult:  # type: ignore[no-untyped-def]
        return CheckResult(name="structure", passed=False, details=["node 3 differs"])


def test_failed_output_check_withholds_the_branded_file_but_still_reports(
    workspace: Path,
) -> None:
    settings, vocab = _settings(workspace), load_vocabulary()
    registry = build_registry(settings, vocab)
    registry.register(_AlwaysFails(), replace=True)
    summary = _orchestrator(workspace, registry, vocab).run(
        workspace / "guide.md", workspace / "page.html", workspace / "out"
    )
    assert summary.status is RunStatus.FAILED_VERIFICATION
    assert BRANDED_FILE not in summary.files
    assert {"report.md", "report.json", "guide_rules.json"} <= set(summary.files)
    assert "withheld" in summary.message
    report = Path(summary.files["report.md"]).read_text(encoding="utf-8")
    assert "branded file was withheld" in report
    assert "node 3 differs" in report
    assert not (Path(summary.output_dir) / BRANDED_FILE).exists()
    assert summary.checks["structure"] is False
