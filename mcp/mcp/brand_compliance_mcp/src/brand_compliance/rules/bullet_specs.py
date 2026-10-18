"""Read ``Label: value`` bullet specs (one reader per kind in the vocabulary).

Anything a reader cannot understand becomes its own ``could_not_interpret``
rule; nothing is guessed.
"""

import re
from collections.abc import Callable
from typing import Final

from brand_compliance.core.css import parse_declarations
from brand_compliance.core.errors import ParseFailedError
from brand_compliance.core.text import split_top_level
from brand_compliance.models.rule import Rule, RuleCandidate, RuleStatus, Scope
from brand_compliance.rules.context import Context
from brand_compliance.rules.vocabulary import BulletSpec

Reader = Callable[[RuleCandidate, BulletSpec, str, Context], list[Rule]]

_LENGTH: Final = r"-?\d*\.?\d+(?:px|rem|em)?"
_RADIUS: Final = re.compile(r"^(?P<name>[\w-]+) \((?P<token>--[\w-]+)\)(?P<rest>.*)$")
_SIZE_PADDING: Final = re.compile(r"^(?P<pad>[\d\w ]+?) \((?P<size>\w+)\)$")
_PADDING_AXES: Final = re.compile(
    rf"^(?P<v>{_LENGTH}) vertical, (?P<h>{_LENGTH}) horizontal$"
)
_FAMILY_WEIGHT: Final = re.compile(r"^(?P<family>[A-Z][A-Za-z]+) (?P<weight>[1-9]00)$")
_LETTER_SPACING: Final = re.compile(
    r"^(?P<value>[+-]?\d*\.?\d+(?:em|px|rem)) letter-spacing$"
)
_FONT_SIZE: Final = re.compile(r"^(?P<value>\d*\.?\d+(?:px|rem|em))$")
_COLOR_FRAGMENT: Final = re.compile(r"^color (?P<value>.+)$")
_FONT_TOKEN: Final = re.compile(r"^--fs-[\w-]+$")
_BOX_KEYS: Final = {
    "border becomes": "border",
    "background": "background",
    "border": "border",
    "text": "color",
    "ring": "box-shadow",
}
_BOX_PAIR: Final = re.compile(
    rf"^(?P<key>{'|'.join(sorted(_BOX_KEYS, key=len, reverse=True))}) (?P<value>.+)$"
)


def _rule(
    candidate: RuleCandidate,
    spec: BulletSpec,
    suffix: str,
    role: str | None = None,
    category: str = "component_spec",
    **fields: object,
) -> Rule:
    return Rule(
        id=f"{candidate.id}#{suffix}",
        category=category,
        target_role=role or spec.role,
        source_span=candidate.span,
        **fields,  # type: ignore[arg-type]
    )


def _unreadable(
    candidate: RuleCandidate, spec: BulletSpec, suffix: str, fragment: str, why: str
) -> Rule:
    return _rule(
        candidate,
        spec,
        suffix,
        value=fragment,
        status=RuleStatus.UNINTERPRETABLE,
        reason=f"{spec.section} '{candidate.hints['label']}': {why}",
    )


def _radius_variable(
    candidate: RuleCandidate, spec: BulletSpec, value: str, ctx: Context
) -> list[Rule]:
    match = _RADIUS.match(value)
    if match is None:
        return [_unreadable(candidate, spec, "radius", value, "shape not understood")]
    radius = ctx.variables.get(match["token"])
    if radius is None:
        return [
            _unreadable(
                candidate, spec, "radius", value, f"{match['token']} is not defined"
            )
        ]
    rest = match["rest"].strip(" ;.")
    notes = [f"Not applied: {rest}"] if rest else []
    return [
        _rule(
            candidate,
            spec,
            "radius",
            property="border-radius",
            value=radius,
            notes=notes,
        )
    ]


