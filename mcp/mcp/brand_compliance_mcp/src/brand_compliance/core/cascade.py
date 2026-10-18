"""A small CSS cascade reader for the *base* styles of one HTML document.

It answers "what is the declared value of this property on this element?" and
"what colour is behind this element?". It is deliberately limited and honest:

- Rules inside ``@media`` / ``@supports`` are counted, not evaluated.
- Selectors with states or pseudo-elements (``:hover``, ``::before``) are skipped.
- ``var()`` is resolved only from custom properties set on ``:root`` / ``html``.
- Anything it cannot determine returns ``None`` (unknown), never a guess.
"""

import copy
import logging
import re
from dataclasses import dataclass, field
from typing import Final, cast

import cssselect
import tinycss2
from lxml.cssselect import CSSSelector
from lxml.etree import _Element

from brand_compliance.core.color import Color, parse_color
from brand_compliance.core.css import parse_declarations
from brand_compliance.core.errors import InvalidInputError, ParseFailedError
from brand_compliance.core.markers import STYLE_ID
from brand_compliance.core.text import split_top_level

logger = logging.getLogger(__name__)

_VAR_RE: Final = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]*))?\)")
_COLOR_IN_VALUE: Final = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|(?:rgb|hsl)a?\([^)]*\)|\b(?:white|black|transparent)\b"
)
_DARK_SCHEME_RE: Final = re.compile(r"prefers-color-scheme\s*:\s*dark")
_DARK_SELECTOR_RE: Final = re.compile(r"data-theme|\.dark\b|\.theme-dark")
_DARK_ATTRIBUTE_RE: Final = re.compile(r'\[[\w-]+\s*=\s*["\']?dark["\']?\]')
_INHERITING_COLORS: Final = {"inherit", "currentcolor", "initial", "unset", "revert"}
_SKIPPED_MEDIA: Final = {"all", "screen"}
_ROOT_SELECTORS: Final = {":root", "html"}


@dataclass(frozen=True)
class _Rule:
    selector: CSSSelector
    text: str
    specificity: tuple[int, int, int]
    order: int
    declarations: dict[str, str]


