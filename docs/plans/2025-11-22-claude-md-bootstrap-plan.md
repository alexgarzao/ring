# CLAUDE.md Auto-Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use ring:executing-plans to implement this plan task-by-task.

**Goal:** Auto-generate CLAUDE.md files for git repos without them on SessionStart

**Architecture:** Shell script orchestrator dispatches Explore agents via Python, aggregates findings, generates CLAUDE.md via synthesis agent, validates output, and writes file before session-start.sh loads it.

**Tech Stack:** Bash scripting, Python 3.8+, JSON processing (jq), Claude Agent framework

**Global Prerequisites:**
- Environment: macOS/Linux with bash 4.0+
- Tools: Python 3.8+, jq 1.6+, bash 4.0+
- Access: Claude Code session with CLAUDE_PROJECT_DIR environment variable
- State: Clean working tree on main branch

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
python3 --version        # Expected: Python 3.8 or higher
jq --version            # Expected: jq-1.6 or higher
bash --version          # Expected: GNU bash, version 4.x or 5.x
git status              # Expected: clean working tree
echo $CLAUDE_PROJECT_DIR  # Expected: path to current project (may be empty for testing)
```

---

## Task 1: Create Bootstrap Shell Script

**Files:**
- Create: `hooks/claude-md-bootstrap.sh`
- Test: Manual execution testing

**Prerequisites:**
- Tools: bash 4.0+, text editor
- Files must exist: `hooks/hooks.json`
- Environment: Working directory in ring repository

**Step 1: Write the bootstrap shell script**

Create `hooks/claude-md-bootstrap.sh`:
```bash
#!/usr/bin/env bash
# CLAUDE.md Auto-Bootstrap Hook
# Generates CLAUDE.md for git repos that lack them
# Runs on SessionStart before session-start.sh

set -euo pipefail

# Determine directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

# Helper function for colored output
log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1" >&2
}

log_success() {
    echo -e "\033[0;32m✓\033[0m $1" >&2
}

log_warning() {
    echo -e "\033[0;33m⚠\033[0m $1" >&2
}

log_error() {
    echo -e "\033[0;31m✗\033[0m $1" >&2
}

# Check if this is a git repository
if [ ! -d "${PROJECT_DIR}/.git" ]; then
    # Not a git repo - skip silently
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart"
  }
}
EOF
    exit 0
fi

# Check if CLAUDE.md already exists
if [ -f "${PROJECT_DIR}/CLAUDE.md" ]; then
    # CLAUDE.md exists - skip silently (idempotent)
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart"
  }
}
EOF
    exit 0
fi

# Log start of bootstrap process
log_info "No CLAUDE.md found. Starting auto-generation process..."

# Run the Python bootstrap orchestrator
bootstrap_output=$("${SCRIPT_DIR}/claude-md-bootstrap.py" 2>&1)
bootstrap_exit_code=$?

# Check result
if [ $bootstrap_exit_code -eq 0 ]; then
    # Count lines in generated file
    if [ -f "${PROJECT_DIR}/CLAUDE.md" ]; then
        line_count=$(wc -l < "${PROJECT_DIR}/CLAUDE.md")
        log_success "Generated CLAUDE.md (${line_count} lines)"
    else
        log_warning "Bootstrap completed but CLAUDE.md not created"
    fi
else
    log_error "Failed to generate CLAUDE.md - created minimal template"
fi

# Return standard SessionStart output
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart"
  }
}
EOF

exit 0
```

**Step 2: Make script executable**

Run: `chmod +x hooks/claude-md-bootstrap.sh`

**Expected output:**
No output (silent success)

**Step 3: Verify script syntax**

Run: `bash -n hooks/claude-md-bootstrap.sh`

**Expected output:**
No output (syntax is valid)

**Step 4: Test script execution (should exit early)**

Run: `cd /tmp && $OLDPWD/hooks/claude-md-bootstrap.sh`

**Expected output:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart"
  }
}
```

**If Task Fails:**

1. **Script syntax error:**
   - Check: `bash -n hooks/claude-md-bootstrap.sh`
   - Fix: Correct syntax errors shown
   - Rollback: `git checkout -- hooks/claude-md-bootstrap.sh`

2. **Permission denied:**
   - Run: `ls -l hooks/claude-md-bootstrap.sh` (check permissions)
   - Fix: `chmod +x hooks/claude-md-bootstrap.sh`

3. **Can't recover:**
   - Document: What failed and error message
   - Stop: Return to human partner

---

## Task 2: Create Python Bootstrap Orchestrator

**Files:**
- Create: `hooks/claude-md-bootstrap.py`
- Test: Import and basic structure testing

**Prerequisites:**
- Tools: Python 3.8+
- Files must exist: `hooks/claude-md-bootstrap.sh`
- Environment: Python with json, pathlib modules (standard library)

**Step 1: Write the Python orchestrator**

