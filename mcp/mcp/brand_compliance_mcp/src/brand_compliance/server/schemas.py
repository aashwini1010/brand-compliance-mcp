"""Shapes returned by the MCP tools (shown to clients as JSON schemas)."""

from typing import Literal

from pydantic import BaseModel, Field

from brand_compliance.models.conflict import Conflict
from brand_compliance.models.report import SCHEMA_VERSION


class RuleView(BaseModel):
    """One rule as a client sees it."""

    id: str
    status: str
    category: str
    role: str | None = None
    property: str | None = None
    value: str | None = None
    scope: str
    severity: str
    guide_line: str
    heading: str
    reason: str = ""
    notes: list[str] = Field(default_factory=list)


class ExtractedRules(BaseModel):
    """How a guide was read, without touching any artifact.

    ``pending`` means the rule was understood; whether it can be applied depends
    on the artifact it is later used with.
    """

    schema_version: str = SCHEMA_VERSION
    guide: str
    counts: dict[str, int]
    total: int
    returned: int
    truncated: bool
    rules: list[RuleView]
    conflicts: list[Conflict]


class PluginList(BaseModel):
    """The plugins this server has loaded, by interface."""

    schema_version: str = SCHEMA_VERSION
    plugins: dict[str, list[str]]


class ReportText(BaseModel):
    """A saved report."""

    schema_version: str = SCHEMA_VERSION
    run_id: str
    format: Literal["markdown", "json"]
    content: str
