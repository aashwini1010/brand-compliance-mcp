"""Find contradictions between rules. The detector never picks a winner.

Policy:
- An unresolved contradiction marks every *applicable* (pending) participant
  ``conflict_unresolved``; none of them is applied.
- Participants that are already unapplied are listed in the conflict but keep
  their own status.
- A contradiction is "resolved" only when the guide itself states the
  exception; the resolution points to where.
"""

import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Final

from brand_compliance.models.conflict import Conflict, ConflictKind
from brand_compliance.models.rule import Rule, RuleStatus, Scope
from brand_compliance.rules.vocabulary import Vocabulary

_RESTRICTIONS: Final = {
    "forbid_effect",
    "forbid_color",
    "font_only",
    "font_exception",
    "min_contrast",
}
_NOT_STYLES: Final = {"unmatched", "directive"}
_GENERIC_FAMILIES: Final = {
    "serif",
    "sans-serif",
    "monospace",
    "cursive",
    "fantasy",
    "system-ui",
    "inherit",
    "initial",
}


@dataclass
class _Finding:
    kind: ConflictKind
    rule_ids: list[str]
    description: str
    resolution: str = ""
    resolved: bool = field(init=False)

    def __post_init__(self) -> None:
        self.resolved = bool(self.resolution)


def detect_conflicts(
    rules: list[Rule], vocabulary: Vocabulary
) -> tuple[list[Rule], list[Conflict]]:
    """Return the rules with conflicts applied, plus the list of conflicts."""
    findings = [
        *_forbidden_effects(rules, vocabulary),
        *_font_restrictions(rules),
        *_value_clashes(rules),
    ]
    conflicts = [
        Conflict(
            id=f"C{number:03d}",
            kind=finding.kind,
            rule_ids=sorted(set(finding.rule_ids)),
            description=finding.description,
            resolved=finding.resolved,
            resolution=finding.resolution,
        )
        for number, finding in enumerate(findings, start=1)
    ]
    return _apply(rules, conflicts), conflicts


# ---- detection -----------------------------------------------------------


def _is_style(rule: Rule) -> bool:
    return (
        rule.property is not None
        and rule.value is not None
        and rule.category not in _RESTRICTIONS | _NOT_STYLES
    )


def _forbidden_effects(rules: list[Rule], vocabulary: Vocabulary) -> list[_Finding]:
    findings: list[_Finding] = []
    for restriction in (r for r in rules if r.category == "forbid_effect"):
        words = vocabulary.effect_words.get(restriction.value or "", [])
        if not words:
            continue
        pattern = re.compile(
            "|".join(rf"\b{re.escape(word)}" for word in words), re.IGNORECASE
        )
        users = [
            r
            for r in rules
            if _is_style(r) and pattern.search(f"{r.property} {r.value}")
        ]
        if users:
            findings.append(
                _Finding(
                    ConflictKind.FORBIDDEN_EFFECT,
                    [restriction.id, *(r.id for r in users)],
                    f"Guide forbids '{restriction.value}' but also specifies "
                    f"{len(users)} style(s) that use it",
                )
            )
    return findings


def _first_family(value: str) -> str:
    return value.split(",")[0].strip().strip("\"'")


def _font_restrictions(rules: list[Rule]) -> list[_Finding]:
    only = [r for r in rules if r.category == "font_only"]
    if not only:
        return []
    allowed = {(r.value or "").lower() for r in only}
    exceptions = [r for r in rules if r.category == "font_exception"]
    offenders: dict[str, list[Rule]] = defaultdict(list)
    for rule in rules:
        if rule.property != "font-family" or rule.category in _RESTRICTIONS:
            continue
        family = _first_family(rule.value or "")
        if family and family.lower() not in allowed | _GENERIC_FAMILIES:
            offenders[family].append(rule)
    findings: list[_Finding] = []
    for family, users in offenders.items():
        exception = next(
            (e for e in exceptions if (e.value or "").lower() == family.lower()), None
        )
        ids = [*(r.id for r in only), *(r.id for r in users)]
        description = (
            f"Guide allows only {sorted(allowed)} but also uses '{family}' "
            f"in {len(users)} style(s)"
        )
        if exception:
            where = exception.source_span.describe()
            note = exception.notes[0] if exception.notes else ""
            findings.append(
                _Finding(
                    ConflictKind.FONT_RESTRICTION,
                    [*ids, exception.id],
                    description,
                    resolution=(
                        f"Resolved by the guide's own exception at {where}. {note}"
                    ),
                )
            )
        else:
            findings.append(_Finding(ConflictKind.FONT_RESTRICTION, ids, description))
    return findings


def _comparable(rule: Rule) -> bool:
    """A rule can clash only if it names a target role or is a named token."""
    return rule.target_role is not None or (rule.property or "").startswith("--")


def _scopes_overlap(first: Scope, second: Scope) -> bool:
    return first is second or Scope.ALL in (first, second)


def _value_clashes(rules: list[Rule]) -> list[_Finding]:
    groups: dict[tuple[str | None, str], list[Rule]] = defaultdict(list)
    for rule in rules:
        if rule.status is RuleStatus.PENDING and _is_style(rule) and _comparable(rule):
            groups[(rule.target_role, rule.property or "")].append(rule)
    findings: list[_Finding] = []
    for (role, prop), members in groups.items():
        clashing = _clashing(members)
        if clashing:
            values = sorted({(r.value or "") for r in clashing})
            findings.append(
                _Finding(
                    ConflictKind.VALUE_CLASH,
                    [r.id for r in clashing],
                    f"{role or 'token'} {prop} is set to different values: {values}",
                )
            )
    return findings


def _clashing(members: list[Rule]) -> list[Rule]:
    result: dict[str, Rule] = {}
    for first in members:
        for second in members:
            if (
                first.id < second.id
                and _normal(first.value) != _normal(second.value)
                and _scopes_overlap(first.scope, second.scope)
            ):
                result[first.id] = first
                result[second.id] = second
    return list(result.values())


def _normal(value: str | None) -> str:
    return " ".join((value or "").lower().split())


# ---- applying results ----------------------------------------------------


def _apply(rules: list[Rule], conflicts: Iterable[Conflict]) -> list[Rule]:
    by_id = {rule.id: rule.model_copy(deep=True) for rule in rules}
    for conflict in conflicts:
        for rule_id in conflict.rule_ids:
            rule = by_id[rule_id]
            if conflict.resolved:
                rule.notes.append(f"{conflict.id} (resolved): {conflict.resolution}")
                continue
            rule.conflicts_with = sorted(
                {*rule.conflicts_with, *(i for i in conflict.rule_ids if i != rule_id)}
            )
            if rule.status is RuleStatus.PENDING:
                rule.status = RuleStatus.CONFLICT_UNRESOLVED
                rule.reason = f"{conflict.id}: {conflict.description}"
    return [by_id[rule.id] for rule in rules]
