"""Tests for brand_compliance.core.hashing."""

from pathlib import Path

from brand_compliance.core.hashing import sha256_bytes, sha256_file

EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_sha256_bytes_matches_known_value_for_empty_input() -> None:
    assert sha256_bytes(b"") == EMPTY_SHA256


def test_sha256_file_matches_sha256_bytes(tmp_path: Path) -> None:
    target = tmp_path / "a.html"
    target.write_bytes(b"<p>hi</p>")
    assert sha256_file(target) == sha256_bytes(b"<p>hi</p>")


def test_sha256_file_changes_when_content_changes(tmp_path: Path) -> None:
    target = tmp_path / "a.html"
    target.write_bytes(b"one")
    before = sha256_file(target)
    target.write_bytes(b"two")
    assert sha256_file(target) != before
