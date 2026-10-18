"""Plugin registry: finds and loads plugins, built-in or installed later."""

import logging
from collections.abc import Callable, Iterable
from importlib.metadata import EntryPoint, entry_points
from typing import Any, TypeVar, cast

from brand_compliance.core.contracts import (
    ArtifactHandler,
    Reporter,
    RuleApplier,
    RuleExtractor,
    SourceAdapter,
    StyleWriter,
    Verifier,
)
from brand_compliance.core.errors import PluginError, UnsupportedFormatError

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "brand_compliance.plugins"

PLUGIN_KINDS: tuple[type, ...] = (
    SourceAdapter,
    RuleExtractor,
    ArtifactHandler,
    RuleApplier,
    StyleWriter,
    Verifier,
    Reporter,
)

T = TypeVar("T")


class PluginRegistry:
    """Holds plugins grouped by the interface they implement."""

    def __init__(self) -> None:
        self._plugins: dict[type, list[Any]] = {kind: [] for kind in PLUGIN_KINDS}

    def register(self, plugin: object, replace: bool = False) -> type:
        """Register a plugin under the single interface it implements.

        Returns the interface it was registered as. Raises ``PluginError`` if it
        matches none or several interfaces, has no name, or reuses a name. With
        ``replace=True`` a plugin of the same name is swapped out instead.
        """
        matches = [kind for kind in PLUGIN_KINDS if isinstance(plugin, kind)]
        if len(matches) != 1:
            raise PluginError(
                f"Plugin {plugin!r} must implement exactly one interface; "
                f"matched {[kind.__name__ for kind in matches]}"
            )
        kind = matches[0]
        name = getattr(plugin, "name", "")
        if not isinstance(name, str) or not name:
            raise PluginError(f"Plugin {plugin!r} needs a non-empty 'name'")
        taken = any(existing.name == name for existing in self._plugins[kind])
        if taken and not replace:
            raise PluginError(f"{kind.__name__} named '{name}' is already registered")
        if taken:
            self._plugins[kind] = [p for p in self._plugins[kind] if p.name != name]
        self._plugins[kind].append(plugin)
        logger.debug("Registered %s plugin '%s'", kind.__name__, name)
        return kind

    def unregister(self, kind: type, name: str) -> None:
        """Remove the plugin of an interface with the given name.

        Raises ``PluginError`` if there is none.
        """
        remaining = [p for p in self._plugins.get(kind, []) if p.name != name]
        if len(remaining) == len(self._plugins.get(kind, [])):
            raise PluginError(f"No {kind.__name__} named '{name}'")
        self._plugins[kind] = remaining

    def plugins(self, kind: type[T]) -> list[T]:
        """Return all plugins registered for an interface, in order."""
        return list(cast("list[T]", self._plugins.get(kind, [])))

    def get(self, kind: type[T], name: str) -> T:
        """Return the plugin with the given name or raise ``PluginError``."""
        for plugin in self.plugins(kind):
            if getattr(plugin, "name", None) == name:
                return plugin
        raise PluginError(f"No {kind.__name__} named '{name}'")

    def find(self, kind: type[T], predicate: Callable[[T], bool]) -> T:
        """Return the first plugin of a kind that satisfies the predicate.

        Raises ``UnsupportedFormatError`` when none does.
        """
        for plugin in self.plugins(kind):
            if predicate(plugin):
                return plugin
        raise UnsupportedFormatError(f"No {kind.__name__} can handle this input")

    def describe(self) -> dict[str, list[str]]:
        """Return plugin names per interface, for the ``list_plugins`` tool."""
        return {
            kind.__name__: [p.name for p in plugins]
            for kind, plugins in self._plugins.items()
        }


def load_entry_point_plugins(
    registry: PluginRegistry,
    group: str = ENTRY_POINT_GROUP,
    entry_points_fn: Callable[..., Iterable[EntryPoint]] = entry_points,
) -> int:
    """Register plugins from installed packages; return how many were added.

    Each entry point must be a zero-argument callable returning a plugin.
    A broken plugin is logged and skipped so it cannot stop the server.
    """
    added = 0
    for entry_point in entry_points_fn(group=group):
        try:
            registry.register(entry_point.load()())
            added += 1
        except (PluginError, ImportError, AttributeError, TypeError) as exc:
            logger.error("Skipping plugin '%s': %s", entry_point.name, exc)
    return added
