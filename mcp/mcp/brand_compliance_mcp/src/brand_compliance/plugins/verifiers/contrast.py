"""Check that text stays readable after the changes, and name what broke it.

The check works on the *planned* edits: it asks the original page's style index
what each piece of text would look like with the changes applied, and traces
each colour back to the element (and change) that supplied it.
"""

import logging
from dataclasses import dataclass
from typing import Final

from lxml.html import HtmlElement

from brand_compliance.core.cascade import StyleIndex
from brand_compliance.core.color import Color
from brand_compliance.core.contrast import AA_NORMAL_TEXT, contrast_ratio
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import Change
from brand_compliance.models.report import CheckResult
from brand_compliance.models.rule import Rule, RuleStatus
from brand_compliance.plugins.artifacts.base import (
    describe_element,
    element_path,
    has_own_text,
    is_content_element,
)

logger = logging.getLogger(__name__)

_FOREGROUND: Final = ("color",)
_BACKGROUND: Final = ("background", "background-color")
_EPSILON: Final = 0.01


@dataclass(frozen=True)
class _Pair:
    foreground: Color
    background: Color
    foreground_source: HtmlElement | None
    background_source: HtmlElement | None

    @property
    def ratio(self) -> float:
        return contrast_ratio(self.foreground, self.background)


class ContrastVerifier:
    """Fails when a change leaves text below the minimum contrast ratio."""

    name = "contrast"
    scope = "changes"

    def __init__(self, minimum: float = AA_NORMAL_TEXT) -> None:
        self._default_minimum = minimum

    def check(
        self,
        original: ArtifactModel,
        output: ArtifactModel,  # noqa: ARG002 (works from the plan, not the output)
        rules: list[Rule],
        changes: list[Change],
    ) -> CheckResult:
        """Return the changes that made text unreadable, with the reason for each."""
        minimum = self._minimum(rules)
        before = original.styles
        overrides = _overrides(changes, original.tree)
        after = before.with_overrides(overrides)
        by_target = {(c.location, c.property): c for c in changes}
        reasons: dict[str, str] = {}
        checked = unchecked = preexisting = 0
        for element in original.tree.iter():
            if not isinstance(element, HtmlElement) or not (
                is_content_element(element) and has_own_text(element)
            ):
                continue
            pair_after = _pair(after, element)
            if pair_after is None:
                unchecked += 1
                continue
            checked += 1
            if pair_after.ratio >= minimum:
                continue
            pair_before = _pair(before, element)
            not_worse = (
                pair_before is not None
                and pair_after.ratio >= pair_before.ratio - _EPSILON
            )
            if not_worse and pair_before is not None and pair_before.ratio < minimum:
                preexisting += 1  # the page already failed; we did not make it worse
                continue
            blamed = _blame(element, pair_after, original, changes, by_target, minimum)
            for change in blamed:
                reasons.setdefault(change.id, _reason(element, pair_after, minimum))
        details = [
            f"{checked} text element(s) checked against {minimum}:1",
            f"{unchecked} could not be checked (background or colour unknown)",
            f"{preexisting} already failed before any change (not caused by this tool)",
            f"{len(reasons)} change(s) caused a failure",
        ]
        return CheckResult(
            name=self.name,
            passed=not reasons,
            details=details,
            failed_change_ids=sorted(reasons),
            change_reasons=reasons,
        )

    def _minimum(self, rules: list[Rule]) -> float:
        for rule in rules:
            if rule.category == "min_contrast" and rule.status is RuleStatus.PENDING:
                try:
                    return float(rule.value or "")
                except ValueError:
                    break
        return self._default_minimum


def _overrides(
    changes: list[Change], tree: HtmlElement
) -> dict[tuple[HtmlElement, str], str]:
    """Map (element, property) to the planned value.

    ``background`` also sets ``background-color``, as it does in CSS.
    """
    result: dict[tuple[HtmlElement, str], str] = {}
    for change in changes:
        is_variable = change.property.startswith("--") and change.surface != "dark"
        if not is_variable and change.property not in (*_FOREGROUND, *_BACKGROUND):
            continue
        element = tree.xpath(change.location)[0]
        result[(element, change.property)] = change.after
        if change.property == "background":
            result[(element, "background-color")] = change.after
    return result


def _pair(index: StyleIndex, element: HtmlElement) -> _Pair | None:
    foreground, fg_source = index.text_color(element)
    background, bg_source = index.background_with_source(element)
    if foreground is None or background is None:
        return None
    return _Pair(foreground, background, fg_source, bg_source)


def _blame(
    element: HtmlElement,
    pair: _Pair,
    original: ArtifactModel,
    changes: list[Change],
    by_target: dict[tuple[str, str], Change],
    minimum: float,
) -> list[Change]:
    """Pick the change(s) to undo: the text colour first, then the background."""
    fg = _change_at(pair.foreground_source, _FOREGROUND, by_target)
    bg = _change_at(pair.background_source, _BACKGROUND, by_target)
    if fg is None and bg is None:  # the colour may come from a remapped variable
        fg = _variable_change(pair.foreground, changes)
        bg = _variable_change(pair.background, changes)
    for group in ([fg], [bg], [fg, bg]):
        if not all(group):
            continue
        undone = {c.id for c in group if c}
        remaining = [c for c in changes if c.id not in undone]
        view = original.styles.with_overrides(_overrides(remaining, original.tree))
        retry = _pair(view, element)
        if retry is not None and retry.ratio >= minimum:
            return [c for c in group if c]
    return [c for c in (fg, bg) if c]


def _variable_change(color: Color, changes: list[Change]) -> Change | None:
    """The light-surface variable change whose new colour is ``color``, if any."""
    for change in changes:
        if (
            change.property.startswith("--")
            and change.surface != "dark"
            and change.after.lower() == color.to_hex().lower()
        ):
            return change
    return None


def _change_at(
    source: HtmlElement | None,
    properties: tuple[str, ...],
    by_target: dict[tuple[str, str], Change],
) -> Change | None:
    if source is None:
        return None
    path = element_path(source)
    for prop in properties:
        if (path, prop) in by_target:
            return by_target[(path, prop)]
    return None


def _reason(element: HtmlElement, pair: _Pair, minimum: float) -> str:
    return (
        f"contrast {pair.ratio:.2f}:1 is below {minimum:g}:1 for "
        f"{describe_element(element)} "
        f"(text {pair.foreground.to_hex()} on {pair.background.to_hex()})"
    )
