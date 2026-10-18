"""WCAG 2.x contrast ratio, used to keep text readable."""

from typing import Final

from brand_compliance.core.color import Color

AA_NORMAL_TEXT: Final = 4.5
AA_LARGE_TEXT: Final = 3.0
LIGHT_SURFACE_LUMINANCE: Final = 0.4


def _linear(channel: int) -> float:
    value = channel / 255
    if value <= 0.03928:
        return value / 12.92
    return float(((value + 0.055) / 1.055) ** 2.4)


def relative_luminance(color: Color) -> float:
    """Return the WCAG relative luminance (0 black to 1 white)."""
    return (
        0.2126 * _linear(color.r)
        + 0.7152 * _linear(color.g)
        + 0.0722 * _linear(color.b)
    )


def contrast_ratio(foreground: Color, background: Color) -> float:
    """Return the contrast ratio (1 to 21) of text on its background.

    A translucent foreground is first blended onto the background. The
    background itself must be opaque.
    """
    fg = foreground.over(background) if foreground.a < 1.0 else foreground
    lighter, darker = sorted(
        (relative_luminance(fg), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def meets_aa(foreground: Color, background: Color, *, large_text: bool = False) -> bool:
    """Return True if the pair passes WCAG AA for its text size."""
    threshold = AA_LARGE_TEXT if large_text else AA_NORMAL_TEXT
    return contrast_ratio(foreground, background) >= threshold


def is_light_surface(color: Color) -> bool:
    """Return True if a surface is light enough to be treated as a light theme."""
    return relative_luminance(color) > LIGHT_SURFACE_LUMINANCE
