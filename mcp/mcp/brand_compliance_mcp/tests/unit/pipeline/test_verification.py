"""Tests for the rollback support and the verify-and-roll-back loop."""

from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import Change
from brand_compliance.models.report import CheckResult
from brand_compliance.models.rule import Rule, RuleStatus
from brand_compliance.models.source import SourceSpan
from brand_compliance.pipeline.planning import PlanResult, RuleOutcome, plan_changes
from brand_compliance.pipeline.verification import verify_and_roll_back, verify_output
from brand_compliance.plugins.appliers.typography import TypographyApplier
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler

PAGE = "<html><body><h1>A</h1><p>B</p><p>C</p></body></html>"


def _artifact() -> ArtifactModel:
    return StaticArtifactHandler().parse(PAGE, "p.html")


def _rule(rule_id: str, role: str, value: str) -> Rule:
    return Rule(
        id=rule_id,
        category="typography",
        target_role=role,
        property="font-size",
        value=value,
        status=RuleStatus.PENDING,
        source_span=SourceSpan(file="g.md", line_start=1),
    )


def _plan() -> tuple[list[Rule], PlanResult]:
    rules = [_rule("R1", "heading.h1", "3rem"), _rule("R2", "text.body", "1rem")]
    return rules, plan_changes(rules, _artifact(), [TypographyApplier()])


class _Blames:
    """A stand-in verifier that fails the given change ids once."""

    name = "stub"

    def __init__(self, *ids: str, forever: bool = False) -> None:
        self._ids, self._forever, self.calls = set(ids), forever, 0

    def check(self, original, output, rules, changes) -> CheckResult:  # type: ignore[no-untyped-def]
        self.calls += 1
        bad = (
            sorted(self._ids & {c.id for c in changes})
            if self._forever or self.calls == 1
            else []
        )
        return CheckResult(
            name=self.name,
            passed=not bad,
            failed_change_ids=bad,
            change_reasons={i: f"blamed {i}" for i in bad},
        )


def test_rolled_back_removes_the_change_and_records_why() -> None:
    _, plan = _plan()
    first = plan.changes[0]
    result = plan.rolled_back({first.id: "too faint"})
    assert first.id not in {c.id for c in result.changes}
    skip = next(s for s in result.skipped if s.location == first.location)
    assert skip.reason == "Rolled back: too faint"
    assert skip.rule_id == first.rule_id


def test_rolled_back_keeps_the_original_plan_unchanged() -> None:
    _, plan = _plan()
    plan.rolled_back({plan.changes[0].id: "x"})
    assert len(plan.changes) == 3


def test_rule_with_every_change_undone_becomes_not_applicable() -> None:
    _, plan = _plan()
    h1 = next(c for c in plan.changes if c.rule_id == "R1")
    outcome = plan.rolled_back({h1.id: "faint"}).outcomes["R1"]
    assert outcome.status is RuleStatus.NOT_APPLICABLE
    assert "Rolled back: faint" in outcome.reason


def test_rule_with_some_changes_undone_stays_applied_and_says_so() -> None:
    _, plan = _plan()
    first_body = next(c for c in plan.changes if c.rule_id == "R2")
    outcome = plan.rolled_back({first_body.id: "x"}).outcomes["R2"]
    assert outcome.status is RuleStatus.APPLIED
    assert outcome.reason == "1 change(s) made; 1 rolled back"


def test_loop_without_failures_changes_nothing() -> None:
    rules, plan = _plan()
    result = verify_and_roll_back(rules, _artifact(), plan, [_Blames()])
    assert len(result.plan.changes) == 3
    assert result.rolled_back == {}
    assert result.checks[0].passed


def test_loop_rolls_back_blamed_changes_and_checks_again() -> None:
    rules, plan = _plan()
    blamed = plan.changes[0].id
    stub = _Blames(blamed)
    result = verify_and_roll_back(rules, _artifact(), plan, [stub])
    assert blamed not in {c.id for c in result.plan.changes}
    assert result.rolled_back == {blamed: f"blamed {blamed} [stub check]"}
    assert stub.calls == 2
    assert result.checks[0].passed


def test_loop_stops_after_the_round_limit_when_a_check_never_passes() -> None:
    rules, plan = _plan()
    stub = _Blames("CH001", "CH002", "CH003", forever=True)
    result = verify_and_roll_back(rules, _artifact(), plan, [stub], max_rounds=2)
    assert result.plan.changes == []
    assert result.checks[0].passed or result.checks[0].failed_change_ids == []


def test_loop_combines_failures_from_several_verifiers() -> None:
    rules, plan = _plan()
    first, second = plan.changes[0].id, plan.changes[1].id
    result = verify_and_roll_back(
        rules, _artifact(), plan, [_Blames(first), _Blames(second)]
    )
    assert set(result.rolled_back) == {first, second}


def test_verify_output_runs_every_output_verifier() -> None:
    rules, plan = _plan()
    artifact = _artifact()
    results = verify_output(
        artifact, artifact, rules, plan.changes, [_Blames(), _Blames()]
    )
    assert len(results) == 2


def test_plan_result_and_outcome_types_are_exposed() -> None:
    assert RuleOutcome(RuleStatus.APPLIED, "x").reason == "x"
    assert isinstance(
        Change(id="c", rule_id="r", location="/html", property="p", after="a"), Change
    )
