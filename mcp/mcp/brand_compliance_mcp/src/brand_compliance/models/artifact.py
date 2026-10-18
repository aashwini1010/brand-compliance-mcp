"""The HTML artifact being restyled (always a copy of the original)."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ArtifactType(StrEnum):
    """Kinds of HTML artifact with different rendering rules."""

    STATIC = "static"
    EMAIL = "email"


class Detection(BaseModel):
    """Result of a handler asking 'is this my kind of artifact?'."""

    artifact_type: ArtifactType
    score: float = Field(ge=0.0, le=1.0)
    signals: list[str] = Field(default_factory=list)


class Classification(BaseModel):
    """Verdict on whether an artifact is a static page or an email.

    ``ambiguous`` means the evidence was close; the safer email strategy is
    chosen then, and the reader is told.
    """

    artifact_type: ArtifactType
    confidence: float = Field(ge=0.0, le=1.0)
    ambiguous: bool = False
    signals: list[str] = Field(default_factory=list)


class ArtifactModel(BaseModel):
    """Parsed artifact: DOM copy, type, detection signals and element roles."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    source_name: str
    source_sha256: str
    artifact_type: ArtifactType
    signals: list[str] = Field(default_factory=list)
    doctype: str | None = None
    tree: Any = Field(default=None, exclude=True, repr=False)
    styles: Any = Field(default=None, exclude=True, repr=False)
    roles: dict[str, str] = Field(default_factory=dict)
    surfaces: dict[str, str] = Field(default_factory=dict)
    unmapped_elements: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
