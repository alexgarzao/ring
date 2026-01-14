# Ring Continuity - Dependency Map (Gate 6)

> **Version:** 1.0
> **Date:** 2026-01-12
> **Status:** Draft
> **Based on:** Data Model v1.0 (docs/pre-dev/ring-continuity/data-model.md)

---

## Executive Summary

Ring Continuity uses **Python stdlib** as much as possible to minimize external dependencies. The only required external package is **PyYAML 6.0+** for YAML serialization. All other functionality (SQLite FTS5, JSON Schema validation, file operations) uses Python 3.9+ standard library.

**Total External Dependencies:** 1 (PyYAML)

**Total Optional Dependencies:** 2 (jsonschema for validation, ruamel.yaml for round-trip)

---

## Technology Stack

### Core Runtime

| Technology | Version | Pinned | Rationale | Alternatives Evaluated |
|------------|---------|--------|-----------|----------------------|
| **Python** | 3.9+ | No (minimum) | Stdlib sqlite3 with FTS5, match statements, type hints | Python 3.8 (no match), Python 3.10+ (reduces compatibility) |
| **Bash** | 4.0+ | No (minimum) | Hook scripts, associative arrays | Shell (no arrays), Zsh (not default on Linux) |
| **SQLite** | 3.35+ | No (via Python) | FTS5 support, included in Python stdlib | PostgreSQL (too heavy), Custom file format (reinventing wheel) |

**Version Pinning Strategy:**
- **Minimum versions specified** (>=3.9, >=4.0, >=3.35)
- **No upper bounds** (allow newer versions)
- **Rationale:** Maximum compatibility, users benefit from platform updates

---

### Python Packages

| Package | Version | Required | Purpose | Alternatives Evaluated |
|---------|---------|----------|---------|----------------------|
| **PyYAML** | >=6.0,<7.0 | Yes | YAML parsing and serialization | ruamel.yaml (heavier, more features), pyyaml-include (not needed) |
| **jsonschema** | >=4.0,<5.0 | No | Validate skill-rules.json and handoff schemas | Custom validation (reinventing wheel), JSON Schema (no Python impl) |
| **ruamel.yaml** | >=0.17 | No | Round-trip YAML with comment preservation | PyYAML (loses comments), YAML 1.2 parsers (overkill) |

**Installation:**
```bash
# Required only
pip install 'PyYAML>=6.0,<7.0'

# With optional validation
pip install 'PyYAML>=6.0,<7.0' 'jsonschema>=4.0,<5.0'

# With round-trip support
pip install 'PyYAML>=6.0,<7.0' 'ruamel.yaml>=0.17'
```

**Rationale for PyYAML 6.0+:**
1. **Security:** Safe loading by default (no `yaml.load()` footgun)
2. **Stability:** Mature, 15+ years of development
3. **Size:** Minimal (~100KB), no transitive dependencies
4. **Speed:** Fast C implementation available (LibYAML)
5. **Compatibility:** Works on all platforms

**Alternatives Rejected:**

| Alternative | Why Rejected |
|-------------|--------------|
| **ruamel.yaml as primary** | Heavier (500KB+), comment preservation not needed for most use cases |
| **Custom YAML parser** | Reinventing wheel, security risks |
| **TOML instead of YAML** | Less human-readable for nested data, no stdlib support |
| **JSON instead of YAML** | Lacks comments, less readable for humans |

---

### Bash Dependencies

| Dependency | Version | Required | Purpose | Alternatives |
|------------|---------|----------|---------|--------------|
| **jq** | 1.6+ | No | JSON escaping in hooks | Python fallback, sed fallback |
| **GNU date** | Any | No (macOS has BSD date) | ISO 8601 timestamps | Python datetime fallback |
| **GNU grep** | Any | No | Pattern matching in hooks | Built-in grep OK |

**Fallback Strategy:**
```bash
# JSON escaping
if command -v jq &>/dev/null; then
    escaped=$(echo "$content" | jq -Rs .)
else
    # Fallback to sed
    escaped=$(echo "$content" | sed 's/\\/\\\\/g; s/"/\\"/g')
fi
```

**Rationale:**
- **Prefer stdlib/builtin** where possible
- **Graceful degradation** if optional tools missing
- **No hard dependencies** on non-standard tools

---

## Database Technology

### Selected: SQLite 3.35+

**Version:** 3.35.0 or higher (for FTS5 support)

