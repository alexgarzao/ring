"""
Core installation logic for Ring multi-platform installer.

This module provides the main installation, update, and uninstall functions
along with supporting data structures.
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

from ring_installer.adapters import get_adapter, SUPPORTED_PLATFORMS, PlatformAdapter


class InstallStatus(Enum):
    """Status of an installation operation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class InstallTarget:
    """
    Represents a target platform for installation.

    Attributes:
        platform: Platform identifier (claude, factory, cursor, cline)
        path: Optional custom installation path (uses default if None)
        components: List of component types to install (agents, commands, skills)
                   If None, installs all components.
    """
    platform: str
    path: Optional[Path] = None
    components: Optional[List[str]] = None

    def __post_init__(self):
        """Validate the target configuration."""
        if self.platform not in SUPPORTED_PLATFORMS:
            raise ValueError(
                f"Unsupported platform: '{self.platform}'. "
                f"Supported: {', '.join(SUPPORTED_PLATFORMS)}"
            )
        if self.path is not None:
            self.path = Path(self.path).expanduser()


@dataclass
class InstallOptions:
    """
    Options controlling the installation behavior.

    Attributes:
        dry_run: If True, show what would be done without making changes
        force: If True, overwrite existing files without prompting
        backup: If True, create backups before overwriting
        verbose: If True, output detailed progress information
        plugin_names: List of plugin names to install (None = all)
        exclude_plugins: List of plugin names to exclude
    """
    dry_run: bool = False
    force: bool = False
    backup: bool = True
    verbose: bool = False
    plugin_names: Optional[List[str]] = None
    exclude_plugins: Optional[List[str]] = None


@dataclass
class ComponentResult:
    """Result of installing a single component."""
    source_path: Path
    target_path: Path
    status: InstallStatus
    message: str = ""
    backup_path: Optional[Path] = None


