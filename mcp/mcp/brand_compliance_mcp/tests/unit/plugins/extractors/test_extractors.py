"""Tests for the built-in extractors (candidates only, no interpretation)."""

from collections.abc import Callable

from brand_compliance.core.contracts import RuleExtractor
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.models.guide import GuideDocument
from brand_compliance.plugins.extractors import register_extractors
from brand_compliance.plugins.extractors.component import ComponentExtractor
from brand_compliance.plugins.extractors.css_block import CssBlockExtractor
from brand_compliance.plugins.extractors.directive import DirectiveExtractor
from brand_compliance.plugins.extractors.token_table import TokenTableExtractor
from brand_compliance.plugins.extractors.typography import TypographyExtractor

LoadGuide = Callable[[str], GuideDocument]


def test_all_extractors_implement_the_contract() -> None:
    extractors = [
        TokenTableExtractor(),
        TypographyExtractor(),
        ComponentExtractor(),
        CssBlockExtractor(),
        DirectiveExtractor(),
    ]
    assert all(isinstance(e, RuleExtractor) for e in extractors)


def test_register_extractors_adds_all_six_with_unique_names() -> None:
    registry = PluginRegistry()
    register_extractors(registry)
    assert sorted(registry.describe()["RuleExtractor"]) == [
        "bullet_spec",
        "component",
        "css_block",
        "directive",
        "token_table",
        "typography",
    ]


def test_register_extractors_accepts_custom_keywords(load_guide: LoadGuide) -> None:
    registry = PluginRegistry()
    register_extractors(registry, directive_keywords=("forbidden",))
    directive = registry.get(RuleExtractor, "directive")
    found = directive.extract(load_guide("- This is forbidden.\n\n- Never mind.\n"))
    assert [c.hints["text"] for c in found] == ["This is forbidden."]


def test_token_table_extractor_reads_rows_with_exact_lines(
    load_guide: LoadGuide,
) -> None:
    doc = load_guide("# T\n\n| Token | Hex |\n|---|---|\n| `--a` | `#fff` |\n")
    found = TokenTableExtractor().extract(doc)
    assert [c.hints["token"] for c in found] == ["--a"]
    assert found[0].hints["hex"] == "#fff"
    assert found[0].span.line_start == 5


def test_token_table_extractor_ignores_tables_without_hex(
    load_guide: LoadGuide,
) -> None:
    doc = load_guide("| Token | Value |\n|---|---|\n| a | b |\n")
    assert TokenTableExtractor().extract(doc) == []


def test_typography_extractor_reads_scale_rows(load_guide: LoadGuide) -> None:
    text = (
        "| Token | Size | Weight | Line-height | Letter-spacing | Use |\n"
        "|---|---|---|---|---|---|\n| `--fs-h1` | 2rem | 700 | 1.1 | 0 | Title |\n"
    )
    found = TypographyExtractor().extract(load_guide(text))
    assert found[0].hints["size"] == "2rem"
    assert found[0].hints["line_height"] == "1.1"


def test_typography_extractor_ignores_other_tables(load_guide: LoadGuide) -> None:
    assert (
        TypographyExtractor().extract(load_guide("| A | B |\n|---|---|\n| 1 | 2 |\n"))
        == []
    )


def test_component_extractor_reads_variant_rows(load_guide: LoadGuide) -> None:
    text = (
        "| Variant | Background | Text |\n|---|---|---|\n| Primary | `--a` | `--b` |\n"
    )
    found = ComponentExtractor().extract(load_guide(text))
    assert found[0].hints["variant"] == "Primary"
    assert found[0].hints["col:background"] == "--a"


def test_component_extractor_ignores_tables_without_variant(
    load_guide: LoadGuide,
) -> None:
    assert (
        ComponentExtractor().extract(load_guide("| A | B |\n|---|---|\n| 1 | 2 |\n"))
        == []
    )


def test_css_extractor_reports_exact_line_of_each_declaration(
    load_guide: LoadGuide,
) -> None:
    text = "# T\n\n```css\n.a {\n  color: red;\n  margin: 0 !important;\n}\n```\n"
    found = CssBlockExtractor().extract(load_guide(text))
    assert [(c.hints["property"], c.span.line_start) for c in found] == [
        ("color", 5),
        ("margin", 6),
    ]
    assert found[1].hints["value"] == "0 !important"
    assert found[0].hints["selector"] == ".a"


