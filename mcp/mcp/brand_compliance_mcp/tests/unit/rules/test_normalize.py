"""Tests for brand_compliance.rules.normalize (through the full pipeline)."""

from collections.abc import Callable

from brand_compliance.models.rule import Rule, RuleStatus, Scope

Interpret = Callable[[str], list[Rule]]


def _find(rules: list[Rule], **fields: object) -> list[Rule]:
    return [r for r in rules if all(getattr(r, k) == v for k, v in fields.items())]


PALETTE = """\
## 2.1 Core Tokens

| Token | Hex | RGB | HSL | Use |
|---|---|---|---|---|
| `--tide` | `#09A78D` | `9 167 141` | `169 90% 35%` | Accent |
| `--white` | `#FFFFFF` | `255 255 255` | `0 0% 100%` | Surface |
| `--bad` | `#GGGGGG` | | | Broken |
"""


def test_palette_row_becomes_a_pending_colour_token(interpret: Interpret) -> None:
    rule = _find(interpret(PALETTE), category="color_token", property="--tide")[0]
    assert rule.value == "#09a78d"
    assert rule.status is RuleStatus.PENDING
    assert rule.reason == "Accent"


def test_palette_hsl_rounding_is_not_noted(interpret: Interpret) -> None:
    rule = _find(interpret(PALETTE), property="--tide")[0]
    assert rule.notes == []


def test_palette_large_hsl_disagreement_is_noted(interpret: Interpret) -> None:
    text = (
        "| Token | Hex | HSL |\n|---|---|---|\n| `--x` | `#E5FD84` | `76 97% 75%` |\n"
    )
    rule = _find(interpret(text), property="--x")[0]
    assert "disagrees with hex" in rule.notes[0]


def test_palette_rgb_mismatch_is_noted(interpret: Interpret) -> None:
    text = "| Token | Hex | RGB |\n|---|---|---|\n| `--x` | `#FFFFFF` | `1 2 3` |\n"
    assert "RGB column" in _find(interpret(text), property="--x")[0].notes[0]


def test_palette_unreadable_colour_is_could_not_interpret(interpret: Interpret) -> None:
    bad = [r for r in interpret(PALETTE) if "Unreadable colour" in r.reason]
    assert len(bad) == 1
    assert bad[0].status is RuleStatus.UNINTERPRETABLE


def test_palette_scope_follows_section_title(interpret: Interpret) -> None:
    text = (
        "## 2.2 Dark Mode Accent Palette\n\n| Token | Hex |\n|---|---|\n"
        "| `--a` | `#52E081` |\n"
    )
    assert _find(interpret(text), property="--a")[0].scope is Scope.DARK


TYPE_TABLE = """\
| Token | Size | Weight | Line-height | Letter-spacing | Use |
|---|---|---|---|---|---|
| `--fs-h1` | `clamp(2rem, 4vw, 4rem)` | 700 | 1.1 | -0.015em | Section title |
| `--fs-caption` | `0.8125rem (13px)` | 500 | 1.45 | +0.04em | Labels |
| `--fs-italic` | inherit | 400 italic | inherit | inherit | Quote |
| `--fs-body-sm` | `0.9rem (99px)` | 400 | 1.55 | 0 | Mismatch |
| `--fs-unknown` | 1rem | 400 | 1.5 | 0 | Unknown |
| `--fs-h2` | big | 700 | 1.1 | 0 | Bad size |
"""


def test_type_row_becomes_one_rule_per_property(interpret: Interpret) -> None:
    rules = _find(interpret(TYPE_TABLE), target_role="heading.h1")
    assert {r.property: r.value for r in rules} == {
        "font-size": "clamp(2rem, 4vw, 4rem)",
        "font-weight": "700",
        "line-height": "1.1",
        "letter-spacing": "-0.015em",
    }


def test_type_row_strips_plus_sign_and_px_annotation(interpret: Interpret) -> None:
    rules = _find(interpret(TYPE_TABLE), target_role="text.caption")
    values = {r.property: r.value for r in rules}
    assert values["letter-spacing"] == "0.04em"
    assert values["font-size"] == "0.8125rem"
    assert all(r.status is RuleStatus.PENDING for r in rules)


def test_type_row_splits_italic_weight_into_style(interpret: Interpret) -> None:
    rules = _find(interpret(TYPE_TABLE), target_role="text.quote")
    values = {r.property: r.value for r in rules}
    assert values["font-weight"] == "400"
    assert values["font-style"] == "italic"


def test_type_row_notes_disagreeing_px_annotation(interpret: Interpret) -> None:
    size = _find(
        interpret(TYPE_TABLE), target_role="text.secondary", property="font-size"
    )[0]
    assert "disagrees" in size.notes[0]


def test_type_row_with_unknown_token_is_could_not_interpret(
    interpret: Interpret,
) -> None:
    rules = [r for r in interpret(TYPE_TABLE) if "--fs-unknown" in r.reason]
    assert rules[0].status is RuleStatus.UNINTERPRETABLE


def test_type_row_with_unreadable_size_flags_only_that_property(
    interpret: Interpret,
) -> None:
    rules = _find(interpret(TYPE_TABLE), target_role="heading.h2")
    by_prop = {r.property: r for r in rules}
    assert by_prop["font-size"].status is RuleStatus.UNINTERPRETABLE
    assert by_prop["font-weight"].status is RuleStatus.PENDING


