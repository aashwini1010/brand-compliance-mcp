"""Verifiers. Per-run ones (original-intact, idempotence) are built by the caller."""

from brand_compliance.core.registry import PluginRegistry
from brand_compliance.plugins.verifiers.assets import AssetsVerifier
from brand_compliance.plugins.verifiers.contrast import ContrastVerifier
from brand_compliance.plugins.verifiers.forbidden import ForbiddenColorVerifier
from brand_compliance.plugins.verifiers.structure import StructureVerifier

CHANGE_VERIFIERS = ("contrast", "forbidden-color")
OUTPUT_VERIFIERS = ("structure", "assets")


def register_verifiers(registry: PluginRegistry) -> None:
    """Register the verifiers that need no per-run information."""
    registry.register(ContrastVerifier())
    registry.register(ForbiddenColorVerifier())
    registry.register(StructureVerifier())
    registry.register(AssetsVerifier())
