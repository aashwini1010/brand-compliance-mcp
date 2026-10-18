"""Finds hard directives (NEVER / ALWAYS / MUST) and Do / Don't tables."""

import re

from brand_compliance.core.text import clean_text
from brand_compliance.models.guide import GuideDocument, GuideNode, NodeKind
from brand_compliance.models.rule import RuleCandidate
from brand_compliance.plugins.extractors.base import (
    CandidateFactory,
    cell,
    column_index,
    row_span,
)

_LIST_MARKER = re.compile(r"^\s*(?:[-*]|\d+\.)\s+")
DEFAULT_KEYWORDS = ("never", "always", "must", "minimum", "don't", "do not", "no other")


class DirectiveExtractor:
    """One candidate per directive sentence or Do / Don't table cell."""

    name = "directive"

    def __init__(self, keywords: tuple[str, ...] = DEFAULT_KEYWORDS) -> None:
        words = "|".join(re.escape(word) for word in keywords)
        self._pattern = re.compile(rf"(?<!\w)(?:{words})(?!\w)", re.IGNORECASE)

    def extract(self, document: GuideDocument) -> list[RuleCandidate]:
        """Return ``directive`` candidates; the normalizer decides what they mean."""
        factory = CandidateFactory(self.name)
        found: list[RuleCandidate] = []
        for node in document.walk():
            if node.kind in (NodeKind.PARAGRAPH, NodeKind.LIST_ITEM):
                text = clean_text(node.text)
                if self._pattern.search(text):
                    hints = {"kind": "directive", "polarity": "neutral", "text": text}
                    found.append(factory.make(text, node.span, hints))
            elif node.kind is NodeKind.TABLE:
                found.extend(self._from_table(node, factory))
            elif node.kind is NodeKind.CODE and node.language is None:
                found.extend(self._from_plain_code(node, factory))
        return found

    def _from_plain_code(
        self, node: GuideNode, factory: CandidateFactory
    ) -> list[RuleCandidate]:
        """Read directive lines inside an untagged code block (e.g. a prompt)."""
        first_line = (node.span.line_start or 0) + 1
        found: list[RuleCandidate] = []
        for offset, raw in enumerate(node.text.splitlines()):
            text = clean_text(_LIST_MARKER.sub("", raw))
            if not text or not self._pattern.search(text):
                continue
            line = first_line + offset
            span = node.span.model_copy(update={"line_start": line, "line_end": line})
            hints = {"kind": "directive", "polarity": "neutral", "text": text}
            found.append(factory.make(text, span, hints))
        return found

    @staticmethod
    def _from_table(node: GuideNode, factory: CandidateFactory) -> list[RuleCandidate]:
        dont = column_index(node.header, "don't")
        do = column_index(node.header, "do")
        if dont is None or do is None:
            return []
        topic = column_index(node.header, "rule")
        found: list[RuleCandidate] = []
        for i, row in enumerate(node.rows):
            prefix = f"{cell(row, topic)}: " if topic is not None else ""
            for polarity, index in (("require", do), ("forbid", dont)):
                value = cell(row, index)
                if not value:
                    continue
                text = f"{prefix}{value}"
                hints = {"kind": "directive", "polarity": polarity, "text": value}
                if prefix:
                    hints["topic"] = cell(row, topic)
                found.append(factory.make(text, row_span(node, i), hints))
        return found
