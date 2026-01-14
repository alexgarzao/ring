# Codereview Enhancement: Pre-Analysis Pipeline

## Macro Plan v1.0

**Goal:** Enhance `/ring:codereview` with script-based static analysis, AST parsing, call graphs, and data flow analysis to catch issues before PR submission.

**Languages:** Go, TypeScript, Python (single-language projects, not mixed)
**Approach:** Script-based with Go binaries for analysis tools
**Integration:** `/ring:codereview` unchanged; scripts provide enriched context to existing reviewers
**Output Location:** `.ring/ring:codereview/` (project-local, gitignored)

---

## Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Script language | Go binaries | Team codes in Go; native AST parsing |
| Output location | `.ring/ring:codereview/` | Project-local, consistent with Ring tooling |
| CI integration | Not in v1 | Focus on local dev experience first |
| Monorepo support | Option B (detect & adapt) | Simple projects expected; warn on complexity |
| Project type | Single-language | Go OR TypeScript OR Python per project, not mixed |

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           /ring:codereview INVOCATION                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 0: SCOPE DETECTION                            │
│  scripts/ring:codereview/bin/scope-detector                                      │
│  ├── Parses git diff to identify changed files                              │
│  ├── Detects language (Go, TypeScript, or Python)                           │
│  ├── Identifies change types (new files, modifications, deletions)          │
│  └── Outputs: scope.json                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 1: STATIC ANALYSIS                               │
│  Runs for detected language:                                                │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐          │
│  │ Go                │ │ TypeScript        │ │ Python            │          │
│  │ ├── go vet        │ │ ├── tsc --noEmit  │ │ ├── ruff          │          │
│  │ ├── staticcheck   │ │ ├── eslint        │ │ ├── mypy          │          │
│  │ ├── golangci-lint │ │ ├── npm audit     │ │ ├── pylint        │          │
│  │ ├── gosec         │ │ └── ts-lint.json  │ │ ├── bandit        │          │
│  │ └── go-lint.json  │ │                   │ │ └── py-lint.json  │          │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘          │
│  Output: static-analysis.json (aggregate) + go/ts/py-lint.json               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 2: AST EXTRACTION                              │
│  Runs for detected language:                                                │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐          │
│  │ Go                │ │ TypeScript        │ │ Python            │          │
│  │ ├── Functions     │ │ ├── Functions     │ │ ├── Functions     │          │
│  │ ├── Structs       │ │ ├── Interfaces    │ │ ├── Classes       │          │
│  │ ├── Interfaces    │ │ ├── Types         │ │ ├── Dataclasses   │          │
│  │ ├── Imports       │ │ ├── Classes       │ │ ├── Type hints    │          │
│  │ └── go-ast.json   │ │ └── ts-ast.json   │ │ └── py-ast.json   │          │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘          │
│  Output: semantic-diff.md                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 3: CALL GRAPH ANALYSIS                          │
│  Runs for detected language:                                                │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐          │
│  │ Go                │ │ TypeScript        │ │ Python            │          │
│  │ ├── callgraph     │ │ ├── dep-cruiser   │ │ ├── pyan3         │          │
│  │ ├── guru          │ │ ├── madge         │ │ ├── custom ast    │          │
│  │ └── go-calls.json │ │ └── ts-calls.json │ │ └── py-calls.json │          │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘          │
│  Output: call-graph.json + impact-summary.md                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 4: DATA FLOW ANALYSIS                           │
│  Runs for detected language:                                                │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐          │
│  │ Go                │ │ TypeScript        │ │ Python            │          │
│  │ ├── HTTP sources  │ │ ├── req.* sources │ │ ├── Flask/Django  │          │
│  │ ├── DB sinks      │ │ ├── DOM sinks     │ │ │   request.*     │          │
│  │ ├── Nil tracking  │ │ ├── Null tracking │ │ ├── SQLAlchemy    │          │
│  │ └── go-flow.json  │ │ └── ts-flow.json  │ │ ├── None tracking │          │
│  └───────────────────┘ └───────────────────┘ │ └── py-flow.json  │          │
│                                              └───────────────────┘          │
│  Output: data-flow.json + security-summary.md                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 5: CONTEXT COMPILATION                           │
│  scripts/ring:codereview/bin/compile-context                                     │
│  ├── Aggregates all phase outputs                                           │
│  ├── Generates reviewer-specific context files:                             │
│  │   ├── context-ring:code-reviewer.md                                           │
│  │   ├── context-ring:security-reviewer.md                                       │
│  │   ├── context-ring:business-logic-reviewer.md                                 │
│  │   ├── context-ring:test-reviewer.md                                           │
│  │   └── context-ring:nil-safety-reviewer.md                                     │
│  └── Outputs: .ring/ring:codereview/ directory                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXISTING /ring:codereview FLOW                            │
│  5 reviewers dispatched in parallel (unchanged)                             │
│  Each reviewer reads their context file + git diff                          │
│  ├── ring:code-reviewer        + context-ring:code-reviewer.md                   │
│  ├── ring:security-reviewer    + context-ring:security-reviewer.md               │
│  ├── ring:business-logic-reviewer + context-ring:business-logic-reviewer.md      │
│  ├── ring:test-reviewer        + context-ring:test-reviewer.md                   │
│  └── ring:nil-safety-reviewer  + context-ring:nil-safety-reviewer.md             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure

