"""Applier for text colours that depend on the surface."""

from brand_compliance.plugins.appliers.base import RoleStyleApplier


class ColorApplier(RoleStyleApplier):
    """Applies colour rules (scoped to light or dark surfaces)."""

    name = "color"
    categories = frozenset({"color"})
