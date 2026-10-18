"""State and helpers the normalizer carries while interpreting a guide."""

import re
from dataclasses import dataclass, field
from typing import Final

from brand_compliance.core.color import parse_color
from brand_compliance.core.contrast import is_light_surface
from brand_compliance.core.errors import InvalidInputError
from brand_compliance.models.rule import Scope
from brand_compliance.rules.vocabulary import Vocabulary

TOKEN_RE: Final = re.compile(r"--[A-Za-z0-9-]+")
_SURFACE_RE: Final = re.compile(
    r"^(?P<value>.*?)(?:\s*\(on (?P<surface>light|dark)\))?$"
)
_BORDER_RE: Final = re.compile(
    r"^(?P<width>\d*\.?\d+px) (?P<style>solid|dashed|dotted) (?P<color>.+)$",
    re.IGNORECASE,
)
_SHADOW_RE: Final = re.compile(
    r"^(?P<offsets>(?:-?\d*\.?\d+(?:px)? ){3}-?\d*\.?\d+(?:px)?) (?P<color>.+)$"
)


@dataclass
class Context:
    """Vocabulary plus facts learned so far (palette, font family)."""

    vocabulary: Vocabulary
    palette: dict[str, str] = field(default_factory=dict)
    font_family: str | None = None
    font_stack: str | None = None
    variables: dict[str, str] = field(default_factory=dict)

    def scope_for(self, section: str) -> Scope:
        """Return the scope implied by a section title (default: all)."""
        lowered = section.lower()
        for words, scope in self.vocabulary.scope_words.items():
            if words in lowered:
                return Scope(scope)
        return Scope.ALL

    def replace_tokens(self, text: str) -> str | None:
        """Replace every ``--token`` with its hex; None if one is unknown."""
        missing = False

        def swap(match: re.Match[str]) -> str:
            nonlocal missing
            value = self.palette.get(match.group(0))
            if value is None:
                missing = True
                return match.group(0)
            return value

        result = TOKEN_RE.sub(swap, text)
        return None if missing else result

    def resolve_value(self, raw: str) -> list[tuple[Scope, str]] | None:
        """Resolve a table cell into ``[(scope, value)]``; None if not understood.

        Understands tokens, listed keywords, simple borders, and ``(on light)`` /
        ``(on dark)`` alternatives separated by `` / ``.
        """
        results: list[tuple[Scope, str]] = []
        for part in raw.split(" / "):
            match = _SURFACE_RE.match(part.strip())
            if match is None or not match["value"]:
                return None
            value = self._resolve_single(match["value"].strip())
            if value is None:
                return None
            surface = match["surface"]
            results.append((Scope(surface) if surface else Scope.ALL, value))
        return results

    def _resolve_single(self, value: str) -> str | None:
        if value.lower() in self.vocabulary.css_keywords:
            return value.lower()
        if value in self.palette:
            return self.palette[value]
        return self.resolve_border(value)

    def resolve_color(self, text: str) -> str | None:
        """Return a colour as hex: a palette token or a literal colour."""
        text = text.strip()
        if text in self.palette:
            return self.palette[text]
        try:
            return parse_color(text).to_hex()
        except InvalidInputError:
            return None

    def resolve_border(self, text: str) -> str | None:
        """Return ``<width> <style> <colour>`` with the colour resolved, or None."""
        match = _BORDER_RE.match(text.strip())
        if match is None:
            return None
        color = match["color"].strip()
        resolved = (
            color.lower()
            if color.lower() == "currentcolor"
            else self.resolve_color(color)
        )
        if resolved is None:
            return None
        return f"{match['width']} {match['style'].lower()} {resolved}"

    def resolve_shadow(self, text: str) -> str | None:
        """Return ``<x> <y> <blur> <spread> <colour>`` with the colour resolved."""
        match = _SHADOW_RE.match(text.strip())
        if match is None:
            return None
        color = self.resolve_color(match["color"])
        return f"{match['offsets']} {color}" if color else None

    def surface_scope(self, tokens: list[str]) -> Scope | None:
        """Return LIGHT or DARK if all surface tokens agree; otherwise None."""
        scopes: set[Scope] = set()
        for token in tokens:
            hex_value = self.palette.get(token)
            if hex_value is None:
                return None
            try:
                light = is_light_surface(parse_color(hex_value))
            except InvalidInputError:
                return None
            scopes.add(Scope.LIGHT if light else Scope.DARK)
        return scopes.pop() if len(scopes) == 1 else None

    def scope_from_surfaces(self, text: str) -> Scope | None:
        """Scope named by surface tokens, else by a listed phrase; None if unclear."""
        tokens = TOKEN_RE.findall(text)
        if tokens:
            return self.surface_scope(tokens)
        lowered = text.lower()
        for phrase, scope in self.vocabulary.surface_phrases.items():
            if phrase in lowered:
                return Scope(scope)
        return None

    def find_role(self, text: str) -> str | None:
        """Return the role of the first known phrase in ``text``, if any."""
        lowered = text.lower()
        hits = [
            (lowered.index(phrase), role)
            for phrase, role in self.vocabulary.role_phrases.items()
            if phrase in lowered
        ]
        return min(hits)[1] if hits else None
