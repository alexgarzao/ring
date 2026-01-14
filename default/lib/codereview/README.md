# Ring Codereview Binaries

Pre-compiled binaries for the Ring codereview pipeline. These tools perform static analysis, AST extraction, call graph generation, and context compilation for AI-assisted code review.

## Binaries

| Binary | Purpose |
|--------|---------|
| `run-all` | Pipeline orchestrator - runs all analysis phases in sequence |
| `scope-detector` | Detects changed files and determines review scope |
| `static-analysis` | Runs language-specific static analysis tools |
| `ast-extractor` | Extracts Abstract Syntax Tree data from source files |
| `call-graph` | Generates function/method call relationships |
| `data-flow` | Analyzes data flow patterns and dependencies |
| `compile-context` | Compiles analysis results into reviewer-specific context |

## Platform Support

| Platform | Architecture | Directory |
|----------|--------------|-----------|
| macOS Intel | amd64 | `bin/darwin_amd64/` |
| macOS Apple Silicon | arm64 | `bin/darwin_arm64/` |
| Linux x86_64 | amd64 | `bin/linux_amd64/` |
| Linux ARM | arm64 | `bin/linux_arm64/` |

## Directory Structure

```
default/lib/codereview/
├── README.md
└── bin/
    ├── darwin_amd64/
    │   ├── run-all
    │   ├── scope-detector
    │   ├── static-analysis
    │   ├── ast-extractor
    │   ├── call-graph
    │   ├── data-flow
    │   └── compile-context
    ├── darwin_arm64/
    │   └── ... (same binaries)
    ├── linux_amd64/
    │   └── ... (same binaries)
    └── linux_arm64/
        └── ... (same binaries)
```

## Security Model

The codereview binaries use a hybrid security approach combining checksum verification with build-from-source fallback.

### How It Works

```
Binary Found? ──Yes──> Verify Checksum ──Pass──> Execute
     │                      │
     No                    Fail
     │                      │
     └────> Build from Source <────┘
                  │
           ┌─────┴─────┐
        Success      Fail
           │           │
       Execute    Degraded Mode
```

### Checksum Verification

Each platform directory contains a `CHECKSUMS.sha256` file with SHA256 hashes for all binaries:

```
default/lib/codereview/bin/
├── CHECKSUMS.sha256           # All platforms (28 entries)
├── darwin_amd64/
│   └── CHECKSUMS.sha256       # 7 entries
├── darwin_arm64/
│   └── CHECKSUMS.sha256       # 7 entries
├── linux_amd64/
│   └── CHECKSUMS.sha256       # 7 entries
└── linux_arm64/
    └── CHECKSUMS.sha256       # 7 entries
```

**Manual verification:**

```bash
# Linux
cd default/lib/codereview/bin/linux_amd64
sha256sum --check CHECKSUMS.sha256

# macOS
cd default/lib/codereview/bin/darwin_arm64
shasum -a 256 --check CHECKSUMS.sha256
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RING_ALLOW_UNVERIFIED` | `false` | Set to `true` to bypass checksum verification (development only) |

**Security implications:**
- When `false` (default): Missing or invalid checksums cause the pipeline to fail or trigger build-from-source
- When `true`: Binaries execute without verification (NOT recommended for production)

### What This Protects Against

| Threat | Protection |
|--------|------------|
| Tampered binaries | Checksum mismatch triggers rebuild |
| Missing checksums | Fails closed (requires explicit bypass) |
| TOCTOU race conditions | Atomic verify-and-execute pattern |
| Partial string bypass | Exact match verification |

### Limitations

- **Integrity, not authenticity**: Checksums verify the binary hasn't changed, not who created it
- **Future enhancement**: GPG/Sigstore signatures planned for authenticity verification

## Rebuilding Binaries

### Prerequisites

- Go 1.21 or later
- Access to the Ring repository

### Build Commands

From the repository root:

```bash
# Build all platforms
./scripts/codereview/build-release.sh

# Clean and rebuild all platforms
./scripts/codereview/build-release.sh --clean

# Build specific platform only
./scripts/codereview/build-release.sh --platform=darwin/arm64
./scripts/codereview/build-release.sh --platform=linux/amd64
```

### Build Options

| Option | Description |
|--------|-------------|
| `--clean` | Remove existing binaries before building |
| `--platform=<os/arch>` | Build only for specific platform |
| `--help` | Show usage information |

### Build Flags

Binaries are built with the following flags for optimization:

- `-ldflags="-s -w"` - Strips debug symbols for smaller binary size

### Source Location

Source code is located at: `scripts/codereview/cmd/<binary>/`

## Usage

The binaries are automatically selected based on the current platform when invoked through the Ring codereview pipeline. For manual usage:

```bash
# Direct invocation (example for macOS ARM)
./default/lib/codereview/bin/darwin_arm64/run-all --help

# Or add to PATH
export PATH="$PATH:$(pwd)/default/lib/codereview/bin/darwin_arm64"
run-all --help
```

## Version Information

Binaries are rebuilt when:
- Source code changes in `scripts/codereview/cmd/`
- Go version is updated
- Build flags are modified

To verify binary integrity, compare SHA256 checksums after building locally.
