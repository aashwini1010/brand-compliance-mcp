"""Guide plus real page, end to end: interpret, plan, write."""

import re
from dataclasses import dataclass
from pathlib import Path

import pytest
from lxml import html

from brand_compliance.core.contracts import RuleApplier, RuleExtractor
from brand_compliance.core.hashing import sha256_file
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.models.change import Change
from brand_compliance.models.rule import RuleStatus
from brand_compliance.pipeline.planning import PlanResult, plan_changes
from brand_compliance.plugins.appliers import register_appliers
from brand_compliance.plugins.artifacts.base import (
    element_path,
    is_content_element,
    serialize_html,
)
from brand_compliance.plugins.artifacts.roles import load_role_aliases
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler
from brand_compliance.plugins.extractors import register_extractors
from brand_compliance.plugins.sources.markdown import MarkdownSourceAdapter
from brand_compliance.plugins.writers.static import StylesheetWriter
from brand_compliance.rules.interpret import GuideInterpretation, interpret_guide
from brand_compliance.rules.vocabulary import load_vocabulary

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "myridius-brand-guide.md"
PAGE = ROOT / "eval" / "artifacts" / "mcp-servers-report-simple-v2.html"


@dataclass
class Run:
    interpretation: GuideInterpretation
    plan: PlanResult
    output: str


def _run(
    text: str, interpretation: GuideInterpretation, registry: PluginRegistry
) -> Run:
    artifact = StaticArtifactHandler().parse(text, PAGE.name)
    plan = plan_changes(interpretation.rules, artifact, registry.plugins(RuleApplier))
    written = StylesheetWriter().write(plan.changes, artifact)
    return Run(interpretation, plan, serialize_html(written.tree, written.doctype))


@pytest.fixture(scope="module")
def registry() -> PluginRegistry:
    vocabulary = load_vocabulary()
    reg = PluginRegistry()
    register_extractors(
        reg, bullet_specs=[(s.section, s.label) for s in vocabulary.bullet_specs]
    )
    register_appliers(reg, load_role_aliases())
    return reg


@pytest.fixture(scope="module")
def interpretation(registry: PluginRegistry) -> GuideInterpretation:
    if not (GUIDE.is_file() and PAGE.is_file()):
        pytest.skip("sample guide or page not present")
    return interpret_guide(
        MarkdownSourceAdapter().load(GUIDE),
        registry.plugins(RuleExtractor),
        load_vocabulary(),
    )


@pytest.fixture(scope="module")
def first(interpretation: GuideInterpretation, registry: PluginRegistry) -> Run:
    return _run(PAGE.read_text(encoding="utf-8"), interpretation, registry)


def _visible(markup: str) -> str:
    return re.sub(r"\s+", " ", html.fromstring(markup).text_content()).strip()


def _scripts(markup: str) -> list[str]:
    found = re.findall(r"<script[^>]*>(.*?)</script>", markup, re.S)
    return [re.sub(r"\s+", "", s) for s in found]


def test_original_file_is_not_modified_by_a_run(
    interpretation: GuideInterpretation, registry: PluginRegistry
) -> None:
    before = sha256_file(PAGE)
    _run(PAGE.read_text(encoding="utf-8"), interpretation, registry)
    assert sha256_file(PAGE) == before


def test_output_keeps_visible_text_scripts_and_icons(first: Run) -> None:
    original = PAGE.read_text(encoding="utf-8")
    assert _visible(first.output).startswith(_visible(original)[:200])
    assert _scripts(first.output) == _scripts(original)
    assert "viewbox=" not in first.output
    assert first.output.count("<svg") == original.count("<svg")


def test_output_keeps_every_link_and_button(first: Run) -> None:
    original = PAGE.read_text(encoding="utf-8")
    assert first.output.count("<button") == original.count("<button")
    assert first.output.count("<a ") == original.count("<a ")


def test_running_the_tool_on_its_own_output_is_stable(
    first: Run, interpretation: GuideInterpretation, registry: PluginRegistry
) -> None:
    second = _run(first.output, interpretation, registry)
    assert second.output == first.output
    assert second.output.count('id="brand-compliance"') == 1


def test_brand_block_and_font_link_are_written(first: Run) -> None:
    assert first.output.count('<style id="brand-compliance">') == 1
    assert "fonts.googleapis.com/css2?family=Montserrat" in first.output


def test_key_guide_values_land_on_the_right_roles(first: Run) -> None:
    css = re.search(r'<style id="brand-compliance">(.*?)</style>', first.output, re.S)
    assert css
    text = css.group(1)
    assert 'data-brand-role="button.primary"' in text
    assert "background: #09a78d;" in text
    assert "border-radius: 999px;" in text
    assert "background: #f6f3f0;" in text
    assert "color: #194247;" in text


def test_only_the_element_with_an_inline_style_is_forced(first: Run) -> None:
    forced = [c for c in first.plan.changes if c.important]
    assert len(forced) == 1
    assert forced[0].note == "Overrides an inline style"
    assert first.output.count('data-brand-force="') == 1


def test_every_change_names_its_rule_where_before_and_after(first: Run) -> None:
    rule_ids = {r.id for r in first.interpretation.rules}
    for change in first.plan.changes:
        assert isinstance(change, Change)
        assert change.rule_id in rule_ids
        assert change.location.startswith("/html")
        assert change.after


def test_every_handled_rule_has_an_outcome_with_a_reason(first: Run) -> None:
    assert first.plan.outcomes
    for outcome in first.plan.outcomes.values():
        assert outcome.status in (RuleStatus.APPLIED, RuleStatus.NOT_APPLICABLE)
        assert outcome.reason


def test_rules_in_conflict_are_never_applied(first: Run) -> None:
    conflicted = {
        r.id
        for r in first.interpretation.rules
        if r.status is RuleStatus.CONFLICT_UNRESOLVED
    }
    assert conflicted
    assert conflicted.isdisjoint(first.plan.outcomes)
    assert conflicted.isdisjoint({c.rule_id for c in first.plan.changes})


def test_every_element_using_a_non_brand_font_is_changed(first: Run) -> None:
    artifact = StaticArtifactHandler().parse(
        PAGE.read_text(encoding="utf-8"), PAGE.name
    )
    off_brand = {
        element_path(el)
        for el in artifact.tree.iter()
        if isinstance(el, html.HtmlElement)
        and is_content_element(el)
        and (family := artifact.styles.declared(el, "font-family"))
        and family.split(",")[0].strip("\"' ").lower() != "montserrat"
    }
    changed = {c.location for c in first.plan.changes if c.property == "font-family"}
    assert off_brand, "the sample is expected to use other fonts"
    assert off_brand <= changed
