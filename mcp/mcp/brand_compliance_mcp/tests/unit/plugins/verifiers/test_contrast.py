"""Tests for the contrast and forbidden-colour verifiers."""

from brand_compliance.core.contracts import Verifier
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import Change
from brand_compliance.models.rule import Rule, RuleStatus, Scope
from brand_compliance.models.source import SourceSpan
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler
from brand_compliance.plugins.verifiers.contrast import ContrastVerifier
from brand_compliance.plugins.verifiers.forbidden import ForbiddenColorVerifier

PAGE = """<!doctype html><html><head><style>
body{background:#ffffff;color:#111111}
.card{background:#222222;color:#eeeeee}
.eyebrow{color:#2446a8}
.weak{color:#dddddd}
.grad{background:linear-gradient(red,blue)}
</style></head><body>
<p class="eyebrow">LABEL</p>
<div class="card"><p>inside card</p></div>
<p class="weak">already weak</p>
<div class="grad"><p>on gradient</p></div>
<ul><li>item</li></ul>
</body></html>"""


def _artifact(text: str = PAGE) -> ArtifactModel:
    return StaticArtifactHandler().parse(text, "p.html")


def _change(
    change_id: str, location: str, prop: str, after: str, **kw: object
) -> Change:
    return Change(
        id=change_id, rule_id="R1", location=location, property=prop, after=after, **kw
    )  # type: ignore[arg-type]


def _check(changes: list[Change], rules: list[Rule] | None = None, text: str = PAGE):  # type: ignore[no-untyped-def]
    artifact = _artifact(text)
    return ContrastVerifier().check(artifact, artifact, rules or [], changes)


def test_verifier_implements_the_contract() -> None:
    assert isinstance(ContrastVerifier(), Verifier)
    assert isinstance(ForbiddenColorVerifier(), Verifier)


def test_readable_changes_pass() -> None:
    result = _check([_change("C1", "/html/body/p[1]", "color", "#194247")])
    assert result.passed
    assert result.failed_change_ids == []


def test_unreadable_text_colour_is_blamed_with_a_reason() -> None:
    result = _check([_change("C1", "/html/body/p[1]", "color", "#09a78d")])
    assert not result.passed
    assert result.failed_change_ids == ["C1"]
    assert "2.9" in result.change_reasons["C1"] or "3.0" in result.change_reasons["C1"]
    assert "#09a78d on #ffffff" in result.change_reasons["C1"]


def test_background_is_blamed_when_the_text_colour_is_the_pages_own() -> None:
    result = _check([_change("C1", "/html/body/div[1]", "background", "#eeeeee")])
    assert result.failed_change_ids == ["C1"]


def test_text_colour_is_undone_before_the_background() -> None:
    changes = [
        _change("TEXT", "/html/body/p[1]", "color", "#cccccc"),
        _change("BG", "/html/body", "background", "#ffffff"),
    ]
    assert _check(changes).failed_change_ids == ["TEXT"]


def test_both_changes_are_blamed_when_neither_alone_fixes_it() -> None:
    changes = [
        _change("TEXT", "/html/body/p[2]", "color", "#cccccc"),
        _change("BG", "/html/body/p[2]", "background", "#bbbbbb"),
    ]
    assert _check(changes).failed_change_ids == ["BG", "TEXT"]


def test_only_the_background_is_blamed_when_undoing_it_alone_fixes_the_text() -> None:
    changes = [
        _change("TEXT", "/html/body/p[1]", "color", "#222222"),
        _change("BG", "/html/body/p[1]", "background", "#111111"),
    ]
    assert _check(changes).failed_change_ids == ["BG"]


def test_a_failure_the_page_already_had_is_not_blamed_on_a_change() -> None:
    result = _check([_change("C1", "/html/body/p[1]", "font-size", "2rem")])
    assert result.passed
    assert any(
        "4 already failed" in d or "1 already failed" in d for d in result.details
    )


def test_a_change_that_makes_an_existing_failure_worse_is_blamed() -> None:
    result = _check([_change("C1", "/html/body/p[2]", "color", "#eeeeee")])
    assert result.failed_change_ids == ["C1"]


def test_a_change_that_improves_an_existing_failure_is_not_blamed() -> None:
    result = _check([_change("C1", "/html/body/p[2]", "color", "#aaaaaa")])
    assert result.passed


def test_text_on_a_gradient_cannot_be_checked_and_is_counted() -> None:
    result = _check([_change("C1", "/html/body/div[2]/p", "color", "#ffffff")])
    assert result.passed
    assert any("1 could not be checked" in d for d in result.details)


def test_colour_set_on_an_ancestor_reaches_its_descendants() -> None:
    result = _check([_change("C1", "/html/body/ul", "color", "#f5f5f5")])
    assert result.failed_change_ids == ["C1"]


def test_background_shorthand_overrides_a_declared_background_color() -> None:
    text = (
        "<html><head><style>div{background-color:#000;color:#fff}</style></head>"
        "<body><div><p>x</p></div></body></html>"
    )
    result = _check(
        [_change("C1", "/html/body/div", "background", "#111111")], text=text
    )
    assert result.passed
    ok = _check([_change("C1", "/html/body/div", "background", "#ffffff")], text=text)
    assert ok.failed_change_ids == ["C1"]


def test_semi_transparent_background_is_blended_with_what_is_underneath() -> None:
    text = (
        "<html><body style='background:#ffffff'>"
        "<div style='background:rgba(0,0,0,0.9)'>"
        "<p style='color:#000000'>x</p></div></body></html>"
    )
    result = _check([_change("C1", "/html/body/div/p", "color", "#222222")], text=text)
    assert result.failed_change_ids == ["C1"]


def test_minimum_comes_from_the_guides_contrast_rule() -> None:
    rule = Rule(
        id="R9",
        category="min_contrast",
        property="contrast-ratio",
        value="7",
        status=RuleStatus.PENDING,
        source_span=SourceSpan(file="g.md", line_start=1),
    )
    change = _change("C1", "/html/body/p[1]", "color", "#767676")
    assert _check([change]).passed
    assert not _check([change], [rule]).passed


def test_unreadable_minimum_falls_back_to_the_default() -> None:
    rule = Rule(
        id="R9",
        category="min_contrast",
        value="n/a",
        status=RuleStatus.PENDING,
        source_span=SourceSpan(file="g.md", line_start=1),
    )
    assert not _check(
        [_change("C1", "/html/body/p[1]", "color", "#09a78d")], [rule]
    ).passed


def _ban(scope: Scope = Scope.LIGHT) -> Rule:
    return Rule(
        id="R5",
        category="forbid_color",
        target_role="text.body",
        property="color",
        value="#52e081",
        scope=scope,
        status=RuleStatus.PENDING,
        source_span=SourceSpan(file="g.md", line_start=1),
    )


def test_forbidden_colour_on_the_named_role_and_surface_is_blamed() -> None:
    artifact = _artifact()
    change = _change("C1", "/html/body/ul/li", "color", "#52E081", surface="light")
    result = ForbiddenColorVerifier().check(artifact, artifact, [_ban()], [change])
    assert result.failed_change_ids == ["C1"]
    assert "rule R5" in result.change_reasons["C1"]


def test_forbidden_colour_on_another_surface_or_role_is_allowed() -> None:
    artifact = _artifact()
    on_dark = _change("C1", "/html/body/ul/li", "color", "#52e081", surface="dark")
    on_eyebrow = _change("C2", "/html/body/p[1]", "color", "#52e081", surface="light")
    result = ForbiddenColorVerifier().check(
        artifact, artifact, [_ban()], [on_dark, on_eyebrow]
    )
    assert result.passed
