"""Check that the original file was not modified."""

from pathlib import Path

from brand_compliance.core.hashing import sha256_file
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import Change
from brand_compliance.models.report import CheckResult
from brand_compliance.models.rule import Rule


class OriginalIntactVerifier:
    """Compares the source file's fingerprint now with the one taken at the start.

    Created per run, because it needs the file path and the starting fingerprint.
    """

    name = "original-intact"

    def __init__(self, path: Path, expected_sha256: str) -> None:
        self._path = path
        self._expected = expected_sha256

    def check(
        self,
        original: ArtifactModel,  # noqa: ARG002
        output: ArtifactModel,  # noqa: ARG002
        rules: list[Rule],  # noqa: ARG002
        changes: list[Change],  # noqa: ARG002
    ) -> CheckResult:
        """Pass only if the file on disk still has its starting fingerprint."""
        current = sha256_file(self._path)
        passed = current == self._expected
        detail = (
            f"source unchanged (sha256 {current[:12]}...)"
            if passed
            else f"source CHANGED: {self._expected[:12]}... -> {current[:12]}..."
        )
        return CheckResult(name=self.name, passed=passed, details=[detail])
