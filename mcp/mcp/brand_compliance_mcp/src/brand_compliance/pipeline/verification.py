"""Verify a plan and undo what breaks it.

Two phases:
1. *Change-level* verifiers (contrast, forbidden colour) judge the planned edits
   and name the changes to undo. The loop undoes them and checks again until
   nothing fails.
2. *Output-level* verifiers (structure, assets, ...) judge the written output.
   Their failures cannot be fixed by undoing one change, so they are reported.
"""

import logging
from dataclasses import dataclass, field

from brand_compliance.core.contracts import Verifier
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import Change
from brand_compliance.models.report import CheckResult
from brand_compliance.models.rule import Rule
from brand_compliance.pipeline.planning import PlanResult

logger = logging.getLogger(__name__)

MAX_ROUNDS = 6


@dataclass
class VerifiedPlan:
    """The plan after rollbacks, the final check results, and what was undone."""

    plan: PlanResult
    checks: list[CheckResult] = field(default_factory=list)
    rolled_back: dict[str, str] = field(default_factory=dict)


def verify_and_roll_back(
    rules: list[Rule],
    original: ArtifactModel,
    plan: PlanResult,
    verifiers: list[Verifier],
    max_rounds: int = MAX_ROUNDS,
) -> VerifiedPlan:
    """Undo changes the change-level verifiers blame, until the plan passes.

    The verifiers only look at ``original`` and the planned changes, so no
    output has to be written yet.
    """
    undone: dict[str, str] = {}
    current = plan
    results: list[CheckResult] = []
    for round_number in range(1, max_rounds + 1):
        results = [
            verifier.check(original, original, rules, current.changes)
            for verifier in verifiers
        ]
        failures: dict[str, str] = {}
        for result in results:
            for change_id in result.failed_change_ids:
                reason = result.change_reasons.get(change_id, "failed " + result.name)
                failures.setdefault(change_id, f"{reason} [{result.name} check]")
        if not failures:
            break
        logger.info("Round %d: rolling back %d change(s)", round_number, len(failures))
        undone.update(failures)
        current = current.rolled_back(failures)
    else:
        results = [
            verifier.check(original, original, rules, current.changes)
            for verifier in verifiers
        ]
    return VerifiedPlan(plan=current, checks=results, rolled_back=undone)


def verify_output(
    original: ArtifactModel,
    output: ArtifactModel,
    rules: list[Rule],
    changes: list[Change],
    verifiers: list[Verifier],
) -> list[CheckResult]:
    """Run the output-level verifiers on the written artifact."""
    return [verifier.check(original, output, rules, changes) for verifier in verifiers]