**Why SQLite:**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| **Zero configuration** | ✓✓✓ | No server setup, just a file |
| **Included in Python** | ✓✓✓ | No separate installation |
| **FTS5 support** | ✓✓✓ | Built-in full-text search |
| **Performance** | ✓✓ | Fast for <100K rows (sufficient) |
| **Portability** | ✓✓✓ | Works everywhere Python works |
| **Size** | ✓✓✓ | Minimal footprint (<1MB for 10K learnings) |

**Alternatives Evaluated:**

| Alternative | Pros | Cons | Verdict |
|-------------|------|------|---------|
| **PostgreSQL** | Better FTS, pgvector for embeddings | Requires server, heavy setup | ✗ Rejected (too heavy) |
| **File-based (JSON/YAML)** | Simple, no DB | No indexing, slow search | ✗ Rejected (performance) |
| **In-memory only** | Fast | No persistence | ✗ Rejected (defeats purpose) |
| **Redis** | Fast, good for caching | Requires server | ✗ Rejected (external service) |
| **TinyDB** | Pure Python | No FTS, slow | ✗ Rejected (no search) |

**Version Pinning:**
```
SQLite: >=3.35.0 (no upper bound)
```

**Feature Requirements:**
- FTS5 virtual tables
- Triggers for automatic index sync
- JSON1 extension for metadata queries
- Window functions for ranking

**Verification Command:**
```bash
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
# Must output: 3.35.0 or higher
```

---

## YAML Processing

### Selected: PyYAML 6.0+

**Version:** >=6.0,<7.0

**Why PyYAML:**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| **Maturity** | ✓✓✓ | 15+ years, stable API |
| **Security** | ✓✓✓ | Safe loading by default in 6.0+ |
| **Performance** | ✓✓✓ | C extension (LibYAML) |
| **Size** | ✓✓✓ | Minimal, no transitive deps |
| **Compatibility** | ✓✓✓ | Python 3.9+ support |
| **Features** | ✓✓ | Full YAML 1.1 support |

**Alternatives Evaluated:**

| Alternative | Pros | Cons | Verdict |
|-------------|------|------|---------|
| **ruamel.yaml** | YAML 1.2, round-trip, comments | Heavier, more complex API | ✗ Use for optional round-trip only |
| **strictyaml** | Type-safe, no tags | Limited features, smaller ecosystem | ✗ Rejected (too restrictive) |
| **pyyaml-include** | Include directives | Niche feature, adds complexity | ✗ Rejected (not needed) |

**Version Pinning:**
```
PyYAML>=6.0,<7.0
```

**Usage:**
```python
import yaml

# Loading (always safe_load)
with open('handoff.yaml') as f:
    data = yaml.safe_load(f)

# Dumping
with open('handoff.yaml', 'w') as f:
    yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
```

**Security Considerations:**
- **Never use `yaml.load()`** (arbitrary code execution)
- **Always use `yaml.safe_load()`** (safe types only)
- **Validate schemas** after loading

---

## Schema Validation

### Selected: jsonschema 4.0+

**Version:** >=4.0,<5.0

**Why jsonschema:**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| **Standard support** | ✓✓✓ | Draft 2020-12 support |
| **Validation features** | ✓✓✓ | Full JSON Schema spec |
| **Error messages** | ✓✓ | Detailed validation errors |
| **Performance** | ✓ | Adequate for <1000 rules |
| **Optional** | ✓✓✓ | Ring works without it |

**Alternatives Evaluated:**

| Alternative | Pros | Cons | Verdict |
|-------------|------|------|---------|
| **Custom validation** | No dependency | Reinventing wheel, bugs | ✗ Rejected (maintenance burden) |
| **Pydantic** | Type hints, great DX | Heavy (15+ deps), overkill | ✗ Rejected (too heavy) |
| **python-jsonschema-objects** | Class generation | Unmaintained | ✗ Rejected (stale) |

**Version Pinning:**
```
jsonschema>=4.0,<5.0
```

**Usage:**
```python
from jsonschema import validate, ValidationError

schema = {
    "type": "object",
    "required": ["session", "task"],
    "properties": {
        "session": {"type": "object"},
        "task": {"type": "object"}
    }
}

try:
    validate(instance=data, schema=schema)
except ValidationError as e:
    print(f"Validation failed: {e.message}")
```

**Graceful Degradation:**
- If jsonschema not installed, skip validation
- Log warning about missing validation
- Rely on YAML parser for basic type checking

