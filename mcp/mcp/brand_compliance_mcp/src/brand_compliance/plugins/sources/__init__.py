"""Guide readers. Add one line to ``register_sources`` per new format."""

from brand_compliance.core.registry import PluginRegistry
from brand_compliance.plugins.sources.markdown import MarkdownSourceAdapter


def register_sources(registry: PluginRegistry, max_bytes: int | None = None) -> None:
    """Register every built-in guide reader."""
    markdown = (
        MarkdownSourceAdapter()
        if max_bytes is None
        else MarkdownSourceAdapter(max_bytes)
    )
    registry.register(markdown)