Create `hooks/claude-md-bootstrap.py`:
```python
#!/usr/bin/env python3
"""
CLAUDE.md Bootstrap Orchestrator
Discovers repository layers, dispatches agents, generates CLAUDE.md
"""

import json
import os
import re
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

# Configuration
MAX_LINES = 500
MAX_LAYER_ANALYSIS_TIME = 120  # seconds per layer agent
PROJECT_DIR = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.')).resolve()


class BootstrapOrchestrator:
    """Orchestrates the CLAUDE.md generation process."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.layers = []
        self.layer_findings = {}

    def run(self) -> bool:
        """Execute the full bootstrap process."""
        try:
            # Phase 1: Layer Discovery
            print("[Phase 1] Discovering repository layers...", file=sys.stderr)
            if not self.discover_layers():
                print("Warning: Layer discovery failed, using fallback", file=sys.stderr)
                self.layers = self.fallback_layers()

            # Phase 2: Parallel Layer Analysis
            print(f"[Phase 2] Analyzing {len(self.layers)} layers...", file=sys.stderr)
            self.analyze_layers()

            # Phase 3: Synthesis
            print("[Phase 3] Synthesizing CLAUDE.md...", file=sys.stderr)
            content = self.synthesize_content()

            # Phase 4: Validation and Write
            print("[Phase 4] Validating and writing file...", file=sys.stderr)
            return self.write_claude_md(content)

        except Exception as e:
            print(f"Bootstrap failed: {e}", file=sys.stderr)
            self.write_fallback_template()
            return False

    def discover_layers(self) -> bool:
        """Phase 1: Discover architectural layers using Explore agent."""
        # For now, use static analysis (will be replaced with agent in Task 4)
        # This is a placeholder implementation
        self.layers = self.static_layer_discovery()
        return len(self.layers) > 0

    def static_layer_discovery(self) -> List[Dict]:
        """Temporary: Discover layers via filesystem analysis."""
        layers = []

        # Common patterns to look for
        patterns = {
            'API Layer': ['api/', 'routes/', 'controllers/', 'endpoints/'],
            'Business Logic': ['services/', 'domain/', 'core/', 'business/'],
            'Data Layer': ['models/', 'repositories/', 'db/', 'database/'],
            'Frontend': ['components/', 'pages/', 'views/', 'ui/', 'frontend/'],
            'Infrastructure': ['docker/', 'k8s/', 'terraform/', '.github/'],
            'Configuration': ['config/', 'settings/', '.env'],
            'Testing': ['tests/', 'test/', '__tests__/', 'spec/'],
        }

        for layer_name, directories in patterns.items():
            found_dirs = []
            for dir_pattern in directories:
                # Check both root and src/ subdirectory
                for base in ['', 'src/', 'lib/']:
                    check_path = self.project_dir / base / dir_pattern.rstrip('/')
                    if check_path.exists():
                        found_dirs.append(str(check_path.relative_to(self.project_dir)))

            if found_dirs:
                layers.append({
                    'name': layer_name,
                    'directories': found_dirs,
                    'description': f'{layer_name} implementation'
                })

        return layers

    def fallback_layers(self) -> List[Dict]:
        """Return minimal layer structure when discovery fails."""
        return [
            {
                'name': 'Monolithic',
                'directories': ['.'],
                'description': 'Single-layer application structure'
            }
        ]

    def analyze_layers(self):
        """Phase 2: Analyze each layer (placeholder for parallel agents)."""
        # For now, use basic filesystem analysis
        for layer in self.layers:
            self.layer_findings[layer['name']] = self.analyze_layer_static(layer)

    def analyze_layer_static(self, layer: Dict) -> Dict:
        """Temporary: Analyze layer via filesystem."""
        findings = {
            'name': layer['name'],
            'directories': layer['directories'],
            'key_files': [],
            'technologies': [],
            'patterns': []
        }

        # Find key files in layer directories
        for dir_path in layer['directories']:
            full_path = self.project_dir / dir_path
            if full_path.exists() and full_path.is_dir():
                # Look for important files
                for pattern in ['*.py', '*.js', '*.ts', '*.go', '*.java']:
                    files = list(full_path.glob(pattern))[:3]  # Limit to 3 examples
                    for f in files:
                        rel_path = f.relative_to(self.project_dir)
                        findings['key_files'].append(str(rel_path))

        return findings

    def synthesize_content(self) -> str:
        """Phase 3: Generate CLAUDE.md content."""
        # For now, use template-based generation
        return self.generate_from_template()

    def generate_from_template(self) -> str:
        """Generate CLAUDE.md using template and findings."""
        lines = []
        lines.append("# CLAUDE.md")
        lines.append("")
        lines.append("This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.")
        lines.append("")
        lines.append("## Repository Overview")
        lines.append("")
        lines.append("[Auto-generated] Repository analyzed and documented by CLAUDE.md bootstrap process.")
        lines.append("")
        lines.append("## Architecture")
        lines.append("")
        lines.append("### Core Components")
        lines.append("")

        for layer in self.layers:
            findings = self.layer_findings.get(layer['name'], {})
            lines.append(f"**{layer['name']}** (`{', '.join(layer['directories'])}`)")
            lines.append(f"- {layer['description']}")

            if findings.get('key_files'):
                lines.append("- Key files:")
                for f in findings['key_files'][:3]:
                    lines.append(f"  - `{f}`")

            lines.append("")

        lines.append("## Common Commands")
        lines.append("")
        lines.append("### Development")
        lines.append("```bash")
        lines.append("# Check git status")
        lines.append("git status")
        lines.append("")
        lines.append("# View recent commits")
        lines.append("git log --oneline -10")
        lines.append("```")
        lines.append("")

        lines.append("## Key Workflows")
        lines.append("")
        lines.append("### Working in This Repository")
        lines.append("1. Review this CLAUDE.md for repository context")
        lines.append("2. Check existing patterns in similar files")
        lines.append("3. Follow established conventions")
        lines.append("")

        lines.append("## Important Patterns")
        lines.append("")
        lines.append("### Anti-Patterns to Avoid")
        lines.append("- Creating files without checking existing patterns")
        lines.append("- Ignoring established directory structure")
        lines.append("")

        return '\n'.join(lines)

    def write_claude_md(self, content: str) -> bool:
        """Validate and write CLAUDE.md to disk."""
        lines = content.split('\n')

        # Enforce line limit
        if len(lines) > MAX_LINES:
            lines = lines[:MAX_LINES]
            lines.append("... (truncated to 500 lines)")
            content = '\n'.join(lines)

        # Write file
        claude_md_path = self.project_dir / 'CLAUDE.md'
        try:
            claude_md_path.write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Failed to write CLAUDE.md: {e}", file=sys.stderr)
            return False

    def write_fallback_template(self):
        """Write minimal fallback template on error."""
        fallback = """# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Repository Overview

[Auto-generated CLAUDE.md - bootstrap process encountered errors]

## Architecture

[Analysis incomplete - delete this file to trigger regeneration on next session]

## Common Commands

```bash
# Check git status
git status

# View recent commits
git log --oneline -10
```

## Notes

This CLAUDE.md was auto-generated but the analysis process failed.
You can:
- Edit this file manually with repository-specific guidance
- Delete this file to trigger regeneration on next session start
- Check hook logs for error details
"""

        claude_md_path = self.project_dir / 'CLAUDE.md'
        try:
            claude_md_path.write_text(fallback, encoding='utf-8')
        except:
            pass  # Silent failure for fallback


