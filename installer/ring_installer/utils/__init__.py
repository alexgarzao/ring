"""
Utility modules for Ring installer.
"""

from ring_installer.utils.fs import (
    copy_with_transform,
    backup_existing,
    ensure_directory,
    safe_remove,
    get_file_hash,
)
from ring_installer.utils.platform_detect import (
    detect_installed_platforms,
    get_platform_version,
    is_platform_installed,
)

__all__ = [
    # Filesystem utilities
    "copy_with_transform",
    "backup_existing",
    "ensure_directory",
    "safe_remove",
    "get_file_hash",
    # Platform detection
    "detect_installed_platforms",
    "get_platform_version",
    "is_platform_installed",
]
