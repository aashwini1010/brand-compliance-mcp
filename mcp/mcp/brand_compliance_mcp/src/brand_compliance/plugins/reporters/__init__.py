"""Report writers. Add one line to ``register_reporters`` per format."""

from brand_compliance.core.registry import PluginRegistry
from brand_compliance.plugins.reporters.guide_rules import GuideRulesReporter
from brand_compliance.plugins.reporters.json_report import JsonReporter
from brand_compliance.plugins.reporters.markdown_report import MarkdownReporter


def register_reporters(registry: PluginRegistry) -> None:
    """Register every built-in reporter."""
    registry.register(JsonReporter())
    registry.register(MarkdownReporter())
    registry.register(GuideRulesReporter())