---

## Hook System Technologies

### Selected: Bash 4.0+ with Python Helpers

**Bash Version:** >=4.0

**Why Bash for Hooks:**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| **Startup speed** | ✓✓✓ | <10ms for simple hooks |
| **Simplicity** | ✓✓ | Good for file ops, JSON output |
| **Compatibility** | ✓✓✓ | Available on all Unix systems |
| **Integration** | ✓✓✓ | Easy to call Python when needed |

**Bash Features Required:**
- Associative arrays (Bash 4.0+)
- Process substitution
- Command substitution
- Here-documents for JSON

**Python Helper Usage:**
```bash
# For complex operations, delegate to Python
result=$(python3 "${PLUGIN_ROOT}/lib/memory_search.py" "$query")
```

**Alternatives Evaluated:**

| Alternative | Pros | Cons | Verdict |
|-------------|------|------|---------|
| **Pure Python hooks** | Better error handling | Slower startup (~50ms) | ✗ Use Python only when needed |
| **TypeScript hooks** | Type safety, better tooling | Compilation step, Node.js dep | ✗ Rejected (complexity) |
| **Shell (sh)** | Maximum compatibility | No arrays, limited features | ✗ Rejected (too limited) |

---

## File Formats

### Configuration: YAML

**Selected:** YAML 1.1 (PyYAML default)

**Rationale:**
- Human-editable
- Comments supported
- Hierarchical structure
- Python stdlib-compatible (via PyYAML)

**Example:**
```yaml
# ~/.ring/config.yaml
memory:
  enabled: true
  max_memories: 10000
  decay:
    enabled: true
    half_life_days: 180

skill_activation:
  enabled: true
  enforcement_default: suggest

handoffs:
  format: yaml  # yaml or markdown
  auto_index: true
```

---

### Skill Rules: JSON

**Selected:** JSON (not YAML) for skill-rules.json

**Rationale:**
- Schema validation with jsonschema
- Faster parsing than YAML
- No ambiguity (YAML has edge cases)
- Standard for rule engines

**Example:**
```json
{
  "version": "1.0",
  "skills": {
    "ring:test-driven-development": {
      "type": "guardrail",
      "enforcement": "block",
      "priority": "critical",
      "promptTriggers": {
        "keywords": ["tdd", "test driven"],
        "intentPatterns": ["write.*test.*first", "red.*green.*refactor"]
      }
    }
  }
}
```

---

### Handoffs: YAML with Frontmatter

**Selected:** YAML with --- delimiters

**Rationale:**
- Machine-parseable frontmatter
- Human-readable body
- Compatible with existing Markdown frontmatter pattern
- Token-efficient

**Example:**
```yaml
---
version: "1.0"
schema: ring-handoff-v1
session:
  id: context-management
  started_at: 2026-01-12T10:00:00Z
task:
  description: Implement memory system
  status: completed
---

# Session Notes

Additional context in Markdown format...
```

---

## Platform Dependencies

### Operating System

| Platform | Support Level | Notes |
|----------|---------------|-------|
| **macOS** | ✓✓✓ Primary | Darwin kernel, BSD userland |
| **Linux** | ✓✓✓ Primary | GNU userland |
| **Windows (WSL)** | ✓✓ Compatible | Via WSL2 with Linux tools |
| **Windows (native)** | ✗ Not supported | Bash hooks incompatible |

**Platform Detection:**
```bash
case "$(uname -s)" in
    Darwin*)  PLATFORM="macos" ;;
    Linux*)   PLATFORM="linux" ;;
    *)        PLATFORM="unknown" ;;
esac
```

---

### File System Requirements

| Requirement | Purpose | Fallback |
|-------------|---------|----------|
| **Home directory writable** | ~/.ring/ creation | Use .ring/ in project |
| **Symlink support** | Avoid duplication | Copy files if symlinks unsupported |
| **UTF-8 filenames** | Unicode session names | ASCII-safe fallback |
| **POSIX paths** | Cross-platform compatibility | - |

---

## Development Dependencies

### Testing

| Package | Version | Purpose |
|---------|---------|---------|
| **pytest** | >=7.0,<8.0 | Unit and integration tests |
| **pytest-asyncio** | >=0.21 | Async test support (if needed) |
| **coverage** | >=7.0 | Code coverage tracking |

**Why pytest:**
- Industry standard
- Fixture system for test data
- Parametrized tests
- Plugin ecosystem

