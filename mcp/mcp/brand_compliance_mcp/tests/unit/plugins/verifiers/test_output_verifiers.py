"""Tests for the structure, assets, original-intact and idempotence verifiers."""

from collections.abc import Callable
from pathlib import Path

from brand_compliance.core.contracts import Verifier
from brand_compliance.core.hashing import sha256_file
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import Change
from brand_compliance.plugins.appliers.font import FONT_SOURCE_PROPERTY, HEAD_PATH
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler
from brand_compliance.plugins.verifiers.assets import AssetsVerifier
from brand_compliance.plugins.verifiers.idempotence import IdempotenceVerifier
from brand_compliance.plugins.verifiers.original import OriginalIntactVerifier
from brand_compliance.plugins.verifiers.structure import StructureVerifier
from brand_compliance.plugins.writers.static import StylesheetWriter

PAGE = """<!doctype html><html><head><title>T</title>
<link rel="stylesheet" href="site.css"><style>.a{background:url(bg.png)}</style></head>
<body><!--[if mso]>keep<![endif]--><h1 id="top">Title</h1>
<p class="a">Hello <b>world</b></p><a href="#top">up</a>
<img src="x.png" alt="x" srcset="x1.png 1x, x2.png 2x">
<script>var a = 1;</script></body></html>"""


def _pair() -> tuple[ArtifactModel, ArtifactModel]:
    handler = StaticArtifactHandler()
    return handler.parse(PAGE, "p.html"), handler.parse(PAGE, "p.html")


def _check(
    verifier: Verifier,
    original: ArtifactModel,
    output: ArtifactModel,
    changes: list[Change] | None = None,
):  # type: ignore[no-untyped-def]
    return verifier.check(original, output, [], changes or [])


def _change(location: str, prop: str, after: str) -> Change:
    return Change(id="C1", rule_id="R1", location=location, property=prop, after=after)


def test_verifiers_implement_the_contract(tmp_path: Path) -> None:
    file = tmp_path / "a.html"
    file.write_text("x")
    for verifier in (
        StructureVerifier(),
        AssetsVerifier(),
        OriginalIntactVerifier(file, "abc"),
        IdempotenceVerifier(lambda text: text),
    ):
        assert isinstance(verifier, Verifier)


def test_structure_passes_for_identical_trees() -> None:
    original, output = _pair()
    assert _check(StructureVerifier(), original, output).passed


def test_structure_ignores_the_tools_own_additions() -> None:
    original, output = _pair()
    changes = [
        _change("/html/body/h1", "font-size", "3rem"),
        _change(HEAD_PATH, FONT_SOURCE_PROPERTY, "https://f.example/a.css"),
    ]
    StylesheetWriter().write(changes, output)
    assert _check(StructureVerifier(), original, output).passed


def test_structure_detects_changed_text() -> None:
    original, output = _pair()
    output.tree.find(".//h1").text = "Other"
    assert not _check(StructureVerifier(), original, output).passed


def test_structure_detects_a_changed_attribute() -> None:
    original, output = _pair()
    output.tree.find(".//img").set("alt", "changed")
    assert not _check(StructureVerifier(), original, output).passed


def test_structure_detects_a_removed_element() -> None:
    original, output = _pair()
    output.tree.find(".//b").getparent().remove(output.tree.find(".//b"))
    result = _check(StructureVerifier(), original, output)
    assert not result.passed
    assert "nodes before" in result.details[0]


def test_structure_detects_a_changed_comment_and_script() -> None:
    original, output = _pair()
    output.tree.find(".//script").text = "var a = 2;"
    assert not _check(StructureVerifier(), original, output).passed
    original, output = _pair()
    for node in output.tree.iter():
        if not isinstance(node.tag, str):
            node.text = "changed"
    assert not _check(StructureVerifier(), original, output).passed


def test_structure_detects_a_changed_doctype() -> None:
    original, output = _pair()
    output.doctype = None
    assert "doctype changed" in _check(StructureVerifier(), original, output).details[0]


def test_assets_pass_when_everything_is_preserved() -> None:
    original, output = _pair()
    assert _check(AssetsVerifier(), original, output).passed


def test_assets_detect_a_missing_image() -> None:
    original, output = _pair()
    output.tree.find(".//img").set("src", "other.png")
    result = _check(AssetsVerifier(), original, output)
    assert any("missing: x.png" in d for d in result.details)
    assert any("unexpected: other.png" in d for d in result.details)


def test_assets_detect_a_lost_srcset_entry_and_css_url() -> None:
    original, output = _pair()
    output.tree.find(".//img").set("srcset", "x1.png 1x")
    output.tree.find(".//style").text = ".a{}"
    result = _check(AssetsVerifier(), original, output)
    assert any("x2.png" in d for d in result.details)
    assert any("bg.png" in d for d in result.details)


def test_assets_allow_the_font_link_named_by_a_change() -> None:
    original, output = _pair()
    url = "https://fonts.example/a.css"
    changes = [_change(HEAD_PATH, FONT_SOURCE_PROPERTY, url)]
    StylesheetWriter().write(changes, output)
    assert _check(AssetsVerifier(), original, output, changes).passed