```
ring/
├── scripts/
│   └── ring:codereview/
│       ├── cmd/                          # Go binaries (main packages)
│       │   ├── scope-detector/           # Phase 0
│       │   │   └── main.go
│       │   ├── static-analysis/          # Phase 1 orchestrator
│       │   │   └── main.go
│       │   ├── ast-extractor/            # Phase 2
│       │   │   └── main.go
│       │   ├── call-graph/               # Phase 3
│       │   │   └── main.go
│       │   ├── data-flow/                # Phase 4
│       │   │   └── main.go
│       │   ├── compile-context/          # Phase 5
│       │   │   └── main.go
│       │   └── run-all/                  # Main orchestrator
│       │       └── main.go
│       │
│       ├── internal/                     # Shared Go packages
│       │   ├── git/                      # Git operations (diff, show, etc.)
│       │   │   └── git.go
│       │   ├── scope/                    # Scope detection logic
│       │   │   └── scope.go
│       │   ├── lint/                     # Linter integrations
│       │   │   ├── golangci.go
│       │   │   ├── staticcheck.go
│       │   │   ├── gosec.go
│       │   │   ├── eslint.go
│       │   │   ├── tsc.go
│       │   │   ├── ruff.go               # Python: ruff
│       │   │   ├── mypy.go               # Python: mypy
│       │   │   ├── pylint.go             # Python: pylint
│       │   │   └── bandit.go             # Python: bandit (security)
│       │   ├── ast/                      # AST extraction
│       │   │   ├── golang.go             # Uses go/ast, go/parser
│       │   │   ├── typescript.go         # Shells out to ts-ast-extractor
│       │   │   └── python.go             # Shells out to py-ast-extractor
│       │   ├── callgraph/                # Call graph analysis
│       │   │   ├── golang.go             # Uses golang.org/x/tools
│       │   │   ├── typescript.go         # Uses dependency-cruiser
│       │   │   └── python.go             # Uses pyan3 or custom
│       │   ├── dataflow/                 # Data flow / taint analysis
│       │   │   ├── golang.go
│       │   │   ├── typescript.go
│       │   │   └── python.go             # Flask/Django/FastAPI patterns
│       │   ├── output/                   # Output formatters
│       │   │   ├── json.go
│       │   │   └── markdown.go
│       │   └── cache/                    # Caching utilities
│       │       └── cache.go
│       │
│       ├── ts/                           # TypeScript helpers (minimal)
│       │   ├── ast-extractor.ts          # Called by Go binary
│       │   ├── package.json
│       │   └── tsconfig.json
│       │
│       ├── py/                           # Python helpers (minimal)
│       │   ├── ast_extractor.py          # Called by Go binary
│       │   ├── call_graph.py             # Uses ast module for call analysis
│       │   ├── data_flow.py              # Framework-aware taint tracking
│       │   └── requirements.txt          # Minimal deps (stdlib mostly)
│       │
│       ├── go.mod                        # Go module for scripts
│       ├── go.sum
│       ├── Makefile                      # Build targets
│       └── install.sh                    # One-time setup
│
├── .ring/                                # Project-local Ring data (gitignored)
│   └── ring:codereview/                       # Pre-analysis outputs
│       ├── scope.json
│       ├── static-analysis.json
│       ├── ast.json                      # Language-specific AST
│       ├── semantic-diff.md
│       ├── call-graph.json
│       ├── impact-summary.md
│       ├── data-flow.json
│       ├── security-summary.md
│       ├── context-ring:code-reviewer.md
│       ├── context-ring:security-reviewer.md
│       ├── context-ring:business-logic-reviewer.md
│       ├── context-ring:test-reviewer.md
│       ├── context-ring:nil-safety-reviewer.md
│       └── cache/                        # Hash-based cache
│           └── ...
│
└── .gitignore                            # Add .ring/
```

**Note:** TypeScript and Python AST extraction require small helper scripts because Go cannot natively parse these languages. The Go binaries shell out to `ts/ast-extractor.ts` and `py/ast_extractor.py` and consume JSON output.

---

## 3. Script Specifications

### 3.1 Phase 0: Scope Detection

**Binary:** `scripts/ring:codereview/bin/scope-detector` (source: `cmd/scope-detector`)

**Input:** Git diff (staged, unstaged, or between refs)
**Output:** `scope.json`

```json
{
  "base_ref": "main",
  "head_ref": "HEAD",
  "languages": ["go", "typescript"],
  "files": {
    "go": {
      "modified": ["internal/handler/user.go", "internal/repo/user.go"],
      "added": ["internal/service/notification.go"],
      "deleted": []
    },
    "typescript": {
      "modified": ["src/components/UserForm.tsx"],
      "added": [],
      "deleted": ["src/utils/deprecated.ts"]
    }
  },
  "stats": {
    "total_files": 4,
    "total_additions": 245,
    "total_deletions": 32
  },
  "packages_affected": {
    "go": ["internal/handler", "internal/repo", "internal/service"],
    "typescript": ["src/components", "src/utils"]
  }
}
```

**Logic:**
1. Run `git diff --name-status --stat`
2. Categorize files by extension (`.go`, `.ts`, `.tsx`)
3. Extract package/directory information
4. Return structured scope

---

### 3.2 Phase 1: Static Analysis

#### 3.2.1 Go Static Analysis

**Binary:** `scripts/ring:codereview/bin/static-analysis` (source: `cmd/static-analysis`)

**Tools Required:**
| Tool | Purpose | Install |
|------|---------|---------|
| `go vet` | Built-in correctness checks | (bundled) |
| `staticcheck` | Advanced static analysis | `go install honnef.co/go/tools/cmd/staticcheck@latest` |
| `golangci-lint` | Meta-linter (runs 50+ linters) | `brew install golangci-lint` |
| `gosec` | Security-focused analysis | `go install github.com/securego/gosec/v2/cmd/gosec@latest` |

**Input:** Changed `.go` files from `scope.json` + derived package list
**Output:** `go-lint.json`

```json
{
  "tool_versions": {
    "go": "1.22.0",
    "staticcheck": "2024.1",
    "golangci-lint": "1.56.0",
    "gosec": "2.19.0"
  },
  "findings": [
    {
      "tool": "staticcheck",
      "rule": "SA1019",
      "severity": "warning",
      "file": "internal/handler/user.go",
      "line": 45,
      "column": 12,
      "message": "grpc.Dial is deprecated: use grpc.NewClient instead",
      "suggestion": "Replace grpc.Dial with grpc.NewClient",
      "category": "deprecation"
    },
    {
      "tool": "gosec",
      "rule": "G401",
      "severity": "high",
      "file": "internal/crypto/hash.go",
      "line": 23,
      "column": 8,
      "message": "Use of weak cryptographic primitive",
      "category": "security"
    }
  ],
  "summary": {
    "critical": 0,
    "high": 1,
    "warning": 3,
    "info": 5
  }
}
```

**Logic:**
1. Determine affected packages from changed files (`go list` + path mapping)
2. Run each tool at package scope (not individual files)
3. Parse outputs and filter findings to changed files
4. Normalize to common schema
5. Deduplicate findings (same issue from multiple tools)

#### 3.2.2 TypeScript Static Analysis

**Script:** `internal/ring:lint/tsc.go`, `internal/ring:lint/eslint.go`

**Tools Required:**
| Tool | Purpose | Install |
|------|---------|---------|
| `tsc` | Type checking | `npm install -g typescript` |
| `eslint` | Linting + style | Project-local |
| `npm audit` | Dependency vulnerabilities | (bundled) |

**Input:** Changed `.ts`/`.tsx` files from `scope.json` + project config (`tsconfig.json`, `.eslintrc`)
**Output:** `ts-lint.json` (same schema as Go)

**Notes:**
- Run `tsc --noEmit -p tsconfig.json` at project scope and filter diagnostics to changed files
- Run `eslint` on changed files; `npm audit` runs at project scope

#### 3.2.3 Python Static Analysis

**Script:** `internal/ring:lint/ruff.go`, `internal/ring:lint/mypy.go`, `internal/ring:lint/pylint.go`, `internal/ring:lint/bandit.go`

**Tools Required:**
| Tool | Purpose | Install |
|------|---------|---------|
| `ruff` | Fast linter (replaces flake8, isort, pyupgrade) | `pip install ruff` |
| `mypy` | Static type checking | `pip install mypy` |
| `pylint` | Comprehensive linting | `pip install pylint` |
| `bandit` | Security-focused analysis | `pip install bandit` |

**Input:** Changed `.py` files from `scope.json` + project config (`pyproject.toml`, `mypy.ini`, `ruff.toml`)
**Output:** `py-lint.json`

