"""Finds the type scale (size, weight, spacing per token)."""

from brand_compliance.core.text import clean_text
from brand_compliance.models.guide import GuideDocument, NodeKind
from brand_compliance.models.rule import RuleCandidate
from brand_compliance.plugins.extractors.base import (
    CandidateFactory,
    cell,
    column_index,
    row_span,
)

_COLUMNS = {
    "token": "token",
    "size": "size",
    "weight": "weight",
    "line-height": "line_height",
    "letter-spacing": "letter_spacing",
    "use": "use",
}


class TypographyExtractor:
    """One candidate per row of a table with Token, Size and Weight columns."""

    name = "typography"

    def extract(self, document: GuideDocument) -> list[RuleCandidate]:
        """Return a ``type_row`` candidate for each type-scale row."""
        factory = CandidateFactory(self.name)
        found: list[RuleCandidate] = []
        for table in document.nodes_of(NodeKind.TABLE):
            indexes = {
                key: column_index(table.header, col) for col, key in _COLUMNS.items()
            }
            if None in (indexes["token"], indexes["size"], indexes["weight"]):
                continue
            for i, row in enumerate(table.rows):
                hints = {"kind": "type_row"}
                hints.update({key: cell(row, idx) for key, idx in indexes.items()})
                text = " | ".join(clean_text(c) for c in row)
                found.append(factory.make(text, row_span(table, i), hints))
        return found