**Installation:**
```bash
pip install 'pytest>=7.0,<8.0' 'coverage>=7.0'
```

---

### Linting & Formatting

| Tool | Version | Purpose | Config |
|------|---------|---------|--------|
| **shellcheck** | latest | Bash linting | .shellcheckrc |
| **black** | >=24.0 | Python formatting | pyproject.toml |
| **ruff** | >=0.1 | Python linting | pyproject.toml |

**Why These Tools:**
- **shellcheck:** Catches Bash bugs before execution
- **black:** Consistent formatting, zero config
- **ruff:** Fast (Rust-based), replaces flake8/pylint/isort

**Installation:**
```bash
# Homebrew (macOS)
brew install shellcheck

# Python tools
pip install 'black>=24.0' 'ruff>=0.1'
```

---

## Optional Enhancements

### Optional: Round-Trip YAML (ruamel.yaml)

**Use Case:** Preserve comments when updating config files programmatically.

**When Needed:**
- Auto-updating skill-rules.json while keeping user comments
- Config migration with comment preservation

**Installation:**
```bash
pip install 'ruamel.yaml>=0.17'
```

**Usage:**
```python
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False

with open('config.yaml') as f:
    data = yaml.load(f)

# Modify data
data['memory']['enabled'] = True

with open('config.yaml', 'w') as f:
    yaml.dump(data, f)
# Comments preserved!
```

---

### Optional: Schema Validation (jsonschema)

**Use Case:** Validate skill-rules.json and handoff YAML against schemas.

**When Needed:**
- Development: Catch schema errors early
- Production: Validate user-edited configs
- Testing: Ensure test data is valid

**Installation:**
```bash
pip install 'jsonschema>=4.0,<5.0'
```

**Usage:**
```python
from jsonschema import validate, Draft202012Validator

validator = Draft202012Validator(schema)
errors = list(validator.iter_errors(data))
if errors:
    for error in errors:
        print(f"{error.json_path}: {error.message}")
```

**Graceful Degradation:**
- If not installed, skip schema validation
- Basic type checking via YAML parser
- Runtime errors caught during execution

---

## Version Compatibility Matrix

### Python Version Support

| Python Version | Support | Notes |
|----------------|---------|-------|
| **3.9** | ✓✓✓ Minimum | Match statements, type hints |
| **3.10** | ✓✓✓ Recommended | Pattern matching improvements |
| **3.11** | ✓✓✓ Supported | Performance improvements |
| **3.12** | ✓✓✓ Supported | Latest stable |
| **3.8** | ✗ Not supported | No match statements |
| **3.13+** | ✓ Untested | Should work |

---

### SQLite Version Support

| SQLite Version | FTS5 | JSON1 | Window Functions | Verdict |
|----------------|------|-------|------------------|---------|
| **3.35+** | ✓ | ✓ | ✓ | ✓✓✓ Recommended |
| **3.32-3.34** | ✓ | ✓ | ✓ | ✓✓ Compatible (missing some FTS5 features) |
| **3.24-3.31** | ✓ | ✓ | ✗ | ✓ Partial (no window functions) |
| **<3.24** | ✗ | - | - | ✗ Not supported |

**Version Detection:**
```python
import sqlite3
version = tuple(map(int, sqlite3.sqlite_version.split('.')))
if version < (3, 35, 0):
    raise RuntimeError(f"SQLite 3.35+ required, found {sqlite3.sqlite_version}")
```

---

### PyYAML Version Support

| PyYAML Version | Python 3.9 | Python 3.12 | safe_load default | Verdict |
|----------------|------------|-------------|-------------------|---------|
| **6.0+** | ✓ | ✓ | ✓ | ✓✓✓ Recommended |
| **5.4** | ✓ | ✓ | ✗ | ✓ Compatible (manual safe_load) |
| **5.3** | ✓ | ✗ | ✗ | ✗ Not compatible with Python 3.12 |
| **<5.3** | ✗ | ✗ | ✗ | ✗ Not supported |

---

## Installation Strategy

### Installation Methods

| Method | Target User | Command |
|--------|-------------|---------|
| **Install script** | End users | `curl ... \| bash` |
| **Manual pip** | Developers | `pip install -r requirements.txt` |
| **System package** | Enterprise | `apt install ring-plugin` (future) |

---

### Install Script Flow

