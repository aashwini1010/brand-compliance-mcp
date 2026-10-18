"""Small helpers shared by the report writers."""

from collections.abc import Sequence

from brand_compliance.models.rule import Rule

_MAX_CELL = 160


def cell(value: object, limit: int = _MAX_CELL) -> str:
    """Make a value safe and short for a Markdown table cell."""
    text = " ".join(str(value if value is not None else "").split())
    text = text.replace("|", "\\|").replace("`", "'")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    """Render a Markdown table (no table at all when there are no rows)."""
    if not rows:
        return "_None._\n"
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
        *("| " + " | ".join(cell(item) for item in row) + " |" for row in rows),
    ]
    return "\n".join(lines) + "\n"


def what(rule: Rule) -> str:
    """Describe what a rule says in words a reviewer can read at a glance."""
    value = rule.value or ""
    role = rule.target_role or "text"
    if rule.category == "forbid_color":
        where = "" if rule.scope.value == "all" else f" on {rule.scope.value} surfaces"
        return f"Never use {value} as {role} colour{where}"
    if rule.category == "forbid_effect":
        return f"Never use the '{value}' effect"
    if rule.category == "min_contrast":
        return f"{role} contrast must be at least {value}:1"
    if rule.category == "font_only":
        return f"Only the font {value} may be used"
    if rule.category == "font_exception":
        limit = rule.notes[0] if rule.notes else "specific places"
        return f"The font {value} is allowed, but only in: {limit}"
    parts = [rule.target_role or "", f"{rule.property}:" if rule.property else ""]
    head = " ".join(p for p in parts if p)
    return f"{head} {value}".strip() or rule.category


def guide_ref(rule: Rule) -> str:
    """Return where in the guide a rule came from, e.g. ``guide.md:30``."""
    return rule.source_span.describe()
