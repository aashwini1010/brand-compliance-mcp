"""Applier for type-scale rules (size, weight, spacing, style)."""

from brand_compliance.plugins.appliers.base import RoleStyleApplier


class TypographyApplier(RoleStyleApplier):
    """Applies typography rules to the elements that have the rule's role."""

    name = "typography"
    categories = frozenset({"typography"})
