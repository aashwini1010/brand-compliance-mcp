"""Check that no image, link, font or anchor was lost, broken or added."""

import re
from collections import Counter
from typing import Final

from lxml.html import HtmlElement

from brand_compliance.core.markers import FONT_LINK_ATTRIBUTE, STYLE_ID
from brand_compliance.models.artifact import ArtifactModel
from brand_compliance.models.change import Change
from brand_compliance.models.report import CheckResult
from brand_compliance.models.rule import Rule

_URL_ATTRIBUTES: Final = ("src", "href", "poster", "data", "action", "background")
_CSS_URL: Final = re.compile(r"""url\(\s*["']?([^"')\s]+)["']?\s*\)""")
_CSS_IMPORT: Final = re.compile(r"""@import\s+["']([^"']+)["']""")
_FONT_SOURCE: Final = "@font-source"


class AssetsVerifier:
    """Fails if an asset disappears, an unexpected one appears, or an anchor breaks."""

    name = "assets"
    scope = "output"

    def check(
        self,
        original: ArtifactModel,
        output: ArtifactModel,
        rules: list[Rule],  # noqa: ARG002
        changes: list[Change],
    ) -> CheckResult:
        """Compare the asset references of the original and the output."""
        before, after = _assets(original.tree), _assets(output.tree)
        allowed = Counter(c.after for c in changes if c.property == _FONT_SOURCE)
        problems: list[str] = []
        problems += [f"missing: {url}" for url in (before - after)]
        problems += [f"unexpected: {url}" for url in ((after - before) - allowed)]
        problems += _broken_anchors(original.tree, output.tree)
        return CheckResult(
            name=self.name,
            passed=not problems,
            details=problems[:10]
            or [f"{sum(before.values())} asset reference(s) preserved, anchors intact"],
        )


def _walk(root: HtmlElement) -> list[HtmlElement]:
    return [
        e
        for e in root.iter()
        if isinstance(e.tag, str)
        and e.get("id") != STYLE_ID
        and not e.get(FONT_LINK_ATTRIBUTE)
    ]


def _assets(root: HtmlElement) -> Counter[str]:
    found: Counter[str] = Counter()
    for element in _walk(root):
        for attribute in _URL_ATTRIBUTES:
            value = element.get(attribute)
            if value and not value.startswith("#"):
                found[value] += 1
        srcset = element.get("srcset")
        if srcset:
            found.update(part.split()[0] for part in srcset.split(",") if part.strip())
        found.update(_CSS_URL.findall(element.get("style") or ""))
        if element.tag == "style":
            css = element.text or ""
            found.update(_CSS_URL.findall(css))
            found.update(_CSS_IMPORT.findall(css))
    return found


def _ids(root: HtmlElement) -> set[str]:
    return {value for e in _walk(root) if (value := e.get("id"))}


def _anchors(root: HtmlElement) -> set[str]:
    targets: set[str] = set()
    for element in _walk(root):
        href = element.get("href") or ""
        if href.startswith("#") and len(href) > 1:
            targets.add(href[1:])
    return targets


def _broken_anchors(original: HtmlElement, output: HtmlElement) -> list[str]:
    was_fine = _anchors(original) & _ids(original)
    now_missing = was_fine - _ids(output)
    return [f"anchor #{name} no longer has a target" for name in sorted(now_missing)]
