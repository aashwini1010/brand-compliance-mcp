"""Applier for the default page surface."""

from brand_compliance.plugins.appliers.base import RoleStyleApplier


class SurfaceApplier(RoleStyleApplier):
    """Applies the default page background."""

    name = "surface"
    categories = frozenset({"surface"})
