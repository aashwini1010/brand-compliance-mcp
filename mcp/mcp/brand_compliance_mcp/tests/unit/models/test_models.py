"""Tests for brand_compliance.models."""

import pytest
from pydantic import ValidationError

from brand_compliance.models.artifact import ArtifactModel, ArtifactType, Detection
from brand_compliance.models.change import ApplyResult, Change, Skip
from brand_compliance.models.guide import GuideDocument, GuideNode, NodeKind
from brand_compliance.models.report import SCHEMA_VERSION, Report, RunResult
from brand_compliance.models.rule import Rule, RuleStatus
from brand_compliance.models.source import SourceSpan


def _span(line: int = 3) -> SourceSpan:
    return SourceSpan(file="guide.md", line_start=line)


def test_source_span_describe_uses_line_when_present() -> None:
    assert _span(30).describe() == "guide.md:30"


def test_source_span_describe_uses_page_when_no_line() -> None:
    assert SourceSpan(file="g.pdf", page=2).describe() == "g.pdf p.2"


def test_source_span_describe_falls_back_to_file() -> None:
    assert SourceSpan(file="g.json").describe() == "g.json"


def test_source_span_rejects_zero_line() -> None:
    with pytest.raises(ValidationError):
        SourceSpan(file="guide.md", line_start=0)


def test_guide_document_walk_visits_nested_nodes() -> None:
    child = GuideNode(kind=NodeKind.PARAGRAPH, span=_span(2), text="child")
    section = GuideNode(kind=NodeKind.SECTION, span=_span(1), children=[child])
    doc = GuideDocument(source_name="guide.md", source_format="md", nodes=[section])
    assert [n.kind for n in doc.walk()] == [NodeKind.SECTION, NodeKind.PARAGRAPH]


def test_guide_document_nodes_of_filters_by_kind() -> None:
    table = GuideNode(kind=NodeKind.TABLE, span=_span())
    para = GuideNode(kind=NodeKind.PARAGRAPH, span=_span())
    doc = GuideDocument(source_name="g", source_format="md", nodes=[table, para])
    assert doc.nodes_of(NodeKind.TABLE) == [table]


def test_rule_defaults_to_pending_and_not_ai_assisted() -> None:
    rule = Rule(id="r1", category="color", source_span=_span())
    assert rule.status is RuleStatus.PENDING
    assert rule.ai_assisted is False


def test_rule_status_has_no_guessed_state() -> None:
    assert {s.value for s in RuleStatus} == {
        "pending",
        "applied",
        "understood_not_applicable",
        "could_not_interpret",
        "conflict_unresolved",
        "reference",
    }


def test_skip_requires_a_reason() -> None:
    with pytest.raises(ValidationError):
        Skip(rule_id="r1", reason="")


def test_apply_result_can_hold_changes_and_skips_together() -> None:
    change = Change(
        id="c1", rule_id="r1", location="/html/body", property="color", after="#000"
    )
    result = ApplyResult(
        changes=[change], skipped=[Skip(rule_id="r1", reason="surface unknown")]
    )
    assert result.changes[0].important is False
    assert result.skipped[0].location is None


def test_detection_score_must_be_between_zero_and_one() -> None:
    with pytest.raises(ValidationError):
        Detection(artifact_type=ArtifactType.EMAIL, score=1.5)


def test_artifact_model_excludes_tree_from_serialisation() -> None:
    artifact = ArtifactModel(
        source_name="a.html",
        source_sha256="abc",
        artifact_type=ArtifactType.STATIC,
        tree=object(),
    )
    assert "tree" not in artifact.model_dump()


def test_report_carries_schema_version() -> None:
    run = RunResult(
        run_id="run-001",
        guide_name="guide.md",
        artifact_name="a.html",
        artifact_type=ArtifactType.STATIC,
        source_sha256_before="abc",
        source_sha256_after="abc",
    )
    assert Report(run=run).schema_version == SCHEMA_VERSION
