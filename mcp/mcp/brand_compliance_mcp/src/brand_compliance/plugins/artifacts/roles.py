"""Label HTML elements with roles from ``config/roles.toml``."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from lxml.cssselect import CSSSelector
from lxml.html import HtmlElement
from pydantic import BaseModel

from brand_compliance.core.errors import InvalidInputError
from brand_compliance.core.settings import DEFAULT_CONFIG_FILE
from brand_compliance.plugins.artifacts.base import (
    describe_element,
    element_path,
    has_own_text,
    is_content_element,
)

DEFAULT_ROLES_FILE: Final = DEFAULT_CONFIG_FILE.parent / "roles.toml"


class RoleRule(BaseModel):
    """One entry of ``roles.toml``."""

    role: str
    selector: str


@dataclass(frozen=True)
class RoleMap:
    """Roles found in a document and the text elements nobody mapped."""

    roles: dict[str, str]
    elements: dict[str, HtmlElement]
    unmapped: list[str]


def load_role_rules(path: Path | None = None) -> list[RoleRule]:
    """Read the role rules (default ``config/roles.toml``)."""
    source = path or DEFAULT_ROLES_FILE
    try:
        raw = tomllib.loads(source.read_text(encoding="utf-8"))
        return [RoleRule(**entry) for entry in raw.get("roles", [])]
    except (OSError, tomllib.TOMLDecodeError, TypeError, ValueError) as exc:
        raise InvalidInputError(f"Cannot read roles {source.name}: {exc}") from exc


def load_role_aliases(path: Path | None = None) -> dict[str, str]:
    """Read ``[[aliases]]``: rule role -> element role (default roles.toml)."""
    source = path or DEFAULT_ROLES_FILE
    try:
        raw = tomllib.loads(source.read_text(encoding="utf-8"))
        return {a["rule_role"]: a["element_role"] for a in raw.get("aliases", [])}
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        raise InvalidInputError(
            f"Cannot read role aliases {source.name}: {exc}"
        ) from exc


def map_roles(root: HtmlElement, rules: list[RoleRule]) -> RoleMap:
    """Assign each content element its first matching role."""
    assigned: dict[HtmlElement, str] = {}
    for rule in rules:
        for element in cast("list[object]", CSSSelector(rule.selector)(root)):
            if (
                isinstance(element, HtmlElement)
                and element not in assigned
                and is_content_element(element)
            ):
                assigned[element] = rule.role
    roles = {element_path(el): role for el, role in assigned.items()}
    elements = {element_path(el): el for el in assigned}
    unmapped = [
        f"{element_path(el)} {describe_element(el)}"
        for el in root.iter()
        if isinstance(el, HtmlElement)
        and is_content_element(el)
        and el not in assigned
        and has_own_text(el)
    ]
    return RoleMap(roles=roles, elements=elements, unmapped=unmapped)
