# Automated Session-Start Hook Design

**Date:** 2025-11-06
**Status:** Approved
**Author:** Ring Team

## Problem Statement

The current `hooks/session-start.sh` script relies on a hardcoded documentation file (`docs/skills-quick-reference.md`) that must be manually maintained. When the docs folder was deleted, the hook began failing. We need dynamic generation of the skills quick reference at session start.

## Design Goals

1. **Zero manual maintenance**: Skills reference auto-generates from skill files
2. **Robust parsing**: Handle YAML frontmatter reliably across all 28 skills
3. **Categorized output**: Group skills logically for easier discovery
4. **Graceful degradation**: Provide useful output even if parsing partially fails
5. **Fast execution**: Session start should remain sub-second

## Architecture

### Component Overview

```
hooks/
├── session-start.sh          # Entry point (bash)
└── generate-skills-ref.py    # Skills scanner (python)

skills/
├── skill-name/
│   └── SKILL.md             # Source of truth
└── using-ring/
    └── SKILL.md             # Mandatory workflow skill
```

### Tool Selection: Python

**Choice:** Python with `pyyaml` library

**Rationale:**
- Pre-installed on macOS and most Linux distributions
- Robust YAML parsing handles frontmatter edge cases
- Rich string processing for markdown formatting
- Better error handling than shell-based parsing
- Easier to test and maintain

**Trade-off:** Requires `pyyaml` pip package (graceful degradation if missing)

## Data Flow

```
1. session-start.sh invokes generate-skills-ref.py
2. Python script:
   a. Scans skills/*/SKILL.md files
   b. Extracts YAML frontmatter (name, description, when_to_use)
   c. Categorizes by directory naming patterns
   d. Generates markdown to stdout
3. Bash script:
   a. Captures Python output
   b. Escapes for JSON
   c. Combines with using-ring skill content
   d. Injects into session context
```

## Categorization Strategy

Skills are grouped using directory name pattern matching:

| Category | Pattern | Count | Examples |
|----------|---------|-------|----------|
| **Pre-Dev Workflow** | `pre-dev-*` | 8 | `pre-dev-prd-creation`, `pre-dev-task-breakdown` |
| **Testing & Debugging** | `test-*`, `*-debugging`, `condition-*`, `defense-*` | 5 | `systematic-debugging`, `test-driven-development` |
| **Collaboration** | `*-review`, `dispatching-*`, `sharing-*` | 5 | `requesting-code-review`, `dispatching-parallel-agents` |
| **Planning & Execution** | `brainstorming`, `writing-plans`, `executing-plans`, `*-worktrees` | 5 | `brainstorming`, `executing-plans` |
| **Meta Skills** | `using-ring`, `writing-skills`, `testing-skills` | 3 | `using-ring`, `writing-skills` |
| **Other** | (uncategorized) | 2 | Any skills not matching above patterns |

**Rationale for pattern-based categorization:**
- No need to add category metadata to frontmatter (avoid migration)
- Naming convention already implies grouping
- Easy to extend with new patterns

## Output Format

### Skills Quick Reference Structure

```markdown
# Ring Skills Quick Reference

## Pre-Dev Workflow (8 skills)
- **skill-name**: Description from frontmatter...

## Testing & Debugging (5 skills)
- **skill-name**: Description from frontmatter...

[... other categories ...]

## Usage
To use a skill: Use the Skill tool with skill name
Example: ring:brainstorming
```

### Session Context Injection

The final context structure:
```xml
<ring-skills-system>
[Generated Skills Quick Reference]

---

**MANDATORY WORKFLOWS:**

[Content from skills/using-ring/SKILL.md]
</ring-skills-system>
```

## Error Handling

### Python Script Errors

| Error Type | Handling Strategy |
|------------|-------------------|
| Missing `pyyaml` | Print warning, attempt basic regex parsing fallback |
| Invalid frontmatter | Skip skill, log warning, continue processing others |
| Missing SKILL.md | Skip directory, continue processing |
| File read error | Skip file, log error, continue processing |
| Zero skills found | Print error message with diagnostic info |

### Bash Script Errors

