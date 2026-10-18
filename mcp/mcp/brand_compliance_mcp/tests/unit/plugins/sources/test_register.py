"""Tests for brand_compliance.plugins.sources registration."""

from pathlib import Path

from brand_compliance.core.contracts import SourceAdapter
from brand_compliance.core.registry import PluginRegistry
from brand_compliance.plugins.sources import register_sources


def test_register_sources_makes_markdown_findable_by_file() -> None:
    registry = PluginRegistry()
    register_sources(registry)
    adapter = registry.find(SourceAdapter, lambda a: a.can_handle(Path("guide.md")))
    assert adapter.name == "markdown"


def test_register_sources_accepts_a_size_limit() -> None:
    registry = PluginRegistry()
    register_sources(registry, max_bytes=10)
    assert registry.describe()["SourceAdapter"] == ["markdown"]
