"""Names the tool puts in the artifacts it writes, so it can recognise its own work."""

from typing import Final

STYLE_ID: Final = "brand-compliance"
FONT_LINK_ATTRIBUTE: Final = "data-brand-compliance"
ROLE_ATTRIBUTE: Final = "data-brand-role"
SURFACE_ATTRIBUTE: Final = "data-brand-surface"
FORCE_ATTRIBUTE: Final = "data-brand-force"
ANNOTATION_ATTRIBUTES: Final = (ROLE_ATTRIBUTE, SURFACE_ATTRIBUTE, FORCE_ATTRIBUTE)
