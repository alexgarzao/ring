"""
Ring Installer - Multi-platform AI agent skill installer.

This package provides tools to install Ring skills, agents, and commands
across multiple AI platforms including Claude Code, Factory AI, Cursor, and Cline.
"""

__version__ = "0.1.0"
__author__ = "Lerian Studio"
__license__ = "Apache-2.0"

from ring_installer.core import (
    InstallTarget,
    InstallOptions,
    InstallResult,
    install,
    update,
    uninstall,
    load_manifest,
)
from ring_installer.adapters import (
    PlatformAdapter,
    ClaudeAdapter,
    FactoryAdapter,
    CursorAdapter,
    ClineAdapter,
    get_adapter,
    SUPPORTED_PLATFORMS,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Core functions
    "InstallTarget",
    "InstallOptions",
    "InstallResult",
    "install",
    "update",
    "uninstall",
    "load_manifest",
    # Adapters
    "PlatformAdapter",
    "ClaudeAdapter",
    "FactoryAdapter",
    "CursorAdapter",
    "ClineAdapter",
    "get_adapter",
    "SUPPORTED_PLATFORMS",
]
