#!/usr/bin/env python3
"""
Validate YAML frontmatter in Ring skill, command, and agent files against
the canonical schema defined in docs/FRONTMATTER_SCHEMA.md.

Scans all 6 plugins (default/, dev-team/, pm-team/, pmo-team/, finops-team/,
tw-team/) and reports errors and warnings.

Usage:
    python default/hooks/validate-frontmatter.py
    python default/hooks/validate-frontmatter.py --strict
    python default/hooks/validate-frontmatter.py --plugin dev-team
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# ---------------------------------------------------------------------------
# Schema definitions (derived from docs/FRONTMATTER_SCHEMA.md)
# ---------------------------------------------------------------------------

# -- Skills --

SKILL_REQUIRED = {"name", "description"}

SKILL_RECOMMENDED = {"trigger", "skip_when"}

SKILL_VALID = (
    SKILL_REQUIRED
    | SKILL_RECOMMENDED
    | {
        "NOT_skip_when",
        "prerequisites",
        "verification",
        "when_to_use",        # deprecated but still valid
        "prerequisite",       # deprecated but still valid
        "sequence",
        "related",
        "compliance_rules",
        "composition",
        "input_schema",
        "output_schema",
    }
)

SKILL_DEPRECATED = {
    "when_to_use": "trigger",
    "prerequisite": "prerequisites",
}

SKILL_INVALID = {
    "version", "allowed-tools", "examples", "category", "tier", "slug",
    "user_invocable", "title", "type", "role", "dependencies", "author",
    "license", "compatibility", "metadata", "agent_selection", "tdd_policy",
    "research_modes", "trigger_when",
}

# -- Commands --

COMMAND_REQUIRED = {"name", "description"}

COMMAND_RECOMMENDED = {"argument-hint"}

COMMAND_VALID = COMMAND_REQUIRED | COMMAND_RECOMMENDED

COMMAND_DEPRECATED: Dict[str, str] = {
    "arguments": "argument-hint",
    "args": "argument-hint",
}

COMMAND_INVALID = {"arguments", "args", "version"}

# -- Agents --

AGENT_REQUIRED = {"name", "description", "type", "output_schema"}

AGENT_TYPE_ENUM = {
    "reviewer",
    "specialist",
    "orchestrator",
    "planning",
    "exploration",
    "analyst",
    "calculator",
}

AGENT_VALID = AGENT_REQUIRED | {"input_schema"}

AGENT_INVALID = {"version", "color", "project_rules_integration", "allowed-tools", "tools"}

# -- Plugin directories --

ALL_PLUGINS = ["default", "dev-team", "pm-team", "pmo-team", "finops-team", "tw-team"]

# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


def parse_frontmatter_yaml(content: str) -> Optional[Dict[str, Any]]:
    """Parse YAML frontmatter using the pyyaml library."""
    if not YAML_AVAILABLE:
        return None

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None

    try:
        data = yaml.safe_load(match.group(1))
        return data if isinstance(data, dict) else None
    except yaml.YAMLError:
        return None


def parse_frontmatter_fallback(content: str) -> Optional[Dict[str, Any]]:
    """Regex-based fallback parser (mirrors generate-skills-ref.py approach).

    Extracts top-level keys and their scalar values.  Nested objects are
    represented as non-empty dicts so presence checks work, but deep
    validation is not attempted in fallback mode.
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None

    text = match.group(1)
    result: Dict[str, Any] = {}

    # Identify all top-level keys (lines starting at column 0 with "key:")
    top_keys = re.findall(r"^([A-Za-z_][A-Za-z0-9_-]*):", text, re.MULTILINE)
    for key in top_keys:
        # Grab everything from "key:" to the next top-level key or end
        pat = rf"^{re.escape(key)}:\s*(.*?)(?=^[A-Za-z_][A-Za-z0-9_-]*:|\Z)"
        m = re.search(pat, text, re.MULTILINE | re.DOTALL)
        if m:
            raw = m.group(1).strip()
            if raw.startswith("|") or raw.startswith(">"):
                # Block scalar -- grab indented lines that follow
                block_lines = []
                for line in raw.split("\n")[1:]:
                    if line and not line[0].isspace():
                        break
                    block_lines.append(line.strip())
                result[key] = "\n".join(block_lines).strip() or raw
            elif raw == "" or raw.startswith("\n"):
                # Nested mapping or list -- mark as present with a placeholder
                result[key] = {"_nested": True}
            else:
                # Simple scalar (possibly quoted)
                first_line = raw.split("\n")[0].strip()
                if first_line.startswith('"') and first_line.endswith('"'):
                    first_line = first_line[1:-1]
                elif first_line.startswith("'") and first_line.endswith("'"):
                    first_line = first_line[1:-1]
                result[key] = first_line

    return result if result else None


