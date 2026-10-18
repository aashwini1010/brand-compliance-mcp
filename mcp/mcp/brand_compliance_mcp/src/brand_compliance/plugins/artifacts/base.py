"""Parsing, serialising and describing HTML artifacts (shared by all handlers)."""

import re
from dataclasses import dataclass
from typing import Final

from lxml import html
from lxml.html import HtmlElement

from brand_compliance.core.errors import ParseFailedError
from brand_compliance.core.svg import restore_svg_case

_DOCTYPE_RE: Final = re.compile(r"^\s*(<!doctype[^>]*>)", re.IGNORECASE)
_SKIPPED_CONTAINERS: Final = ("head", "svg", "script", "style", "template", "noscript")


@dataclass(frozen=True)
class ParsedHtml:
    """A parsed document plus what the parser would otherwise drop."""

    root: HtmlElement
    doctype: str | None


def parse_artifact_html(text: str) -> ParsedHtml:
    """Parse HTML text into a tree, keeping the doctype and SVG letter case."""
    text = text.lstrip("﻿")
    if not text.strip():
        raise ParseFailedError("The HTML artifact is empty")
    match = _DOCTYPE_RE.match(text)
    try:
        root = html.document_fromstring(text)
    except (ValueError, html.etree.ParserError) as exc:
        raise ParseFailedError(f"Cannot parse HTML: {exc}") from exc
    restore_svg_case(root)
    return ParsedHtml(root=root, doctype=match.group(1) if match else None)


def serialize_html(root: HtmlElement, doctype: str | None) -> str:
    """Write the whole document back to HTML text with its original doctype.

    The full tree is written, not just the root element, so comments or
    processing instructions before ``<html>`` or after ``</html>`` (common in
    Outlook-style emails) are kept.
    """
    tree = root.getroottree()
    if doctype is None:
        # lxml invents a doctype when the source had none; an empty one suppresses it
        written = str(html.tostring(tree, encoding="unicode", doctype=""))
        return written.removeprefix("\n")
    return str(html.tostring(tree, encoding="unicode", doctype=doctype))


def top_level_nodes(root: HtmlElement) -> list[HtmlElement]:
    """Return every node of the document in order, including the comments that
    sit outside the root element."""
    before = list(reversed(list(root.itersiblings(preceding=True))))
    after = list(root.itersiblings())
    return [*before, *root.iter(), *after]


def element_path(element: HtmlElement) -> str:
    """Return a unique, stable XPath for an element, e.g. ``/html/body/p[2]``."""
    return str(element.getroottree().getpath(element))


def describe_element(element: HtmlElement) -> str:
    """Return a short human description such as ``<button.btn.primary> line 40``."""
    classes = ".".join((element.get("class") or "").split())
    name = f"{element.tag}.{classes}" if classes else str(element.tag)
    line = element.sourceline
    return f"<{name}> line {line}" if line else f"<{name}>"


def is_content_element(element: HtmlElement) -> bool:
    """True for ordinary body elements (not head, svg, script, style...)."""
    if not isinstance(element.tag, str) or element.tag == "html":
        return False
    if element.tag == "body":
        return True
    chain = [element, *element.iterancestors()]
    return not any(node.tag in _SKIPPED_CONTAINERS for node in chain)


def has_own_text(element: HtmlElement) -> bool:
    """True if the element holds visible text directly (not only via children)."""
    if element.text and element.text.strip():
        return True
    return any(child.tail and child.tail.strip() for child in element)
