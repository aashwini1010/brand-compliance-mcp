"""Tests for brand_compliance.core.svg."""

from lxml import html

from brand_compliance.core.svg import restore_svg_case


def _svg_page() -> html.HtmlElement:
    return html.document_fromstring(
        '<body><svg viewBox="0 0 24 24"><linearGradient id="g" gradientUnits="x">'
        '</linearGradient><path d="M0"/></svg><p viewBox="keep">x</p></body>'
    )


def test_restore_svg_case_repairs_attributes_and_tags_inside_svg() -> None:
    root = _svg_page()
    assert restore_svg_case(root) == 3
    svg = root.find(".//svg")
    assert svg.get("viewBox") == "0 0 24 24"
    assert svg.find("linearGradient").get("gradientUnits") == "x"


def test_restore_svg_case_leaves_html_outside_svg_alone() -> None:
    root = _svg_page()
    restore_svg_case(root)
    assert root.find(".//p").get("viewbox") == "keep"


def test_restore_svg_case_is_idempotent() -> None:
    root = _svg_page()
    restore_svg_case(root)
    assert restore_svg_case(root) == 0