def test_assets_reject_an_unannounced_addition() -> None:
    original, output = _pair()
    link = output.tree.find(".//link").makeelement(
        "link", {"rel": "stylesheet", "href": "evil.css"}
    )
    output.tree.find("head").append(link)
    assert any(
        "unexpected: evil.css" in d
        for d in _check(AssetsVerifier(), original, output).details
    )


def test_assets_detect_a_broken_anchor() -> None:
    original, output = _pair()
    del output.tree.find(".//h1").attrib["id"]
    assert any("#top" in d for d in _check(AssetsVerifier(), original, output).details)


def test_assets_do_not_blame_the_tool_for_an_anchor_that_was_already_broken() -> None:
    handler = StaticArtifactHandler()
    page = "<html><body><a href='#nowhere'>x</a></body></html>"
    original, output = handler.parse(page, "p.html"), handler.parse(page, "p.html")
    assert _check(AssetsVerifier(), original, output).passed


def test_original_intact_passes_and_fails_on_the_fingerprint(
    write_file: Callable[[str, str], Path],
) -> None:
    path = write_file("a.html", "<p>x</p>")
    original, output = _pair()
    verifier = OriginalIntactVerifier(path, sha256_file(path))
    assert _check(verifier, original, output).passed
    path.write_text("<p>changed</p>")
    result = _check(verifier, original, output)
    assert not result.passed
    assert "CHANGED" in result.details[0]


def test_idempotence_passes_when_a_second_run_gives_the_same_output() -> None:
    original, output = _pair()
    assert _check(IdempotenceVerifier(lambda text: text), original, output).passed


def test_idempotence_reports_where_the_second_run_differs() -> None:
    original, output = _pair()
    result = _check(IdempotenceVerifier(lambda text: text + "!"), original, output)
    assert not result.passed
    assert "differs at character" in result.details[0]


MAIL = (
    "<html><body><p style='margin:0;color:red'>One</p>"
    "<p style='display:none;max-height:0'>Hidden</p><p>Plain</p></body></html>"
)


def _mail_pair() -> tuple[ArtifactModel, ArtifactModel]:
    from brand_compliance.plugins.artifacts.email import EmailArtifactHandler

    handler = EmailArtifactHandler()
    return handler.parse(MAIL, "m.html"), handler.parse(MAIL, "m.html")


def test_structure_for_emails_accepts_exactly_the_planned_style_edits() -> None:
    original, output = _mail_pair()
    changes = [
        _change("/html/body/p[1]", "color", "#102a43"),
        _change("/html/body/p[3]", "line-height", "1.6"),
    ]
    output.tree.xpath("/html/body/p[1]")[0].set("style", "margin: 0; color: #102a43")
    output.tree.xpath("/html/body/p[3]")[0].set("style", "line-height: 1.6")
    assert _check(StructureVerifier(), original, output, changes).passed


def test_structure_for_emails_rejects_a_style_edit_nobody_planned() -> None:
    original, output = _mail_pair()
    changes = [_change("/html/body/p[1]", "color", "#102a43")]
    output.tree.xpath("/html/body/p[1]")[0].set(
        "style", "margin: 0; color: #102a43; font-size: 99px"
    )
    assert not _check(StructureVerifier(), original, output, changes).passed


def test_structure_for_emails_rejects_a_change_that_was_not_written() -> None:
    original, output = _mail_pair()
    changes = [_change("/html/body/p[3]", "line-height", "1.6")]
    assert not _check(StructureVerifier(), original, output, changes).passed


def test_structure_for_emails_ignores_formatting_of_untouched_styles() -> None:
    original, output = _mail_pair()
    output.tree.xpath("/html/body/p[2]")[0].set("style", "display: none; max-height: 0")
    assert _check(StructureVerifier(), original, output).passed


def test_structure_for_emails_rejects_changed_text_even_with_style_edits() -> None:
    original, output = _mail_pair()
    output.tree.xpath("/html/body/p[1]")[0].text = "Changed"
    assert not _check(StructureVerifier(), original, output).passed


def test_structure_for_static_pages_still_rejects_any_style_attribute_change() -> None:
    handler = StaticArtifactHandler()
    page = "<html><body><p style='color:red'>x</p></body></html>"
    original, output = handler.parse(page, "p.html"), handler.parse(page, "p.html")
    output.tree.xpath("/html/body/p")[0].set("style", "color: blue")
    assert not _check(StructureVerifier(), original, output).passed


def test_structure_detects_a_comment_dropped_from_outside_the_html_element() -> None:
    handler = StaticArtifactHandler()
    page = (
        "<!DOCTYPE html>\n<!-- licence notice -->\n<html><body><p>x</p></body></html>"
    )
    original = handler.parse(page, "p.html")
    dropped = handler.parse(page.replace("<!-- licence notice -->", ""), "p.html")
    result = _check(StructureVerifier(), original, dropped)
    assert not result.passed
    assert "nodes before" in result.details[0]
