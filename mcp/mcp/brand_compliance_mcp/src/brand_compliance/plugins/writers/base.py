"""Pieces every writer needs: the head element and the web-font link."""

from lxml import etree
from lxml.html import HtmlElement

from brand_compliance.core.markers import FONT_LINK_ATTRIBUTE


def ensure_head(root: HtmlElement) -> HtmlElement:
    """Return the document's ``<head>``, creating one if it is missing."""
    head = root.find("head")
    if head is None:
        head = etree.Element("head")
        root.insert(0, head)
    return head


def remove_font_links(head: HtmlElement) -> None:
    """Drop the font links an earlier run added, so re-running stays stable."""
    for element in list(head):
        if element.get(FONT_LINK_ATTRIBUTE):
            head.remove(element)


def add_font_links(head: HtmlElement, urls: list[str]) -> None:
    """Add a stylesheet link for each web-font URL."""
    for url in urls:
        link = etree.SubElement(head, "link", rel="stylesheet", href=url)
        link.set(FONT_LINK_ATTRIBUTE, "font")