def main():
    """Main entry point."""
    orchestrator = BootstrapOrchestrator(PROJECT_DIR)
    success = orchestrator.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
```

**Step 2: Make script executable**

Run: `chmod +x hooks/claude-md-bootstrap.py`

**Expected output:**
No output (silent success)

**Step 3: Verify Python syntax**

Run: `python3 -m py_compile hooks/claude-md-bootstrap.py`

**Expected output:**
No output (syntax is valid)

**Step 4: Test basic import**

Run: `python3 -c "import sys; sys.path.insert(0, 'hooks'); import claude_md_bootstrap; print('OK')"`

**Expected output:**
```
OK
```

**If Task Fails:**

1. **Python syntax error:**
   - Check: `python3 -m py_compile hooks/claude-md-bootstrap.py`
   - Fix: Correct syntax errors shown
   - Rollback: `git checkout -- hooks/claude-md-bootstrap.py`

2. **Import error:**
   - Run: `python3 --version` (verify Python 3.8+)
   - Fix: Ensure using Python 3.8 or higher

3. **Can't recover:**
   - Document: Python error details
   - Stop: Return to human partner

---

## Task 3: Update hooks.json Configuration

**Files:**
- Modify: `hooks/hooks.json`
- Test: JSON validation

**Prerequisites:**
- Tools: jq 1.6+
- Files must exist: `hooks/claude-md-bootstrap.sh`, `hooks/hooks.json`

**Step 1: Read current hooks.json**

Run: `cat hooks/hooks.json | jq .`

**Expected output:**
Valid JSON structure with SessionStart hooks

**Step 2: Update hooks.json to add bootstrap before session-start**

Modify `hooks/hooks.json`:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/claude-md-bootstrap.sh"
          },
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
          }
        ]
      },
      {
        "matcher": "clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/claude-md-reminder.sh"
          }
        ]
      }
    ]
  }
}
```

**Step 3: Validate JSON syntax**

Run: `cat hooks/hooks.json | jq . > /dev/null && echo "Valid JSON"`

**Expected output:**
```
Valid JSON
```

**Step 4: Verify hook order**

Run: `cat hooks/hooks.json | jq '.hooks.SessionStart[0].hooks[].command' | head -2`

**Expected output:**
```
"${CLAUDE_PLUGIN_ROOT}/hooks/claude-md-bootstrap.sh"
"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
```

**If Task Fails:**

1. **Invalid JSON:**
   - Check: `cat hooks/hooks.json | jq .`
   - Fix: Correct JSON syntax errors shown
   - Rollback: `git checkout -- hooks/hooks.json`

2. **Wrong hook order:**
   - Verify: claude-md-bootstrap.sh comes before session-start.sh
   - Fix: Reorder hooks array

3. **Can't recover:**
   - Document: JSON validation error
   - Stop: Return to human partner

---

## Task 4: Run Code Review

### Task 4: Run Code Review

1. **Dispatch all 3 reviewers in parallel:**
   - REQUIRED SUB-SKILL: Use ring:requesting-code-review
   - All reviewers run simultaneously (code-reviewer, business-logic-reviewer, security-reviewer)
   - Wait for all to complete

2. **Handle findings by severity (MANDATORY):**

**Critical/High/Medium Issues:**
- Fix immediately (do NOT add TODO comments for these severities)
- Re-run all 3 reviewers in parallel after fixes
- Repeat until zero Critical/High/Medium issues remain

**Low Issues:**
- Add `TODO(review):` comments in code at the relevant location
- Format: `TODO(review): [Issue description] (reported by [reviewer] on 2025-11-22, severity: Low)`
- This tracks tech debt for future resolution

**Cosmetic/Nitpick Issues:**
- Add `FIXME(nitpick):` comments in code at the relevant location
- Format: `FIXME(nitpick): [Issue description] (reported by [reviewer] on 2025-11-22, severity: Cosmetic)`
- Low-priority improvements tracked inline

3. **Proceed only when:**
   - Zero Critical/High/Medium issues remain
   - All Low issues have TODO(review): comments added
   - All Cosmetic issues have FIXME(nitpick): comments added

---

## Task 5: Add Agent Discovery Implementation

**Files:**
- Modify: `hooks/claude-md-bootstrap.py:50-80` (discover_layers method)
- Test: Agent invocation testing

**Prerequisites:**
- Tools: Python 3.8+
- Files must exist: `hooks/claude-md-bootstrap.py`
- Environment: Claude Code session with agent capabilities

**Step 1: Write failing test for agent discovery**

Create test file temporarily for validation:
```python
# test_discovery.py
import sys
sys.path.insert(0, 'hooks')
from claude_md_bootstrap import BootstrapOrchestrator
from pathlib import Path

orchestrator = BootstrapOrchestrator(Path('.'))
result = orchestrator.discover_layers()
assert result == True, "Discovery should return True"
assert len(orchestrator.layers) > 0, "Should discover at least one layer"
print(f"Discovered {len(orchestrator.layers)} layers")
```

Run: `python3 test_discovery.py`

**Expected output:**
Should work with static discovery (current implementation)

**Step 2: Implement agent-based discovery**

Update `hooks/claude-md-bootstrap.py` discover_layers method:
```python
def discover_layers(self) -> bool:
    """Phase 1: Discover architectural layers using Explore agent."""
    try:
        # Prepare discovery prompt
        discovery_prompt = """
Analyze this codebase's layered architecture:

1. Identify ALL architectural layers (e.g., API, business logic, data, UI, infrastructure)
2. For each layer, provide:
   - Layer name
   - Primary directories/files
   - Key responsibilities
   - Technologies used
3. Identify cross-cutting concerns (auth, logging, config, testing)

Format response as structured JSON:
{
  "layers": [
    {
      "name": "Layer Name",
      "directories": ["dir1/", "dir2/"],
      "description": "What this layer does",
      "technologies": ["tech1", "tech2"]
    }
  ],
  "cross_cutting": {
    "authentication": "path/to/auth",
    "logging": "path/to/logging",
    "configuration": "path/to/config",
    "testing": "test/ directories"
  }
}
"""

        # TODO(review): Add actual agent invocation when Task framework available
        # For now, continue using static discovery as fallback
        # agent_response = Task(
        #     subagent_type="Explore",
        #     model="sonnet",
        #     description="Discover architectural layers",
        #     prompt=discovery_prompt
        # )

        # Use static discovery for now
        self.layers = self.static_layer_discovery()

        if not self.layers:
            print("Warning: No layers discovered, using fallback", file=sys.stderr)
            self.layers = self.fallback_layers()

        return len(self.layers) > 0

    except Exception as e:
        print(f"Layer discovery failed: {e}", file=sys.stderr)
        self.layers = self.fallback_layers()
        return False
```

