"""Tests for brand_compliance.plugins.sources.base."""

from collections.abc import Callable
from pathlib import Path

import pytest

from brand_compliance.core.errors import InvalidInputError, ParseFailedError
from brand_compliance.plugins.sources.base import read_source_text

WriteFile = Callable[[str, str], Path]


def test_read_source_text_returns_file_content(write_file: WriteFile) -> None:
    path = write_file("g.md", "# hi")
    assert read_source_text(path, [".md"]) == "# hi"


def test_read_source_text_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(InvalidInputError):
        read_source_text(tmp_path / "nope.md", [".md"])


def test_read_source_text_rejects_wrong_suffix(write_file: WriteFile) -> None:
    with pytest.raises(InvalidInputError):
        read_source_text(write_file("g.txt", "x"), [".md"])


def test_read_source_text_rejects_oversized_file(write_file: WriteFile) -> None:
    with pytest.raises(InvalidInputError):
        read_source_text(write_file("g.md", "abcdef"), [".md"], max_bytes=3)


def test_read_source_text_rejects_non_utf8_file(tmp_path: Path) -> None:
    path = tmp_path / "g.md"
    path.write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(ParseFailedError):
        read_source_text(path, [".md"])
