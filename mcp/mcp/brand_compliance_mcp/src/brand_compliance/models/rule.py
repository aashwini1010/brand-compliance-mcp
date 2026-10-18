"""Rules found in a guide and what became of them."""

from enum import StrEnum

from pydantic import BaseModel, Field

from brand_compliance.models.source import SourceSpan


class RuleStatus(StrEnum):
    """Final outcome of a rule. There is no 'guessed' status by design.

    ``REFERENCE`` is for definitions (palette tokens, variables) that other rules
    use; there is nothing to apply, so they are neither applied nor skipped.
    """

    PENDING = "pending"
    APPLIED = "applied"
    NOT_APPLICABLE = "understood_not_applicable"
    UNINTERPRETABLE = "could_not_interpret"
    CONFLICT_UNRESOLVED = "conflict_unresolved"
    REFERENCE = "reference"


class Severity(StrEnum):
    """How strongly the guide states a rule."""

    HARD = "hard"
    SOFT = "soft"


class Scope(StrEnum):
    """Where a rule is meant to apply."""

    ALL = "all"
    LIGHT = "light"
    DARK = "dark"
    STATIC = "static"
    EMAIL = "email"


class RuleCandidate(BaseModel):
    """A raw finding from one extractor, before normalisation."""

    id: str
    extractor: str
    text: str
    span: SourceSpan
    hints: dict[str, str] = Field(default_factory=dict)
    ai_assisted: bool = False


class Rule(BaseModel):
    """A normalised rule with its status and the reason for that status."""

    id: str
    category: str
    target_role: str | None = None
    property: str | None = None
    value: str | None = None
    scope: Scope = Scope.ALL
    severity: Severity = Severity.SOFT
    status: RuleStatus = RuleStatus.PENDING
    reason: str = ""
    source_span: SourceSpan
    conflicts_with: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    ai_assisted: bool = False
