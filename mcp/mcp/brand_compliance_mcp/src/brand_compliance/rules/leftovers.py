"""Keep every part of the guide that no extractor claimed (nothing is dropped)."""

from brand_compliance.core.text import clean_text
from brand_compliance.models.guide import GuideDocument, GuideNode, NodeKind
from brand_compliance.models.rule import RuleCandidate
from brand_compliance.models.source import SourceSpan

_MAX_TEXT = 300


def _claimed_lines(candidates: list[RuleCandidate]) -> set[int]:
    lines: set[int] = set()
    for candidate in candidates:
        start = candidate.span.line_start
        if start is None:
            continue
        lines.update(range(start, (candidate.span.line_end or start) + 1))
    return lines


def _unclaimed_runs(node: GuideNode, claimed: set[int]) -> list[tuple[int, int, str]]:
    """Group unclaimed, non-blank lines of a code block into contiguous runs."""
    first_line = (node.span.line_start or 0) + 1
    runs: list[tuple[int, int, str]] = []
    current: list[tuple[int, str]] = []

    def flush() -> None:
        if current:
            text = clean_text(" ".join(part for _, part in current))
            runs.append((current[0][0], current[-1][0], text))
            current.clear()

    for offset, raw in enumerate(node.text.splitlines()):
        line = first_line + offset
        if raw.strip() and line not in claimed:
            current.append((line, raw.strip()))
        else:
            flush()
    flush()
    return runs


def collect_unmatched(
    document: GuideDocument, candidates: list[RuleCandidate]
) -> list[RuleCandidate]:
    """Return an ``unmatched`` candidate for each unclaimed piece of the guide."""
    claimed = _claimed_lines(candidates)
    found: list[RuleCandidate] = []

    def add(text: str, span: SourceSpan) -> None:
        found.append(
            RuleCandidate(
                id=f"unmatched:{span.line_start}:{len(found) + 1}",
                extractor="unmatched",
                text=text[:_MAX_TEXT],
                span=span,
                hints={"kind": "unmatched"},
            )
        )

    for node in document.walk():
        start = node.span.line_start or 0
        if node.kind in (NodeKind.PARAGRAPH, NodeKind.LIST_ITEM):
            if start not in claimed:
                add(clean_text(node.text), node.span)
        elif node.kind is NodeKind.CODE and node.language is None:
            for first, last, text in _unclaimed_runs(node, claimed):
                add(
                    text,
                    node.span.model_copy(
                        update={"line_start": first, "line_end": last}
                    ),
                )
        elif node.kind is NodeKind.CODE:
            end = node.span.line_end or start
            if not claimed.intersection(range(start, end + 1)):
                add(clean_text(node.text), node.span)
        elif node.kind is NodeKind.TABLE:
            for index, row in enumerate(node.rows):
                line = node.row_lines[index]
                if line not in claimed:
                    span = node.span.model_copy(
                        update={"line_start": line, "line_end": line}
                    )
                    add(" | ".join(clean_text(c) for c in row), span)
    return found
