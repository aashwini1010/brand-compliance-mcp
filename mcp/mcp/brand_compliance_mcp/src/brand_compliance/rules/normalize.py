"""Turn raw candidates into clean rules, each with a status and a reason.

Honesty rule: anything not understood becomes ``could_not_interpret``; the
normalizer never guesses.
"""

import re
from typing import Final

from brand_compliance.core.color import parse_color
from brand_compliance.core.errors import InvalidInputError
from brand_compliance.core.units import to_px
from brand_compliance.models.rule import Rule, RuleCandidate, RuleStatus
from brand_compliance.rules.bullet_specs import interpret_bullet
from brand_compliance.rules.context import Context
from brand_compliance.rules.directives import interpret_directive
from brand_compliance.rules.vocabulary import PhraseStatus, Vocabulary

_SIZE_RE: Final = re.compile(
    r"^(?:clamp\(.+\)|-?\d*\.?\d+(?:px|rem|em|pt|%)|inherit)$", re.IGNORECASE
)
_WEIGHT_RE: Final = re.compile(r"^(?P<weight>\d{3})(?: (?P<style>italic))?$")
_LINE_HEIGHT_RE: Final = re.compile(r"^(?:\d*\.?\d+(?:px|rem|em)?|normal|inherit)$")
_SPACING_RE: Final = re.compile(r"^[+-]?\d*\.?\d+(?:px|rem|em)?$|^normal$|^inherit$")
_COMPONENT_PROPERTIES: Final = {
    "col:background": "background",
    "col:text": "color",
    "col:border": "border",
}
# Whole-number HSL cannot be more precise than this per channel.
_ROUNDING_TOLERANCE: Final = 6
_PX_ANNOTATION_RE: Final = re.compile(r"^(?P<main>.+?) \((?P<px>\d*\.?\d+)px\)$")
_FIRST_PASS: Final = ("palette_row",)
_SECOND_PASS: Final = ("css_declaration", "css_import", "css_unsupported")


def normalize(candidates: list[RuleCandidate], vocabulary: Vocabulary) -> list[Rule]:
    """Return the final rule list for a guide, ordered by guide line."""
    ctx = Context(vocabulary)
    ordered = sorted(candidates, key=lambda c: (c.span.line_start or 0, c.id))
    rules: list[Rule] = []
    for kinds in (_FIRST_PASS, _SECOND_PASS, None):
        for candidate in ordered:
            kind = candidate.hints.get("kind", "")
            in_pass = kind in kinds if kinds else kind not in _FIRST_PASS + _SECOND_PASS
            if in_pass:
                rules.extend(_interpret(candidate, kind, ctx))
    rules = _apply_section_status(rules, vocabulary)
    return _finalize(rules)


def _interpret(candidate: RuleCandidate, kind: str, ctx: Context) -> list[Rule]:
    handlers = {
        "palette_row": _palette,
        "type_row": _typography,
        "component_row": _component,
        "css_declaration": _css_declaration,
        "css_import": _css_import,
        "directive": _directive,
        "bullet_spec": _bullet_spec,
    }
    handler = handlers.get(kind)
    if handler is not None:
        return handler(candidate, ctx)
    reason = {
        "css_unsupported": f"CSS could not be read: {candidate.hints.get('problem')}",
        "unmatched": "No extractor understood this text.",
    }.get(kind, f"Unknown kind of finding: {kind!r}")
    return [_unreadable(candidate, reason)]


def _unreadable(candidate: RuleCandidate, reason: str, **fields: str | None) -> Rule:
    """A rule recording that something was found but not understood."""
    return Rule(
        id=candidate.id,
        category=fields.pop("category", None) or candidate.hints.get("kind", "unknown"),
        value=fields.pop("value", None) or candidate.text,
        source_span=candidate.span,
        status=RuleStatus.UNINTERPRETABLE,
        reason=reason,
        **fields,  # type: ignore[arg-type]
    )


# ---- palette -------------------------------------------------------------


def _palette(candidate: RuleCandidate, ctx: Context) -> list[Rule]:
    hints = candidate.hints
    try:
        color = parse_color(hints["hex"])
    except InvalidInputError:
        return [_unreadable(candidate, f"Unreadable colour {hints['hex']!r}")]
    value = color.to_hex()
    ctx.palette[hints["token"]] = value
    notes = _palette_notes(hints, value)
    return [
        Rule(
            id=candidate.id,
            category="color_token",
            property=hints["token"],
            value=value,
            scope=ctx.scope_for(hints.get("section", "")),
            source_span=candidate.span,
            notes=notes,
            reason=hints.get("use", ""),
        )
    ]


def _channel_gap(first: str, second: str) -> int:
    """Largest difference between two colours' red, green or blue values."""
    a, b = parse_color(first), parse_color(second)
    return max(abs(a.r - b.r), abs(a.g - b.g), abs(a.b - b.b))


