"""Rule appliers. Add one line to ``register_appliers`` per new applier."""

from brand_compliance.core.registry import PluginRegistry
from brand_compliance.plugins.appliers.color import ColorApplier
from brand_compliance.plugins.appliers.component import ComponentApplier
from brand_compliance.plugins.appliers.font import FontFamilyApplier, FontSourceApplier
from brand_compliance.plugins.appliers.support import EmailSupport
from brand_compliance.plugins.appliers.surface import SurfaceApplier
from brand_compliance.plugins.appliers.tokens import TokenApplier, TokenMap
from brand_compliance.plugins.appliers.typography import TypographyApplier


def register_appliers(
    registry: PluginRegistry,
    aliases: dict[str, str] | None = None,
    email_support: EmailSupport | None = None,
    token_maps: list[TokenMap] | None = None,
) -> None:
    """Register every built-in applier.

    ``aliases`` maps rule roles to element roles; ``email_support`` tells the
    appliers what email clients cannot display; ``token_maps`` says which page
    colour variables take which palette token.
    """
    registry.register(TypographyApplier(aliases, email_support))
    registry.register(ColorApplier(aliases, email_support))
    registry.register(ComponentApplier(aliases, email_support))
    registry.register(SurfaceApplier(aliases, email_support))
    registry.register(TokenApplier(token_maps))
    registry.register(FontFamilyApplier())
    registry.register(FontSourceApplier())
