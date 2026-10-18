"""Tests for bullet specs (finder + interpreter, through the full pipeline)."""

from collections.abc import Callable

from brand_compliance.models.rule import Rule, RuleStatus

Interpret = Callable[[str], list[Rule]]

BUTTONS = """\
## 4.3 Border Radius

```css
--radius-pill: 999px;
```

| Token | Hex |
|---|---|
| `--white` | `#FFFFFF` |
| `--leaf` | `#194247` |
| `--tide` | `#09A78D` |

## 7.1 Buttons

- **Shape**: pill (`--radius-pill`) by default; rectangular with `8px` radius only.
- **Padding**: `12px 28px` (medium); `16px 36px` (large); weird.
- **Font**: Montserrat 600, `--fs-button`, +0.02em letter-spacing.
- **Destructive variant**: background `#C84B47`, text `--white`.
- **Disabled**: `opacity: 0.5; cursor: not-allowed`.
- **Voice**: calm and clear.
"""

FORMS = """\
| Token | Hex |
|---|---|
| `--white` | `#FFFFFF` |
| `--leaf` | `#194247` |
| `--tide` | `#09A78D` |

## 7.3 Forms & Inputs

- Background: `--white`, border `1px solid rgba(25,66,71,0.16)`.
- Border radius: `12px` (modern) or `8px` (compact).
- Padding: 14px vertical, 16px horizontal.
- Focus state: border becomes `2px solid --tide`, ring `0 0 0 4px rgba(9,167,141,0.15)`.
- Label: Montserrat 600, 14px, color `--leaf`, sits above input.
"""


def _spec(rules: list[Rule], role: str, prop: str | None) -> list[Rule]:
    return [
        r
        for r in rules
        if r.category == "component_spec"
        and r.target_role == role
        and r.property == prop
    ]


def test_shape_bullet_resolves_the_radius_variable(interpret: Interpret) -> None:
    rule = _spec(interpret(BUTTONS), "button", "border-radius")[0]
    assert rule.value == "999px"
    assert rule.notes == ["Not applied: by default; rectangular with 8px radius only"]


def test_padding_bullet_makes_one_rule_per_size(interpret: Interpret) -> None:
    rules = interpret(BUTTONS)
    assert _spec(rules, "button.medium", "padding")[0].value == "12px 28px"
    assert _spec(rules, "button.large", "padding")[0].value == "16px 36px"


def test_padding_size_is_never_assumed_default(interpret: Interpret) -> None:
    rule = _spec(interpret(BUTTONS), "button.medium", "padding")[0]
    assert "marks the button size" in rule.notes[0]
    assert _spec(interpret(BUTTONS), "button", "padding") == []


def test_padding_piece_not_understood_is_reported_alone(interpret: Interpret) -> None:
    bad = [r for r in interpret(BUTTONS) if r.value == "weird"]
    assert bad[0].status is RuleStatus.UNINTERPRETABLE
    assert "size not understood" in bad[0].reason


def test_font_bullet_reads_family_weight_and_spacing(interpret: Interpret) -> None:
    rules = interpret(BUTTONS)
    assert _spec(rules, "button.label", "font-family")[0].value == "Montserrat"
    assert _spec(rules, "button.label", "font-weight")[0].value == "600"
    assert _spec(rules, "button.label", "letter-spacing")[0].value == "0.02em"


def test_box_pairs_resolve_tokens_and_literals(interpret: Interpret) -> None:
    rules = interpret(BUTTONS)
    assert _spec(rules, "button.destructive", "background")[0].value == "#c84b47"
    assert _spec(rules, "button.destructive", "color")[0].value == "#ffffff"


def test_declaration_bullet_reads_each_property(interpret: Interpret) -> None:
    rules = interpret(BUTTONS)
    assert _spec(rules, "button.disabled", "opacity")[0].value == "0.5"
    assert _spec(rules, "button.disabled", "cursor")[0].value == "not-allowed"


def test_unlisted_label_is_left_to_leftovers(interpret: Interpret) -> None:
    rules = interpret(BUTTONS)
    voice = [r for r in rules if "Voice" in (r.value or "")]
    assert voice[0].category == "unmatched"
    assert not any(
        r.category == "component_spec" and "calm" in (r.value or "") for r in rules
    )


def test_shape_with_undefined_variable_is_not_guessed(interpret: Interpret) -> None:
    text = "## 7.1 Buttons\n\n- **Shape**: pill (`--radius-pill`) by default.\n"
    rule = interpret(text)[0]
    assert rule.status is RuleStatus.UNINTERPRETABLE
    assert "--radius-pill is not defined" in rule.reason


def test_first_fragment_uses_the_bullet_label_as_its_key(interpret: Interpret) -> None:
    rules = interpret(FORMS)
    assert _spec(rules, "input", "background")[0].value == "#ffffff"
    assert _spec(rules, "input", "border")[0].value == "1px solid #19424729"


def test_axis_padding_becomes_one_shorthand(interpret: Interpret) -> None:
    assert _spec(interpret(FORMS), "input", "padding")[0].value == "14px 16px"


def test_focus_state_reads_border_and_ring(interpret: Interpret) -> None:
    rules = interpret(FORMS)
    assert _spec(rules, "input.focus", "border")[0].value == "2px solid #09a78d"
    assert _spec(rules, "input.focus", "box-shadow")[0].value == "0 0 0 4px #09a78d26"


def test_alternatives_with_no_choosing_rule_are_not_guessed(
    interpret: Interpret,
) -> None:
    rule = [r for r in interpret(FORMS) if "modern" in (r.value or "")][0]
    assert rule.status is RuleStatus.UNINTERPRETABLE
    assert "no rule for choosing" in rule.reason


def test_label_bullet_reads_what_it_can_and_flags_the_rest(
    interpret: Interpret,
) -> None:
    rules = interpret(FORMS)
    assert _spec(rules, "form.label", "font-size")[0].value == "14px"
    assert _spec(rules, "form.label", "color")[0].value == "#194247"
    layout = [r for r in rules if r.value == "sits above input"][0]
    assert layout.status is RuleStatus.UNINTERPRETABLE
