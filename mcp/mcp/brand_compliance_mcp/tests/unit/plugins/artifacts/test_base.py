"""Tests for brand_compliance.plugins.artifacts.base."""

import pytest

from brand_compliance.core.errors import ParseFailedError
from brand_compliance.plugins.artifacts.base import (
    describe_element,
    element_path,
    has_own_text,
    is_content_element,
    parse_artifact_html,
    serialize_html,
    top_level_nodes,
)

PAGE = (
    "<!DOCTYPE html><html><head><title>t</title><style>a{}</style></head>"
    '<body><p class="a b">hi <b>x</b></p><svg><circle/></svg>'
    "<script>1</script></body></html>"
)


def test_parse_keeps_the_original_doctype() -> None:
    assert parse_artifact_html(PAGE).doctype == "<!DOCTYPE html>"


def test_parse_reports_missing_doctype_as_none() -> None:
    assert parse_artifact_html("<html><body>x</body></html>").doctype is None


def test_parse_strips_a_byte_order_mark() -> None:
    assert parse_artifact_html("﻿<!doctype html><p>x</p>").doctype == "<!doctype html>"


@pytest.mark.parametrize("text", ["", "   \n"])
def test_parse_rejects_empty_input(text: str) -> None:
    with pytest.raises(ParseFailedError):
        parse_artifact_html(text)


def test_serialize_writes_the_doctype_back() -> None:
    parsed = parse_artifact_html(PAGE)
    assert serialize_html(parsed.root, parsed.doctype).startswith("<!DOCTYPE html>")


def test_parse_then_serialize_restores_svg_attribute_case() -> None:
    page = '<!doctype html><body><svg viewBox="0 0 1 1"><path d="M0"/></svg></body>'
    parsed = parse_artifact_html(page)
    assert 'viewBox="0 0 1 1"' in serialize_html(parsed.root, parsed.doctype)


def test_element_path_is_unique_and_stable() -> None:
    root = parse_artifact_html("<body><p>a</p><p>b</p></body>").root
    first, second = root.findall(".//p")
    assert element_path(first) == "/html/body/p[1]"
    assert element_path(second) == "/html/body/p[2]"


def test_describe_element_names_tag_classes_and_line() -> None:
    root = parse_artifact_html("<body>\n<p class='a b'>x</p></body>").root
    assert describe_element(root.find(".//p")) == "<p.a.b> line 2"


def test_is_content_element_excludes_head_svg_script_and_style() -> None:
    root = parse_artifact_html(PAGE).root
    assert is_content_element(root.find(".//p"))
    assert is_content_element(root.find("body"))
    assert not is_content_element(root.find(".//title"))
    assert not is_content_element(root.find(".//style"))
    assert not is_content_element(root.find(".//circle"))
    assert not is_content_element(root.find(".//script"))
    assert not is_content_element(root)


def test_has_own_text_sees_text_and_tails_but_not_child_only_text() -> None:
    root = parse_artifact_html(
        "<body><p>hi</p><div><b>x</b></div><div><b>x</b> tail</div></body>"
    ).root
    first, only_child, with_tail = root.findall(".//p") + root.findall(".//div")
    assert has_own_text(first)
    assert not has_own_text(only_child)
    assert has_own_text(with_tail)


OUTER = (
    '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '
    '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'
    "<!-- before the root -->\n<!--[if mso]><p>outlook only</p><![endif]-->\n"
    "<html><body><p>x</p></body></html>\n<!-- after the root -->\n"
)


def test_serialize_keeps_comments_before_and_after_the_html_element() -> None:
    parsed = parse_artifact_html(OUTER)
    output = serialize_html(parsed.root, parsed.doctype)
    assert "<!-- before the root -->" in output
    assert "<!--[if mso]><p>outlook only</p><![endif]-->" in output
    assert "<!-- after the root -->" in output


def test_serialize_keeps_the_original_doctype_text_exactly() -> None:
    page = "<!doctype html>\n<!-- c --><html><body>x</body></html>"
    parsed = parse_artifact_html(page)
    assert serialize_html(parsed.root, parsed.doctype).startswith("<!doctype html>")


def test_serialize_without_a_doctype_writes_none() -> None:
    parsed = parse_artifact_html("<html><body>x</body></html>")
    assert "DOCTYPE" not in serialize_html(parsed.root, None).upper()


def test_a_serialised_document_parses_back_to_the_same_comments() -> None:
    first = parse_artifact_html(OUTER)
    second = parse_artifact_html(serialize_html(first.root, first.doctype))
    assert [
        c.text for c in top_level_nodes(first.root) if not isinstance(c.tag, str)
    ] == [c.text for c in top_level_nodes(second.root) if not isinstance(c.tag, str)]


def test_top_level_nodes_lists_outer_comments_in_document_order() -> None:
    root = parse_artifact_html(OUTER).root
    texts = [n.text for n in top_level_nodes(root) if not isinstance(n.tag, str)]
    assert texts[0] == " before the root "
    assert texts[-1] == " after the root "


def test_a_page_without_a_doctype_stays_without_one_after_serialising() -> None:
    parsed = parse_artifact_html("<html><body><p>x</p></body></html>")
    output = serialize_html(parsed.root, parsed.doctype)
    assert output.startswith("<html>")
    assert parsed.doctype is None
