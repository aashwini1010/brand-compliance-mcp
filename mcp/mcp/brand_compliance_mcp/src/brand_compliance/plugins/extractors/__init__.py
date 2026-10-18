"""Rule finders. Add one line to ``register_extractors`` per new finder."""

from collections.abc import Iterable

from brand_compliance.core.registry import PluginRegistry
from brand_compliance.plugins.extractors.bullet_spec import BulletSpecExtractor
from brand_compliance.plugins.extractors.component import ComponentExtractor
from brand_compliance.plugins.extractors.css_block import CssBlockExtractor
from brand_compliance.plugins.extractors.directive import DirectiveExtractor
from brand_compliance.plugins.extractors.token_table import TokenTableExtractor
from brand_compliance.plugins.extractors.typography import TypographyExtractor


def register_extractors(
    registry: PluginRegistry,
    directive_keywords: tuple[str, ...] | None = None,
    bullet_specs: Iterable[tuple[str, str]] = (),
) -> None:
    """Register every built-in extractor.

    ``bullet_specs`` lists the (section, label) bullets to read as specs.
    """
    registry.register(TokenTableExtractor())
    registry.register(TypographyExtractor())
    registry.register(ComponentExtractor())
    registry.register(CssBlockExtractor())
    registry.register(BulletSpecExtractor(bullet_specs))
    registry.register(
        DirectiveExtractor(directive_keywords)
        if directive_keywords
        else DirectiveExtractor()
    )
