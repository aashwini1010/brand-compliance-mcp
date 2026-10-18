"""Tests for brand_compliance.core.css."""

import pytest

from brand_compliance.core.css import (
    format_declarations,
    merge_declarations,
    parse_declarations,
)
from brand_compliance.core.errors import ParseFailedError


def test_parse_declarations_reads_pairs_in_order() -> None:
    result = parse_declarations("color: #fff; Margin:0")
    assert list(result.items()) == [("color", "#fff"), ("margin", "0")]


def test_parse_declarations_keeps_important_flag() -> None:
    assert parse_declarations("color: red !important") == {"color": "red !important"}


def test_parse_declarations_keeps_custom_property_case() -> None:
    assert parse_declarations("--Brand-Tide: #09a78d") == {"--Brand-Tide": "#09a78d"}


def test_parse_declarations_keeps_commas_in_values() -> None:
    value = parse_declarations('font-family: "Montserrat", Arial, sans-serif')
    assert value["font-family"] == '"Montserrat", Arial, sans-serif'


def test_parse_declarations_ignores_comments_and_blank_input() -> None:
    assert parse_declarations("/* note */ color: red;") == {"color": "red"}
    assert parse_declarations("") == {}


def test_parse_declarations_raises_on_malformed_input() -> None:
    with pytest.raises(ParseFailedError):
        parse_declarations("color red")


def test_format_declarations_round_trips() -> None:
    text = "color: red; margin: 0"
    assert format_declarations(parse_declarations(text)) == text


def test_merge_declarations_prefers_overrides_without_mutating() -> None:
    base = {"color": "red", "margin": "0"}
    merged = merge_declarations(base, {"color": "blue"})
    assert merged == {"color": "blue", "margin": "0"}
    assert base["color"] == "red"


def test_parse_declarations_skips_nested_rules() -> None:
    assert parse_declarations("color: red; @media print { a { b: c } }") == {
        "color": "red"
    }