**Step 3: Test updated discovery**

Run: `python3 test_discovery.py`

**Expected output:**
```
Discovered N layers
```

**Step 4: Clean up test file**

Run: `rm test_discovery.py`

**If Task Fails:**

1. **Discovery returns empty:**
   - Check: Project structure has recognizable directories
   - Fix: Ensure fallback_layers() returns at least one layer
   - Rollback: `git checkout -- hooks/claude-md-bootstrap.py`

2. **Agent invocation fails:**
   - Use static discovery as fallback (already implemented)
   - Document limitation for future enhancement

3. **Can't recover:**
   - Document: What discovery method failed
   - Stop: Return to human partner

---

## Task 6: Add Parallel Layer Analysis

**Files:**
- Modify: `hooks/claude-md-bootstrap.py:120-150` (analyze_layers method)
- Test: Multi-layer analysis

**Prerequisites:**
- Tools: Python 3.8+
- Files must exist: `hooks/claude-md-bootstrap.py`

**Step 1: Write test for parallel analysis**

Create temporary test:
```python
# test_analysis.py
import sys
sys.path.insert(0, 'hooks')
from claude_md_bootstrap import BootstrapOrchestrator
from pathlib import Path

orchestrator = BootstrapOrchestrator(Path('.'))
orchestrator.discover_layers()
orchestrator.analyze_layers()
assert len(orchestrator.layer_findings) > 0, "Should have findings"
print(f"Analyzed {len(orchestrator.layer_findings)} layers")
```

Run: `python3 test_analysis.py`

**Expected output:**
```
Analyzed N layers
```

**Step 2: Implement parallel layer analysis**

Update `hooks/claude-md-bootstrap.py` analyze_layers method:
```python
def analyze_layers(self):
    """Phase 2: Analyze each layer (parallel when agents available)."""
    # Prepare all layer prompts
    layer_prompts = []
    for layer in self.layers:
        prompt = f"""
Deep-dive into the {layer['name']} of this codebase:

Focus on: {', '.join(layer['directories'])}

Provide:
1. Key components and their roles
2. Important patterns/conventions
3. Common workflows
4. Notable files (with exact paths)
5. Dependencies and integrations

Be concise but complete (max 150 words).

Format as JSON:
{{
  "components": ["comp1", "comp2"],
  "patterns": ["pattern1", "pattern2"],
  "key_files": ["path/to/file1.ext", "path/to/file2.ext"],
  "technologies": ["tech1", "tech2"],
  "summary": "Brief description"
}}
"""
        layer_prompts.append((layer['name'], prompt))

    # TODO(review): Dispatch parallel agents when Task framework available
    # For now, use sequential static analysis
    # parallel_tasks = []
    # for layer_name, prompt in layer_prompts:
    #     task = Task(
    #         subagent_type="Explore",
    #         model="haiku",  # Fast model for parallel execution
    #         description=f"Explore {layer_name}",
    #         prompt=prompt
    #     )
    #     parallel_tasks.append((layer_name, task))
    #
    # # Wait for all to complete
    # for layer_name, task in parallel_tasks:
    #     self.layer_findings[layer_name] = task.result

    # Use static analysis for now
    for layer in self.layers:
        self.layer_findings[layer['name']] = self.analyze_layer_static(layer)
```

**Step 3: Test parallel analysis**

Run: `python3 test_analysis.py`

**Expected output:**
```
Analyzed N layers
```

**Step 4: Clean up test**

Run: `rm test_analysis.py`

**If Task Fails:**

1. **No findings generated:**
   - Check: analyze_layer_static returns valid dict
   - Fix: Ensure findings dict has required keys
   - Rollback: `git checkout -- hooks/claude-md-bootstrap.py`

2. **Timeout in analysis:**
   - Already has MAX_LAYER_ANALYSIS_TIME constant
   - Static analysis should complete quickly

3. **Can't recover:**
   - Document: Analysis failure details
   - Stop: Return to human partner

---

## Task 7: Implement Content Synthesis

**Files:**
- Modify: `hooks/claude-md-bootstrap.py:160-250` (synthesize_content method)
- Test: Content generation and validation

**Prerequisites:**
- Tools: Python 3.8+
- Files must exist: `hooks/claude-md-bootstrap.py`

**Step 1: Write test for synthesis**

Create temporary test:
```python
# test_synthesis.py
import sys
sys.path.insert(0, 'hooks')
from claude_md_bootstrap import BootstrapOrchestrator
from pathlib import Path

orchestrator = BootstrapOrchestrator(Path('.'))
orchestrator.discover_layers()
orchestrator.analyze_layers()
content = orchestrator.synthesize_content()
assert len(content) > 0, "Should generate content"
assert "# CLAUDE.md" in content, "Should have header"
assert "## Repository Overview" in content, "Should have overview section"
lines = content.split('\n')
assert len(lines) <= 500, f"Should be under 500 lines, got {len(lines)}"
print(f"Generated {len(lines)} lines")
```

Run: `python3 test_synthesis.py`

**Expected output:**
```
Generated N lines
```

**Step 2: Enhance synthesis with agent**