```json
{
  "tool_versions": {
    "python": "3.11.0",
    "ruff": "0.4.0",
    "mypy": "1.10.0",
    "pylint": "3.2.0",
    "bandit": "1.7.8"
  },
  "findings": [
    {
      "tool": "ruff",
      "rule": "F841",
      "severity": "warning",
      "file": "app/services/user.py",
      "line": 45,
      "column": 5,
      "message": "Local variable 'result' is assigned but never used",
      "category": "unused"
    },
    {
      "tool": "mypy",
      "rule": "arg-type",
      "severity": "error",
      "file": "app/handlers/api.py",
      "line": 23,
      "column": 15,
      "message": "Argument 1 to 'process' has incompatible type 'str | None'; expected 'str'",
      "category": "type"
    },
    {
      "tool": "bandit",
      "rule": "B608",
      "severity": "high",
      "file": "app/db/queries.py",
      "line": 34,
      "column": 12,
      "message": "Possible SQL injection via string concatenation",
      "category": "security"
    }
  ],
  "summary": {
    "critical": 0,
    "high": 1,
    "warning": 5,
    "info": 3
  }
}
```

**Logic:**
1. Run `ruff check --output-format=json` on changed files
2. Run `mypy --show-error-codes --output=json` at package/project scope, then filter diagnostics to changed files
3. Run `pylint --output-format=json` on changed files
4. Run `bandit -f json` on changed files
5. Normalize and deduplicate findings

---

### 3.3 Phase 2: AST Extraction

#### 3.3.1 Go AST Extractor

**Binary:** `scripts/ring:codereview/bin/ast-extractor` (source: `cmd/ast-extractor`)

**Why Go binary?** Native `go/ast` and `go/parser` packages provide accurate parsing.

**Input:** Changed `.go` files + their base versions (from git)
**Output:** `go-ast.json`

```json
{
  "functions": {
    "modified": [
      {
        "name": "CreateUser",
        "file": "internal/handler/user.go",
        "package": "handler",
        "receiver": "*UserHandler",
        "before": {
          "signature": "func (h *UserHandler) CreateUser(ctx context.Context, req *CreateUserRequest) (*User, error)",
          "params": [
            {"name": "ctx", "type": "context.Context"},
            {"name": "req", "type": "*CreateUserRequest"}
          ],
          "returns": [
            {"type": "*User"},
            {"type": "error"}
          ],
          "line_start": 45,
          "line_end": 78
        },
        "after": {
          "signature": "func (h *UserHandler) CreateUser(ctx context.Context, req *CreateUserRequest, opts ...CreateOption) (*User, error)",
          "params": [
            {"name": "ctx", "type": "context.Context"},
            {"name": "req", "type": "*CreateUserRequest"},
            {"name": "opts", "type": "...CreateOption"}
          ],
          "returns": [
            {"type": "*User"},
            {"type": "error"}
          ],
          "line_start": 45,
          "line_end": 92
        },
        "changes": ["added_param:opts", "body_expanded"]
      }
    ],
    "added": [
      {
        "name": "NotifyUser",
        "file": "internal/service/notification.go",
        "package": "service",
        "signature": "func NotifyUser(ctx context.Context, userID string, event Event) error",
        "line_start": 12,
        "line_end": 45
      }
    ],
    "deleted": []
  },
  "types": {
    "modified": [
      {
        "name": "CreateUserRequest",
        "kind": "struct",
        "file": "internal/handler/types.go",
        "before": {
          "fields": [
            {"name": "Name", "type": "string", "tags": "`json:\"name\"`"},
            {"name": "Email", "type": "string", "tags": "`json:\"email\"`"}
          ]
        },
        "after": {
          "fields": [
            {"name": "Name", "type": "string", "tags": "`json:\"name\"`"},
            {"name": "Email", "type": "string", "tags": "`json:\"email\"`"},
            {"name": "Metadata", "type": "map[string]any", "tags": "`json:\"metadata,omitempty\"`"}
          ]
        },
        "changes": ["added_field:Metadata"]
      }
    ],
    "added": [],
    "deleted": []
  },
  "interfaces": {
    "modified": [],
    "added": [],
    "deleted": []
  },
  "imports": {
    "added": [
      {"file": "internal/handler/user.go", "path": "github.com/company/lib/options"}
    ],
    "removed": []
  },
  "error_handling": {
    "new_error_returns": [
      {
        "function": "CreateUser",
        "file": "internal/handler/user.go",
        "line": 67,
        "error_type": "validation",
        "message": "return nil, ErrInvalidMetadata"
      }
    ],
    "removed_error_checks": []
  }
}
```

**Logic:**
1. Parse current file with `go/parser`
2. Parse base version (from git) with `go/parser`
3. Compare ASTs: functions, types, interfaces, imports
4. Extract semantic changes (not line-level diff)

#### 3.3.2 TypeScript AST Extractor

**Script:** `ts/ast-extractor.ts` (Node script, called by Go binary)

**Why TypeScript?** Native TypeScript compiler API provides accurate parsing.

**Dependencies:**
```json
{
  "dependencies": {
    "typescript": "^5.0.0"
  }
}
```

**Input:** Changed `.ts`/`.tsx` files + their base versions
**Output:** `ts-ast.json` (similar schema to Go)

```json
{
  "functions": {
    "modified": [...],
    "added": [...],
    "deleted": [...]
  },
  "types": {
    "interfaces": {...},
    "type_aliases": {...},
    "enums": {...}
  },
  "classes": {
    "modified": [...],
    "added": [...],
    "deleted": [...]
  },
  "imports_exports": {
    "added_imports": [...],
    "removed_imports": [...],
    "added_exports": [...],
    "removed_exports": [...]
  },
  "react_components": {
    "modified": [
      {
        "name": "UserForm",
        "file": "src/components/UserForm.tsx",
        "props_before": [...],
        "props_after": [...],
        "hooks_used": ["useState", "useEffect", "useCallback"],
        "changes": ["added_prop:onMetadataChange"]
      }
    ]
  }
}
```

#### 3.3.3 Python AST Extractor

**Script:** `py/ast_extractor.py` (Python script, called by Go binary)

**Why Python?** Native `ast` module provides accurate parsing without dependencies.

**Dependencies:** None (uses stdlib `ast` module)

**Input:** Changed `.py` files + their base versions (from git)
**Output:** `py-ast.json`

```json
{
  "functions": {
    "modified": [
      {
        "name": "create_user",
        "file": "app/services/user.py",
        "module": "app.services.user",
        "is_async": true,
        "decorators": ["@transactional"],
        "before": {
          "signature": "async def create_user(db: Session, data: CreateUserRequest) -> User",
          "params": [
            {"name": "db", "type": "Session", "default": null},
            {"name": "data", "type": "CreateUserRequest", "default": null}
          ],
          "returns": "User",
          "line_start": 45,
          "line_end": 78
        },
        "after": {
          "signature": "async def create_user(db: Session, data: CreateUserRequest, *, notify: bool = True) -> User",
          "params": [
            {"name": "db", "type": "Session", "default": null},
            {"name": "data", "type": "CreateUserRequest", "default": null},
            {"name": "notify", "type": "bool", "default": "True", "keyword_only": true}
          ],
          "returns": "User",
          "line_start": 45,
          "line_end": 92
        },
        "changes": ["added_param:notify", "body_expanded"]
      }
    ],
    "added": [...],
    "deleted": [...]
  },
  "classes": {
    "modified": [
      {
        "name": "UserService",
        "file": "app/services/user.py",
        "bases": ["BaseService"],
        "is_dataclass": false,
        "before": {
          "methods": ["__init__", "create", "update", "delete"],
          "attributes": ["db", "cache"]
        },
        "after": {
          "methods": ["__init__", "create", "update", "delete", "notify"],
          "attributes": ["db", "cache", "notifier"]
        },
        "changes": ["added_method:notify", "added_attr:notifier"]
      }
    ],
    "added": [],
    "deleted": []
  },
  "dataclasses": {
    "modified": [
      {
        "name": "CreateUserRequest",
        "file": "app/schemas/user.py",
        "before": {
          "fields": [
            {"name": "name", "type": "str"},
            {"name": "email", "type": "str"}
          ]
        },
        "after": {
          "fields": [
            {"name": "name", "type": "str"},
            {"name": "email", "type": "str"},
            {"name": "metadata", "type": "dict[str, Any]", "default": "field(default_factory=dict)"}
          ]
        },
        "changes": ["added_field:metadata"]
      }
    ]
  },
  "imports": {
    "added": [
      {"file": "app/services/user.py", "module": "app.notifications", "names": ["Notifier"]}
    ],
    "removed": []
  },
  "type_aliases": {
    "added": [],
    "modified": [],
    "deleted": []
  }
}
```

**Logic:**
1. Parse current file with `ast.parse()`
2. Parse base version (from git) with `ast.parse()`
3. Walk AST to extract: functions, classes, dataclasses, imports, type aliases
4. Compare and identify changes
5. Output JSON to stdout for Go binary to consume

#### 3.3.4 Semantic Diff Renderer

**Script:** `internal/output/markdown.go`

**Input:** `go-ast.json` OR `ts-ast.json` OR `py-ast.json` (based on detected language)
**Output:** `semantic-diff.md`

```markdown
# Semantic Change Summary

