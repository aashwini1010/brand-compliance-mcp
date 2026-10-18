"""Verification and rollback on the real guide and the real page."""

from pathlib import Path

import pytest

from brand_compliance.core.contracts import RuleApplier, RuleExtractor, Verifier
from brand_compliance.core.hashing import sha256_file
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.models.rule import RuleStatus
from brand_compliance.pipeline.planning import PlanResult, plan_changes
from brand_compliance.pipeline.verification import (
    VerifiedPlan,
    verify_and_roll_back,
    verify_output,
)
from brand_compliance.plugins.appliers import register_appliers
from brand_compliance.plugins.artifacts.roles import load_role_aliases
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler
from brand_compliance.plugins.extractors import register_extractors
from brand_compliance.plugins.sources.markdown import MarkdownSourceAdapter
from brand_compliance.plugins.verifiers import register_verifiers
from brand_compliance.plugins.verifiers.original import OriginalIntactVerifier
from brand_compliance.plugins.writers.static import StylesheetWriter
from brand_compliance.rules.interpret import GuideInterpretation, interpret_guide
from brand_compliance.rules.vocabulary import load_vocabulary

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "myridius-brand-guide.md"
PAGE = ROOT / "eval" / "artifacts" / "mcp-servers-report-simple-v2.html"


@pytest.fixture(scope="module")
def registry() -> PluginRegistry:
    vocabulary = load_vocabulary()
    reg = PluginRegistry()
    register_extractors(
        reg, bullet_specs=[(s.section, s.label) for s in vocabulary.bullet_specs]
    )
    register_appliers(reg, load_role_aliases())
    register_verifiers(reg)
    return reg


@pytest.fixture(scope="module")
def interpretation(registry: PluginRegistry) -> GuideInterpretation:
    if not (GUIDE.is_file() and PAGE.is_file()):
        pytest.skip("sample guide or page not present")
    return interpret_guide(
        MarkdownSourceAdapter().load(GUIDE),
        registry.plugins(RuleExtractor),
        load_vocabulary(),
    )


@pytest.fixture(scope="module")
def planned(
    registry: PluginRegistry, interpretation: GuideInterpretation
) -> PlanResult:
    text = PAGE.read_text(encoding="utf-8")
    return plan_changes(
        interpretation.rules,
        StaticArtifactHandler().parse(text, PAGE.name),
        registry.plugins(RuleApplier),
    )


@pytest.fixture(scope="module")
def verified(
    registry: PluginRegistry, interpretation: GuideInterpretation, planned: PlanResult
) -> VerifiedPlan:
    handler = StaticArtifactHandler()
    by_name = {v.name: v for v in registry.plugins(Verifier)}
    return verify_and_roll_back(
        interpretation.rules,
        handler.parse(PAGE.read_text(encoding="utf-8"), PAGE.name),
        planned,
        [by_name["contrast"], by_name["forbidden-color"]],
    )


def test_the_guides_own_unreadable_colours_are_rolled_back(
    planned: PlanResult, verified: VerifiedPlan
) -> None:
    undone = sorted(
        (c.property, c.after) for c in planned.changes if c.id in verified.rolled_back
    )
    assert undone == [("background", "#09a78d")] * 2 + [("color", "#09a78d")] * 4


def test_nothing_else_is_rolled_back(
    planned: PlanResult, verified: VerifiedPlan
) -> None:
    assert len(verified.plan.changes) == len(planned.changes) - 6


def test_every_rollback_names_the_measured_ratio_and_the_element(
    verified: VerifiedPlan,
) -> None:
    assert len(verified.rolled_back) == 6
    for reason in verified.rolled_back.values():
        assert "is below 4.5:1" in reason
        assert "line " in reason


def test_remaining_plan_has_no_contrast_failure(verified: VerifiedPlan) -> None:
    assert all(check.passed for check in verified.checks)


def test_rules_whose_changes_were_all_undone_say_so(
    verified: VerifiedPlan, interpretation: GuideInterpretation
) -> None:
    undone = {
        r.id: verified.plan.outcomes[r.id]
        for r in interpretation.rules
        if r.id in verified.plan.outcomes
        and verified.plan.outcomes[r.id].status is RuleStatus.NOT_APPLICABLE
        and "Rolled back" in verified.plan.outcomes[r.id].reason
    }
    assert undone
    assert all("contrast" in o.reason for o in undone.values())


def test_page_that_already_failed_is_reported_not_blamed(
    verified: VerifiedPlan,
) -> None:
    contrast = next(c for c in verified.checks if c.name == "contrast")
    assert any("already failed before any change" in d for d in contrast.details)
    assert any("0 change(s) caused a failure" in d for d in contrast.details)


def test_written_output_passes_structure_assets_and_original_checks(
    registry: PluginRegistry,
    interpretation: GuideInterpretation,
    verified: VerifiedPlan,
) -> None:
    text = PAGE.read_text(encoding="utf-8")
    handler = StaticArtifactHandler()
    working = handler.parse(text, PAGE.name)
    output = StylesheetWriter().write(verified.plan.changes, working)
    by_name = {v.name: v for v in registry.plugins(Verifier)}
    checks = verify_output(
        handler.parse(text, PAGE.name),
        output,
        interpretation.rules,
        verified.plan.changes,
        [by_name["structure"], by_name["assets"]],
    )
    original = OriginalIntactVerifier(PAGE, sha256_file(PAGE)).check(
        working, output, [], []
    )
    assert [c.name for c in checks] == ["structure", "assets"]
    assert all(c.passed for c in [*checks, original]), [c.details for c in checks]
