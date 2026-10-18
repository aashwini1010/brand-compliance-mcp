"""Convert CSS lengths to pixels so email-safe values can be written."""

import re
from typing import Final

from brand_compliance.core.errors import InvalidInputError

DEFAULT_BASE_PX: Final = 16.0

_LENGTH_RE: Final = re.compile(r"^(-?\d*\.?\d+)(px|rem|em|pt)?$")
_PX_PER_UNIT: Final[dict[str, float]] = {"pt": 96 / 72}


def to_px(length: str, base_px: float = DEFAULT_BASE_PX) -> float:
    """Return a length in pixels.

    Supports ``px``, ``rem``, ``em`` and ``pt`` (a bare ``0`` is allowed).
    Anything else, such as ``clamp()``, ``vw`` or ``%``, raises
    ``InvalidInputError`` because its pixel value depends on the page.
    """
    match = _LENGTH_RE.match(length.strip().lower())
    if match is None:
        raise InvalidInputError(f"Cannot convert to px: {length!r}")
    number = float(match.group(1))
    unit = match.group(2)
    if unit is None:
        if number != 0:
            raise InvalidInputError(f"Length needs a unit: {length!r}")
        return 0.0
    if unit in ("rem", "em"):
        return number * base_px
    return number * _PX_PER_UNIT.get(unit, 1.0)


def format_px(value: float) -> str:
    """Format pixels without a needless decimal, e.g. ``15px`` or ``12.8px``."""
    rounded = round(value, 2)
    text = f"{rounded:g}"
    return f"{text}px"