def _palette_notes(hints: dict[str, str], hex_value: str) -> list[str]:
    """Note RGB/HSL columns that disagree with hex by more than rounding."""
    notes: list[str] = []
    for column, function in (("rgb", "rgb"), ("hsl", "hsl")):
        text = hints.get(column)
        if not text:
            continue
        try:
            gap = _channel_gap(f"{function}({text})", hex_value)
        except InvalidInputError:
            notes.append(f"{column.upper()} column ({text}) is not readable")
            continue
        if gap > (0 if column == "rgb" else _ROUNDING_TOLERANCE):
            notes.append(
                f"{column.upper()} column ({text}) disagrees with hex {hex_value}; "
                "hex is used"
            )
    return notes


# ---- typography ----------------------------------------------------------


def _typography(candidate: RuleCandidate, ctx: Context) -> list[Rule]:
    hints = candidate.hints
    role = ctx.vocabulary.type_token_roles.get(hints["token"])
    if role is None:
        return [
            _unreadable(candidate, f"No role known for type token {hints['token']!r}")
        ]
    rules: list[Rule] = []
    weight_match = _WEIGHT_RE.match(hints["weight"])
    size, size_notes = _strip_px_annotation(hints["size"])
    checks = (
        ("font-size", size, _SIZE_RE.match(size)),
        ("font-weight", hints["weight"], weight_match),
        (
            "line-height",
            hints["line_height"],
            _LINE_HEIGHT_RE.match(hints["line_height"]),
        ),
        (
            "letter-spacing",
            hints["letter_spacing"],
            _SPACING_RE.match(hints["letter_spacing"]),
        ),
    )
    for prop, raw, ok in checks:
        suffix = f"#{prop}"
        if not ok:
            rules.append(
                _unreadable(
                    candidate,
                    f"Value {raw!r} for {prop} is not understood",
                    category="typography",
                    property=prop,
                    value=raw,
                    target_role=role,
                ).model_copy(update={"id": candidate.id + suffix})
            )
            continue
        value = raw.lstrip("+") if prop == "letter-spacing" else raw
        if prop == "font-weight" and weight_match:
            value = weight_match["weight"]
        rule = _typo_rule(candidate, suffix, role, prop, value)
        if prop == "font-size":
            rule.notes.extend(size_notes)
        rules.append(rule)
        if prop == "font-weight" and weight_match and weight_match["style"]:
            rules.append(
                _typo_rule(candidate, "#font-style", role, "font-style", "italic")
            )
    return rules


def _strip_px_annotation(raw: str) -> tuple[str, list[str]]:
    """Split ``0.9375rem (15px)`` into the value and any disagreement note."""
    match = _PX_ANNOTATION_RE.match(raw)
    if match is None:
        return raw, []
    main = match["main"]
    try:
        agrees = abs(to_px(main) - float(match["px"])) < 0.01
    except InvalidInputError:
        return raw, []
    note = [] if agrees else [f"Annotation ({match['px']}px) disagrees with {main}"]
    return main, note


def _typo_rule(
    candidate: RuleCandidate, suffix: str, role: str, prop: str, value: str
) -> Rule:
    return Rule(
        id=candidate.id + suffix,
        category="typography",
        target_role=role,
        property=prop,
        value=value,
        source_span=candidate.span,
        reason=candidate.hints.get("use", ""),
    )


# ---- components ----------------------------------------------------------


def _component(candidate: RuleCandidate, ctx: Context) -> list[Rule]:
    hints = candidate.hints
    role = ctx.vocabulary.variant_roles.get(hints["variant"].lower())
    if role is None:
        return [
            _unreadable(candidate, f"No role known for variant {hints['variant']!r}")
        ]
    rules: list[Rule] = []
    for key, prop in _COMPONENT_PROPERTIES.items():
        raw = hints.get(key, "")
        resolved = ctx.resolve_value(raw) if raw else None
        if resolved is None:
            rules.append(
                _unreadable(
                    candidate,
                    f"Cannot resolve {prop} value {raw!r}",
                    category="component",
                    property=prop,
                    value=raw,
                    target_role=role,
                ).model_copy(update={"id": f"{candidate.id}#{prop}"})
            )
            continue
        for scope, value in resolved:
            rules.append(
                Rule(
                    id=f"{candidate.id}#{prop}#{scope.value}",
                    category="component",
                    target_role=role,
                    property=prop,
                    value=value,
                    scope=scope,
                    source_span=candidate.span,
                    reason=hints.get("col:use", ""),
                )
            )
    hover = hints.get("col:hover")
    if hover:
        rules.append(
            _unreadable(
                candidate,
                "Hover behaviour is described in prose, not as property values.",
                category="component",
                property="hover",
                value=hover,
                target_role=role,
            ).model_copy(update={"id": f"{candidate.id}#hover"})
        )
    return rules


