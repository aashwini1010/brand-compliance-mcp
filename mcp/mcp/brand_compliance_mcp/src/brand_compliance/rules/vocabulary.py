"""Vocabulary: guide wording -> standard roles, loaded from a TOML file."""

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from brand_compliance.core.errors import InvalidInputError
from brand_compliance.core.settings import DEFAULT_CONFIG_FILE
from brand_compliance.models.rule import RuleStatus

DEFAULT_VOCABULARY_FILE = DEFAULT_CONFIG_FILE.parent / "vocabulary.toml"


class PhraseStatus(BaseModel):
    """Unreadable text that mentions one of these words gets this status.

    ``patterns`` are regular expressions matched case-insensitively.
    """

    patterns: list[str]
    status: RuleStatus
    reason: str


class SectionStatus(BaseModel):
    """A guide section that cannot be applied, and why."""

    match: str
    status: RuleStatus
    reason: str


SpecKind = Literal[
    "radius_variable",
    "size_padding",
    "font_spec",
    "box_pairs",
    "declarations",
    "padding_axes",
    "variants_unresolved",
    "text_style",
]


class BulletSpec(BaseModel):
    """A ``Label: value`` bullet in a section, and how to read it."""

    section: str
    label: str
    role: str
    kind: SpecKind

    def matches(self, section: str, label: str) -> bool:
        """Return True if a bullet with this section title and label is this spec."""
        return (
            section.lower().startswith(self.section.lower())
            and label.strip().lower() == self.label.lower()
        )


class Vocabulary(BaseModel):
    """All wording maps used by the normalizer."""

    scope_words: dict[str, str] = Field(default_factory=dict)
    type_token_roles: dict[str, str] = Field(default_factory=dict)
    variant_roles: dict[str, str] = Field(default_factory=dict)
    selector_roles: dict[str, str] = Field(default_factory=dict)
    css_variable_roles: dict[str, str] = Field(default_factory=dict)
    role_phrases: dict[str, str] = Field(default_factory=dict)
    surface_phrases: dict[str, str] = Field(default_factory=dict)
    effect_words: dict[str, list[str]] = Field(default_factory=dict)
    directive_keywords: list[str] = Field(default_factory=list)
    css_keywords: list[str] = Field(default_factory=list)
    section_status: list[SectionStatus] = Field(default_factory=list)
    phrase_status: list[PhraseStatus] = Field(default_factory=list)
    bullet_specs: list[BulletSpec] = Field(default_factory=list)

    def find_bullet_spec(self, section: str, label: str) -> BulletSpec | None:
        """Return the spec for a bullet, if the vocabulary lists one."""
        return next((s for s in self.bullet_specs if s.matches(section, label)), None)


def load_vocabulary(path: Path | None = None) -> Vocabulary:
    """Load the vocabulary file (default: ``config/vocabulary.toml``)."""
    source = path or DEFAULT_VOCABULARY_FILE
    try:
        raw = tomllib.loads(source.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise InvalidInputError(f"Cannot read vocabulary {source.name}: {exc}") from exc
    return Vocabulary(
        scope_words=raw.get("scope_words", {}),
        type_token_roles=raw.get("type_token_roles", {}),
        variant_roles=raw.get("variant_roles", {}),
        selector_roles=raw.get("selector_roles", {}),
        css_variable_roles=raw.get("css_variable_roles", {}),
        role_phrases=raw.get("role_phrases", {}),
        surface_phrases=raw.get("surface_phrases", {}),
        effect_words=raw.get("effect_words", {}),
        directive_keywords=raw.get("directives", {}).get("keywords", []),
        css_keywords=raw.get("css_keywords", {}).get("values", []),
        section_status=raw.get("section_status", []),
        phrase_status=raw.get("phrase_status", []),
        bullet_specs=raw.get("bullet_specs", []),
    )
