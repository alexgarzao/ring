## Makefile Standards

All projects **MUST** include a Makefile with standardized commands for consistent developer experience.

### Required Commands

| Command                | Purpose                                               | Category      |
| ---------------------- | ----------------------------------------------------- | ------------- |
| `make build`           | Build all components                                  | Core          |
| `make lint`            | Run linters (golangci-lint)                           | Code Quality  |
| `make test`            | Run all tests                                         | Testing       |
| `make cover`           | Generate test coverage report                         | Testing       |
| `make test-unit`       | Run unit tests only                                   | Testing       |
| `make up`              | Start all services with Docker Compose                | Docker        |
| `make down`            | Stop all services                                     | Docker        |
| `make start`           | Start existing containers                             | Docker        |
| `make stop`            | Stop running containers                               | Docker        |
| `make restart`         | Restart all containers                                | Docker        |
| `make rebuild-up`      | Rebuild and restart services                          | Docker        |
| `make set-env`         | Copy .env.example to .env                             | Setup         |
| `make dev-setup`       | Install development tools (swag, golangci-lint, etc.) | Setup         |
| `make generate-docs`   | Generate API documentation (Swagger)                  | Documentation |
| `make migrate-up`      | Apply all pending database migrations                 | Database      |
| `make migrate-down`    | Rollback last migration                               | Database      |
| `make migrate-create`  | Create new migration file                             | Database      |
| `make migrate-version` | Show current migration version                        | Database      |

### Component Delegation Pattern (Monorepo)

For monorepo projects with multiple components:

| Command                             | Purpose                             |
| ----------------------------------- | ----------------------------------- |
| `make infra COMMAND=<cmd>`          | Run command in infra component      |
| `make onboarding COMMAND=<cmd>`     | Run command in onboarding component |
| `make all-components COMMAND=<cmd>` | Run command across all components   |

### Root Makefile Example

```makefile
# Project Root Makefile

# Component directories
INFRA_DIR := ./components/infra
ONBOARDING_DIR := ./components/onboarding
TRANSACTION_DIR := ./components/transaction

COMPONENTS := $(INFRA_DIR) $(ONBOARDING_DIR) $(TRANSACTION_DIR)

# Docker command detection
DOCKER_CMD := $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo "docker-compose"; fi)

#-------------------------------------------------------
# Core Commands
#-------------------------------------------------------

.PHONY: build
build:
	@for dir in $(COMPONENTS); do \
		echo "Building in $$dir..."; \
		(cd $$dir && $(MAKE) build) || exit 1; \
	done
	@echo "[ok] All components built successfully"

.PHONY: test
test:
	@for dir in $(COMPONENTS); do \
		(cd $$dir && $(MAKE) test) || exit 1; \
	done

.PHONY: test-unit
test-unit:
	@for dir in $(COMPONENTS); do \
		(cd $$dir && go test -v -short ./...) || exit 1; \
	done

.PHONY: cover
cover:
	@sh ./scripts/coverage.sh
	@go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated at coverage.html"

#-------------------------------------------------------
# Code Quality Commands
#-------------------------------------------------------

.PHONY: lint
lint:
	@for dir in $(COMPONENTS); do \
		if find "$$dir" -name "*.go" -type f | grep -q .; then \
			(cd $$dir && golangci-lint run --fix ./...) || exit 1; \
		fi; \
	done
	@echo "[ok] Linting completed successfully"

#-------------------------------------------------------
# Docker Commands
#-------------------------------------------------------

.PHONY: up
up:
	@for dir in $(COMPONENTS); do \
		if [ -f "$$dir/docker-compose.yml" ]; then \
			(cd $$dir && $(DOCKER_CMD) -f docker-compose.yml up -d) || exit 1; \
		fi; \
	done
	@echo "[ok] All services started successfully"

.PHONY: down
down:
	@for dir in $(COMPONENTS); do \
		if [ -f "$$dir/docker-compose.yml" ]; then \
			(cd $$dir && $(DOCKER_CMD) -f docker-compose.yml down) || exit 1; \
		fi; \
	done

.PHONY: start
start:
	@for dir in $(COMPONENTS); do \
		if [ -f "$$dir/docker-compose.yml" ]; then \
			(cd $$dir && $(DOCKER_CMD) -f docker-compose.yml start) || exit 1; \
		fi; \
	done

.PHONY: stop
stop:
	@for dir in $(COMPONENTS); do \
		if [ -f "$$dir/docker-compose.yml" ]; then \
			(cd $$dir && $(DOCKER_CMD) -f docker-compose.yml stop) || exit 1; \
		fi; \
	done

.PHONY: restart
restart:
	@make stop && make start

.PHONY: rebuild-up
rebuild-up:
	@for dir in $(COMPONENTS); do \
		if [ -f "$$dir/docker-compose.yml" ]; then \
			(cd $$dir && $(DOCKER_CMD) -f docker-compose.yml down && \
			 $(DOCKER_CMD) -f docker-compose.yml build && \
			 $(DOCKER_CMD) -f docker-compose.yml up -d) || exit 1; \
		fi; \
	done

#-------------------------------------------------------
# Setup Commands
#-------------------------------------------------------

.PHONY: set-env
set-env:
	@for dir in $(COMPONENTS); do \
		if [ -f "$$dir/.env.example" ] && [ ! -f "$$dir/.env" ]; then \
			cp "$$dir/.env.example" "$$dir/.env"; \
			echo "Created .env in $$dir"; \
		fi; \
	done

#-------------------------------------------------------
# Documentation Commands
#-------------------------------------------------------

.PHONY: generate-docs
generate-docs:
	@./scripts/generate-docs.sh

#-------------------------------------------------------
# Component Delegation
#-------------------------------------------------------

.PHONY: infra
infra:
	@if [ -z "$(COMMAND)" ]; then \
		echo "Error: Use COMMAND=<cmd>"; exit 1; \
	fi
	@cd $(INFRA_DIR) && $(MAKE) $(COMMAND)

.PHONY: onboarding
onboarding:
	@if [ -z "$(COMMAND)" ]; then \
		echo "Error: Use COMMAND=<cmd>"; exit 1; \
	fi
	@cd $(ONBOARDING_DIR) && $(MAKE) $(COMMAND)

.PHONY: all-components
all-components:
	@if [ -z "$(COMMAND)" ]; then \
		echo "Error: Use COMMAND=<cmd>"; exit 1; \
	fi
	@for dir in $(COMPONENTS); do \
		(cd $$dir && $(MAKE) $(COMMAND)) || exit 1; \
	done
```

