"""Outcome of a run: verification results and the final report."""

from enum import StrEnum

from pydantic import BaseModel, Field

from brand_compliance.models.artifact import ArtifactType
from brand_compliance.models.change import Change, Skip
from brand_compliance.models.conflict import Conflict
from brand_compliance.models.rule import Rule

SCHEMA_VERSION = "1.0"


class CheckResult(BaseModel):
    """Result of one verifier."""

    name: str
    passed: bool
    details: list[str] = Field(default_factory=list)
    failed_change_ids: list[str] = Field(default_factory=list)
    change_reasons: dict[str, str] = Field(default_factory=dict)


class RunStatus(StrEnum):
    """How a run ended."""

    COMPLETED = "completed"
    FAILED_VERIFICATION = "failed_verification"


class RunResult(BaseModel):
    """Everything the pipeline knows at the end of a run."""

    run_id: str
    guide_name: str
    artifact_name: str
    artifact_type: ArtifactType
    status: RunStatus = RunStatus.COMPLETED
    started_at: str = ""
    detection_signals: list[str] = Field(default_factory=list)
    classification_ambiguous: bool = False
    source_sha256_before: str
    source_sha256_after: str
    rules: list[Rule] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    changes: list[Change] = Field(default_factory=list)
    skipped: list[Skip] = Field(default_factory=list)
    rolled_back: dict[str, str] = Field(default_factory=dict)
    checks: list[CheckResult] = Field(default_factory=list)
    unmapped_elements: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)


class RunSummary(BaseModel):
    """The short answer returned to a caller (for example an MCP client)."""

    schema_version: str = SCHEMA_VERSION
    run_id: str
    status: RunStatus
    artifact_type: ArtifactType
    output_dir: str
    files: dict[str, str]
    rule_counts: dict[str, int]
    change_count: int
    conflict_count: int
    checks: dict[str, bool]
    message: str


class Report(BaseModel):
    """Machine-readable report written for each run."""

    schema_version: str = SCHEMA_VERSION
    run: RunResult
