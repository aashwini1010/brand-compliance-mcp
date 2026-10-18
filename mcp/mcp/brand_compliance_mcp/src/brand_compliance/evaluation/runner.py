"""Run evaluation cases through the real orchestrator and score them."""

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from brand_compliance.core.errors import BrandComplianceError
from brand_compliance.core.hashing import sha256_file
from brand_compliance.core.settings import PathSettings, Settings
from brand_compliance.evaluation import metrics as m
from brand_compliance.evaluation.cases import EvalCase
from brand_compliance.models.report import Report, RunResult, RunStatus, RunSummary
from brand_compliance.pipeline.bootstrap import build_registry
from brand_compliance.pipeline.orchestrator import BRANDED_FILE, Orchestrator
from brand_compliance.rules.vocabulary import Vocabulary, load_vocabulary

logger = logging.getLogger(__name__)

_KEPT_FILES = (BRANDED_FILE, "report.md", "report.json")


@dataclass
class CaseResult:
    """The scored outcome of one case."""

    case: EvalCase
    metrics: list[m.Metric] = field(default_factory=list)
    error_code: str | None = None
    summary: RunSummary | None = None

    @property
    def passed(self) -> bool:
        """True if every metric passed."""
        return all(metric.passed for metric in self.metrics)


class EvalRunner:
    """Runs cases from ``root`` using ``work_dir`` for temporary output."""

    def __init__(
        self, root: Path, work_dir: Path, vocabulary: Vocabulary | None = None
    ) -> None:
        self._root = root.resolve()
        self._work = work_dir.resolve()
        self._vocabulary = vocabulary or load_vocabulary()
        self._work.mkdir(parents=True, exist_ok=True)
        (self._work / "runs").mkdir(exist_ok=True)
        self._settings = Settings(
            paths=PathSettings(
                allowed_input_dirs=[str(self._root), str(self._work)],
                allowed_output_dirs=[str(self._work / "runs")],
            )
        )
        self._orchestrator = Orchestrator(
            build_registry(self._settings, self._vocabulary),
            self._settings,
            self._vocabulary,
        )

    def run_all(
        self, cases: list[EvalCase], reports_dir: Path | None = None
    ) -> list[CaseResult]:
        """Run every case; keep each case's outputs under ``reports_dir/<id>/``."""
        return [self.run_case(case, reports_dir) for case in cases]

    def run_case(self, case: EvalCase, reports_dir: Path | None = None) -> CaseResult:
        """Run one case and score it."""
        guide, artifact = self._root / case.guide, self._root / case.artifact
        before = sha256_file(artifact) if artifact.is_file() else ""
        try:
            summary = self._orchestrator.run(
                guide, artifact, self._work / "runs", case.artifact_type
            )
        except BrandComplianceError as exc:
            return self._refused(case, exc, artifact, before)
        result = CaseResult(case, summary=summary)
        report = self._report(summary)
        expect = case.expect
        result.metrics.append(
            m.Metric(
                "no error expected",
                expect.error_code is None,
                "ran"
                if expect.error_code is None
                else f"expected the error {expect.error_code}, but the run succeeded",
            )
        )
        result.metrics += m.run_outcome(report, expect)
        for optional in (m.rule_status_accuracy(report, expect),):
            if optional:
                result.metrics.append(optional)
        result.metrics += m.change_metrics(report, expect)
        result.metrics += m.conflict_metrics(report, expect)
        result.metrics.append(m.conflicts_never_applied(report))
        result.metrics.append(m.original_untouched(before, sha256_file(artifact)))
        branded = summary.files.get(BRANDED_FILE)
        if branded:
            self._content_metrics(case, artifact, Path(branded), report, guide, result)
        if reports_dir:
            self._keep(case, summary, reports_dir)
        return result

    # ---- helpers -------------------------------------------------------

    @staticmethod
    def _report(summary: RunSummary) -> RunResult:
        text = Path(summary.files["report.json"]).read_text(encoding="utf-8")
        return Report.model_validate_json(text).run

    def _content_metrics(
        self,
        case: EvalCase,
        artifact: Path,
        branded: Path,
        report: RunResult,
        guide: Path,
        result: CaseResult,
    ) -> None:
        original_text = artifact.read_text(encoding="utf-8")
        branded_text = branded.read_text(encoding="utf-8")
        result.metrics += m.content_preserved(original_text, branded_text)
        result.metrics.append(m.report_fidelity(original_text, branded_text, report))
        second_input = self._work / f"{case.id}-second-run.html"
        second_input.write_text(branded_text, encoding="utf-8")
        second = self._orchestrator.run(
            guide, second_input, self._work / "runs", report.artifact_type
        )
        again = Path(second.files[BRANDED_FILE]).read_text(encoding="utf-8")
        result.metrics.append(m.idempotence(branded_text, again))

    def _refused(
        self, case: EvalCase, exc: BrandComplianceError, artifact: Path, before: str
    ) -> CaseResult:
        expected = case.expect.error_code
        result = CaseResult(case, error_code=exc.code)
        result.metrics.append(
            m.Metric(
                "refused with the right error",
                expected == exc.code,
                f"expected {expected}, got {exc.code}: {exc}",
            )
        )
        if artifact.is_file():
            result.metrics.append(m.original_untouched(before, sha256_file(artifact)))
        return result

    def _keep(self, case: EvalCase, summary: RunSummary, reports_dir: Path) -> None:
        target = reports_dir / case.id
        shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True)
        for name in _KEPT_FILES:
            source = summary.files.get(name)
            if source:
                shutil.copy(source, target / name)
        if summary.status is RunStatus.FAILED_VERIFICATION:
            logger.warning("Case %s ended with a failed verification", case.id)
