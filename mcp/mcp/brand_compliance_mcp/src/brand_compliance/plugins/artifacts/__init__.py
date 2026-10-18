"""HTML artifact handlers. Add one line to ``register_artifacts`` per type."""

from brand_compliance.core.registry import PluginRegistry
from brand_compliance.plugins.artifacts.email import EmailArtifactHandler
from brand_compliance.plugins.artifacts.static import StaticArtifactHandler


def register_artifacts(registry: PluginRegistry) -> None:
    """Register every built-in artifact handler."""
    registry.register(StaticArtifactHandler())
    registry.register(EmailArtifactHandler())