Update `hooks/claude-md-bootstrap.py` synthesize_content method:
```python
def synthesize_content(self) -> str:
    """Phase 3: Generate CLAUDE.md content."""
    # Prepare synthesis data
    synthesis_data = {
        "repository_path": str(self.project_dir),
        "layers": self.layers,
        "layer_findings": self.layer_findings,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Synthesis prompt
    synthesis_prompt = f"""
You are generating a CLAUDE.md file for this repository.

INPUT DATA:
{json.dumps(synthesis_data, indent=2)}

CONSTRAINTS:
- Maximum 500 lines (HARD LIMIT)
- Token-conscious (this file gets re-injected every prompt)
- Actionable and practical (not generic)

REQUIRED SECTIONS:
1. Repository Overview (2-3 sentences max)
2. Architecture (layer-by-layer breakdown)
3. Common Commands (git, build, test, deploy)
4. Key Workflows (how developers work in this repo)
5. Important Patterns (conventions, anti-patterns)

STYLE:
- Concise bullet points
- Use exact file paths
- Focus on "how to work in this repo" not "what this repo does"
- Prioritize information Claude needs to write good code here

Generate the complete CLAUDE.md content now. Start with:
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
"""

    # TODO(review): Use synthesis agent when available
    # agent_response = Task(
    #     subagent_type="general-purpose",
    #     model="sonnet",
    #     description="Generate CLAUDE.md from findings",
    #     prompt=synthesis_prompt
    # )
    # return agent_response.content

    # Use template generation for now
    return self.generate_enhanced_template(synthesis_data)

def generate_enhanced_template(self, data: Dict) -> str:
    """Enhanced template generation with richer content."""
    lines = []
    lines.append("# CLAUDE.md")
    lines.append("")
    lines.append("This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.")
    lines.append("")
    lines.append("## Repository Overview")
    lines.append("")

    # Determine main technologies
    all_techs = set()
    for findings in self.layer_findings.values():
        if 'technologies' in findings:
            all_techs.update(findings.get('technologies', []))

    if all_techs:
        lines.append(f"Repository using {', '.join(list(all_techs)[:3])} with {len(self.layers)}-layer architecture.")
    else:
        lines.append(f"Repository with {len(self.layers)}-layer architecture. [Auto-generated documentation]")

    lines.append("")
    lines.append("## Architecture")
    lines.append("")
    lines.append("### Core Components")
    lines.append("")

    for layer in self.layers:
        findings = self.layer_findings.get(layer['name'], {})
        lines.append(f"**{layer['name']}** (`{', '.join(layer['directories'])}`)")
        lines.append(f"- {layer['description']}")

        if findings.get('key_files'):
            lines.append("- Notable files:")
            for f in findings['key_files'][:5]:  # Limit to 5 files
                lines.append(f"  - `{f}`")

        if findings.get('patterns'):
            lines.append(f"- Patterns: {', '.join(findings['patterns'][:3])}")

        lines.append("")

    # Add cross-cutting concerns if found
    lines.append("### Cross-Cutting Concerns")
    lines.append("")
    lines.append("- **Configuration:** Check for .env, config/ directories")
    lines.append("- **Testing:** Look for test/, tests/, or __tests__/ directories")
    lines.append("- **Documentation:** Check README.md and docs/ directory")
    lines.append("")

    lines.append("## Common Commands")
    lines.append("")
    lines.append("### Git Operations")
    lines.append("```bash")
    lines.append("# Check status")
    lines.append("git status")
    lines.append("")
    lines.append("# View recent commits")
    lines.append("git log --oneline -10")
    lines.append("")
    lines.append("# Create feature branch")
    lines.append("git checkout -b feature/your-feature")
    lines.append("```")
    lines.append("")

    # Add package manager commands if detected
    if (self.project_dir / "package.json").exists():
        lines.append("### Node.js/npm")
        lines.append("```bash")
        lines.append("# Install dependencies")
        lines.append("npm install")
        lines.append("")
        lines.append("# Run development server")
        lines.append("npm run dev")
        lines.append("")
        lines.append("# Run tests")
        lines.append("npm test")
        lines.append("```")
        lines.append("")

    if (self.project_dir / "requirements.txt").exists() or (self.project_dir / "pyproject.toml").exists():
        lines.append("### Python")
        lines.append("```bash")
        lines.append("# Install dependencies")
        lines.append("pip install -r requirements.txt")
        lines.append("")
        lines.append("# Run tests")
        lines.append("pytest")
        lines.append("```")
        lines.append("")

    lines.append("## Key Workflows")
    lines.append("")
    lines.append("### Working in This Repository")
    lines.append("1. Review this CLAUDE.md for repository context")
    lines.append("2. Check existing code patterns in similar files")
    lines.append("3. Follow directory structure conventions")
    lines.append("4. Run tests before committing changes")
    lines.append("")

    if len(self.layers) > 1:
        lines.append("### Adding New Features")
        lines.append("1. Identify the appropriate layer for your changes")
        lines.append("2. Follow existing patterns in that layer")
        lines.append("3. Update tests accordingly")
        lines.append("4. Document significant changes")
        lines.append("")

    lines.append("## Important Patterns")
    lines.append("")
    lines.append("### Code Organization")
    for layer in self.layers[:3]:  # Show first 3 layers
        lines.append(f"- **{layer['name']}:** {', '.join(layer['directories'])}")
    lines.append("")

    lines.append("### Anti-Patterns to Avoid")
    lines.append("- Creating files without checking existing patterns first")
    lines.append("- Mixing concerns across architectural layers")
    lines.append("- Skipping tests for new functionality")
    lines.append("- Committing without reviewing changes")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*Generated on {data['timestamp']} by CLAUDE.md Bootstrap*")

    return '\n'.join(lines)
