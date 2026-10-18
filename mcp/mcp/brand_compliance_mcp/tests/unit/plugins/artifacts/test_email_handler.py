"""Tests for the email handler."""

from brand_compliance.core.contracts import ArtifactHandler
from brand_compliance.models.artifact import ArtifactType
from brand_compliance.plugins.artifacts.email import EmailArtifactHandler
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler

EMAIL = """<html xmlns:v="urn:schemas-microsoft-com:vml"><head>
<meta name="x-apple-disable-message-reformatting">
<!--[if mso]><style>td{mso-line-height-rule:exactly}</style><![endif]-->
<style>@media (max-width:600px){.x{width:100%}}</style></head>
<body style="background:#eef1f5"><table role="presentation" bgcolor="#eef1f5"><tr>
<td bgcolor="#102a43"><p style="color:#9fb3c8">Dark header</p></td></tr><tr>
<td style="background:#ffffff"><h1>Title</h1><p>Body</p>
<a class="button" href="https://example.com/go">Go</a></td></tr></table>
<!--[if mso]><table><tr><td>mso only</td></tr></table><![endif]--></body></html>"""


def _parse():  # type: ignore[no-untyped-def]
    return EmailArtifactHandler().parse(EMAIL, "mail.html")


def test_email_handler_implements_the_contract() -> None:
    handler = EmailArtifactHandler()
    assert isinstance(handler, ArtifactHandler)
    assert handler.artifact_type is ArtifactType.EMAIL


def test_detect_scores_email_markup_high_and_a_static_page_low() -> None:
    page = (
        '<html><head><link rel="stylesheet" href="a.css"></head><body><main>'
        "<section><p>x</p></section></main><script>1</script></body></html>"
    )
    assert EmailArtifactHandler().detect(EMAIL).score > 0.5
    assert EmailArtifactHandler().detect(page).score < 0.5
    assert StaticArtifactHandler().detect(EMAIL).score < 0.5


def test_parse_builds_an_email_model_with_roles() -> None:
    artifact = _parse()
    assert artifact.artifact_type is ArtifactType.EMAIL
    assert "heading.h1" in artifact.roles.values()
    assert "button" in artifact.roles.values()


def test_surfaces_come_from_bgcolor_attributes_and_inline_backgrounds() -> None:
    artifact = _parse()
    surfaces = {path: artifact.surfaces[path] for path in artifact.roles}
    header = next(p for p in surfaces if p.endswith("tr[1]/td/p"))
    body = next(p for p in surfaces if p.endswith("/h1"))
    assert surfaces[header] == "dark"
    assert surfaces[body] == "light"


def test_outlook_conditional_comments_are_counted_in_a_note() -> None:
    notes = _parse().notes
    assert any(
        "2 Outlook conditional comment(s) were left untouched" in n for n in notes
    )


def test_media_queries_are_noted_as_not_evaluated() -> None:
    assert any("conditional style block" in n for n in _parse().notes)


def test_email_without_outlook_markup_has_no_outlook_note() -> None:
    artifact = EmailArtifactHandler().parse(
        "<html><body><p>x</p></body></html>", "m.html"
    )
    assert not any("Outlook" in n for n in artifact.notes)


def test_conditional_comment_content_is_not_parsed_as_elements() -> None:
    assert "mso only" not in " ".join(_parse().unmapped_elements)
