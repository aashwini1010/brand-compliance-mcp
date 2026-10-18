"""Tests for brand_compliance.core.units."""

import pytest

from brand_compliance.core.errors import InvalidInputError
from brand_compliance.core.units import format_px, to_px


@pytest.mark.parametrize(
    ("length", "expected"),
    [
        ("16px", 16.0),
        ("1rem", 16.0),
        ("0.9375rem", 15.0),
        ("1.5em", 24.0),
        ("12pt", 16.0),
        ("0", 0.0),
        (" 2REM ", 32.0),
    ],
)
def test_to_px_converts_supported_units(length: str, expected: float) -> None:
    assert to_px(length) == pytest.approx(expected)


def test_to_px_uses_given_base_size() -> None:
    assert to_px("2rem", base_px=10) == 20.0


@pytest.mark.parametrize(
    "length", ["clamp(1rem, 2vw, 3rem)", "50%", "4vw", "12", "abc", ""]
)
def test_to_px_rejects_values_it_cannot_resolve(length: str) -> None:
    with pytest.raises(InvalidInputError):
        to_px(length)


def test_format_px_drops_needless_decimals() -> None:
    assert format_px(15.0) == "15px"
    assert format_px(12.8) == "12.8px"
    assert format_px(10.666666) == "10.67px"
