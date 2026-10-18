"""Helpers shared by the extractors."""

import re
from itertools import count

from brand_compliance.core.text import clean_text
from brand_compliance.models.guide import GuideNode
from brand_compliance.models.rule import RuleCandidate
from brand_compliance.models.source import SourceSpan

_LEADING_SYMBOLS = re.compile(r"^[^\w]+")


def normalize_header(cell: str) -> str:
    """Lower-case a header cell and drop marks and leading symbols (e.g. ✓)."""
    return _LEADING_SYMBOLS.sub("", clean_text(cell)).lower()


def column_index(header: list[str], name: str) -> int | None:
    """Return the index of the header cell called ``name``, if any."""
    for index, cell in enumerate(header):
        if normalize_header(cell) == name:
            return index
    return None


def row_span(table: GuideNode, index: int) -> SourceSpan:
    """Return the source location of one table row."""
    line = table.row_lines[index] if index < len(table.row_lines) else None
    return SourceSpan(
        file=table.span.file,
        line_start=line or table.span.line_start,
        line_end=line or table.span.line_start,
        heading_path=table.span.heading_path,
    )


def cell(row: list[str], index: int | None) -> str:
    """Return a cleaned cell, or an empty string when missing."""
    if index is None or index >= len(row):
        return ""
    return clean_text(row[index])


class CandidateFactory:
    """Creates candidates with ids that are unique within one extractor run."""

    def __init__(self, extractor: str) -> None:
        self._extractor = extractor
        self._seq = count(1)

    def make(self, text: str, span: SourceSpan, hints: dict[str, str]) -> RuleCandidate:
        """Build one candidate."""
        line = span.line_start or 0
        return RuleCandidate(
            id=f"{self._extractor}:{line}:{next(self._seq)}",
            extractor=self._extractor,
            text=text,
            span=span,
            hints=hints,
        )
