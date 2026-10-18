"""Style writers. Add one line to ``register_writers`` per artifact type."""

from brand_compliance.core.registry import PluginRegistry
from brand_compliance.plugins.writers.inline import InlineWriter
from brand_compliance.plugins.writers.static import StylesheetWriter


def register_writers(registry: PluginRegistry) -> None:
    """Register every built-in style writer."""
    registry.register(StylesheetWriter())
    registry.register(InlineWriter())
