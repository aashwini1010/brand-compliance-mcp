"""Restore the letter case of SVG names that the HTML parser lowercases.

libxml2's HTML parser lowercases ``viewBox`` to ``viewbox``. Browsers repair
this when reading HTML, but we hand back the author's markup unchanged.
"""

from typing import Final

from lxml.etree import _Element

_SVG_ATTRIBUTES: Final = {
    name.lower(): name
    for name in (
        "viewBox",
        "preserveAspectRatio",
        "gradientUnits",
        "gradientTransform",
        "patternUnits",
        "patternContentUnits",
        "patternTransform",
        "clipPathUnits",
        "maskUnits",
        "maskContentUnits",
        "markerUnits",
        "markerWidth",
        "markerHeight",
        "refX",
        "refY",
        "spreadMethod",
        "startOffset",
        "textLength",
        "lengthAdjust",
        "stdDeviation",
        "baseFrequency",
        "numOctaves",
        "tableValues",
        "pathLength",
        "filterUnits",
        "primitiveUnits",
        "keyTimes",
        "keySplines",
        "repeatCount",
        "attributeName",
    )
}
_SVG_TAGS: Final = {
    name.lower(): name
    for name in (
        "linearGradient",
        "radialGradient",
        "clipPath",
        "textPath",
        "foreignObject",
        "feGaussianBlur",
        "feOffset",
        "feBlend",
        "feColorMatrix",
        "feComposite",
        "feFlood",
        "feMerge",
        "feMergeNode",
        "feMorphology",
        "feTurbulence",
        "animateTransform",
        "animateMotion",
        "altGlyph",
    )
}


def restore_svg_case(root: _Element) -> int:
    """Rename lowercased SVG tags/attributes under every ``<svg>``; return count."""
    changed = 0
    for svg in root.iter("svg"):
        for element in svg.iter():
            if not isinstance(element.tag, str):
                continue
            tag = _SVG_TAGS.get(element.tag)
            if tag is not None:
                element.tag = tag
                changed += 1
            for name in list(element.attrib):
                if not isinstance(name, str):
                    continue
                proper = _SVG_ATTRIBUTES.get(name)
                if proper is not None and proper != name:
                    element.attrib[proper] = element.attrib.pop(name)
                    changed += 1
    return changed
