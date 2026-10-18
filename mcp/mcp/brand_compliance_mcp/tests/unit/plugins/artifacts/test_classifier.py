"""Tests for brand_compliance.plugins.artifacts.classifier."""

from brand_compliance.models.artifact import ArtifactType
from brand_compliance.plugins.artifacts.base import parse_artifact_html
from brand_compliance.plugins.artifacts.classifier import classify_html

EMAIL = """<html xmlns:v="urn:schemas-microsoft-com:vml"><head>
<meta name="x-apple-disable-message-reformatting">
<!--[if mso]><style>td{mso-line-height-rule:exactly}</style><![endif]--></head>
<body><table role="presentation" cellpadding="0" bgcolor="#fff"><tr><td>
<table role="presentation"><tr><td style="color:red">Hi</td></tr></table>
</td></tr></table></body></html>"""

STATIC = """<html><head><link rel="stylesheet" href="a.css">
<style>:root{--a:1} .g{display:grid}</style></head>
<body><header>h</header><main><section><p>x</p></section></main>
<script>console.log(1)</script></body></html>"""


def _classify(text: str):  # type: ignore[no-untyped-def]
    return classify_html(parse_artifact_html(text).root, text)


def test_email_markup_is_classified_as_email_with_reasons() -> None:
    verdict = _classify(EMAIL)
    assert verdict.artifact_type is ArtifactType.EMAIL
    assert not verdict.ambiguous
    assert any("Outlook" in s for s in verdict.signals)
    assert any("layout table" in s for s in verdict.signals)


def test_web_page_markup_is_classified_as_static_with_reasons() -> None:
    verdict = _classify(STATIC)
    assert verdict.artifact_type is ArtifactType.STATIC
    assert any("script" in s for s in verdict.signals)
    assert any("landmark" in s for s in verdict.signals)


def test_a_plain_page_with_no_email_markup_is_static_not_ambiguous() -> None:
    verdict = _classify("<html><body><p>hello</p></body></html>")
    assert verdict.artifact_type is ArtifactType.STATIC
    assert not verdict.ambiguous
    assert verdict.signals[-1] == "no email markup found"


def test_a_little_email_evidence_without_web_evidence_is_ambiguous_email() -> None:
    page = "<html><body><center><p>hello</p></center></body></html>"
    verdict = _classify(page)
    assert verdict.artifact_type is ArtifactType.EMAIL
    assert verdict.ambiguous
    assert "too little evidence" in verdict.signals[-1]


def test_balanced_evidence_is_flagged_ambiguous_and_uses_the_safe_strategy() -> None:
    balanced = (
        '<html><head><link rel="stylesheet" href="a.css"></head><body>'
        '<table role="presentation"><tr><td>x</td></tr></table>'
        "<!--[if mso]><b>x</b><![endif]-->"
        "<main>m</main><script>1</script></body></html>"
    )
    verdict = _classify(balanced)
    assert verdict.ambiguous
    assert verdict.artifact_type is ArtifactType.EMAIL


def test_clear_lean_towards_static_is_not_ambiguous_even_with_a_table() -> None:
    page = (
        '<html><head><link rel="stylesheet" href="a.css">'
        "<style>.g{display:grid}</style></head><body>"
        '<table role="presentation"><tr><td>x</td></tr></table>'
        "<main>m</main><script>1</script></body></html>"
    )
    verdict = _classify(page)
    assert verdict.artifact_type is ArtifactType.STATIC
    assert not verdict.ambiguous


def test_json_data_scripts_do_not_count_as_executable_scripts() -> None:
    page = '<html><body><script type="application/json">{}</script></body></html>'
    assert not any("script" in s for s in _classify(page).signals)


def test_confidence_is_between_zero_and_one() -> None:
    assert 0.0 <= _classify(EMAIL).confidence <= 1.0
