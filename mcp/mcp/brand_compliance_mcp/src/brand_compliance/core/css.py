"""Read, write and merge CSS declarations (``prop: value; ...``)."""

import tinycss2
from tinycss2.ast import Declaration

from brand_compliance.core.errors import ParseFailedError


def parse_declarations(style: str) -> dict[str, str]:
    """Parse the text of a ``style`` attribute into ``{property: value}``.

    Property names are lower-cased; ``!important`` is kept on the value.
    Malformed input raises ``ParseFailedError`` instead of being dropped.
    Custom properties (``--name``) keep their original case.
    """
    result: dict[str, str] = {}
    for item in tinycss2.parse_blocks_contents(
        style, skip_comments=True, skip_whitespace=True
    ):
        if item.type == "error":
            raise ParseFailedError(f"Invalid CSS declaration: {item.message}")
        if not isinstance(item, Declaration):
            continue
        name = item.name if item.name.startswith("--") else item.lower_name
        value = tinycss2.serialize(item.value).strip()
        result[name] = f"{value} !important" if item.important else value
    return result


def format_declarations(declarations: dict[str, str]) -> str:
    """Write declarations back as ``a: b; c: d`` (no trailing semicolon)."""
    return "; ".join(f"{name}: {value}" for name, value in declarations.items())


def merge_declarations(
    base: dict[str, str], overrides: dict[str, str]
) -> dict[str, str]:
    """Return ``base`` updated with ``overrides``; neither input is changed."""
    return {**base, **overrides}
