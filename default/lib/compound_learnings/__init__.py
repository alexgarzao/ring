"""Compound Learnings Library - Transform session learnings into permanent capabilities.

This package provides:
- Learning file parsing (learning_parser)
- Pattern detection across sessions (pattern_detector)
- Rule/skill generation from patterns (rule_generator)
"""

from .learning_parser import (
    parse_learning_file,
    extract_patterns,
    extract_what_worked,
    extract_what_failed,
    extract_key_decisions,
    load_all_learnings,
)

from .pattern_detector import (
    normalize_pattern,
    find_similar_patterns,
    aggregate_patterns,
    detect_recurring_patterns,
    categorize_pattern,
    generate_pattern_summary,
    similarity_score,
    DEFAULT_SIMILARITY_THRESHOLD,
)

from .rule_generator import (
    generate_rule_content,
    generate_skill_content,
    create_rule_file,
    create_skill_file,
    generate_proposal,
    save_proposal,
    load_pending_proposals,
    approve_proposal,
    reject_proposal,
    slugify,
    RuleGenerationError,
)

__all__ = [
    # learning_parser
    "parse_learning_file",
    "extract_patterns",
    "extract_what_worked",
    "extract_what_failed",
    "extract_key_decisions",
    "load_all_learnings",
    # pattern_detector
    "normalize_pattern",
    "find_similar_patterns",
    "aggregate_patterns",
    "detect_recurring_patterns",
    "categorize_pattern",
    "generate_pattern_summary",
    "similarity_score",
    "DEFAULT_SIMILARITY_THRESHOLD",
    # rule_generator
    "generate_rule_content",
    "generate_skill_content",
    "create_rule_file",
    "create_skill_file",
    "generate_proposal",
    "save_proposal",
    "load_pending_proposals",
    "approve_proposal",
    "reject_proposal",
    "slugify",
    "RuleGenerationError",
]
