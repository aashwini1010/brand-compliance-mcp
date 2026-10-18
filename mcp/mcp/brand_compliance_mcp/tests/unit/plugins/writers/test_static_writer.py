"""Tests for brand_compliance.plugins.writers.static."""

import re

from brand_compliance.core.contracts import StyleWriter
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import Change
from brand_compliance.plugins.appliers.font import FONT_SOURCE_PROPERTY, HEAD_PATH
from brand_compliance.plugins.artifacts.base import serialize_html
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler
from brand_compliance.plugins.writers import register_writers
from brand_compliance.plugins.writers.static import StylesheetWriter

PAGE = """<!doctype html><html><head><title>t</title></head>
<body><h1>Title</h1><p class="a">light</p>
<p style="font-size:.8rem">inline</p></body></html>"""


def _artifact(text: str = PAGE) -> ArtifactModel:
    return StaticArtifactHandler().parse(text, "page.html")


def _change(location: str, prop: str, after: str, **kw: object) -> Change:
    return Change(
        id="CH1",
        rule_id="R1",
        location=location,
        property=prop,
        after=after,
        **kw,  # type: ignore[arg-type]
    )


def _css(artifact: ArtifactModel) -> str:
    html = serialize_html(artifact.tree, artifact.doctype)
    match = re.search(r'<style id="brand-compliance">(.*?)</style>', html, re.S)
    assert match
    return match.group(1)


def test_writer_implements_the_contract_and_registers() -> None:
    assert isinstance(StylesheetWriter(), StyleWriter)
    registry = PluginRegistry()
    register_writers(registry)
    assert registry.describe()["StyleWriter"] == ["stylesheet", "inline"]


def test_writer_adds_one_brand_block_with_an_id_boost_selector() -> None:
    artifact = StylesheetWriter().write(
        [_change("/html/body/h1", "font-size", "3rem")], _artifact()
    )
    css = _css(artifact)
    assert 'html:not(#brand-compliance) [data-brand-role="heading.h1"]' in css
    assert "font-size: 3rem;" in css
    assert "!important" not in css


def test_writer_marks_changed_elements_with_their_role() -> None:
    artifact = StylesheetWriter().write(
        [_change("/html/body/h1", "font-size", "3rem")], _artifact()
    )
    html = serialize_html(artifact.tree, artifact.doctype)
    assert '<h1 data-brand-role="heading.h1">' in html
    assert "data-brand-role" not in html.split("<p")[1]


def test_writer_groups_properties_of_the_same_role_into_one_rule() -> None:
    changes = [
        _change("/html/body/h1", "font-size", "3rem"),
        _change("/html/body/h1", "font-weight", "700"),
    ]
    css = _css(StylesheetWriter().write(changes, _artifact()))
    assert css.count("[data-brand-role=") == 1
    assert "font-size: 3rem;" in css
    assert "font-weight: 700;" in css


def test_writer_scopes_rules_by_surface() -> None:
    change = _change("/html/body/p[1]", "color", "#194247", surface="light")
    artifact = StylesheetWriter().write([change], _artifact())
    assert '[data-brand-surface="light"]' in _css(artifact)
    assert 'data-brand-surface="light"' in serialize_html(
        artifact.tree, artifact.doctype
    )


def test_writer_forces_important_only_on_the_element_that_needs_it() -> None:
    changes = [
        _change("/html/body/p[1]", "font-size", "1rem"),
        _change("/html/body/p[2]", "font-size", "1rem", important=True),
    ]
    artifact = StylesheetWriter().write(changes, _artifact())
    css = _css(artifact)
    assert '[data-brand-force~="font-size"]' in css
    assert css.count("!important") == 1
    html = serialize_html(artifact.tree, artifact.doctype)
    assert html.count('data-brand-force="') == 1