def _size_padding(
    candidate: RuleCandidate, spec: BulletSpec, value: str, _ctx: Context
) -> list[Rule]:
    rules: list[Rule] = []
    for index, piece in enumerate(split_top_level(value, ";")):
        match = _SIZE_PADDING.match(piece)
        if match is None:
            rules.append(
                _unreadable(
                    candidate, spec, f"pad{index}", piece, "size not understood"
                )
            )
            continue
        size = match["size"].lower()
        rules.append(
            _rule(
                candidate,
                spec,
                size,
                role=f"{spec.role}.{size}",
                property="padding",
                value=match["pad"].strip(),
                notes=["Applies only when the artifact marks the button size"],
            )
        )
    return rules


def _padding_axes(
    candidate: RuleCandidate, spec: BulletSpec, value: str, _ctx: Context
) -> list[Rule]:
    match = _PADDING_AXES.match(value)
    if match is None:
        return [
            _unreadable(candidate, spec, "padding", value, "padding not understood")
        ]
    return [
        _rule(
            candidate,
            spec,
            "padding",
            property="padding",
            value=f"{match['v']} {match['h']}",
        )
    ]


def _declarations(
    candidate: RuleCandidate, spec: BulletSpec, value: str, _ctx: Context
) -> list[Rule]:
    try:
        declarations = parse_declarations(value)
    except ParseFailedError as exc:
        return [_unreadable(candidate, spec, "css", value, str(exc))]
    return [
        _rule(candidate, spec, name, property=name, value=text)
        for name, text in declarations.items()
    ]


def _box_pairs(
    candidate: RuleCandidate, spec: BulletSpec, value: str, ctx: Context
) -> list[Rule]:
    rules: list[Rule] = []
    label = candidate.hints["label"].lower()
    for index, piece in enumerate(split_top_level(value)):
        match = _BOX_PAIR.match(piece)
        if match is None and index == 0 and label in _BOX_KEYS:
            match = _BOX_PAIR.match(f"{label} {piece}")  # the label names the key
        if match is None:
            rules.append(
                _unreadable(candidate, spec, f"part{index}", piece, "not understood")
            )
            continue
        prop = _BOX_KEYS[match["key"]]
        resolved = _box_value(prop, match["value"], ctx)
        if resolved is None:
            rules.append(
                _unreadable(
                    candidate, spec, f"part{index}", piece, f"cannot resolve {prop}"
                )
            )
            continue
        rules.append(_rule(candidate, spec, prop, property=prop, value=resolved))
    return rules


def _box_value(prop: str, raw: str, ctx: Context) -> str | None:
    if prop == "border":
        return ctx.resolve_border(raw)
    if prop == "box-shadow":
        return ctx.resolve_shadow(raw)
    resolved = ctx.resolve_value(raw)
    return resolved[0][1] if resolved and len(resolved) == 1 else ctx.resolve_color(raw)


def _family_value(family: str, ctx: Context) -> str:
    """Use the guide's full font stack when the bullet names its main family."""
    if ctx.font_stack and ctx.font_family == family:
        return ctx.font_stack
    return family


def _font_spec(
    candidate: RuleCandidate, spec: BulletSpec, value: str, ctx: Context
) -> list[Rule]:
    rules: list[Rule] = []
    notes: list[str] = []
    for index, piece in enumerate(split_top_level(value.rstrip("."))):
        suffix = f"part{index}"
        if match := _FAMILY_WEIGHT.match(piece):
            rules.append(
                _rule(
                    candidate,
                    spec,
                    f"{suffix}a",
                    property="font-family",
                    value=_family_value(match["family"], ctx),
                )
            )
            rules.append(
                _rule(
                    candidate,
                    spec,
                    f"{suffix}b",
                    property="font-weight",
                    value=match["weight"],
                )
            )
        elif match := _LETTER_SPACING.match(piece):
            rules.append(
                _rule(
                    candidate,
                    spec,
                    suffix,
                    property="letter-spacing",
                    value=match["value"].lstrip("+"),
                )
            )
        elif match := _FONT_SIZE.match(piece):
            rules.append(
                _rule(
                    candidate, spec, suffix, property="font-size", value=match["value"]
                )
            )
        elif match := _COLOR_FRAGMENT.match(piece):
            color = ctx.resolve_color(match["value"])
            rules.append(
                _rule(candidate, spec, suffix, property="color", value=color)
                if color
                else _unreadable(
                    candidate, spec, suffix, piece, "colour not understood"
                )
            )
        elif _FONT_TOKEN.match(piece) and piece in ctx.vocabulary.type_token_roles:
            role = ctx.vocabulary.type_token_roles[piece]
            notes.append(f"Font size comes from {piece} (see rules for {role})")
        else:
            rules.append(
                _unreadable(candidate, spec, suffix, piece, "instruction not supported")
            )
    for rule in rules:
        if rule.status is RuleStatus.PENDING:
            rule.notes.extend(notes)
    return rules


