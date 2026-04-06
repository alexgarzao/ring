"""
Agent content transformer.

Transforms Ring agent markdown files to platform-specific formats.
"""

import re
from typing import Any, Dict, Optional

from ring_installer.transformers.base import (
    BaseTransformer,
    TransformContext,
    TransformResult,
)


class AgentTransformer(BaseTransformer):
    """
    Transformer for Ring agent files.

    Handles transformation of agent definitions including:
    - Claude: passthrough (native format)
    - Factory: agent -> droid, update references
    """

    def __init__(
        self,
        platform: str,
        terminology: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the agent transformer.

        Args:
            platform: Target platform identifier
            terminology: Platform-specific terminology mapping
        """
        super().__init__()
        self.platform = platform
        self.terminology = terminology or {}

    def transform(self, content: str, context: TransformContext) -> TransformResult:
        """
        Transform agent content for the target platform.

        Args:
            content: Original agent content
            context: Transformation context

        Returns:
            TransformResult with transformed content
        """
        errors = self.validate(content, context)
        if errors:
            return TransformResult(content=content, success=False, errors=errors)

        frontmatter, body = self.extract_frontmatter(content)

        # Transform based on platform
        if self.platform == "claude":
            return self._transform_claude(frontmatter, body, context)
        elif self.platform == "factory":
            return self._transform_factory(frontmatter, body, context)
        else:
            return TransformResult(content=content, success=True)

    def _transform_claude(
        self,
        frontmatter: Dict[str, Any],
        body: str,
        context: TransformContext
    ) -> TransformResult:
        """Transform agent for Claude Code (passthrough)."""
        if frontmatter:
            content = self.create_frontmatter(frontmatter) + "\n" + body
        else:
            content = body

        return TransformResult(content=content, success=True)

    def _transform_factory(
        self,
        frontmatter: Dict[str, Any],
        body: str,
        context: TransformContext
    ) -> TransformResult:
        """
        Transform agent to Factory AI droid format.

        Converts terminology and structure for Factory compatibility.
        """
        # Transform frontmatter
        transformed_fm = self._transform_factory_frontmatter(frontmatter)

        # Transform body
        transformed_body = self._transform_factory_body(body)

        if transformed_fm:
            content = self.create_frontmatter(transformed_fm) + "\n" + transformed_body
        else:
            content = transformed_body

        return TransformResult(content=content, success=True)

    def _transform_factory_frontmatter(
        self,
        frontmatter: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform agent frontmatter to droid frontmatter."""
        result = dict(frontmatter)

        # Rename agent-related fields
        if "agent" in result:
            result["droid"] = result.pop("agent")

        if "agents" in result:
            result["droids"] = result.pop("agents")

        if "subagent_type" in result:
            result["subdroid_type"] = result.pop("subagent_type")

        # Add Factory-specific type
        if "type" not in result:
            result["type"] = "droid"

        # Transform string values
        for key, value in list(result.items()):
            if isinstance(value, str):
                result[key] = self._replace_agent_references(value)
            elif isinstance(value, list):
                result[key] = [
                    self._replace_agent_references(v) if isinstance(v, str) else v
                    for v in value
                ]

        return result

    def _transform_factory_body(self, body: str) -> str:
        """Transform agent body to droid format."""
        result = self._replace_agent_references(body)

        # Replace section headers
        replacements = [
            ("# Agent ", "# Droid "),
            ("## Agent ", "## Droid "),
            ("### Agent ", "### Droid "),
        ]

        for old, new in replacements:
            result = result.replace(old, new)

        return result

    def _replace_agent_references(self, text: str) -> str:
        """Replace agent references with droid references."""
        replacements = [
            (r'\bagent\b', 'droid'),
            (r'\bAgent\b', 'Droid'),
            (r'\bAGENT\b', 'DROID'),
            (r'\bagents\b', 'droids'),
            (r'\bAgents\b', 'Droids'),
            (r'\bAGENTS\b', 'DROIDS'),
            (r'\bsubagent\b', 'subdroid'),
            (r'\bSubagent\b', 'Subdroid'),
            (r'\bsubagent_type\b', 'subdroid_type'),
            (r'"ring:([^"]*)-agent"', r'"ring:\1-droid"'),
            (r"'ring:([^']*)-agent'", r"'ring:\1-droid'"),
        ]

        result = text
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result)

        return result



class AgentTransformerFactory:
    """Factory for creating platform-specific agent transformers."""

    PLATFORM_TERMINOLOGY = {
        "claude": {"agent": "agent"},
        "factory": {"agent": "droid"},
    }

    @classmethod
    def create(cls, platform: str) -> AgentTransformer:
        """
        Create an agent transformer for the specified platform.

        Args:
            platform: Target platform identifier

        Returns:
            Configured AgentTransformer
        """
        terminology = cls.PLATFORM_TERMINOLOGY.get(platform, {})
        return AgentTransformer(platform=platform, terminology=terminology)
