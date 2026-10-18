"""Tests for brand_compliance.rules.leftovers."""

from collections.abc import Callable

from brand_compliance.models.guide import GuideDocument
from brand_compliance.models.rule import RuleCandidate
from brand_compliance.models.source import SourceSpan
from brand_compliance.rules.leftovers import collect_unmatched

LoadGuide = Callable[[str], GuideDocument]

TEXT = """\
# T

Plain paragraph.

- a bullet

| A | B |
|---|---|
| x | y |
| p | q |

```
ascii art
```
"""


def _claim(line: int) -> RuleCandidate:
    return RuleCandidate(
        id=f"c{line}",
        extractor="t",
        text="t",
        span=SourceSpan(file="guide.md", line_start=line, line_end=line),
    )


def test_collect_unmatched_returns_everything_when_nothing_is_claimed(
    load_guide: LoadGuide,
) -> None:
    found = collect_unmatched(load_guide(TEXT), [])
    texts = [c.text for c in found]
    assert texts == ["Plain paragraph.", "a bullet", "x | y", "p | q", "ascii art"]


def test_collect_unmatched_skips_claimed_lines(load_guide: LoadGuide) -> None:
    found = collect_unmatched(load_guide(TEXT), [_claim(3), _claim(9)])
    assert [c.text for c in found] == ["a bullet", "p | q", "ascii art"]


def test_collect_unmatched_keeps_exact_row_line_numbers(load_guide: LoadGuide) -> None:
    found = collect_unmatched(load_guide(TEXT), [])
    rows = {c.text: c.span.line_start for c in found if "|" in c.text}
    assert rows == {"x | y": 9, "p | q": 10}


def test_collect_unmatched_treats_code_as_claimed_if_any_line_is(
    load_guide: LoadGuide,
) -> None:
    found = collect_unmatched(load_guide(TEXT), [_claim(13)])
    assert "ascii art" not in [c.text for c in found]


def test_collect_unmatched_truncates_very_long_text(load_guide: LoadGuide) -> None:
    found = collect_unmatched(load_guide("x" * 1000 + "\n"), [])
    assert len(found[0].text) == 300


def test_collect_unmatched_groups_unclaimed_prompt_lines_into_runs(
    load_guide: LoadGuide,
) -> None:
    doc = load_guide("```\nline a\nline b\n\nline c\nclaimed\nline d\n```\n")
    found = collect_unmatched(doc, [_claim(6)])
    assert [(c.text, c.span.line_start, c.span.line_end) for c in found] == [
        ("line a line b", 2, 3),
        ("line c", 5, 5),
        ("line d", 7, 7),
    ]


def test_collect_unmatched_keeps_fully_tagged_code_node_level(
    load_guide: LoadGuide,
) -> None:
    doc = load_guide("```css\na { b: c }\n```\n")
    assert [c.text for c in collect_unmatched(doc, [])] == ["a { b: c }"]
    assert collect_unmatched(doc, [_claim(2)]) == []
