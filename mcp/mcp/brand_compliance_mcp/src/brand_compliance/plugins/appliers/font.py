"""Appliers for the brand font: the family everywhere, and where to load it."""

import re
from typing import Final

from lxml.html import HtmlElement

from brand_compliance.core.markers import FONT_LINK_ATTRIBUTE
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import ApplyResult, Change, Skip
from brand_compliance.models.rule import Rule
from brand_compliance.plugins.appliers.base import inline_declares, same_value
from brand_compliance.plugins.artifacts.base import element_path, is_content_element

FONT_SOURCE_PROPERTY: Final = "@font-source"
HEAD_PATH: Final = "/html/head"
_URL_RE: Final = re.compile(r"""url\(\s*["']?(?P<url>https://[^"')\s]+)["']?\s*\)""")


def _first_family(value: str) -> str:
    return value.split(",")[0].strip().strip("\"'").lower()


class FontFamilyApplier:
    """Sets the brand font stack on the page and on every element that uses another."""

    name = "font-family"
    categories = frozenset({"font_family"})

    def plan(self, rule: Rule, artifact: ArtifactModel) -> ApplyResult:
        """Change every element whose declared font family is not the brand font."""
        if not rule.value:
            return ApplyResult(skipped=[Skip(rule_id=rule.id, reason="No font value")])
        brand = _first_family(rule.value)
        result = ApplyResult()
        for element in artifact.tree.iter():
            if not isinstance(element, HtmlElement) or not is_content_element(element):
                continue
            declared = artifact.styles.declared(element, "font-family")
            is_body = element.tag == "body"
            if declared is None and not is_body:
                continue
            if (
                declared is not None and _first_family(declared) == brand
            ) or same_value(declared, rule.value):
                result.satisfied += 1
                continue
            result.changes.append(
                Change(
                    id=f"{rule.id}/{len(result.changes) + 1}",
                    rule_id=rule.id,
                    location=element_path(element),
                    property="font-family",
                    before=declared,
                    after=rule.value,
                    important=inline_declares(element, "font-family"),
                )
            )
        return result


class FontSourceApplier:
    """Carries the guide's web-font import into the artifact as one change."""

    name = "font-source"
    categories = frozenset({"font_source"})

    def plan(self, rule: Rule, artifact: ArtifactModel) -> ApplyResult:
        """Add the font stylesheet unless the page already loads it."""
        match = _URL_RE.search(rule.value or "")
        if match is None:
            return ApplyResult(
                skipped=[
                    Skip(rule_id=rule.id, reason="The font import is not an https URL")
                ]
            )
        url = match["url"]
        existing = {
            link.get("href")
            for link in artifact.tree.iter("link")
            if not link.get(FONT_LINK_ATTRIBUTE)  # our own earlier link does not count
        }
        if url in existing:
            return ApplyResult(satisfied=1)
        return ApplyResult(
            changes=[
                Change(
                    id=f"{rule.id}/1",
                    rule_id=rule.id,
                    location=HEAD_PATH,
                    property=FONT_SOURCE_PROPERTY,
                    before=None,
                    after=url,
                )
            ]
        )
