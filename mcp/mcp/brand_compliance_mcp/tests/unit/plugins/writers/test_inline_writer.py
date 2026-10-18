"""Tests for brand_compliance.plugins.writers.inline."""

from brand_compliance.core.contracts import StyleWriter
from brand_compliance.models.artifact import ArtifactModel, ArtifactType
from brand_compliance.models.change import Change
from brand_compliance.plugins.appliers.font import FONT_SOURCE_PROPERTY, HEAD_PATH
from brand_compliance.plugins.artifacts.base import serialize_html
from brand_compliance.plugins.artifacts.email import EmailArtifactHandler
from brand_compliance.plugins.writers.inline import InlineWriter

MAIL = """<!DOCTYPE html><html><head><title>t</title></head>
<body><!--[if mso]><p>keep me</p><![endif]-->
<h1 style="margin:0;font-size:30px">Title</h1><p>Body</p></body></html>"""


def _artifact(text: str = MAIL) -> ArtifactModel:
    return EmailArtifactHandler().parse(text, "mail.html")


def _change(location: str, prop: str, after: str) -> Change:
    return Change(id="C1", rule_id="R1", location=location, property=prop, after=after)


def _write(changes: list[Change], text: str = MAIL) -> str:
    artifact = InlineWriter().write(changes, _artifact(text))
    return serialize_html(artifact.tree, artifact.doctype)


def test_inline_writer_implements_the_contract_for_emails() -> None:
    assert isinstance(InlineWriter(), StyleWriter)
    assert InlineWriter.artifact_type is ArtifactType.EMAIL


def test_changes_are_merged_into_the_existing_inline_style() -> None:
    html = _write(
        [
            _change("/html/body/h1", "font-size", "32px"),
            _change("/html/body/h1", "color", "#102a43"),
        ]
    )
    assert 'style="margin: 0; font-size: 32px; color: #102a43"' in html


def test_an_element_without_a_style_gets_one() -> None:
    assert '<p style="line-height: 1.6">Body</p>' in _write(
        [_change("/html/body/p", "line-height", "1.6")]
    )


def test_font_names_use_single_quotes_inside_the_attribute() -> None:
    html = _write([_change("/html/body/p", "font-family", '"Montserrat", sans-serif')])
    assert "font-family: 'Montserrat', sans-serif" in html
    assert "&quot;" not in html


def test_nothing_but_the_style_attribute_is_added_to_the_markup() -> None:
    html = _write([_change("/html/body/p", "line-height", "1.6")])
    assert "<style" not in html
    assert "data-brand" not in html


def test_outlook_conditional_comments_are_left_exactly_as_they_were() -> None:
    assert "<!--[if mso]><p>keep me</p><![endif]-->" in _write(
        [_change("/html/body/p", "line-height", "1.6")]
    )


def test_the_font_link_is_added_to_head_and_the_limit_is_noted() -> None:
    artifact = InlineWriter().write(
        [_change(HEAD_PATH, FONT_SOURCE_PROPERTY, "https://fonts.example/a.css")],
        _artifact(),
    )
    html = serialize_html(artifact.tree, artifact.doctype)
    assert 'href="https://fonts.example/a.css"' in html
    assert any(
        "Montserrat loads only in email clients that support web fonts" in n
        for n in artifact.notes
    )


def test_no_changes_leave_the_email_untouched() -> None:
    artifact = _artifact()
    before = serialize_html(artifact.tree, artifact.doctype)
    assert (
        serialize_html(InlineWriter().write([], artifact).tree, artifact.doctype)
        == before
    )


def test_writing_again_replaces_the_font_link_instead_of_duplicating_it() -> None:
    change = _change(HEAD_PATH, FONT_SOURCE_PROPERTY, "https://fonts.example/a.css")
    first = serialize_html(
        InlineWriter().write([change], _artifact()).tree, "<!DOCTYPE html>"
    )
    second = serialize_html(
        InlineWriter().write([change], _artifact(first)).tree, "<!DOCTYPE html>"
    )
    assert second.count("fonts.example") == 1


def test_an_unreadable_existing_style_is_kept_and_extended() -> None:
    html = _write(
        [_change("/html/body/p", "line-height", "1.6")],
        MAIL.replace("<p>Body</p>", '<p style="color red">Body</p>'),
    )
    assert 'style="color red; line-height: 1.6"' in html


def test_the_writer_notes_how_many_elements_it_styled() -> None:
    artifact = InlineWriter().write(
        [
            _change("/html/body/h1", "font-size", "32px"),
            _change("/html/body/p", "line-height", "1.6"),
        ],
        _artifact(),
    )
    assert any("Wrote inline styles on 2 element(s)" in n for n in artifact.notes)
