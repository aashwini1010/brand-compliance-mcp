"""Check that running the tool on its own output changes nothing."""

from collections.abc import Callable

from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import Change
from brand_compliance.models.report import CheckResult
from brand_compliance.models.rule import Rule
from brand_compliance.plugins.artifacts.base import serialize_html


class IdempotenceVerifier:
    """Feeds the output back through the pipeline and compares the result.

    Created per run: ``rerun`` takes HTML text and returns the branded HTML text.
    """

    name = "idempotence"

    def __init__(self, rerun: Callable[[str], str]) -> None:
        self._rerun = rerun

    def check(
        self,
        original: ArtifactModel,  # noqa: ARG002
        output: ArtifactModel,
        rules: list[Rule],  # noqa: ARG002
        changes: list[Change],  # noqa: ARG002
    ) -> CheckResult:
        """Pass only if a second run reproduces the first output exactly."""
        first = serialize_html(output.tree, output.doctype)
        second = self._rerun(first)
        if first == second:
            return CheckResult(
                name=self.name,
                passed=True,
                details=["a second run gives identical output"],
            )
        position = next(
            (i for i, (a, b) in enumerate(zip(first, second, strict=False)) if a != b),
            min(len(first), len(second)),
        )
        return CheckResult(
            name=self.name,
            passed=False,
            details=[f"second run differs at character {position}"],
        )
