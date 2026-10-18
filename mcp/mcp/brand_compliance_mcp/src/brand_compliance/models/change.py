"""Edits made to an artifact, and the places where a rule was skipped."""

from typing import Final

from pydantic import BaseModel, Field

ROLLED_BACK_PREFIX: Final = "Rolled back: "


class Change(BaseModel):
    """One edit: where, before, after, and which rule drove it.

    ``surface`` is set when the rule only applies on a light or dark surface.
    ``important`` is set when an inline style on the element had to be overridden.
    """

    id: str
    rule_id: str
    location: str
    property: str
    before: str | None = None
    after: str
    surface: str | None = None
    important: bool = False
    note: str | None = None


class Skip(BaseModel):
    """A place where a rule was understood but could not be applied, and why."""

    rule_id: str
    reason: str = Field(min_length=1)
    location: str | None = None


class ApplyResult(BaseModel):
    """What an applier decided for one rule: changes made and places skipped."""

    changes: list[Change] = Field(default_factory=list)
    skipped: list[Skip] = Field(default_factory=list)
    satisfied: int = Field(default=0, ge=0)  # elements that already match the rule
