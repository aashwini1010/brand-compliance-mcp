"""Tests for brand_compliance.core.cascade."""

import pytest
from lxml import html

from brand_compliance.core.cascade import StyleIndex
from brand_compliance.core.color import Color


def _index(body: str, css: str = "") -> tuple[html.HtmlElement, StyleIndex]:
    root = html.document_fromstring(
        f"<html><head><style>{css}</style></head>{body}</html>"
    )
    return root, StyleIndex.build(root)


def _first(root: html.HtmlElement, tag: str) -> html.HtmlElement:
    return root.find(f".//{tag}")


def test_declared_uses_the_more_specific_selector() -> None:
    root, ix = _index('<body><p class="a">x</p></body>', "p{color:red} p.a{color:blue}")
    assert ix.declared(_first(root, "p"), "color") == "blue"


def test_declared_prefers_later_rule_when_specificity_ties() -> None:
    root, ix = _index("<body><p>x</p></body>", "p{color:red} p{color:green}")
    assert ix.declared(_first(root, "p"), "color") == "green"


def test_inline_style_beats_stylesheet_but_important_beats_inline() -> None:
    root, ix = _index(
        '<body><p style="color:blue">x</p><i style="color:blue">y</i></body>',
        "p{color:red} i{color:red !important}",
    )
    assert ix.declared(_first(root, "p"), "color") == "blue"
    assert ix.declared(_first(root, "i"), "color") == "red"


def test_declared_returns_none_when_nothing_sets_the_property() -> None:
    root, ix = _index("<body><p>x</p></body>", "p{color:red}")
    assert ix.declared(_first(root, "p"), "margin") is None


def test_variables_from_root_are_resolved() -> None:
    root, ix = _index("<body><p>x</p></body>", ":root{--ink:#111} p{color:var(--ink)}")
    assert ix.variables == {"--ink": "#111"}
    assert ix.declared(_first(root, "p"), "color") == "#111"


def test_variable_fallback_is_used_when_undefined() -> None:
    root, ix = _index("<body><p>x</p></body>", "p{color:var(--nope, #222)}")
    assert ix.declared(_first(root, "p"), "color") == "#222"


def test_unknown_variable_without_fallback_is_none() -> None:
    root, ix = _index("<body><p>x</p></body>", "p{color:var(--nope)}")
    assert ix.declared(_first(root, "p"), "color") is None


def test_nested_variable_references_resolve() -> None:
    root, ix = _index(
        "<body><p>x</p></body>",
        ":root{--a:var(--b);--b:#333} p{color:var(--a)}",
    )
    assert ix.declared(_first(root, "p"), "color") == "#333"


def test_media_blocks_are_counted_not_evaluated() -> None:
    root, ix = _index(
        "<body><p>x</p></body>", "p{color:red} @media (max-width:5px){p{color:blue}}"
    )
    assert ix.conditional_blocks == 1
    assert ix.declared(_first(root, "p"), "color") == "red"


def test_hover_rules_never_affect_base_styles_and_pseudo_elements_are_skipped() -> None:
    root, ix = _index(
        "<body><a href='#'>x</a></body>",
        "a{color:blue} a:hover{color:red} a::before{x:y}",
    )
    assert ix.declared(_first(root, "a"), "color") == "blue"
    assert ix.skipped_selectors == 1


def test_print_only_style_blocks_count_as_conditional() -> None:
    root = html.document_fromstring(
        "<html><head><style media='print'>p{color:red}</style></head>"
        "<body><p>x</p></body></html>"
    )
    ix = StyleIndex.build(root)
    assert ix.conditional_blocks == 1
    assert ix.declared(_first(root, "p"), "color") is None


@pytest.mark.parametrize(
    ("style", "expected"),
    [
        ("background-color:#102a43", Color(16, 42, 67)),
        ("background:#fff url(x.png) no-repeat", None),
        ("background:linear-gradient(red, blue)", None),
        ("background:rgb(1,2,3)", Color(1, 2, 3)),
        ("background-color:var(--missing)", None),
    ],
)
def test_background_color_reads_direct_values(
    style: str, expected: Color | None
) -> None:
    root, ix = _index(f'<body><div style="{style}"><p>x</p></div></body>')
    assert ix.background_color(_first(root, "p")) == expected


def test_background_walks_up_past_transparent_ancestors() -> None:
    root, ix = _index(
        '<body style="background:#000"><div style="background:transparent">'
        "<p>x</p></div></body>"
    )
    assert ix.background_color(_first(root, "p")) == Color(0, 0, 0)


def test_background_reads_the_bgcolor_attribute() -> None:
    root, ix = _index(
        '<body><table><tr><td bgcolor="#102a43"><p>x</p></td></tr></table></body>'
    )
    assert ix.background_color(_first(root, "p")) == Color(16, 42, 67)