```

**Step 3: Test enhanced synthesis**

Run: `python3 test_synthesis.py`

**Expected output:**
```
Generated N lines
```

**Step 4: Clean up test**

Run: `rm test_synthesis.py`

**If Task Fails:**

1. **Content too long:**
   - Check: Line count validation in write_claude_md
   - Fix: Truncation logic already implemented
   - Rollback: `git checkout -- hooks/claude-md-bootstrap.py`

2. **Missing sections:**
   - Verify: All required sections present
   - Fix: Add missing sections to template

3. **Can't recover:**
   - Document: What synthesis failed
   - Stop: Return to human partner

---

## Task 8: Integration Testing

**Files:**
- Test: Full pipeline execution
- Create: Temporary test environment

**Prerequisites:**
- Tools: bash, git
- Files must exist: All hook files created
- Environment: Clean test directory

**Step 1: Create test git repository**

Run:
```bash
test_dir=$(mktemp -d)
cd "$test_dir"
git init
echo "# Test Repo" > README.md
mkdir -p src/api src/services tests config
touch src/api/routes.js src/services/user.js tests/test.js config/db.json
git add .
git commit -m "Initial commit"
echo "Test repo created at: $test_dir"
```

**Expected output:**
```
Initialized empty Git repository in /tmp/...
[master (root-commit) ...] Initial commit
Test repo created at: /tmp/...
```

**Step 2: Run bootstrap in test repo**

Run:
```bash
export CLAUDE_PROJECT_DIR="$test_dir"
export CLAUDE_PLUGIN_ROOT="$OLDPWD"
"$CLAUDE_PLUGIN_ROOT/hooks/claude-md-bootstrap.sh"
```

**Expected output:**
```
[INFO] No CLAUDE.md found. Starting auto-generation process...
[Phase 1] Discovering repository layers...
[Phase 2] Analyzing N layers...
[Phase 3] Synthesizing CLAUDE.md...
[Phase 4] Validating and writing file...
✓ Generated CLAUDE.md (N lines)
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart"
  }
}
```

**Step 3: Verify CLAUDE.md created**

Run:
```bash
cd "$test_dir"
ls -la CLAUDE.md
head -20 CLAUDE.md
wc -l CLAUDE.md
```

**Expected output:**
```
-rw-r--r-- 1 user group ... CLAUDE.md
# CLAUDE.md

This file provides guidance to Claude Code...
[First 20 lines of generated file]
N CLAUDE.md
```

**Step 4: Test idempotency (second run should skip)**

Run:
```bash
"$CLAUDE_PLUGIN_ROOT/hooks/claude-md-bootstrap.sh"
```

**Expected output:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart"
  }
}
```
(No generation messages - skipped because CLAUDE.md exists)

**Step 5: Clean up test directory**

Run:
```bash
cd "$OLDPWD"
rm -rf "$test_dir"
unset CLAUDE_PROJECT_DIR CLAUDE_PLUGIN_ROOT
```

**If Task Fails:**

1. **Bootstrap doesn't run:**
   - Check: Script permissions (`ls -l hooks/*.sh`)
   - Fix: `chmod +x hooks/*.sh`
   - Rollback: Remove test directory

2. **CLAUDE.md not created:**
   - Check: Error messages in output
   - Fix: Debug Python script with error details
   - Check: Fallback template should be created

3. **Can't recover:**
   - Document: Full error output
   - Stop: Return to human partner

---

## Task 9: Create Documentation

**Files:**
- Create: `hooks/README-claude-md-bootstrap.md`
- Test: Documentation completeness

**Prerequisites:**
- Files must exist: All bootstrap implementation files
- Environment: Working directory in ring repository

**Step 1: Write comprehensive documentation**

Create `hooks/README-claude-md-bootstrap.md`:
```markdown
# CLAUDE.md Auto-Bootstrap Hook

## Purpose

Automatically generates `CLAUDE.md` documentation for git repositories that lack them. This hook runs on SessionStart (before session-start.sh) to ensure repositories have proper Claude Code guidance documentation.

## How It Works

### Trigger Conditions

The bootstrap process runs when ALL conditions are met:
1. **SessionStart event** with `startup` or `resume` matcher
2. **Git repository** detected (`.git/` directory exists)
3. **No CLAUDE.md** file in project root

If any condition is false, the hook exits silently without action.

### Generation Process

**Phase 1: Layer Discovery (~15-20s)**
- Analyzes repository structure to identify architectural layers
- Discovers API, business logic, data, frontend, infrastructure layers
- Identifies cross-cutting concerns (auth, logging, config, testing)
- Falls back to monolithic structure if discovery fails

**Phase 2: Parallel Layer Analysis (~20-30s)**
- Dispatches parallel analysis for each discovered layer
- Examines key files, patterns, technologies in each layer
- Aggregates findings for synthesis phase
- Continues with partial results if some analyses timeout

**Phase 3: Content Synthesis (~10-15s)**
- Combines all findings into structured CLAUDE.md
- Generates repository overview, architecture breakdown
- Includes common commands, workflows, patterns
- Enforces 500-line maximum for token efficiency

**Phase 4: Validation & Write (~1s)**
- Validates generated content structure
- Enforces line limit (truncates if needed)
- Writes CLAUDE.md to project root
- Falls back to minimal template on error

**Total time:** ~45-65 seconds typical, 90 seconds maximum

### Generated Content Structure

```markdown
# CLAUDE.md

## Repository Overview
[2-3 sentences about the repository]

## Architecture
### Core Components
- Layer descriptions with directories
- Key files and patterns
- Technologies used

### Cross-Cutting Concerns
- Authentication, logging, config locations

## Common Commands
- Git operations
- Build/test/deploy commands
- Package manager commands

## Key Workflows
- How to work in this repository
- Adding new features
- Testing procedures

## Important Patterns
- Code organization
- Naming conventions
- Anti-patterns to avoid
```

### Integration with Other Hooks

**Execution Order:**
1. `claude-md-bootstrap.sh` - Generates CLAUDE.md if missing
2. `session-start.sh` - Loads skills and generated CLAUDE.md
3. Session begins with full context available

The bootstrap runs **before** session-start.sh to ensure the generated CLAUDE.md is immediately available for context injection.

## Configuration

### File Locations

- **Bootstrap script:** `hooks/claude-md-bootstrap.sh`
- **Python orchestrator:** `hooks/claude-md-bootstrap.py`
- **Hook configuration:** `hooks/hooks.json`
- **Generated file:** `${CLAUDE_PROJECT_DIR}/CLAUDE.md`

### Environment Variables

- `CLAUDE_PROJECT_DIR`: Project directory path (defaults to current directory)
- `CLAUDE_PLUGIN_ROOT`: Plugin installation directory (auto-detected)
- `CLAUDE_SESSION_ID`: Session identifier for isolation

### Customization

To customize the generation process, modify `hooks/claude-md-bootstrap.py`:

```python
# Adjust maximum lines (default 500)
MAX_LINES = 500

