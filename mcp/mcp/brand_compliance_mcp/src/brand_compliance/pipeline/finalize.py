"""Decide the final status of every rule once planning and verification are done.

After this step no rule is ``pending``: each is applied, understood but not
applied, could not be interpreted, in conflict, or a reference definition.
"""

from typing import Final

from brand_compliance.core.errors import BrandComplianceError
from brand_compliance.models.report import CheckResult
from brand_compliance.models.rule import Rule, RuleStatus
from brand_compliance.pipeline.planning import PlanResult

# Definitions that other rules use; nothing to apply by themselves.
_REFERENCE: Final = {
    "color_token": "Palette token; its value is used by the rules that refer to it",
    "css_variable": "Design variable; not applied by itself",
    "font_exception": "Exception stated by the guide; used when checking font rules",
}
# Rules enforced by a check rather than by an edit: category -> check name.
_ENFORCED_BY: Final = {"min_contrast": "contrast", "forbid_color": "forbidden-color"}


def finalize_rules(
    rules: list[Rule], plan: PlanResult, checks: list[CheckResult]
) -> list[Rule]:
    """Return every rule with its final status and reason."""
    by_check = {check.name: check for check in checks}
    font_applied = any(
        outcome.status is RuleStatus.APPLIED
        for rule in rules
        if rule.category == "font_family" and (outcome := plan.outcomes.get(rule.id))
    )
    final: list[Rule] = []
    for rule in rules:
        if rule.status is not RuleStatus.PENDING:
            final.append(rule)
            continue
        status, reason = _decide(rule, plan, by_check, font_applied)
        final.append(rule.model_copy(update={"status": status, "reason": reason}))
    if any(rule.status is RuleStatus.PENDING for rule in final):
        raise BrandComplianceError("A rule was left without a final status")
    return final


def _decide(
    rule: Rule,
    plan: PlanResult,
    by_check: dict[str, CheckResult],
    font_applied: bool,
) -> tuple[RuleStatus, str]:
    outcome = plan.outcomes.get(rule.id)
    if outcome is not None:
        return outcome.status, outcome.reason
    if rule.category in _REFERENCE:
        return RuleStatus.REFERENCE, _REFERENCE[rule.category]
    check_name = _ENFORCED_BY.get(rule.category)
    if check_name is not None:
        return _from_check(check_name, by_check.get(check_name))
    if rule.category == "font_only":
        if font_applied:
            return RuleStatus.APPLIED, "Enforced through the font-family changes"
        return (
            RuleStatus.NOT_APPLICABLE,
            "Enforced through the font-family rule, which was not applied",
        )
    return (
        RuleStatus.NOT_APPLICABLE,
        f"No applier supports '{rule.category}' rules yet (deferred)",
    )


def _from_check(name: str, check: CheckResult | None) -> tuple[RuleStatus, str]:
    if check is None:
        return RuleStatus.NOT_APPLICABLE, f"The {name} check was not run"
    summary = check.details[0] if check.details else "no detail"
    if check.passed:
        return RuleStatus.APPLIED, f"Enforced by the {name} check: {summary}"
    return RuleStatus.NOT_APPLICABLE, f"The {name} check failed: {summary}"
