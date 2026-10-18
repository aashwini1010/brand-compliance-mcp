"""Tests for brand_compliance.rules.vocabulary."""

from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import ValidationError

from brand_compliance.core.errors import InvalidInputError
from brand_compliance.models.rule import RuleStatus
from brand_compliance.rules.vocabulary import load_vocabulary


def test_load_vocabulary_reads_the_default_file() -> None:
    vocabulary = load_vocabulary()
    assert vocabulary.variant_roles["primary (cta)"] == "button.primary"
    assert vocabulary.type_token_roles["--fs-h1"] == "heading.h1"


def test_load_vocabulary_parses_section_status_entries() -> None:
    entry = next(
        s for s in load_vocabulary().section_status if s.match.startswith("5.")
    )
    assert entry.status is RuleStatus.NOT_APPLICABLE
    assert "never invents" in entry.reason


def test_load_vocabulary_accepts_a_custom_file(
    write_file: Callable[[str, str], Path],
) -> None:
    path = write_file("v.toml", '[variant_roles]\n"main" = "button.primary"\n')
    assert load_vocabulary(path).variant_roles == {"main": "button.primary"}


def test_load_vocabulary_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(InvalidInputError):
        load_vocabulary(tmp_path / "missing.toml")


def test_load_vocabulary_rejects_invalid_toml(
    write_file: Callable[[str, str], Path],
) -> None:
    with pytest.raises(InvalidInputError):
        load_vocabulary(write_file("v.toml", "not = = toml"))


def test_find_bullet_spec_matches_section_prefix_and_label_case_insensitively() -> None:
    spec = load_vocabulary().find_bullet_spec("7.1 Buttons", "SHAPE")
    assert spec is not None
    assert spec.role == "button"


def test_find_bullet_spec_returns_none_for_unlisted_bullet() -> None:
    assert load_vocabulary().find_bullet_spec("7.1 Buttons", "Voice") is None


def test_load_vocabulary_rejects_unknown_bullet_kind(
    write_file: Callable[[str, str], Path],
) -> None:
    path = write_file(
        "v.toml",
        '[[bullet_specs]]\nsection = "a"\nlabel = "b"\nrole = "c"\nkind = "typo"\n',
    )
    with pytest.raises(ValidationError):
        load_vocabulary(path)
