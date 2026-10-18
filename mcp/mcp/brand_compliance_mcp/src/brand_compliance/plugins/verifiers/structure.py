"""Check that the output has the same elements, attributes, text and comments."""

import re
from typing import Final

from lxml.html import HtmlElement

from brand_compliance.core.css import format_declarations, parse_declarations
from brand_compliance.core.errors import ParseFailedError
from brand_compliance.core.markers import (
    ANNOTATION_ATTRIBUTES,
    FONT_LINK_ATTRIBUTE,
    STYLE_ID,
)
from brand_compliance.models.artifact import ArtifactModel, ArtifactType
from brand_compliance.models.change import Change
from brand_compliance.models.report import CheckResult
from brand_compliance.models.rule import Rule
from brand_compliance.plugins.appliers.font import FONT_SOURCE_PROPERTY
from brand_compliance.plugins.artifacts.base import top_level_nodes

_MAX_REPORTED: Final = 5
_VERBATIM: Final = ("script", "style")
_SPACES: Final = re.compile(r"\s+")

_Signature = tuple[object, ...]


class StructureVerifier:
    """Fails if anything but the tool's own additions differs from the original."""

    name = "structure"
    scope = "output"

    def check(
        self,
        original: ArtifactModel,
        output: ArtifactModel,
        rules: list[Rule],  # noqa: ARG002
        changes: list[Change],
    ) -> CheckResult:
        """Compare the two trees element by element, in document order.

        For emails, styles are written inline, so each changed element's ``style``
        must equal its original declarations updated by exactly the planned changes.
        """
        problems: list[str] = []
        if original.doctype != output.doctype:
            problems.append(
                f"doctype changed: {original.doctype!r} -> {output.doctype!r}"
            )
        expected = _expected_styles(original, changes)
        first = _signatures(original.tree, expected)
        second = _signatures(output.tree, {} if expected is not None else None)
        if len(first) != len(second):
            problems.append(f"{len(first)} nodes before, {len(second)} after")
        for index, (before, after) in enumerate(zip(first, second, strict=False)):
            if before != after:
                problems.append(f"node {index} <{before[0]}> differs from <{after[0]}>")
                if len(problems) >= _MAX_REPORTED:
                    break
        return CheckResult(
            name=self.name,
            passed=not problems,
            details=problems or [f"{len(first)} nodes identical, in the same order"],
        )


def _is_ours(element: HtmlElement) -> bool:
    return element.get("id") == STYLE_ID or bool(element.get(FONT_LINK_ATTRIBUTE))


def _text(element: HtmlElement, value: str | None) -> str:
    if element.tag in _VERBATIM:
        return value or ""
    return _SPACES.sub(" ", value or "").strip()


def _expected_styles(
    original: ArtifactModel, changes: list[Change]
) -> dict[str, dict[str, str]] | None:
    """For emails: the declarations each changed element should end up with.

    Returns None for other artifacts, whose ``style`` attributes must not change.
    """
    if original.artifact_type is not ArtifactType.EMAIL:
        return None
    expected: dict[str, dict[str, str]] = {}
    for change in changes:
        if change.property == FONT_SOURCE_PROPERTY:
            continue
        element = original.tree.xpath(change.location)[0]
        base = expected.get(change.location)
        if base is None:
            base = _declarations(element.get("style"))
            expected[change.location] = base
        base[change.property] = _quotes(change.after)
    return expected


def _quotes(value: str) -> str:
    return value.replace('"', "'")


def _declarations(style: str | None) -> dict[str, str]:
    try:
        return {k: _quotes(v) for k, v in parse_declarations(style or "").items()}
    except ParseFailedError:
        return {"?unreadable": style or ""}


def _signatures(
    root: HtmlElement, expected: dict[str, dict[str, str]] | None = None
) -> list[_Signature]:
    """Describe every node.

    With ``expected`` (emails), every ``style`` is compared as parsed declarations,
    and a changed element must carry exactly its expected declarations.
    """
    tree = root.getroottree()
    result: list[_Signature] = []
    for element in top_level_nodes(root):
        if not isinstance(element.tag, str):  # comments and processing instructions
            result.append(
                ("#comment", _SPACES.sub(" ", element.text or "").strip(), "")
            )
            continue
        if _is_ours(element):
            continue
        attributes = {
            k: v for k, v in element.attrib.items() if k not in ANNOTATION_ATTRIBUTES
        }
        if expected is not None:
            path = tree.getpath(element)
            if path in expected:
                attributes["style"] = format_declarations(expected[path])
            elif "style" in attributes:
                attributes["style"] = format_declarations(
                    _declarations(attributes["style"])
                )
        tail = _SPACES.sub(" ", element.tail or "").strip()
        result.append(
            (
                element.tag,
                tuple(sorted(attributes.items())),
                _text(element, element.text),
                tail,
            )
        )
    return result