def test_background_defaults_to_browser_white_when_nothing_is_set() -> None:
    root, ix = _index("<body><p>x</p></body>")
    assert ix.background_color(_first(root, "p")) == Color(255, 255, 255)


def test_broken_inline_style_does_not_crash() -> None:
    root, ix = _index('<body><p style="color red">x</p></body>', "p{color:red}")
    assert ix.declared(_first(root, "p"), "color") == "red"


def test_dark_variants_are_detected_from_media_queries_and_attribute_selectors() -> (
    None
):
    _, plain = _index("<body></body>", "p{color:red}")
    _, media = _index(
        "<body></body>", "@media (prefers-color-scheme: dark){p{color:red}}"
    )
    _, toggle = _index("<body></body>", ':root[data-theme="dark"]{--a:1} p{color:red}')
    assert not plain.dark_variants
    assert media.dark_variants
    assert toggle.dark_variants
    assert toggle.dark_selectors == {'[data-theme="dark"]'}


def test_the_tools_own_style_block_is_not_treated_as_the_pages_design() -> None:
    root = html.document_fromstring(
        '<html><head><style id="brand-compliance">p{color:red}</style></head>'
        "<body><p>x</p></body></html>"
    )
    index = StyleIndex.build(root)
    assert index.declared(_first(root, "p"), "color") is None


def test_text_color_is_inherited_and_names_the_element_that_set_it() -> None:
    root, ix = _index('<body style="color:#123456"><div><p>x</p></div></body>')
    color, source = ix.text_color(_first(root, "p"))
    assert color == Color(0x12, 0x34, 0x56)
    assert source is root.find("body")


def test_text_color_defaults_to_black_when_nothing_sets_it() -> None:
    root, ix = _index("<body><p>x</p></body>")
    assert ix.text_color(_first(root, "p")) == (Color(0, 0, 0), None)


def test_text_color_inherit_keyword_looks_further_up() -> None:
    root, ix = _index(
        '<body style="color:#111111"><p style="color:inherit">x</p></body>'
    )
    assert ix.text_color(_first(root, "p"))[0] == Color(0x11, 0x11, 0x11)


@pytest.mark.parametrize("style", ["color:var(--missing)", "color:notacolour"])
def test_text_color_is_unknown_when_it_cannot_be_read(style: str) -> None:
    root, ix = _index(f'<body><p style="{style}">x</p></body>')
    assert ix.text_color(_first(root, "p"))[0] is None


def test_background_with_source_names_the_element_that_set_it() -> None:
    root, ix = _index('<body><div style="background:#102a43"><p>x</p></div></body>')
    color, source = ix.background_with_source(_first(root, "p"))
    assert color == Color(16, 42, 67)
    assert source is _first(root, "div")


def test_translucent_backgrounds_are_blended_over_the_ones_beneath() -> None:
    root, ix = _index(
        '<body style="background:#ffffff"><div style="background:rgba(0,0,0,0.5)">'
        "<p>x</p></div></body>"
    )
    assert ix.background_color(_first(root, "p")) == Color(128, 128, 128)


def test_translucent_background_over_an_unknown_one_is_unknown() -> None:
    root, ix = _index(
        '<body style="background:var(--missing)">'
        '<div style="background:rgba(0,0,0,0.5)"><p>x</p></div></body>'
    )
    assert ix.background_color(_first(root, "p")) is None


def test_with_overrides_changes_a_copy_and_never_the_original() -> None:
    root, ix = _index("<body><p>x</p></body>", "p{color:red}")
    paragraph = _first(root, "p")
    view = ix.with_overrides({(paragraph, "color"): "blue"})
    assert view.declared(paragraph, "color") == "blue"
    assert ix.declared(paragraph, "color") == "red"


def test_dark_variables_are_read_from_dark_scopes_and_media_blocks() -> None:
    _, ix = _index(
        "<body></body>",
        ':root{--a:red} :root[data-theme="dark"]{--a:blue;--b:navy}'
        "@media (prefers-color-scheme: dark){:root{--c:teal}}",
    )
    assert ix.variables == {"--a": "red"}
    assert ix.dark_variables == {"--a": "blue", "--b": "navy", "--c": "teal"}


def test_with_overrides_replaces_a_root_variable_without_touching_the_original() -> (
    None
):
    root, ix = _index(
        "<body><p>x</p></body>", ":root{--ink:#111111} p{color:var(--ink)}"
    )
    view = ix.with_overrides({(root, "--ink"): "#222222"})
    assert view.declared(_first(root, "p"), "color") == "#222222"
    assert ix.declared(_first(root, "p"), "color") == "#111111"