def test_css_extractor_reads_bare_declarations_and_imports(
    load_guide: LoadGuide,
) -> None:
    text = '```css\n--x: 1px;\n@import url("a.css");\n```\n'
    kinds = [c.hints["kind"] for c in CssBlockExtractor().extract(load_guide(text))]
    assert kinds == ["css_declaration", "css_import"]


def test_css_extractor_reads_inline_html_styles(load_guide: LoadGuide) -> None:
    span = "<span style=\"font-family:'Caveat'; color:#E5FD84\">y</span>"
    text = f"```html\n<p>x</p>\n{span}\n```\n"
    found = CssBlockExtractor().extract(load_guide(text))
    assert [(c.hints["selector"], c.hints["property"]) for c in found] == [
        ("span", "font-family"),
        ("span", "color"),
    ]
    assert found[0].span.line_start == 3


def test_css_extractor_reports_unreadable_inline_style(load_guide: LoadGuide) -> None:
    text = '```html\n<p style="color red">x</p>\n```\n'
    found = CssBlockExtractor().extract(load_guide(text))
    assert found[0].hints["kind"] == "css_unsupported"


def test_css_extractor_ignores_other_languages(load_guide: LoadGuide) -> None:
    assert CssBlockExtractor().extract(load_guide("```python\nx = 1\n```\n")) == []


def test_directive_extractor_finds_keyword_sentences_only(
    load_guide: LoadGuide,
) -> None:
    doc = load_guide("- NEVER do this\n\n- calm and quiet\n\nAlways do that.\n")
    found = DirectiveExtractor().extract(doc)
    assert [c.hints["text"] for c in found] == ["NEVER do this", "Always do that."]


def test_directive_extractor_reads_do_dont_tables_with_polarity(
    load_guide: LoadGuide,
) -> None:
    doc = load_guide("| ✓ Do | ✗ Don't |\n|---|---|\n| Be kind | Be rude |\n")
    found = DirectiveExtractor().extract(doc)
    assert [(c.hints["polarity"], c.hints["text"]) for c in found] == [
        ("require", "Be kind"),
        ("forbid", "Be rude"),
    ]


def test_directive_extractor_keeps_topic_of_rule_tables(load_guide: LoadGuide) -> None:
    doc = load_guide("| Rule | Do | Don't |\n|---|---|---|\n| Logo | Left | Right |\n")
    found = DirectiveExtractor().extract(doc)
    assert {c.hints["topic"] for c in found} == {"Logo"}


def test_bullet_spec_extractor_claims_only_listed_bullets(
    load_guide: LoadGuide,
) -> None:
    from brand_compliance.plugins.extractors.bullet_spec import BulletSpecExtractor

    doc = load_guide(
        "## 7.1 Buttons\n\n- **Shape**: pill\n\n- **Voice**: calm\n\n"
        "## 9. Voice\n\n- Shape: wavy\n"
    )
    found = BulletSpecExtractor([("7.1 Buttons", "shape")]).extract(doc)
    assert [(c.hints["label"], c.hints["value"]) for c in found] == [("Shape", "pill")]


def test_bullet_spec_extractor_without_specs_claims_nothing(
    load_guide: LoadGuide,
) -> None:
    from brand_compliance.plugins.extractors.bullet_spec import BulletSpecExtractor

    assert BulletSpecExtractor().extract(load_guide("- Label: value\n")) == []


def test_directive_extractor_reads_each_keyword_line_of_untagged_code(
    load_guide: LoadGuide,
) -> None:
    doc = load_guide("```\n- Always do this\nplain line\n3. Never do that\n```\n")
    found = DirectiveExtractor().extract(doc)
    assert [(c.hints["text"], c.span.line_start) for c in found] == [
        ("Always do this", 2),
        ("Never do that", 4),
    ]


def test_directive_extractor_ignores_tagged_code_blocks(load_guide: LoadGuide) -> None:
    doc = load_guide("```css\n/* Always do this */\na { b: c }\n```\n")
    assert DirectiveExtractor().extract(doc) == []
