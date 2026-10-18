"""Tests for brand_compliance.plugins.sources.markdown."""

from collections.abc import Callable
from pathlib import Path

import pytest

from brand_compliance.core.contracts import SourceAdapter
from brand_compliance.core.errors import InvalidInputError
from brand_compliance.models.guide import GuideDocument, NodeKind
from brand_compliance.plugins.sources.markdown import MarkdownSourceAdapter

WriteFile = Callable[[str, str], Path]

SAMPLE = """\
# Brand

Intro text.

## Colors

| Token | Hex |
|---|---|
| `--tide` | `#09A78D` |
| `--leaf` | `#194247` |

### Rules

- First rule
- Second rule
  - Nested rule

```css
.btn { color: red; }
```

## Fonts

Use Montserrat.
"""


def _load(write_file: WriteFile, text: str = SAMPLE) -> GuideDocument:
    return MarkdownSourceAdapter().load(write_file("guide.md", text))


def test_adapter_implements_the_source_adapter_contract() -> None:
    assert isinstance(MarkdownSourceAdapter(), SourceAdapter)


@pytest.mark.parametrize(
    ("name", "expected"),
    [("g.md", True), ("G.MARKDOWN", True), ("g.pdf", False), ("g", False)],
)
def test_can_handle_checks_the_file_extension(name: str, expected: bool) -> None:
    assert MarkdownSourceAdapter().can_handle(Path(name)) is expected


def test_load_nests_sections_by_heading_level(write_file: WriteFile) -> None:
    doc = _load(write_file)
    brand = doc.nodes[0]
    assert (brand.text, brand.level) == ("Brand", 1)
    assert [c.text for c in brand.children if c.kind is NodeKind.SECTION] == [
        "Colors",
        "Fonts",
    ]
    colors = brand.children[1]
    assert [c.text for c in colors.children if c.kind is NodeKind.SECTION] == ["Rules"]


def test_load_records_heading_path_on_every_node(write_file: WriteFile) -> None:
    doc = _load(write_file)
    table = doc.nodes_of(NodeKind.TABLE)[0]
    assert table.span.heading_path == ("Brand", "Colors")
    rules = next(n for n in doc.nodes_of(NodeKind.SECTION) if n.text == "Rules")
    assert rules.span.heading_path == ("Brand", "Colors", "Rules")


def test_load_reads_table_header_rows_and_row_line_numbers(
    write_file: WriteFile,
) -> None:
    table = _load(write_file).nodes_of(NodeKind.TABLE)[0]
    assert table.header == ["Token", "Hex"]
    assert table.rows == [["`--tide`", "`#09A78D`"], ["`--leaf`", "`#194247`"]]
    assert table.row_lines == [9, 10]


def test_load_keeps_code_block_language_and_content(write_file: WriteFile) -> None:
    code = _load(write_file).nodes_of(NodeKind.CODE)[0]
    assert code.language == "css"
    assert ".btn { color: red; }" in code.text
    assert code.span.line_start == 18


def test_load_reads_list_items_once_including_nested(write_file: WriteFile) -> None:
    items = [n.text for n in _load(write_file).nodes_of(NodeKind.LIST_ITEM)]
    assert items == ["First rule", "Second rule", "Nested rule"]


def test_load_does_not_duplicate_list_text_as_paragraphs(write_file: WriteFile) -> None:
    paragraphs = [n.text for n in _load(write_file).nodes_of(NodeKind.PARAGRAPH)]
    assert paragraphs == ["Intro text.", "Use Montserrat."]


def test_load_reads_loose_list_items_once(write_file: WriteFile) -> None:
    doc = _load(write_file, "- one\n\n- two\n")
    assert [n.text for n in doc.nodes_of(NodeKind.LIST_ITEM)] == ["one", "two"]
    assert doc.nodes_of(NodeKind.PARAGRAPH) == []


def test_load_keeps_untagged_code_block_with_no_language(write_file: WriteFile) -> None:
    code = _load(write_file, "```\nplain\n```\n").nodes_of(NodeKind.CODE)[0]
    assert code.language is None


def test_load_keeps_html_blocks_as_html_code(write_file: WriteFile) -> None:
    code = _load(write_file, "<div>x</div>\n").nodes_of(NodeKind.CODE)[0]
    assert code.language == "html"


def test_load_ignores_horizontal_rules(write_file: WriteFile) -> None:
    doc = _load(write_file, "para\n\n---\n\nmore\n")
    assert [n.text for n in doc.nodes_of(NodeKind.PARAGRAPH)] == ["para", "more"]


def test_load_handles_content_before_first_heading(write_file: WriteFile) -> None:
    doc = _load(write_file, "loose text\n\n# Title\n")
    assert doc.nodes[0].kind is NodeKind.PARAGRAPH
    assert doc.nodes[1].kind is NodeKind.SECTION


def test_load_handles_empty_file(write_file: WriteFile) -> None:
    assert _load(write_file, "").nodes == []


def test_load_sets_source_name_and_format(write_file: WriteFile) -> None:
    doc = _load(write_file)
    assert (doc.source_name, doc.source_format) == ("guide.md", "markdown")


def test_load_rejects_oversized_file(write_file: WriteFile) -> None:
    adapter = MarkdownSourceAdapter(max_bytes=5)
    with pytest.raises(InvalidInputError):
        adapter.load(write_file("guide.md", "# too long"))


def test_load_reads_code_inside_a_list_item_that_has_no_text(
    write_file: WriteFile,
) -> None:
    doc = _load(write_file, "- ```css\n  a { b: c }\n  ```\n")
    assert doc.nodes_of(NodeKind.LIST_ITEM) == []
    assert doc.nodes_of(NodeKind.CODE)[0].language == "css"
