"""Tests for brand_compliance.core.text."""

import pytest

from brand_compliance.core.text import clean_text, split_top_level


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("`#09A78D`", "#09A78D"),
        ("**NEVER** use  this", "NEVER use this"),
        ("*A reference*", "A reference"),
        ("  spaced \n out ", "spaced out"),
        ("", ""),
        ("a * b", "a * b"),
    ],
)
def test_clean_text_removes_marks_and_collapses_spaces(raw: str, expected: str) -> None:
    assert clean_text(raw) == expected


def test_split_top_level_ignores_separators_inside_parentheses() -> None:
    assert split_top_level("a, rgba(1,2,3), b") == ["a", "rgba(1,2,3)", "b"]


def test_split_top_level_supports_several_separators_and_drops_blanks() -> None:
    assert split_top_level("a; b, c;;") == ["a", "b", "c"]


def test_split_top_level_handles_unbalanced_parenthesis_safely() -> None:
    assert split_top_level("a), b") == ["a)", "b"]
