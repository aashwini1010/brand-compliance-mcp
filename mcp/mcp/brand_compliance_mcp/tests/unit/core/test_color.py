"""Tests for brand_compliance.core.color."""

import pytest

from brand_compliance.core.color import Color, parse_color
from brand_compliance.core.errors import InvalidInputError


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("#09A78D", "#09a78d"),
        ("#0af", "#00aaff"),
        ("rgb(9, 167, 141)", "#09a78d"),
        ("rgb(9 167 141)", "#09a78d"),
        ("hsl(120, 100%, 25%)", "#008000"),
        ("WHITE", "#ffffff"),
        ("rgba(0, 0, 0, 0.5)", "#00000080"),
        ("#00000080", "#00000080"),
    ],
)
def test_parse_color_accepts_supported_notations(text: str, expected: str) -> None:
    assert parse_color(text).to_hex() == expected


@pytest.mark.parametrize(
    "text", ["", "#12", "#ggg", "rgb(1,2)", "rgb(a,b,c)", "tomato"]
)
def test_parse_color_rejects_unknown_notation(text: str) -> None:
    with pytest.raises(InvalidInputError):
        parse_color(text)


def test_parse_color_clamps_out_of_range_channels() -> None:
    assert parse_color("rgb(300, -5, 0)").to_hex() == "#ff0000"


def test_over_blends_translucent_colour_on_background() -> None:
    blended = Color(0, 0, 0, 0.5).over(Color(255, 255, 255))
    assert blended.to_hex() == "#808080"


def test_parse_color_hsl_is_rounded_not_identical_to_guide_hex() -> None:
    """Guide HSL values are rounded; hex stays the source of truth."""
    assert parse_color("hsl(169, 90%, 35%)").to_hex() != "#09a78d"
