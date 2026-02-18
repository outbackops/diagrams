"""Node registry service — introspect the diagrams library to build the
provider → category → service map. Read-only, built at startup."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings


@dataclass
class NodeRegistryEntry:
    provider: str
    category: str
    class_name: str
    aliases: list[str] = field(default_factory=list)
    icon_path: str = ""
    module_path: str = ""


class NodeRegistry:
    """Singleton registry of all available diagram node classes."""

    def __init__(self) -> None:
        self._entries: list[NodeRegistryEntry] = []
        self._by_provider: dict[str, list[NodeRegistryEntry]] = {}
        self._loaded = False

    def load(self) -> None:
        """Scan the diagrams library and build the registry."""
        if self._loaded:
            return

        import diagrams

        base_path = Path(diagrams.__file__).parent
        # Walk all provider subpackages
        for importer, modname, ispkg in pkgutil.walk_packages(
            path=[str(base_path)], prefix="diagrams."
        ):
            # Skip non-provider modules
            parts = modname.split(".")
            if len(parts) < 3 or parts[1] in ("base", "custom", "c4"):
                continue

            provider = parts[1]
            category = parts[2] if len(parts) >= 3 else ""

            try:
                module = importlib.import_module(modname)
            except Exception:
                continue

            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Only include classes that are Node subclasses defined in this module
                if not hasattr(obj, "_provider") or obj.__module__ != modname:
                    continue
                if name.startswith("_"):
                    continue

                icon_path = ""
                if hasattr(obj, "_icon") and obj._icon:
                    icon_dir = getattr(obj, "_icon_dir", "")
                    icon_path = f"{icon_dir}/{obj._icon}" if icon_dir else obj._icon

                entry = NodeRegistryEntry(
                    provider=provider,
                    category=category,
                    class_name=name,
                    aliases=[],
                    icon_path=icon_path,
                    module_path=f"{modname}.{name}",
                )
                self._entries.append(entry)

                if provider not in self._by_provider:
                    self._by_provider[provider] = []
                self._by_provider[provider].append(entry)

        self._loaded = True

    @property
    def providers(self) -> list[str]:
        self.load()
        return sorted(self._by_provider.keys())

    def get_nodes_for_provider(self, provider: str) -> list[NodeRegistryEntry]:
        self.load()
        return self._by_provider.get(provider, [])

    def search(self, query: str) -> list[NodeRegistryEntry]:
        self.load()
        q = query.lower()
        return [
            e
            for e in self._entries
            if q in e.class_name.lower()
            or q in e.category.lower()
            or q in e.provider.lower()
            or q in e.module_path.lower()
        ]

    def get_all(self) -> list[NodeRegistryEntry]:
        self.load()
        return self._entries

    def get_registry_context(self) -> str:
        """Return a text summary of the full registry for AI prompt context."""
        self.load()
        lines = []
        for provider in self.providers:
            nodes = self.get_nodes_for_provider(provider)
            by_cat: dict[str, list[str]] = {}
            for n in nodes:
                by_cat.setdefault(n.category, []).append(n.class_name)
            lines.append(f"\n## Provider: {provider}")
            for cat, classes in sorted(by_cat.items()):
                lines.append(f"  {cat}: {', '.join(sorted(classes))}")
        return "\n".join(lines)


# Singleton instance
node_registry = NodeRegistry()
