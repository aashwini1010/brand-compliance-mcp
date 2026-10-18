"""Tests for brand_compliance.rules.directives (through the full pipeline)."""

from collections.abc import Callable

from brand_compliance.models.rule import Rule, RuleStatus, Scope, Severity

Interpret = Callable[[str], list[Rule]]

TOKENS = """\
| Token | Hex |
|---|---|
| `--pulse` | `#52E081` |
| `--beam` | `#E5FD84` |
| `--linen` | `#F6F3F0` |
| `--moss` | `#0C2226` |
| `--tide` | `#09A78D` |

"""


def _by(rules: list[Rule], category: str) -> list[Rule]:
    return [r for r in rules if r.category == category]


def test_never_use_colour_on_surface_becomes_forbid_rules(interpret: Interpret) -> None:
    text = TOKENS + (
        "- **NEVER** use `--pulse` (`#52E081`) or `--beam` as body text "
        "on `--linen` — fails WCAG AA.\n"
    )
    rules = _by(interpret(text), "forbid_color")
    assert {r.value for r in rules} == {"#52e081", "#e5fd84"}
    assert all(r.scope is Scope.LIGHT for r in rules)
    assert all(r.target_role == "text.body" for r in rules)
    assert all(r.severity is Severity.HARD for r in rules)


def test_forbid_colour_on_mixed_surfaces_is_not_guessed(interpret: Interpret) -> None:
    text = TOKENS + "- NEVER use `--pulse` as body text on `--linen` or `--moss`.\n"
    rules = interpret(text)
    assert _by(rules, "forbid_color") == []
    assert any(r.status is RuleStatus.UNINTERPRETABLE for r in rules)


def test_forbid_colour_with_unknown_token_is_not_guessed(interpret: Interpret) -> None:
    text = TOKENS + "- NEVER use `--nope` as body text on `--linen`.\n"
    assert _by(interpret(text), "forbid_color") == []


def test_minimum_contrast_becomes_a_hard_rule(interpret: Interpret) -> None:
    text = "- Body text minimum contrast ratio: **4.5:1** against its surface.\n"
    rule = _by(interpret(text), "min_contrast")[0]
    assert (rule.value, rule.target_role) == ("4.5", "text.body")
    assert rule.severity is Severity.HARD


def test_use_font_exclusively_becomes_font_only(interpret: Interpret) -> None:
    text = "| Do | Don't |\n|---|---|\n| Use Montserrat exclusively | Mix fonts |\n"
    assert _by(interpret(text), "font_only")[0].value == "Montserrat"


def test_no_other_font_families_uses_the_guides_font(interpret: Interpret) -> None:
    text = (
        '```css\n--font-sans: "Montserrat", sans-serif;\n```\n\n'
        "- **No other font families.**\n"
    )
    assert _by(interpret(text), "font_only")[0].value == "Montserrat"


def test_no_other_font_families_without_known_font_is_not_guessed(
    interpret: Interpret,
) -> None:
    rules = interpret("- **No other font families.**\n")
    assert _by(rules, "font_only") == []
    assert rules[0].status is RuleStatus.UNINTERPRETABLE


def test_dont_column_effects_become_forbid_effect_rules(interpret: Interpret) -> None:
    text = (
        "| Do | Don't |\n|---|---|\n"
        "| Use waves | Add gradients, glows, or glassmorphism |\n"
    )
    effects = {r.value for r in _by(interpret(text), "forbid_effect")}
    assert effects == {"gradient", "glow", "glassmorphism"}


def test_effect_in_a_topic_row_is_not_made_global(interpret: Interpret) -> None:
    text = (
        "| Rule | Do | Don't |\n|---|---|---|\n"
        "| Background | Transparent | Gradient background behind logo |\n"
    )
    assert _by(interpret(text), "forbid_effect") == []


def test_default_surface_becomes_page_background(interpret: Interpret) -> None:
    text = (
        TOKENS
        + "| Do | Don't |\n|---|---|\n| Default surface is `--linen` | Dark site |\n"
    )
    rule = _by(interpret(text), "surface")[0]
    assert (rule.target_role, rule.property, rule.value) == (
        "page.surface",
        "background",
        "#f6f3f0",
    )


def test_focus_ring_becomes_outline_and_offset_rules(interpret: Interpret) -> None:
    text = TOKENS + (
        "- **Always** include focus ring: "
        "`outline: 2px solid --tide; outline-offset: 2px`.\n"
    )
    values = {r.property: r.value for r in _by(interpret(text), "focus")}
    assert values == {"outline": "2px solid #09a78d", "outline-offset": "2px"}


def test_unsupported_directive_is_reported_not_guessed(interpret: Interpret) -> None:
    rules = interpret("- Always remember to smile.\n")
    assert rules[0].status is RuleStatus.UNINTERPRETABLE
    assert "not one of the supported patterns" in rules[0].reason


def test_surface_phrase_is_understood_without_tokens(interpret: Interpret) -> None:
    text = TOKENS + "- Never use `--pulse` as body text on light surfaces.\n"
    rule = _by(interpret(text), "forbid_color")[0]
    assert rule.scope is Scope.LIGHT


def test_unknown_surface_phrase_is_not_guessed(interpret: Interpret) -> None:
    text = TOKENS + "- Never use `--pulse` as body text on busy photos.\n"
    assert _by(interpret(text), "forbid_color") == []


def test_font_exception_sentence_becomes_an_exception_rule(
    interpret: Interpret,
) -> None:
    text = (
        "Note: the `Caveat` handwriting only appears in **developer docs and "
        "templates**, never customer-facing marketing.\n"
    )
    rule = _by(interpret(text), "font_exception")[0]
    assert rule.value == "Caveat"
    assert "developer docs and templates" in rule.notes[0]


def test_prompt_style_focus_ring_becomes_outline_rules(interpret: Interpret) -> None:
    line = "All buttons: focus ring 2px solid #09A78D with 4px offset. Always keep it."
    text = TOKENS + f"```\n  {line}\n```\n"
    values = {r.property: r.value for r in _by(interpret(text), "focus")}
    assert values == {"outline": "2px solid #09a78d", "outline-offset": "4px"}


def test_directive_lines_inside_untagged_code_are_read_with_line_numbers(
    interpret: Interpret,
) -> None:
    text = "```\nintro\n- Body text minimum contrast ratio: 4.5:1\n```\n"
    rule = _by(interpret(text), "min_contrast")[0]
    assert rule.source_span.line_start == 3
