"""
Pi adapter - transforms Ring components for pi-coding-agent.

Pi (https://github.com/badlogic/pi-mono) has a different resource model:

  Ring skills   → Pi skills   (~/.pi/agent/skills/<name>/SKILL.md)
  Ring commands  → Pi prompts  (~/.pi/agent/prompts/<name>.md)
  Ring agents    → Pi agents   (~/.pi/agent/agents/<name>.md)  ← persona files for $ activation
  Ring hooks     → unsupported (Pi uses extension events)

Pi skill frontmatter:
  ---
  name: <lowercase-alphanumeric-hyphens>
  description: <what the skill does and when to use it>
  ---

Pi prompt template frontmatter:
  ---
  description: <what the command does>
  ---

Pi agent persona frontmatter:
  ---
  name: Human-Readable Name
  description: One-line description of what this agent persona does
  model: <optional preferred model id>
  thinking: <optional preferred thinking level>
  ---

Key constraints:
  - Skill names: 1-64 chars, lowercase a-z 0-9 hyphens, no leading/trailing/consecutive hyphens
  - Skill names must match parent directory name
  - Prompt template names derived from filename (no frontmatter `name` field)
  - Skills are loaded from SKILL.md inside a named directory
  - Prompts are flat .md files (non-recursive discovery)
  - Agent persona names derived from filename (flat .md files in agents/)
  - Agents are flat .md files (non-recursive discovery in agents/)
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ring_installer.adapters.base import PlatformAdapter


def _sanitize_pi_name(name: str) -> str:
    """
    Sanitize a Ring component name into a valid Pi skill/prompt name.

    Pi skill names: lowercase a-z, 0-9, hyphens only. No leading/trailing
    or consecutive hyphens. Max 64 chars.

    Examples:
        "ring:code-reviewer"       -> "code-reviewer"
        "ring:backend-engineer-golang" -> "backend-engineer-golang"
        "Ring:Dev--Cycle"          -> "dev-cycle"
    """
    # Strip ring: prefix
    cleaned = re.sub(r"^ring:", "", name, flags=re.IGNORECASE)
    # Lowercase
    cleaned = cleaned.lower()
    # Replace non-alphanumeric (except hyphens) with hyphens
    cleaned = re.sub(r"[^a-z0-9-]", "-", cleaned)
    # Collapse consecutive hyphens
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    # Strip leading/trailing hyphens
    cleaned = cleaned.strip("-")
    # Truncate to 64 chars
    cleaned = cleaned[:64]
    # Final strip in case truncation left trailing hyphen
    cleaned = cleaned.strip("-")
    return cleaned or "unnamed"


def _build_agent_skill_body(frontmatter: Dict[str, Any], body: str) -> str:
    """
    Convert a Ring agent body into a Pi skill body.

    Prepends structured context from agent frontmatter (type, output_schema)
    as prose instructions, so the LLM knows how to behave as this agent.
    """
    sections: List[str] = []

    agent_type = frontmatter.get("type", "")
    if agent_type:
        sections.append(f"**Agent type:** {agent_type}")

    # Convert output_schema to prose instructions
    output_schema = frontmatter.get("output_schema")
    if isinstance(output_schema, dict):
        fmt = output_schema.get("format", "markdown")
        required_sections = output_schema.get("required_sections", [])
        verdict_values = output_schema.get("verdict_values", [])

        schema_lines = [f"**Output format:** {fmt}"]
        if required_sections:
            schema_lines.append("")
            schema_lines.append("**Required output sections:**")
            for sec in required_sections:
                if isinstance(sec, dict):
                    name = sec.get("name", "")
                    pattern = sec.get("pattern", "")
                    required = sec.get("required", False)
                    desc = sec.get("description", "")
                    req_mark = " (required)" if required else " (optional)"
                    line = f"- **{name}**{req_mark}"
                    if pattern:
                        line += f" — pattern: `{pattern}`"
                    if desc:
                        line += f" — {desc}"
                    schema_lines.append(line)

        if verdict_values:
            schema_lines.append(f"\n**Valid verdict values:** {', '.join(str(v) for v in verdict_values)}")

        sections.append("\n".join(schema_lines))

    # Convert input_schema to prose
    input_schema = frontmatter.get("input_schema")
    if isinstance(input_schema, dict):
        input_lines = ["**Expected input context:**"]
        for category in ("required", "optional"):
            fields = input_schema.get(category, [])
            if fields:
                input_lines.append(f"\n*{category.title()} fields:*")
                for field in fields:
                    if isinstance(field, dict):
                        fname = field.get("name", "")
                        ftype = field.get("type", "")
                        fdesc = field.get("description", "")
                        input_lines.append(f"- `{fname}` ({ftype}): {fdesc}")
        sections.append("\n".join(input_lines))

    if sections:
        preamble = "## Agent Metadata\n\n" + "\n\n".join(sections) + "\n\n---\n\n"
        return preamble + body
    return body


class PiAdapter(PlatformAdapter):
    """
    Platform adapter for pi-coding-agent.

    Transforms Ring components into Pi's resource model:
    - Skills → Pi skills (SKILL.md in named directories)
    - Commands → Pi prompt templates (flat .md files)
    - Agents → Pi agent personas (flat .md files for $ activation)
    - Hooks → Unsupported (skipped)
    """

    platform_id = "pi"
    platform_name = "Pi"

    def transform_skill(self, skill_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Transform a Ring skill into a Pi skill.

        Keeps name and description, strips Ring-specific frontmatter fields.
        Body content is preserved as-is.
        """
        frontmatter, body = self.extract_frontmatter(skill_content)

        raw_name = self._string_field(frontmatter, "name")
        pi_name = _sanitize_pi_name(raw_name) if raw_name else self._name_from_metadata(metadata)

        description = self._string_field(frontmatter, "description")
        if not description:
            # Fallback: use trigger or first line of body
            description = (
                self._string_field(frontmatter, "trigger")
                or self._string_field(frontmatter, "when_to_use")
                or self._first_meaningful_line(body)
                or "Ring skill"
            )

        pi_frontmatter = {"name": pi_name, "description": description}

        body = self._rewrite_ring_references(body, metadata)

        return self.create_frontmatter(pi_frontmatter) + "\n" + body.strip() + "\n"

    def transform_agent(self, agent_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Transform a Ring agent into a Pi agent persona file.

        Pi agents are flat .md files in ~/.pi/agent/agents/ with simplified
        frontmatter (name, description, optional model/thinking). The body is
        the persona prompt injected into the system prompt when activated via $.

        Ring-specific frontmatter (output_schema, input_schema, type) is stripped.
        The body is preserved as-is (it's the persona prompt content).
        """
        frontmatter, body = self.extract_frontmatter(agent_content)

        # Build human-readable name from ring:name
        raw_name = self._string_field(frontmatter, "name")
        display_name = (
            raw_name.replace("ring:", "").replace("-", " ").title()
            if raw_name
            else ""
        )

        description = self._string_field(frontmatter, "description")
        if not description:
            agent_type = frontmatter.get("type", "agent")
            description = f"Ring {agent_type} agent"

        # Build simplified Pi agent frontmatter
        pi_frontmatter: Dict[str, str] = {}
        if display_name:
            pi_frontmatter["name"] = display_name
        if description:
            pi_frontmatter["description"] = description

        # Rewrite ring: references in body
        body = self._rewrite_ring_references(body, metadata)

        return self.create_frontmatter(pi_frontmatter) + "\n" + body.strip() + "\n"

    def transform_command(self, command_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Transform a Ring command into a Pi prompt template.

        Pi prompt templates use a simpler frontmatter (just `description`).
        The command body becomes the template content.
        Arguments are preserved using Pi's $1, $@, ${@:N} syntax if applicable.
        """
        frontmatter, body = self.extract_frontmatter(command_content)

        description = self._string_field(frontmatter, "description")
        argument_hint = self._string_field(frontmatter, "argument-hint")

        if not description:
            description = self._first_meaningful_line(body) or "Ring command"

        # Include argument hint in description for discoverability
        if argument_hint:
            description = f"{description} — args: {argument_hint}"

        pi_frontmatter = {"description": description}

        # Add argument placeholder if the command expects arguments
        if argument_hint:
            body = body.strip()
            # If body doesn't already reference $1/$@, add a note
            if "$1" not in body and "$@" not in body and "$ARGUMENTS" not in body:
                body += "\n\n<!-- Arguments (if provided): $@ -->\n"

        body = self._rewrite_ring_references(body, metadata)

        return self.create_frontmatter(pi_frontmatter) + "\n" + body.strip() + "\n"

    def transform_hook(self, hook_content: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Hooks are not supported by Pi.

        Pi uses extension events (TypeScript) instead of shell-based hooks.
        Returns None to signal the installer to skip this component.
        """
        return None

    def get_install_path(self) -> Path:
        """
        Get the installation path for Pi.

        Default: ~/.pi/agent/
        Override: PI_CODING_AGENT_DIR environment variable
        """
        if self._install_path is None:
            env_override = os.environ.get("PI_CODING_AGENT_DIR")
            if env_override:
                candidate = Path(env_override).expanduser().resolve()
                home = Path.home().resolve()
                try:
                    candidate.relative_to(home)
                    self._install_path = candidate
                except ValueError:
                    import logging
                    logging.getLogger(__name__).warning(
                        "PI_CODING_AGENT_DIR=%s ignored: path must be under home",
                        env_override,
                    )
                    self._install_path = Path(
                        self.config.get("install_path", "~/.pi/agent")
                    ).expanduser()
            else:
                self._install_path = Path(
                    self.config.get("install_path", "~/.pi/agent")
                ).expanduser()
        return self._install_path

    def get_component_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Map Ring component types to Pi directories.

        Ring skills  → ~/.pi/agent/skills/<name>/SKILL.md
        Ring commands → ~/.pi/agent/prompts/<name>.md
        Ring agents  → ~/.pi/agent/agents/<name>.md  (persona files for $ activation)

        Note: Pi's skill discovery expects SKILL.md inside a named directory.
        Agents are flat .md files (like prompts), not SKILL.md directories.
        """
        return {
            "skills": {"target_dir": "skills", "extension": ".md"},
            "commands": {"target_dir": "prompts", "extension": ".md"},
            "agents": {"target_dir": "agents", "extension": ".md"},
        }

    def get_terminology(self) -> Dict[str, str]:
        """
        Pi terminology mapping.

        Pi uses 'skill', 'prompt template', and 'agent persona'.
        """
        return {
            "agent": "agent",
            "skill": "skill",
            "command": "prompt",
            "hook": "hook",
        }

    def is_native_format(self) -> bool:
        """Pi requires transformation from Ring's native format."""
        return False

    def supports_component(self, component_type: str) -> bool:
        """Pi supports skills, commands, and agents. Not hooks."""
        return component_type in ("skills", "commands", "agents")

    def requires_flat_components(self, component_type: str) -> bool:
        """
        Commands (→ prompts) and agents require flat structure.

        Pi discovers prompt templates non-recursively from the prompts/ directory.
        Pi discovers agent personas non-recursively from the agents/ directory.
        Skills use named subdirectories (handled by core.py SKILL.md logic).
        """
        return component_type in ("commands", "agents")

    def get_flat_filename(self, source_filename: str, component_type: str, plugin_name: str) -> str:
        """
        Get a flattened filename for multi-plugin installs.

        For commands → prompts, prefix with plugin name to avoid collisions.
        For agents → agents/, use short names (no plugin prefix needed since
        agents are selected interactively via $, not by slash command).
        For skills, use the sanitized name (handled by SKILL.md logic in core.py).
        """
        source_path = Path(source_filename)
        stem = source_path.stem

        if component_type == "commands":
            # Prompt template name = filename without .md (prefixed to avoid collisions)
            sanitized = _sanitize_pi_name(f"ring-{plugin_name}-{stem}")
            return f"{sanitized}.md"

        if component_type == "agents":
            # Agent persona files use short names for easy $ activation
            # e.g., $backend-engineer-golang not $ring-dev-team-backend-engineer-golang
            sanitized = _sanitize_pi_name(stem)
            return f"{sanitized}.md"

        # For skills, use prefixed ring name
        sanitized = _sanitize_pi_name(f"ring-{plugin_name}-{stem}")
        return f"{sanitized}.md"

    # ── Private helpers ──────────────────────────────────────────

    @staticmethod
    def _string_field(frontmatter: Dict[str, Any], key: str) -> str:
        """Extract a string field from frontmatter, handling block scalars."""
        value = frontmatter.get(key)
        if value is None:
            return ""
        if isinstance(value, str):
            # Collapse multi-line block scalar to single line
            return " ".join(value.split())
        return str(value).strip()

    @staticmethod
    def _name_from_metadata(metadata: Optional[Dict[str, Any]]) -> str:
        """Derive a Pi-safe name from installer metadata."""
        if not metadata:
            return "unnamed"
        source_file = metadata.get("source_file", "")
        if source_file:
            stem = Path(source_file).stem
            if stem.upper() == "SKILL":
                stem = Path(source_file).parent.name
            return _sanitize_pi_name(stem)
        return "unnamed"

    @staticmethod
    def _first_meaningful_line(body: str) -> str:
        """Get the first non-empty, non-heading line from markdown body."""
        for line in body.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return stripped[:200]
        return ""

    def _rewrite_ring_references(self, body: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Rewrite ring: prefixed references in the body.

        Converts references like `ring:code-reviewer` to just `code-reviewer`
        for Pi's namespace. Also rewrites skill/command/agent path references
        to Pi's directory structure.
        """
        # Strip ring: prefix from inline references
        result = re.sub(r"\bring:([a-zA-Z0-9_-]+)\b", r"\1", body)

        # Rewrite relative paths to ring components if we know the source context
        # e.g., ../skills/shared-patterns/foo.md stays as-is (relative paths work in Pi too)

        return result
