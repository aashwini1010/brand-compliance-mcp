"""Tests for the email support table and how appliers use it."""

from collections.abc import Callable
from pathlib import Path

import pytest

from brand_compliance.core.errors import InvalidInputError
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.rule import Rule, RuleStatus
from brand_compliance.models.source import SourceSpan
from brand_compliance.plugins.appliers.base import same_value
from brand_compliance.plugins.appliers.support import (
    EmailSupport,
    load_email_support,
)
from brand_compliance.plugins.appliers.typography import TypographyApplier
from brand_compliance.plugins.artifacts.email import EmailArtifactHandler
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler

SUPPORT = load_email_support()
PAGE = (
    '<html><body style="background:#ffffff"><h1 style="font-size:30px">Hi</h1>'
    "<p>Body</p></body></html>"
)


def _rule(prop: str, value: str, role: str = "heading.h1") -> Rule:
    return Rule(
        id="R1",
        category="typography",
        target_role=role,
        property=prop,
        value=value,
        status=RuleStatus.PENDING,
        source_span=SourceSpan(file="g.md", line_start=1),
    )


def _email() -> ArtifactModel:
    return EmailArtifactHandler().parse(PAGE, "mail.html")


def test_default_table_loads_with_values_properties_and_partial_support() -> None:
    assert SUPPORT.rem_base_px == 16
    assert any(u.pattern == "clamp(" for u in SUPPORT.unsupported_values)
    assert any(u.property == "backdrop-filter" for u in SUPPORT.unsupported_properties)
    assert any(p.property == "border-radius" for p in SUPPORT.partial_properties)


@pytest.mark.parametrize(
    ("prop", "value", "reason"),
    [
        ("font-size", "clamp(1rem, 2vw, 3rem)", "clamp()"),
        ("color", "var(--ink)", "CSS variables"),
        ("width", "calc(100% - 4px)", "calc()"),
        ("width", "50vw", "Viewport units (vw)"),
        ("backdrop-filter", "blur(4px)", "backdrop-filter"),
        ("gap", "8px", "gap"),
    ],
)
def test_unsupported_values_and_properties_are_rejected_with_a_reason(
    prop: str, value: str, reason: str
) -> None:
    adapted = SUPPORT.adapt(prop, value)
    assert adapted.value is None
    assert reason in (adapted.rejected_because or "")


def test_rem_is_converted_to_px_with_a_note() -> None:
    adapted = SUPPORT.adapt("font-size", "0.9375rem")
    assert adapted.value == "15px"
    assert "rem converted to px" in (adapted.note or "")


def test_a_custom_root_size_is_used_for_the_conversion() -> None:
    assert EmailSupport(rem_base_px=10).adapt("font-size", "2rem").value == "20px"


def test_partially_supported_properties_are_kept_with_a_note() -> None:
    adapted = SUPPORT.adapt("border-radius", "999px")
    assert adapted.value == "999px"
    assert "Outlook desktop ignores border-radius" in (adapted.note or "")


def test_plain_values_pass_through_untouched() -> None:
    adapted = SUPPORT.adapt("line-height", "1.6")
    assert (adapted.value, adapted.rejected_because, adapted.note) == (
        "1.6",
        None,
        None,
    )


def test_bad_support_file_is_rejected(write_file: Callable[[str, str], Path]) -> None:
    with pytest.raises(InvalidInputError):
        load_email_support(
            write_file("e.toml", "[[unsupported_values]]\npattern = 1\n")
        )
    with pytest.raises(InvalidInputError):
        load_email_support(write_file("e2.toml", "not = = toml"))


def test_applier_skips_a_clamp_value_in_an_email_and_says_why() -> None:
    applier = TypographyApplier(email_support=SUPPORT)
    result = applier.plan(_rule("font-size", "clamp(2rem, 4vw, 4rem)"), _email())
    assert result.changes == []
    assert result.skipped[0].reason == "clamp() is not supported by most email clients"
    assert result.skipped[0].location == "/html/body/h1"


def test_applier_converts_rem_for_an_email_and_notes_it() -> None:
    applier = TypographyApplier(email_support=SUPPORT)
    change = applier.plan(_rule("font-size", "2rem"), _email()).changes[0]
    assert (change.before, change.after) == ("30px", "32px")
    assert "rem converted to px" in (change.note or "")
    assert change.important is False


def test_applier_does_not_use_the_table_for_a_static_page() -> None:
    applier = TypographyApplier(email_support=SUPPORT)
    page = StaticArtifactHandler().parse(PAGE, "page.html")
    change = applier.plan(_rule("font-size", "clamp(2rem, 4vw, 4rem)"), page).changes[0]
    assert change.after == "clamp(2rem, 4vw, 4rem)"


def test_applier_without_a_table_leaves_email_values_alone() -> None:
    change = TypographyApplier().plan(_rule("font-size", "2rem"), _email()).changes[0]
    assert change.after == "2rem"


def test_equal_fonts_with_different_quotes_count_as_the_same_value() -> None:
    assert same_value(
        "\"Montserrat\", 'Segoe UI', sans-serif",
        "'Montserrat', \"Segoe UI\", sans-serif",
    )


def test_a_plain_background_colour_is_written_as_background_color_for_emails() -> None:
    adapted = SUPPORT.adapt("background", "#f6f3f0")
    assert adapted.property == "background-color"
    assert adapted.value == "#f6f3f0"
    assert "written as background-color" in (adapted.note or "")


def test_a_background_that_is_not_a_plain_colour_keeps_its_property() -> None:
    adapted = SUPPORT.adapt("background", "linear-gradient(red, blue)")
    assert adapted.property == "background"


def test_applier_reads_and_writes_background_color_in_an_email() -> None:
    from brand_compliance.plugins.appliers.component import ComponentApplier

    mail = EmailArtifactHandler().parse(
        '<html><body style="background-color:#eef1f5"><p>x</p></body></html>', "m.html"
    )
    rule = Rule(
        id="R1",
        category="surface",
        target_role="page.surface",
        property="background",
        value="#f6f3f0",
        status=RuleStatus.PENDING,
        source_span=SourceSpan(file="g.md", line_start=1),
    )
    change = ComponentApplier(email_support=SUPPORT).plan(rule, mail).changes[0]
    assert (change.property, change.before, change.after) == (
        "background-color",
        "#eef1f5",
        "#f6f3f0",
    )
