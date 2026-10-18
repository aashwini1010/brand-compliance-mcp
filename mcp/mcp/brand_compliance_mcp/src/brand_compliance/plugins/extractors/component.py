"""Finds component variants (e.g. button styles) in tables."""

from brand_compliance.core.text import clean_text
from brand_compliance.models.guide import GuideDocument, NodeKind
from brand_compliance.models.rule import RuleCandidate
from brand_compliance.plugins.extractors.base import (
    CandidateFactory,
    cell,
    normalize_header,
    row_span,
)


class ComponentExtractor:
    """One candidate per row of a table whose first column is ``Variant``."""

    name = "component"

    def extract(self, document: GuideDocument) -> list[RuleCandidate]:
        """Return a ``component_row`` candidate per variant row."""
        factory = CandidateFactory(self.name)
        found: list[RuleCandidate] = []
        for table in document.nodes_of(NodeKind.TABLE):
            if not table.header or normalize_header(table.header[0]) != "variant":
                continue
            for i, row in enumerate(table.rows):
                hints = {"kind": "component_row", "variant": cell(row, 0)}
                for index in range(1, len(table.header)):
                    key = f"col:{normalize_header(table.header[index])}"
                    hints[key] = cell(row, index)
                text = " | ".join(clean_text(c) for c in row)
                found.append(factory.make(text, row_span(table, i), hints))
        return found
