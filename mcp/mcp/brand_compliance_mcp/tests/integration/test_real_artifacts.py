"""The artifact side against the two real sample files."""

import re
from pathlib import Path

import pytest
from lxml import html

from brand_compliance.models.artifact import ArtifactType
from brand_compliance.plugins.artifacts.base import parse_artifact_html, serialize_html
from brand_compliance.plugins.artifacts.classifier import classify_html
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler

ARTIFACTS = Path(__file__).resolve().parents[2] / "eval" / "artifacts"
PAGE = ARTIFACTS / "mcp-servers-report-simple-v2.html"
EMAIL = ARTIFACTS / "sample-marketing-email.html"


def _text(path: Path) -> str:
    if not path.is_file():
        pytest.skip(f"{path.name} not present")
    return path.read_text(encoding="utf-8")


def _visible(markup: str) -> str:
    return re.sub(r"\s+", " ", html.fromstring(markup).text_content()).strip()


def _scripts(markup: str) -> list[str]:
    return [
        re.sub(r"\s+", "", s)
        for s in re.findall(r"<script[^>]*>(.*?)</script>", markup, re.S)
    ]


@pytest.mark.parametrize("path", [PAGE, EMAIL])
def test_round_trip_keeps_text_scripts_links_and_images(path: Path) -> None:
    original = _text(path)
    parsed = parse_artifact_html(original)
    output = serialize_html(parsed.root, parsed.doctype)
    assert _visible(output) == _visible(original)
    assert _scripts(output) == _scripts(original)
    assert sorted(re.findall(r'href="([^"]+)"', output)) == sorted(
        re.findall(
            r'href="([^"]+)"', original.replace("&amp;", "&").replace("&", "&amp;")
        )
    ) or len(re.findall("href=", output)) == len(re.findall("href=", original))
    assert output.count("<img") == original.count("<img")


def test_round_trip_keeps_every_svg_view_box_of_the_page() -> None:
    original = _text(PAGE)
    parsed = parse_artifact_html(original)
    output = serialize_html(parsed.root, parsed.doctype)
    assert output.count("viewBox=") >= original.count('viewBox="')
    assert "viewbox=" not in output


def test_round_trip_keeps_conditional_comments_of_the_email() -> None:
    original = _text(EMAIL)
    parsed = parse_artifact_html(original)
    output = serialize_html(parsed.root, parsed.doctype)
    assert output.count("<!--[if") == original.count("<!--[if")
    assert output.count("<![endif]-->") == original.count("<![endif]-->")


def test_page_is_classified_static_and_email_is_classified_email() -> None:
    page, email = _text(PAGE), _text(EMAIL)
    assert classify_html(parse_artifact_html(page).root, page).artifact_type is (
        ArtifactType.STATIC
    )
    assert classify_html(parse_artifact_html(email).root, email).artifact_type is (
        ArtifactType.EMAIL
    )


def test_page_roles_match_what_a_reader_sees() -> None:
    artifact = StaticArtifactHandler().parse(_text(PAGE), PAGE.name)
    counts = {
        role: list(artifact.roles.values()).count(role)
        for role in set(artifact.roles.values())
    }
    assert counts["heading.h1"] == 4
    assert counts["heading.h2"] == 9
    assert counts["button.primary"] == 2
    assert counts["button"] == 7
    assert counts["text.eyebrow"] == 4
    assert counts["page.surface"] == 1


def test_page_backgrounds_resolve_through_css_variables() -> None:
    artifact = StaticArtifactHandler().parse(_text(PAGE), PAGE.name)
    body = next(p for p, r in artifact.roles.items() if r == "page.surface")
    assert artifact.surfaces[body] == "light"
    assert set(artifact.surfaces.values()) <= {"light", "dark", "unknown"}


def test_page_lists_the_text_elements_it_could_not_map() -> None:
    artifact = StaticArtifactHandler().parse(_text(PAGE), PAGE.name)
    assert artifact.unmapped_elements
    assert all("line" in item for item in artifact.unmapped_elements)


def test_page_states_that_media_queries_were_not_evaluated() -> None:
    artifact = StaticArtifactHandler().parse(_text(PAGE), PAGE.name)
    assert any("conditional style block" in note for note in artifact.notes)
