"""Plugin interfaces. Every plugin implements exactly one of these."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from brand_compliance.models.artifact import ArtifactModel, ArtifactType, Detection
from brand_compliance.models.change import ApplyResult, Change
from brand_compliance.models.guide import GuideDocument
from brand_compliance.models.report import CheckResult, RunResult
from brand_compliance.models.rule import Rule, RuleCandidate


@runtime_checkable
class SourceAdapter(Protocol):
    """Reads one guide format into the common ``GuideDocument`` tree."""

    name: str

    def can_handle(self, source: Path) -> bool:
        """Return True if this adapter can read the given source."""
        ...

    def load(self, source: Path) -> GuideDocument:
        """Read the source and return the format-neutral tree."""
        ...


@runtime_checkable
class RuleExtractor(Protocol):
    """Finds one kind of rule in a ``GuideDocument``."""

    name: str

    def extract(self, document: GuideDocument) -> list[RuleCandidate]:
        """Return rule candidates found in the document."""
        ...


@runtime_checkable
class ArtifactHandler(Protocol):
    """Detects and parses one kind of HTML artifact."""

    name: str
    artifact_type: ArtifactType

    def detect(self, html: str) -> Detection:
        """Score how likely the HTML is this handler's artifact type."""
        ...

    def parse(self, html: str, source_name: str) -> ArtifactModel:
        """Parse the HTML into an ``ArtifactModel`` (a copy to edit)."""
        ...


@runtime_checkable
class RuleApplier(Protocol):
    """Decides WHAT to change for one category of rule."""

    name: str
    categories: frozenset[str]

    def plan(self, rule: Rule, artifact: ArtifactModel) -> ApplyResult:
        """Return the changes for a rule and any places it had to skip."""
        ...


@runtime_checkable
class StyleWriter(Protocol):
    """Decides HOW changes are written for one artifact type."""

    name: str
    artifact_type: ArtifactType

    def write(self, changes: list[Change], artifact: ArtifactModel) -> ArtifactModel:
        """Write the changes into the artifact copy and return it."""
        ...


@runtime_checkable
class Verifier(Protocol):
    """Runs one check on the original versus the output."""

    name: str

    def check(
        self,
        original: ArtifactModel,
        output: ArtifactModel,
        rules: list[Rule],
        changes: list[Change],
    ) -> CheckResult:
        """Return pass or fail, naming any change that caused a failure."""
        ...


@runtime_checkable
class Reporter(Protocol):
    """Renders a run result into one report format."""

    name: str
    format: str
    filename: str

    def render(self, result: RunResult, output_dir: Path) -> Path:
        """Write the report into ``output_dir`` and return its path."""
        ...
