# Changelog

All notable changes to Ring will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-03

### Added - Infrastructure Layer

**Automated Review & Orchestration:**
- `review-orchestrator` agent - Sequential 3-gate review automation
- `full-reviewer` agent - All gates in single invocation
- `/ring:review` command - User-facing automated review
- Shared state (`.ring/review-state.json`) for cross-gate context

**Validation & Compliance:**
- `lib/compliance-validator.sh` - Validates skill adherence
- `lib/output-validator.sh` - Validates agent output format
- `lib/preflight-checker.sh` - Checks skill prerequisites
- `/ring:validate` command - Check skill compliance

**Discovery & Guidance:**
- `lib/skill-matcher.sh` - Maps tasks to relevant skills
- `lib/skill-composer.sh` - Suggests workflow transitions
- `/ring:which-skill` command - Skill discovery
- `/ring:next-skill` command - Workflow guidance

**Metrics & Analytics:**
- `lib/metrics-tracker.sh` - Tracks usage and violations
- `/ring:metrics` command - View effectiveness data
- `.ring/metrics.json` - Usage metrics storage

**Metadata Enhancements:**
- `output_schema` added to all 3 review agents
- `compliance_rules` added to test-driven-development
- `prerequisites` added to test-driven-development
- `composition` metadata added to test-driven-development
- Violation recovery procedures added to TDD, debugging, verification skills

**Documentation:**
- `docs/plans/2025-11-02-skills-infrastructure-improvements.md` - Design doc
- `testing/README.md` - Testing documentation
- `testing/test-review-orchestrator.md` - Integration tests
- `testing/test-skill-matcher.md` - Core two tests
- Enhanced `skills/shared-patterns/failure-recovery.md` with violation recovery
- New `skills/shared-patterns/preflight-checks.md` pattern

**Configuration:**
- Updated `.gitignore` to exclude `.ring/` runtime files

### Changed

**Agents:**
- `code-reviewer` v2.1.0 → v2.2.0 - Added output_schema
- `business-logic-reviewer` v2.0.0 → v2.1.0 - Added output_schema
- `security-reviewer` v2.0.0 → v2.1.0 - Added output_schema

**Documentation:**
- Updated `README.md` with infrastructure features
- Updated `docs/skills-quick-reference.md` with new commands/agents

### Plugin Version

- Version: 0.0.3 → 0.1.0 (minor version bump for new features)

## [0.0.3] - 2025-11-02

### Changed
- Enhanced `code-reviewer` with "mental walking" capabilities
- Added algorithmic flow analysis to Gate 1 review

## [0.0.2] - 2025-11-02

### Added
- Structured output templates for all review agents
- Pass/fail criteria with quantitative thresholds
- Code examples (good vs bad patterns) in all agents

## [0.0.1] - 2025-10-30

### Added
- Initial release with 28 skills
- 3 review agents (code-reviewer, business-logic-reviewer, security-reviewer)
- 8-gate pre-development workflow
- Session hooks
