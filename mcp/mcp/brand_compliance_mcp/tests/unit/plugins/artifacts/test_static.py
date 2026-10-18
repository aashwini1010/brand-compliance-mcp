"""Tests for brand_compliance.plugins.artifacts.static."""

from brand_compliance.core.contracts import ArtifactHandler
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.models.artifact import ArtifactType
from brand_compliance.plugins.artifacts import register_artifacts
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler

PAGE = """<!doctype html><html><head><style>
:root{--bg:#0e1117;--ink:#f1f4f8} body{background:var(--bg);color:var(--ink)}
.hero{background:linear-gradient(red,blue)} @media (min-width:1px){p{color:red}}
a:hover{color:red}</style></head><body><main>
<h1>Hi</h1><p>text</p><div class="hero"><p id="h">on gradient</p></div>
<button class="primary">Go</button><script>1</script></main></body></html>"""


def test_handler_implements_the_artifact_contract() -> None:
    assert isinstance(StaticArtifactHandler(), ArtifactHandler)


def test_register_artifacts_makes_the_handler_findable() -> None:
    registry = PluginRegistry()
    register_artifacts(registry)
    assert registry.describe()["ArtifactHandler"] == ["static", "email"]


def test_detect_gives_a_high_score_for_a_web_page() -> None:
    detection = StaticArtifactHandler().detect(PAGE)
    assert detection.artifact_type is ArtifactType.STATIC
    assert detection.score > 0.5


def test_detect_gives_a_low_score_for_an_email() -> None:
    email = (
        '<html xmlns:v="urn:schemas-microsoft-com:vml"><body>'
        '<table role="presentation" bgcolor="#fff"><tr><td>x</td></tr></table>'
        "<!--[if mso]><b>x</b><![endif]--></body></html>"
    )
    assert StaticArtifactHandler().detect(email).score < 0.5


def test_parse_builds_a_model_with_roles_and_surfaces() -> None:
    artifact = StaticArtifactHandler().parse(PAGE, "page.html")
    assert artifact.artifact_type is ArtifactType.STATIC
    assert artifact.doctype == "<!doctype html>"
    assert artifact.roles["/html/body/main/h1"] == "heading.h1"
    assert artifact.surfaces["/html/body/main/h1"] == "dark"


def test_surface_is_unknown_when_the_background_cannot_be_determined() -> None:
    artifact = StaticArtifactHandler().parse(PAGE, "page.html")
    assert artifact.surfaces["/html/body/main/div/p"] == "unknown"


def test_parse_records_what_was_not_evaluated() -> None:
    notes = StaticArtifactHandler().parse(PAGE, "page.html").notes
    assert any("conditional style block" in n for n in notes)


def test_parse_fingerprints_the_source_text() -> None:
    first = StaticArtifactHandler().parse(PAGE, "a.html")
    second = StaticArtifactHandler().parse(PAGE + " ", "a.html")
    assert len(first.source_sha256) == 64
    assert first.source_sha256 != second.source_sha256


def test_parse_does_not_expose_the_tree_in_serialised_output() -> None:
    dump = StaticArtifactHandler().parse(PAGE, "a.html").model_dump()
    assert "tree" not in dump
    assert "styles" not in dump
