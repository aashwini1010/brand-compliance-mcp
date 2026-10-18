"""Applier for component rules (buttons, inputs, labels)."""

from brand_compliance.plugins.appliers.base import RoleStyleApplier


class ComponentApplier(RoleStyleApplier):
    """Applies component table rows and bullet specs."""

    name = "component"
    categories = frozenset({"component", "component_spec"})
