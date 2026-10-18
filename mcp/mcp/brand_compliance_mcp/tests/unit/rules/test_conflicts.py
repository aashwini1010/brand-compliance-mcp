"""Tests for brand_compliance.rules.conflicts."""

from brand_compliance.models.conflict import ConflictKind
from brand_compliance.models.rule import Rule, RuleStatus, Scope
from brand_compliance.models.source import SourceSpan
from brand_compliance.rules.conflicts import detect_conflicts
from brand_compliance.rules.vocabulary import Vocabulary

VOCAB = Vocabulary(effect_words={"gradient": ["gradient", "gradients"]})


def _rule(rule_id: str, **fields: object) -> Rule:
    base: dict[str, object] = {
        "category": "css_declaration",
        "source_span": SourceSpan(file="g.md", line_start=int(rule_id[1:])),
        "status": RuleStatus.PENDING,
    }
    return Rule(id=rule_id, **{**base, **fields})  # type: ignore[arg-type]


def _status(rules: list[Rule], rule_id: str) -> RuleStatus:
    return next(r.status for r in rules if r.id == rule_id)


def test_detect_conflicts_returns_nothing_for_consistent_rules() -> None:
    rules = [
        _rule("R001", target_role="button", property="color", value="#fff"),
        _rule("R002", target_role="button", property="background", value="#000"),
    ]
    updated, conflicts = detect_conflicts(rules, VOCAB)
    assert conflicts == []
    assert updated == rules


def test_forbidden_effect_conflicts_with_a_style_that_uses_it() -> None:
    rules = [
        _rule("R001", category="forbid_effect", property="effect", value="gradient"),
        _rule(
            "R002",
            target_role="card",
            property="background",
            value="linear-gradient(90deg, #fff, #000)",
        ),
        _rule("R003", target_role="card", property="border", value="1px solid #000"),
    ]
    updated, conflicts = detect_conflicts(rules, VOCAB)
    assert [c.kind for c in conflicts] == [ConflictKind.FORBIDDEN_EFFECT]
    assert conflicts[0].rule_ids == ["R001", "R002"]
    assert _status(updated, "R001") is RuleStatus.CONFLICT_UNRESOLVED
    assert _status(updated, "R002") is RuleStatus.CONFLICT_UNRESOLVED
    assert _status(updated, "R003") is RuleStatus.PENDING


def test_conflict_sets_reason_and_links_the_other_rules() -> None:
    rules = [
        _rule("R001", category="forbid_effect", property="effect", value="gradient"),
        _rule("R002", property="background", value="linear-gradient(#fff, #000)"),
    ]
    updated, _ = detect_conflicts(rules, VOCAB)
    first = next(r for r in updated if r.id == "R001")
    assert first.conflicts_with == ["R002"]
    assert first.reason.startswith("C001:")


def test_unapplied_participant_is_listed_but_keeps_its_status() -> None:
    rules = [
        _rule("R001", category="forbid_effect", property="effect", value="gradient"),
        _rule(
            "R002",
            property="background",
            value="linear-gradient(#fff, #000)",
            status=RuleStatus.UNINTERPRETABLE,
            reason="no selector",
        ),
    ]
    updated, conflicts = detect_conflicts(rules, VOCAB)
    assert conflicts[0].rule_ids == ["R001", "R002"]
    kept = next(r for r in updated if r.id == "R002")
    assert kept.status is RuleStatus.UNINTERPRETABLE
    assert kept.reason == "no selector"
    assert kept.conflicts_with == ["R001"]


def test_prose_rules_are_never_treated_as_styles() -> None:
    rules = [
        _rule("R001", category="forbid_effect", property="effect", value="gradient"),
        _rule("R002", category="unmatched", value="photo gradient overlay"),
    ]
    assert detect_conflicts(rules, VOCAB)[1] == []


def test_effect_without_known_words_is_ignored() -> None:
    rules = [
        _rule("R001", category="forbid_effect", property="effect", value="glow"),
        _rule("R002", property="box-shadow", value="0 0 4px glow"),
    ]
    assert detect_conflicts(rules, VOCAB)[1] == []


def _font_rules(*extra: Rule) -> list[Rule]:
    only = _rule(
        "R001", category="font_only", property="font-family", value="Montserrat"
    )
    stack = _rule(
        "R002",
        category="font_family",
        property="font-family",
        value='"Montserrat", -apple-system, sans-serif',
    )
    return [only, stack, *extra]


def test_font_stack_with_allowed_first_family_is_not_a_conflict() -> None:
    assert detect_conflicts(_font_rules(), VOCAB)[1] == []


