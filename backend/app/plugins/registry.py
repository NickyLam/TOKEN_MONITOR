"""Plugin registry with decorator-based self-registration."""

import importlib
import logging
import pkgutil
from typing import Optional

from app.plugins.base import VendorPlugin

logger = logging.getLogger(__name__)

_PLUGINS: dict[str, VendorPlugin] = {}


def register_plugin(cls):
    """Class decorator — instantiate and add to global registry on import."""
    instance = cls()
    _PLUGINS[instance.slug] = instance
    logger.debug("Registered plugin: %s (%s)", instance.slug, instance.display_name)
    return cls


def get_plugin(slug: str) -> Optional[VendorPlugin]:
    """Retrieve a plugin by slug."""
    return _PLUGINS.get(slug)


def all_plugins() -> dict[str, VendorPlugin]:
    """Return all registered plugins."""
    return dict(_PLUGINS)


def discover_plugins():
    """Import all modules in plugins/ to trigger registration."""
    package = importlib.import_module("app.plugins")
    for _, name, _ in pkgutil.iter_modules(package.__path__):
        if name not in ("base", "registry", "__init__"):
            try:
                importlib.import_module(f"app.plugins.{name}")
            except Exception as e:
                logger.warning("Failed to load plugin '%s': %s", name, e)
