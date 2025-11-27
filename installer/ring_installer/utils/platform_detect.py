"""
Platform detection utilities for Ring installer.

Provides functions to detect which AI platforms are installed on the system
and retrieve their version information.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

from ring_installer.adapters import SUPPORTED_PLATFORMS


@dataclass
class PlatformInfo:
    """Information about an installed platform."""
    platform_id: str
    name: str
    installed: bool
    partial: bool = False
    version: Optional[str] = None
    install_path: Optional[Path] = None
    config_path: Optional[Path] = None
    binary_path: Optional[Path] = None
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


def detect_installed_platforms() -> List[PlatformInfo]:
    """
    Detect all supported platforms that are installed on the system.

    Returns:
        List of PlatformInfo objects for each detected platform
    """
    platforms = []

    for platform_id in SUPPORTED_PLATFORMS:
        info = _detect_platform(platform_id)
        if info.installed:
            platforms.append(info)

    return platforms


def is_platform_installed(platform_id: str) -> bool:
    """
    Check if a specific platform is installed.

    Args:
        platform_id: Platform identifier (claude, factory, cursor, cline)

    Returns:
        True if the platform is installed
    """
    info = _detect_platform(platform_id)
    return info.installed


def get_platform_version(platform_id: str) -> Optional[str]:
    """
    Get the version of an installed platform.

    Args:
        platform_id: Platform identifier

    Returns:
        Version string, or None if not installed or version unavailable
    """
    info = _detect_platform(platform_id)
    return info.version if info.installed else None


def get_platform_info(platform_id: str) -> PlatformInfo:
    """
    Get detailed information about a platform.

    Args:
        platform_id: Platform identifier

    Returns:
        PlatformInfo object with detection results
    """
    return _detect_platform(platform_id)


def _detect_platform(platform_id: str) -> PlatformInfo:
    """
    Detect a specific platform.

    Args:
        platform_id: Platform identifier

    Returns:
        PlatformInfo with detection results
    """
    detectors = {
        "claude": _detect_claude,
        "factory": _detect_factory,
        "cursor": _detect_cursor,
        "cline": _detect_cline,
    }

    detector = detectors.get(platform_id.lower())
    if detector:
        return detector()

    return PlatformInfo(
        platform_id=platform_id,
        name=platform_id.title(),
        installed=False
    )


def _detect_claude() -> PlatformInfo:
    """
    Detect Claude Code installation.

    Checks for:
    - ~/.claude directory
    - claude binary in PATH
    """
    info = PlatformInfo(
        platform_id="claude",
        name="Claude Code",
        installed=False
    )

    # Check config directory
    config_path = Path.home() / ".claude"
    if config_path.exists():
        info.config_path = config_path
        info.install_path = config_path

    # Check for binary
    binary = shutil.which("claude")
    if binary:
        info.binary_path = Path(binary)
        info.installed = True

        # Get version using resolved binary path
        try:
            result = subprocess.run(
                [binary, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
                if version_match:
                    info.version = version_match.group(1)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass

    # Even without binary, config directory indicates partial install
    if not info.installed and config_path.exists():
        info.installed = False  # Don't mark as installed
        info.partial = True  # Mark as partial
        info.details["note"] = "Config directory exists but binary not found"

    return info


def _detect_factory() -> PlatformInfo:
    """
    Detect Factory AI installation.

    Checks for:
    - ~/.factory directory
    - factory binary in PATH
    """
    info = PlatformInfo(
        platform_id="factory",
        name="Factory AI",
        installed=False
    )

    # Check config directory
    config_path = Path.home() / ".factory"
    if config_path.exists():
        info.config_path = config_path
        info.install_path = config_path

    # Check for binary
    binary = shutil.which("factory")
    if binary:
        info.binary_path = Path(binary)
        info.installed = True

        # Get version using resolved binary path
        try:
            result = subprocess.run(
                [binary, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
                if version_match:
                    info.version = version_match.group(1)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass

    if not info.installed and config_path.exists():
        info.installed = False  # Don't mark as installed
        info.partial = True  # Mark as partial
        info.details["note"] = "Config directory exists but binary not found"

    return info


def _detect_cursor() -> PlatformInfo:
    """
    Detect Cursor installation.

    Checks for:
    - ~/.cursor directory
    - Cursor application in standard locations
    """
    info = PlatformInfo(
        platform_id="cursor",
        name="Cursor",
        installed=False
    )

    # Check config directory
    config_path = Path.home() / ".cursor"
    if config_path.exists():
        info.config_path = config_path
        info.install_path = config_path

    # Check for application
    app_paths = _get_cursor_app_paths()
    for app_path in app_paths:
        if app_path.exists():
            info.binary_path = app_path
            info.installed = True

            # Try to get version from package.json or similar
            version = _get_cursor_version(app_path)
            if version:
                info.version = version
            break

    if not info.installed and config_path.exists():
        info.installed = False  # Don't mark as installed
        info.partial = True  # Mark as partial
        info.details["note"] = "Config directory exists but application not found"

    return info


def _detect_cline() -> PlatformInfo:
    """
    Detect Cline installation.

    Checks for:
    - ~/.cline directory
    - Cline VS Code extension
    """
    info = PlatformInfo(
        platform_id="cline",
        name="Cline",
        installed=False
    )

    # Check config directory
    config_path = Path.home() / ".cline"
    if config_path.exists():
        info.config_path = config_path
        info.install_path = config_path
        info.installed = True

    # Check for VS Code extension
    extension_info = _find_vscode_extension("saoudrizwan.claude-dev")
    if extension_info:
        info.installed = True
        info.version = extension_info.get("version")
        info.details["extension_path"] = extension_info.get("path")
        info.details["extension_id"] = "saoudrizwan.claude-dev"

    return info


def _get_cursor_app_paths() -> List[Path]:
    """Get potential Cursor application paths based on platform."""
    paths = []

    if sys.platform == "darwin":
        paths.extend([
            Path("/Applications/Cursor.app"),
            Path.home() / "Applications/Cursor.app",
        ])
    elif sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            paths.append(Path(local_app_data) / "Programs/cursor/Cursor.exe")
        paths.append(Path("C:/Program Files/Cursor/Cursor.exe"))
    else:  # Linux
        paths.extend([
            Path("/usr/bin/cursor"),
            Path("/usr/local/bin/cursor"),
            Path.home() / ".local/bin/cursor",
            Path("/opt/Cursor/cursor"),
        ])

    return paths


def _get_cursor_version(app_path: Path) -> Optional[str]:
    """Try to extract Cursor version from application."""
    if sys.platform == "darwin":
        # Try Info.plist
        plist_path = app_path / "Contents/Info.plist"
        if plist_path.exists():
            try:
                import plistlib
                with open(plist_path, "rb") as f:
                    plist = plistlib.load(f)
                    return plist.get("CFBundleShortVersionString")
            except Exception:
                pass

        # Try package.json in resources
        package_json = app_path / "Contents/Resources/app/package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    return data.get("version")
            except Exception:
                pass

    elif sys.platform == "win32":
        # Try version from executable (would need win32api)
        # Fall back to checking package.json if available
        pass

    return None


def _find_vscode_extension(extension_id: str) -> Optional[Dict[str, Any]]:
    """
    Find a VS Code extension and get its information.

    Args:
        extension_id: Extension identifier (publisher.name)

    Returns:
        Dictionary with extension info, or None if not found
    """
    extension_paths = _get_vscode_extension_paths()

    for ext_dir in extension_paths:
        if not ext_dir.exists():
            continue

        # Look for extension directory
        for entry in ext_dir.iterdir():
            if entry.is_dir() and entry.name.startswith(extension_id):
                # Found the extension
                package_json = entry / "package.json"
                if package_json.exists():
                    try:
                        with open(package_json) as f:
                            data = json.load(f)
                            return {
                                "path": str(entry),
                                "version": data.get("version"),
                                "name": data.get("displayName", data.get("name")),
                            }
                    except Exception:
                        return {"path": str(entry)}
                return {"path": str(entry)}

    return None


def _get_vscode_extension_paths() -> List[Path]:
    """Get VS Code extension directories based on platform."""
    paths = []

    if sys.platform == "darwin":
        paths.extend([
            Path.home() / ".vscode/extensions",
            Path.home() / ".vscode-insiders/extensions",
        ])
    elif sys.platform == "win32":
        user_profile = os.environ.get("USERPROFILE", "")
        if user_profile:
            paths.extend([
                Path(user_profile) / ".vscode/extensions",
                Path(user_profile) / ".vscode-insiders/extensions",
            ])
    else:  # Linux
        paths.extend([
            Path.home() / ".vscode/extensions",
            Path.home() / ".vscode-insiders/extensions",
            Path.home() / ".vscode-server/extensions",
        ])

    return paths


def get_system_info() -> Dict[str, Any]:
    """
    Get system information relevant to installation.

    Returns:
        Dictionary with system details
    """
    return {
        "platform": sys.platform,
        "python_version": sys.version,
        "home_directory": str(Path.home()),
        "current_directory": str(Path.cwd()),
        "path": os.environ.get("PATH", "").split(os.pathsep),
    }


def print_detection_report() -> None:
    """Print a human-readable report of detected platforms."""
    platforms = detect_installed_platforms()

    print("Ring Installer - Platform Detection Report")
    print("=" * 50)

    if not platforms:
        print("\nNo supported platforms detected.")
        print("\nSupported platforms:")
        for platform_id in SUPPORTED_PLATFORMS:
            print(f"  - {platform_id}")
        return

    print(f"\nDetected {len(platforms)} platform(s):\n")

    for info in platforms:
        print(f"  {info.name} ({info.platform_id})")
        if info.version:
            print(f"    Version: {info.version}")
        if info.install_path:
            print(f"    Install path: {info.install_path}")
        if info.binary_path:
            print(f"    Binary: {info.binary_path}")
        if info.details:
            for key, value in info.details.items():
                print(f"    {key}: {value}")
        print()
