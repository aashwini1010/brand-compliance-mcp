"""Tests for brand_compliance.core.registry."""

from pathlib import Path
from typing import Any

import pytest

from brand_compliance.core.contracts import Reporter, RuleExtractor, SourceAdapter
from brand_compliance.core.errors import PluginError, UnsupportedFormatError
from brand_compliance.core.registry import PluginRegistry, load_entry_point_plugins
from brand_compliance.models.guide import GuideDocument
from brand_compliance.models.report import RunResult
from brand_compliance.models.rule import RuleCandidate


class FakeMarkdownAdapter:
    name = "markdown"

    def can_handle(self, source: Path) -> bool:
        return source.suffix == ".md"

    def load(self, source: Path) -> GuideDocument:
        return GuideDocument(source_name=source.name, source_format="md")


class FakeExtractor:
    name = "fake-extractor"

    def extract(self, document: GuideDocument) -> list[RuleCandidate]:
        return []


class FakeReporter:
    name = "fake-reporter"
    format = "json"
    filename = "r.json"

    def render(self, result: RunResult, output_dir: Path) -> Path:
        return output_dir / "report.json"


class NotAPlugin:
    name = "nothing"


class FakeEntryPoint:
    def __init__(self, name: str, target: Any) -> None:
        self.name = name
        self._target = target

    def load(self) -> Any:
        if isinstance(self._target, Exception):
            raise self._target
        return self._target


def test_register_returns_the_interface_it_matched() -> None:
    registry = PluginRegistry()
    assert registry.register(FakeMarkdownAdapter()) is SourceAdapter


def test_register_rejects_object_matching_no_interface() -> None:
    with pytest.raises(PluginError):
        PluginRegistry().register(NotAPlugin())


def test_register_rejects_duplicate_name_for_same_interface() -> None:
    registry = PluginRegistry()
    registry.register(FakeMarkdownAdapter())
    with pytest.raises(PluginError):
        registry.register(FakeMarkdownAdapter())


def test_register_rejects_empty_name() -> None:
    adapter = FakeMarkdownAdapter()
    adapter.name = ""
    with pytest.raises(PluginError):
        PluginRegistry().register(adapter)


def test_plugins_returns_only_the_requested_kind() -> None:
    registry = PluginRegistry()
    registry.register(FakeMarkdownAdapter())
    registry.register(FakeExtractor())
    assert [p.name for p in registry.plugins(RuleExtractor)] == ["fake-extractor"]


def test_find_returns_plugin_that_can_handle_source() -> None:
    registry = PluginRegistry()
    registry.register(FakeMarkdownAdapter())
    adapter = registry.find(SourceAdapter, lambda a: a.can_handle(Path("g.md")))
    assert adapter.name == "markdown"


def test_find_raises_unsupported_format_when_nothing_matches() -> None:
    registry = PluginRegistry()
    registry.register(FakeMarkdownAdapter())
    with pytest.raises(UnsupportedFormatError):
        registry.find(SourceAdapter, lambda a: a.can_handle(Path("g.pdf")))


def test_get_raises_plugin_error_for_unknown_name() -> None:
    with pytest.raises(PluginError):
        PluginRegistry().get(Reporter, "missing")


def test_get_returns_plugin_by_name() -> None:
    registry = PluginRegistry()
    registry.register(FakeReporter())
    assert registry.get(Reporter, "fake-reporter").format == "json"


def test_describe_lists_names_per_interface() -> None:
    registry = PluginRegistry()
    registry.register(FakeMarkdownAdapter())
    assert registry.describe()["SourceAdapter"] == ["markdown"]


def test_load_entry_point_plugins_registers_valid_plugins() -> None:
    registry = PluginRegistry()
    eps = [FakeEntryPoint("md", FakeMarkdownAdapter)]
    added = load_entry_point_plugins(registry, entry_points_fn=lambda group: eps)  # type: ignore[arg-type,return-value]
    assert added == 1
    assert registry.describe()["SourceAdapter"] == ["markdown"]


def test_load_entry_point_plugins_skips_broken_plugin() -> None:
    registry = PluginRegistry()
    eps = [
        FakeEntryPoint("broken", ImportError("boom")),
        FakeEntryPoint("bad", NotAPlugin),
        FakeEntryPoint("good", FakeExtractor),
    ]
    added = load_entry_point_plugins(registry, entry_points_fn=lambda group: eps)  # type: ignore[arg-type,return-value]
    assert added == 1


def test_register_with_replace_swaps_a_plugin_of_the_same_name() -> None:
    registry = PluginRegistry()
    registry.register(FakeMarkdownAdapter())
    newer = FakeMarkdownAdapter()
    registry.register(newer, replace=True)
    assert registry.plugins(SourceAdapter) == [newer]


def test_register_with_replace_still_adds_a_plugin_that_is_not_taken() -> None:
    registry = PluginRegistry()
    registry.register(FakeMarkdownAdapter(), replace=True)
    assert registry.describe()["SourceAdapter"] == ["markdown"]


def test_unregister_removes_a_plugin_by_name() -> None:
    registry = PluginRegistry()
    registry.register(FakeMarkdownAdapter())
    registry.unregister(SourceAdapter, "markdown")
    assert registry.plugins(SourceAdapter) == []


def test_unregister_an_unknown_plugin_is_an_error() -> None:
    with pytest.raises(PluginError):
        PluginRegistry().unregister(SourceAdapter, "nope")
