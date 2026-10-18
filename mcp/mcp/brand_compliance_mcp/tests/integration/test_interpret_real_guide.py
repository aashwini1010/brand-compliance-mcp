"""Interpreting the real Myridius guide end to end."""

from pathlib import Path

import pytest

from brand_compliance.core.contracts import RuleExtractor
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.models.guide import GuideDocument, NodeKind
from brand_compliance.models.rule import Rule, RuleStatus, Scope
from brand_compliance.plugins.extractors import register_extractors
from brand_compliance.plugins.sources.markdown import MarkdownSourceAdapter
from brand_compliance.rules.interpret import GuideInterpretation, interpret_guide
from brand_compliance.rules.vocabulary import load_vocabulary


@pytest.fixture(scope="module")
def guide(myridius_guide_path_module: Path) -> GuideDocument:
    return MarkdownSourceAdapter().load(myridius_guide_path_module)


@pytest.fixture(scope="module")
def interpretation(guide: GuideDocument) -> GuideInterpretation:
    registry = PluginRegistry()
    vocabulary = load_vocabulary()
    register_extractors(
        registry, bullet_specs=[(s.section, s.label) for s in vocabulary.bullet_specs]
    )
    return interpret_guide(guide, registry.plugins(RuleExtractor), vocabulary)


@pytest.fixture(scope="module")
def rules(interpretation: GuideInterpretation) -> list[Rule]:
    return interpretation.rules


def _one(rules: list[Rule], **fields: object) -> Rule:
    found = [r for r in rules if all(getattr(r, k) == v for k, v in fields.items())]
    assert len(found) == 1, f"expected one rule for {fields}, found {len(found)}"
    return found[0]


def test_every_rule_has_a_status_other_than_pending_or_is_pending_on_purpose(
    rules: list[Rule],
) -> None:
    allowed = {
        RuleStatus.PENDING,
        RuleStatus.UNINTERPRETABLE,
        RuleStatus.NOT_APPLICABLE,
        RuleStatus.CONFLICT_UNRESOLVED,
    }
    assert {r.status for r in rules} <= allowed


def test_rules_that_were_not_understood_always_say_why(rules: list[Rule]) -> None:
    unclear = [r for r in rules if r.status is not RuleStatus.PENDING]
    assert unclear
    assert all(r.reason.strip() for r in unclear)


def test_rule_ids_are_unique_and_ordered(rules: list[Rule]) -> None:
    ids = [r.id for r in rules]
    assert ids == [f"R{n:03d}" for n in range(1, len(ids) + 1)]


def test_nothing_in_the_guide_is_silently_dropped(
    guide: GuideDocument, rules: list[Rule]
) -> None:
    """Every paragraph, bullet, table row and code block maps to some rule."""
    covered: set[int] = set()
    for rule in rules:
        start = rule.source_span.line_start or 0
        covered.update(range(start, (rule.source_span.line_end or start) + 1))
    missing: list[str] = []
    for node in guide.walk():
        start = node.span.line_start or 0
        if node.kind in (NodeKind.PARAGRAPH, NodeKind.LIST_ITEM):
            lines = [start]
        elif node.kind is NodeKind.CODE:
            lines = list(range(start, (node.span.line_end or start) + 1))
            lines = [line for line in lines if line in covered][:1] or [start]
        elif node.kind is NodeKind.TABLE:
            lines = list(node.row_lines)
        else:
            continue
        missing.extend(f"line {line}" for line in lines if line not in covered)
    assert missing == []


def test_palette_has_all_18_tokens_with_correct_scopes(rules: list[Rule]) -> None:
    tokens = [r for r in rules if r.category == "color_token"]
    assert len(tokens) == 18
    assert (
        _one(rules, category="color_token", property="--virtual-tide").value
        == "#09a78d"
    )
    assert (
        _one(rules, category="color_token", property="--dm-text-linen").scope
        is Scope.DARK
    )
    assert (
        _one(rules, category="color_token", property="--lm-text-moss").scope
        is Scope.LIGHT
    )


def test_only_the_genuine_hsl_disagreement_is_noted(rules: list[Rule]) -> None:
    noted = [r.property for r in rules if r.category == "color_token" and r.notes]
    assert noted == ["--neural-beam"]


def test_type_scale_covers_all_twelve_tokens(rules: list[Rule]) -> None:
    roles = {r.target_role for r in rules if r.category == "typography"}
    assert len(roles) == 12
    assert (
        _one(rules, target_role="heading.display", property="font-weight").value
        == "800"
    )


def test_primary_button_rules_match_the_guide_table(rules: list[Rule]) -> None:
    primary = {
        r.property: r.value
        for r in rules
        if r.target_role == "button.primary" and r.status is RuleStatus.PENDING
    }
    assert primary == {"background": "#09a78d", "color": "#ffffff", "border": "none"}


def test_pulse_green_and_neural_beam_are_forbidden_as_body_text_on_light(
    rules: list[Rule],
) -> None:
    forbidden = {
        r.value
        for r in rules
        if r.category == "forbid_color" and r.scope is Scope.LIGHT
    }
    assert forbidden == {"#52e081", "#e5fd84"}


