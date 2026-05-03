## Containers

### Dockerfile Best Practices

```dockerfile
# Multi-stage build for minimal images
FROM golang:1.22-alpine AS builder

WORKDIR /app

# Cache dependencies
COPY go.mod go.sum ./
RUN go mod download

# Build
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/server ./cmd/api

# Production image
FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=builder /app/server /server

USER nonroot:nonroot

EXPOSE 8080

ENTRYPOINT ["/server"]
```

### Image Guidelines

| Guideline              | Reason                 |
| ---------------------- | ---------------------- |
| Use multi-stage builds | Smaller images         |
| Use distroless/alpine  | Minimal attack surface |
| Run as non-root        | Security               |
| Pin versions           | Reproducibility        |
| Use .dockerignore      | Smaller context        |

### Docker Compose (Local Dev)

**MANDATORY:** Use `.env` file for environment variables instead of inline definitions.

```yaml
# docker-compose.yml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  db:
    image: postgres:15-alpine
    env_file:
      - .env
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

#### .env File Structure

```bash
# .env (add to .gitignore)

# Application
ENV_NAME=local
LOG_LEVEL=debug
SERVER_ADDRESS=:8080

# PostgreSQL
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=app
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Telemetry
ENABLE_TELEMETRY=false
```

| Guideline                  | Reason                             |
| -------------------------- | ---------------------------------- |
| Use `env_file` directive   | Centralized configuration          |
| Add `.env` to `.gitignore` | Prevent secrets in version control |
| Provide `.env.example`     | Document required variables        |
| Use consistent naming      | Match application config struct    |

---