# ---- CSS -----------------------------------------------------------------


def _css_import(candidate: RuleCandidate, _ctx: Context) -> list[Rule]:
    return [
        Rule(
            id=candidate.id,
            category="font_source",
            property="@import",
            value=candidate.hints["value"],
            source_span=candidate.span,
        )
    ]


def _css_declaration(candidate: RuleCandidate, ctx: Context) -> list[Rule]:
    hints = candidate.hints
    prop, value, selector = hints["property"], hints["value"], hints["selector"]
    if prop.startswith("--"):
        return [_css_variable(candidate, prop, value, ctx)]
    role = ctx.vocabulary.selector_roles.get(selector)
    if role is not None:
        return [
            Rule(
                id=candidate.id,
                category="css_declaration",
                target_role=role,
                property=prop,
                value=value,
                source_span=candidate.span,
                notes=[f"selector {selector}"],
            )
        ]
    why = (
        f"No element role known for selector {selector!r}"
        if selector
        else "CSS has no selector, so the element it targets is unknown"
    )
    return [
        _unreadable(
            candidate, why, category="css_declaration", property=prop, value=value
        )
    ]


def _css_variable(
    candidate: RuleCandidate, prop: str, value: str, ctx: Context
) -> Rule:
    ctx.variables[prop] = value
    if ctx.vocabulary.css_variable_roles.get(prop) == "font_family":
        families = [part.strip().strip("\"'") for part in value.split(",")]
        ctx.font_family = families[0]
        ctx.font_stack = value
        return Rule(
            id=candidate.id,
            category="font_family",
            target_role="document",
            property="font-family",
            value=value,
            source_span=candidate.span,
            notes=[f"defined by {prop}"],
        )
    return Rule(
        id=candidate.id,
        category="css_variable",
        property=prop,
        value=value,
        source_span=candidate.span,
    )


# ---- directives ----------------------------------------------------------


def _directive(candidate: RuleCandidate, ctx: Context) -> list[Rule]:
    rules = interpret_directive(candidate, ctx)
    if rules:
        return rules
    return [
        _unreadable(
            candidate,
            "Directive wording is not one of the supported patterns.",
            category="directive",
            value=candidate.hints.get("text", candidate.text),
        )
    ]


# ---- bullet specs --------------------------------------------------------


def _bullet_spec(candidate: RuleCandidate, ctx: Context) -> list[Rule]:
    hints = candidate.hints
    spec = ctx.vocabulary.find_bullet_spec(hints["section"], hints["label"])
    if spec is None:
        return [_unreadable(candidate, f"No spec known for {hints['label']!r}")]
    return interpret_bullet(candidate, spec, ctx)


# ---- finishing -----------------------------------------------------------


def _apply_section_status(rules: list[Rule], vocabulary: Vocabulary) -> list[Rule]:
    """Re-label unreadable rules the vocabulary explains (by section, then phrase)."""
    phrases = [
        (re.compile("|".join(p.patterns), re.IGNORECASE), p)
        for p in vocabulary.phrase_status
    ]
    result: list[Rule] = []
    for rule in rules:
        if rule.status is RuleStatus.UNINTERPRETABLE:
            update = _section_update(rule, vocabulary) or _phrase_update(rule, phrases)
            if update:
                rule = rule.model_copy(update=update)
        result.append(rule)
    return result


def _section_update(rule: Rule, vocabulary: Vocabulary) -> dict[str, object] | None:
    for section in vocabulary.section_status:
        if any(
            heading.lower().startswith(section.match.lower())
            for heading in rule.source_span.heading_path
        ):
            return {"status": section.status, "reason": section.reason}
    return None


def _phrase_update(
    rule: Rule, phrases: list[tuple[re.Pattern[str], PhraseStatus]]
) -> dict[str, object] | None:
    text = rule.value or ""
    for pattern, phrase in phrases:
        if pattern.search(text):
            return {"status": phrase.status, "reason": phrase.reason}
    return None


def _finalize(rules: list[Rule]) -> list[Rule]:
    """Merge identical rules, order by guide line and number them R001, R002..."""
    ordered = sorted(
        enumerate(rules),
        key=lambda pair: (pair[1].source_span.line_start or 0, pair[0]),
    )
    merged: dict[tuple[object, ...], Rule] = {}
    for _, rule in ordered:
        key = (
            rule.category,
            rule.target_role,
            rule.property,
            rule.value,
            rule.scope,
            rule.status,
        )
        if key in merged and rule.status is RuleStatus.PENDING:
            merged[key].notes.append(f"Also stated at {rule.source_span.describe()}")
        else:
            merged[key if rule.status is RuleStatus.PENDING else (rule.id, *key)] = rule
    final: list[Rule] = []
    for number, rule in enumerate(merged.values(), start=1):
        final.append(rule.model_copy(update={"id": f"R{number:03d}"}))
    return final
