"""The evaluation case format: a guide, an artifact, and what a person expects.

Each case is one ``expected/<id>.json`` file. Expectations are written by a
person from the guide, never copied from the tool's own output.
"""

import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from brand_compliance.core.errors import InvalidInputError
from brand_compliance.models.artifact import ArtifactType
from brand_compliance.models.report import RunStatus
from brand_compliance.models.rule import Rule, RuleStatus


class RuleSelector(BaseModel):
    """Picks rules by their fields; every field given must match."""

    category: str | None = None
    role: str | None = None
    property: str | None = None
    value: str | None = None
    scope: str | None = None
    guide_line: int | None = None

    def matches(self, rule: Rule) -> bool:
        """True if the rule matches every field this selector sets."""
        checks = (
            (self.category, rule.category),
            (self.role, rule.target_role),
            (self.property, rule.property),
            (self.scope, rule.scope.value),
            (self.guide_line, rule.source_span.line_start),
        )
        if any(want is not None and want != have for want, have in checks):
            return False
        if self.value is not None:
            return (rule.value or "").lower() == self.value.lower()
        return True


class RuleExpectation(BaseModel):
    """Every rule the selector picks must end in this status."""

    selector: RuleSelector
    status: RuleStatus
    why: str = ""


class ChangeExpectation(BaseModel):
    """An edit that should (or may) happen, described by the rule behind it."""

    rule: RuleSelector
    property: str | None = None
    after: str | None = None
    why: str = ""


class ConflictExpectation(BaseModel):
    """A contradiction the guide contains."""

    kind: str
    resolved: bool
    guide_lines: list[int] = Field(default_factory=list)


class Expectations(BaseModel):
    """Everything a person expects from one case."""

    run_status: RunStatus = RunStatus.COMPLETED
    artifact_type: ArtifactType | None = None
    rules: list[RuleExpectation] = Field(default_factory=list)
    changes: list[ChangeExpectation] = Field(default_factory=list)
    allowed_changes: list[ChangeExpectation] = Field(default_factory=list)
    zero_changes: bool = False
    conflicts: list[ConflictExpectation] = Field(default_factory=list)
    exact_conflict_count: int | None = None
    rolled_back_at_least: int = 0
    notes_contain: list[str] = Field(default_factory=list)
    error_code: str | None = None


class EvalCase(BaseModel):
    """One evaluation case."""

    id: str
    description: str
    synthetic: bool = False
    guide: str
    artifact: str
    artifact_type: ArtifactType | None = None
    expect: Expectations


def load_case(path: Path) -> EvalCase:
    """Read and validate one case file."""
    try:
        return EvalCase.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise InvalidInputError(
            f"Cannot read evaluation case {path.name}: {exc}"
        ) from exc


def load_cases(folder: Path) -> list[EvalCase]:
    """Read every ``*.json`` case in a folder, ordered by file name."""
    files = sorted(folder.glob("*.json"))
    if not files:
        raise InvalidInputError(f"No evaluation cases found in {folder}")
    cases = [load_case(path) for path in files]
    ids = [case.id for case in cases]
    if len(set(ids)) != len(ids):
        raise InvalidInputError("Evaluation case ids must be unique")
    return cases
