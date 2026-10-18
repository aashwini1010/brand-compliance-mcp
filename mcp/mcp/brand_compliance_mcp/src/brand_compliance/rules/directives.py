"""Interpret directive sentences. Unsupported shapes return no rules."""

import re
from collections.abc import Callable
from typing import Final

from brand_compliance.models.rule import Rule, RuleCandidate, RuleStatus, Severity
from brand_compliance.rules.context import TOKEN_RE, Context

Handler = Callable[[RuleCandidate, re.Match[str], str, Context], list[Rule]]

_FORBID_COLOR: Final = re.compile(
    r"never use (?P<colors>.+?) as (?P<role>.+?) on (?P<surfaces>.+?)(?: — |\. |$)",
    re.IGNORECASE,
)
_CONTRAST: Final = re.compile(r"contrast ratio\D*?(?P<ratio>\d+(?:\.\d+)?):1", re.I)
_FONT_ONLY: Final = re.compile(r"use (?P<font>[A-Za-z][\w ]*?) exclusively", re.I)
_FONT_EXCEPTION: Final = re.compile(
    r"the (?P<font>[A-Z][A-Za-z]+) handwriting only appears in "
    r"(?P<where>.+?),? never customer-facing",
    re.IGNORECASE,
)
_FOCUS_PROMPT: Final = re.compile(
    r"focus ring (?P<outline>\d*\.?\d+px solid #[0-9a-f]{3,8}) "
    r"with (?P<offset>\d*\.?\d+(?:px|rem|em)?) offset",
    re.IGNORECASE,
)
_NO_OTHER_FONTS: Final = re.compile(r"no other font famil", re.IGNORECASE)
_DEFAULT_SURFACE: Final = re.compile(r"default surface is (?P<token>--[\w-]+)", re.I)
_FOCUS_RING: Final = re.compile(
    r"focus ring: outline: (?P<outline>[^;]+); "
    r"outline-offset: (?P<offset>\d*\.?\d+(?:px|rem|em)?)",
    re.IGNORECASE,
)


def _rule(candidate: RuleCandidate, suffix: str, **fields: object) -> Rule:
    """Build a pending rule from a candidate with the given fields."""
    return Rule(
        id=f"{candidate.id}#{suffix}",
        source_span=candidate.span,
        status=RuleStatus.PENDING,
        **fields,  # type: ignore[arg-type]
    )


def _forbid_color(
    candidate: RuleCandidate, match: re.Match[str], _text: str, ctx: Context
) -> list[Rule]:
    colors = TOKEN_RE.findall(match["colors"])
    role = ctx.vocabulary.role_phrases.get(match["role"].strip().lower())
    scope = ctx.scope_from_surfaces(match["surfaces"])
    if not colors or role is None or scope is None:
        return []
    if any(color not in ctx.palette for color in colors):
        return []
    return [
        _rule(
            candidate,
            color,
            category="forbid_color",
            target_role=role,
            property="color",
            value=ctx.palette[color],
            scope=scope,
            severity=Severity.HARD,
        )
        for color in colors
    ]


def _contrast(
    candidate: RuleCandidate, match: re.Match[str], text: str, ctx: Context
) -> list[Rule]:
    return [
        _rule(
            candidate,
            "contrast",
            category="min_contrast",
            target_role=ctx.find_role(text),
            property="contrast-ratio",
            value=match["ratio"],
            severity=Severity.HARD,
        )
    ]


def _font_only(
    candidate: RuleCandidate, match: re.Match[str], _text: str, _ctx: Context
) -> list[Rule]:
    return [
        _rule(
            candidate,
            "font",
            category="font_only",
            property="font-family",
            value=match["font"].strip(),
            severity=Severity.HARD,
        )
    ]


def _no_other_fonts(
    candidate: RuleCandidate, _match: re.Match[str], _text: str, ctx: Context
) -> list[Rule]:
    if ctx.font_family is None:
        return []
    return [
        _rule(
            candidate,
            "font",
            category="font_only",
            property="font-family",
            value=ctx.font_family,
            severity=Severity.HARD,
        )
    ]


def _font_exception(
    candidate: RuleCandidate, match: re.Match[str], _text: str, _ctx: Context
) -> list[Rule]:
    return [
        _rule(
            candidate,
            "exception",
            category="font_exception",
            property="font-family",
            value=match["font"],
            notes=[f"The guide limits it to: {match['where']}"],
        )
    ]


def _default_surface(
    candidate: RuleCandidate, match: re.Match[str], _text: str, ctx: Context
) -> list[Rule]:
    value = ctx.palette.get(match["token"])
    if value is None:
        return []
    return [
        _rule(
            candidate,
            "surface",
            category="surface",
            target_role="page.surface",
            property="background",
            value=value,
        )
    ]


def _focus_ring(
    candidate: RuleCandidate, match: re.Match[str], _text: str, ctx: Context
) -> list[Rule]:
    outline = ctx.replace_tokens(match["outline"].strip())
    if outline is None:
        return []
    return [
        _rule(
            candidate,
            name,
            category="focus",
            target_role="interactive.focus",
            property=name,
            value=value,
            severity=Severity.HARD,
        )
        for name, value in (("outline", outline), ("outline-offset", match["offset"]))
    ]


def _focus_prompt(
    candidate: RuleCandidate, match: re.Match[str], _text: str, ctx: Context
) -> list[Rule]:
    outline = ctx.replace_tokens(match["outline"].lower())
    if outline is None:
        return []
    return [
        _rule(
            candidate,
            name,
            category="focus",
            target_role="interactive.focus",
            property=name,
            value=value,
            severity=Severity.HARD,
        )
        for name, value in (("outline", outline), ("outline-offset", match["offset"]))
    ]


def _forbid_effect(candidate: RuleCandidate, text: str, ctx: Context) -> list[Rule]:
    if candidate.hints.get("polarity") != "forbid" or candidate.hints.get("topic"):
        return []  # a topic-specific row (e.g. logo) is not a global rule
    lowered = text.lower()
    effects = [
        effect
        for effect, words in ctx.vocabulary.effect_words.items()
        if any(re.search(rf"\b{re.escape(w)}\b", lowered) for w in words)
    ]
    return [
        _rule(
            candidate,
            effect,
            category="forbid_effect",
            property="effect",
            value=effect,
            severity=Severity.HARD,
        )
        for effect in effects
    ]


_PATTERNS: Final[list[tuple[re.Pattern[str], Handler]]] = [
    (_FORBID_COLOR, _forbid_color),
    (_CONTRAST, _contrast),
    (_FONT_ONLY, _font_only),
    (_NO_OTHER_FONTS, _no_other_fonts),
    (_DEFAULT_SURFACE, _default_surface),
    (_FOCUS_RING, _focus_ring),
    (_FOCUS_PROMPT, _focus_prompt),
    (_FONT_EXCEPTION, _font_exception),
]


def interpret_directive(candidate: RuleCandidate, ctx: Context) -> list[Rule]:
    """Return rules for a directive, or an empty list if its shape is unsupported."""
    text = candidate.hints.get("text", candidate.text)
    for pattern, handler in _PATTERNS:
        match = pattern.search(text)
        if match and (rules := handler(candidate, match, text, ctx)):
            return rules
    return _forbid_effect(candidate, text, ctx)
