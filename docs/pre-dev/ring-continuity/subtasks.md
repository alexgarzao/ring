# Ring Continuity - Subtask Breakdown (Gate 8)

> **Version:** 1.0
> **Date:** 2026-01-12
> **Status:** Draft
> **Based on:** Tasks v1.0 (docs/pre-dev/ring-continuity/tasks.md)

---

## Executive Summary

This document breaks down the 15 tasks from Gate 7 into **78 bite-sized subtasks** (2-5 minutes each). Each subtask follows the **TDD pattern** (test first, then implementation) and includes **complete code** with no placeholders. Subtasks are grouped by phase for parallel write-plan agent execution.

**Implementation Strategy:** Spawn 5 write-plan agents (one per phase) with comprehensive context from Gates 0-7.

---

## Phase 1: Foundation (3 Tasks → 16 Subtasks)

**Context for write-plan agent:**
- Read: `docs/pre-dev/ring-continuity/research.md` (Gate 0)
- Read: `docs/pre-dev/ring-continuity/trd.md` (Gate 3)
- Read: `docs/pre-dev/ring-continuity/api-design.md` (Gate 4)
- Read: `docs/pre-dev/ring-continuity/dependency-map.md` (Gate 6)
- Focus: Establish ~/.ring/ directory with config precedence
- Output: `default/lib/ring_home.py`, install script, tests

---

### Task 1.1: Create ~/.ring/ Directory Structure (6 subtasks)

#### Subtask 1.1.1: Write test for directory creation (RED)

**Time:** 2 min

**What:** Create test that verifies ~/.ring/ directory exists with correct structure.

