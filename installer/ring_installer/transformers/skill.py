"""
Skill content transformer.

Transforms Ring SKILL.md files to platform-specific formats.
"""

import re
from typing import Any, Dict, List, Optional

from ring_installer.transformers.base import (
    BaseTransformer,
    TransformContext,
    TransformResult,
)


class SkillTransformer(BaseTransformer):
    """
    Transformer for Ring skill files.

    Handles transformation of YAML frontmatter and content body
    for different platform conventions.
    """

    def __init__(
        self,
        platform: str,
        terminology: Optional[Dict[str, str]] = None,
        preserve_frontmatter: bool = True
    ):
        """
        Initialize the skill transformer.

        Args:
            platform: Target platform identifier
            terminology: Platform-specific terminology mapping
            preserve_frontmatter: Whether to keep frontmatter in output
        """
        super().__init__()
        self.platform = platform
        self.terminology = terminology or {}
        self.preserve_frontmatter = preserve_frontmatter

    def transform(self, content: str, context: TransformContext) -> TransformResult:
        """
        Transform skill content for the target platform.

        Args:
            content: Original skill content
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
            # Default passthrough
            return TransformResult(content=content, success=True)

    def _transform_claude(
        self,
        frontmatter: Dict[str, Any],
        body: str,
        context: TransformContext
    ) -> TransformResult:
        """Transform skill for Claude Code (passthrough)."""
        # Claude uses Ring format natively
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
        """Transform skill for Factory AI."""
        # Update terminology in frontmatter
        transformed_fm = self._transform_frontmatter_terminology(frontmatter)

        # Update terminology in body
        transformed_body = self._transform_body_terminology(body)

        if transformed_fm and self.preserve_frontmatter:
            content = self.create_frontmatter(transformed_fm) + "\n" + transformed_body
        else:
            content = transformed_body

        return TransformResult(content=content, success=True)

    def _transform_frontmatter_terminology(
        self,
        frontmatter: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply terminology changes to frontmatter."""
        result = dict(frontmatter)

        for old_term, new_term in self.terminology.items():
            if old_term == new_term:
                continue

            # Rename keys
            if old_term in result:
                result[new_term] = result.pop(old_term)

            # Rename plurals
            old_plural = f"{old_term}s"
            new_plural = f"{new_term}s"
            if old_plural in result:
                result[new_plural] = result.pop(old_plural)

            # Transform string values
            for key, value in list(result.items()):
                if isinstance(value, str):
                    result[key] = self._replace_term(value, old_term, new_term)
                elif isinstance(value, list):
                    result[key] = [
                        self._replace_term(v, old_term, new_term)
                        if isinstance(v, str) else v
                        for v in value
                    ]

        return result

    def _transform_body_terminology(self, body: str) -> str:
        """Apply terminology changes to body content."""
        result = body

        for old_term, new_term in self.terminology.items():
            if old_term != new_term:
                result = self._replace_term(result, old_term, new_term)

        return result

    def _replace_term(self, text: str, old_term: str, new_term: str) -> str:
        """Replace a term with various case variants."""
        result = text
        # Lowercase
        result = re.sub(rf'\b{old_term}\b', new_term, result)
        # Title case
        result = re.sub(rf'\b{old_term.title()}\b', new_term.title(), result)
        # Uppercase
        result = re.sub(rf'\b{old_term.upper()}\b', new_term.upper(), result)
        return result

    def _add_list_section(self, parts: List[str], text: str) -> None:
        """Add list items from YAML list or multi-line string."""
        self.add_list_items(parts, text)


class SkillTransformerFactory:
    """Factory for creating platform-specific skill transformers."""

    PLATFORM_TERMINOLOGY = {
        "claude": {
            "agent": "agent",
            "skill": "skill",
            "command": "command",
        },
        "factory": {
            "agent": "droid",
            "skill": "skill",
            "command": "command",
        },
    }

    @classmethod
    def create(cls, platform: str) -> SkillTransformer:
        """
        Create a skill transformer for the specified platform.

        Args:
            platform: Target platform identifier

        Returns:
            Configured SkillTransformer
        """
        terminology = cls.PLATFORM_TERMINOLOGY.get(platform, {})
        preserve_frontmatter = platform in ("claude", "factory")

        return SkillTransformer(
            platform=platform,
            terminology=terminology,
            preserve_frontmatter=preserve_frontmatter
        )
