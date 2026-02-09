"""
Cursor adapter - converts Ring format to Cursor rules and workflows.

Cursor uses a different approach to AI assistance:
- skills -> rules (in .cursorrules or rules/ directory)
- agents/commands -> workflows
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ring_installer.adapters.base import PlatformAdapter


class CursorAdapter(PlatformAdapter):
    """
    Platform adapter for Cursor.

    Cursor uses "rules" for skills and "workflows" for agents/commands.
    Rules are typically stored in .cursorrules or a rules/ directory.
    """

    platform_id = "cursor"
    platform_name = "Cursor"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Cursor adapter.

        Args:
            config: Platform-specific configuration from platforms.json
        """
        super().__init__(config)

    def transform_skill(self, skill_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Transform a Ring skill to a Cursor rule.

        Converts the Ring skill format to Cursor's rule format, which is
        simpler markdown without YAML frontmatter.

        Args:
            skill_content: The original skill content
            metadata: Optional metadata about the skill

        Returns:
            Transformed rule content for Cursor
        """
        frontmatter, body = self.extract_frontmatter(skill_content)

        # Build Cursor rule structure
        rule_parts: List[str] = []

        # Extract name and description from frontmatter
        name = frontmatter.get("name", metadata.get("name", "Untitled Rule") if metadata else "Untitled Rule")
        description = frontmatter.get("description", "")

        # Create rule header
        rule_parts.append(f"# {self._to_title_case(name)}")
        rule_parts.append("")

        if description:
            # Clean up description (remove YAML multi-line markers)
            clean_desc = self._clean_yaml_string(description)
            rule_parts.append(clean_desc)
            rule_parts.append("")

        # Add trigger information as "When to apply" section
        trigger = frontmatter.get("trigger", "")
        if trigger:
            rule_parts.append("## When to Apply")
            rule_parts.append("")
            clean_trigger = self._clean_yaml_string(trigger)
            for line in clean_trigger.split("\n"):
                line = line.strip()
                if line.startswith("-"):
                    rule_parts.append(line)
                elif line:
                    rule_parts.append(f"- {line}")
            rule_parts.append("")

        # Add skip conditions if present
        skip_when = frontmatter.get("skip_when", "")
        if skip_when:
            rule_parts.append("## Skip When")
            rule_parts.append("")
            clean_skip = self._clean_yaml_string(skip_when)
            for line in clean_skip.split("\n"):
                line = line.strip()
                if line.startswith("-"):
                    rule_parts.append(line)
                elif line:
                    rule_parts.append(f"- {line}")
            rule_parts.append("")

        # Add the main content
        rule_parts.append("## Instructions")
        rule_parts.append("")
        rule_parts.append(self._transform_body_for_cursor(body))

        return "\n".join(rule_parts)

    def transform_agent(self, agent_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Transform a Ring agent to a Cursor workflow.

        Converts agent format to Cursor's workflow format for complex
        multi-step operations.

        Args:
            agent_content: The original agent content
            metadata: Optional metadata about the agent

        Returns:
            Transformed workflow content for Cursor
        """
        frontmatter, body = self.extract_frontmatter(agent_content)

        workflow_parts: List[str] = []

        # Extract agent information
        name = frontmatter.get("name", metadata.get("name", "Untitled Workflow") if metadata else "Untitled Workflow")
        description = frontmatter.get("description", "")

        # Create workflow header
        workflow_parts.append(f"# {self._to_title_case(name)} Workflow")
        workflow_parts.append("")

        if description:
            clean_desc = self._clean_yaml_string(description)
            workflow_parts.append(f"**Purpose:** {clean_desc}")
            workflow_parts.append("")

        # Add model information if present
        model = frontmatter.get("model", "")
        if model:
            workflow_parts.append(f"**Recommended Model:** {model}")
            workflow_parts.append("")

        # Extract output schema requirements
        output_schema = frontmatter.get("output_schema", {})
        if output_schema:
            workflow_parts.append("## Output Requirements")
            workflow_parts.append("")
            required_sections = output_schema.get("required_sections", [])
            for section in required_sections:
                section_name = section.get("name", "")
                if section_name:
                    workflow_parts.append(f"- {section_name}")
            workflow_parts.append("")

        # Transform and add the body
        workflow_parts.append("## Workflow Steps")
        workflow_parts.append("")
        workflow_parts.append(self._transform_body_for_cursor(body))

        return "\n".join(workflow_parts)

    def transform_command(self, command_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Transform a Ring command to a Cursor workflow.

        Commands become workflows in Cursor, similar to agents.

        Args:
            command_content: The original command content
            metadata: Optional metadata about the command

        Returns:
            Transformed workflow content for Cursor
        """
        frontmatter, body = self.extract_frontmatter(command_content)

        workflow_parts: List[str] = []

        # Extract command information
        name = frontmatter.get("name", metadata.get("name", "Untitled Command") if metadata else "Untitled Command")
        description = frontmatter.get("description", "")

        # Create workflow header
        workflow_parts.append(f"# {self._to_title_case(name)}")
        workflow_parts.append("")

        if description:
            clean_desc = self._clean_yaml_string(description)
            workflow_parts.append(clean_desc)
            workflow_parts.append("")

        # Add argument information if present
        args = frontmatter.get("args", [])
        if args:
            workflow_parts.append("## Parameters")
            workflow_parts.append("")
            for arg in args:
                arg_name = arg.get("name", "")
                arg_desc = arg.get("description", "")
                required = "required" if arg.get("required", False) else "optional"
                workflow_parts.append(f"- **{arg_name}** ({required}): {arg_desc}")
            workflow_parts.append("")

        # Add the body content
        workflow_parts.append("## Instructions")
        workflow_parts.append("")
        workflow_parts.append(self._transform_body_for_cursor(body))

        return "\n".join(workflow_parts)

    def get_install_path(self) -> Path:
        """
        Get the installation path for Cursor.

        Returns:
            Path to ~/.cursor directory
        """
        if self._install_path is None:
            base_path = self.config.get("install_path", "~/.cursor")
            self._install_path = Path(base_path).expanduser()
        return self._install_path

    def get_component_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Get the component mapping for Cursor.

        Returns:
            Mapping of Ring components to Cursor directories
        """
        return {
            "agents": {
                "target_dir": "workflows",
                "extension": ".md"
            },
            "commands": {
                "target_dir": "workflows",
                "extension": ".md"
            },
            "skills": {
                "target_dir": "rules",
                "extension": ".md"
            }
        }

    def get_terminology(self) -> Dict[str, str]:
        """
        Get Cursor terminology.

        Returns:
            Mapping of Ring terms to Cursor terms
        """
        return {
            "agent": "workflow",
            "skill": "rule",
            "command": "workflow",
            "hook": "automation"
        }

    def is_native_format(self) -> bool:
        """
        Check if this platform uses Ring's native format.

        Returns:
            False - Cursor requires transformation
        """
        return False

    def _to_title_case(self, text: str) -> str:
        """
        Convert text to title case, handling kebab-case and snake_case.

        Args:
            text: Input text

        Returns:
            Title-cased text
        """
        # Replace separators with spaces
        text = text.replace("-", " ").replace("_", " ")
        # Title case
        return text.title()

    def _clean_yaml_string(self, text: str) -> str:
        """
        Clean up YAML multi-line string markers.

        Args:
            text: YAML string value

        Returns:
            Cleaned string
        """
        # Remove | and > markers
        text = re.sub(r'^[|>]\s*', '', text)
        # Clean up extra whitespace
        return text.strip()

    def _transform_body_for_cursor(self, body: str) -> str:
        """
        Transform body content for Cursor compatibility.

        Args:
            body: Original body content

        Returns:
            Transformed body content
        """
        # Replace Ring-specific terminology
        replacements = [
            ("subagent", "sub-workflow"),
            ("Subagent", "Sub-workflow"),
            ("Task tool", "workflow step"),
            ("Skill tool", "rule reference"),
        ]

        result = body
        for old, new in replacements:
            result = result.replace(old, new)

        # Remove Ring-specific tool references that don't apply
        result = re.sub(r'`ring:[^`]+`', lambda m: self._transform_ring_reference(m.group(0)), result)

        return result

    def _transform_ring_reference(self, ref: str) -> str:
        """
        Transform a Ring tool reference to Cursor format.

        Args:
            ref: Ring reference like `ring:skill-name`

        Returns:
            Cursor-friendly reference
        """
        # Extract the name from the reference
        match = re.match(r'`ring:([^`]+)`', ref)
        if match:
            name = match.group(1)
            # Convert to readable format
            readable = self._to_title_case(name)
            return f"**{readable}**"
        return ref

    def generate_cursorrules_entry(self, rule_content: str, rule_name: str) -> str:
        """
        Generate an entry for the main .cursorrules file.

        Cursor allows rules to be defined in a single .cursorrules file
        or in separate files. This generates an entry for the combined format.

        Args:
            rule_content: The rule content
            rule_name: Name of the rule

        Returns:
            Formatted entry for .cursorrules
        """
        return f"""
---
## {self._to_title_case(rule_name)}

{rule_content}
"""

    def get_cursorrules_path(self, project_path: Optional[Path] = None) -> Path:
        """
        Get the path to the .cursorrules file.

        Args:
            project_path: Optional project directory path

        Returns:
            Path to .cursorrules file
        """
        if project_path:
            return project_path / ".cursorrules"
        return self.get_install_path() / ".cursorrules"