```bash
#!/usr/bin/env bash
# install-ring-continuity.sh

set -euo pipefail

echo "🔄 Installing Ring Continuity..."

# 1. Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ "${python_version}" < "3.9" ]]; then
    echo "❌ Python 3.9+ required, found ${python_version}"
    exit 1
fi

# 2. Check SQLite version
sqlite_version=$(python3 -c 'import sqlite3; print(sqlite3.sqlite_version)')
if [[ "${sqlite_version}" < "3.35.0" ]]; then
    echo "⚠️  SQLite 3.35+ recommended, found ${sqlite_version}"
    echo "   FTS5 features may be limited"
fi

# 3. Install PyYAML
echo "📦 Installing PyYAML..."
pip3 install --user 'PyYAML>=6.0,<7.0'

# 4. Optional: Install jsonschema
read -p "Install jsonschema for validation? (y/N) " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip3 install --user 'jsonschema>=4.0,<5.0'
fi

# 5. Create ~/.ring/ structure
echo "📁 Creating ~/.ring/ directory..."
mkdir -p ~/.ring/{handoffs,logs,cache,state}

# 6. Initialize databases
echo "💾 Initializing memory database..."
python3 - <<'EOF'
import sqlite3
from pathlib import Path

db_path = Path.home() / '.ring' / 'memory.db'
conn = sqlite3.connect(str(db_path))
# Execute schema creation...
conn.close()
EOF

# 7. Create default config
if [[ ! -f ~/.ring/config.yaml ]]; then
    cat > ~/.ring/config.yaml <<'EOF'
memory:
  enabled: true
  max_memories: 10000

skill_activation:
  enabled: true
  enforcement_default: suggest

handoffs:
  format: yaml
  auto_index: true
EOF
fi

# 8. Create default skill rules
if [[ ! -f ~/.ring/skill-rules.json ]]; then
    echo '{"version": "1.0", "skills": {}}' > ~/.ring/skill-rules.json
fi

echo "✅ Ring Continuity installed successfully!"
echo "   Location: ~/.ring/"
echo "   Config: ~/.ring/config.yaml"
echo "   Memory: ~/.ring/memory.db"
```

---

### Requirements File

**File:** `requirements.txt`

```txt
# Ring Continuity Requirements
# Python 3.9+ required

# Core dependencies (required)
PyYAML>=6.0,<7.0

# Optional dependencies
jsonschema>=4.0,<5.0  # For schema validation
ruamel.yaml>=0.17     # For round-trip YAML with comments

# Development dependencies
pytest>=7.0,<8.0
coverage>=7.0,<8.0
black>=24.0
ruff>=0.1
```

---

## Dependency Justification

### Why Minimize Dependencies?

| Reason | Impact |
|--------|--------|
| **Easier installation** | Users don't need to manage many packages |
| **Fewer conflicts** | Less chance of version conflicts |
| **Faster startup** | Fewer imports = faster hook execution |
| **Better reliability** | Fewer points of failure |
| **Simpler maintenance** | Less to update and test |

### Why PyYAML is Worth It

| Benefit | Value |
|---------|-------|
| **YAML ubiquity** | Industry standard for config |
| **Human-editable** | Users can edit handoffs manually |
| **Structured data** | Better than JSON for readability |
| **Comment support** | Document configs inline |
| **5x token savings** | From ~2000 (Markdown) to ~400 (YAML) |

**Token savings calculation:**
```
Markdown handoff: ~2000 tokens (measured from examples)
YAML handoff: ~400 tokens (estimated from schema)
Savings: 1600 tokens per handoff
Cost: 1 dependency (PyYAML)
ROI: 1600 tokens / 1 dependency = Excellent
```

---

## Build & Distribution

### Build Process

**No build step required** for end users:
- Bash scripts are interpreted
- Python scripts are interpreted
- YAML/JSON configs are data files

**Development build:**
```bash
# Lint Bash hooks
shellcheck default/hooks/*.sh

# Format Python scripts
black default/lib/

# Lint Python scripts
ruff check default/lib/

# Run tests
pytest tests/
```

---

### Distribution Format

**Method:** Git repository + install script

**Structure:**
```
ring/
├── default/
│   ├── hooks/
│   │   ├── session-start.sh
│   │   ├── user-prompt-submit.sh
│   │   └── ...
│   ├── lib/
│   │   ├── memory_repository.py
│   │   ├── handoff_serializer.py
│   │   ├── skill_activator.py
│   │   └── ...
│   └── skills/
│       └── ring:handoff-tracking/
│           └── SKILL.md (updated)
├── install-ring-continuity.sh
└── requirements.txt
```