BUTTONS = (
    PALETTE.replace("`--bad` | `#GGGGGG`", "`--leaf` | `#194247`")
    + """
## 7.1 Buttons

| Variant | Background | Text | Border | Hover | Use |
|---|---|---|---|---|---|
| **Primary (CTA)** | `--tide` | `--white` | none | darken 8% | Primary action |
| **Secondary** | transparent | `--leaf` (on light) / `--white` (on dark) \
| `1.5px solid currentColor` | tint | Secondary |
| **Mystery** | `--tide` | `--white` | none | none | ? |
"""
)


def test_component_row_resolves_tokens_to_hex(interpret: Interpret) -> None:
    rules = _find(
        interpret(BUTTONS), target_role="button.primary", status=RuleStatus.PENDING
    )
    assert {r.property: r.value for r in rules} == {
        "background": "#09a78d",
        "color": "#ffffff",
        "border": "none",
    }


def test_component_row_splits_scoped_alternatives(interpret: Interpret) -> None:
    rules = _find(interpret(BUTTONS), target_role="button.secondary", property="color")
    assert {(r.scope, r.value) for r in rules} == {
        (Scope.LIGHT, "#194247"),
        (Scope.DARK, "#ffffff"),
    }


def test_component_hover_prose_is_could_not_interpret(interpret: Interpret) -> None:
    hover = _find(interpret(BUTTONS), target_role="button.primary", property="hover")[0]
    assert hover.status is RuleStatus.UNINTERPRETABLE
    assert "prose" in hover.reason


def test_component_unknown_variant_is_could_not_interpret(interpret: Interpret) -> None:
    rules = [r for r in interpret(BUTTONS) if "Mystery" in r.reason]
    assert rules[0].status is RuleStatus.UNINTERPRETABLE


CSS = """\
## 3.1 Font Stack

```css
--font-sans: "Montserrat", Arial, sans-serif;
@import url("https://fonts.example/css?family=Montserrat");
```

## 6.3 Cards

```css
.gradient-card { background: linear-gradient(90deg, #fff, transparent); }
.other { color: red; }
```

```css
border-radius: 12px;
```

```css
@media print { a { b: c } }
```
"""


def test_css_font_variable_becomes_font_family_rule(interpret: Interpret) -> None:
    rule = _find(interpret(CSS), category="font_family")[0]
    assert rule.value.startswith('"Montserrat"')
    assert rule.target_role == "document"


def test_css_import_becomes_font_source_rule(interpret: Interpret) -> None:
    assert _find(interpret(CSS), category="font_source")[0].property == "@import"


def test_css_known_selector_gets_a_role(interpret: Interpret) -> None:
    rule = _find(interpret(CSS), target_role="card.gradient", property="background")[0]
    assert "linear-gradient" in rule.value
    assert rule.status is RuleStatus.PENDING


def test_css_unknown_selector_is_could_not_interpret(interpret: Interpret) -> None:
    rule = _find(interpret(CSS), category="css_declaration", property="color")[0]
    assert rule.status is RuleStatus.UNINTERPRETABLE
    assert "'.other'" in rule.reason


def test_css_without_selector_says_target_is_unknown(interpret: Interpret) -> None:
    rule = _find(interpret(CSS), property="border-radius")[0]
    assert rule.status is RuleStatus.UNINTERPRETABLE
    assert "no selector" in rule.reason


def test_css_unsupported_construct_is_reported(interpret: Interpret) -> None:
    reasons = [
        r.reason for r in interpret(CSS) if r.status is RuleStatus.UNINTERPRETABLE
    ]
    assert any("CSS could not be read" in reason for reason in reasons)


def test_css_custom_property_becomes_plain_variable(interpret: Interpret) -> None:
    text = "```css\n--space-1: 4px;\n```\n"
    rule = _find(interpret(text), category="css_variable")[0]
    assert (rule.property, rule.value) == ("--space-1", "4px")


def test_section_status_relabels_unreadable_rules_only(interpret: Interpret) -> None:
    text = (
        "## 5. Logo Usage\n\nPlace it bottom-left.\n\n## 9. Voice & Copy\n\nBe calm.\n"
    )
    rules = interpret(text)
    logo = _find(rules, status=RuleStatus.NOT_APPLICABLE)
    assert "never invents a logo" in logo[0].reason
    voice = [r for r in rules if "Subjective" in r.reason]
    assert voice[0].status is RuleStatus.UNINTERPRETABLE


def test_identical_rules_are_merged_with_a_note(interpret: Interpret) -> None:
    text = (
        "| Do | Don't |\n|---|---|\n| Use Montserrat exclusively | Mix fonts |\n\n"
        '```css\n--font-sans: "Montserrat", sans-serif;\n```\n\n'
        "- **No other font families.**\n"
    )
    fonts = _find(interpret(text), category="font_only")
    assert len(fonts) == 1
    assert fonts[0].notes
    assert "Also stated at" in fonts[0].notes[0]


def test_rule_ids_are_sequential_and_unique(interpret: Interpret) -> None:
    ids = [r.id for r in interpret(BUTTONS)]
    assert ids == [f"R{n:03d}" for n in range(1, len(ids) + 1)]
