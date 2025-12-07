"""
Utility modules for Ring installer.
"""

from ring_installer.utils.fs import (
    copy_with_transform,
    backup_existing,
    ensure_directory,
    safe_remove,
    get_file_hash,
    are_files_identical,
)
from ring_installer.utils.platform_detect import (
    detect_installed_platforms,
    get_platform_version,
    is_platform_installed,
)
from ring_installer.utils.version import (
    Version,
    InstallManifest,
    compare_versions,
    is_update_available,
    get_ring_version,
    get_installed_version,
    check_for_updates,
    save_install_manifest,
)

__all__ = [
    # Filesystem utilities
    "copy_with_transform",
    "backup_existing",
    "ensure_directory",
    "safe_remove",
    "get_file_hash",
    "are_files_identical",
    # Platform detection
    "detect_installed_platforms",
    "get_platform_version",
    "is_platform_installed",
    # Version management
    "Version",
    "InstallManifest",
    "compare_versions",
    "is_update_available",
    "get_ring_version",
    "get_installed_version",
    "check_for_updates",
    "save_install_manifest",
]
