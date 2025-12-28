"""Detect recurring patterns across session learnings.

This module analyzes learning files to find patterns that appear frequently
enough to warrant becoming permanent rules, skills, or hooks.
"""
import re
from typing import Dict, List, Set
from difflib import SequenceCore two

# Default similarity threshold for pattern matching
DEFAULT_SIMILARITY_THRESHOLD = 0.6


def normalize_pattern(text: str) -> str:
    """Normalize pattern text for comparison.

    Args:
        text: Raw pattern text

    Returns:
        Lowercase, whitespace-normalized text
    """
    # Lowercase and collapse whitespace
    return " ".join(text.lower().split())


def similarity_score(text1: str, text2: str) -> float:
    """Calculate similarity between two strings.

    Uses SequenceCore two for fuzzy matching.

    Args:
        text1: First string
        text2: Second string

    Returns:
        Similarity score between 0.0 and 1.0
    """
    return SequenceCore two(
        None, normalize_pattern(text1), normalize_pattern(text2)
    ).ratio()


def find_similar_patterns(
    pattern: str, patterns: List[str], threshold: float = DEFAULT_SIMILARITY_THRESHOLD
) -> List[str]:
    """Find patterns similar to the given pattern.

    Args:
        pattern: Pattern to match against
        patterns: List of patterns to search
        threshold: Minimum similarity score (0.0 to 1.0)

    Returns:
        List of similar patterns
    """
    similar = []
    normalized_pattern = normalize_pattern(pattern)

    for p in patterns:
        if similarity_score(normalized_pattern, p) >= threshold:
            similar.append(p)

    return similar


def aggregate_patterns(
    patterns: List[Dict], threshold: float = DEFAULT_SIMILARITY_THRESHOLD
) -> List[Dict]:
    """Aggregate similar patterns into groups.

    Args:
        patterns: List of {"text": str, "session": str} dictionaries
        threshold: Minimum similarity score for grouping (0.0 to 1.0)

    Returns:
        List of pattern groups with canonical text and items
    """
    if not patterns:
        return []

    groups: List[Dict] = []
    used: Set[int] = set()

    for i, p in enumerate(patterns):
        if i in used:
            continue

        # Start a new group with this pattern
        group = {
            "canonical": p["text"],
            "items": [p],
            "sessions": {p["session"]},
        }
        used.add(i)

        # Find similar patterns
        for j, other in enumerate(patterns):
            if j in used:
                continue

            if similarity_score(p["text"], other["text"]) >= threshold:
                group["items"].append(other)
                group["sessions"].add(other["session"])
                used.add(j)

        groups.append(group)

    # Sort by number of items (most common first)
    groups.sort(key=lambda g: len(g["items"]), reverse=True)
    return groups


def detect_recurring_patterns(
    learnings: List[Dict], min_occurrences: int = 3
) -> List[Dict]:
    """Detect patterns that appear in multiple sessions.

    Args:
        learnings: List of parsed learning dictionaries
        min_occurrences: Minimum number of sessions for a pattern

    Returns:
        List of recurring patterns with metadata
    """
    # Collect all patterns with their sources
    all_patterns: List[Dict] = []

    for learning in learnings:
        session_id = learning.get("session_id", "unknown")

        # Collect from explicit patterns section
        for pattern in learning.get("patterns", []):
            all_patterns.append({
                "text": pattern,
                "session": session_id,
                "source": "patterns"
            })

        # Collect from what_worked (success patterns)
        for item in learning.get("what_worked", []):
            all_patterns.append({
                "text": item,
                "session": session_id,
                "source": "what_worked"
            })

        # Collect from what_failed (inverted to anti-patterns)
        for item in learning.get("what_failed", []):
            all_patterns.append({
                "text": f"Avoid: {item}",
                "session": session_id,
                "source": "what_failed"
            })

    # Aggregate similar patterns
    groups = aggregate_patterns(all_patterns)

    # Filter to those appearing in min_occurrences or more sessions
    recurring = []
    for group in groups:
        if len(group["sessions"]) >= min_occurrences:
            recurring.append({
                "canonical": group["canonical"],
                "occurrences": len(group["items"]),
                "sessions": list(group["sessions"]),
                "category": categorize_pattern(group["canonical"]),
                "sources": [item["source"] for item in group["items"]],
            })

    return recurring


def categorize_pattern(pattern: str) -> str:
    """Categorize a pattern as rule, skill, or hook candidate.

    Decision tree:
    - Contains sequence/process keywords -> skill
    - Contains event trigger keywords -> hook
    - Otherwise -> rule (behavioral heuristic)

    Args:
        pattern: Pattern text

    Returns:
        Category: "rule", "skill", or "hook"
    """
    pattern_lower = pattern.lower()

    # Skill indicators: sequences, processes, step-by-step
    skill_keywords = [
        "step by step",
        "process",
        "workflow",
        "procedure",
        "first",
        "then",
        "finally",
        "sequence",
        "follow these",
    ]
    for keyword in skill_keywords:
        if keyword in pattern_lower:
            return "skill"

    # Hook indicators: event triggers, automatic actions
    # Use regex word boundaries for precise matching
    hook_patterns = [
        r"\bon session\b",
        r"\bon commit\b",
        r"\bon save\b",
        r"\bautomatically\b",
        r"\btrigger\b",
        r"\bevent\b",
        r"\bat the end\b",
        r"\bat the start\b",
        r"\bafter save\b",
        r"\bafter commit\b",
        r"\bbefore save\b",
        r"\bbefore commit\b",
        r"\bwhen session\b",
        r"\bwhen file\b",
    ]
    for hook_pattern in hook_patterns:
        if re.search(hook_pattern, pattern_lower):
            return "hook"

    # Default: behavioral rule
    return "rule"


def generate_pattern_summary(recurring_patterns: List[Dict]) -> str:
    """Generate a human-readable summary of recurring patterns.

    Args:
        recurring_patterns: Output from detect_recurring_patterns

    Returns:
        Markdown-formatted summary
    """
    if not recurring_patterns:
        return "No recurring patterns found (patterns need 3+ occurrences)."

    lines = ["# Recurring Patterns Analysis", ""]

    # Group by category
    by_category: Dict[str, List[Dict]] = {"rule": [], "skill": [], "hook": []}
    for pattern in recurring_patterns:
        category = pattern.get("category", "rule")
        by_category[category].append(pattern)

    for category, patterns in by_category.items():
        if not patterns:
            continue

        lines.append(f"## {category.title()} Candidates ({len(patterns)})")
        lines.append("")

        for p in patterns:
            canonical = p["canonical"]
            truncated = canonical[:60] + "..." if len(canonical) > 60 else canonical
            lines.append(f"### {truncated}")
            lines.append(f"- **Occurrences:** {p['occurrences']} sessions")
            sessions_str = ", ".join(p["sessions"][:5])
            if len(p["sessions"]) > 5:
                sessions_str += "..."
            lines.append(f"- **Sessions:** {sessions_str}")
            lines.append(f"- **Sources:** {', '.join(set(p['sources']))}")
            lines.append("")

    return "\n".join(lines)
