"""Human-readable report, organised around the questions a reviewer asks."""

from collections import Counter, defaultdict
from pathlib import Path

from brand_compliance.models.change import ROLLED_BACK_PREFIX, Change
from brand_compliance.models.report import RunResult, RunStatus
from brand_compliance.models.rule import Rule, RuleStatus
from brand_compliance.plugins.reporters.base import cell, guide_ref, table, what

_UNMAPPED_SHOWN = 25
_STATUS_LABEL = {
    RuleStatus.APPLIED: "Applied",
    RuleStatus.NOT_APPLICABLE: "Understood but not applied",
    RuleStatus.UNINTERPRETABLE: "Could not interpret",
    RuleStatus.CONFLICT_UNRESOLVED: "Conflict (unresolved)",
    RuleStatus.REFERENCE: "Reference definition",
}


class MarkdownReporter:
    """Writes ``report.md``."""

    name = "markdown"
    format = "markdown"
    filename = "report.md"

    def render(self, result: RunResult, output_dir: Path) -> Path:
        """Write the report and return its path."""
        path = output_dir / self.filename
        path.write_text(build_markdown(result), encoding="utf-8")
        return path


def build_markdown(result: RunResult) -> str:
    """Return the whole report as Markdown text."""
    by_status: dict[RuleStatus, list[Rule]] = defaultdict(list)
    for rule in result.rules:
        by_status[rule.status].append(rule)
    sections = [
        _header(result),
        _summary(result, by_status),
        _verification(result),
        _applied(by_status[RuleStatus.APPLIED]),
        _change_log(result),
        _not_applied(by_status[RuleStatus.NOT_APPLICABLE]),
        _uninterpretable(by_status[RuleStatus.UNINTERPRETABLE]),
        _conflicts(result),
        _reference(by_status[RuleStatus.REFERENCE]),
        _rolled_back(result),
        _skips(result),
        _unmapped(result),
        _notes(result),
    ]
    return "\n".join(section for section in sections if section) + "\n"


def _header(result: RunResult) -> str:
    unchanged = result.source_sha256_before == result.source_sha256_after
    mark = (
        "completed" if result.status is RunStatus.COMPLETED else "FAILED VERIFICATION"
    )
    lines = [
        "# Brand compliance report\n",
        f"**Run:** `{result.run_id}`  ·  **Status:** {mark}\n",
        table(
            ["", ""],
            [
                ["Brand guide", result.guide_name],
                ["Artifact", f"{result.artifact_name} ({result.artifact_type.value})"],
                [
                    "Original file",
                    "unchanged" if unchanged else "CHANGED (this must never happen)",
                ],
                ["Fingerprint (sha256)", result.source_sha256_before],
                ["Started", result.started_at or "n/a"],
            ],
        ),
    ]
    if result.status is RunStatus.FAILED_VERIFICATION:
        lines.append(
            "> **The branded file was withheld** because an output check failed "
            "(see Verification). Nothing unusable was handed back.\n"
        )
    if result.classification_ambiguous:
        lines.append(
            "> The artifact could not be classified with confidence; the safer "
            "email-style handling applies. Evidence:\n"
        )
    lines.append("Why it was treated as " + result.artifact_type.value + ":\n")
    lines.extend(f"- {signal}" for signal in result.detection_signals)
    return "\n".join(lines) + "\n"


def _summary(result: RunResult, by_status: dict[RuleStatus, list[Rule]]) -> str:
    rows = [[_STATUS_LABEL[s], len(by_status[s])] for s in _STATUS_LABEL]
    rows.append(["**Total rules**", len(result.rules)])
    undone = sum(1 for s in result.skipped if s.reason.startswith(ROLLED_BACK_PREFIX))
    return (
        "## Summary\n\n"
        + table(["Rules", "Count"], rows)
        + f"\nChanges made: **{len(result.changes)}**  ·  "
        f"changes rolled back: **{undone}**  ·  "
        f"contradictions in the guide: **{len(result.conflicts)}**\n"
    )


def _verification(result: RunResult) -> str:
    lines = ["## Verification\n"]
    for check in result.checks:
        mark = "pass" if check.passed else "**FAIL**"
        lines.append(f"- **{check.name}**: {mark}")
        lines.extend(f"  - {detail}" for detail in check.details)
    return "\n".join(lines) + "\n"


def _applied(rules: list[Rule]) -> str:
    rows = [[r.id, what(r), r.scope.value, guide_ref(r), r.reason] for r in rules]
    return "## 1. Rules applied\n\n" + table(
        ["Rule", "What the guide says", "Scope", "Guide line", "Result"], rows
    )