@dataclass
class InstallResult:
    """
    Result of an installation operation.

    Attributes:
        status: Overall status of the installation
        targets: List of platforms that were targeted
        components_installed: Count of successfully installed components
        components_failed: Count of failed component installations
        components_skipped: Count of skipped components
        errors: List of error messages
        warnings: List of warning messages
        details: Detailed results per component
        timestamp: When the installation was performed
    """
    status: InstallStatus
    targets: List[str] = field(default_factory=list)
    components_installed: int = 0
    components_failed: int = 0
    components_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: List[ComponentResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_success(self, source: Path, target: Path, backup: Optional[Path] = None) -> None:
        """Record a successful component installation."""
        self.components_installed += 1
        self.details.append(ComponentResult(
            source_path=source,
            target_path=target,
            status=InstallStatus.SUCCESS,
            backup_path=backup
        ))

    def add_failure(self, source: Path, target: Path, message: str) -> None:
        """Record a failed component installation."""
        self.components_failed += 1
        self.errors.append(f"{source}: {message}")
        self.details.append(ComponentResult(
            source_path=source,
            target_path=target,
            status=InstallStatus.FAILED,
            message=message
        ))

    def add_skip(self, source: Path, target: Path, message: str) -> None:
        """Record a skipped component."""
        self.components_skipped += 1
        self.warnings.append(f"{source}: {message}")
        self.details.append(ComponentResult(
            source_path=source,
            target_path=target,
            status=InstallStatus.SKIPPED,
            message=message
        ))

    def finalize(self) -> None:
        """Set the overall status based on component results."""
        if self.components_failed == 0 and self.components_installed > 0:
            self.status = InstallStatus.SUCCESS
        elif self.components_installed > 0:
            self.status = InstallStatus.PARTIAL
        elif self.components_skipped > 0 and self.components_failed == 0:
            self.status = InstallStatus.SKIPPED
        else:
            self.status = InstallStatus.FAILED


def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the platform manifest configuration.

    Args:
        manifest_path: Path to platforms.json. If None, uses the bundled manifest.

    Returns:
        Dictionary containing platform configurations

    Raises:
        FileNotFoundError: If the manifest file doesn't exist
        json.JSONDecodeError: If the manifest is invalid JSON
    """
    if manifest_path is None:
        # Use bundled manifest
        manifest_path = Path(__file__).parent / "manifests" / "platforms.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Platform manifest not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def discover_ring_components(ring_path: Path, plugin_names: Optional[List[str]] = None,
                             exclude_plugins: Optional[List[str]] = None) -> Dict[str, Dict[str, List[Path]]]:
    """
    Discover Ring components (skills, agents, commands) from a Ring installation.

    Args:
        ring_path: Path to Ring repository/installation
        plugin_names: Optional list of plugin names to include
        exclude_plugins: Optional list of plugin names to exclude

    Returns:
        Dictionary mapping plugin names to their components:
        {
            "default": {
                "agents": [Path(...), ...],
                "commands": [Path(...), ...],
                "skills": [Path(...), ...],
                "hooks": [Path(...), ...]
            },
            ...
        }
    """
    components: Dict[str, Dict[str, List[Path]]] = {}

    # Check for marketplace structure
    marketplace_path = ring_path / ".claude-plugin" / "marketplace.json"
    if marketplace_path.exists():
        with open(marketplace_path) as f:
            marketplace = json.load(f)

        # Process each plugin in marketplace
        for plugin in marketplace.get("plugins", []):
            plugin_name = plugin.get("name", "").replace("ring-", "")
            source = plugin.get("source", "")

            # Check filters
            if plugin_names and plugin_name not in plugin_names:
                continue
            if exclude_plugins and plugin_name in exclude_plugins:
                continue

            # Resolve plugin path
            if source.startswith("./"):
                plugin_path = ring_path / source[2:]
            else:
                plugin_path = ring_path / source

            if plugin_path.exists():
                components[plugin_name] = _discover_plugin_components(plugin_path)
    else:
        # Single plugin structure (legacy or simple install)
        components["default"] = _discover_plugin_components(ring_path)

    return components


def _discover_plugin_components(plugin_path: Path) -> Dict[str, List[Path]]:
    """
    Discover components within a single plugin directory.

    Args:
        plugin_path: Path to the plugin directory

    Returns:
        Dictionary mapping component types to file paths
    """
    result: Dict[str, List[Path]] = {
        "agents": [],
        "commands": [],
        "skills": [],
        "hooks": []
    }

    # Discover agents
    agents_dir = plugin_path / "agents"
    if agents_dir.exists():
        result["agents"] = list(agents_dir.glob("*.md"))

    # Discover commands
    commands_dir = plugin_path / "commands"
    if commands_dir.exists():
        result["commands"] = list(commands_dir.glob("*.md"))

    # Discover skills (in subdirectories with SKILL.md)
    skills_dir = plugin_path / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    result["skills"].append(skill_file)

    # Discover hooks
    hooks_dir = plugin_path / "hooks"
    if hooks_dir.exists():
        for ext in ["*.json", "*.sh", "*.py"]:
            result["hooks"].extend(hooks_dir.glob(ext))

    return result


def install(
    source_path: Path,
    targets: List[InstallTarget],
    options: Optional[InstallOptions] = None,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> InstallResult:
    """
    Install Ring components to one or more target platforms.

    Args:
        source_path: Path to the Ring repository/installation
        targets: List of installation targets
        options: Installation options
        progress_callback: Optional callback for progress updates
                          Called with (message, current, total)

    Returns:
        InstallResult with details about what was installed
    """
    from ring_installer.utils.fs import copy_with_transform, backup_existing, ensure_directory

    options = options or InstallOptions()
    result = InstallResult(status=InstallStatus.SUCCESS, targets=[t.platform for t in targets])

    # Load manifest
    manifest = load_manifest()

    # Discover components
    components = discover_ring_components(
        source_path,
        plugin_names=options.plugin_names,
        exclude_plugins=options.exclude_plugins
    )

    # Calculate total work
    total_components = sum(
        len(files) for plugin_components in components.values()
        for files in plugin_components.values()
    ) * len(targets)

    current = 0

    # Process each target platform
    for target in targets:
        adapter = get_adapter(target.platform, manifest.get("platforms", {}).get(target.platform))
        install_path = target.path or adapter.get_install_path()
        component_mapping = adapter.get_component_mapping()

        # Process each plugin
        for plugin_name, plugin_components in components.items():
            # Process each component type
            for component_type, files in plugin_components.items():
                # Skip if component type not supported by platform
                if component_type not in component_mapping:
                    continue

                # Skip if not in target's component list
                if target.components and component_type not in target.components:
                    continue

                target_config = component_mapping[component_type]
                target_dir = install_path / target_config["target_dir"]

                # For multi-plugin installs, add plugin subdirectory
                if len(components) > 1:
                    target_dir = target_dir / plugin_name

                # Ensure target directory exists
                if not options.dry_run:
                    ensure_directory(target_dir)

                # Process each file
                for source_file in files:
                    current += 1

                    if progress_callback:
                        progress_callback(
                            f"Installing {source_file.name} to {target.platform}",
                            current,
                            total_components
                        )

                    # Determine target filename
                    if component_type == "skills":
                        # Skills use their directory name
                        skill_name = source_file.parent.name
                        target_file = target_dir / skill_name / source_file.name
                    else:
                        target_filename = adapter.get_target_filename(
                            source_file.name,
                            component_type.rstrip("s")  # agents -> agent
                        )
                        target_file = target_dir / target_filename

                    # Check if target exists
                    if target_file.exists() and not options.force:
                        result.add_skip(
                            source_file,
                            target_file,
                            "File exists (use --force to overwrite)"
                        )
                        continue

                    # Create backup if needed
                    backup_path = None
                    if target_file.exists() and options.backup and not options.dry_run:
                        backup_path = backup_existing(target_file)

                    # Read source content
                    try:
                        with open(source_file, "r", encoding="utf-8") as f:
                            content = f.read()
                    except Exception as e:
                        result.add_failure(source_file, target_file, f"Read error: {e}")
                        continue

                    # Transform content
                    try:
                        metadata = {
                            "name": source_file.stem,
                            "source_path": str(source_file),
                            "plugin": plugin_name
                        }

                        if component_type == "agents":
                            transformed = adapter.transform_agent(content, metadata)
                        elif component_type == "commands":
                            transformed = adapter.transform_command(content, metadata)
                        elif component_type == "skills":
                            transformed = adapter.transform_skill(content, metadata)
                        elif component_type == "hooks":
                            transformed = adapter.transform_hook(content, metadata)
                        else:
                            transformed = content
                    except Exception as e:
                        result.add_failure(source_file, target_file, f"Transform error: {e}")
                        continue

                    # Write transformed content
                    if options.dry_run:
                        if options.verbose:
                            result.warnings.append(
                                f"[DRY RUN] Would install {source_file} -> {target_file}"
                            )
                        result.add_success(source_file, target_file)
                    else:
                        try:
                            copy_with_transform(
                                source_file,
                                target_file,
                                transform_func=lambda _: transformed
                            )
                            result.add_success(source_file, target_file, backup_path)
                        except Exception as e:
                            result.add_failure(source_file, target_file, f"Write error: {e}")

    result.finalize()
    return result


def update(
    source_path: Path,
    targets: List[InstallTarget],
    options: Optional[InstallOptions] = None,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> InstallResult:
    """
    Update Ring components on target platforms.

    This is equivalent to install with force=True.

    Args:
        source_path: Path to the Ring repository/installation
        targets: List of installation targets
        options: Installation options
        progress_callback: Optional callback for progress updates

    Returns:
        InstallResult with details about what was updated
    """
    options = options or InstallOptions()
    options.force = True
    return install(source_path, targets, options, progress_callback)


def uninstall(
    targets: List[InstallTarget],
    options: Optional[InstallOptions] = None,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> InstallResult:
    """
    Remove Ring components from target platforms.

    Args:
        targets: List of platforms to uninstall from
        options: Uninstall options
        progress_callback: Optional callback for progress updates

    Returns:
        InstallResult with details about what was removed
    """
    options = options or InstallOptions()
    result = InstallResult(status=InstallStatus.SUCCESS, targets=[t.platform for t in targets])

    manifest = load_manifest()

    for target in targets:
        adapter = get_adapter(target.platform, manifest.get("platforms", {}).get(target.platform))
        install_path = target.path or adapter.get_install_path()
        component_mapping = adapter.get_component_mapping()

        # Remove each component directory
        for component_type, config in component_mapping.items():
            target_dir = install_path / config["target_dir"]

            if not target_dir.exists():
                continue

            if options.dry_run:
                if options.verbose:
                    result.warnings.append(f"[DRY RUN] Would remove {target_dir}")
                continue

            try:
                # Create backup if requested
                if options.backup:
                    from ring_installer.utils.fs import backup_existing
                    backup_existing(target_dir)

                # Remove directory
                shutil.rmtree(target_dir)
                result.components_installed += 1  # Using installed count for removed
            except Exception as e:
                result.errors.append(f"Failed to remove {target_dir}: {e}")
                result.components_failed += 1

    result.finalize()
    return result


def list_installed(platform: str) -> Dict[str, List[str]]:
    """
    List Ring components installed on a platform.

    Args:
        platform: Platform identifier

    Returns:
        Dictionary mapping component types to lists of installed component names
    """
    adapter = get_adapter(platform)
    install_path = adapter.get_install_path()
    component_mapping = adapter.get_component_mapping()

    installed: Dict[str, List[str]] = {}

    for component_type, config in component_mapping.items():
        target_dir = install_path / config["target_dir"]
        installed[component_type] = []

        if target_dir.exists():
            extension = config.get("extension", ".md")
            if extension:
                for file in target_dir.glob(f"*{extension}"):
                    installed[component_type].append(file.stem)
            else:
                # Multiple extensions (hooks)
                for file in target_dir.iterdir():
                    if file.is_file():
                        installed[component_type].append(file.name)

    return installed
