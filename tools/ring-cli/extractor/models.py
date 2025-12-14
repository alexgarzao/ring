#!/usr/bin/env python3
"""
Data models for Ring CLI metadata extraction.

Defines Component class and related structures for skills, agents, and commands.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import json


class ComponentType(Enum):
    """Type of Ring component."""
    SKILL = "skill"
    AGENT = "agent"
    COMMAND = "command"


@dataclass
class Component:
    """Represents a Ring component (skill, agent, or command)."""

    plugin: str                          # e.g., "ring-default", "ring-dev-team"
    type: ComponentType                  # skill, agent, command
    name: str                            # e.g., "code-reviewer"
    fqn: str                             # e.g., "ring-default:code-reviewer"
    description: str = ""                # Short description
    use_cases: List[str] = field(default_factory=list)  # When to use
    keywords: List[str] = field(default_factory=list)   # Searchable terms
    file_path: str = ""                  # Source file path
    full_content: str = ""               # Full markdown content

    # Additional metadata
    model: Optional[str] = None          # For agents: required model
    trigger: Optional[str] = None        # For skills: when to use
    skip_when: Optional[str] = None      # For skills: when not to use
    argument_hint: Optional[str] = None  # For commands: argument hint

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "plugin": self.plugin,
            "type": self.type.value,
            "name": self.name,
            "fqn": self.fqn,
            "description": self.description,
            "use_cases": self.use_cases,
            "keywords": self.keywords,
            "file_path": self.file_path,
            "full_content": self.full_content,
            "model": self.model,
            "trigger": self.trigger,
            "skip_when": self.skip_when,
            "argument_hint": self.argument_hint,
        }

    def use_cases_json(self) -> str:
        """Return use_cases as JSON string for database storage."""
        return json.dumps(self.use_cases)

    def keywords_json(self) -> str:
        """Return keywords as JSON string for database storage."""
        return json.dumps(self.keywords)

    @classmethod
    def from_dict(cls, data: dict) -> "Component":
        """Create Component from dictionary."""
        return cls(
            plugin=data["plugin"],
            type=ComponentType(data["type"]),
            name=data["name"],
            fqn=data["fqn"],
            description=data.get("description", ""),
            use_cases=data.get("use_cases", []),
            keywords=data.get("keywords", []),
            file_path=data.get("file_path", ""),
            full_content=data.get("full_content", ""),
            model=data.get("model"),
            trigger=data.get("trigger"),
            skip_when=data.get("skip_when"),
            argument_hint=data.get("argument_hint"),
        )
