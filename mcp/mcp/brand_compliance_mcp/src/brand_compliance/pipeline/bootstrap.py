"""Build the plugin registry with every built-in plugin."""

import logging

from brand_compliance.core.registry import PluginRegistry, load_entry_point_plugins
from brand_compliance.core.settings import Settings
from brand_compliance.plugins.appliers import register_appliers
from brand_compliance.plugins.appliers.support import load_email_support
from brand_compliance.plugins.appliers.tokens import load_token_maps
from brand_compliance.plugins.artifacts import register_artifacts
from brand_compliance.plugins.artifacts.roles import load_role_aliases
from brand_compliance.plugins.extractors import register_extractors
from brand_compliance.plugins.reporters import register_reporters
from brand_compliance.plugins.sources import register_sources
from brand_compliance.plugins.verifiers import register_verifiers
from brand_compliance.plugins.writers import register_writers
from brand_compliance.rules.vocabulary import Vocabulary

logger = logging.getLogger(__name__)


def build_registry(settings: Settings, vocabulary: Vocabulary) -> PluginRegistry:
    """Register the built-in plugins, then any installed through entry points."""
    registry = PluginRegistry()
    register_sources(registry, settings.limits.max_guide_bytes)
    register_extractors(
        registry,
        tuple(vocabulary.directive_keywords) or None,
        [(spec.section, spec.label) for spec in vocabulary.bullet_specs],
    )
    register_artifacts(registry)
    register_appliers(
        registry, load_role_aliases(), load_email_support(), load_token_maps()
    )
    register_writers(registry)
    register_verifiers(registry)
    register_reporters(registry)
    added = load_entry_point_plugins(registry)
    logger.info("Plugin registry ready (%d external plugin(s))", added)
    return registry