def parse_frontmatter(content: str) -> Optional[Dict[str, Any]]:
    """Try YAML first, then regex fallback."""
    data = parse_frontmatter_yaml(content)
    if data is not None:
        return data
    return parse_frontmatter_fallback(content)


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

class Issue:
    """A single validation issue."""

    def __init__(self, level: str, path: str, message: str):
        self.level = level   # "ERROR" or "WARNING"
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"[{self.level}] {self.path}: {self.message}"


def validate_skill(file_path: str, fm: Dict[str, Any]) -> List[Issue]:
    """Validate a skill frontmatter dict."""
    issues: List[Issue] = []

    # Required fields
    for field in sorted(SKILL_REQUIRED):
        if field not in fm:
            issues.append(Issue("ERROR", file_path, f"missing required field '{field}'"))

    # Recommended fields
    for field in sorted(SKILL_RECOMMENDED):
        if field not in fm:
            issues.append(Issue("WARNING", file_path, f"missing recommended field '{field}'"))

    # Deprecated fields
    for old_field, new_field in sorted(SKILL_DEPRECATED.items()):
        if old_field in fm:
            issues.append(
                Issue(
                    "WARNING",
                    file_path,
                    f"deprecated field '{old_field}' -- use '{new_field}' instead",
                )
            )

    # Unknown / explicitly invalid fields
    for field in sorted(fm.keys()):
        if field in SKILL_INVALID:
            issues.append(
                Issue("WARNING", file_path, f"invalid field '{field}' (not part of the schema)")
            )
        elif field not in SKILL_VALID:
            issues.append(
                Issue("WARNING", file_path, f"unknown field '{field}'")
            )

    return issues


def validate_command(file_path: str, fm: Dict[str, Any]) -> List[Issue]:
    """Validate a command frontmatter dict."""
    issues: List[Issue] = []

    # Required fields
    for field in sorted(COMMAND_REQUIRED):
        if field not in fm:
            issues.append(Issue("ERROR", file_path, f"missing required field '{field}'"))

    # Recommended fields
    for field in sorted(COMMAND_RECOMMENDED):
        if field not in fm:
            issues.append(Issue("WARNING", file_path, f"missing recommended field '{field}'"))

    # Deprecated / invalid fields
    for old_field, new_field in sorted(COMMAND_DEPRECATED.items()):
        if old_field in fm:
            issues.append(
                Issue(
                    "WARNING",
                    file_path,
                    f"invalid field '{old_field}' -- use '{new_field}' instead",
                )
            )

    # Unknown fields
    for field in sorted(fm.keys()):
        if field in COMMAND_INVALID:
            # Already covered by deprecated check above for args/arguments
            if field not in COMMAND_DEPRECATED:
                issues.append(
                    Issue("WARNING", file_path, f"invalid field '{field}' (not part of the schema)")
                )
        elif field not in COMMAND_VALID:
            issues.append(
                Issue("WARNING", file_path, f"unknown field '{field}'")
            )

    return issues