### Component Makefile Example

```makefile
# Component Makefile (e.g., components/onboarding/Makefile)

SERVICE_NAME := onboarding-service
ARTIFACTS_DIR := ./artifacts

.PHONY: build test lint up down

build:
	@go build -o $(ARTIFACTS_DIR)/$(SERVICE_NAME) ./cmd/app

test:
	@go test -v ./...

lint:
	@golangci-lint run --fix ./...

up:
	@docker compose -f docker-compose.yml up -d

down:
	@docker compose -f docker-compose.yml down
```

### Database Migration Commands (MANDATORY)

MUST: All projects with a database include these migration commands using `golang-migrate`:

```makefile
#-------------------------------------------------------
# Database Migration Commands
#-------------------------------------------------------

# Database URL from environment or default
DATABASE_URL ?= postgres://$(DB_USER):$(DB_PASSWORD)@$(DB_HOST):$(DB_PORT)/$(DB_NAME)?sslmode=$(DB_SSLMODE)
MIGRATE = migrate -path ./migrations -database "$(DATABASE_URL)"

.PHONY: migrate-up
migrate-up: ## Apply all pending migrations
	@echo "Applying migrations..."
	$(MIGRATE) up
	@echo "[ok] Migrations applied successfully"

.PHONY: migrate-down
migrate-down: ## Rollback last migration
	@echo "Rolling back last migration..."
	$(MIGRATE) down 1
	@echo "[ok] Rollback completed"

.PHONY: migrate-down-all
migrate-down-all: ## Rollback all migrations (DANGEROUS)
	@echo "WARNING: Rolling back ALL migrations..."
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	$(MIGRATE) down
	@echo "[ok] All migrations rolled back"

.PHONY: migrate-create
migrate-create: ## Create new migration (usage: make migrate-create NAME=create_users)
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME is required. Usage: make migrate-create NAME=create_users"; \
		exit 1; \
	fi
	migrate create -ext sql -dir ./migrations -seq $(NAME)
	@echo "[ok] Migration files created in ./migrations/"

.PHONY: migrate-version
migrate-version: ## Show current migration version
	$(MIGRATE) version

.PHONY: migrate-force
migrate-force: ## Force set migration version (usage: make migrate-force VERSION=1)
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required. Usage: make migrate-force VERSION=1"; \
		exit 1; \
	fi
	$(MIGRATE) force $(VERSION)
	@echo "[ok] Version forced to $(VERSION)"

.PHONY: migrate-status
migrate-status: ## Show migration status
	@echo "Current migration version:"
	@$(MIGRATE) version 2>/dev/null || echo "No migrations applied yet"
```

**Usage examples:**

```bash
# Apply all pending migrations
make migrate-up

# Rollback last migration (one feature = one rollback)
make migrate-down

# Create new migration for a feature
make migrate-create NAME=add_user_preferences

# Check current version
make migrate-version

# Force version after manual fix (use with caution)
make migrate-force VERSION=5
```

