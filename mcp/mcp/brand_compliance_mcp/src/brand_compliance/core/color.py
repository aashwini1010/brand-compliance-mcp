"""Read CSS colours into one standard form.

Unknown notations raise ``InvalidInputError``; a colour is never guessed.
"""

import colorsys
import re
from dataclasses import dataclass
from typing import Final

from brand_compliance.core.errors import InvalidInputError

_HEX_RE: Final = re.compile(r"^#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$")
_FUNC_RE: Final = re.compile(r"^(rgba?|hsla?)\(([^)]*)\)$")

_NAMED: Final[dict[str, str]] = {
    "white": "#ffffff",
    "black": "#000000",
    "transparent": "#00000000",
}


@dataclass(frozen=True)
class Color:
    """An RGB colour with alpha (0.0 transparent to 1.0 opaque)."""

    r: int
    g: int
    b: int
    a: float = 1.0

    def to_hex(self) -> str:
        """Return ``#rrggbb``, or ``#rrggbbaa`` when not fully opaque."""
        base = f"#{self.r:02x}{self.g:02x}{self.b:02x}"
        if self.a >= 1.0:
            return base
        return f"{base}{round(self.a * 255):02x}"

    def over(self, background: "Color") -> "Color":
        """Return this colour blended on top of an opaque background."""
        a = self.a
        return Color(
            round(self.r * a + background.r * (1 - a)),
            round(self.g * a + background.g * (1 - a)),
            round(self.b * a + background.b * (1 - a)),
        )


def parse_color(text: str) -> Color:
    """Parse a hex, rgb(a), hsl(a) or supported named colour."""
    value = text.strip().lower()
    value = _NAMED.get(value, value)
    if hex_match := _HEX_RE.match(value):
        return _from_hex(hex_match.group(1))
    if func_match := _FUNC_RE.match(value):
        return _from_function(func_match.group(1), func_match.group(2), text)
    raise InvalidInputError(f"Unrecognised colour: {text!r}")


def _from_hex(digits: str) -> Color:
    if len(digits) in (3, 4):
        digits = "".join(ch * 2 for ch in digits)
    alpha = int(digits[6:8], 16) / 255 if len(digits) == 8 else 1.0
    return Color(
        int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16), alpha
    )


def _from_function(name: str, args: str, original: str) -> Color:
    parts = [p for p in re.split(r"[\s,/]+", args.strip()) if p]
    if len(parts) not in (3, 4):
        raise InvalidInputError(f"Unrecognised colour: {original!r}")
    try:
        alpha = _parse_alpha(parts[3]) if len(parts) == 4 else 1.0
        if name.startswith("rgb"):
            r, g, b = (_parse_channel(p) for p in parts[:3])
            return Color(r, g, b, alpha)
        return _from_hsl(parts[0], parts[1], parts[2], alpha)
    except ValueError as exc:
        raise InvalidInputError(f"Unrecognised colour: {original!r}") from exc


def _parse_channel(part: str) -> int:
    value = float(part[:-1]) * 2.55 if part.endswith("%") else float(part)
    return max(0, min(255, round(value)))


def _parse_alpha(part: str) -> float:
    value = float(part[:-1]) / 100 if part.endswith("%") else float(part)
    return max(0.0, min(1.0, value))


def _from_hsl(h: str, s: str, light: str, alpha: float) -> Color:
    hue = float(h.removesuffix("deg")) % 360 / 360
    sat = float(s.removesuffix("%")) / 100
    lum = float(light.removesuffix("%")) / 100
    r, g, b = colorsys.hls_to_rgb(hue, lum, sat)
    return Color(round(r * 255), round(g * 255), round(b * 255), alpha)