@dataclass
class StyleIndex:
    """Index of the base style rules of one document."""

    root: _Element
    variables: dict[str, str] = field(default_factory=dict)
    conditional_blocks: int = 0
    dark_variants: bool = False
    dark_selectors: set[str] = field(default_factory=set)
    dark_variables: dict[str, str] = field(default_factory=dict)
    overrides: dict[tuple[_Element, str], str] = field(default_factory=dict)
    skipped_selectors: int = 0
    _rules: list[_Rule] = field(default_factory=list)
    _matches: dict[_Element, list[_Rule]] = field(default_factory=dict)

    @classmethod
    def build(cls, root: _Element) -> "StyleIndex":
        """Read every ``<style>`` block of the document."""
        index = cls(root)
        for style in root.iter("style"):
            if style.get("id") == STYLE_ID:
                continue  # our own earlier output is not the page's design
            media = (style.get("media") or "all").strip().lower()
            if media not in _SKIPPED_MEDIA:
                index.conditional_blocks += 1
                continue
            index._read_sheet(style.text or "")
        index._match_all()
        index._read_variables()
        return index

    # ---- building ------------------------------------------------------

    def _read_sheet(self, text: str) -> None:
        for item in tinycss2.parse_stylesheet(
            text, skip_comments=True, skip_whitespace=True
        ):
            if item.type == "at-rule":
                if item.lower_at_keyword in {"media", "supports", "container"}:
                    self.conditional_blocks += 1
                    if _DARK_SCHEME_RE.search(tinycss2.serialize(item.prelude)):
                        self.dark_variants = True
                        self._read_dark_block(item)
                continue
            if item.type != "qualified-rule":
                continue
            try:
                declarations = parse_declarations(tinycss2.serialize(item.content))
            except ParseFailedError:
                self.skipped_selectors += 1
                continue
            for selector_text in split_top_level(tinycss2.serialize(item.prelude), ","):
                self._add_rule(selector_text, declarations)

    def _read_dark_block(self, item: tinycss2.ast.AtRule) -> None:
        """Collect the custom properties a dark ``@media`` block sets on the root."""
        for inner in tinycss2.parse_rule_list(
            item.content or [], skip_comments=True, skip_whitespace=True
        ):
            if inner.type != "qualified-rule":
                continue
            prelude = tinycss2.serialize(inner.prelude)
            if not any(
                _is_root_selector(part) for part in split_top_level(prelude, ",")
            ):
                continue
            try:
                declarations = parse_declarations(tinycss2.serialize(inner.content))
            except ParseFailedError:
                continue
            self._keep_variables(self.dark_variables, declarations)

    @staticmethod
    def _keep_variables(target: dict[str, str], declarations: dict[str, str]) -> None:
        for name, value in declarations.items():
            if name.startswith("--"):
                target[name] = value.removesuffix("!important").strip()

    def _add_rule(self, selector_text: str, declarations: dict[str, str]) -> None:
        if _DARK_SELECTOR_RE.search(selector_text):
            self.dark_variants = True
            self.dark_selectors.update(_DARK_ATTRIBUTE_RE.findall(selector_text))
            if _is_root_selector(selector_text):
                self._keep_variables(self.dark_variables, declarations)
        try:
            parsed = cssselect.parse(selector_text)[0]
            compiled = CSSSelector(selector_text)
        except (cssselect.SelectorError, cssselect.ExpressionError):
            self.skipped_selectors += 1
            return
        self._rules.append(
            _Rule(
                compiled,
                selector_text,
                parsed.specificity(),
                len(self._rules),
                declarations,
            )
        )

    def _match_all(self) -> None:
        for rule in self._rules:
            for element in cast("list[object]", rule.selector(self.root)):
                if isinstance(element, _Element):
                    self._matches.setdefault(element, []).append(rule)

    def _read_variables(self) -> None:
        """Collect custom properties set on ``:root`` / ``html`` (later wins)."""
        for rule in sorted(self._rules, key=lambda r: (r.specificity, r.order)):
            if rule.text.strip() not in _ROOT_SELECTORS:
                continue
            for name, value in rule.declarations.items():
                if name.startswith("--"):
                    self.variables[name] = value.removesuffix("!important").strip()

    # ---- queries -------------------------------------------------------

    def with_overrides(
        self, overrides: dict[tuple[_Element, str], str]
    ) -> "StyleIndex":
        """Return a view of this index where some values are replaced.

        Used to ask "what would the page look like after these edits?" without
        touching the document.
        """
        view = copy.copy(self)
        view.overrides = dict(overrides)
        view.variables = dict(self.variables)
        for (_, prop), value in overrides.items():
            if prop.startswith("--"):  # a custom property set on the root
                view.variables[prop] = value
        return view

    def declared(self, element: _Element, prop: str) -> str | None:
        """Return the winning declared value (``var()`` resolved) or None."""
        raw = self.declared_raw(element, prop)
        return None if raw is None else self.resolve_variables(raw)

    def declared_raw(self, element: _Element, prop: str) -> str | None:
        """Return the winning declared value before ``var()`` is resolved."""
        replaced = self.overrides.get((element, prop))
        if replaced is not None:
            return replaced
        candidates: list[tuple[tuple[object, ...], str]] = []
        for rule in self._matches.get(element, []):
            value = rule.declarations.get(prop)
            if value is not None:
                key = (
                    value.endswith("!important"),
                    False,
                    rule.specificity,
                    rule.order,
                )
                candidates.append((key, value.removesuffix("!important").strip()))
        inline = element.get("style")
        if inline:
            try:
                value = parse_declarations(inline).get(prop)
            except ParseFailedError:
                value = None
            if value is not None:
                key = (value.endswith("!important"), True, (1, 0, 0), 0)
                candidates.append((key, value.removesuffix("!important").strip()))
        if not candidates:
            return None
        return max(candidates, key=lambda pair: pair[0])[1]

    def resolve_variables(self, value: str) -> str | None:
        """Replace ``var(--x, fallback)``; None if a variable is unknown."""
        for _ in range(8):  # nested references
            if "var(" not in value:
                return value
            failed = False

            def swap(match: re.Match[str]) -> str:
                nonlocal failed
                found = self.variables.get(match.group(1), match.group(2))
                if found is None:
                    failed = True
                    return match.group(0)
                return found.strip()

            value = _VAR_RE.sub(swap, value)
            if failed:
                return None
        return None

    def background_color(self, element: _Element) -> Color | None:
        """Return the opaque colour behind an element, or None if unknown."""
        return self.background_with_source(element)[0]

    def background_with_source(
        self, element: _Element
    ) -> tuple[Color | None, _Element | None]:
        """Return the opaque colour behind an element and the element that set it.

        Walks up the ancestors. A gradient, image or unresolvable value means
        unknown. Semi-transparent colours are blended with what is underneath.
        Reaching the top with nothing set gives the browser default (white).
        """
        translucent: list[Color] = []
        source: _Element | None = None
        node: _Element | None = element
        base: Color | None = Color(255, 255, 255)
        while node is not None:
            result = self._own_background(node)
            if result is _UNKNOWN:
                return None, node
            if isinstance(result, Color):
                if source is None:
                    source = node
                if result.a >= 1.0:
                    base = result
                    break
                translucent.append(result)
            node = node.getparent()
        for color in reversed(translucent):
            base = color.over(base) if base else None
        return base, source

    def text_color(self, element: _Element) -> tuple[Color | None, _Element | None]:
        """Return the text colour of an element and the element that set it.

        ``color`` is inherited. Unresolvable values give ``None`` (unknown); no
        declaration at all gives the browser default (black).
        """
        node: _Element | None = element
        while node is not None:
            raw = self.declared_raw(node, "color")
            if raw is not None:
                value = self.resolve_variables(raw)
                if value is None:
                    return None, node
                if value.strip().lower() in _INHERITING_COLORS:
                    node = node.getparent()
                    continue
                try:
                    return parse_color(value), node
                except InvalidInputError:
                    return None, node
            node = node.getparent()
        return Color(0, 0, 0), None

    def _own_background(self, element: _Element) -> "Color | None | object":
        for prop in ("background-color", "background"):
            raw = self.declared_raw(element, prop)
            value = None if raw is None else self.resolve_variables(raw)
            if raw is not None and value is None:
                return _UNKNOWN  # set, but we cannot resolve it: unknown, not white
            if value is None:
                if prop == "background-color" and element.get("bgcolor"):
                    return _parse_or_unknown(element.get("bgcolor") or "")
                continue
            if "gradient(" in value or "url(" in value:
                return _UNKNOWN
            match = _COLOR_IN_VALUE.search(value) if prop == "background" else None
            text = match.group(0) if match else value
            return _parse_or_unknown(text)
        if element.get("bgcolor"):
            return _parse_or_unknown(element.get("bgcolor") or "")
        return None


_UNKNOWN: Final = object()
_ROOT_START_RE: Final = re.compile(r"^(?::root|html)(?![\w-])")


def _is_root_selector(selector: str) -> bool:
    """True for ``:root`` / ``html`` with optional attribute or :not() parts."""
    return bool(_ROOT_START_RE.match(selector.strip()))


def _parse_or_unknown(text: str) -> "Color | None | object":
    """Parse a colour; transparent means 'look further up', failure means unknown."""
    try:
        color = parse_color(text)
    except InvalidInputError:
        return _UNKNOWN
    return None if color.a == 0 else color
