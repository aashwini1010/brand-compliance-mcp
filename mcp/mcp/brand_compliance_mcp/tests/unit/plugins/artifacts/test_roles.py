"""Tests for brand_compliance.plugins.artifacts.roles."""

from collections.abc import Callable
from pathlib import Path

import pytest

from brand_compliance.core.errors import InvalidInputError
from brand_compliance.plugins.artifacts.base import parse_artifact_html
from brand_compliance.plugins.artifacts.roles import (
    RoleRule,
    load_role_rules,
    map_roles,
)

PAGE = """<html><head><title>t</title></head><body>
<h1>Title</h1><p class="eyebrow">LABEL</p><p>Body text</p>
<button class="btn primary">Go</button><button class="btn">Back</button>
<a class="cta" href="#">Act</a><a href="/x">link</a>
<div class="panel">loose text</div><h5>small heading</h5>
<svg><title>icon</title></svg></body></html>"""


def _roles(text: str = PAGE) -> dict[str, str]:
    root = parse_artifact_html(text).root
    return map_roles(root, load_role_rules()).roles


def test_load_role_rules_reads_the_default_file() -> None:
    rules = load_role_rules()
    assert rules[0].role == "button.primary"
    assert any(r.role == "text.body" for r in rules)


def test_headings_text_and_links_get_their_roles() -> None:
    roles = _roles()
    assert roles["/html/body/h1"] == "heading.h1"
    assert roles["/html/body/p[2]"] == "text.body"
    assert roles["/html/body/a[2]"] == "link"
    assert roles["/html/body"] == "page.surface"


def test_first_matching_rule_wins_so_eyebrow_is_not_body_text() -> None:
    assert _roles()["/html/body/p[1]"] == "text.eyebrow"


def test_a_button_is_primary_only_when_its_markup_says_so() -> None:
    roles = _roles()
    assert roles["/html/body/button[1]"] == "button.primary"
    assert roles["/html/body/button[2]"] == "button"
    assert roles["/html/body/a[1]"] == "button.primary"


def test_unmapped_text_elements_are_listed_not_styled() -> None:
    root = parse_artifact_html(PAGE).root
    result = map_roles(root, load_role_rules())
    listed = " ".join(result.unmapped)
    assert "<div.panel>" in listed
    assert "<h5>" in listed
    assert "/html/body/h1" not in listed


def test_head_and_svg_content_never_get_roles_or_appear_unmapped() -> None:
    root = parse_artifact_html(PAGE).root
    result = map_roles(root, load_role_rules())
    assert not any("title" in path for path in result.roles)
    assert not any("<title>" in item for item in result.unmapped)


def test_custom_role_rules_are_respected() -> None:
    root = parse_artifact_html("<body><div class='hero'>x</div></body>").root
    rules = [RoleRule(role="heading.display", selector=".hero")]
    assert map_roles(root, rules).roles == {"/html/body/div": "heading.display"}


def test_load_role_rules_rejects_bad_file(
    write_file: Callable[[str, str], Path],
) -> None:
    with pytest.raises(InvalidInputError):
        load_role_rules(write_file("r.toml", "[[roles]]\nrole = 1\n"))
    with pytest.raises(InvalidInputError):
        load_role_rules(write_file("r2.toml", "not = = toml"))


def test_role_aliases_are_read_from_the_default_file() -> None:
    from brand_compliance.plugins.artifacts.roles import load_role_aliases

    aliases = load_role_aliases()
    assert aliases["button.label"] == "button"
    assert aliases["document"] == "page.surface"


def test_role_aliases_reject_a_bad_file(
    write_file: Callable[[str, str], Path],
) -> None:
    from brand_compliance.plugins.artifacts.roles import load_role_aliases

    with pytest.raises(InvalidInputError):
        load_role_aliases(write_file("a.toml", "[[aliases]]\nrule_role = 'x'\n"))
