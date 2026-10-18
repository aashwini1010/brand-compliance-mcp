"""Tests for brand_compliance.core.paths."""

from pathlib import Path

import pytest

from brand_compliance.core.errors import InvalidInputError, PathNotAllowedError
from brand_compliance.core.paths import (
    resolve_within,
    validate_input_file,
    validate_output_dir,
)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """An allowed folder containing one guide, plus a file outside it."""
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    (allowed / "guide.md").write_text("# guide")
    (tmp_path / "secret.md").write_text("secret")
    return allowed


def test_resolve_within_accepts_file_inside_allowed_folder(workspace: Path) -> None:
    assert (
        resolve_within(workspace / "guide.md", [workspace])
        == (workspace / "guide.md").resolve()
    )


def test_resolve_within_rejects_file_outside_allowed_folder(workspace: Path) -> None:
    with pytest.raises(PathNotAllowedError):
        resolve_within(workspace.parent / "secret.md", [workspace])


def test_resolve_within_rejects_parent_traversal(workspace: Path) -> None:
    with pytest.raises(PathNotAllowedError):
        resolve_within(workspace / ".." / "secret.md", [workspace])


def test_resolve_within_rejects_symlink_escaping_the_folder(workspace: Path) -> None:
    link = workspace / "link.md"
    link.symlink_to(workspace.parent / "secret.md")
    with pytest.raises(PathNotAllowedError):
        resolve_within(link, [workspace])


def test_validate_input_file_accepts_valid_file(workspace: Path) -> None:
    result = validate_input_file(workspace / "guide.md", [workspace], 1000, [".md"])
    assert result.name == "guide.md"


def test_validate_input_file_rejects_missing_file(workspace: Path) -> None:
    with pytest.raises(InvalidInputError):
        validate_input_file(workspace / "nope.md", [workspace], 1000, [".md"])


def test_validate_input_file_rejects_wrong_extension(workspace: Path) -> None:
    with pytest.raises(InvalidInputError):
        validate_input_file(workspace / "guide.md", [workspace], 1000, [".html"])


def test_validate_input_file_rejects_oversized_file(workspace: Path) -> None:
    with pytest.raises(InvalidInputError):
        validate_input_file(workspace / "guide.md", [workspace], 3, [".md"])


def test_validate_output_dir_accepts_new_folder(workspace: Path) -> None:
    out = validate_output_dir(workspace / "out", [workspace])
    assert out.name == "out"


def test_validate_output_dir_rejects_folder_that_is_a_file(workspace: Path) -> None:
    with pytest.raises(InvalidInputError):
        validate_output_dir(workspace / "guide.md", [workspace])


def test_validate_output_dir_rejects_folder_holding_the_source(
    workspace: Path,
) -> None:
    with pytest.raises(PathNotAllowedError):
        validate_output_dir(
            workspace, [workspace], protected_files=[workspace / "guide.md"]
        )
