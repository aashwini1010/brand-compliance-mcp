"""Shared logic for appliers: find the elements a rule targets and plan edits."""

import logging
from typing import Final

from lxml.html import HtmlElement

from brand_compliance.core.color import parse_color
from brand_compliance.core.css import parse_declarations
from brand_compliance.core.errors import InvalidInputError, ParseFailedError
from brand_compliance.models.artifact import ArtifactModel, ArtifactType
from brand_compliance.models.change import ApplyResult, Change, Skip
from brand_compliance.models.rule import Rule, Scope
from brand_compliance.plugins.appliers.support import EmailSupport

logger = logging.getLogger(__name__)

_SURFACE_SCOPES: Final = {Scope.LIGHT: "light", Scope.DARK: "dark"}
_ARTIFACT_SCOPES: Final = {
    Scope.STATIC: ArtifactType.STATIC,
    Scope.EMAIL: ArtifactType.EMAIL,
}


def role_matches(element_role: str, target: str) -> bool:
    """True if an element role is the target role or one of its variants."""
    return element_role == target or element_role.startswith(target + ".")


def same_value(first: str | None, second: str | None) -> bool:
    """Compare two CSS values, treating equal colours as equal."""
    if first is None or second is None:
        return False
    a = " ".join(first.lower().replace('"', "'").split())
    b = " ".join(second.lower().replace('"', "'").split())
    if a == b:
        return True
    try:
        return parse_color(a) == parse_color(b)
    except InvalidInputError:
        return False


def inline_declares(element: HtmlElement, prop: str) -> bool:
    """True if the element's own ``style`` attribute sets ``prop``."""
    try:
        return prop in parse_declarations(element.get("style") or "")
    except ParseFailedError:
        return False


class RoleStyleApplier:
    """Plan ``property: value`` edits for the elements that have a rule's role.

    Subclasses only set ``name`` and ``categories``.
    """

    name = "role-style"
    categories: frozenset[str] = frozenset()

    def __init__(
        self,
        aliases: dict[str, str] | None = None,
        email_support: EmailSupport | None = None,
    ) -> None:
        self._aliases = aliases or {}
        self._email_support = email_support

    def plan(self, rule: Rule, artifact: ArtifactModel) -> ApplyResult:
        """Return the changes for a rule and where it had to skip."""
        role, prop, value = rule.target_role, rule.property, rule.value
        if not (role and prop and value):
            return _nothing(rule, "The rule has no role, property or value to apply")
        wanted_type = _ARTIFACT_SCOPES.get(rule.scope)
        if wanted_type and wanted_type is not artifact.artifact_type:
            return _nothing(rule, f"The rule is for {rule.scope.value} artifacts only")
        targets = self._elements(role, artifact)
        if not targets:
            return _nothing(rule, f"No element in the artifact has the role '{role}'")
        wanted = _SURFACE_SCOPES.get(rule.scope)
        result = ApplyResult()
        eligible = 0
        for path, element in targets:
            surface = artifact.surfaces.get(path, "unknown")
            if wanted and surface == "unknown":
                result.skipped.append(
                    Skip(
                        rule_id=rule.id,
                        location=path,
                        reason="The surface behind this element is unknown",
                    )
                )
                continue
            if wanted and surface != wanted:
                continue
            eligible += 1
            outcome = self._change(rule, artifact, path, element, prop, value, wanted)
            if outcome is None:
                result.satisfied += 1
            elif isinstance(outcome, Skip):
                result.skipped.append(outcome)
            else:
                result.changes.append(outcome)
        if eligible == 0 and not result.skipped:
            return _nothing(
                rule, f"No '{role}' element sits on a {rule.scope.value} surface"
            )
        return result

    def _elements(
        self, role: str, artifact: ArtifactModel
    ) -> list[tuple[str, HtmlElement]]:
        target = self._aliases.get(role, role)
        return [
            (path, artifact.tree.xpath(path)[0])
            for path, element_role in artifact.roles.items()
            if role_matches(element_role, target)
        ]

    def _change(
        self,
        rule: Rule,
        artifact: ArtifactModel,
        path: str,
        element: HtmlElement,
        prop: str,
        value: str,
        surface: str | None,
    ) -> Change | Skip | None:
        """One edit, a skip (value unusable here), or None (already matches)."""
        note: str | None = None
        if artifact.artifact_type is ArtifactType.EMAIL and self._email_support:
            adapted = self._email_support.adapt(prop, value)
            if adapted.value is None:
                return Skip(
                    rule_id=rule.id,
                    location=path,
                    reason=adapted.rejected_because or "Not supported in email",
                )
            value, note, prop = adapted.value, adapted.note, adapted.property or prop
        before = artifact.styles.declared(element, prop)
        if same_value(before, value):
            return None  # already matches the guide: nothing to edit
        inline = inline_declares(element, prop)
        if inline:
            note = "; ".join(filter(None, [note, "Overrides an inline style"]))
        return Change(
            id=f"{rule.id}/{path}/{prop}",
            rule_id=rule.id,
            location=path,
            property=prop,
            before=before,
            after=value,
            surface=surface,
            important=inline and artifact.artifact_type is not ArtifactType.EMAIL,
            note=note,
        )


def _nothing(rule: Rule, reason: str) -> ApplyResult:
    return ApplyResult(skipped=[Skip(rule_id=rule.id, reason=reason)])
