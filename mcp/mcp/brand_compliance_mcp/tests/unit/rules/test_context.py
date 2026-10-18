"""Tests for brand_compliance.rules.context."""

import pytest

from brand_compliance.models.rule import Scope
from brand_compliance.rules.context import Context
from brand_compliance.rules.vocabulary import Vocabulary


@pytest.fixture
def ctx() -> Context:
    vocabulary = Vocabulary(
        scope_words={"dark mode": "dark"},
        role_phrases={"body text": "text.body"},
        css_keywords=["transparent", "none", "currentcolor"],
    )
    return Context(
        vocabulary,
        palette={"--leaf": "#194247", "--linen": "#f6f3f0", "--moss": "#0c2226"},
    )


def test_scope_for_uses_section_words_and_defaults_to_all(ctx: Context) -> None:
    assert ctx.scope_for("2.2 Dark Mode Accent Palette") is Scope.DARK
    assert ctx.scope_for("2.1 Core Tokens") is Scope.ALL


def test_resolve_value_maps_token_to_hex(ctx: Context) -> None:
    assert ctx.resolve_value("--leaf") == [(Scope.ALL, "#194247")]


def test_resolve_value_splits_light_and_dark_alternatives(ctx: Context) -> None:
    result = ctx.resolve_value("--leaf (on light) / --linen (on dark)")
    assert result == [(Scope.LIGHT, "#194247"), (Scope.DARK, "#f6f3f0")]


def test_resolve_value_accepts_listed_keywords(ctx: Context) -> None:
    assert ctx.resolve_value("transparent") == [(Scope.ALL, "transparent")]


def test_resolve_value_resolves_border_colour(ctx: Context) -> None:
    assert ctx.resolve_value("1.5px solid currentColor") == [
        (Scope.ALL, "1.5px solid currentcolor")
    ]
    assert ctx.resolve_value("2px solid --leaf") == [(Scope.ALL, "2px solid #194247")]


@pytest.mark.parametrize(
    "raw", ["", "--unknown", "darken 8%", "current", "2px solid --nope"]
)
def test_resolve_value_returns_none_when_not_understood(ctx: Context, raw: str) -> None:
    assert ctx.resolve_value(raw) is None


def test_replace_tokens_swaps_known_and_rejects_unknown(ctx: Context) -> None:
    assert ctx.replace_tokens("2px solid --leaf") == "2px solid #194247"
    assert ctx.replace_tokens("2px solid --nope") is None


def test_surface_scope_requires_all_surfaces_to_agree(ctx: Context) -> None:
    assert ctx.surface_scope(["--linen"]) is Scope.LIGHT
    assert ctx.surface_scope(["--moss"]) is Scope.DARK
    assert ctx.surface_scope(["--linen", "--moss"]) is None
    assert ctx.surface_scope(["--unknown"]) is None


def test_find_role_returns_role_of_known_phrase(ctx: Context) -> None:
    assert ctx.find_role("Body text minimum contrast") == "text.body"
    assert ctx.find_role("Something else") is None
