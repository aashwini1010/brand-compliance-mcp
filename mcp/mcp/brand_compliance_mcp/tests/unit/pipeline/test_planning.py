"""Tests for brand_compliance.pipeline.planning."""

from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.rule import Rule, RuleStatus, Scope
from brand_compliance.models.source import SourceSpan
from brand_compliance.pipeline.planning import plan_changes
from brand_compliance.plugins.appliers.color import ColorApplier
from brand_compliance.plugins.appliers.component import ComponentApplier
from brand_compliance.plugins.appliers.typography import TypographyApplier
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler

PAGE = """<!doctype html><html><head><style>
.btn{border-radius:4px;color:#000} .primary{background:#222}
</style></head><body style="background:#fff">
<h1>Title</h1><p>Text</p>
<button class="btn">Back</button><button class="btn primary">Next</button>
</body></html>"""


def _artifact() -> ArtifactModel:
    return StaticArtifactHandler().parse(PAGE, "page.html")


def _rule(
    rule_id: str, category: str, role: str, prop: str, value: str, **kw: object
) -> Rule:
    return Rule(
        id=rule_id,
        category=category,
        target_role=role,
        property=prop,
        value=value,
        status=kw.pop("status", RuleStatus.PENDING),  # type: ignore[arg-type]
        source_span=SourceSpan(file="g.md", line_start=1),
        **kw,  # type: ignore[arg-type]
    )


APPLIERS = [TypographyApplier(), ColorApplier(), ComponentApplier()]


def test_changes_are_numbered_in_document_order() -> None:
    rules = [
        _rule("R001", "typography", "text.body", "font-size", "1rem"),
        _rule("R002", "typography", "heading.h1", "font-size", "3rem"),
    ]
    plan = plan_changes(rules, _artifact(), APPLIERS)
    assert [c.id for c in plan.changes] == ["CH001", "CH002"]
    assert [c.location for c in plan.changes] == ["/html/body/h1", "/html/body/p"]


def test_most_specific_role_wins_and_the_loser_is_recorded() -> None:
    rules = [
        _rule("R001", "component", "button", "color", "#111111"),
        _rule("R002", "component", "button.primary", "color", "#ffffff"),
    ]
    plan = plan_changes(rules, _artifact(), APPLIERS)
    by_location = {c.location: c for c in plan.changes}
    assert by_location["/html/body/button[2]"].after == "#ffffff"
    assert by_location["/html/body/button[1]"].after == "#111111"
    overridden = [s for s in plan.skipped if "Overridden" in s.reason]
    assert [(s.rule_id, s.location) for s in overridden] == [
        ("R001", "/html/body/button[2]")
    ]
    assert "R002" in overridden[0].reason


def test_scoped_rule_beats_unscoped_rule_of_the_same_role() -> None:
    rules = [
        _rule("R001", "color", "text.body", "color", "#111111"),
        _rule("R002", "color", "text.body", "color", "#222222", scope=Scope.LIGHT),
    ]
    plan = plan_changes(rules, _artifact(), APPLIERS)
    assert plan.changes[0].after == "#222222"


def test_later_rule_wins_when_everything_else_ties() -> None:
    rules = [
        _rule("R001", "typography", "text.body", "font-size", "1rem"),
        _rule("R002", "typography", "text.body", "font-size", "1.1rem"),
    ]
    assert plan_changes(rules, _artifact(), APPLIERS).changes[0].after == "1.1rem"


def test_outcome_is_applied_when_changes_were_made() -> None:
    rules = [_rule("R001", "typography", "heading.h1", "font-size", "3rem")]
    outcome = plan_changes(rules, _artifact(), APPLIERS).outcomes["R001"]
    assert outcome.status is RuleStatus.APPLIED
    assert outcome.reason == "1 change(s) made"


def test_outcome_is_applied_when_the_artifact_already_matches() -> None:
    rules = [_rule("R001", "component", "button", "border-radius", "4px")]
    outcome = plan_changes(rules, _artifact(), APPLIERS).outcomes["R001"]
    assert outcome.status is RuleStatus.APPLIED
    assert "already matches" in outcome.reason


def test_outcome_is_not_applicable_with_the_reason_when_nothing_applied() -> None:
    rules = [_rule("R001", "typography", "heading.h3", "font-size", "1rem")]
    outcome = plan_changes(rules, _artifact(), APPLIERS).outcomes["R001"]
    assert outcome.status is RuleStatus.NOT_APPLICABLE
    assert "role 'heading.h3'" in outcome.reason


def test_rule_whose_changes_were_all_overridden_is_not_applicable() -> None:
    rules = [
        _rule("R001", "component", "button", "color", "#111111"),
        _rule("R002", "component", "button", "color", "#222222"),
    ]
    plan = plan_changes(rules, _artifact(), APPLIERS)
    assert plan.outcomes["R001"].status is RuleStatus.NOT_APPLICABLE
    assert "Overridden by rule R002" in plan.outcomes["R001"].reason
    assert plan.outcomes["R002"].status is RuleStatus.APPLIED


def test_rules_that_are_not_pending_or_have_no_applier_are_left_out() -> None:
    rules = [
        _rule(
            "R001",
            "typography",
            "heading.h1",
            "font-size",
            "3rem",
            status=RuleStatus.UNINTERPRETABLE,
        ),
        _rule("R002", "color_token", "x", "--a", "#fff"),
    ]
    plan = plan_changes(rules, _artifact(), APPLIERS)
    assert plan.outcomes == {}
    assert plan.changes == []


def test_planning_does_not_modify_the_artifact_tree() -> None:
    artifact = _artifact()
    before = artifact.tree.xpath("count(//@*)")
    plan_changes(
        [_rule("R001", "typography", "heading.h1", "font-size", "3rem")],
        artifact,
        APPLIERS,
    )
    assert artifact.tree.xpath("count(//@*)") == before
