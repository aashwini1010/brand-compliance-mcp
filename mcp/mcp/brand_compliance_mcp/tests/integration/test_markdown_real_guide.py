"""The Markdown adapter against the real Myridius guide."""

from pathlib import Path

from brand_compliance.models.guide import NodeKind
from brand_compliance.plugins.sources.markdown import MarkdownSourceAdapter


def test_load_reads_all_structure_of_the_myridius_guide(
    myridius_guide_path: Path,
) -> None:
    doc = MarkdownSourceAdapter().load(myridius_guide_path)
    assert len(doc.nodes_of(NodeKind.SECTION)) == 39
    assert len(doc.nodes_of(NodeKind.TABLE)) == 8
    assert len(doc.nodes_of(NodeKind.CODE)) == 12
    languages = [n.language for n in doc.nodes_of(NodeKind.CODE)]
    assert languages.count("css") == 9
    assert languages.count("html") == 1
    assert languages.count(None) == 2


def test_load_gives_core_tokens_table_exact_line_numbers(
    myridius_guide_path: Path,
) -> None:
    doc = MarkdownSourceAdapter().load(myridius_guide_path)
    table = next(
        t
        for t in doc.nodes_of(NodeKind.TABLE)
        if t.span.heading_path[-1:] == ("2.1 Core Tokens",)
    )
    index = next(i for i, r in enumerate(table.rows) if "--virtual-tide" in r[0])
    lines = myridius_guide_path.read_text(encoding="utf-8").splitlines()
    assert "--virtual-tide" in lines[table.row_lines[index] - 1]


def test_load_covers_every_table_row_with_a_line_number(
    myridius_guide_path: Path,
) -> None:
    doc = MarkdownSourceAdapter().load(myridius_guide_path)
    for table in doc.nodes_of(NodeKind.TABLE):
        assert len(table.rows) == len(table.row_lines)
        assert all(line > 0 for line in table.row_lines)
