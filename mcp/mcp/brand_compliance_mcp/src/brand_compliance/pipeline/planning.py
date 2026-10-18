"""Plan all edits: run the appliers, resolve overlaps, decide each rule's outcome."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field

from lxml.html import HtmlElement

from brand_compliance.core.contracts import RuleApplier
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import ROLLED_BACK_PREFIX, Change, Skip
from brand_compliance.models.rule import Rule, RuleStatus, Scope
from brand_compliance.plugins.artifacts.base import element_path

logger = logging.getLogger(__name__)

_MAX_REASONS = 3


@dataclass(frozen=True)
class RuleOutcome:
    """What became of one rule: applied, or not applicable with the reasons."""

    status: RuleStatus
    reason: str


@dataclass
class PlanResult:
    """The resolved edits, every skip, and the outcome of each handled rule."""

    changes: list[Change] = field(default_factory=list)
    skipped: list[Skip] = field(default_factory=list)
    outcomes: dict[str, RuleOutcome] = field(default_factory=dict)
    handled: set[str] = field(default_factory=set)
    satisfied: set[str] = field(default_factory=set)

    def rolled_back(self, reasons: dict[str, str]) -> "PlanResult":
        """Return a plan without the given changes (id -> why), kept as skips."""
        undone = [c for c in self.changes if c.id in reasons]
        kept = [c for c in self.changes if c.id not in reasons]
        skips = [
            *self.skipped,
            *(
                Skip(
                    rule_id=c.rule_id,
                    location=c.location,
                    reason=f"{ROLLED_BACK_PREFIX}{reasons[c.id]}",
                )
                for c in undone
            ),
        ]
        return PlanResult(
            changes=kept,
            skipped=skips,
            outcomes=_outcomes(self.handled, kept, skips, self.satisfied),
            handled=self.handled,
            satisfied=self.satisfied,
        )


def plan_changes(
    rules: list[Rule], artifact: ArtifactModel, appliers: list[RuleApplier]
) -> PlanResult:
    """Run every applier over the pending rules and resolve overlapping edits."""
    by_id = {rule.id: rule for rule in rules}
    order = {rule.id: index for index, rule in enumerate(rules)}
    raw: list[Change] = []
    skips: list[Skip] = []
    satisfied: set[str] = set()
    handled: set[str] = set()
    for rule in rules:
        if rule.status is not RuleStatus.PENDING:
            continue
        applier = next((a for a in appliers if rule.category in a.categories), None)
        if applier is None:
            continue
        outcome = applier.plan(rule, artifact)
        if getattr(applier, "passive", False) and not (
            outcome.changes or outcome.skipped or outcome.satisfied
        ):
            continue  # nothing to do: the rule stays a plain reference definition
        handled.add(rule.id)
        raw.extend(outcome.changes)
        skips.extend(outcome.skipped)
        if outcome.satisfied:
            satisfied.add(rule.id)
    kept, overridden = _resolve_overlaps(raw, by_id, order)
    skips.extend(overridden)
    ordered = _number(kept, artifact)
    outcomes = _outcomes(handled, ordered, skips, satisfied)
    logger.info(
        "Planned %d change(s), %d skip(s) for %d rule(s)",
        len(ordered),
        len(skips),
        len(handled),
    )
    return PlanResult(ordered, skips, outcomes, handled, satisfied)


def _specificity(rule: Rule, order: int) -> tuple[int, int, int]:
    depth = len(rule.target_role.split(".")) if rule.target_role else 0
    scoped = 1 if rule.scope in (Scope.LIGHT, Scope.DARK) else 0
    return (depth, scoped, order)


def _resolve_overlaps(
    changes: list[Change], by_id: dict[str, Rule], order: dict[str, int]
) -> tuple[list[Change], list[Skip]]:
    """Keep one change per element and property: the most specific rule wins."""
    groups: dict[tuple[str, str, str | None], list[Change]] = defaultdict(list)
    for change in changes:
        # a colour variable has a value per surface, so light and dark never clash
        surface = change.surface if change.property.startswith("--") else None
        groups[(change.location, change.property, surface)].append(change)
    kept: list[Change] = []
    overridden: list[Skip] = []
    for group in groups.values():
        ranked = sorted(
            group,
            key=lambda c: _specificity(by_id[c.rule_id], order[c.rule_id]),
            reverse=True,
        )
        winner = ranked[0]
        kept.append(winner)
        for loser in ranked[1:]:
            if loser.rule_id == winner.rule_id:
                continue
            overridden.append(
                Skip(
                    rule_id=loser.rule_id,
                    location=loser.location,
                    reason=(
                        f"Overridden by rule {winner.rule_id} (more specific, or "
                        f"later in the guide) for {loser.property}"
                    ),
                )
            )
    return kept, overridden


def _number(changes: list[Change], artifact: ArtifactModel) -> list[Change]:
    """Order changes as the elements appear in the document; number them."""
    position = {
        element_path(el): index
        for index, el in enumerate(artifact.tree.iter())
        if isinstance(el, HtmlElement)
    }
    ordered = sorted(
        changes, key=lambda c: (position.get(c.location, 0), c.property, c.rule_id)
    )
    return [
        change.model_copy(update={"id": f"CH{number:03d}"})
        for number, change in enumerate(ordered, start=1)
    ]


def _outcomes(
    handled: set[str],
    changes: list[Change],
    skips: list[Skip],
    satisfied: set[str],
) -> dict[str, RuleOutcome]:
    changed: dict[str, int] = defaultdict(int)
    for change in changes:
        changed[change.rule_id] += 1
    reasons: dict[str, list[str]] = defaultdict(list)
    for skip in skips:
        if skip.reason not in reasons[skip.rule_id]:
            reasons[skip.rule_id].append(skip.reason)
    rolled: dict[str, int] = defaultdict(int)
    for skip in skips:
        if skip.reason.startswith(ROLLED_BACK_PREFIX):
            rolled[skip.rule_id] += 1
    outcomes: dict[str, RuleOutcome] = {}
    for rule_id in sorted(handled):
        if changed[rule_id]:
            text = f"{changed[rule_id]} change(s) made"
            if rolled[rule_id]:
                text += f"; {rolled[rule_id]} rolled back"
            outcomes[rule_id] = RuleOutcome(RuleStatus.APPLIED, text)
        elif rule_id in satisfied:
            outcomes[rule_id] = RuleOutcome(
                RuleStatus.APPLIED, "The artifact already matches this rule"
            )
        else:
            why = "; ".join(reasons[rule_id][:_MAX_REASONS]) or "Nothing to apply"
            outcomes[rule_id] = RuleOutcome(RuleStatus.NOT_APPLICABLE, why)
    return outcomes
