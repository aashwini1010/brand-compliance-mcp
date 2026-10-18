"""Handler for marketing emails (table layouts, inline styles, Outlook markup)."""

import re
from typing import Final

from lxml.html import HtmlElement

from brand_compliance.models.artifact import ArtifactType
from brand_compliance.plugins.artifacts.html_handler import HtmlArtifactHandler

_MSO_COMMENT: Final = re.compile(r"<!--\s*\[if[^\]]*mso", re.IGNORECASE)


class EmailArtifactHandler(HtmlArtifactHandler):
    """Parses an email the same way as a page, and notes what it cannot reach."""

    name = "email"
    artifact_type = ArtifactType.EMAIL

    def extra_notes(self, root: HtmlElement, raw: str) -> list[str]:  # noqa: ARG002
        """Say what is left untouched: markup that only Outlook reads."""
        count = len(_MSO_COMMENT.findall(raw))
        if not count:
            return []
        return [
            f"{count} Outlook conditional comment(s) were left untouched; Outlook "
            "desktop may still show the original styling inside them"
        ]