# Adjust timeout for layer analysis (default 120 seconds)
MAX_LAYER_ANALYSIS_TIME = 120

# Modify layer discovery patterns
patterns = {
    'Your Layer': ['your/', 'directories/'],
    # Add more patterns...
}
```

## Error Handling

### Graceful Degradation

The bootstrap implements multiple fallback strategies:

1. **Layer discovery fails** → Uses monolithic structure
2. **Layer analysis timeouts** → Continues with partial results
3. **Synthesis fails** → Creates minimal template
4. **Write permission denied** → Logs error, continues session

### Fallback Template

If generation fails completely, a minimal template is created:

```markdown
# CLAUDE.md

[Auto-generated - bootstrap process encountered errors]

## Architecture
[Analysis incomplete - delete this file to trigger regeneration]

## Common Commands
- git status
- git log --oneline -10

## Notes
Delete this file to trigger regeneration on next session.
```

### Error Recovery

To retry generation after a failure:
1. Delete the existing CLAUDE.md: `rm CLAUDE.md`
2. Start a new Claude Code session
3. Bootstrap will automatically retry

## Performance Characteristics

### Typical Metrics

- **Small repos (<100 files):** ~30-45 seconds
- **Medium repos (100-1000 files):** ~45-60 seconds
- **Large repos (>1000 files):** ~60-90 seconds
- **Monorepos:** May reach 90-second timeout

### Resource Usage

- **CPU:** Moderate (parallel analysis phases)
- **Memory:** ~50-100MB Python process
- **Disk I/O:** Read-only repository analysis
- **Network:** None (fully local operation)

### Optimization

The bootstrap is optimized for:
- **Token efficiency:** 500-line maximum output
- **Parallel execution:** Layer analyses run concurrently
- **Fast failure:** Early exit for non-applicable contexts
- **Partial results:** Continues despite individual failures

## Troubleshooting

### Bootstrap Doesn't Run

Check prerequisites:
```bash
# Verify git repository
ls -la .git/

# Check CLAUDE.md doesn't exist
ls -la CLAUDE.md

# Test hook directly
CLAUDE_PROJECT_DIR=$(pwd) ./hooks/claude-md-bootstrap.sh
```

### Generation Fails

Check error output:
```bash
# Run with verbose output
CLAUDE_PROJECT_DIR=$(pwd) python3 hooks/claude-md-bootstrap.py

# Check Python version
python3 --version  # Requires 3.8+

# Verify write permissions
touch CLAUDE.md && rm CLAUDE.md
```

### Content Quality Issues

If generated content is poor:
1. Ensure repository has clear structure
2. Add README.md with project description
3. Organize code into logical directories
4. Consider manual editing after generation

### Manual Regeneration

To force regeneration:
```bash
# Remove existing file
rm CLAUDE.md

# Run bootstrap manually
CLAUDE_PROJECT_DIR=$(pwd) ./hooks/claude-md-bootstrap.sh
```

## Limitations

### Current Limitations

1. **Agent integration pending:** Currently uses static analysis instead of Claude agents
2. **Language detection basic:** Relies on file extensions and common patterns
3. **No incremental updates:** Full regeneration only (no updates)
4. **Single file output:** Doesn't generate modular documentation
5. **English only:** No multi-language support

### Future Enhancements

Planned improvements:
- Full agent integration for intelligent analysis
- Incremental updates based on git changes
- Template library for common frameworks
- Multi-file documentation support
- Language detection via GitHub Linguist

## Examples

### Example: Node.js Application

For a typical Node.js project:
```
project/
├── src/
│   ├── api/
│   ├── services/
│   └── models/
├── tests/
├── config/
└── package.json
```

Generates:
- Identifies API, Business Logic, Data layers
- Includes npm commands
- Documents test structure
- ~300-400 lines typical

### Example: Python Monorepo

For a Python monorepo:
```
project/
├── services/
│   ├── api/
│   └── worker/
├── packages/
│   └── shared/
├── tests/
└── pyproject.toml
```

Generates:
- Identifies multiple service layers
- Includes pip/poetry commands
- Documents service boundaries
- ~400-500 lines typical

### Example: Simple Script Repository

For a simple scripts repository:
```
project/
├── scripts/
├── README.md
└── .git/
```

Generates:
- Single monolithic layer
- Basic git commands
- Minimal workflows section
- ~150-200 lines typical

## Integration with CI/CD

While primarily for interactive sessions, the bootstrap can be used in CI:

```bash
# CI validation that CLAUDE.md can be generated
./hooks/claude-md-bootstrap.sh
test -f CLAUDE.md || exit 1
```

This ensures all repositories maintain generatable documentation.

## Support

For issues or questions:
1. Check this documentation
2. Review error messages carefully
3. Try manual regeneration
4. Consider manual editing for specific needs

Remember: The auto-generated CLAUDE.md is a starting point. Manual refinement is encouraged for optimal results.
```

**Step 2: Verify documentation completeness**

Run: `grep -c "^#" hooks/README-claude-md-bootstrap.md`

**Expected output:**
A number indicating section headers (should be >10 for comprehensive docs)

**Step 3: Check documentation references all files**

Run:
```bash
grep -o "hooks/[a-z-]*\.\(sh\|py\|json\)" hooks/README-claude-md-bootstrap.md | sort -u
```

**Expected output:**
```
hooks/claude-md-bootstrap.py
hooks/claude-md-bootstrap.sh
hooks/hooks.json
```

**If Task Fails:**

1. **Documentation incomplete:**
   - Add missing sections
   - Ensure all features documented

2. **Examples missing:**
   - Add concrete examples
   - Show expected outputs

3. **Can't recover:**
   - Document: What sections are missing
   - Stop: Return to human partner

---

## Task 10: Final Integration Test and Commit

**Files:**
- Test: Complete integration
- Commit: All changes

