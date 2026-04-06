"""
Content transformers for Ring multi-platform installer.

This module provides transformers for converting Ring components
(skills, agents, commands, hooks) to platform-specific formats.

Supported Platforms:
- Claude Code: Native Ring format (passthrough)
- Factory AI: Agents -> Droids transformation
"""

from pathlib import Path
from typing import Dict, Optional, Type

from ring_installer.transformers.agent import (
    AgentTransformer,
    AgentTransformerFactory,
)
from ring_installer.transformers.base import (
    BaseTransformer,
    FrontmatterTransformer,
    PassthroughTransformer,
    TerminologyTransformer,
    TransformContext,
    TransformerPipeline,
    TransformResult,
)
from ring_installer.transformers.command import (
    CommandTransformer,
    CommandTransformerFactory,
)
from ring_installer.transformers.hooks import (
    HookTransformer,
    HookTransformerFactory,
    generate_hooks_json,
    parse_hooks_json,
)
from ring_installer.transformers.skill import (
    SkillTransformer,
    SkillTransformerFactory,
)

# Component type to transformer factory mapping
TRANSFORMER_FACTORIES: Dict[str, Dict[str, Type]] = {
    "skill": {
        "claude": SkillTransformer,
        "factory": SkillTransformer,
    },
    "agent": {
        "claude": AgentTransformer,
        "factory": AgentTransformer,
    },
    "command": {
        "claude": CommandTransformer,
        "factory": CommandTransformer,
    },
    "hook": {
        "claude": HookTransformer,
        "factory": HookTransformer,
    },
}


def get_transformer(
    platform: str,
    component_type: str
) -> BaseTransformer:
    """
    Get a transformer for the specified platform and component type.

    Args:
        platform: Target platform (claude, factory)
        component_type: Component type (skill, agent, command, hook)

    Returns:
        Configured transformer instance

    Raises:
        ValueError: If platform or component type is not supported
    """
    platform = platform.lower()
    component_type = component_type.lower().rstrip("s")  # skills -> skill

    if component_type not in TRANSFORMER_FACTORIES:
        raise ValueError(
            f"Unsupported component type: '{component_type}'. "
            f"Supported: {', '.join(TRANSFORMER_FACTORIES.keys())}"
        )

    platform_transformers = TRANSFORMER_FACTORIES[component_type]

    if platform not in platform_transformers:
        raise ValueError(
            f"Unsupported platform: '{platform}'. "
            f"Supported: {', '.join(platform_transformers.keys())}"
        )

    # Use the appropriate factory
    if component_type == "skill":
        return SkillTransformerFactory.create(platform)
    elif component_type == "agent":
        return AgentTransformerFactory.create(platform)
    elif component_type == "command":
        return CommandTransformerFactory.create(platform)
    elif component_type == "hook":
        return HookTransformerFactory.create(platform)

    # Fallback
    transformer_class = platform_transformers[platform]
    return transformer_class(platform=platform)


def transform_content(
    content: str,
    platform: str,
    component_type: str,
    metadata: Optional[Dict] = None,
    source_path: str = ""
) -> TransformResult:
    """
    Transform content for a specific platform.

    This is a convenience function that creates the appropriate
    transformer and context, then performs the transformation.

    Args:
        content: Source content to transform
        platform: Target platform
        component_type: Type of component
        metadata: Optional metadata dict
        source_path: Optional source file path

    Returns:
        TransformResult with transformed content
    """
    transformer = get_transformer(platform, component_type)

    context = TransformContext(
        platform=platform,
        component_type=component_type,
        source_path=source_path,
        metadata=metadata or {}
    )

    return transformer.transform(content, context)


def create_pipeline(
    platform: str,
    component_types: Optional[list] = None
) -> TransformerPipeline:
    """
    Create a transformation pipeline for a platform.

    Args:
        platform: Target platform
        component_types: Optional list of component types to include

    Returns:
        Configured TransformerPipeline
    """
    pipeline = TransformerPipeline()

    types_to_include = component_types or ["skill", "agent", "command"]

    for component_type in types_to_include:
        try:
            transformer = get_transformer(platform, component_type)
            pipeline.add(transformer)
        except ValueError:
            pass  # Skip unsupported combinations

    return pipeline


__all__ = [
    # Base classes
    "BaseTransformer",
    "TransformContext",
    "TransformResult",
    "TransformerPipeline",
    "PassthroughTransformer",
    "TerminologyTransformer",
    "FrontmatterTransformer",
    # Component transformers
    "SkillTransformer",
    "SkillTransformerFactory",
    "AgentTransformer",
    "AgentTransformerFactory",
    "CommandTransformer",
    "CommandTransformerFactory",
    "HookTransformer",
    "HookTransformerFactory",
    # Factory functions
    "get_transformer",
    "transform_content",
    "create_pipeline",
    # Hook utilities
    "generate_hooks_json",
    "parse_hooks_json",
]