def _change_log(result: RunResult) -> str:
    rules = {r.id: r for r in result.rules}
    grouped: dict[str, list[Change]] = defaultdict(list)
    for change in result.changes:
        grouped[change.rule_id].append(change)
    parts = [
        "## 2. Change log\n",
        "Every edit: which element, before and after, and the guideline behind it.\n",
    ]
    for rule_id in sorted(grouped):
        rule = rules.get(rule_id)
        title = f"{rule_id} · {what(rule)}" if rule else rule_id
        where = f" (guide line {guide_ref(rule)})" if rule else ""
        rows = [
            [
                c.id,
                c.location,
                c.property,
                c.before or "(not set)",
                c.after,
                c.note or "",
            ]
            for c in grouped[rule_id]
        ]
        parts.append(f"### {cell(title, 200)}{where}\n")
        parts.append(
            table(["Change", "Element", "Property", "Before", "After", "Note"], rows)
        )
    if not grouped:
        parts.append("_No changes were made._\n")
    return "\n".join(parts)


def _not_applied(rules: list[Rule]) -> str:
    rows = [
        [r.id, what(r), guide_ref(r), r.reason]
        for r in sorted(rules, key=lambda r: r.reason)
    ]
    return (
        "## 3. Understood but not applied\n\n"
        "The guide's rule was understood, but could not be applied here.\n\n"
        + table(["Rule", "What the guide says", "Guide line", "Why not"], rows)
    )


def _uninterpretable(rules: list[Rule]) -> str:
    counts = Counter(r.reason for r in rules)
    reasons = table(["Reason", "Count"], counts.most_common())
    rows = [
        [r.id, guide_ref(r), r.value or what(r), r.reason]
        for r in sorted(rules, key=lambda r: (r.reason, r.source_span.line_start or 0))
    ]
    return (
        "## 4. Could not interpret\n\n"
        "Guidance the tool could not turn into a checkable rule. Nothing here was "
        "guessed or applied.\n\n"
        + reasons
        + "\n"
        + table(["Rule", "Guide line", "Text", "Reason"], rows)
    )


def _conflicts(result: RunResult) -> str:
    rules = {r.id: r for r in result.rules}
    parts = ["## 5. Contradictions in the guide\n"]
    if not result.conflicts:
        return parts[0] + "\n_None found._\n"
    for conflict in result.conflicts:
        state = (
            "resolved by the guide itself"
            if conflict.resolved
            else "UNRESOLVED: neither side applied"
        )
        parts.append(f"### {conflict.id} · {state}\n\n{conflict.description}\n")
        if conflict.resolution:
            parts.append(f"Resolution: {conflict.resolution}\n")
        rows = [
            [
                rid,
                what(rules[rid]),
                guide_ref(rules[rid]),
                _STATUS_LABEL[rules[rid].status],
            ]
            for rid in conflict.rule_ids
            if rid in rules
        ]
        parts.append(
            table(["Rule", "What it says", "Guide line", "Final status"], rows)
        )
    return "\n".join(parts)


def _reference(rules: list[Rule]) -> str:
    counts = Counter(r.category for r in rules)
    items = ", ".join(f"{n} × {name}" for name, n in sorted(counts.items()))
    return (
        "## 6. Reference definitions\n\n"
        "Understood and used as input by other rules; nothing to apply on their own: "
        f"{items or 'none'}. Full list in `guide_rules.json`.\n"
    )


def _rolled_back(result: RunResult) -> str:
    rules = {r.id: r for r in result.rules}
    undone = [s for s in result.skipped if s.reason.startswith(ROLLED_BACK_PREFIX)]
    rows = [
        [
            s.rule_id,
            what(rules[s.rule_id]) if s.rule_id in rules else "",
            s.location or "",
            s.reason.removeprefix(ROLLED_BACK_PREFIX),
        ]
        for s in undone
    ]
    return (
        "## 7. Changes rolled back\n\n"
        "Edits that were planned, then undone because they would have broken the "
        "result. The page keeps its own value there.\n\n"
        + table(["Rule", "What the guide says", "Element", "Why"], rows)
    )


def _skips(result: RunResult) -> str:
    other = [s for s in result.skipped if not s.reason.startswith(ROLLED_BACK_PREFIX)]
    counts = Counter(s.reason for s in other)
    rows = [[n, reason] for reason, n in counts.most_common()]
    return "## 8. Other places a rule was skipped\n\n" + table(
        ["Times", "Reason"], rows
    )


def _unmapped(result: RunResult) -> str:
    shown = result.unmapped_elements[:_UNMAPPED_SHOWN]
    more = len(result.unmapped_elements) - len(shown)
    lines = [
        "## 9. Elements with text but no role\n",
        f"{len(result.unmapped_elements)} element(s) have text but match no role, so "
        "brand rules did not target them (only the font family was enforced).\n",
        *(f"- `{cell(item, 200)}`" for item in shown),
    ]
    if more > 0:
        lines.append(f"- … and {more} more (see `report.json`)")
    return "\n".join(lines) + "\n"


def _notes(result: RunResult) -> str:
    if not result.notes:
        return ""
    return (
        "## Notes and limits\n\n"
        + "\n".join(f"- {note}" for note in result.notes)
        + "\n"
    )
