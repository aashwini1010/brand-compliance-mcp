"""Tests for brand_compliance.pipeline.finalize."""

import pytest

from brand_compliance.core.errors import BrandComplianceError
from brand_compliance.models.report import CheckResult
from brand_compliance.models.rule import Rule, RuleStatus
from brand_compliance.models.source import SourceSpan
from brand_compliance.pipeline.finalize import finalize_rules
from brand_compliance.pipeline.planning import PlanResult, RuleOutcome


def _rule(rule_id: str, category: str, status: RuleStatus = RuleStatus.PENDING) -> Rule:
    return Rule(
        id=rule_id,
        category=category,
        status=status,
        reason="before",
        source_span=SourceSpan(file="g.md", line_start=1),
    )


def _check(name: str, passed: bool = True, detail: str = "12 checked") -> CheckResult:
    return CheckResult(name=name, passed=passed, details=[detail])


def _final(
    rules: list[Rule],
    plan: PlanResult | None = None,
    checks: list[CheckResult] | None = None,
) -> dict[str, Rule]:
    done = finalize_rules(rules, plan or PlanResult(), checks or [])
    return {r.id: r for r in done}


def test_rules_that_already_have_a_final_status_are_kept_as_they_are() -> None:
    kept = _final([_rule("R1", "x", RuleStatus.UNINTERPRETABLE)])["R1"]
    assert kept.status is RuleStatus.UNINTERPRETABLE
    assert kept.reason == "before"


def test_planned_rules_take_the_planners_outcome_and_reason() -> None:
    plan = PlanResult(
        outcomes={
            "R1": RuleOutcome(RuleStatus.APPLIED, "3 change(s) made"),
            "R2": RuleOutcome(RuleStatus.NOT_APPLICABLE, "No element has the role"),
        }
    )
    done = _final([_rule("R1", "typography"), _rule("R2", "typography")], plan)
    assert done["R1"].status is RuleStatus.APPLIED
    assert done["R2"].reason == "No element has the role"


@pytest.mark.parametrize("category", ["color_token", "css_variable", "font_exception"])
def test_definitions_become_reference_rules(category: str) -> None:
    done = _final([_rule("R1", category)])["R1"]
    assert done.status is RuleStatus.REFERENCE


@pytest.mark.parametrize(
    ("category", "check"),
    [("min_contrast", "contrast"), ("forbid_color", "forbidden-color")],
)
def test_rules_enforced_by_a_passing_check_are_applied_with_its_evidence(
    category: str, check: str
) -> None:
    done = _final([_rule("R1", category)], checks=[_check(check)])["R1"]
    assert done.status is RuleStatus.APPLIED
    assert done.reason == f"Enforced by the {check} check: 12 checked"


def test_rule_enforced_by_a_failed_or_missing_check_is_not_applied() -> None:
    failed = _final([_rule("R1", "min_contrast")], checks=[_check("contrast", False)])[
        "R1"
    ]
    missing = _final([_rule("R1", "min_contrast")])["R1"]
    assert failed.status is RuleStatus.NOT_APPLICABLE
    assert "failed" in failed.reason
    assert "was not run" in missing.reason


def test_font_only_follows_the_font_family_rule_outcome() -> None:
    plan = PlanResult(outcomes={"F": RuleOutcome(RuleStatus.APPLIED, "21 change(s)")})
    rules = [_rule("F", "font_family"), _rule("O", "font_only")]
    assert _final(rules, plan)["O"].status is RuleStatus.APPLIED
    assert _final([_rule("O", "font_only")])["O"].status is RuleStatus.NOT_APPLICABLE


def test_unsupported_categories_are_not_applicable_and_say_deferred() -> None:
    done = _final([_rule("R1", "focus")])["R1"]
    assert done.status is RuleStatus.NOT_APPLICABLE
    assert done.reason == "No applier supports 'focus' rules yet (deferred)"


def test_no_rule_is_ever_left_pending() -> None:
    rules = [
        _rule(f"R{i}", c)
        for i, c in enumerate(["x", "color_token", "min_contrast", "focus"])
    ]
    assert all(
        r.status is not RuleStatus.PENDING
        for r in finalize_rules(rules, PlanResult(), [])
    )


def test_leaving_a_rule_pending_is_an_internal_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "brand_compliance.pipeline.finalize._decide",
        lambda *args: (RuleStatus.PENDING, "oops"),
    )
    with pytest.raises(BrandComplianceError):
        finalize_rules([_rule("R1", "x")], PlanResult(), [])