def validate_agent(file_path: str, fm: Dict[str, Any]) -> List[Issue]:
    """Validate an agent frontmatter dict."""
    issues: List[Issue] = []

    # Required fields
    for field in sorted(AGENT_REQUIRED):
        if field not in fm:
            issues.append(Issue("ERROR", file_path, f"missing required field '{field}'"))

    # Type enum check
    agent_type = fm.get("type")
    if agent_type is not None and agent_type not in AGENT_TYPE_ENUM:
        issues.append(
            Issue(
                "WARNING",
                file_path,
                f"type '{agent_type}' not in allowed values: {sorted(AGENT_TYPE_ENUM)}",
            )
        )

    # Explicitly invalid fields
    for field in sorted(fm.keys()):
        if field in AGENT_INVALID:
            issues.append(
                Issue("WARNING", file_path, f"invalid field '{field}' (not part of the schema)")
            )
        elif field not in AGENT_VALID:
            issues.append(
                Issue("WARNING", file_path, f"unknown field '{field}'")
            )

    return issues


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def discover_files(repo_root: Path, plugins: List[str]) -> Tuple[List[Path], List[Path], List[Path]]:
    """Discover skill, command, and agent files across the requested plugins.

    Returns (skills, commands, agents) as three sorted lists of Paths.
    Skips shared-patterns/ directories.
    """
    skills: List[Path] = []
    commands: List[Path] = []
    agents: List[Path] = []

    for plugin in plugins:
        plugin_dir = repo_root / plugin

        # Skills: {plugin}/skills/*/SKILL.md  (skip shared-patterns)
        skills_dir = plugin_dir / "skills"
        if skills_dir.is_dir():
            for child in sorted(skills_dir.iterdir()):
                if not child.is_dir():
                    continue
                if child.name == "shared-patterns":
                    continue
                skill_file = child / "SKILL.md"
                if skill_file.is_file():
                    skills.append(skill_file)

        # Commands: {plugin}/commands/*.md
        commands_dir = plugin_dir / "commands"
        if commands_dir.is_dir():
            for child in sorted(commands_dir.iterdir()):
                if child.is_file() and child.suffix == ".md":
                    commands.append(child)

        # Agents: {plugin}/agents/*.md
        agents_dir = plugin_dir / "agents"
        if agents_dir.is_dir():
            for child in sorted(agents_dir.iterdir()):
                if child.is_file() and child.suffix == ".md":
                    agents.append(child)

    return skills, commands, agents


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def relative_path(path: Path, repo_root: Path) -> str:
    """Return a display-friendly path relative to the repo root."""
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate YAML frontmatter in Ring skill, command, and agent files.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (exit code 1 if any warnings).",
    )
    parser.add_argument(
        "--plugin",
        type=str,
        default=None,
        help="Check only one plugin (e.g., --plugin dev-team).",
    )
    args = parser.parse_args()

    # Resolve repo root (this script lives in default/hooks/)
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent

    # Determine which plugins to scan
    if args.plugin:
        if args.plugin not in ALL_PLUGINS:
            print(
                f"Error: unknown plugin '{args.plugin}'. "
                f"Valid plugins: {', '.join(ALL_PLUGINS)}",
                file=sys.stderr,
            )
            return 1
        plugins = [args.plugin]
    else:
        plugins = ALL_PLUGINS

    # Discover files
    skill_files, command_files, agent_files = discover_files(repo_root, plugins)

    all_issues: List[Issue] = []
    files_checked = 0

    # Validate skills
    for path in skill_files:
        rel = relative_path(path, repo_root)
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            all_issues.append(Issue("ERROR", rel, f"cannot read file: {exc}"))
            files_checked += 1
            continue

        fm = parse_frontmatter(content)
        if fm is None:
            all_issues.append(Issue("ERROR", rel, "no YAML frontmatter found"))
            files_checked += 1
            continue

        all_issues.extend(validate_skill(rel, fm))
        files_checked += 1

    # Validate commands
    for path in command_files:
        rel = relative_path(path, repo_root)
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            all_issues.append(Issue("ERROR", rel, f"cannot read file: {exc}"))
            files_checked += 1
            continue

        fm = parse_frontmatter(content)
        if fm is None:
            all_issues.append(Issue("ERROR", rel, "no YAML frontmatter found"))
            files_checked += 1
            continue

        all_issues.extend(validate_command(rel, fm))
        files_checked += 1

    # Validate agents
    for path in agent_files:
        rel = relative_path(path, repo_root)
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            all_issues.append(Issue("ERROR", rel, f"cannot read file: {exc}"))
            files_checked += 1
            continue

        fm = parse_frontmatter(content)
        if fm is None:
            all_issues.append(Issue("ERROR", rel, "no YAML frontmatter found"))
            files_checked += 1
            continue

        all_issues.extend(validate_agent(rel, fm))
        files_checked += 1

    # Print issues
    for issue in all_issues:
        print(issue)

    # Summary
    error_count = sum(1 for i in all_issues if i.level == "ERROR")
    warning_count = sum(1 for i in all_issues if i.level == "WARNING")
    print(f"\n{error_count} errors, {warning_count} warnings across {files_checked} files")

    # Exit code
    if error_count > 0:
        return 1
    if args.strict and warning_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
