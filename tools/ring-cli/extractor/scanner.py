#!/usr/bin/env python3
"""
Directory scanner for Ring plugin components.

Scans all plugin directories and extracts component metadata.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    from .models import Component, ComponentType
    from .parser import parse_skill_file, parse_agent_file, parse_command_file
except ImportError:
    from models import Component, ComponentType
    from parser import parse_skill_file, parse_agent_file, parse_command_file


def get_plugin_name(plugin_dir: Path, marketplace_data: Optional[Dict] = None) -> str:
    """Get plugin name from marketplace.json or directory name."""
    dir_name = plugin_dir.name

    if marketplace_data:
        for plugin in marketplace_data.get('plugins', []):
            source = plugin.get('source', '').replace('./', '')
            if source == dir_name:
                return plugin.get('name', f"ring-{dir_name}")

    # Default: prefix with "ring-" if not already
    if dir_name.startswith('ring-'):
        return dir_name
    return f"ring-{dir_name}"


def scan_skills(plugin_dir: Path, plugin_name: str) -> List[Component]:
    """Scan skills directory for SKILL.md files."""
    components = []
    skills_dir = plugin_dir / 'skills'

    if not skills_dir.exists():
        return components

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue

        # Skip shared-patterns directory
        if skill_dir.name == 'shared-patterns':
            continue

        skill_file = skill_dir / 'SKILL.md'
        if skill_file.exists():
            component = parse_skill_file(skill_file, plugin_name)
            if component:
                components.append(component)

    return components


def scan_agents(plugin_dir: Path, plugin_name: str) -> List[Component]:
    """Scan agents directory for *.md files."""
    components = []
    agents_dir = plugin_dir / 'agents'

    if not agents_dir.exists():
        return components

    for agent_file in sorted(agents_dir.glob('*.md')):
        # Skip non-agent files
        if agent_file.name.startswith('.'):
            continue

        component = parse_agent_file(agent_file, plugin_name)
        if component:
            components.append(component)

    return components


def scan_commands(plugin_dir: Path, plugin_name: str) -> List[Component]:
    """Scan commands directory for *.md files."""
    components = []
    commands_dir = plugin_dir / 'commands'

    if not commands_dir.exists():
        return components

    for command_file in sorted(commands_dir.glob('*.md')):
        # Skip non-command files
        if command_file.name.startswith('.'):
            continue

        component = parse_command_file(command_file, plugin_name)
        if component:
            components.append(component)

    return components


def scan_plugin(plugin_dir: Path, plugin_name: str) -> List[Component]:
    """Scan a single plugin directory for all components."""
    components = []

    print(f"Scanning plugin: {plugin_name} ({plugin_dir})", file=sys.stderr)

    # Scan each component type
    skills = scan_skills(plugin_dir, plugin_name)
    agents = scan_agents(plugin_dir, plugin_name)
    commands = scan_commands(plugin_dir, plugin_name)

    components.extend(skills)
    components.extend(agents)
    components.extend(commands)

    print(f"  Found: {len(skills)} skills, {len(agents)} agents, {len(commands)} commands",
          file=sys.stderr)

    return components


def scan_all_plugins(repo_root: Path) -> List[Component]:
    """Scan all plugins in the repository.

    Plugin directories are discovered from marketplace.json (authoritative source).
    Falls back to hardcoded list only if marketplace.json is unavailable.
    """
    components = []

    # Load marketplace.json for plugin names and directories
    marketplace_path = repo_root / '.claude-plugin' / 'marketplace.json'
    marketplace_data = None

    if marketplace_path.exists():
        try:
            marketplace_data = json.loads(marketplace_path.read_text())
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse marketplace.json: {e}", file=sys.stderr)

    # Get plugin directories from marketplace.json (authoritative source)
    plugin_dirs = []
    if marketplace_data:
        for plugin in marketplace_data.get('plugins', []):
            source = plugin.get('source', '').replace('./', '')
            if source and source not in plugin_dirs:
                plugin_dirs.append(source)
        if plugin_dirs:
            print(f"Discovered {len(plugin_dirs)} plugins from marketplace.json", file=sys.stderr)

    # Fallback to hardcoded list if marketplace.json unavailable or has no plugins
    if not plugin_dirs:
        print("Warning: Using fallback plugin list (marketplace.json not available)", file=sys.stderr)
        plugin_dirs = [
            'default',
            'dev-team',
            'pm-team',
            'finops-team',
            'tw-team',
            'finance-team',
            'ops-team',
            'pmm-team',
            'pmo-team',
        ]

    for dir_name in plugin_dirs:
        plugin_dir = repo_root / dir_name
        if plugin_dir.exists() and plugin_dir.is_dir():
            plugin_name = get_plugin_name(plugin_dir, marketplace_data)
            plugin_components = scan_plugin(plugin_dir, plugin_name)
            components.extend(plugin_components)

    return components


def main():
    """Main entry point for standalone testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Scan Ring plugins for components')
    parser.add_argument('--repo', type=Path, default=Path('.'),
                        help='Repository root directory')
    parser.add_argument('--output', type=Path, default=None,
                        help='Output JSON file (default: stdout)')
    args = parser.parse_args()

    repo_root = args.repo.resolve()
    components = scan_all_plugins(repo_root)

    # Output as JSON
    output = json.dumps([c.to_dict() for c in components], indent=2)

    if args.output:
        args.output.write_text(output)
        print(f"Wrote {len(components)} components to {args.output}", file=sys.stderr)
    else:
        print(output)

    print(f"\nTotal: {len(components)} components", file=sys.stderr)


if __name__ == '__main__':
    main()
