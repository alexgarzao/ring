"""
Platform adapters for Ring installer.

This module provides adapters for transforming Ring components to various
AI platform formats.

Supported Platforms:
- Claude Code: Native Ring format (passthrough)
- Factory AI: Agents -> Droids transformation
- Cursor: Skills -> Rules, Agents/Commands -> Workflows
- Cline: All components -> Prompts
"""

from typing import Dict, Type, Optional

from ring_installer.adapters.base import PlatformAdapter
from ring_installer.adapters.claude import ClaudeAdapter
from ring_installer.adapters.factory import FactoryAdapter
from ring_installer.adapters.cursor import CursorAdapter
from ring_installer.adapters.cline import ClineAdapter

# Registry of supported platforms and their adapters
ADAPTER_REGISTRY: Dict[str, Type[PlatformAdapter]] = {
    "claude": ClaudeAdapter,
    "factory": FactoryAdapter,
    "cursor": CursorAdapter,
    "cline": ClineAdapter,
}

# List of supported platform identifiers
SUPPORTED_PLATFORMS = list(ADAPTER_REGISTRY.keys())


def get_adapter(platform: str, config: Optional[dict] = None) -> PlatformAdapter:
    """
    Get an adapter instance for the specified platform.

    Args:
        platform: Platform identifier (claude, factory, cursor, cline)
        config: Optional platform-specific configuration

    Returns:
        Instantiated adapter for the platform

    Raises:
        ValueError: If the platform is not supported
    """
    platform = platform.lower()

    if platform not in ADAPTER_REGISTRY:
        supported = ", ".join(SUPPORTED_PLATFORMS)
        raise ValueError(
            f"Unsupported platform: '{platform}'. "
            f"Supported platforms are: {supported}"
        )

    adapter_class = ADAPTER_REGISTRY[platform]
    return adapter_class(config)


def register_adapter(platform: str, adapter_class: Type[PlatformAdapter]) -> None:
    """
    Register a custom adapter for a platform.

    This allows extending the installer with support for additional platforms.

    Args:
        platform: Platform identifier
        adapter_class: Adapter class (must inherit from PlatformAdapter)

    Raises:
        TypeError: If adapter_class doesn't inherit from PlatformAdapter
    """
    if not issubclass(adapter_class, PlatformAdapter):
        raise TypeError(
            f"Adapter class must inherit from PlatformAdapter, "
            f"got {adapter_class.__name__}"
        )

    ADAPTER_REGISTRY[platform.lower()] = adapter_class


def list_platforms() -> list[dict]:
    """
    List all supported platforms with their details.

    Returns:
        List of platform information dictionaries
    """
    platforms = []
    for platform_id, adapter_class in ADAPTER_REGISTRY.items():
        adapter = adapter_class()
        platforms.append({
            "id": platform_id,
            "name": adapter.platform_name,
            "native_format": adapter.is_native_format(),
            "terminology": adapter.get_terminology(),
            "components": list(adapter.get_component_mapping().keys()),
        })
    return platforms


__all__ = [
    # Base class
    "PlatformAdapter",
    # Concrete adapters
    "ClaudeAdapter",
    "FactoryAdapter",
    "CursorAdapter",
    "ClineAdapter",
    # Registry and utilities
    "ADAPTER_REGISTRY",
    "SUPPORTED_PLATFORMS",
    "get_adapter",
    "register_adapter",
    "list_platforms",
]