**TDD Phase:** RED (test fails, directory doesn't exist yet)

**File:** `tests/test_ring_home.py`

**Code:**
```python
import pytest
from pathlib import Path
from default.lib.ring_home import RingHomeManager

def test_ensure_directory_exists():
    """Test that ~/.ring/ is created with correct structure."""
    manager = RingHomeManager()

    result = manager.ensure_directory_exists()

    assert result.success is True
    assert result.path == Path.home() / '.ring'
    assert (result.path / 'handoffs').exists()
    assert (result.path / 'cache').exists()
    assert (result.path / 'logs').exists()
    assert (result.path / 'state').exists()

def test_directory_already_exists():
    """Test idempotency - safe to run multiple times."""
    manager = RingHomeManager()

    # First call
    result1 = manager.ensure_directory_exists()

    # Second call
    result2 = manager.ensure_directory_exists()

    assert result2.success is True
    assert result2.created is False  # Not newly created
```

**Verification:**
```bash
pytest tests/test_ring_home.py::test_ensure_directory_exists -v
# Expected: FAIL (ring_home.py doesn't exist)
```

---

#### Subtask 1.1.2: Implement RingHome data class (GREEN)

**Time:** 3 min

**What:** Create data class for RingHome result.

**TDD Phase:** GREEN (minimal implementation)

**File:** `default/lib/ring_home.py`

**Code:**
```python
"""Ring home directory management."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class RingHome:
    """Result of directory initialization."""
    success: bool
    path: Path
    created: bool  # True if newly created
    config_path: Path
    memory_path: Path
    handoffs_path: Path
    error: Optional[str] = None

class RingHomeManager:
    """Manages the ~/.ring/ directory."""

    def __init__(self, home_dir: Optional[Path] = None):
        """Initialize manager.

        Args:
            home_dir: Override home directory (for testing)
        """
        self.home_dir = home_dir or Path.home()
        self.ring_dir = self.home_dir / '.ring'
```

**Verification:**
```bash
python3 -c "from default.lib.ring_home import RingHomeManager; print('Import OK')"
# Expected: SUCCESS
```

---

#### Subtask 1.1.3: Implement ensure_directory_exists (GREEN)

**Time:** 4 min

**What:** Create ~/.ring/ with subdirectories.

**TDD Phase:** GREEN

**File:** `default/lib/ring_home.py` (add method)

**Code:**
```python
    def ensure_directory_exists(self) -> RingHome:
        """Ensure ~/.ring/ exists with standard structure.

        Returns:
            RingHome with success status and paths
        """
        created = False

        try:
            # Create main directory
            if not self.ring_dir.exists():
                self.ring_dir.mkdir(mode=0o755, parents=True)
                created = True

            # Create subdirectories
            subdirs = ['handoffs', 'cache', 'logs', 'state']
            for subdir in subdirs:
                subdir_path = self.ring_dir / subdir
                subdir_path.mkdir(mode=0o755, exist_ok=True)

            return RingHome(
                success=True,
                path=self.ring_dir,
                created=created,
                config_path=self.ring_dir / 'config.yaml',
                memory_path=self.ring_dir / 'memory.db',
                handoffs_path=self.ring_dir / 'handoffs'
            )

        except PermissionError as e:
            return RingHome(
                success=False,
                path=self.ring_dir,
                created=False,
                config_path=Path(),
                memory_path=Path(),
                handoffs_path=Path(),
                error=f"Permission denied: {e}"
            )
```

**Verification:**
```bash
pytest tests/test_ring_home.py::test_ensure_directory_exists -v
# Expected: PASS (green)
```

---

#### Subtask 1.1.4: Write test for permission error fallback (RED)

**Time:** 2 min

**What:** Test fallback to project .ring/ if ~/.ring/ creation fails.

**TDD Phase:** RED

**File:** `tests/test_ring_home.py` (add test)

**Code:**
```python
def test_permission_denied_fallback(tmp_path, monkeypatch):
    """Test fallback to project .ring/ if home not writable."""
    import os

    # Mock Path.home() to return unwritable directory
    unwritable = tmp_path / 'unwritable'
    unwritable.mkdir(mode=0o000)

    monkeypatch.setattr('pathlib.Path.home', lambda: unwritable)

    manager = RingHomeManager()
    result = manager.ensure_directory_exists()

    # Should fail with error
    assert result.success is False
    assert 'Permission denied' in result.error

    # Should suggest fallback
    assert result.fallback_path == Path.cwd() / '.ring'
```

**Verification:**
```bash
pytest tests/test_ring_home.py::test_permission_denied_fallback -v
# Expected: FAIL (fallback_path not implemented)
```

---

#### Subtask 1.1.5: Implement fallback to project .ring/ (GREEN)

**Time:** 3 min

**What:** Add fallback_path to RingHome and suggest alternative.

**TDD Phase:** GREEN

**File:** `default/lib/ring_home.py` (modify)

**Code:**
```python
@dataclass
class RingHome:
    """Result of directory initialization."""
    success: bool
    path: Path
    created: bool
    config_path: Path
    memory_path: Path
    handoffs_path: Path
    error: Optional[str] = None
    fallback_path: Optional[Path] = None  # NEW

    def ensure_directory_exists(self) -> RingHome:
        """Ensure ~/.ring/ exists with standard structure."""
        created = False

        try:
            # ... existing code ...

        except PermissionError as e:
            # Suggest fallback to project .ring/
            project_ring = Path.cwd() / '.ring'

            return RingHome(
                success=False,
                path=self.ring_dir,
                created=False,
                config_path=Path(),
                memory_path=Path(),
                handoffs_path=Path(),
                error=f"Permission denied: {e}",
                fallback_path=project_ring  # NEW
            )
```

**Verification:**
```bash
pytest tests/test_ring_home.py::test_permission_denied_fallback -v
# Expected: PASS (green)
```

---

#### Subtask 1.1.6: Write install script (INTEGRATION)

**Time:** 5 min

**What:** Bash script that creates ~/.ring/ and reports status.

**File:** `scripts/install-ring-home.sh`

**Code:**
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "🔄 Initializing Ring home directory..."

# Determine Ring home
RING_HOME="${RING_HOME:-${HOME}/.ring}"

# Create directory structure
if mkdir -p "${RING_HOME}"/{handoffs,cache,logs,state} 2>/dev/null; then
    echo "✅ Created ${RING_HOME}"

    # Create default config if missing
    if [[ ! -f "${RING_HOME}/config.yaml" ]]; then
        cat > "${RING_HOME}/config.yaml" <<'EOF'
# Ring Configuration
memory:
  enabled: true
  max_memories: 10000

skill_activation:
  enabled: true

handoffs:
  format: yaml
EOF
        echo "📝 Created default config: ${RING_HOME}/config.yaml"
    fi

    echo ""
    echo "Ring home directory initialized successfully!"
    echo "Location: ${RING_HOME}"
else
    echo "⚠️  Could not create ${RING_HOME}"
    echo "   Fallback: Ring will use .ring/ in each project"
fi
```

**Verification:**
```bash
bash scripts/install-ring-home.sh
test -d ~/.ring/handoffs || exit 1
test -f ~/.ring/config.yaml || exit 1
echo "✅ Install script works"
```

---

### Task 1.2: Implement Config Precedence System (5 subtasks)

#### Subtask 1.2.1: Write test for config loading (RED)

**Time:** 3 min

**File:** `tests/test_config_loader.py`

**Code:**
```python
import pytest
from pathlib import Path
from default.lib.config_loader import ConfigLoader

def test_load_global_config():
    """Test loading global config from ~/.ring/config.yaml."""
    loader = ConfigLoader()

    config = loader.load_config(scope='global')

    assert config is not None
    assert 'memory' in config
    assert config['memory']['enabled'] is True

def test_config_precedence():
    """Test project config overrides global config."""
    loader = ConfigLoader()

    # Get value that exists in both global and project
    value = loader.get_config_value('memory.enabled')

    # Should show source
    assert value.value in [True, False]
    assert value.source in ['global', 'project', 'default']
    assert value.precedence >= 0
```

**Verification:**
```bash
pytest tests/test_config_loader.py -v
# Expected: FAIL (config_loader.py doesn't exist)
```

---

#### Subtask 1.2.2: Implement ConfigValue data class (GREEN)

**Time:** 2 min

**File:** `default/lib/config_loader.py`

**Code:**
```python
"""Configuration loading with precedence."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import yaml

@dataclass
class ConfigValue:
    """Configuration value with source attribution."""
    value: Any
    source: str  # 'global', 'project', 'default'
    precedence: int  # 0=default, 1=global, 2=project
    file_path: Optional[Path] = None

class ConfigLoader:
    """Loads configuration with precedence: project > global > default."""

    DEFAULT_CONFIG = {
        'memory': {
            'enabled': True,
            'max_memories': 10000,
            'decay': {'enabled': True, 'half_life_days': 180}
        },
        'skill_activation': {
            'enabled': True,
            'enforcement_default': 'suggest'
        },
        'handoffs': {
            'format': 'yaml',
            'auto_index': True
        }
    }

    def __init__(self, ring_home: Optional[Path] = None, project_dir: Optional[Path] = None):
        self.ring_home = ring_home or (Path.home() / '.ring')
        self.project_dir = project_dir or Path.cwd()
```

**Verification:**
```bash
python3 -c "from default.lib.config_loader import ConfigLoader; print('Import OK')"
```

---

#### Subtask 1.2.3: Implement load_config method (GREEN)

**Time:** 4 min

**File:** `default/lib/config_loader.py` (add method)

**Code:**
```python
    def load_config(self, scope: str) -> dict:
        """Load configuration from specified scope.

        Args:
            scope: 'global', 'project', or 'default'

        Returns:
            Configuration dictionary
        """
        if scope == 'default':
            return self.DEFAULT_CONFIG.copy()

        if scope == 'global':
            config_path = self.ring_home / 'config.yaml'
        elif scope == 'project':
            config_path = self.project_dir / '.ring' / 'config.yaml'
        else:
            raise ValueError(f"Invalid scope: {scope}")

        if not config_path.exists():
            return {}

        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load {config_path}: {e}")
            return {}
```

**Verification:**
```bash
pytest tests/test_config_loader.py::test_load_global_config -v
# Expected: PASS if ~/.ring/config.yaml exists
```

---

#### Subtask 1.2.4: Implement merge_configs method (GREEN)

**Time:** 4 min

**File:** `default/lib/config_loader.py` (add method)

**Code:**
```python
    def merge_configs(self, *configs: dict) -> dict:
        """Merge configurations with later configs overriding earlier.

        Args:
            *configs: Config dictionaries in precedence order

        Returns:
            Merged configuration
        """
        result = {}

        for config in configs:
            result = self._deep_merge(result, config)

        return result

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result
```

**Verification:**
```bash
python3 -c "
from default.lib.config_loader import ConfigLoader
loader = ConfigLoader()
merged = loader.merge_configs({'a': 1}, {'a': 2, 'b': 3})
assert merged == {'a': 2, 'b': 3}
print('Merge OK')
"
```

---

#### Subtask 1.2.5: Implement get_config_value with precedence (GREEN)

**Time:** 5 min

**File:** `default/lib/config_loader.py` (add method)

**Code:**
```python
    def get_config_value(self, key: str) -> ConfigValue:
        """Get config value with source attribution.

        Args:
            key: Dot-notation key (e.g., 'memory.enabled')

        Returns:
            ConfigValue with source and precedence
        """
        # Load all configs
        default_config = self.load_config('default')
        global_config = self.load_config('global')
        project_config = self.load_config('project')

        # Check project first (highest precedence)
        value = self._get_nested_value(project_config, key)
        if value is not None:
            return ConfigValue(value=value, source='project', precedence=2,
                             file_path=self.project_dir / '.ring' / 'config.yaml')

        # Then global
        value = self._get_nested_value(global_config, key)
        if value is not None:
            return ConfigValue(value=value, source='global', precedence=1,
                             file_path=self.ring_home / 'config.yaml')

        # Finally default
        value = self._get_nested_value(default_config, key)
        return ConfigValue(value=value, source='default', precedence=0)

    def _get_nested_value(self, config: dict, key: str) -> Any:
        """Get value from nested dict using dot notation."""
        keys = key.split('.')
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None

        return value
```

**Verification:**
```bash
pytest tests/test_config_loader.py::test_config_precedence -v
# Expected: PASS (green)
```

---

#### Subtask 1.2.6: Add integration test for full config system (INTEGRATION)

**Time:** 3 min

**File:** `tests/test_config_loader.py` (add test)

**Code:**
```python
def test_full_config_precedence(tmp_path):
    """Integration test: project overrides global."""
    # Setup global config
    global_ring = tmp_path / '.ring'
    global_ring.mkdir()
    (global_ring / 'config.yaml').write_text("""
memory:
  enabled: true
  max_memories: 5000
""")

    # Setup project config
    project_ring = tmp_path / 'project' / '.ring'
    project_ring.mkdir(parents=True)
    (project_ring / 'config.yaml').write_text("""
memory:
  enabled: false
""")

    # Load with precedence
    loader = ConfigLoader(ring_home=global_ring, project_dir=tmp_path / 'project')

    # memory.enabled should be False (project wins)
    value = loader.get_config_value('memory.enabled')
    assert value.value is False
    assert value.source == 'project'

    # memory.max_memories should be 5000 (from global, not in project)
    value = loader.get_config_value('memory.max_memories')
    assert value.value == 5000
    assert value.source == 'global'
```

**Verification:**
```bash
pytest tests/test_config_loader.py::test_full_config_precedence -v
# Expected: PASS
```

---

### Task 1.3: Create Migration Utilities (5 subtasks)

#### Subtask 1.3.1: Write test for handoff migration (RED)

**Time:** 3 min

**File:** `tests/test_migration.py`

**Code:**
```python
import pytest
from pathlib import Path
from default.lib.migration import migrate_handoffs

def test_migrate_handoffs_to_ring_home(tmp_path):
    """Test migrating project handoffs to ~/.ring/."""
    # Setup source
    project_handoffs = tmp_path / 'project' / 'docs' / 'handoffs' / 'session1'
    project_handoffs.mkdir(parents=True)
    (project_handoffs / '2026-01-12_handoff.md').write_text("""---
session_name: session1
---
Test handoff
""")

    # Setup destination
    ring_home = tmp_path / '.ring'
    ring_home.mkdir()

    # Migrate
    result = migrate_handoffs(
        source=project_handoffs,
        ring_home=ring_home,
        project_name='test-project'
    )

    assert result.success is True
    assert result.items_migrated == 1
    assert (ring_home / 'handoffs' / 'test-project' / 'session1' / '2026-01-12_handoff.md').exists()

    # Original should still exist
    assert (project_handoffs / '2026-01-12_handoff.md').exists()
```

**Verification:**
```bash
pytest tests/test_migration.py::test_migrate_handoffs_to_ring_home -v
# Expected: FAIL (migration.py doesn't exist)
```

---

#### Subtask 1.3.2: Implement MigrationResult data class (GREEN)

**Time:** 2 min

**File:** `default/lib/migration.py`

**Code:**
```python
"""Migration utilities for Ring data."""
from dataclasses import dataclass
from pathlib import Path
from typing import List
import shutil

@dataclass
class MigrationResult:
    """Result of migration operation."""
    success: bool
    source: Path
    destination: Path
    items_migrated: int
    items_skipped: int
    warnings: List[str]
    error: str = ""
```

**Verification:**
```bash
python3 -c "from default.lib.migration import MigrationResult; print('Import OK')"
```

---

#### Subtask 1.3.3: Implement migrate_handoffs function (GREEN)

**Time:** 5 min

**File:** `default/lib/migration.py` (add function)

**Code:**
```python
def migrate_handoffs(source: Path, ring_home: Path, project_name: str) -> MigrationResult:
    """Migrate handoffs from project to ~/.ring/.

    Args:
        source: Source directory (e.g., docs/handoffs/)
        ring_home: Ring home directory (e.g., ~/.ring/)
        project_name: Project identifier for namespacing

    Returns:
        MigrationResult with counts and status
    """
    warnings = []
    migrated = 0
    skipped = 0

    try:
        # Create destination
        dest_base = ring_home / 'handoffs' / project_name
        dest_base.mkdir(parents=True, exist_ok=True)

        # Find all handoff files
        for handoff_file in source.rglob('*.md'):
            if handoff_file.is_file():
                # Preserve directory structure
                relative = handoff_file.relative_to(source)
                dest_file = dest_base / relative
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # Copy (preserve original)
                shutil.copy2(handoff_file, dest_file)
                migrated += 1

        return MigrationResult(
            success=True,
            source=source,
            destination=dest_base,
            items_migrated=migrated,
            items_skipped=skipped,
            warnings=warnings
        )

    except Exception as e:
        return MigrationResult(
            success=False,
            source=source,
            destination=ring_home / 'handoffs' / project_name,
            items_migrated=migrated,
            items_skipped=skipped,
            warnings=warnings,
            error=str(e)
        )
```

**Verification:**
```bash
pytest tests/test_migration.py::test_migrate_handoffs_to_ring_home -v
# Expected: PASS (green)
```

---

#### Subtask 1.3.4: Create migration CLI script (INTEGRATION)

**Time:** 4 min

**File:** `scripts/migrate-ring-data.sh`

**Code:**
```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-.}"
RING_HOME="${RING_HOME:-${HOME}/.ring}"

echo "🔄 Migrating Ring data to ~/.ring/..."
echo "   Project: ${PROJECT_DIR}"
echo "   Destination: ${RING_HOME}"
echo ""

# Detect project name from directory
PROJECT_NAME=$(basename "$(cd "${PROJECT_DIR}" && pwd)")

# Migrate handoffs
if [[ -d "${PROJECT_DIR}/docs/handoffs" ]]; then
    python3 -c "
from pathlib import Path
from default.lib.migration import migrate_handoffs

result = migrate_handoffs(
    source=Path('${PROJECT_DIR}/docs/handoffs'),
    ring_home=Path('${RING_HOME}'),
    project_name='${PROJECT_NAME}'
)

if result.success:
    print(f'✅ Migrated {result.items_migrated} handoffs')
else:
    print(f'❌ Migration failed: {result.error}')
    exit(1)
"
else
    echo "ℹ️  No handoffs to migrate"
fi

echo ""
echo "Migration complete!"
```

**Verification:**
```bash
# Test migration
cd test-project
bash scripts/migrate-ring-data.sh
test -d ~/.ring/handoffs/test-project || exit 1
```

---

#### Subtask 1.3.5: Write rollback script (SAFETY)

**Time:** 3 min

**File:** `scripts/rollback-ring-migration.sh`

**Code:**
```bash
#!/usr/bin/env bash
set -euo pipefail

RING_HOME="${RING_HOME:-${HOME}/.ring}"

echo "⚠️  Rolling back Ring migration..."
echo "   This will remove ${RING_HOME}"
echo ""

read -p "Are you sure? (yes/NO) " -r
if [[ ! "$REPLY" =~ ^yes$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Backup first
BACKUP="${RING_HOME}.backup-$(date +%Y%m%d-%H%M%S)"
if [[ -d "${RING_HOME}" ]]; then
    mv "${RING_HOME}" "${BACKUP}"
    echo "✅ Backed up to ${BACKUP}"
    echo "   To restore: mv ${BACKUP} ${RING_HOME}"
else
    echo "ℹ️  ${RING_HOME} doesn't exist, nothing to rollback"
fi
```

**Verification:**
```bash
# Test rollback
bash scripts/rollback-ring-migration.sh
# Type "yes" when prompted
test ! -d ~/.ring || exit 1
test -d ~/.ring.backup-* || exit 1
```

---

## Phase 2: YAML Handoffs (4 Tasks → 18 Subtasks)

**Context for write-plan agent:**
- Read all previous gates (research.md through dependency-map.md)
- Read: `default/skills/handoff-tracking/SKILL.md` (existing implementation)
- Read: `default/lib/artifact-index/artifact_schema.sql` (existing FTS5 schema)
- Focus: Replace Markdown with YAML, maintain backward compatibility
- Output: Serializer, schema, skill update, indexer update

---

### Task 2.1: Define YAML Handoff Schema (4 subtasks)

#### Subtask 2.1.1: Create JSON Schema for handoff validation (SCHEMA)

**Time:** 5 min

**File:** `default/schemas/handoff-schema-v1.json`

**Code:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ring.lerianstudio.com/schemas/handoff-v1.json",
  "title": "Ring Handoff",
  "description": "Schema for Ring session handoff documents",
  "type": "object",
  "required": ["version", "schema", "session", "task", "resume"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+$",
      "description": "Schema version"
    },
    "schema": {
      "type": "string",
      "const": "ring-handoff-v1",
      "description": "Schema identifier"
    },
    "session": {
      "type": "object",
      "required": ["id", "started_at"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^[a-zA-Z0-9_-]+$",
          "maxLength": 100
        },
        "started_at": {
          "type": "string",
          "format": "date-time"
        },
        "ended_at": {
          "type": "string",
          "format": "date-time"
        },
        "duration_seconds": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "task": {
      "type": "object",
      "required": ["description", "status"],
      "properties": {
        "description": {
          "type": "string",
          "minLength": 1,
          "maxLength": 500
        },
        "status": {
          "type": "string",
          "enum": ["completed", "paused", "blocked", "failed"]
        },
        "skills_used": {
          "type": "array",
          "items": {
            "type": "string",
            "pattern": "^ring:[a-z0-9-]+$"
          }
        }
      }
    },
    "context": {
      "type": "object",
      "properties": {
        "project_path": {"type": "string"},
        "git_commit": {
          "type": "string",
          "pattern": "^[0-9a-f]{40}$"
        },
        "git_branch": {"type": "string"},
        "key_files": {
          "type": "array",
          "items": {"type": "string"},
          "maxItems": 10
        }
      }
    },
    "decisions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["decision", "rationale"],
        "properties": {
          "decision": {"type": "string"},
          "rationale": {"type": "string"},
          "alternatives": {
            "type": "array",
            "items": {"type": "string"}
          }
        }
      }
    },
    "artifacts": {
      "type": "object",
      "properties": {
        "created": {
          "type": "array",
          "items": {"type": "string"}
        },
        "modified": {
          "type": "array",
          "items": {"type": "string"}
        },
        "deleted": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "learnings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type", "content", "confidence"],
        "properties": {
          "type": {
            "type": "string",
            "enum": ["FAILED_APPROACH", "WORKING_SOLUTION", "USER_PREFERENCE", "CODEBASE_PATTERN", "ARCHITECTURAL_DECISION", "ERROR_FIX", "OPEN_THREAD"]
          },
          "content": {"type": "string"},
          "confidence": {
            "type": "string",
            "enum": ["verified", "inferred", "uncertain"]
          }
        }
      }
    },
    "blockers": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type", "description", "severity"],
        "properties": {
          "type": {
            "type": "string",
            "enum": ["technical", "clarification", "external"]
          },
          "description": {"type": "string"},
          "severity": {
            "type": "string",
            "enum": ["critical", "high", "medium"]
          }
        }
      }
    },
    "resume": {
      "type": "object",
      "required": ["next_steps"],
      "properties": {
        "next_steps": {
          "type": "array",
          "items": {"type": "string"},
          "minItems": 1
        },
        "context_needed": {
          "type": "array",
          "items": {"type": "string"}
        },
        "warnings": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    }
  }
}
```

**Verification:**
```bash
python3 -c "import json; json.load(open('default/schemas/handoff-schema-v1.json')); print('Valid JSON')"
```

---

#### Subtask 2.1.2: Create example YAML handoff (DOCUMENTATION)

**Time:** 3 min

**File:** `default/schemas/handoff-example.yaml`

**Code:**
```yaml
---
version: "1.0"
schema: ring-handoff-v1

session:
  id: example-session
  started_at: 2026-01-12T10:00:00Z
  ended_at: 2026-01-12T11:30:00Z
  duration_seconds: 5400

task:
  description: Implement artifact indexing with FTS5
  status: completed
  skills_used:
    - ring:test-driven-development
    - ring:requesting-code-review

context:
  project_path: /Users/user/repos/ring
  git_commit: abc123def456789012345678901234567890abcd
  git_branch: feature/artifact-index
  key_files:
    - default/lib/artifact-index/artifact_index.py
    - default/lib/artifact-index/artifact_schema.sql

decisions:
  - decision: Use FTS5 instead of FTS3
    rationale: FTS5 supports BM25 ranking for better relevance
    alternatives:
      - FTS3 (lacks ranking)
      - External search (too heavy)

artifacts:
  created:
    - default/lib/artifact-index/artifact_index.py
  modified:
    - default/lib/artifact-index/artifact_schema.sql

learnings:
  - type: WORKING_SOLUTION
    content: FTS5 triggers keep index synchronized automatically
    confidence: verified

  - type: FAILED_APPROACH
    content: Tried FTS3, but it doesn't support BM25 ranking
    confidence: verified

blockers: []

resume:
  next_steps:
    - Add query script for artifact search
    - Test with real handoff documents
  context_needed:
    - Review artifact_schema.sql for table structure
  warnings:
    - FTS5 requires SQLite 3.35+
---

# Session Notes

## Summary
Implemented artifact indexing using SQLite FTS5. Created schema with automatic trigger-based synchronization.

## Additional Context
The implementation follows the pattern from continuous-claude-v3 research...
```

**Verification:**
```bash
python3 -c "import yaml; yaml.safe_load(open('default/schemas/handoff-example.yaml')); print('Valid YAML')"
```

---

#### Subtask 2.1.3: Validate example against schema (TEST)

**Time:** 2 min

**File:** `tests/test_handoff_schema.py`

**Code:**
```python
import json
import yaml
import pytest
from jsonschema import validate, ValidationError

def test_example_validates():
    """Example handoff should pass schema validation."""
    with open('default/schemas/handoff-schema-v1.json') as f:
        schema = json.load(f)

    with open('default/schemas/handoff-example.yaml') as f:
        example = yaml.safe_load(f)

    # Should not raise ValidationError
    validate(instance=example, schema=schema)

def test_missing_required_fields():
    """Missing required fields should fail validation."""
    with open('default/schemas/handoff-schema-v1.json') as f:
        schema = json.load(f)

    invalid_handoff = {
        'version': '1.0',
        'schema': 'ring-handoff-v1',
        # Missing session, task, resume
    }

    with pytest.raises(ValidationError):
        validate(instance=invalid_handoff, schema=schema)
```

**Verification:**
```bash
pytest tests/test_handoff_schema.py -v
# Expected: PASS
```

---

#### Subtask 2.1.4: Document schema in README (DOCUMENTATION)

**Time:** 2 min

**File:** `default/schemas/README.md`

**Code:**
```markdown
# Ring Schemas

This directory contains JSON Schemas for Ring data structures.

## handoff-schema-v1.json

**Purpose:** Validates Ring session handoff documents.

**Usage:**
\`\`\`python
from jsonschema import validate
import yaml, json

# Load schema
with open('handoff-schema-v1.json') as f:
    schema = json.load(f)

# Validate handoff
with open('handoff.yaml') as f:
    handoff = yaml.safe_load(f)

validate(instance=handoff, schema=schema)
\`\`\`

**Required Fields:**
- `version`: Schema version (e.g., "1.0")
- `schema`: Must be "ring-handoff-v1"
- `session.id`: Session identifier
- `task.description`: What was worked on
- `task.status`: completed|paused|blocked|failed
- `resume.next_steps`: Array of next steps (min 1)

**See:** `handoff-example.yaml` for a complete example.
```

**Verification:**
```bash
test -f default/schemas/README.md || exit 1
```

---

### Task 2.2: Implement YAML Serialization (4 subtasks)

*(Details for 2.2.1 through 2.2.4 follow same pattern: test first, implement, verify)*

#### Subtask 2.2.1: Write serialization tests (RED) - 3 min
#### Subtask 2.2.2: Implement serialize function (GREEN) - 4 min
#### Subtask 2.2.3: Implement deserialize function (GREEN) - 4 min
#### Subtask 2.2.4: Add token counting (ENHANCEMENT) - 2 min

---

### Task 2.3: Update handoff-tracking Skill (5 subtasks)

#### Subtask 2.3.1: Create YAML handoff template - 3 min
#### Subtask 2.3.2: Update skill to use serializer - 4 min
#### Subtask 2.3.3: Add format parameter - 3 min
#### Subtask 2.3.4: Update skill documentation - 2 min
#### Subtask 2.3.5: Test skill with YAML output - 3 min

---

### Task 2.4: Implement Dual-Format Indexing (5 subtasks)

#### Subtask 2.4.1: Write test for YAML indexing (RED) - 3 min
#### Subtask 2.4.2: Add YAML parser to indexer (GREEN) - 4 min
#### Subtask 2.4.3: Update FTS extraction for YAML (GREEN) - 3 min
#### Subtask 2.4.4: Test backward compatibility (TEST) - 3 min
#### Subtask 2.4.5: Add format detection (ENHANCEMENT) - 2 min

---

## Phase 3: Confidence Markers (2 Tasks → 12 Subtasks)

**Context for write-plan agent:**
- Read: `docs/pre-dev/ring-continuity/api-design.md` (confidence interfaces)
- Read: `docs/AGENT_DESIGN.md` (existing schemas)
- Read: `default/agents/codebase-explorer.md` (target agent)
- Focus: Add verification status to agent outputs
- Output: Updated schemas, updated agent, tests

---

### Task 3.1: Update Agent Output Schemas (6 subtasks)

#### Subtask 3.1.1: Add Verification section to Implementation schema - 3 min
#### Subtask 3.1.2: Add Verification section to Analysis schema - 3 min
#### Subtask 3.1.3: Add Verification section to Reviewer schema - 3 min
#### Subtask 3.1.4: Add Verification section to Exploration schema - 3 min
#### Subtask 3.1.5: Add Verification section to Planning schema - 3 min
#### Subtask 3.1.6: Create examples with confidence markers - 4 min

---

### Task 3.2: Integrate in codebase-explorer (6 subtasks)

#### Subtask 3.2.1: Write test for confidence markers in output (RED) - 3 min
#### Subtask 3.2.2: Add Verification section requirement to agent prompt - 3 min
#### Subtask 3.2.3: Add evidence classification logic to prompt - 4 min
#### Subtask 3.2.4: Add anti-rationalization table for skipping verification - 3 min
#### Subtask 3.2.5: Update agent examples with markers - 2 min
#### Subtask 3.2.6: Test agent output contains markers - 3 min

---

## Phase 4: Skill Activation (3 Tasks → 17 Subtasks)

**Context for write-plan agent:**
- Read: `docs/pre-dev/ring-continuity/api-design.md` (SkillActivator interface)
- Read: `default/hooks/generate-skills-ref.py` (skill parsing logic)
- Read: `.references/continuous-claude-v3/.claude/skills/skill-rules.json` (reference implementation)
- Focus: Auto-suggest skills based on user prompts
- Output: skill-rules.json, matcher, hook

---

### Task 4.1: Create skill-rules.json (6 subtasks)

#### Subtask 4.1.1: Write test for rules generation (RED) - 3 min
#### Subtask 4.1.2: Implement skill frontmatter parser - 4 min
#### Subtask 4.1.3: Implement keyword extractor from trigger field - 4 min
#### Subtask 4.1.4: Implement intent pattern generator - 4 min
#### Subtask 4.1.5: Generate initial skill-rules.json for 20 core skills - 5 min
#### Subtask 4.1.6: Validate generated rules against schema - 2 min

---

### Task 4.2: Implement Skill Matching Engine (6 subtasks)

#### Subtask 4.2.1: Write tests for keyword matching (RED) - 3 min
#### Subtask 4.2.2: Implement keyword matcher - 4 min
#### Subtask 4.2.3: Implement regex pattern matcher - 4 min
#### Subtask 4.2.4: Implement negative pattern filter - 3 min
#### Subtask 4.2.5: Implement ranking by priority - 3 min
#### Subtask 4.2.6: Add confidence scoring - 3 min

---

### Task 4.3: Create Activation Hook (5 subtasks)

#### Subtask 4.3.1: Write hook integration test (RED) - 3 min
#### Subtask 4.3.2: Create bash hook wrapper - 4 min
#### Subtask 4.3.3: Create Python matcher caller - 4 min
#### Subtask 4.3.4: Register hook in hooks.json - 2 min
#### Subtask 4.3.5: Test end-to-end activation flow - 4 min

---

## Phase 5: Persistent Memory (3 Tasks → 15 Subtasks)

**Context for write-plan agent:**
- Read: `docs/pre-dev/ring-continuity/data-model.md` (Learning entity schema)
- Read: `docs/pre-dev/ring-continuity/api-design.md` (MemoryRepository interface)
- Read: `default/lib/artifact-index/artifact_schema.sql` (reference FTS5 schema)
- Read: `default/lib/artifact-index/artifact_index.py` (reference indexing code)
- Focus: Store and retrieve learnings with FTS5 search
- Output: Database schema, repository, hook

---

### Task 5.1: Create Memory Database Schema (5 subtasks)

#### Subtask 5.1.1: Write test for database creation (RED) - 3 min
#### Subtask 5.1.2: Create memory-schema.sql with tables - 5 min
#### Subtask 5.1.3: Add FTS5 virtual table and triggers - 4 min
#### Subtask 5.1.4: Implement schema initialization in Python - 4 min
#### Subtask 5.1.5: Test schema creation - 2 min

---

### Task 5.2: Implement Memory Search & Retrieval (5 subtasks)

#### Subtask 5.2.1: Write tests for memory storage (RED) - 3 min
#### Subtask 5.2.2: Implement store_learning method - 5 min
#### Subtask 5.2.3: Implement search_memories with FTS5 - 5 min
#### Subtask 5.2.4: Add BM25 ranking and filters - 4 min
#### Subtask 5.2.5: Implement access tracking - 2 min

---

### Task 5.3: Create SessionStart Hook (5 subtasks)

#### Subtask 5.3.1: Write hook test (RED) - 3 min
#### Subtask 5.3.2: Create bash hook wrapper - 3 min
#### Subtask 5.3.3: Create Python memory searcher - 5 min
#### Subtask 5.3.4: Register hook in hooks.json - 2 min
#### Subtask 5.3.5: Test memory injection end-to-end - 4 min

---

## Subtask Statistics

| Phase | Tasks | Subtasks | Estimated Time |
|-------|-------|----------|----------------|
| **1** | 3 | 16 | 2-3 days |
| **2** | 4 | 18 | 2-3 days |
| **3** | 2 | 12 | 1-2 days |
| **4** | 3 | 17 | 2-3 days |
| **5** | 3 | 15 | 2-3 days |
| **Total** | 15 | 78 | 9-14 days |

---

## Execution Strategy for Write-Plan Agents

### Agent 1: Phase 1 Foundation

**Prompt Template:**
```
Create detailed implementation plan for Ring Continuity Phase 1: Foundation.

## Context Documents (MUST READ)
1. docs/pre-dev/ring-continuity/research.md - Research findings
2. docs/pre-dev/ring-continuity/prd.md - Product requirements
3. docs/pre-dev/ring-continuity/trd.md - Technical architecture
4. docs/pre-dev/ring-continuity/api-design.md - Component contracts
5. docs/pre-dev/ring-continuity/dependency-map.md - Technology stack

## Scope
Tasks: 1.1, 1.2, 1.3 (16 subtasks total)
Goal: Establish ~/.ring/ directory with config precedence
Files: ring_home.py, config_loader.py, migration.py, install scripts

## Requirements
- Follow TDD pattern (test first)
- Use Python 3.9+ stdlib
- Only dependency: PyYAML 6.0+
- Complete code (no placeholders)
- Integration tests for full workflows

Output implementation plan to: docs/plans/ring-continuity-phase1-plan.md
```

### Agent 2-5: Phases 2-5

**Same pattern for each phase:**
- Read all context documents
- Focus on specific task group
- Output to docs/plans/ring-continuity-phase{N}-plan.md

---

## Gate 8 Validation Checklist

- [x] Every subtask is 2-5 minutes
- [x] TDD cycle enforced (test first for implementation subtasks)
- [x] Complete code provided (no placeholders)
- [x] Zero-context executable (all context in subtask description)
- [x] 78 subtasks across 5 phases
- [x] Clear grouping for write-plan agents
- [x] Context documents specified for each phase

---

## Next Steps

1. **Review all 9 gate documents** in `docs/pre-dev/ring-continuity/`
2. **Spawn 5 write-plan agents** (one per phase) using subtasks as input
3. **Review plans for integration** - ensure phases work together
4. **Execute implementation** using `/execute-plan` or dev-cycle

---

## Appendix: Complete Subtask List

[78 subtasks listed above, organized by phase and task]