_ALL_CAPS: Final = re.compile(r"^ALL CAPS$")
_WEIGHT: Final = re.compile(r"^(?:weight |Regular \()(?P<w>[1-9]00)\)?$")
_LINE_HEIGHT: Final = re.compile(r"^line-height (?P<v>\d*\.?\d+)$")
_SPACING: Final = re.compile(r"^letter-spacing (?P<v>[+-]?\d*\.?\d+em)$")
_COLOR_ON: Final = re.compile(r"(?P<token>--[\w-]+)\s+on\s+(?P<surface>light|dark)")


def _text_style(
    candidate: RuleCandidate, spec: BulletSpec, value: str, ctx: Context
) -> list[Rule]:
    rules: list[Rule] = []
    for index, piece in enumerate(split_top_level(value)):
        suffix = f"part{index}"
        simple = _simple_text_property(piece)
        pairs = _COLOR_ON.findall(piece)
        if simple is not None:
            prop, text = simple
            rules.append(
                _rule(
                    candidate,
                    spec,
                    suffix,
                    category="typography",
                    property=prop,
                    value=text,
                )
            )
        elif pairs:
            rules.extend(_scoped_colors(candidate, spec, suffix, pairs, ctx))
        else:
            rules.append(
                _unreadable(candidate, spec, suffix, piece, "not a single value")
            )
    return rules


def _simple_text_property(piece: str) -> tuple[str, str] | None:
    if _ALL_CAPS.match(piece):
        return "text-transform", "uppercase"
    if match := _WEIGHT.match(piece):
        return "font-weight", match["w"]
    if match := _LINE_HEIGHT.match(piece):
        return "line-height", match["v"]
    if match := _SPACING.match(piece):
        return "letter-spacing", match["v"].lstrip("+")
    return None


def _scoped_colors(
    candidate: RuleCandidate,
    spec: BulletSpec,
    suffix: str,
    pairs: list[tuple[str, str]],
    ctx: Context,
) -> list[Rule]:
    rules: list[Rule] = []
    for token, surface in pairs:
        color = ctx.palette.get(token)
        if color is None:
            rules.append(
                _unreadable(
                    candidate,
                    spec,
                    f"{suffix}{surface}",
                    token,
                    "colour is not defined",
                )
            )
            continue
        rules.append(
            _rule(
                candidate,
                spec,
                f"{suffix}{surface}",
                category="color",
                property="color",
                value=color,
                scope=Scope(surface),
            )
        )
    return rules


def _variants_unresolved(
    candidate: RuleCandidate, spec: BulletSpec, value: str, _ctx: Context
) -> list[Rule]:
    return [
        _unreadable(
            candidate,
            spec,
            "choice",
            value,
            "gives alternatives with no rule for choosing between them",
        )
    ]


_READERS: Final[dict[str, Reader]] = {
    "radius_variable": _radius_variable,
    "size_padding": _size_padding,
    "padding_axes": _padding_axes,
    "declarations": _declarations,
    "box_pairs": _box_pairs,
    "font_spec": _font_spec,
    "text_style": _text_style,
    "variants_unresolved": _variants_unresolved,
}


def interpret_bullet(
    candidate: RuleCandidate, spec: BulletSpec, ctx: Context
) -> list[Rule]:
    """Return the rules a bullet spec describes."""
    value = candidate.hints["value"].strip().removesuffix(".").strip()
    return _READERS[spec.kind](candidate, spec, value, ctx)
