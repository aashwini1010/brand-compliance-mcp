"""Small text helpers shared by extractors."""

import re
from typing import Final

_MARKS_RE: Final = re.compile(r"(\*\*|__|`)")
_SPACES_RE: Final = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Remove Markdown emphasis and code marks and collapse whitespace."""
    text = _SPACES_RE.sub(" ", _MARKS_RE.sub("", text)).strip()
    if len(text) > 2 and text[0] == text[-1] and text[0] in "*_":
        text = text[1:-1].strip()
    return text


def split_top_level(text: str, separators: str = ",;") -> list[str]:
    """Split on separators that are not inside parentheses; trim each piece.

    ``"a, rgba(1,2,3), b"`` gives ``["a", "rgba(1,2,3)", "b"]``.
    """
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char in separators and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    parts.append("".join(current).strip())
    return [part for part in parts if part]
