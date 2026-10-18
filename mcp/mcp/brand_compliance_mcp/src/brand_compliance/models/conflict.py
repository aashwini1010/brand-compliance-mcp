"""Contradictions found between rules of one guide."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ConflictKind(StrEnum):
    """What kind of contradiction it is."""

    VALUE_CLASH = "value_clash"
    FORBIDDEN_EFFECT = "forbidden_effect"
    FONT_RESTRICTION = "font_restriction"


class Conflict(BaseModel):
    """Two or more rules that contradict each other.

    ``resolved`` is True only when the guide itself states the exception;
    ``resolution`` then says where.
    """

    id: str
    kind: ConflictKind
    rule_ids: list[str] = Field(min_length=2)
    description: str
    resolved: bool = False
    resolution: str = ""
