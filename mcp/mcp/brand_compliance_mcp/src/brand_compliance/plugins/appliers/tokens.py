"""Applier that points a page's own colour variables at the guide's palette."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from brand_compliance.core.errors import InvalidInputError
from brand_compliance.models.artifact import ArtifactModel, ArtifactType
from brand_compliance.models.change import ApplyResult, Change
from brand_compliance.models.rule import Rule

DEFAULT_TOKEN_MAP_FILE: Final = (
    Path(__file__).resolve().parents[4] / "config" / "token_map.toml"
)
ROOT_PATH: Final = "/html"
_SURFACES: Final = ("light", "dark")


@dataclass(frozen=True)
class TokenMap:
    """One page variable and the guide token it takes on each surface."""

    variable: str
    light: str | None = None
    dark: str | None = None

    def token_for(self, surface: str) -> str | None:
        """The guide token for a surface, if the map names one."""
        return self.light if surface == "light" else self.dark


class TokenApplier:
    """Plans ``--page-variable: <brand colour>`` edits from palette token rules.

    It is passive: a palette token that no map uses stays a plain reference
    definition. Emails have no custom properties, so they are left alone.
    """

    name = "token"
    categories = frozenset({"color_token"})
    passive = True

    def __init__(self, maps: list[TokenMap] | None = None) -> None:
        self._maps = maps or []

    def plan(self, rule: Rule, artifact: ArtifactModel) -> ApplyResult:
        """Return the variable overrides that use this palette token."""
        result = ApplyResult()
        if artifact.artifact_type is not ArtifactType.STATIC or not (
            rule.property and rule.value and artifact.styles
        ):
            return result
        styles = artifact.styles
        for entry in self._maps:
            for surface in _SURFACES:
                if entry.token_for(surface) != rule.property:
                    continue
                if surface == "dark" and not styles.dark_variants:
                    continue
                known = (
                    styles.variables if surface == "light" else styles.dark_variables
                )
                if entry.variable not in known:
                    continue
                result.changes.append(
                    Change(
                        id=f"{rule.id}/{entry.variable}/{surface}",
                        rule_id=rule.id,
                        location=ROOT_PATH,
                        property=entry.variable,
                        before=known[entry.variable],
                        after=rule.value,
                        surface=surface,
                        note=f"Page colour variable now uses {rule.property}",
                    )
                )
        return result


def load_token_maps(path: Path | None = None) -> list[TokenMap]:
    """Read ``[[maps]]`` from ``config/token_map.toml`` (or a given file)."""
    source = path or DEFAULT_TOKEN_MAP_FILE
    try:
        raw = tomllib.loads(source.read_text(encoding="utf-8"))
        return [
            TokenMap(m["variable"], m.get("light"), m.get("dark"))
            for m in raw.get("maps", [])
        ]
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        raise InvalidInputError(f"Cannot read token map {source.name}: {exc}") from exc