def test_hard_rules_from_the_guide_are_captured(rules: list[Rule]) -> None:
    assert _one(rules, category="min_contrast").value == "4.5"
    assert _one(rules, category="font_only").value == "Montserrat"
    assert {r.value for r in rules if r.category == "forbid_effect"} == {
        "gradient",
        "glow",
        "glassmorphism",
    }
    offsets = {
        r.value
        for r in rules
        if r.category == "focus" and r.property == "outline-offset"
    }
    assert offsets == {"2px", "4px"}


def test_logo_rules_are_not_applicable_and_say_never_invent(rules: list[Rule]) -> None:
    logo = [r for r in rules if r.source_span.heading_path[-1:] == ("5. Logo Usage",)]
    assert logo
    assert {r.status for r in logo} == {RuleStatus.NOT_APPLICABLE}
    assert all("never invents a logo" in r.reason for r in logo)


def test_voice_guidance_is_could_not_interpret(rules: list[Rule]) -> None:
    voice = [
        r for r in rules if r.source_span.heading_path[-1:] == ("9. Voice & Copy",)
    ]
    assert voice
    assert {r.status for r in voice} == {RuleStatus.UNINTERPRETABLE}


def test_gradient_card_css_is_kept_with_its_role(rules: list[Rule]) -> None:
    card = [r for r in rules if r.target_role == "card.gradient"]
    assert any("linear-gradient" in (r.value or "") for r in card)


def test_button_and_form_bullets_are_read_with_exact_values(rules: list[Rule]) -> None:
    def spec(role: str, prop: str) -> str | None:
        found = [
            r
            for r in rules
            if r.category == "component_spec"
            and r.target_role == role
            and r.property == prop
            and r.status is RuleStatus.PENDING
        ]
        return found[0].value if found else None

    assert spec("button", "border-radius") == "999px"
    assert spec("button.large", "padding") == "16px 36px"
    assert spec("button.destructive", "background") == "#c84b47"
    assert spec("input", "padding") == "14px 16px"
    assert spec("input.focus", "box-shadow") == "0 0 0 4px #09a78d26"
    assert spec("form.helper", "color") == "#337077"


def test_bullet_pieces_that_stay_uninterpretable_are_the_known_ones(
    rules: list[Rule],
) -> None:
    unclear = {
        r.value
        for r in rules
        if r.category == "component_spec" and r.status is RuleStatus.UNINTERPRETABLE
    }
    assert unclear == {
        "12px (modern) or 8px (compact)",
        "sits above input",
        "Bold (700+)",
        "tight line-height (1.05–1.15)",
        "slightly negative letter-spacing",
        "letter-spacing +0.08em to +0.12em",
    }


def test_text_colours_per_surface_are_read_from_the_style_rules(
    rules: list[Rule],
) -> None:
    colours = {
        (r.target_role, r.scope.value): r.value
        for r in rules
        if r.category == "color" and r.status is RuleStatus.PENDING
    }
    assert colours == {
        ("text.eyebrow", "light"): "#09a78d",
        ("text.eyebrow", "dark"): "#52e081",
        ("text.body", "light"): "#194247",
        ("text.body", "dark"): "#f6f3f0",
    }


def test_exactly_the_three_known_contradictions_are_found(
    interpretation: GuideInterpretation,
) -> None:
    summary = sorted((c.kind.value, c.resolved) for c in interpretation.conflicts)
    assert summary == [
        ("font_restriction", True),
        ("forbidden_effect", False),
        ("value_clash", False),
    ]


def test_gradient_contradiction_leaves_both_sides_unapplied(
    interpretation: GuideInterpretation,
) -> None:
    conflict = next(
        c for c in interpretation.conflicts if c.kind.value == "forbidden_effect"
    )
    sides = {r.id: r for r in interpretation.rules if r.id in conflict.rule_ids}
    assert any(r.category == "forbid_effect" for r in sides.values())
    assert any(r.target_role == "card.gradient" for r in sides.values())
    pending_sides = [r for r in sides.values() if r.reason.startswith(conflict.id)]
    assert {r.status for r in pending_sides} == {RuleStatus.CONFLICT_UNRESOLVED}


def test_caveat_font_is_resolved_by_the_guides_own_exception(
    interpretation: GuideInterpretation,
) -> None:
    conflict = next(
        c for c in interpretation.conflicts if c.kind.value == "font_restriction"
    )
    assert conflict.resolved
    assert "myridius-brand-guide.md:194" in conflict.resolution
    only = [r for r in interpretation.rules if r.category == "font_only"][0]
    assert only.status is RuleStatus.PENDING


def test_focus_offset_contradiction_names_both_guide_lines(
    interpretation: GuideInterpretation,
) -> None:
    conflict = next(
        c for c in interpretation.conflicts if c.kind.value == "value_clash"
    )
    sides = [r for r in interpretation.rules if r.id in conflict.rule_ids]
    assert sorted(r.source_span.line_start or 0 for r in sides) == [228, 460]
    assert {r.value for r in sides} == {"2px", "4px"}


def test_focus_outline_is_not_in_conflict_because_both_lines_agree(
    rules: list[Rule],
) -> None:
    outline = [r for r in rules if r.category == "focus" and r.property == "outline"]
    assert len(outline) == 1
    assert outline[0].status is RuleStatus.PENDING
    assert any("Also stated at" in n for n in outline[0].notes)
