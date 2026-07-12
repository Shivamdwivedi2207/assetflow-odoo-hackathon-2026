"""Compatibility import for the shared in-memory AssetFlow database."""

from .__registry import CentralRegistry, GLOBAL_DB

__all__ = ["CentralRegistry", "GLOBAL_DB"]
