"""Markdown guide reader: turns a ``.md`` guide into a ``GuideDocument`` tree."""

import logging
from pathlib import Path
from typing import Final

from markdown_it import MarkdownIt
from markdown_it.token import Token

from brand_compliance.models.guide import GuideDocument, GuideNode, NodeKind
from brand_compliance.models.source import SourceSpan
from brand_compliance.plugins.sources.base import DEFAULT_MAX_BYTES, read_source_text

logger = logging.getLogger(__name__)

_SUFFIXES: Final = (".md", ".markdown")


class MarkdownSourceAdapter:
    """Reads Markdown. Sections follow headings; each node keeps its line number."""

    name = "markdown"

    def __init__(self, max_bytes: int = DEFAULT_MAX_BYTES) -> None:
        self._max_bytes = max_bytes

    def can_handle(self, source: Path) -> bool:
        """Return True for ``.md`` and ``.markdown`` files."""
        return source.suffix.lower() in _SUFFIXES

    def load(self, source: Path) -> GuideDocument:
        """Read the file and build the guide tree."""
        text = read_source_text(source, _SUFFIXES, self._max_bytes)
        tokens = MarkdownIt("commonmark").enable("table").parse(text)
        nodes = _TreeBuilder(source.name).build(tokens)
        logger.info("Read guide %s: %d top-level sections", source.name, len(nodes))
        return GuideDocument(
            source_name=source.name, source_format="markdown", nodes=nodes
        )


class _TreeBuilder:
    """Walks markdown-it tokens once and builds nested section nodes."""

    def __init__(self, file_name: str) -> None:
        self._file = file_name
        self._roots: list[GuideNode] = []
        self._open: list[GuideNode] = []  # currently open sections, outermost first

    def build(self, tokens: list[Token]) -> list[GuideNode]:
        """Return the top-level nodes for the token stream."""
        index = 0
        while index < len(tokens):
            index = self._handle(tokens, index)
        return self._roots

    def _handle(self, tokens: list[Token], index: int) -> int:
        token = tokens[index]
        handlers = {
            "heading_open": self._heading,
            "paragraph_open": self._paragraph,
            "list_item_open": self._list_item,
            "table_open": self._table,
            "fence": self._fence,
            "code_block": self._fence,
            "html_block": self._html_block,
        }
        handler = handlers.get(token.type)
        return handler(tokens, index) if handler else index + 1

    # ---- helpers -------------------------------------------------------

    def _span(self, token: Token) -> SourceSpan:
        start, end = token.map if token.map else (0, 0)
        return SourceSpan(
            file=self._file,
            line_start=start + 1,
            line_end=max(end, start + 1),
            heading_path=tuple(section.text for section in self._open),
        )

    def _add(self, node: GuideNode) -> None:
        if self._open:
            self._open[-1].children.append(node)
        else:
            self._roots.append(node)

    @staticmethod
    def _end_of(tokens: list[Token], index: int, close_type: str) -> int:
        """Return the index of the matching close token for a nested block."""
        depth = 0
        open_type = tokens[index].type
        for i in range(index, len(tokens)):
            if tokens[i].type == open_type:
                depth += 1
            elif tokens[i].type == close_type:
                depth -= 1
                if depth == 0:
                    return i
        return len(tokens) - 1

    # ---- node builders -------------------------------------------------

    def _heading(self, tokens: list[Token], index: int) -> int:
        token = tokens[index]
        level = int(token.tag[1:])
        title = tokens[index + 1].content
        while self._open and (self._open[-1].level or 0) >= level:
            self._open.pop()
        section = GuideNode(
            kind=NodeKind.SECTION,
            span=self._span(token),
            text=title,
            level=level,
        )
        self._add(section)
        self._open.append(section)
        # The section's own path includes its title.
        section.span = section.span.model_copy(
            update={"heading_path": tuple(s.text for s in self._open)}
        )
        return index + 3

    def _paragraph(self, tokens: list[Token], index: int) -> int:
        inline = tokens[index + 1]
        if inline.content.strip():
            self._add(
                GuideNode(
                    kind=NodeKind.PARAGRAPH,
                    span=self._span(tokens[index]),
                    text=inline.content,
                )
            )
        return index + 3

    def _list_item(self, tokens: list[Token], index: int) -> int:
        """Record a list item from its first paragraph; read nested lists after."""
        if tokens[index + 1].type != "paragraph_open":
            return index + 1  # item starts with something else; read it normally
        text = tokens[index + 2].content
        if text.strip():
            self._add(
                GuideNode(
                    kind=NodeKind.LIST_ITEM,
                    span=self._span(tokens[index]),
                    text=text,
                )
            )
        return index + 4  # skip paragraph_open, inline, paragraph_close

    def _table(self, tokens: list[Token], index: int) -> int:
        end = self._end_of(tokens, index, "table_close")
        header: list[str] = []
        rows: list[list[str]] = []
        row_lines: list[int] = []
        current: list[str] = []
        in_head = False
        line = 0
        for token in tokens[index:end]:
            if token.type == "thead_open":
                in_head = True
            elif token.type == "thead_close":
                in_head = False
            elif token.type == "tr_open":
                current = []
                line = (token.map[0] + 1) if token.map else 0
            elif token.type == "inline":
                current.append(token.content)
            elif token.type == "tr_close":
                if in_head:
                    header = current
                else:
                    rows.append(current)
                    row_lines.append(line)
        self._add(
            GuideNode(
                kind=NodeKind.TABLE,
                span=self._span(tokens[index]),
                header=header,
                rows=rows,
                row_lines=row_lines,
            )
        )
        return end + 1

    def _fence(self, tokens: list[Token], index: int) -> int:
        token = tokens[index]
        language = token.info.strip().split()[0] if token.info.strip() else None
        self._add(
            GuideNode(
                kind=NodeKind.CODE,
                span=self._span(token),
                text=token.content,
                language=language,
            )
        )
        return index + 1

    def _html_block(self, tokens: list[Token], index: int) -> int:
        self._add(
            GuideNode(
                kind=NodeKind.CODE,
                span=self._span(tokens[index]),
                text=tokens[index].content,
                language="html",
            )
        )
        return index + 1
