"""Finds colour tokens in tables with Token and Hex columns."""

from brand_compliance.core.text import clean_text
from brand_compliance.models.guide import GuideDocument, NodeKind
from brand_compliance.models.rule import RuleCandidate
from brand_compliance.plugins.extractors.base import (
    CandidateFactory,
    cell,
    column_index,
    row_span,
)

_COLUMNS = ("token", "hex", "rgb", "hsl", "use")


class TokenTableExtractor:
    """One candidate per palette row (name, hex, optional rgb/hsl/use)."""

    name = "token_table"

    def extract(self, document: GuideDocument) -> list[RuleCandidate]:
        """Return a ``palette_row`` candidate for each row of each palette table."""
        factory = CandidateFactory(self.name)
        found: list[RuleCandidate] = []
        for table in document.nodes_of(NodeKind.TABLE):
            indexes = {name: column_index(table.header, name) for name in _COLUMNS}
            if indexes["token"] is None or indexes["hex"] is None:
                continue
            section = table.span.heading_path[-1] if table.span.heading_path else ""
            for i, row in enumerate(table.rows):
                hints = {"kind": "palette_row", "section": section}
                hints.update({n: cell(row, idx) for n, idx in indexes.items()})
                text = " | ".join(clean_text(c) for c in row)
                found.append(factory.make(text, row_span(table, i), hints))
        return found
