.PHONY: all build test test-coverage clean install fmt vet golangci-lint lint \
	scope-detector static-analysis ast-extractor call-graph data-flow compile-context run-all \
	build-context

# Binary output directory
BIN_DIR := bin

# All binaries to build
BINARIES := scope-detector static-analysis ast-extractor call-graph data-flow compile-context run-all

all: build

build: $(BINARIES)

# Phase 0: Scope Detection
scope-detector:
	@echo "Building scope-detector..."
	@mkdir -p $(BIN_DIR)
	@go build -o $(BIN_DIR)/scope-detector ./cmd/scope-detector

# Phase 1: Static Analysis
static-analysis:
	@echo "Building static-analysis..."
	@mkdir -p $(BIN_DIR)
	@go build -o $(BIN_DIR)/static-analysis ./cmd/static-analysis

# Phase 2: AST Extraction
ast-extractor:
	@echo "Building ast-extractor..."
	@mkdir -p $(BIN_DIR)
	@go build -o $(BIN_DIR)/ast-extractor ./cmd/ast-extractor

# Phase 3: Call Graph
call-graph:
	@echo "Building call-graph..."
	@mkdir -p $(BIN_DIR)
	@go build -o $(BIN_DIR)/call-graph ./cmd/call-graph

# Phase 4: Data Flow
data-flow:
	@echo "Building data-flow..."
	@mkdir -p $(BIN_DIR)
	@go build -o $(BIN_DIR)/data-flow ./cmd/data-flow

# Phase 5: Context Compilation
compile-context:
	@echo "Building compile-context..."
	@mkdir -p $(BIN_DIR)
	@go build -o $(BIN_DIR)/compile-context ./cmd/compile-context

run-all:
	@echo "Building run-all..."
	@mkdir -p $(BIN_DIR)
	@go build -o $(BIN_DIR)/run-all ./cmd/run-all

# Convenience target for Phase 5 binaries only
build-context: compile-context run-all
	@echo "Context binaries built."

test:
	@echo "Running tests..."
	@go test -v -race ./...

test-coverage:
	@echo "Running tests with coverage..."
	@go test -v -race -coverprofile=coverage.out ./...
	@go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report: coverage.html"

clean:
	@echo "Cleaning..."
	@rm -rf $(BIN_DIR)
	@rm -f coverage.out coverage.html

install: build
	@echo "Installing binaries to $(BIN_DIR)..."
	@chmod +x $(BIN_DIR)/*

# Development helpers
fmt:
	@go fmt ./...

vet:
	@go vet ./...

golangci-lint:
	@echo "Running golangci-lint..."
	@golangci-lint run ./...

lint: fmt vet golangci-lint
