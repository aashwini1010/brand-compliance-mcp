"""Tests for the role-style appliers and the font appliers."""

import pytest

from brand_compliance.core.contracts import RuleApplier
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.rule import Rule, RuleStatus, Scope
from brand_compliance.models.source import SourceSpan
from brand_compliance.plugins.appliers import register_appliers
from brand_compliance.plugins.appliers.color import ColorApplier
from brand_compliance.plugins.appliers.component import ComponentApplier
from brand_compliance.plugins.appliers.font import (
    FONT_SOURCE_PROPERTY,
    FontFamilyApplier,
    FontSourceApplier,
)
from brand_compliance.plugins.appliers.surface import SurfaceApplier
from brand_compliance.plugins.appliers.typography import TypographyApplier
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler

PAGE = """<!doctype html><html><head><style>
body{background:#0e1117;font-family:"Georgia",serif}
.light{background:#ffffff} h1{font-size:2rem;font-family:"Times New Roman",serif}
.btn{border-radius:4px} .primary{background:#2446a8}
</style></head><body>
<div class="light"><p>on light</p><p style="font-size:.9rem">inline size</p></div>
<p>on dark</p><h1>Title</h1>
<button class="btn">Back</button><button class="btn primary">Next</button>
<div style="background:linear-gradient(red,blue)"><p>on gradient</p></div>
</body></html>"""


def _artifact(text: str = PAGE) -> ArtifactModel:
    return StaticArtifactHandler().parse(text, "page.html")


def _rule(
    category: str, role: str | None, prop: str | None, value: str | None, **kw: object
) -> Rule:
    return Rule(
        id=str(kw.pop("id", "R001")),
        category=category,
        target_role=role,
        property=prop,
        value=value,
        status=RuleStatus.PENDING,
        source_span=SourceSpan(file="g.md", line_start=1),
        **kw,  # type: ignore[arg-type]
    )


def _typo() -> TypographyApplier:
    return TypographyApplier()


def test_appliers_claim_their_own_categories_and_implement_the_contract() -> None:
    appliers = [
        TypographyApplier(),
        ColorApplier(),
        ComponentApplier(),
        SurfaceApplier(),
        FontFamilyApplier(),
        FontSourceApplier(),
    ]
    assert all(isinstance(a, RuleApplier) for a in appliers)
    assert TypographyApplier.categories == {"typography"}
    assert ComponentApplier.categories == {"component", "component_spec"}


def test_register_appliers_registers_all_seven() -> None:
    registry = PluginRegistry()
    register_appliers(registry)
    assert len(registry.describe()["RuleApplier"]) == 7


def test_rule_changes_every_element_with_the_role_using_the_cascade_for_before() -> (
    None
):
    result = _typo().plan(
        _rule("typography", "heading.h1", "font-size", "3rem"), _artifact()
    )
    assert len(result.changes) == 1
    change = result.changes[0]
    assert (change.before, change.after) == ("2rem", "3rem")
    assert change.location == "/html/body/h1"


def test_rule_for_a_base_role_reaches_its_variants() -> None:
    rule = _rule("component", "button", "border-radius", "999px")
    result = ComponentApplier().plan(rule, _artifact())
    assert len(result.changes) == 2  # button and button.primary


def test_rule_for_a_specific_role_does_not_reach_the_base_role() -> None:
    rule = _rule("component", "button.primary", "color", "#ffffff")
    assert len(ComponentApplier().plan(rule, _artifact()).changes) == 1


def test_value_that_already_matches_is_satisfied_not_changed() -> None:
    rule = _rule("typography", "heading.h1", "font-size", "2rem")
    result = _typo().plan(rule, _artifact())
    assert result.changes == []
    assert result.satisfied == 1


def test_equal_colours_in_different_notation_count_as_satisfied() -> None:
    rule = _rule("component", "button.primary", "background", "rgb(36, 70, 168)")
    assert ComponentApplier().plan(rule, _artifact()).satisfied == 1


def test_unknown_role_is_skipped_with_a_clear_reason() -> None:
    result = _typo().plan(
        _rule("typography", "heading.h3", "font-size", "1rem"), _artifact()
    )
    assert result.changes == []
    assert (
        "No element in the artifact has the role 'heading.h3'"
        in result.skipped[0].reason
    )


def test_rule_without_property_or_value_is_skipped() -> None:
    result = _typo().plan(_rule("typography", "heading.h1", None, None), _artifact())
    assert "no role, property or value" in result.skipped[0].reason


def test_email_only_rule_is_skipped_on_a_static_artifact() -> None:
    rule = _rule("typography", "heading.h1", "font-size", "3rem", scope=Scope.EMAIL)
    assert "email artifacts only" in _typo().plan(rule, _artifact()).skipped[0].reason