## Go Changes

### Functions Modified (2)

#### `handler.CreateUser`
**File:** `internal/handler/user.go:45-92`
**Change:** Signature modified

```diff
- func (h *UserHandler) CreateUser(ctx context.Context, req *CreateUserRequest) (*User, error)
+ func (h *UserHandler) CreateUser(ctx context.Context, req *CreateUserRequest, opts ...CreateOption) (*User, error)
```

**Impact:**
- Added variadic parameter `opts ...CreateOption`
- Body expanded (+14 lines)
- New error return path at line 67

#### `repo.SaveUser`
**File:** `internal/repo/user.go:23-45`
**Change:** Body modified (logic change)

### Functions Added (1)

#### `service.NotifyUser`
**File:** `internal/service/notification.go:12-45`
**Purpose:** New function (requires review)

### Types Modified (1)

#### `handler.CreateUserRequest`
**File:** `internal/handler/types.go`

| Field | Before | After |
|-------|--------|-------|
| Metadata | - | `map[string]any` (added) |

---

## TypeScript Changes

### Components Modified (1)

#### `UserForm`
**File:** `src/components/UserForm.tsx`
**Props Changed:**
- Added: `onMetadataChange?: (metadata: Record<string, unknown>) => void`

**Hooks Used:** `useState`, `useEffect`, `useCallback`
```

---

### 3.4 Phase 3: Call Graph Analysis

#### 3.4.1 Go Call Graph

**Binary:** `scripts/ring:codereview/bin/call-graph` (source: `cmd/call-graph`)

**Tools Required:**
| Tool | Purpose | Install |
|------|---------|---------|
| `callgraph` | Static call graph | `go install golang.org/x/tools/cmd/callgraph@latest` |
| `guru` | Code navigation | `go install golang.org/x/tools/cmd/guru@latest` |

**Input:** Modified functions from `go-ast.json`
**Output:** `go-calls.json`

```json
{
  "modified_functions": [
    {
      "function": "handler.CreateUser",
      "file": "internal/handler/user.go",
      "callers": [
        {
          "function": "handler.UserHandler.ServeHTTP",
          "file": "internal/handler/router.go",
          "line": 89,
          "call_site": "h.CreateUser(ctx, req)"
        },
        {
          "function": "batch.BatchImporter.ProcessUsers",
          "file": "internal/batch/importer.go",
          "line": 156,
          "call_site": "h.CreateUser(ctx, &req)"
        }
      ],
      "callees": [
        {
          "function": "validator.ValidateCreateUserRequest",
          "file": "internal/validator/user.go",
          "line": 12
        },
        {
          "function": "repo.UserRepository.Save",
          "file": "internal/repo/user.go",
          "line": 67
        },
        {
          "function": "events.Publisher.Publish",
          "file": "internal/events/publisher.go",
          "line": 34
        }
      ],
      "test_coverage": [
        {
          "test_function": "TestCreateUser",
          "file": "internal/handler/user_test.go",
          "line": 23
        },
        {
          "test_function": "TestCreateUserValidation",
          "file": "internal/handler/user_test.go",
          "line": 89
        }
      ]
    }
  ],
  "impact_analysis": {
    "direct_callers": 2,
    "transitive_callers": 5,
    "affected_tests": 2,
    "affected_packages": ["handler", "batch"]
  }
}
```

**Logic:**
1. Build call graph for affected packages only: `callgraph -algo=cha <affected packages>`
2. Enforce a time budget (target <30s); if exceeded, emit partial results with a warning
3. For each modified function, find:
   - Direct callers (who calls this function)
   - Direct callees (what this function calls)
   - Transitive callers (full upstream chain)
4. Cross-reference with test files

#### 3.4.2 TypeScript Call Graph

**Script:** `internal/callgraph/typescript.go` (calls `dependency-cruiser`)

**Tools Required:**
| Tool | Purpose | Install |
|------|---------|---------|
| `dependency-cruiser` | Dependency analysis | `npm install -g dependency-cruiser` |
| `madge` | Circular dependency detection | `npm install -g madge` |

**Input:** Modified functions/components from `ts-ast.json`
**Output:** `ts-calls.json` (similar schema)

#### 3.4.3 Python Call Graph

**Script:** `internal/callgraph/python.go` (calls `py/call_graph.py`)

**Tools Required:**
| Tool | Purpose | Install |
|------|---------|---------|
| `pyan3` | Static call graph generator | `pip install pyan3` |
| Custom `py/call_graph.py` | AST-based call analysis | (bundled) |

**Input:** Modified functions from `py-ast.json`
**Output:** `py-calls.json`

```json
{
  "modified_functions": [
    {
      "function": "app.services.user.create_user",
      "file": "app/services/user.py",
      "callers": [
        {
          "function": "app.api.routes.user.create_user_endpoint",
          "file": "app/api/routes/user.py",
          "line": 45,
          "call_site": "await user_service.create_user(db, data)"
        },
        {
          "function": "app.tasks.batch.import_users",
          "file": "app/tasks/batch.py",
          "line": 78,
          "call_site": "await create_user(session, user_data)"
        }
      ],
      "callees": [
        {
          "function": "app.validators.user.validate_user_data",
          "file": "app/validators/user.py",
          "line": 12
        },
        {
          "function": "app.repositories.user.UserRepository.save",
          "file": "app/repositories/user.py",
          "line": 56
        }
      ],
      "test_coverage": [
        {
          "test_function": "test_create_user",
          "file": "tests/services/test_user.py",
          "line": 23
        }
      ]
    }
  ],
  "impact_analysis": {
    "direct_callers": 2,
    "transitive_callers": 4,
    "affected_tests": 1,
    "affected_modules": ["app.api.routes.user", "app.tasks.batch"]
  }
}
```

**Logic:**
1. Use `pyan3` to generate static call graph: `pyan3 --dot app/`
2. Parse into internal representation
3. For each modified function, find callers and callees
4. Cross-reference with test files (`tests/`, `*_test.py`)

#### 3.4.4 Impact Summary Renderer

**Input:** `go-calls.json` OR `ts-calls.json` OR `py-calls.json` (based on detected language)
**Output:** `impact-summary.md`

```markdown
# Impact Analysis