**No packaging needed:**
- Scripts run in place
- No compilation
- No bundling

---

## Dependency Security

### Security Considerations

| Package | Supply Chain Risk | Mitigation |
|---------|-------------------|------------|
| **PyYAML** | Low (mature, widely used) | Pin major version, use safe_load only |
| **jsonschema** | Low (optional, validation only) | Pin major version, optional install |
| **sqlite3** | None (stdlib) | Use parameterized queries |

### Security Best Practices

1. **Pin major versions** to prevent breaking changes
2. **Use safe APIs** (yaml.safe_load, not yaml.load)
3. **Parameterize queries** (prevent SQL injection)
4. **Validate inputs** before processing
5. **Regular updates** for security patches

---

## Runtime Environment

### Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `CLAUDE_PLUGIN_ROOT` | Yes | - | Plugin directory |
| `CLAUDE_PROJECT_DIR` | Yes | - | Current project |
| `CLAUDE_SESSION_ID` | Yes | - | Session identifier |
| `RING_HOME` | No | `~/.ring` | Override home directory |
| `RING_LOG_LEVEL` | No | `INFO` | Logging verbosity |

**Detection Script:**
```bash
# Detect Ring home directory
if [[ -n "${RING_HOME:-}" ]]; then
    RING_HOME="${RING_HOME}"
elif [[ -d "${HOME}/.ring" ]]; then
    RING_HOME="${HOME}/.ring"
else
    echo "Creating ~/.ring/ directory..."
    mkdir -p "${HOME}/.ring"
    RING_HOME="${HOME}/.ring"
fi
```

---

### System Requirements

| Resource | Minimum | Recommended | Purpose |
|----------|---------|-------------|---------|
| **Disk space** | 10 MB | 100 MB | Memory DB, handoffs, logs |
| **Memory (RAM)** | 50 MB | 200 MB | Python processes, SQLite cache |
| **Python heap** | Default | Default | No large allocations |

---

## Gate 6 Validation Checklist

- [x] All technologies selected with versions pinned
- [x] Rationale provided for each selection (Why this? Why not alternatives?)
- [x] Alternatives evaluated with pros/cons tables
- [x] Version compatibility matrix documented
- [x] Installation strategy defined (install script + requirements.txt)
- [x] Platform support specified (macOS, Linux)
- [x] Build process documented (none for users, lint/test for devs)
- [x] Security considerations addressed
- [x] Tech stack is complete and actionable

---

## Appendix: Dependency Catalog

### Required Dependencies

| Dependency | Version | Type | Installation |
|------------|---------|------|--------------|
| Python | >=3.9 | Runtime | System package manager |
| Bash | >=4.0 | Runtime | Included with OS |
| PyYAML | >=6.0,<7.0 | Library | pip install |
| SQLite | >=3.35 | Runtime | Included with Python |

### Optional Dependencies

| Dependency | Version | Type | Purpose |
|------------|---------|------|---------|
| jsonschema | >=4.0,<5.0 | Library | Schema validation |
| ruamel.yaml | >=0.17 | Library | Round-trip YAML |
| jq | >=1.6 | CLI Tool | JSON processing in hooks |

### Development Dependencies

| Dependency | Version | Type | Purpose |
|------------|---------|------|---------|
| pytest | >=7.0,<8.0 | Library | Testing |
| coverage | >=7.0,<8.0 | Library | Coverage tracking |
| black | >=24.0 | Tool | Code formatting |
| ruff | >=0.1 | Tool | Linting |
| shellcheck | latest | Tool | Bash linting |

---

## Technology Decision Summary

| Decision | Rationale | Risk |
|----------|-----------|------|
| **SQLite over PostgreSQL** | Zero config, included in Python | Limited for very large datasets (>100K memories) |
| **PyYAML over ruamel.yaml** | Lighter, simpler API | No round-trip support (acceptable trade-off) |
| **JSON for rules, YAML for config** | JSON has better schema validation | Slightly less readable |
| **Bash for hooks** | Fast startup, good for simple ops | Complex operations delegate to Python |
| **FTS5 over embeddings** | Sufficient for keyword search, no deps | Weaker semantic search (acceptable for MVP) |
| **Python 3.9 minimum** | Match statements, modern typing | Excludes older systems (acceptable) |