def test_writer_adds_the_font_link_to_head() -> None:
    change = _change(
        HEAD_PATH, FONT_SOURCE_PROPERTY, "https://fonts.example/a.css?x=1&y=2"
    )
    html = serialize_html(StylesheetWriter().write([change], _artifact()).tree, None)
    assert 'href="https://fonts.example/a.css?x=1&amp;y=2"' in html
    assert 'data-brand-compliance="font"' in html
    assert 'brand-compliance"' not in html.split("</head>")[0].replace(
        'data-brand-compliance="font"', ""
    )


def test_writer_with_no_changes_leaves_the_artifact_alone() -> None:
    artifact = _artifact()
    before = serialize_html(artifact.tree, artifact.doctype)
    assert (
        serialize_html(StylesheetWriter().write([], artifact).tree, artifact.doctype)
        == before
    )


def test_writer_replaces_its_own_earlier_block_instead_of_duplicating() -> None:
    first = StylesheetWriter().write(
        [_change("/html/body/h1", "font-size", "3rem")], _artifact()
    )
    html = serialize_html(first.tree, first.doctype)
    second = StylesheetWriter().write(
        [_change("/html/body/h1", "font-size", "4rem")], _artifact(html)
    )
    out = serialize_html(second.tree, second.doctype)
    assert out.count('id="brand-compliance"') == 1
    assert "4rem" in out
    assert "3rem" not in out


def test_writer_clears_stale_annotations_when_it_rewrites() -> None:
    first = StylesheetWriter().write(
        [_change("/html/body/h1", "font-size", "3rem")], _artifact()
    )
    html = serialize_html(first.tree, first.doctype)
    second = StylesheetWriter().write(
        [_change("/html/body/p[1]", "font-size", "1rem")], _artifact(html)
    )
    out = serialize_html(second.tree, second.doctype)
    assert "<h1>" in out
    assert 'data-brand-role="text.body"' in out


def test_writer_stays_out_of_dark_modes_when_page_has_a_dark_theme() -> None:
    text = (
        "<!doctype html><html><head><style>"
        ":root{--a:1} @media (prefers-color-scheme: dark){:root{--a:2}} "
        ':root[data-theme="dark"]{--a:3}</style></head><body><h1>T</h1></body></html>'
    )
    artifact = StylesheetWriter().write(
        [_change("/html/body/h1", "font-size", "3rem")], _artifact(text)
    )
    css = _css(artifact)
    assert "@media (prefers-color-scheme: light)" in css
    assert ':not([data-theme="dark"])' in css
    assert any("dark theme keeps its original look" in n for n in artifact.notes)


def test_writer_creates_a_head_when_the_page_has_none() -> None:
    artifact = _artifact("<html><body><h1>T</h1></body></html>")
    head = artifact.tree.find("head")
    if head is not None:
        artifact.tree.remove(head)
    out = StylesheetWriter().write(
        [_change("/html/body/h1", "font-size", "3rem")], artifact
    )
    assert out.tree.find("head") is not None


def test_writer_records_how_many_elements_it_marked() -> None:
    artifact = StylesheetWriter().write(
        [
            _change("/html/body/h1", "font-size", "3rem"),
            _change("/html/body/h1", "font-weight", "700"),
        ],
        _artifact(),
    )
    assert any("Marked 1 element(s)" in n for n in artifact.notes)


def test_writer_emits_colour_variables_per_surface_and_not_as_role_rules() -> None:
    artifact = _artifact(
        "<html><head><style>:root{--accent:red}"
        ':root[data-theme="dark"]{--accent:blue}</style></head><body></body></html>'
    )
    changes = [
        _change("/html", "--accent", "#337077", surface="light"),
        _change("/html", "--accent", "#09a78d", surface="dark"),
    ]
    out = StylesheetWriter().write(changes, artifact)
    css = _css(out)
    assert "--accent: #337077;" in css and "--accent: #09a78d;" in css
    assert 'html[data-theme="dark"]:not(#brand-compliance)' in css
    assert "data-brand-role" not in css
