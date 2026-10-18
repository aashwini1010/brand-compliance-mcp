"""Tests for brand_compliance.core.contrast (reference values from WCAG)."""

import pytest

from brand_compliance.core.color import parse_color
from brand_compliance.core.contrast import contrast_ratio, meets_aa

WHITE = parse_color("#ffffff")


def test_contrast_ratio_black_on_white_is_21() -> None:
    assert contrast_ratio(parse_color("#000"), WHITE) == pytest.approx(21.0)


def test_contrast_ratio_is_symmetric_in_lightness_order() -> None:
    a, b = parse_color("#194247"), parse_color("#f6f3f0")
    assert contrast_ratio(a, b) == pytest.approx(contrast_ratio(b, a))


def test_meets_aa_passes_at_4_54() -> None:
    assert meets_aa(parse_color("#767676"), WHITE)


def test_meets_aa_fails_at_4_48() -> None:
    assert not meets_aa(parse_color("#777777"), WHITE)


def test_meets_aa_large_text_uses_lower_threshold() -> None:
    tide = parse_color("#09A78D")
    assert not meets_aa(tide, WHITE)
    assert meets_aa(tide, WHITE, large_text=True)


def test_contrast_ratio_blends_translucent_foreground_first() -> None:
    translucent_black = parse_color("rgba(0,0,0,0.5)")
    assert contrast_ratio(translucent_black, WHITE) == pytest.approx(3.95, abs=0.01)


def test_brand_pulse_green_fails_on_linen_but_passes_on_moss() -> None:
    pulse = parse_color("#52E081")
    assert not meets_aa(pulse, parse_color("#F6F3F0"))
    assert meets_aa(pulse, parse_color("#0C2226"))


def test_is_light_surface_separates_linen_from_moss() -> None:
    from brand_compliance.core.contrast import is_light_surface

    assert is_light_surface(parse_color("#F6F3F0"))
    assert not is_light_surface(parse_color("#0C2226"))