## High Impact Changes

### `handler.CreateUser` (Go)
**Risk Level:** HIGH (2 direct callers, 5 transitive)

**Direct Callers (signature change affects these):**
1. `handler.UserHandler.ServeHTTP` - `internal/handler/router.go:89`
2. `batch.BatchImporter.ProcessUsers` - `internal/batch/importer.go:156`

**Callees (this function depends on):**
1. `validator.ValidateCreateUserRequest`
2. `repo.UserRepository.Save`
3. `events.Publisher.Publish`

**Test Coverage:**
- ✅ `TestCreateUser` - `internal/handler/user_test.go:23`
- ✅ `TestCreateUserValidation` - `internal/handler/user_test.go:89`
- ⚠️ New parameter `opts` may need additional test cases

---

## Low Impact Changes

### `service.NotifyUser` (Go)
**Risk Level:** LOW (new function, no existing callers)

**Note:** New function - verify it's called somewhere or mark as dead code.
```

---

### 3.5 Phase 4: Data Flow Analysis

#### 3.5.1 Go Data Flow

**Binary:** `scripts/ring:codereview/bin/data-flow` (source: `cmd/data-flow`)

**Why Go binary?** Complex AST traversal for taint tracking.

**Concepts:**
- **Sources:** Where untrusted data enters (HTTP params, env vars, DB reads, file reads)
- **Sinks:** Where data exits (DB writes, HTTP responses, logs, file writes, exec)
- **Sanitizers:** Validation/encoding functions that make data safe
- **Taint:** Data that flows from source without passing through sanitizer

**Input:** Changed `.go` files
**Output:** `go-flow.json`

```json
{
  "flows": [
    {
      "id": "flow-1",
      "source": {
        "type": "http_request",
        "subtype": "body",
        "variable": "req",
        "file": "internal/handler/user.go",
        "line": 48,
        "expression": "json.NewDecoder(r.Body).Decode(&req)"
      },
      "path": [
        {
          "step": 1,
          "file": "internal/handler/user.go",
          "line": 52,
          "expression": "req.Name",
          "operation": "field_access"
        },
        {
          "step": 2,
          "file": "internal/handler/user.go",
          "line": 55,
          "expression": "validator.ValidateName(req.Name)",
          "operation": "sanitizer",
          "sanitizer_type": "validation"
        },
        {
          "step": 3,
          "file": "internal/repo/user.go",
          "line": 34,
          "expression": "db.Exec(query, name)",
          "operation": "sink_usage"
        }
      ],
      "sink": {
        "type": "database",
        "subtype": "write",
        "file": "internal/repo/user.go",
        "line": 34,
        "expression": "db.Exec(query, name)"
      },
      "sanitized": true,
      "risk": "low",
      "notes": "Input validated before DB write"
    },
    {
      "id": "flow-2",
      "source": {
        "type": "http_request",
        "subtype": "query_param",
        "variable": "userID",
        "file": "internal/handler/user.go",
        "line": 23,
        "expression": "r.URL.Query().Get(\"user_id\")"
      },
      "path": [
        {
          "step": 1,
          "file": "internal/handler/user.go",
          "line": 25,
          "expression": "repo.GetUser(ctx, userID)",
          "operation": "function_call"
        }
      ],
      "sink": {
        "type": "database",
        "subtype": "read",
        "file": "internal/repo/user.go",
        "line": 12,
        "expression": "db.Query(\"SELECT * FROM users WHERE id = $1\", userID)"
      },
      "sanitized": false,
      "risk": "medium",
      "notes": "Query param used in DB query without UUID validation"
    }
  ],
  "nil_sources": [
    {
      "variable": "user",
      "file": "internal/handler/user.go",
      "line": 67,
      "expression": "user, err := repo.GetUser(ctx, id)",
      "checked": true,
      "check_line": 68,
      "check_expression": "if err != nil || user == nil"
    },
    {
      "variable": "config",
      "file": "internal/service/notification.go",
      "line": 23,
      "expression": "config := os.Getenv(\"NOTIFICATION_CONFIG\")",
      "checked": false,
      "risk": "high",
      "notes": "Environment variable used without empty check"
    }
  ],
  "summary": {
    "total_flows": 2,
    "sanitized_flows": 1,
    "unsanitized_flows": 1,
    "high_risk": 1,
    "medium_risk": 1,
    "low_risk": 0,
    "nil_risks": 1
  }
}
```

**Source Types to Track:**
| Source Type | Examples |
|-------------|----------|
| `http_request` | `r.Body`, `r.URL.Query()`, `r.Header`, `r.FormValue()` |
| `environment` | `os.Getenv()`, `os.LookupEnv()` |
| `database` | `db.Query()`, `db.QueryRow()` |
| `file` | `os.ReadFile()`, `io.ReadAll()` |
| `external_api` | `http.Get()`, `client.Do()` |

**Sink Types to Track:**
| Sink Type | Examples |
|-----------|----------|
| `database` | `db.Exec()`, `db.Query()` (with interpolation) |
| `http_response` | `w.Write()`, `json.NewEncoder().Encode()` |
| `logging` | `log.Printf()`, `logger.Info()` |
| `file` | `os.WriteFile()`, `io.WriteString()` |
| `exec` | `exec.Command()`, `os.StartProcess()` |

#### 3.5.2 TypeScript Data Flow

**Script:** `internal/dataflow/typescript.go` (calls `ts/data-flow.ts`)

**Input:** Changed `.ts`/`.tsx` files
**Output:** `ts-flow.json`

**Source Types:**
| Source Type | Examples |
|-------------|----------|
| `http_request` | `req.body`, `req.params`, `req.query`, `req.headers` |
| `environment` | `process.env.*` |
| `user_input` | `event.target.value`, form inputs |
| `url_params` | `useParams()`, `searchParams` |
| `local_storage` | `localStorage.getItem()` |

**Sink Types:**
| Sink Type | Examples |
|-----------|----------|
| `database` | ORM calls, raw queries |
| `http_response` | `res.json()`, `res.send()` |
| `dom_manipulation` | `innerHTML`, `dangerouslySetInnerHTML` |
| `external_api` | `fetch()`, `axios.*` |
| `eval` | `eval()`, `Function()` |

#### 3.5.3 Python Data Flow

**Script:** `internal/dataflow/python.go` (calls `py/data_flow.py`)

**Input:** Changed `.py` files
**Output:** `py-flow.json`

**Framework Detection:**
The Python data flow analyzer auto-detects the web framework:
- **Flask:** `from flask import request`, `request.args`, `request.form`, `request.json`
- **Django:** `request.GET`, `request.POST`, `request.body`
- **FastAPI:** `Query()`, `Body()`, `Path()` parameters
- **Starlette:** `request.query_params`, `request.form()`

**Source Types:**
| Source Type | Framework | Examples |
|-------------|-----------|----------|
| `http_request` | Flask | `request.args.get()`, `request.form`, `request.json` |
| `http_request` | Django | `request.GET`, `request.POST`, `request.body` |
| `http_request` | FastAPI | Function parameters with `Query()`, `Body()`, `Path()` |
| `environment` | All | `os.environ.get()`, `os.getenv()` |
| `database` | All | `session.query()`, `Model.objects.get()`, ORM reads |
| `file` | All | `open()`, `Path.read_text()` |
| `user_input` | All | `input()`, CLI arguments |

**Sink Types:**
| Sink Type | Examples |
|-----------|----------|
| `database` | `session.execute()`, `cursor.execute()`, `Model.save()` |
| `http_response` | `jsonify()`, `HttpResponse()`, `return {...}` (FastAPI) |
| `file` | `open(..., 'w')`, `Path.write_text()` |
| `subprocess` | `subprocess.run()`, `os.system()`, `os.popen()` |
| `eval` | `eval()`, `exec()`, `compile()` |
| `template` | `render_template()`, `Template().render()` (XSS risk) |
| `deserialization` | `pickle.loads()`, `yaml.load()` (insecure deserialize) |

**None/Optional Tracking:**
| Pattern | Risk |
|---------|------|
| `dict.get()` without default | Returns `None` if key missing |
| `Optional[T]` without check | May be `None` |
| `or None` in expression | Explicit `None` possibility |
| `getattr(..., None)` | May return `None` |
| `.first()` ORM queries | Returns `None` if no match |

**Output:** `py-flow.json` (same schema as Go/TS)

```json
{
  "flows": [
    {
      "id": "flow-1",
      "source": {
        "type": "http_request",
        "subtype": "query_param",
        "framework": "fastapi",
        "variable": "user_id",
        "file": "app/api/routes/user.py",
        "line": 23,
        "expression": "user_id: str = Query(...)"
      },
      "path": [
        {
          "step": 1,
          "file": "app/api/routes/user.py",
          "line": 25,
          "expression": "user_service.get_user(user_id)",
          "operation": "function_call"
        }
      ],
      "sink": {
        "type": "database",
        "subtype": "read",
        "file": "app/repositories/user.py",
        "line": 34,
        "expression": "session.execute(select(User).where(User.id == user_id))"
      },
      "sanitized": false,
      "risk": "medium",
      "notes": "Query param used in DB query - verify UUID validation in Pydantic model"
    }
  ],
  "none_sources": [
    {
      "variable": "user",
      "file": "app/services/user.py",
      "line": 45,
      "expression": "user = session.query(User).filter_by(id=user_id).first()",
      "checked": true,
      "check_line": 46,
      "check_expression": "if user is None:"
    },
    {
      "variable": "config_value",
      "file": "app/config.py",
      "line": 12,
      "expression": "config_value = os.environ.get('API_KEY')",
      "checked": false,
      "risk": "high",
      "notes": "Environment variable may be None"
    }
  ],
  "summary": {
    "total_flows": 1,
    "sanitized_flows": 0,
    "unsanitized_flows": 1,
    "high_risk": 1,
    "medium_risk": 1,
    "low_risk": 0,
    "none_risks": 1
  }
}
```

#### 3.5.4 Security Summary Renderer

**Input:** `go-flow.json` OR `ts-flow.json` OR `py-flow.json` (based on detected language)
**Output:** `security-summary.md`

```markdown
# Security Analysis

