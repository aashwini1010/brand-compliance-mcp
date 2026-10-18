"""Finds CSS declarations in ``css`` code blocks and inline HTML styles."""

import re
from typing import Any

import tinycss2

from brand_compliance.core.css import parse_declarations
from brand_compliance.core.errors import ParseFailedError
from brand_compliance.models.guide import GuideDocument, GuideNode, NodeKind
from brand_compliance.models.rule import RuleCandidate
from brand_compliance.models.source import SourceSpan
from brand_compliance.plugins.extractors.base import CandidateFactory

_INLINE_STYLE_RE = re.compile(r'<(\w+)[^>]*?\sstyle="([^"]*)"')


class CssBlockExtractor:
    """One candidate per CSS declaration, import or problem found in code."""

    name = "css_block"

    def extract(self, document: GuideDocument) -> list[RuleCandidate]:
        """Return CSS candidates from ``css`` and ``html`` code blocks."""
        factory = CandidateFactory(self.name)
        found: list[RuleCandidate] = []
        for node in document.nodes_of(NodeKind.CODE):
            if node.language == "css":
                found.extend(self._from_css(node, factory))
            elif node.language == "html":
                found.extend(self._from_html(node, factory))
        return found

    @staticmethod
    def _span(node: GuideNode, line: int) -> SourceSpan:
        return SourceSpan(
            file=node.span.file,
            line_start=line,
            line_end=line,
            heading_path=node.span.heading_path,
        )

    def _from_css(
        self, node: GuideNode, factory: CandidateFactory
    ) -> list[RuleCandidate]:
        base = node.span.line_start or 0
        found: list[RuleCandidate] = []
        items = tinycss2.parse_blocks_contents(
            node.text, skip_comments=True, skip_whitespace=True
        )
        for item in items:
            span = self._span(node, base + getattr(item, "source_line", 1))
            if item.type == "declaration":
                found.append(self._declaration(factory, span, "", item))
            elif item.type == "qualified-rule":
                selector = tinycss2.serialize(item.prelude).strip()
                inner = tinycss2.parse_blocks_contents(
                    item.content, skip_comments=True, skip_whitespace=True
                )
                for decl in inner:
                    line = base + getattr(decl, "source_line", 1)
                    if decl.type == "declaration":
                        found.append(
                            self._declaration(
                                factory, self._span(node, line), selector, decl
                            )
                        )
            elif item.type == "at-rule" and item.lower_at_keyword == "import":
                value = tinycss2.serialize(item.prelude).strip()
                hints = {"kind": "css_import", "value": value}
                found.append(factory.make(f"@import {value}", span, hints))
            else:
                reason = getattr(item, "message", f"unsupported {item.type}")
                hints = {"kind": "css_unsupported", "problem": reason}
                found.append(factory.make(f"CSS: {reason}", span, hints))
        return found

    @staticmethod
    def _declaration(
        factory: CandidateFactory, span: SourceSpan, selector: str, decl: Any
    ) -> RuleCandidate:
        name = decl.name if decl.name.startswith("--") else decl.lower_name
        value = tinycss2.serialize(decl.value).strip()
        if decl.important:
            value += " !important"
        hints = {
            "kind": "css_declaration",
            "selector": selector,
            "property": name,
            "value": value,
        }
        return factory.make(f"{selector} {name}: {value}".strip(), span, hints)

    def _from_html(
        self, node: GuideNode, factory: CandidateFactory
    ) -> list[RuleCandidate]:
        base = node.span.line_start or 0
        found: list[RuleCandidate] = []
        for match in _INLINE_STYLE_RE.finditer(node.text):
            line = base + node.text.count("\n", 0, match.start()) + 1
            span = self._span(node, line)
            try:
                declarations = parse_declarations(match.group(2))
            except ParseFailedError as exc:
                hints = {"kind": "css_unsupported", "problem": str(exc)}
                found.append(factory.make(f"CSS: {exc}", span, hints))
                continue
            for name, value in declarations.items():
                hints = {
                    "kind": "css_declaration",
                    "selector": match.group(1),
                    "property": name,
                    "value": value,
                }
                found.append(
                    factory.make(f"{match.group(1)} {name}: {value}", span, hints)
                )
        return found