### Documentation Commands (MANDATORY)

All projects with API endpoints MUST include Swagger generation using swaggo:

```makefile
#-------------------------------------------------------
# Documentation Commands
#-------------------------------------------------------

.PHONY: generate-docs
generate-docs: ## Generate Swagger API documentation
	@echo "Generating Swagger documentation..."
	@if ! command -v swag >/dev/null 2>&1; then \
		echo "Error: swag is not installed. Run: make dev-setup"; \
		exit 1; \
	fi
	swag init -g cmd/app/main.go -o api --parseDependency --parseInternal
	@echo "[ok] Swagger documentation generated in api/"

.PHONY: serve-docs
serve-docs: ## Serve Swagger UI locally (requires swagger-ui)
	@echo "Serving Swagger UI at http://localhost:8081"
	@docker run -p 8081:8080 -e SWAGGER_JSON=/api/swagger.json -v $(PWD)/api:/api swaggerapi/swagger-ui
```

**Command parameters:**

| Flag                 | Purpose                                        |
| -------------------- | ---------------------------------------------- |
| `-g cmd/app/main.go` | Entry point file with API metadata annotations |
| `-o api`             | Output directory for generated files           |
| `--parseDependency`  | Parse external dependencies for models         |
| `--parseInternal`    | Parse internal packages for types              |

**Generated files:**

```text
/api
  docs.go         # Go code for embedding (GENERATED - do not edit)
  swagger.json    # OpenAPI spec in JSON (GENERATED - do not edit)
  swagger.yaml    # OpenAPI spec in YAML (GENERATED - do not edit)
```

**⛔ FORBIDDEN:** Editing generated files directly. Always edit the annotations in source code.

### Development Setup Commands (MANDATORY)

All projects MUST include a dev-setup command to install required tools:

```makefile
#-------------------------------------------------------
# Development Setup Commands
#-------------------------------------------------------

.PHONY: dev-setup
dev-setup: ## Install development tools
	@echo "Installing development tools..."

	@# golangci-lint
	@if ! command -v golangci-lint >/dev/null 2>&1; then \
		echo "Installing golangci-lint..."; \
		go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest; \
	else \
		echo "[ok] golangci-lint already installed"; \
	fi

	@# swag (Swagger generator)
	@if ! command -v swag >/dev/null 2>&1; then \
		echo "Installing swag..."; \
		go install github.com/swaggo/swag/cmd/swag@latest; \
	else \
		echo "[ok] swag already installed"; \
	fi

	@# golang-migrate
	@if ! command -v migrate >/dev/null 2>&1; then \
		echo "Installing golang-migrate..."; \
		go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest; \
	else \
		echo "[ok] migrate already installed"; \
	fi

	@# mockgen (for GoMock)
	@if ! command -v mockgen >/dev/null 2>&1; then \
		echo "Installing mockgen..."; \
		go install go.uber.org/mock/mockgen@latest; \
	else \
		echo "[ok] mockgen already installed"; \
	fi

	@echo "[ok] All development tools installed"

.PHONY: check-tools
check-tools: ## Verify all required tools are installed
	@echo "Checking required tools..."
	@command -v go >/dev/null 2>&1 || { echo "❌ go not found"; exit 1; }
	@command -v golangci-lint >/dev/null 2>&1 || { echo "❌ golangci-lint not found"; exit 1; }
	@command -v swag >/dev/null 2>&1 || { echo "❌ swag not found"; exit 1; }
	@command -v migrate >/dev/null 2>&1 || { echo "❌ migrate not found"; exit 1; }
	@command -v mockgen >/dev/null 2>&1 || { echo "❌ mockgen not found"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "❌ docker not found"; exit 1; }
	@echo "[ok] All required tools are installed"
```

**Required tools:**

| Tool            | Purpose             | Installation                                                                          |
| --------------- | ------------------- | ------------------------------------------------------------------------------------- |
| `golangci-lint` | Code linting        | `go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest`               |
| `swag`          | Swagger generation  | `go install github.com/swaggo/swag/cmd/swag@latest`                                   |
| `migrate`       | Database migrations | `go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest` |
| `mockgen`       | Mock generation     | `go install go.uber.org/mock/mockgen@latest`                                          |

### Generate Mocks Command (MANDATORY)

```makefile
#-------------------------------------------------------
# Code Generation Commands
#-------------------------------------------------------

.PHONY: generate
generate: ## Run all code generation (mocks, etc.)
	@echo "Running go generate..."
	@go generate ./...
	@echo "[ok] Code generation completed"

.PHONY: generate-mocks
generate-mocks: ## Generate mock files using mockgen
	@echo "Generating mocks..."
	@go generate ./...
	@echo "[ok] Mocks generated"
```

---

