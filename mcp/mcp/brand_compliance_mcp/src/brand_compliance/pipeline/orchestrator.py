"""Run one guide + one artifact through every stage and write the results.

The orchestrator only coordinates: it knows the order of the stages and finds
every plugin through the registry, never by format name.
"""

import logging
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from brand_compliance.core.contracts import (
    ArtifactHandler,
    Reporter,
    RuleApplier,
    RuleExtractor,
    SourceAdapter,
    StyleWriter,
    Verifier,
)
from brand_compliance.core.errors import (
    InvalidInputError,
    ParseFailedError,
    UnsupportedFormatError,
)
from brand_compliance.core.hashing import sha256_file
from brand_compliance.core.paths import (
    resolve_within,
    validate_input_file,
    validate_output_dir,
)
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.core.settings import Settings
from brand_compliance.models.artifact import ArtifactModel, ArtifactType, Classification
from brand_compliance.models.report import CheckResult, RunResult, RunStatus, RunSummary
from brand_compliance.models.rule import RuleStatus
from brand_compliance.pipeline.finalize import finalize_rules
from brand_compliance.pipeline.planning import PlanResult, plan_changes
from brand_compliance.pipeline.verification import (
    VerifiedPlan,
    verify_and_roll_back,
    verify_output,
)
from brand_compliance.plugins.artifacts.base import serialize_html
from brand_compliance.plugins.artifacts.classifier import classify_text
from brand_compliance.plugins.verifiers.idempotence import IdempotenceVerifier
from brand_compliance.plugins.verifiers.original import OriginalIntactVerifier
from brand_compliance.rules.interpret import GuideInterpretation, interpret_guide
from brand_compliance.rules.vocabulary import Vocabulary

logger = logging.getLogger(__name__)

BRANDED_FILE: Final = "branded.html"
RUN_ID_PATTERN: Final = re.compile(r"^run-\d{8}-\d{6}-[0-9a-f]{6}$")
_REPORT_FILES: Final = {"markdown": "report.md", "json": "report.json"}
_RUN_SEARCH_DEPTH: Final = 3
_ARTIFACT_SUFFIXES: Final = (".html", ".htm")


@dataclass
class _Transformed:
    """The result of applying a set of rules to one piece of HTML."""

    output: ArtifactModel
    pristine: ArtifactModel
    plan: PlanResult
    verified: VerifiedPlan


