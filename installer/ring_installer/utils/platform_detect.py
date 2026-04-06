"""
Platform detection utilities for Ring installer.

Provides functions to detect which AI platforms are installed on the system
and retrieve their version information.
"""

import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ring_installer.adapters import SUPPORTED_PLATFORMS

logger = logging.getLogger(__name__)


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
    details: Dict[str, Any] = field(default_factory=dict)


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
        platform_id: Platform identifier (claude, codex, factory, opencode, pi)

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


def _validate_env_path(env_var: str, candidate: str, default: Path) -> Path:
    """Validate an environment-provided path, falling back to default if unsafe."""
    path = Path(candidate).expanduser().resolve()
    home = Path.home().resolve()

    try:
        path.relative_to(home)
        return path
    except ValueError:
        logger.warning(
            "Ignoring %s=%s: path must be under home directory",
            env_var,
            candidate,
        )
        return Path(default).expanduser().resolve()


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
        "codex": _detect_codex,
        "factory": _detect_factory,
        "opencode": _detect_opencode,
    }

    detector = detectors.get(platform_id.lower())
    if detector:
        return detector()

    return PlatformInfo(
        platform_id=platform_id,
        name=platform_id.title(),
        installed=False
    )


# Allowed binary path prefixes for security validation
_ALLOWED_BINARY_PREFIXES = [
    Path("/usr"),
    Path("/opt"),
    Path("/bin"),
    Path("/sbin"),
]


def _is_binary_path_allowed(binary_path: Path) -> bool:
    """
    Validate that a binary path is from an expected location.

    Security: Prevents executing binaries from untrusted locations.

    Args:
        binary_path: Path to the binary to validate

    Returns:
        True if the binary is in an allowed location
    """
    resolved = binary_path.resolve()

    # Check system paths
    for prefix in _ALLOWED_BINARY_PREFIXES:
        if prefix.exists():
            try:
                resolved.relative_to(prefix)
                return True
            except ValueError:
                continue

    # Check user-local paths (common for npm/pip installs)
    home = Path.home()
    allowed_user_paths = [
        home / ".local" / "bin",
        home / ".local" / "share",
        home / "bin",
        home / ".cargo" / "bin",
        home / ".npm-global" / "bin",
    ]

    for user_path in allowed_user_paths:
        if user_path.exists():
            try:
                resolved.relative_to(user_path)
                return True
            except ValueError:
                continue

    # macOS specific paths
    if sys.platform == "darwin":
        macos_paths = [
            Path("/Applications"),
            home / "Applications",
            Path("/Library"),
            home / "Library",
        ]
        for macos_path in macos_paths:
            if macos_path.exists():
                try:
                    resolved.relative_to(macos_path)
                    return True
                except ValueError:
                    continue

    # Windows specific paths
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("PROGRAMFILES", "")
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "")

        win_paths = [p for p in [local_app_data, program_files, program_files_x86] if p]
        for win_path in win_paths:
            try:
                resolved.relative_to(Path(win_path))
                return True
            except ValueError:
                continue

    return False


def _detect_generic_cli_platform(
    platform_id: str,
    name: str,
    config_dir_name: str,
    binary_name: Optional[str] = None,
) -> PlatformInfo:
    """
    Generic platform detection for CLI-based platforms.

    Shared logic for platforms that have a config directory and optional CLI binary.

    Args:
        platform_id: Platform identifier (e.g., "claude", "factory")
        name: Human-readable platform name (e.g., "Claude Code")
        config_dir_name: Name of the config directory (e.g., ".claude")
        binary_name: Optional binary name to search in PATH

    Returns:
        PlatformInfo with detection results
    """
    # Allow environment variable override for config path (validated)
    env_var = f"{platform_id.upper()}_CONFIG_PATH"
    env_path = os.environ.get(env_var)

    if env_path:
        config_path = _validate_env_path(env_var, env_path, Path.home() / config_dir_name)
    else:
        config_path = Path.home() / config_dir_name

    info = PlatformInfo(
        platform_id=platform_id,
        name=name,
        installed=False
    )

    # Check config directory
    if config_path.exists():
        info.config_path = config_path
        info.install_path = config_path

    # Check for binary if specified
    if binary_name:
        binary = shutil.which(binary_name)
        if binary:
            binary_path = Path(binary)

            # Security: Validate binary is from allowed location
            if _is_binary_path_allowed(binary_path):
                info.binary_path = binary_path
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
                except subprocess.TimeoutExpired:
                    logger.warning("Binary %s timed out during version check", binary)
                except (subprocess.SubprocessError, FileNotFoundError) as e:
                    logger.debug("Binary %s version check failed: %s", binary, e)
            else:
                logger.warning(
                    "Binary %s found at %s but path is not in allowed locations",
                    binary_name, binary_path
                )

    # Config directory without binary indicates partial install
    if not info.installed and config_path.exists():
        info.partial = True
        info.details["note"] = "Config directory exists but binary not found"

    return info


def _detect_claude() -> PlatformInfo:
    """
    Detect Claude Code installation.

    Checks for:
    - ~/.claude directory (or CLAUDE_CONFIG_PATH env var)
    - claude binary in PATH
    """
    return _detect_generic_cli_platform(
        platform_id="claude",
        name="Claude Code",
        config_dir_name=".claude",
        binary_name="claude",
    )


def _detect_codex() -> PlatformInfo:
    """
    Detect Codex CLI installation.

    Checks for:
    - ~/.codex directory (or CODEX_CONFIG_PATH env var)
    - codex binary in PATH
    """
    return _detect_generic_cli_platform(
        platform_id="codex",
        name="Codex",
        config_dir_name=".codex",
        binary_name="codex",
    )


def _detect_factory() -> PlatformInfo:
    """
    Detect Factory AI installation.

    Checks for:
    - ~/.factory directory (or FACTORY_CONFIG_PATH env var)
    - factory binary in PATH
    """
    return _detect_generic_cli_platform(
        platform_id="factory",
        name="Factory AI",
        config_dir_name=".factory",
        binary_name="factory",
    )


def _detect_opencode() -> PlatformInfo:
    """
    Detect OpenCode installation.

    Checks for:
    - ~/.config/opencode directory (or OPENCODE_CONFIG_PATH env var)
    - opencode binary in PATH
    """
    return _detect_generic_cli_platform(
        platform_id="opencode",
        name="OpenCode",
        config_dir_name=".config/opencode",
        binary_name="opencode",
    )


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
