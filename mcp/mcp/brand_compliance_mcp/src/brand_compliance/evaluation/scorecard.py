"""Turn case results into a scorecard (Markdown for people, JSON for tools)."""

import json
from collections import defaultdict

from brand_compliance.evaluation.runner import CaseResult

_TICK = {True: "✅", False: "❌"}


def aggregate(results: list[CaseResult]) -> list[dict[str, object]]:
    """For each metric name: how many cases passed it, and its overall ratio."""
    passed: dict[str, int] = defaultdict(int)
    total: dict[str, int] = defaultdict(int)
    num: dict[str, int] = defaultdict(int)
    den: dict[str, int] = defaultdict(int)
    for result in results:
        for metric in result.metrics:
            total[metric.name] += 1
            passed[metric.name] += int(metric.passed)
            num[metric.name] += metric.numerator
            den[metric.name] += metric.denominator
    return [
        {
            "metric": name,
            "cases_passed": passed[name],
            "cases_total": total[name],
            "ratio": (num[name] / den[name]) if den[name] else None,
            "items": f"{num[name]}/{den[name]}" if den[name] else "",
        }
        for name in sorted(total)
    ]


def to_json(results: list[CaseResult]) -> str:
    """Machine-readable scorecard."""
    payload = {
        "cases_passed": sum(r.passed for r in results),
        "cases_total": len(results),
        "all_passed": all(r.passed for r in results),
        "aggregate": aggregate(results),
        "cases": [
            {
                "id": r.case.id,
                "description": r.case.description,
                "synthetic": r.case.synthetic,
                "passed": r.passed,
                "error_code": r.error_code,
                "metrics": [
                    {
                        "name": mt.name,
                        "passed": mt.passed,
                        "detail": mt.detail,
                        "score": mt.score,
                    }
                    for mt in r.metrics
                ],
            }
            for r in results
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def to_markdown(results: list[CaseResult]) -> str:
    """Human-readable scorecard."""
    passed = sum(r.passed for r in results)
    lines = [
        "# Evaluation scorecard\n",
        f"**{passed} of {len(results)} cases passed.** "
        + (
            "All metrics are green.\n"
            if passed == len(results)
            else "Some metrics failed; see below.\n"
        ),
        "## How to read this\n",
        "Each case is a guide and an artifact with **hand-written expectations** "
        "(`eval/expected/*.json`). The content, fidelity and idempotence metrics are "
        "computed by the evaluator's own code from the original and branded files, "
        "not taken from the tool's verifiers. Cases marked *synthetic* were written "
        "for testing; real client material should be added for a proper evaluation.\n",
        "## Overall by metric\n",
        "| Metric | Cases passing | Items |",
        "|---|---|---|",
    ]
    for row in aggregate(results):
        cells = (
            row["metric"],
            f"{row['cases_passed']}/{row['cases_total']}",
            row["items"],
        )
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    lines.append("\n## Cases\n")
    lines.append("| Case | Result | Kind |\n|---|---|---|")
    for r in results:
        kind = "synthetic" if r.case.synthetic else "real material"
        lines.append(f"| [{r.case.id}](#{r.case.id}) | {_TICK[r.passed]} | {kind} |")
    for r in results:
        lines.append(f"\n### {r.case.id}\n")
        lines.append(f"{r.case.description}\n")
        lines.append("| | Metric | Detail |\n|---|---|---|")
        for mt in r.metrics:
            detail = mt.detail.replace("|", "\\|")
            lines.append(f"| {_TICK[mt.passed]} | {mt.name} | {detail} |")
    return "\n".join(lines) + "\n"
