"""Generate rules and skills from detected patterns.

This module creates the actual rule/skill files that will be added
to the Ring plugin based on user-approved patterns.
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def slugify(text: str, default: str = "unnamed-pattern") -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: Input text
        default: Fallback value if text produces empty slug

    Returns:
        Lowercase, hyphen-separated slug
    """
    if not text or not text.strip():
        return default
    # Lowercase and replace non-alphanumeric with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower())
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug if slug else default


def generate_rule_content(pattern: Dict) -> str:
    """Generate markdown content for a rule.

    Args:
        pattern: Pattern dictionary with canonical, occurrences, sessions

    Returns:
        Markdown content for the rule file
    """
    canonical = pattern["canonical"]
    occurrences = pattern.get("occurrences", 0)
    sessions = pattern.get("sessions", [])
    sources = pattern.get("sources", [])

    # Generate DO/DON'T based on pattern text
    if canonical.lower().startswith("avoid"):
        dont_text = canonical.replace("Avoid: ", "").replace("avoid ", "")
        do_text = f"Do the opposite of: {dont_text}"
    else:
        do_text = canonical
        dont_text = f"Skip or ignore: {canonical}"

    content = f"""# {canonical}

**Context:** This rule emerged from {occurrences} sessions where this pattern appeared.

## Pattern

{canonical}

## DO

- {do_text}

## DON'T

- {dont_text}

## Source Sessions

This rule was automatically generated from learnings in these sessions:

"""
    for session in sessions[:10]:  # Show first 10
        content += f"- `{session}`\n"

    if len(sessions) > 10:
        content += f"- ... and {len(sessions) - 10} more sessions\n"

    content += f"""
## Evidence

- **Occurrences:** {occurrences} times across {len(sessions)} sessions
- **Sources:** {', '.join(set(sources))}
- **Generated:** {datetime.now().strftime('%Y-%m-%d')}
"""

    return content


def generate_skill_content(pattern: Dict) -> str:
    """Generate markdown content for a skill.

    Args:
        pattern: Pattern dictionary with canonical, occurrences, sessions

    Returns:
        Markdown content for SKILL.md file
    """
    canonical = pattern["canonical"]
    occurrences = pattern.get("occurrences", 0)
    sessions = pattern.get("sessions", [])
    slug = slugify(canonical)

    # Create description for frontmatter
    description = f"Use when {canonical.lower()} - emerged from {occurrences} sessions"
    if len(description) > 200:
        description = description[:197] + "..."

    content = f"""---
name: {slug}
description: |
  {description}
---

# {canonical}

## Overview

This skill emerged from patterns observed across {occurrences} sessions.

{canonical}

## When to Use

- When you encounter situations similar to those in the source sessions
- When the pattern would apply to your current task

## When NOT to Use

- When the context is significantly different from the source sessions
- When project-specific conventions override this pattern

## Process

1. [Step 1 - TO BE FILLED: Review and customize this skill]
2. [Step 2 - TO BE FILLED: Add specific steps for your use case]
3. [Step 3 - TO BE FILLED: Include verification steps]

## Source Sessions

This skill was automatically generated from learnings in these sessions:

"""
    for session in sessions[:10]:
        content += f"- `{session}`\n"

    content += f"""
## Notes

- **Generated:** {datetime.now().strftime('%Y-%m-%d')}
- **IMPORTANT:** This skill needs human review and customization before use
- Edit the Process section to add specific, actionable steps
"""

    return content


class RuleGenerationError(Exception):
    """Error raised when rule/skill generation fails."""
    pass


def create_rule_file(pattern: Dict, rules_dir: Path) -> Path:
    """Create a rule file on disk.

    Args:
        pattern: Pattern dictionary
        rules_dir: Path to rules directory

    Returns:
        Path to created rule file

    Raises:
        RuleGenerationError: If file cannot be written
    """
    slug = slugify(pattern["canonical"])
    file_path = rules_dir / f"{slug}.md"

    content = generate_rule_content(pattern)

    try:
        file_path.write_text(content, encoding='utf-8')
    except (IOError, PermissionError, OSError) as e:
        raise RuleGenerationError(f"Failed to write rule file {file_path}: {e}") from e

    return file_path


