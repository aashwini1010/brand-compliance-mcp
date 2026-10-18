"""What an artifact type can display, and how to adapt a value to it.

Only email needs this today. The table lives in ``config/email_support.toml``.
"""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pydantic import BaseModel, Field

from brand_compliance.core.color import parse_color
from brand_compliance.core.errors import InvalidInputError
from brand_compliance.core.settings import DEFAULT_CONFIG_FILE
from brand_compliance.core.units import format_px, to_px

DEFAULT_EMAIL_SUPPORT_FILE: Final = DEFAULT_CONFIG_FILE.parent / "email_support.toml"
_REM: Final = re.compile(r"(?P<number>-?\d*\.?\d+)rem\b")


class UnsupportedValue(BaseModel):
    """A value fragment email clients cannot handle."""

    pattern: str
    reason: str


class UnsupportedProperty(BaseModel):
    """A property email clients cannot handle."""

    property: str
    reason: str


class PartialProperty(BaseModel):
    """A property some clients ignore; it is still applied, with a note."""

    property: str
    note: str


class EmailSupport(BaseModel):
    """The email support table."""

    rem_base_px: float = Field(default=16.0, gt=0)
    unsupported_values: list[UnsupportedValue] = Field(default_factory=list)
    unsupported_properties: list[UnsupportedProperty] = Field(default_factory=list)
    partial_properties: list[PartialProperty] = Field(default_factory=list)

    def adapt(self, prop: str, value: str) -> "Adaptation":
        """Return the value to write for an email, or why it cannot be written."""
        lowered = value.lower()
        for unsupported in self.unsupported_properties:
            if unsupported.property == prop:
                return Adaptation(None, unsupported.reason, None, prop)
        for fragment in self.unsupported_values:
            if fragment.pattern in lowered:
                return Adaptation(None, fragment.reason, None, prop)
        adapted, notes = self._convert_rem(value)
        target = prop
        if prop == "background" and _is_plain_color(adapted):
            target = "background-color"  # Outlook is unreliable with the shorthand
            notes.append("written as background-color for email clients")
        for partial in self.partial_properties:
            if partial.property == target:
                notes.append(partial.note)
        return Adaptation(adapted, None, "; ".join(notes) or None, target)

    def _convert_rem(self, value: str) -> tuple[str, list[str]]:
        if "rem" not in value:
            return value, []

        def swap(match: re.Match[str]) -> str:
            pixels = to_px(match.group(0), self.rem_base_px)
            return format_px(pixels)

        converted = _REM.sub(swap, value)
        return converted, [f"rem converted to px (1rem = {self.rem_base_px:g}px)"]


@dataclass(frozen=True)
class Adaptation:
    """Outcome of adapting a value: the value to write, or why it cannot be used."""

    value: str | None
    rejected_because: str | None
    note: str | None
    property: str = ""


def _is_plain_color(value: str) -> bool:
    try:
        parse_color(value)
    except InvalidInputError:
        return False
    return True


def load_email_support(path: Path | None = None) -> EmailSupport:
    """Read ``config/email_support.toml`` (or a given file)."""
    source = path or DEFAULT_EMAIL_SUPPORT_FILE
    try:
        raw = tomllib.loads(source.read_text(encoding="utf-8"))
        return EmailSupport(
            rem_base_px=raw.get("settings", {}).get("rem_base_px", 16.0),
            unsupported_values=raw.get("unsupported_values", []),
            unsupported_properties=raw.get("unsupported_properties", []),
            partial_properties=raw.get("partial_properties", []),
        )
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        raise InvalidInputError(
            f"Cannot read email support {source.name}: {exc}"
        ) from exc
