"""Finds ``Label: value`` bullets that the vocabulary says are specs."""

import re
from collections.abc import Iterable

from brand_compliance.core.text import clean_text
from brand_compliance.models.guide import GuideDocument, NodeKind
from brand_compliance.models.rule import RuleCandidate
from brand_compliance.plugins.extractors.base import CandidateFactory

_LABELLED = re.compile(r"^(?P<label>[^:]{1,60}):\s*(?P<value>.+)$")


class BulletSpecExtractor:
    """One candidate per listed ``Label: value`` bullet (section + label)."""

    name = "bullet_spec"

    def __init__(self, known: Iterable[tuple[str, str]] = ()) -> None:
        self._known = [(section.lower(), label.lower()) for section, label in known]

    def extract(self, document: GuideDocument) -> list[RuleCandidate]:
        """Return ``bullet_spec`` candidates; unlisted bullets are left alone."""
        factory = CandidateFactory(self.name)
        found: list[RuleCandidate] = []
        for node in document.nodes_of(NodeKind.LIST_ITEM):
            match = _LABELLED.match(clean_text(node.text))
            if match is None:
                continue
            section = node.span.heading_path[-1] if node.span.heading_path else ""
            label = match["label"].strip()
            if not self._is_known(section, label):
                continue
            hints = {
                "kind": "bullet_spec",
                "section": section,
                "label": label,
                "value": match["value"].strip(),
            }
            found.append(factory.make(clean_text(node.text), node.span, hints))
        return found

    def _is_known(self, section: str, label: str) -> bool:
        return any(
            section.lower().startswith(known_section) and label.lower() == known_label
            for known_section, known_label in self._known
        )