| Error Type | Handling Strategy |
|------------|-------------------|
| Python script fails | Fall back to minimal context (using-ring only) |
| JSON escaping fails | Return error context with diagnostic message |
| Plugin root not found | Exit with error (cannot proceed) |

## Implementation Plan

### Phase 1: Python Script (generate-skills-ref.py)
1. Import dependencies (`os`, `yaml`, `pathlib`)
2. Implement frontmatter parser
3. Implement category matcher
4. Implement markdown formatter
5. Add error handling and logging
6. Test with all 28 skills

### Phase 2: Bash Script Update (session-start.sh)
1. Call Python script with proper path handling
2. Capture output with error checking
3. Fall back to minimal context on failure
4. Test JSON escaping edge cases

### Phase 3: Validation
1. Test session start with all skills present
2. Test with missing skills
3. Test with malformed frontmatter
4. Test without pyyaml installed
5. Verify session context injection works

## Testing Strategy

### Unit Tests (Python)
```python
# Test frontmatter extraction
def test_parse_frontmatter_valid()
def test_parse_frontmatter_invalid()
def test_parse_frontmatter_missing()

# Test categorization
def test_categorize_pre_dev_skills()
def test_categorize_testing_skills()
def test_categorize_uncategorized()

# Test markdown generation
def test_generate_markdown_output()
def test_generate_markdown_empty()
```

### Integration Tests (Bash)
```bash
# Test end-to-end hook execution
./hooks/session-start.sh | jq .

# Test with skills directory
PLUGIN_ROOT=. ./hooks/session-start.sh

# Test error conditions
rm skills/*/SKILL.md # temporary
./hooks/session-start.sh # should gracefully degrade
```

## Performance Considerations

**Expected timing:**
- Scan 28 skill files: ~10ms
- Parse YAML frontmatter: ~20ms
- Generate markdown: ~5ms
- Bash JSON escaping: ~10ms
- **Total: ~45ms** (well under 1 second)

**Optimization opportunities if needed:**
- Cache generated reference (invalidate on git hook)
- Parallel file reading (overkill for 28 files)
- Compiled YAML parser (marginal benefit)

## Security Considerations

- **No user input**: Script only reads from known skill files
- **No code execution**: YAML parsing only extracts data
- **Path traversal**: Use absolute paths, validate plugin root
- **JSON injection**: Proper escaping prevents context injection attacks

## Maintenance

### Adding New Skills
1. Create `skills/new-skill/SKILL.md` with proper frontmatter
2. Hook automatically detects and includes it
3. No manual documentation updates needed

### Modifying Categories
Edit the category patterns in `generate-skills-ref.py`:
```python
CATEGORIES = {
    'Pre-Dev Workflow': ['pre-dev-*'],
    # ... update patterns as needed
}
```

### Debugging
```bash
# Test Python script directly
./hooks/generate-skills-ref.py

# Test with verbose output
VERBOSE=1 ./hooks/session-start.sh
```

## Alternatives Considered

### 1. Pure Bash Parsing
**Pros:** No external dependencies
**Cons:** Fragile YAML parsing, hard to maintain
**Decision:** Rejected for maintainability concerns

### 2. Pre-Generated Cache (Git Hook)
**Pros:** Fastest at session start
**Cons:** Cache staleness, hook chaining complexity
**Decision:** Rejected for added complexity

### 3. yq YAML Parser
**Pros:** Purpose-built for YAML
**Cons:** Not pre-installed, additional setup friction
**Decision:** Rejected; Python more universally available

## Success Metrics

- ✅ Hook executes successfully on all platforms (macOS, Linux)
- ✅ All 28 skills appear in generated reference
- ✅ Skills correctly categorized
- ✅ Execution completes in < 100ms
- ✅ Graceful degradation when pyyaml missing
- ✅ Zero manual maintenance required for new skills

## Future Enhancements

1. **Rich metadata**: Add `category`, `tags`, `difficulty` to frontmatter
2. **Interactive selection**: CLI tool to browse/filter skills
3. **Usage analytics**: Track which skills are used most often
4. **Validation**: Lint skill frontmatter for completeness
5. **Web dashboard**: Visual skill browser for documentation site
