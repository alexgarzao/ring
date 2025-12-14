#!/usr/bin/env python3
"""
YAML frontmatter parser for Ring markdown files.

Extracts metadata from SKILL.md, agent.md, and command.md files.
Based on patterns from default/hooks/generate-skills-ref.py.
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("Warning: PyYAML not installed, using fallback parser", file=sys.stderr)

try:
    from .models import Component, ComponentType
except ImportError:
    from models import Component, ComponentType


def extract_frontmatter(content: str) -> Optional[Dict[str, Any]]:
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return None

    if YAML_AVAILABLE:
        try:
            frontmatter = yaml.safe_load(match.group(1))
            return frontmatter if isinstance(frontmatter, dict) else None
        except yaml.YAMLError as e:
            print(f"Warning: YAML parse error: {e}", file=sys.stderr)
            return None
    else:
        # Fallback regex parser for basic fields
        return _parse_frontmatter_fallback(match.group(1))


def _parse_frontmatter_fallback(text: str) -> Dict[str, Any]:
    """Fallback parser using regex when PyYAML unavailable."""
    result = {}

    # Simple scalar fields
    for field in ['name', 'description', 'trigger', 'skip_when', 'model', 'argument-hint']:
        pattern = rf'^{field}:\s*\|?\s*\n?(.*?)(?=^[a-z_-]+:|\Z)'
        match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            # Clean up multi-line values
            lines = [line.strip().lstrip('- ') for line in value.split('\n')
                     if line.strip() and not line.strip().startswith('#')]
            if lines:
                result[field.replace('-', '_')] = lines[0] if len(lines) == 1 else '\n'.join(lines)

    return result


def extract_keywords_from_content(content: str, frontmatter: Dict[str, Any]) -> List[str]:
    """Extract searchable keywords from content and frontmatter."""
    keywords = set()

    # From frontmatter fields
    if 'trigger' in frontmatter:
        keywords.update(_extract_terms(frontmatter['trigger']))
    if 'skip_when' in frontmatter:
        keywords.update(_extract_terms(frontmatter['skip_when']))
    if 'related' in frontmatter and isinstance(frontmatter['related'], dict):
        for key in ['similar', 'complementary']:
            if key in frontmatter['related']:
                keywords.update(frontmatter['related'][key])

    # From markdown headings
    headings = re.findall(r'^##?\s+(.+)$', content, re.MULTILINE)
    for heading in headings[:10]:  # Limit to first 10 headings
        keywords.update(_extract_terms(heading))

    return sorted(list(keywords))


def _extract_terms(text: str) -> List[str]:
    """Extract meaningful terms from text."""
    if not text:
        return []
    # Split on common delimiters and filter
    terms = re.split(r'[\s,\-\>→:]+', text.lower())
    # Filter short and common words
    stopwords = {'the', 'a', 'an', 'is', 'are', 'for', 'to', 'and', 'or', 'in', 'on', 'at', 'of', 'with'}
    return [t for t in terms if len(t) > 2 and t not in stopwords and t.isalnum()]


def extract_use_cases(frontmatter: Dict[str, Any]) -> List[str]:
    """Extract use cases from trigger and description fields."""
    use_cases = []

    if 'trigger' in frontmatter:
        trigger = frontmatter['trigger']
        if isinstance(trigger, str):
            # Split multi-line triggers into separate use cases
            lines = [line.strip().lstrip('- ') for line in trigger.split('\n')
                     if line.strip() and line.strip() != '-']
            use_cases.extend(lines)
        elif isinstance(trigger, list):
            use_cases.extend(trigger)

    return use_cases


def first_line(text: str) -> str:
    """Extract first meaningful line from text."""
    if not text:
        return ""
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip().lstrip('- ')
        if line and not line.startswith('#'):
            return line
    return lines[0].strip() if lines else ""


def parse_skill_file(file_path: Path, plugin_name: str) -> Optional[Component]:
    """Parse a SKILL.md file and create Component."""
    try:
        content = file_path.read_text(encoding='utf-8')
        frontmatter = extract_frontmatter(content)

        if not frontmatter or 'name' not in frontmatter:
            print(f"Warning: Missing name in {file_path}", file=sys.stderr)
            return None

        name = frontmatter['name']
        description = first_line(frontmatter.get('description', ''))

        return Component(
            plugin=plugin_name,
            type=ComponentType.SKILL,
            name=name,
            fqn=f"{plugin_name}:{name}",
            description=description,
            use_cases=extract_use_cases(frontmatter),
            keywords=extract_keywords_from_content(content, frontmatter),
            file_path=str(file_path),
            full_content=content,
            trigger=frontmatter.get('trigger'),
            skip_when=frontmatter.get('skip_when'),
        )
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return None


def parse_agent_file(file_path: Path, plugin_name: str) -> Optional[Component]:
    """Parse an agent.md file and create Component."""
    try:
        content = file_path.read_text(encoding='utf-8')
        frontmatter = extract_frontmatter(content)

        if not frontmatter or 'name' not in frontmatter:
            print(f"Warning: Missing name in {file_path}", file=sys.stderr)
            return None

        name = frontmatter['name']
        description = first_line(frontmatter.get('description', ''))

        # Extract use cases from description and content
        use_cases = []
        if 'description' in frontmatter:
            use_cases.append(first_line(frontmatter['description']))

        return Component(
            plugin=plugin_name,
            type=ComponentType.AGENT,
            name=name,
            fqn=f"{plugin_name}:{name}",
            description=description,
            use_cases=use_cases,
            keywords=extract_keywords_from_content(content, frontmatter),
            file_path=str(file_path),
            full_content=content,
            model=frontmatter.get('model'),
        )
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return None


def parse_command_file(file_path: Path, plugin_name: str) -> Optional[Component]:
    """Parse a command.md file and create Component."""
    try:
        content = file_path.read_text(encoding='utf-8')
        frontmatter = extract_frontmatter(content)

        if not frontmatter or 'name' not in frontmatter:
            print(f"Warning: Missing name in {file_path}", file=sys.stderr)
            return None

        name = frontmatter['name']
        description = first_line(frontmatter.get('description', ''))
        argument_hint = frontmatter.get('argument-hint', frontmatter.get('argument_hint'))

        return Component(
            plugin=plugin_name,
            type=ComponentType.COMMAND,
            name=name,
            fqn=f"/ring-{plugin_name.replace('ring-', '')}:{name}" if not name.startswith('/') else name,
            description=description,
            use_cases=[description] if description else [],
            keywords=extract_keywords_from_content(content, frontmatter),
            file_path=str(file_path),
            full_content=content,
            argument_hint=argument_hint,
        )
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return None
