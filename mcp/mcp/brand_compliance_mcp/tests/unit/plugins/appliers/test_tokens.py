"""Tests for the applier that points page colour variables at the palette."""

from pathlib import Path

import pytest

from brand_compliance.core.errors import InvalidInputError
from brand_compliance.models.artifact import ArtifactType
from brand_compliance.models.rule import Rule, RuleStatus
from brand_compliance.models.source import SourceSpan
from brand_compliance.plugins.appliers.tokens import (
    ROOT_PATH,
    TokenApplier,
    TokenMap,
    load_token_maps,
)
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler

PAGE = """<!doctype html><html><head><style>
:root{--accent:#2446a8; --bar:#2a78d6}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--accent:#8fa7f2}}
:root[data-theme="dark"]{--accent:#8fa7f2; --bar:#3987e5}
a{color:var(--accent)}
</style></head><body><a href="#x">link</a></body></html>"""

MAPS = [
    TokenMap("--accent", light="--digital-pavo", dark="--dm-accent-tide"),
    TokenMap("--bar", light="--pulse-green"),
    TokenMap("--missing", light="--digital-pavo"),
]


def _token(prop: str, value: str) -> Rule:
    return Rule(
        id="R001",
        category="color_token",
        property=prop,
        value=value,
        status=RuleStatus.PENDING,
        source_span=SourceSpan(file="g.md", line_start=1),
    )


def _page(text: str = PAGE):  # type: ignore[no-untyped-def]
    return StaticArtifactHandler().parse(text, "page.html")


def test_plan_overrides_the_page_variable_that_maps_to_the_token() -> None:
    result = TokenApplier(MAPS).plan(_token("--digital-pavo", "#337077"), _page())
    assert [(c.property, c.after, c.surface) for c in result.changes] == [
        ("--accent", "#337077", "light")
    ]
    assert result.changes[0].before == "#2446a8"
    assert result.changes[0].location == ROOT_PATH


def test_plan_uses_the_dark_scope_values_for_dark_tokens() -> None:
    result = TokenApplier(MAPS).plan(_token("--dm-accent-tide", "#09a78d"), _page())
    assert [(c.property, c.surface, c.before) for c in result.changes] == [
        ("--accent", "dark", "#8fa7f2")
    ]


def test_plan_skips_dark_values_when_the_page_has_no_dark_theme() -> None:
    page = _page("<html><head><style>:root{--accent:#2446a8}</style></head></html>")
    result = TokenApplier(MAPS).plan(_token("--dm-accent-tide", "#09a78d"), page)
    assert result.changes == []


def test_plan_never_adds_a_variable_the_page_does_not_define() -> None:
    result = TokenApplier(MAPS).plan(_token("--digital-pavo", "#337077"), _page())
    assert "--missing" not in {c.property for c in result.changes}


def test_plan_is_silent_for_a_token_no_map_uses() -> None:
    result = TokenApplier(MAPS).plan(_token("--neural-beam", "#e5fd84"), _page())
    assert result.changes == [] and result.skipped == []


def test_plan_leaves_emails_alone() -> None:
    page = _page().model_copy(update={"artifact_type": ArtifactType.EMAIL})
    result = TokenApplier(MAPS).plan(_token("--digital-pavo", "#337077"), page)
    assert result.changes == []


def test_load_token_maps_reads_the_shipped_file() -> None:
    maps = {m.variable: m for m in load_token_maps()}
    assert maps["--accent"].light == "--digital-pavo"
    assert maps["--accent"].token_for("dark") == "--dm-accent-tide"


def test_load_token_maps_rejects_a_broken_file(tmp_path: Path) -> None:
    bad = tmp_path / "bad.toml"
    bad.write_text("[[maps]]\nlight = 'x'\n", encoding="utf-8")
    with pytest.raises(InvalidInputError):
        load_token_maps(bad)
