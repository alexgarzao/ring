"""
Ring CLI Metadata Extractor package.

Provides tools for extracting component metadata from Ring plugins
and building the SQLite search index.
"""

from .models import Component, ComponentType
from .parser import extract_frontmatter, parse_skill_file, parse_agent_file, parse_command_file
from .scanner import scan_all_plugins, scan_plugin
from .database import create_database, insert_components, search_fts, get_database_stats, rebuild_fts_index

__all__ = [
    'Component',
    'ComponentType',
    'extract_frontmatter',
    'parse_skill_file',
    'parse_agent_file',
    'parse_command_file',
    'scan_all_plugins',
    'scan_plugin',
    'create_database',
    'insert_components',
    'search_fts',
    'get_database_stats',
    'rebuild_fts_index',
]
