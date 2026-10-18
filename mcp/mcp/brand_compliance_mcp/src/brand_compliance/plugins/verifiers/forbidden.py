"""Check that no change introduces a colour the guide forbids for a role."""

from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import Change
from brand_compliance.models.report import CheckResult
from brand_compliance.models.rule import Rule, RuleStatus, Scope
from brand_compliance.plugins.appliers.base import role_matches, same_value


class ForbiddenColorVerifier:
    """Fails when a change sets a forbidden colour on the role and surface it names."""

    name = "forbidden-color"
    scope = "changes"

    def check(
        self,
        original: ArtifactModel,
        output: ArtifactModel,  # noqa: ARG002 (works from the plan, not the output)
        rules: list[Rule],
        changes: list[Change],
    ) -> CheckResult:
        """Return the changes that apply a forbidden colour."""
        bans = [
            r
            for r in rules
            if r.category == "forbid_color"
            and r.status is RuleStatus.PENDING
            and r.target_role
            and r.value
        ]
        reasons: dict[str, str] = {}
        for change in changes:
            if change.property != "color":
                continue
            role = original.roles.get(change.location, "")
            for ban in bans:
                if _violates(change, role, ban):
                    reasons[change.id] = (
                        f"{ban.value} is forbidden for {ban.target_role} on "
                        f"{ban.scope.value} surfaces (rule {ban.id})"
                    )
        return CheckResult(
            name=self.name,
            passed=not reasons,
            details=[f"{len(bans)} colour ban(s) checked, {len(reasons)} violation(s)"],
            failed_change_ids=sorted(reasons),
            change_reasons=reasons,
        )


def _violates(change: Change, role: str, ban: Rule) -> bool:
    if not (ban.target_role and role_matches(role, ban.target_role)):
        return False
    if ban.scope in (Scope.LIGHT, Scope.DARK) and change.surface != ban.scope.value:
        return False
    return same_value(change.after, ban.value)