## 🔴 High Risk Findings

### Unvalidated Environment Variable
**File:** `internal/service/notification.go:23`
**Issue:** Environment variable used without validation

```go
config := os.Getenv("NOTIFICATION_CONFIG")  // No empty check
```

**Recommendation:** Add validation before use:
```go
config := os.Getenv("NOTIFICATION_CONFIG")
if config == "" {
    return fmt.Errorf("NOTIFICATION_CONFIG not set")
}
```

---

## 🟡 Medium Risk Findings

### Query Parameter Without UUID Validation
**File:** `internal/handler/user.go:23`
**Flow:** HTTP query param → Database query

```go
userID := r.URL.Query().Get("user_id")  // No UUID validation
// ...
db.Query("SELECT * FROM users WHERE id = $1", userID)
```

**Recommendation:** Validate UUID format before use:
```go
userID := r.URL.Query().Get("user_id")
if _, err := uuid.Parse(userID); err != nil {
    return ErrInvalidUserID
}
```

---

## ✅ Properly Sanitized Flows

### User Name Input
**File:** `internal/handler/user.go:48-55`
**Flow:** HTTP body → Validator → Database

✅ Input validated via `validator.ValidateName()` before DB write.

---

## Nil Safety Concerns

| Variable | File | Line | Checked? | Risk |
|----------|------|------|----------|------|
| `user` | handler/user.go | 67 | ✅ Yes | Low |
| `config` | service/notification.go | 23 | ❌ No | High |
```

---

### 3.6 Phase 5: Context Compilation

**Binary:** `scripts/ring:codereview/bin/compile-context` (source: `cmd/compile-context`)

**Purpose:** Aggregate all analysis outputs into reviewer-specific context files.

**Input:** All phase outputs
**Output:** Reviewer context files in `.ring/ring:codereview/`

#### Context File Templates

**`context-ring:code-reviewer.md`:**
```markdown
# Pre-Analysis Context: Code Quality

## Static Analysis Findings (3 issues)

| Severity | Tool | File | Line | Message |
|----------|------|------|------|---------|
| warning | staticcheck | handler/user.go | 45 | SA1019: grpc.Dial is deprecated |
| warning | golangci-lint | repo/user.go | 23 | ineffassign: variable assigned but never used |
| info | staticcheck | service/notification.go | 12 | S1000: single-case select can be simplified |

## Semantic Changes

[Embedded content from semantic-diff.md]

## Focus Areas