def test_light_rule_applies_only_to_elements_on_light_surfaces() -> None:
    rule = _rule("color", "text.body", "color", "#194247", scope=Scope.LIGHT)
    result = ColorApplier().plan(rule, _artifact())
    assert [c.location for c in result.changes] == [
        "/html/body/div[1]/p[1]",
        "/html/body/div[1]/p[2]",
    ]
    assert {c.surface for c in result.changes} == {"light"}


def test_surface_that_cannot_be_determined_is_skipped_per_element() -> None:
    rule = _rule("color", "text.body", "color", "#194247", scope=Scope.LIGHT)
    skips = ColorApplier().plan(rule, _artifact()).skipped
    assert [s.location for s in skips] == ["/html/body/div[2]/p"]
    assert "surface behind this element is unknown" in skips[0].reason


def test_dark_rule_with_no_dark_elements_explains_why() -> None:
    text = "<html><body style='background:#fff'><p>x</p></body></html>"
    rule = _rule("color", "text.body", "color", "#fff", scope=Scope.DARK)
    result = ColorApplier().plan(rule, _artifact(text))
    assert "sits on a dark surface" in result.skipped[0].reason


def test_inline_style_on_the_property_is_overridden_and_flagged() -> None:
    rule = _rule("typography", "text.body", "font-size", "1rem")
    changes = {c.location: c for c in _typo().plan(rule, _artifact()).changes}
    inline = changes["/html/body/div[1]/p[2]"]
    assert inline.important is True
    assert inline.note == "Overrides an inline style"
    assert changes["/html/body/p"].important is False


def test_alias_applies_a_rule_written_for_one_role_to_another() -> None:
    rule = _rule("component_spec", "button.label", "font-weight", "600")
    plain = ComponentApplier().plan(rule, _artifact())
    assert plain.changes == []
    aliased = ComponentApplier({"button.label": "button"}).plan(rule, _artifact())
    assert len(aliased.changes) == 2


def test_font_family_applier_fixes_body_and_every_element_using_another_font() -> None:
    stack = '"Montserrat", sans-serif'
    result = FontFamilyApplier().plan(
        _rule("font_family", "document", "font-family", stack), _artifact()
    )
    assert sorted(c.location for c in result.changes) == ["/html/body", "/html/body/h1"]
    assert {c.after for c in result.changes} == {stack}


def test_font_family_applier_leaves_elements_already_using_the_brand_font() -> None:
    text = "<html><body style='font-family:Montserrat'><p>x</p></body></html>"
    rule = _rule("font_family", "document", "font-family", '"Montserrat", sans-serif')
    result = FontFamilyApplier().plan(rule, _artifact(text))
    assert result.changes == []
    assert result.satisfied >= 1


def test_font_family_applier_without_a_value_is_skipped() -> None:
    result = FontFamilyApplier().plan(
        _rule("font_family", "document", "font-family", None), _artifact()
    )
    assert result.skipped


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            'url("https://fonts.example/css?family=M")',
            "https://fonts.example/css?family=M",
        ),
        ("url(https://fonts.example/a.css)", "https://fonts.example/a.css"),
    ],
)
def test_font_source_applier_adds_the_https_stylesheet_to_head(
    value: str, expected: str
) -> None:
    result = FontSourceApplier().plan(
        _rule("font_source", None, "@import", value), _artifact()
    )
    change = result.changes[0]
    assert (change.location, change.property, change.after) == (
        "/html/head",
        FONT_SOURCE_PROPERTY,
        expected,
    )


def test_font_source_applier_rejects_non_https_urls() -> None:
    rule = _rule("font_source", None, "@import", 'url("http://insecure.example/a.css")')
    assert (
        "not an https URL"
        in FontSourceApplier().plan(rule, _artifact()).skipped[0].reason
    )


def test_font_source_applier_is_satisfied_when_the_page_already_links_it() -> None:
    text = '<html><head><link rel="stylesheet" href="https://f.example/a.css"></head><body></body></html>'
    rule = _rule("font_source", None, "@import", 'url("https://f.example/a.css")')
    assert FontSourceApplier().plan(rule, _artifact(text)).satisfied == 1


def test_font_source_applier_ignores_its_own_earlier_link() -> None:
    text = (
        '<html><head><link rel="stylesheet" href="https://f.example/a.css" '
        'data-brand-compliance="font"></head><body></body></html>'
    )
    rule = _rule("font_source", None, "@import", 'url("https://f.example/a.css")')
    assert len(FontSourceApplier().plan(rule, _artifact(text)).changes) == 1
