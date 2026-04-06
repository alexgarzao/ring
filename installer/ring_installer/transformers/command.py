"""
Command content transformer.

Transforms Ring slash command files to platform-specific formats.
"""

import re
from typing import Any, Dict, Optional

from ring_installer.transformers.base import (
    BaseTransformer,
    TransformContext,
    TransformResult,
)


class CommandTransformer(BaseTransformer):
    """
    Transformer for Ring command files.

    Handles transformation of slash command definitions:
    - Claude: passthrough (native format)
    - Factory: minimal terminology changes
    """

    def __init__(
        self,
        platform: str,
        terminology: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the command transformer.

        Args:
            platform: Target platform identifier
            terminology: Platform-specific terminology mapping
        """
        super().__init__()
        self.platform = platform
        self.terminology = terminology or {}

    def transform(self, content: str, context: TransformContext) -> TransformResult:
        """
        Transform command content for the target platform.

        Args:
            content: Original command content
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
        """Transform command for Claude Code (passthrough)."""
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
        Transform command for Factory AI.

        Factory supports commands but with droid terminology.
        """
        transformed_fm = self._transform_factory_frontmatter(frontmatter)
        transformed_body = self._replace_agent_references(body)

        if transformed_fm:
            content = self.create_frontmatter(transformed_fm) + "\n" + transformed_body
        else:
            content = transformed_body

        return TransformResult(content=content, success=True)

    def _transform_factory_frontmatter(
        self,
        frontmatter: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform command frontmatter for Factory."""
        result = dict(frontmatter)

        # Transform string values containing agent references
        for key, value in list(result.items()):
            if isinstance(value, str):
                result[key] = self._replace_agent_references(value)
            elif isinstance(value, list):
                result[key] = [
                    self._replace_agent_references(v) if isinstance(v, str) else v
                    for v in value
                ]

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
            (r'"ring:([^"]*)-agent"', r'"ring:\1-droid"'),
        ]

        result = text
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result)

        return result



class CommandTransformerFactory:
    """Factory for creating platform-specific command transformers."""

    PLATFORM_TERMINOLOGY = {
        "claude": {"command": "command"},
        "factory": {"command": "command"},
    }

    @classmethod
    def create(cls, platform: str) -> CommandTransformer:
        """
        Create a command transformer for the specified platform.

        Args:
            platform: Target platform identifier

        Returns:
            Configured CommandTransformer
        """
        terminology = cls.PLATFORM_TERMINOLOGY.get(platform, {})
        return CommandTransformer(platform=platform, terminology=terminology)