Based on analysis, pay special attention to:
1. **Signature change in `CreateUser`** - New variadic parameter may affect callers
2. **New error return path** - Line 67 in handler/user.go
3. **Deprecated API usage** - grpc.Dial needs update
```

**`context-ring:security-reviewer.md`:**
```markdown
# Pre-Analysis Context: Security

## Security Scanner Findings (1 issue)

| Severity | Tool | Rule | File | Line | Message |
|----------|------|------|------|------|---------|
| high | gosec | G401 | crypto/hash.go | 23 | Use of weak cryptographic primitive |

## Data Flow Analysis

[Embedded content from security-summary.md]

## Focus Areas

Based on analysis, pay special attention to:
1. **Unvalidated env var** - `NOTIFICATION_CONFIG` at service/notification.go:23
2. **Query param validation** - `user_id` at handler/user.go:23
3. **Crypto weakness** - crypto/hash.go:23
```

**`context-ring:business-logic-reviewer.md`:**
```markdown
# Pre-Analysis Context: Business Logic

## Impact Analysis

[Embedded content from impact-summary.md]

## Semantic Changes

### Functions with Logic Changes

1. **`handler.CreateUser`** - Added options parameter, new validation path
2. **`repo.SaveUser`** - Body modified (requires logic review)

## Focus Areas

Based on analysis, pay special attention to:
1. **New parameter handling** - How are options processed?
2. **Caller impact** - 2 direct callers affected by signature change
3. **New function** - `service.NotifyUser` - verify business requirements
```

**`context-ring:test-reviewer.md`:**
```markdown
# Pre-Analysis Context: Testing

## Test Coverage for Modified Code

| Function | File | Tests | Status |
|----------|------|-------|--------|
| `handler.CreateUser` | handler/user.go | 2 tests | ⚠️ May need update for new param |
| `repo.SaveUser` | repo/user.go | 1 test | ✅ Covered |
| `service.NotifyUser` | service/notification.go | 0 tests | ❌ New, needs tests |

## Focus Areas

1. **New function without tests** - `NotifyUser` needs test coverage
2. **New parameter** - `CreateUser` opts parameter may need test cases
3. **New error path** - Line 67 error return needs negative test
```

**`context-ring:nil-safety-reviewer.md`:**
```markdown
# Pre-Analysis Context: Nil Safety

## Nil Source Analysis

| Variable | File | Line | Checked? | Risk |
|----------|------|------|----------|------|
| `user` | handler/user.go | 67 | ✅ Yes | Low |
| `config` | service/notification.go | 23 | ❌ No | High |

## Data Flow Nil Risks

[Relevant sections from data-flow analysis]

## Focus Areas

1. **Unchecked env var** - `config` at service/notification.go:23
2. **New function returns** - Verify nil checks for `NotifyUser` return values
```

---

## 4. Integration with /ring:codereview

### 4.1 Modified Reviewer Prompts

Each reviewer's prompt in `ring:codereview.md` gets updated to include:

```markdown
## Pre-Analysis Context

Before reviewing, read the pre-analysis context:
1. Run: `cat .ring/ring:codereview/context-{reviewer-name}.md`
2. Use findings to guide your review
3. Verify pre-analysis findings (tools can miss context)
4. Add findings that tools missed
```

### 4.2 Execution Flow

```
User runs: /ring:codereview

1. Orchestrator runs: scripts/ring:codereview/bin/run-all
   ├── Phase 0: bin/scope-detector → scope.json
   ├── Phase 1: static-analysis (detected language only)
   ├── Phase 2: ast-extractor (detected language only)
   ├── Phase 3: call-graph (detected language only)
   ├── Phase 4: data-flow (detected language only)
   └── Phase 5: bin/compile-context → .ring/ring:codereview/

2. Orchestrator dispatches 5 reviewers (parallel)
   Each reviewer:
   ├── Reads: .ring/ring:codereview/context-{name}.md
   ├── Reads: git diff
   └── Produces: findings

3. Orchestrator aggregates findings
```

### 4.3 Caching Strategy

**Problem:** Re-running analysis on unchanged files wastes time.

**Solution:** Hash-based caching in `.ring/ring:codereview/cache/`

```bash
# Cache structure
.ring/ring:codereview/cache/
├── scope-{hash}.json           # Cached scope
├── go-lint-{hash}.json         # Cached Go lint
├── ts-lint-{hash}.json         # Cached TS lint
├── go-ast-{hash}.json          # Cached Go AST
└── ...
```

**Cache key:** SHA256 of (file content + tool version + tool flags + relevant config files)

**Invalidation:**
- File content changes → re-analyze
- Tool version changes → re-analyze
- Config changes (e.g., .golangci.yml, tsconfig.json, .eslintrc, pyproject.toml, mypy.ini, ruff.toml) → re-analyze

---

## 5. Tool Requirements

### 5.1 Go Tools

| Tool | Version | Purpose | Installation |
|------|---------|---------|--------------|
| `go` | ≥1.21 | Compiler, vet | System |
| `staticcheck` | ≥2024.1 | Static analysis | `go install honnef.co/go/tools/cmd/staticcheck@latest` |
| `golangci-lint` | ≥1.56 | Meta-linter | `brew install golangci-lint` |
| `gosec` | ≥2.19 | Security scanner | `go install github.com/securego/gosec/v2/cmd/gosec@latest` |
| `callgraph` | latest | Call graph | `go install golang.org/x/tools/cmd/callgraph@latest` |
| `guru` | latest | Code navigation | `go install golang.org/x/tools/cmd/guru@latest` |

### 5.2 TypeScript Tools

| Tool | Version | Purpose | Installation |
|------|---------|---------|--------------|
| `node` | ≥18 | Runtime | System |
| `typescript` | ≥5.0 | Type checking, AST | `npm install -g typescript` |
| `eslint` | ≥8.0 | Linting | Project-local |
| `dependency-cruiser` | ≥16.0 | Dependency analysis | `npm install -g dependency-cruiser` |
| `madge` | ≥7.0 | Circular deps | `npm install -g madge` |

### 5.3 Python Tools

| Tool | Version | Purpose | Installation |
|------|---------|---------|--------------|
| `python` | ≥3.10 | Runtime, AST (stdlib) | System |
| `ruff` | ≥0.4.0 | Fast linter (flake8 + isort + more) | `pip install ruff` |
| `mypy` | ≥1.10 | Static type checking | `pip install mypy` |
| `pylint` | ≥3.0 | Comprehensive linting | `pip install pylint` |
| `bandit` | ≥1.7 | Security scanner | `pip install bandit` |
| `pyan3` | ≥1.2 | Call graph analysis | `pip install pyan3` |

**Note:** Python's `ast` module (stdlib) is used for AST extraction - no additional dependencies needed.

### 5.4 Installation Script

**Script:** `scripts/ring:codereview/install.sh`

```bash
#!/bin/bash
set -e

# Installs all required tools for ring:codereview pre-analysis
# Run: ./scripts/ring:codereview/install.sh [go|ts|py|all]

INSTALL_TARGET="${1:-all}"

