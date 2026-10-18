"""Handler for ordinary web pages."""

from brand_compliance.models.artifact import ArtifactType
from brand_compliance.plugins.artifacts.html_handler import HtmlArtifactHandler


class StaticArtifactHandler(HtmlArtifactHandler):
    """Parses a static page, labels its elements and notes each text surface."""

    name = "static"
    artifact_type = ArtifactType.STATIC