def test_other_font_family_conflicts_with_font_only() -> None:
    other = _rule("R003", property="font-family", value="'Caveat', cursive")
    updated, conflicts = detect_conflicts(_font_rules(other), VOCAB)
    assert conflicts[0].kind is ConflictKind.FONT_RESTRICTION
    assert not conflicts[0].resolved
    assert _status(updated, "R003") is RuleStatus.CONFLICT_UNRESOLVED
    assert _status(updated, "R001") is RuleStatus.CONFLICT_UNRESOLVED


def test_font_conflict_is_resolved_only_by_an_explicit_guide_exception() -> None:
    other = _rule("R003", property="font-family", value="'Caveat', cursive")
    exception = _rule(
        "R004",
        category="font_exception",
        property="font-family",
        value="Caveat",
        notes=["The guide limits it to: developer docs"],
    )
    updated, conflicts = detect_conflicts(_font_rules(other, exception), VOCAB)
    assert conflicts[0].resolved
    assert "g.md:4" in conflicts[0].resolution
    assert _status(updated, "R001") is RuleStatus.PENDING
    assert _status(updated, "R003") is RuleStatus.PENDING
    assert any(
        "(resolved)" in n for n in next(r for r in updated if r.id == "R003").notes
    )


def test_exception_for_a_different_font_does_not_resolve() -> None:
    other = _rule("R003", property="font-family", value="Comic Sans")
    exception = _rule(
        "R004", category="font_exception", property="font-family", value="Caveat"
    )
    assert not detect_conflicts(_font_rules(other, exception), VOCAB)[1][0].resolved


def test_value_clash_for_same_role_property_and_scope() -> None:
    rules = [
        _rule("R001", target_role="focus", property="outline-offset", value="2px"),
        _rule("R002", target_role="focus", property="outline-offset", value="4px"),
    ]
    updated, conflicts = detect_conflicts(rules, VOCAB)
    assert conflicts[0].kind is ConflictKind.VALUE_CLASH
    assert "['2px', '4px']" in conflicts[0].description
    assert {_status(updated, "R001"), _status(updated, "R002")} == {
        RuleStatus.CONFLICT_UNRESOLVED
    }


def test_same_value_written_differently_is_not_a_clash() -> None:
    rules = [
        _rule("R001", target_role="b", property="padding", value="12px  28px"),
        _rule("R002", target_role="b", property="padding", value="12px 28PX"),
    ]
    assert detect_conflicts(rules, VOCAB)[1] == []


def test_different_scopes_do_not_clash_but_all_overlaps_with_any() -> None:
    light = _rule(
        "R001", target_role="b", property="color", value="#111", scope=Scope.LIGHT
    )
    dark = _rule(
        "R002", target_role="b", property="color", value="#eee", scope=Scope.DARK
    )
    anywhere = _rule("R003", target_role="b", property="color", value="#999")
    assert detect_conflicts([light, dark], VOCAB)[1] == []
    assert len(detect_conflicts([light, anywhere], VOCAB)[1]) == 1


def test_non_pending_rules_do_not_form_value_clashes() -> None:
    rules = [
        _rule("R001", target_role="b", property="color", value="#111"),
        _rule(
            "R002",
            target_role="b",
            property="color",
            value="#222",
            status=RuleStatus.UNINTERPRETABLE,
        ),
    ]
    assert detect_conflicts(rules, VOCAB)[1] == []


def test_detect_conflicts_does_not_modify_its_input() -> None:
    rules = [
        _rule("R001", target_role="f", property="x", value="1"),
        _rule("R002", target_role="f", property="x", value="2"),
    ]
    detect_conflicts(rules, VOCAB)
    assert all(r.status is RuleStatus.PENDING for r in rules)
    assert all(r.conflicts_with == [] for r in rules)


def test_conflict_ids_are_sequential() -> None:
    rules = [
        _rule("R001", target_role="a", property="x", value="1"),
        _rule("R002", target_role="a", property="x", value="2"),
        _rule("R003", target_role="b", property="y", value="1"),
        _rule("R004", target_role="b", property="y", value="2"),
    ]
    assert [c.id for c in detect_conflicts(rules, VOCAB)[1]] == ["C001", "C002"]


def test_rules_without_a_target_role_are_not_compared() -> None:
    rules = [
        _rule("R001", property="font-family", value="Montserrat"),
        _rule("R002", property="font-family", value="Caveat"),
    ]
    assert detect_conflicts(rules, VOCAB)[1] == []


def test_named_tokens_with_different_values_do_clash() -> None:
    rules = [
        _rule("R001", category="color_token", property="--tide", value="#09a78d"),
        _rule("R002", category="color_token", property="--tide", value="#09a78e"),
    ]
    conflicts = detect_conflicts(rules, VOCAB)[1]
    assert "token --tide" in conflicts[0].description