install_go_tools() {
    echo "=== Installing Go tools ==="
    go install honnef.co/go/tools/cmd/staticcheck@latest
    go install github.com/securego/gosec/v2/cmd/gosec@latest
    go install golang.org/x/tools/cmd/callgraph@latest
    go install golang.org/x/tools/cmd/guru@latest

    # golangci-lint (platform-specific)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install golangci-lint || brew upgrade golangci-lint
    else
        curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(go env GOPATH)/bin
    fi
    echo "✅ Go tools installed"
}

install_ts_tools() {
    echo "=== Installing TypeScript tools ==="
    npm install -g typescript dependency-cruiser madge
    
    # Install local TS helper deps
    cd "$(dirname "$0")/ts"
    npm install
    cd -
    echo "✅ TypeScript tools installed"
}

install_py_tools() {
    echo "=== Installing Python tools ==="
    pip install --upgrade ruff mypy pylint bandit pyan3
    
    # Verify Python helper has no external deps (uses stdlib ast)
    python3 -c "import ast; print('Python ast module: OK')"
    echo "✅ Python tools installed"
}

build_binaries() {
    echo "=== Building Go analysis binaries ==="
    cd "$(dirname "$0")"
    go build -o bin/scope-detector ./cmd/scope-detector
    go build -o bin/static-analysis ./cmd/static-analysis
    go build -o bin/ast-extractor ./cmd/ast-extractor
    go build -o bin/call-graph ./cmd/call-graph
    go build -o bin/data-flow ./cmd/data-flow
    go build -o bin/compile-context ./cmd/compile-context
    go build -o bin/run-all ./cmd/run-all
    cd -
    echo "✅ Binaries built"
}

case "$INSTALL_TARGET" in
    go)
        install_go_tools
        ;;
    ts)
        install_ts_tools
        ;;
    py)
        install_py_tools
        ;;
    all)
        install_go_tools
        install_ts_tools
        install_py_tools
        build_binaries
        ;;
    *)
        echo "Usage: $0 [go|ts|py|all]"
        exit 1
        ;;
esac

echo ""
echo "🎉 Installation complete!"
echo "Run 'scripts/ring:codereview/verify.sh' to verify installation."
```

---

## 6. Error Handling

### 6.1 Graceful Degradation

If a tool fails, the pipeline continues with reduced context:

| Failure | Impact | Fallback |
|---------|--------|----------|
| `staticcheck` fails | No static findings | Continue with `go vet` only |
| `ast-extractor` fails | No semantic diff | Reviewers use raw git diff |
| `call-graph` fails | No impact analysis | Reviewers explore manually |
| `data-flow` fails | No taint analysis | Security reviewer uses heuristics |

### 6.2 Error Reporting

Each script outputs errors to `stderr` and includes in context:

```json
{
  "success": false,
  "error": "staticcheck: command not found",
  "partial_results": true,
  "available_data": ["go-vet.json"]
}
```

Reviewers see warnings:

```markdown
## ⚠️ Pre-Analysis Warnings

Some analysis tools failed. Manual verification recommended:
- staticcheck: not installed (run `scripts/install-tools.sh`)
```

---

## 7. Future Enhancements (Out of Scope for v1)

| Enhancement | Description | Complexity | Phase |
|-------------|-------------|------------|-------|
| **Test coverage integration** | Map changes to coverage reports | Medium | v2 |
| **Historical pattern learning** | Learn from past review findings | High | v2 |
| **Custom rule definitions** | Project-specific lint rules | Medium | v2 |
| **IDE integration** | VSCode extension for pre-commit | High | v3 |
| **CI integration** | Run analysis in GitHub Actions | Low | v1.1 |
| **Incremental analysis** | Only analyze changed lines | High | v2 |
| **Cross-language flow** | Track data across Go ↔ TS ↔ Python | Very High | v3 |

---

## 8. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Pre-catch rate** | 40% of issues found by scripts before AI review | Compare script findings vs reviewer findings |
| **False positive rate** | <10% of script findings are wrong | Track dismissed findings |
| **Analysis time** | <30 seconds for typical PR | Time `run-all.sh` |
| **Reviewer efficiency** | 20% fewer tokens used per review | Compare context sizes |
| **Issue severity accuracy** | 80% severity match with human judgment | Sample review |

---

## 9. Phasing Summary

| Phase | Components | Effort | Value |
|-------|------------|--------|-------|
| **Phase 1** | Scope detection, static analysis (Go + TS + Python) | 4-5 days | High (immediate lint integration) |
| **Phase 2** | AST extraction (Go + TS + Python), semantic diff | 6-8 days | High (structured understanding) |
| **Phase 3** | Call graph (Go + TS + Python), impact analysis | 5-6 days | Medium (blast radius awareness) |
| **Phase 4** | Data flow (Go + TS + Python), security summary | 7-9 days | High (security pre-screening) |
| **Phase 5** | Context compilation, reviewer integration | 3-4 days | Critical (ties everything together) |
| **Phase 6** | Caching, error handling, polish | 2-3 days | Medium (performance, reliability) |

**Total estimated effort:** 27-35 days

### Per-Language Effort Breakdown

| Component | Go | TypeScript | Python |
|-----------|----|-----------:|-------:|
| Static Analysis | 1 day | 1 day | 1.5 days |
| AST Extraction | 2 days | 2 days | 2 days |
| Call Graph | 1.5 days | 1.5 days | 2 days |
| Data Flow | 2 days | 2 days | 3 days |
| **Subtotal** | 6.5 days | 6.5 days | 8.5 days |

**Note:** Python data flow is more complex due to framework detection (Flask/Django/FastAPI) and dynamic typing.

---

## 10. Resolved Questions

| Question | Decision |
|----------|----------|
| Script language | Go binaries (team expertise, native AST) |
| Context file format | Markdown for reviewers (human-readable) |
| Cache location | `.ring/ring:codereview/cache/` (project-local) |
| CI mode | Not in v1 (local dev focus) |
| Monorepo support | Option B: detect & adapt, warn on complexity |

## 11. Remaining Open Questions

1. **TS AST helper:** Bundle pre-built JS or require `npx ts-node`?
2. **Binary distribution:** Build per-platform or require Go toolchain?
3. **Python framework detection:** Auto-detect or require config?

---

## 12. Project Assumptions

Based on user input, the pipeline assumes:

1. **Single-language projects** - A project is Go OR TypeScript OR Python, not mixed
2. **Simple module structure** - One `go.mod`, one root `package.json`, or standard Python layout
3. **Standard layouts:**
   - Go: `internal/`, `cmd/`, `pkg/`
   - TypeScript: `src/`
   - Python: `app/`, `src/`, or flat layout with `pyproject.toml`/`setup.py`

**Graceful degradation on complexity:**
- Multiple `go.mod` detected → Warn, analyze files individually
- Workspace files detected (`go.work`, `pnpm-workspace.yaml`) → Warn, analyze changed files only
- Multiple `pyproject.toml` detected → Warn, analyze changed files only
- Mixed languages detected → Warn, run analysis for dominant language only
