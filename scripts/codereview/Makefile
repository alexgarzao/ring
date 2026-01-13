.PHONY: all build test test-coverage clean install fmt vet golangci-lint lint scope-detector

# Binary output directory
BIN_DIR := bin

# All binaries to build
BINARIES := scope-detector

all: build

build: $(BINARIES)

scope-detector:
	@echo "Building scope-detector..."
	@mkdir -p $(BIN_DIR)
	@go build -o $(BIN_DIR)/scope-detector ./cmd/scope-detector

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