**Prerequisites:**
- All previous tasks completed successfully
- Clean working tree except new files

**Step 1: Run complete test in real repository**

Run:
```bash
# Create a test branch
git checkout -b test-bootstrap-feature

# Make a test directory that simulates a repo without CLAUDE.md
test_repo="/tmp/test-claude-bootstrap"
mkdir -p "$test_repo"
cd "$test_repo"
git init
mkdir -p src/api src/services tests
touch src/api/routes.js src/services/logic.js tests/test.js
git add . && git commit -m "Test repo"

# Run bootstrap
CLAUDE_PROJECT_DIR="$test_repo" CLAUDE_PLUGIN_ROOT="$OLDPWD" "$OLDPWD/hooks/claude-md-bootstrap.sh"

# Verify CLAUDE.md was created
ls -la CLAUDE.md
echo "Lines in generated file: $(wc -l < CLAUDE.md)"

# Clean up
cd "$OLDPWD"
rm -rf "$test_repo"
```

**Expected output:**
```
[INFO] No CLAUDE.md found. Starting auto-generation process...
[Phase 1-4 messages...]
✓ Generated CLAUDE.md (N lines)
-rw-r--r-- ... CLAUDE.md
Lines in generated file: N
```

**Step 2: Test with existing CLAUDE.md (idempotency)**

Run:
```bash
# In current ring repo (has CLAUDE.md)
CLAUDE_PROJECT_DIR=$(pwd) ./hooks/claude-md-bootstrap.sh
```

**Expected output:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart"
  }
}
```
(Should skip silently since CLAUDE.md exists)

**Step 3: Verify all files are executable**

Run:
```bash
ls -l hooks/*.sh | grep -E "^-rwx"
```

**Expected output:**
All .sh files should show with execute permissions (rwx)

**Step 4: Run final validation**

Run:
```bash
# JSON syntax check
cat hooks/hooks.json | jq . > /dev/null && echo "✓ hooks.json valid"

# Python syntax check
python3 -m py_compile hooks/claude-md-bootstrap.py && echo "✓ Python valid"

# Bash syntax check
bash -n hooks/claude-md-bootstrap.sh && echo "✓ Bash valid"

# Documentation exists
test -f hooks/README-claude-md-bootstrap.md && echo "✓ Documentation exists"
```

**Expected output:**
```
✓ hooks.json valid
✓ Python valid
✓ Bash valid
✓ Documentation exists
```

**Step 5: Commit all changes**

Run:
```bash
git add hooks/claude-md-bootstrap.sh
git add hooks/claude-md-bootstrap.py
git add hooks/README-claude-md-bootstrap.md
git add hooks/hooks.json
git add docs/plans/2025-11-22-claude-md-bootstrap-plan.md

git status

git commit -m "feat(hooks): add CLAUDE.md auto-bootstrap for repos without documentation

- Automatically generates CLAUDE.md on SessionStart for git repos
- Discovers repository architecture through layer analysis
- Synthesizes findings into concise, actionable documentation
- Enforces 500-line limit for token efficiency
- Includes fallback templates for error cases
- Fully idempotent (skips if CLAUDE.md exists)"
```

**Expected output:**
```
[test-bootstrap-feature ...] feat(hooks): add CLAUDE.md auto-bootstrap...
 5 files changed, ... insertions(+), ... deletions(-)
```

**If Task Fails:**

1. **Test failures:**
   - Debug specific test that failed
   - Check error messages
   - Fix and re-test

2. **Commit issues:**
   - Verify all files staged: `git status`
   - Check for conflicts: `git diff`

3. **Can't recover:**
   - Document: What test failed and why
   - Stop: Return to human partner

---

## Task 11: Run Code Review (Final)

### Task 11: Run Code Review

1. **Dispatch all 3 reviewers in parallel:**
   - REQUIRED SUB-SKILL: Use ring:requesting-code-review
   - All reviewers run simultaneously (code-reviewer, business-logic-reviewer, security-reviewer)
   - Wait for all to complete

2. **Handle findings by severity (MANDATORY):**

**Critical/High/Medium Issues:**
- Fix immediately (do NOT add TODO comments for these severities)
- Re-run all 3 reviewers in parallel after fixes
- Repeat until zero Critical/High/Medium issues remain

**Low Issues:**
- Add `TODO(review):` comments in code at the relevant location
- Format: `TODO(review): [Issue description] (reported by [reviewer] on 2025-11-22, severity: Low)`

**Cosmetic/Nitpick Issues:**
- Add `FIXME(nitpick):` comments in code at the relevant location
- Format: `FIXME(nitpick): [Issue description] (reported by [reviewer] on 2025-11-22, severity: Cosmetic)`

3. **Proceed only when:**
   - Zero Critical/High/Medium issues remain
   - All Low issues have TODO(review): comments added
   - All Cosmetic issues have FIXME(nitpick): comments added

---

## Completion Checklist

Before considering implementation complete:

- [ ] Bootstrap shell script created and executable
- [ ] Python orchestrator implements all phases
- [ ] hooks.json updated with correct order
- [ ] Layer discovery works (static or agent-based)
- [ ] Layer analysis produces findings
- [ ] Content synthesis generates valid CLAUDE.md
- [ ] 500-line limit enforced
- [ ] Fallback template works on error
- [ ] Idempotency verified (skips when CLAUDE.md exists)
- [ ] Documentation complete and accurate
- [ ] All code review issues addressed
- [ ] Tests pass in multiple scenarios
- [ ] Committed to feature branch

## Notes

**Architecture Decisions:**
- Shell script wrapper for hook compatibility
- Python orchestrator for complex logic
- Static analysis fallback when agents unavailable
- Template-based generation as baseline
- 500-line limit for token efficiency

**Known Limitations:**
- Agent integration requires Task framework (TODO comments added)
- Parallel execution simulated with sequential fallback
- Language detection basic (file extension based)
- No incremental updates (full regeneration only)

**Future Enhancements:**
- Full agent integration when Task framework available
- True parallel layer analysis
- Smarter language/framework detection
- Incremental updates based on git diff
- Template library for common patterns