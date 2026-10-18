"""Shared parsing for every kind of HTML artifact (web page, email).

The two kinds are read the same way: a tree, the base styles, a role for each
element, and the surface behind each. They differ only in their type and in the
notes they add, so subclasses set ``name``, ``artifact_type`` and ``extra_notes``.
"""

import logging

from lxml.html import HtmlElement

from brand_compliance.core.cascade import StyleIndex
from brand_compliance.core.color import Color
from brand_compliance.core.contrast import is_light_surface
from brand_compliance.core.hashing import sha256_bytes
from brand_compliance.models.artifact import ArtifactModel, ArtifactType, Detection
from brand_compliance.plugins.artifacts.base import parse_artifact_html
from brand_compliance.plugins.artifacts.classifier import classify_html
from brand_compliance.plugins.artifacts.roles import (
    RoleRule,
    load_role_rules,
    map_roles,
)

logger = logging.getLogger(__name__)


class HtmlArtifactHandler:
    """Parses HTML into an ``ArtifactModel`` of a fixed artifact type."""

    name = "html"
    artifact_type = ArtifactType.STATIC

    def __init__(self, role_rules: list[RoleRule] | None = None) -> None:
        self._role_rules = role_rules if role_rules is not None else load_role_rules()

    def detect(self, html: str) -> Detection:
        """Score how likely the HTML is this handler's kind of artifact."""
        parsed = parse_artifact_html(html)
        verdict = classify_html(parsed.root, html)
        mine = verdict.artifact_type is self.artifact_type
        return Detection(
            artifact_type=self.artifact_type,
            score=verdict.confidence if mine else round(1 - verdict.confidence, 2),
            signals=verdict.signals,
        )

    def parse(self, html: str, source_name: str) -> ArtifactModel:
        """Parse the HTML into an editable ``ArtifactModel`` copy."""
        parsed = parse_artifact_html(html)
        verdict = classify_html(parsed.root, html)
        styles = StyleIndex.build(parsed.root)
        role_map = map_roles(parsed.root, self._role_rules)
        surfaces = {
            path: _surface(styles.background_color(element))
            for path, element in role_map.elements.items()
        }
        logger.info(
            "Parsed %s as %s: %d roles, %d unmapped text elements",
            source_name,
            self.artifact_type.value,
            len(role_map.roles),
            len(role_map.unmapped),
        )
        return ArtifactModel(
            source_name=source_name,
            source_sha256=sha256_bytes(html.encode("utf-8")),
            artifact_type=self.artifact_type,
            signals=verdict.signals,
            doctype=parsed.doctype,
            tree=parsed.root,
            styles=styles,
            roles=role_map.roles,
            surfaces=surfaces,
            unmapped_elements=role_map.unmapped,
            notes=[*_style_notes(styles), *self.extra_notes(parsed.root, html)],
        )

    def extra_notes(self, root: HtmlElement, raw: str) -> list[str]:  # noqa: ARG002
        """Notes specific to this kind of artifact (override in subclasses)."""
        return []


def _surface(color: Color | None) -> str:
    if color is None:
        return "unknown"
    return "light" if is_light_surface(color) else "dark"


def _style_notes(styles: StyleIndex) -> list[str]:
    notes: list[str] = []
    if styles.conditional_blocks:
        notes.append(
            f"{styles.conditional_blocks} conditional style block(s) "
            "(@media, @supports) were not evaluated"
        )
    if styles.skipped_selectors:
        notes.append(
            f"{styles.skipped_selectors} style rule(s) with states or unsupported "
            "selectors were skipped"
        )
    return notes