class Orchestrator:
    """Runs the whole workflow for one guide and one artifact."""

    def __init__(
        self,
        registry: PluginRegistry,
        settings: Settings,
        vocabulary: Vocabulary,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._registry = registry
        self._settings = settings
        self._vocabulary = vocabulary
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex[:6])

    # ---- public --------------------------------------------------------

    def run(
        self,
        guide_path: str | Path,
        artifact_path: str | Path,
        output_root: str | Path,
        artifact_type: ArtifactType | None = None,
    ) -> RunSummary:
        """Brand one artifact with one guide; return a short summary."""
        started = self._clock()
        run_id = f"run-{started:%Y%m%d-%H%M%S}-{self._id_factory()}"
        guide, artifact = self._validate_inputs(guide_path, artifact_path)
        run_dir = self._prepare_output(output_root, run_id, guide, artifact)
        before = sha256_file(artifact)
        text = _read_text(artifact)
        logger.info("Run %s started", run_id)

        interpretation = self._interpret(guide)
        classification, chosen, notes = self._classify(text, artifact_type)
        handler = self._find_handler(chosen)
        transformed = self._transform(
            text, artifact.name, interpretation, handler, chosen
        )
        checks = self._final_checks(
            transformed, interpretation, artifact, before, handler, chosen
        )
        failed = [c for c in checks if not c.passed]
        status = RunStatus.FAILED_VERIFICATION if failed else RunStatus.COMPLETED
        result = self._result(
            run_id,
            started,
            guide,
            artifact,
            chosen,
            classification,
            status,
            interpretation,
            transformed,
            checks,
            notes,
            before,
            sha256_file(artifact),
        )
        files = self._write_outputs(result, transformed, run_dir, status)
        return self._summary(result, run_dir, files)

    def extract_rules(self, guide_path: str | Path) -> tuple[str, GuideInterpretation]:
        """Read a guide on its own and return its name and interpretation."""
        guide = self._resolve_guide(guide_path)
        return guide.name, self._interpret(guide)

    def classify_file(self, artifact_path: str | Path) -> Classification:
        """Classify an artifact file as a static page or an email."""
        artifact = self._resolve_artifact(artifact_path)
        return classify_text(_read_text(artifact))

    def read_report(self, run_id: str, report_format: str = "markdown") -> str:
        """Return the saved report of an earlier run."""
        if not RUN_ID_PATTERN.match(run_id):
            raise InvalidInputError("run_id must look like run-YYYYMMDD-HHMMSS-xxxxxx")
        filename = _REPORT_FILES.get(report_format)
        if filename is None:
            raise InvalidInputError(f"format must be one of {sorted(_REPORT_FILES)}")
        run_dir = self._find_run(run_id)
        return (run_dir / filename).read_text(encoding="utf-8")

    # ---- stages --------------------------------------------------------

    def _resolve_guide(self, guide_path: str | Path) -> Path:
        guide = resolve_within(guide_path, self._settings.paths.allowed_input_dirs)
        if not guide.is_file():
            raise InvalidInputError(f"Guide is not a file: {guide.name}")
        return guide

    def _resolve_artifact(self, artifact_path: str | Path) -> Path:
        return validate_input_file(
            artifact_path,
            self._settings.paths.allowed_input_dirs,
            self._settings.limits.max_artifact_bytes,
            _ARTIFACT_SUFFIXES,
        )

    def _validate_inputs(
        self, guide_path: str | Path, artifact_path: str | Path
    ) -> tuple[Path, Path]:
        return self._resolve_guide(guide_path), self._resolve_artifact(artifact_path)

    def _find_run(self, run_id: str) -> Path:
        """Find a run folder under the allowed output folders (a few levels deep)."""
        for root in self._settings.paths.allowed_output_dirs:
            base = Path(root).expanduser().resolve()
            if not base.is_dir():
                continue
            for depth in range(_RUN_SEARCH_DEPTH):
                pattern = "/".join(["*"] * depth + [run_id])
                for candidate in sorted(base.glob(pattern)):
                    if candidate.is_dir():
                        return resolve_within(candidate, [base])
        raise InvalidInputError(f"No saved run {run_id}")

    def _prepare_output(
        self, output_root: str | Path, run_id: str, guide: Path, artifact: Path
    ) -> Path:
        root = validate_output_dir(
            output_root, self._settings.paths.allowed_output_dirs, [guide, artifact]
        )
        run_dir = root / run_id
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise InvalidInputError(f"Run folder {run_id} already exists") from exc
        return run_dir

    def _interpret(self, guide: Path) -> GuideInterpretation:
        adapter = self._registry.find(SourceAdapter, lambda a: a.can_handle(guide))
        document = adapter.load(guide)
        return interpret_guide(
            document, self._registry.plugins(RuleExtractor), self._vocabulary
        )

    @staticmethod
    def _classify(
        text: str, forced: ArtifactType | None
    ) -> tuple[Classification, ArtifactType, list[str]]:
        classification = classify_text(text)
        notes: list[str] = []
        if forced is not None:
            notes.append(f"The artifact type was set by the caller: {forced.value}")
            return classification, forced, notes
        if classification.ambiguous:
            notes.append(
                "The artifact type could not be determined with confidence; the "
                "safer email handling was chosen. Pass the type explicitly to override."
            )
        return classification, classification.artifact_type, notes

    def _find_handler(self, artifact_type: ArtifactType) -> ArtifactHandler:
        try:
            return self._registry.find(
                ArtifactHandler, lambda h: h.artifact_type is artifact_type
            )
        except UnsupportedFormatError as exc:
            raise UnsupportedFormatError(
                f"{artifact_type.value} artifacts are not supported yet"
                + (
                    " (pass artifact_type='static' to treat it as a web page)"
                    if artifact_type is ArtifactType.EMAIL
                    else ""
                )
            ) from exc

    def _verifiers(self, scope: str) -> list[Verifier]:
        """Every registered verifier of a scope: ``changes`` or ``output`` (default)."""
        return [
            v
            for v in self._registry.plugins(Verifier)
            if getattr(v, "scope", "output") == scope
        ]

    def _find_writer(self, artifact_type: ArtifactType) -> StyleWriter:
        try:
            return self._registry.find(
                StyleWriter, lambda w: w.artifact_type is artifact_type
            )
        except UnsupportedFormatError as exc:
            raise UnsupportedFormatError(
                f"No style writer is available for {artifact_type.value} artifacts"
            ) from exc

    def _transform(
        self,
        text: str,
        name: str,
        interpretation: GuideInterpretation,
        handler: ArtifactHandler,
        artifact_type: ArtifactType,
    ) -> _Transformed:
        """Plan, verify and write, on two parses so the original stays pristine."""
        pristine = handler.parse(text, name)
        working = handler.parse(text, name)
        rules = interpretation.rules
        plan = plan_changes(rules, working, self._registry.plugins(RuleApplier))
        verified = verify_and_roll_back(
            rules, pristine, plan, self._verifiers("changes")
        )
        writer = self._find_writer(artifact_type)
        output = writer.write(verified.plan.changes, working)
        return _Transformed(output, pristine, plan, verified)

    def _final_checks(
        self,
        transformed: _Transformed,
        interpretation: GuideInterpretation,
        artifact: Path,
        before: str,
        handler: ArtifactHandler,
        artifact_type: ArtifactType,
    ) -> list[CheckResult]:
        """Change-level results plus output-level, original and idempotence checks."""
        rules, changes = interpretation.rules, transformed.verified.plan.changes
        checks = list(transformed.verified.checks)
        checks += verify_output(
            transformed.pristine,
            transformed.output,
            rules,
            changes,
            self._verifiers("output"),
        )

        def rerun(branded: str) -> str:
            again = self._transform(
                branded, artifact.name, interpretation, handler, artifact_type
            )
            return serialize_html(again.output.tree, again.output.doctype)

        for per_run in (
            OriginalIntactVerifier(artifact, before),
            IdempotenceVerifier(rerun),
        ):
            checks.append(
                per_run.check(transformed.pristine, transformed.output, rules, changes)
            )
        return checks

    def _result(
        self,
        run_id: str,
        started: datetime,
        guide: Path,
        artifact: Path,
        artifact_type: ArtifactType,
        classification: Classification,
        status: RunStatus,
        interpretation: GuideInterpretation,
        transformed: _Transformed,
        checks: list[CheckResult],
        notes: list[str],
        before: str,
        after: str,
    ) -> RunResult:
        verified = transformed.verified
        rules = finalize_rules(interpretation.rules, verified.plan, checks)
        return RunResult(
            run_id=run_id,
            guide_name=guide.name,
            artifact_name=artifact.name,
            artifact_type=artifact_type,
            status=status,
            started_at=started.isoformat(timespec="seconds"),
            detection_signals=classification.signals,
            classification_ambiguous=classification.ambiguous,
            source_sha256_before=before,
            source_sha256_after=after,
            rules=rules,
            conflicts=interpretation.conflicts,
            changes=verified.plan.changes,
            skipped=verified.plan.skipped,
            rolled_back=verified.rolled_back,
            checks=checks,
            unmapped_elements=transformed.output.unmapped_elements,
            notes=[*notes, *transformed.output.notes],
        )

    def _write_outputs(
        self,
        result: RunResult,
        transformed: _Transformed,
        run_dir: Path,
        status: RunStatus,
    ) -> dict[str, Path]:
        reporters = self._registry.plugins(Reporter)
        names = [r.filename for r in reporters]
        if status is RunStatus.COMPLETED:
            names.append(BRANDED_FILE)
        result.outputs = sorted(
            names
        )  # known before writing, so the report lists itself
        files: dict[str, Path] = {}
        if status is RunStatus.COMPLETED:
            branded = run_dir / BRANDED_FILE
            branded.write_text(
                serialize_html(transformed.output.tree, transformed.output.doctype),
                encoding="utf-8",
            )
            files[BRANDED_FILE] = branded
        for reporter in reporters:
            path = reporter.render(result, run_dir)
            files[path.name] = path
        return files

    @staticmethod
    def _summary(
        result: RunResult, run_dir: Path, files: dict[str, Path]
    ) -> RunSummary:
        counts = {s.value: 0 for s in RuleStatus if s is not RuleStatus.PENDING}
        for rule in result.rules:
            counts[rule.status.value] += 1
        ok = result.status is RunStatus.COMPLETED
        message = (
            f"Branded {result.artifact_name}: {counts['applied']} rule(s) applied, "
            f"{len(result.changes)} change(s)."
            if ok
            else "Verification failed; the branded file was withheld. See report.md."
        )
        return RunSummary(
            run_id=result.run_id,
            status=result.status,
            artifact_type=result.artifact_type,
            output_dir=str(run_dir),
            files={name: str(path) for name, path in files.items()},
            rule_counts=counts,
            change_count=len(result.changes),
            conflict_count=sum(1 for c in result.conflicts if not c.resolved),
            checks={c.name: c.passed for c in result.checks},
            message=message,
        )


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ParseFailedError(f"{path.name} is not valid UTF-8 text") from exc