def create_skill_file(pattern: Dict, skills_dir: Path) -> Path:
    """Create a skill directory and SKILL.md file.

    Args:
        pattern: Pattern dictionary
        skills_dir: Path to skills directory

    Returns:
        Path to created skill directory

    Raises:
        RuleGenerationError: If directory/file cannot be created
    """
    slug = slugify(pattern["canonical"])
    skill_dir = skills_dir / slug

    try:
        skill_dir.mkdir(exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        content = generate_skill_content(pattern)
        skill_file.write_text(content, encoding='utf-8')
    except (IOError, PermissionError, OSError) as e:
        raise RuleGenerationError(f"Failed to create skill {skill_dir}: {e}") from e

    return skill_dir


def generate_proposal(patterns: List[Dict]) -> Dict:
    """Generate a proposal document for user review.

    Args:
        patterns: List of recurring patterns from pattern_detector

    Returns:
        Proposal dictionary with proposals list and metadata
    """
    proposals = []

    for i, pattern in enumerate(patterns):
        category = pattern.get("category", "rule")

        proposal = {
            "id": f"proposal-{i+1}",
            "canonical": pattern["canonical"],
            "category": category,
            "occurrences": pattern.get("occurrences", 0),
            "sessions": pattern.get("sessions", []),
            "sources": pattern.get("sources", []),
            "status": "pending",
            "preview": (
                generate_rule_content(pattern)
                if category == "rule"
                else generate_skill_content(pattern)
            ),
        }
        proposals.append(proposal)

    return {
        "generated": datetime.now().isoformat(),
        "total_proposals": len(proposals),
        "proposals": proposals,
    }


def save_proposal(proposal: Dict, proposals_dir: Path) -> Path:
    """Save proposal to pending.json file.

    Args:
        proposal: Proposal dictionary from generate_proposal
        proposals_dir: Path to .ring/cache/proposals/

    Returns:
        Path to saved proposals file
    """
    proposals_dir.mkdir(parents=True, exist_ok=True)
    pending_file = proposals_dir / "pending.json"

    with open(pending_file, 'w', encoding='utf-8') as f:
        json.dump(proposal, f, indent=2)

    return pending_file


def load_pending_proposals(proposals_dir: Path) -> Optional[Dict]:
    """Load pending proposals from file.

    Args:
        proposals_dir: Path to proposals directory

    Returns:
        Proposal dictionary or None if not found/corrupted
    """
    pending_file = proposals_dir / "pending.json"

    if not pending_file.exists():
        return None

    try:
        with open(pending_file, encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _update_proposal_status(
    proposal_id: str,
    proposals_dir: Path,
    status: str,
    extra_fields: Optional[Dict] = None
) -> Optional[Dict]:
    """Common logic for updating proposal status.

    Args:
        proposal_id: ID of proposal to update
        proposals_dir: Path to proposals directory
        status: New status ("approved" or "rejected")
        extra_fields: Additional fields to add to proposal

    Returns:
        Updated proposal dictionary, or None if not found
    """
    pending_file = proposals_dir / "pending.json"
    history_file = proposals_dir / "history.json"

    if not pending_file.exists():
        return None

    try:
        with open(pending_file, encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

    # Find and update proposal
    updated = None
    for proposal in data.get("proposals", []):
        if proposal["id"] == proposal_id:
            proposal["status"] = status
            proposal[f"{status}_at"] = datetime.now().isoformat()
            if extra_fields:
                proposal.update(extra_fields)
            updated = proposal
            break

    if updated:
        # Save updated pending file
        with open(pending_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        # Append to history
        history = []
        if history_file.exists():
            try:
                with open(history_file, encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        history = loaded
            except (json.JSONDecodeError, IOError):
                pass  # Start with empty history if corrupt
        history.append(updated)
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)

    return updated


def approve_proposal(proposal_id: str, proposals_dir: Path) -> Optional[Dict]:
    """Mark a proposal as approved.

    Args:
        proposal_id: ID of proposal to approve
        proposals_dir: Path to proposals directory

    Returns:
        Approved proposal dictionary, or None if not found
    """
    return _update_proposal_status(proposal_id, proposals_dir, "approved")


def reject_proposal(
    proposal_id: str, proposals_dir: Path, reason: str = ""
) -> Optional[Dict]:
    """Mark a proposal as rejected.

    Args:
        proposal_id: ID of proposal to reject
        proposals_dir: Path to proposals directory
        reason: Optional rejection reason

    Returns:
        Rejected proposal dictionary, or None if not found
    """
    return _update_proposal_status(
        proposal_id, proposals_dir, "rejected",
        {"rejection_reason": reason}
    )
