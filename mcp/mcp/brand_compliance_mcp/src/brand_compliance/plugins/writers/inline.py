"""Writer for emails: styles go inline, on each element, with plain values.

Email clients ignore or strip most ``<style>`` blocks and modern CSS, so every
change is written into the element's own ``style`` attribute. Nothing is added
to the markup except that attribute (and the optional font link in the head),
and Outlook conditional comments are left exactly as they were.
"""

import logging
from collections import defaultdict

from brand_compliance.core.css import (
    format_declarations,
    merge_declarations,
    parse_declarations,
)
from brand_compliance.core.errors import ParseFailedError
from brand_compliance.models.artifact import ArtifactModel, ArtifactType
from brand_compliance.models.change import Change
from brand_compliance.plugins.appliers.font import FONT_SOURCE_PROPERTY
from brand_compliance.plugins.writers.base import (
    add_font_links,
    ensure_head,
    remove_font_links,
)

logger = logging.getLogger(__name__)


class InlineWriter:
    """Writes changes into ``style`` attributes."""

    name = "inline"
    artifact_type = ArtifactType.EMAIL

    def write(self, changes: list[Change], artifact: ArtifactModel) -> ArtifactModel:
        """Merge each element's changes into its inline style."""
        style_changes = [c for c in changes if c.property != FONT_SOURCE_PROPERTY]
        font_urls = [c.after for c in changes if c.property == FONT_SOURCE_PROPERTY]
        if not style_changes and not font_urls:
            return artifact  # nothing new: keep whatever is there
        head = ensure_head(artifact.tree)
        remove_font_links(head)
        add_font_links(head, font_urls)
        per_element: dict[str, dict[str, str]] = defaultdict(dict)
        for change in style_changes:
            per_element[change.location][change.property] = _email_safe(change.after)
        for location, properties in per_element.items():
            element = artifact.tree.xpath(location)[0]
            element.set("style", _merged_style(element.get("style") or "", properties))
        if style_changes:
            artifact.notes.append(
                f"Wrote inline styles on {len(per_element)} element(s); no <style> "
                "block or marker attributes were added"
            )
        if font_urls:
            artifact.notes.append(
                "Montserrat loads only in email clients that support web fonts "
                "(for example Apple Mail); other clients show the fallback fonts"
            )
        return artifact


def _email_safe(value: str) -> str:
    """Use single quotes, which survive inside a ``style="..."`` attribute."""
    return value.replace('"', "'")


def _merged_style(existing: str, properties: dict[str, str]) -> str:
    try:
        current = parse_declarations(existing)
    except ParseFailedError:
        # Keep the author's text as it is and add ours after it.
        return "; ".join(
            filter(
                None, [existing.strip().rstrip(";"), format_declarations(properties)]
            )
        )
    return format_declarations(merge_declarations(current, properties))
