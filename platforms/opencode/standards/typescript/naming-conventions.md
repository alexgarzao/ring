## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files | kebab-case | `user-service.ts` |
| Interfaces | PascalCase | `UserRepository` |
| Types | PascalCase | `CreateUserInput` |
| Functions | camelCase | `createUser` |
| Constants | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| Enums | PascalCase + UPPER_SNAKE values | `UserRole.ADMIN` |

---

## Directory Structure

The directory structure follows the **Lerian pattern** - a simplified hexagonal architecture without explicit DDD folders.

```
/src
  /bootstrap           # Application initialization
    config.ts
    server.ts
    service.ts
  /services            # Business logic
    /command           # Write operations (use cases)
    /query             # Read operations (use cases)
  /adapters            # Infrastructure implementations
    /http/in           # HTTP handlers + routes
    /grpc/in           # gRPC handlers (if needed)
    /postgres          # PostgreSQL repositories
    /mongodb           # MongoDB repositories
    /redis             # Redis repositories
    /rabbitmq          # RabbitMQ producers/consumers
  /lib                 # Utilities
    db.ts
    logger.ts
  /types               # Shared types and models
    index.ts
/tests
  /unit
  /integration
```

**Key differences from traditional DDD:**
- **No `/src/domain` folder** - Business entities live in `/src/types` or within service files
- **Services are the core** - `/src/services` contains all business logic (command/query pattern)
- **Adapters are flat** - Database repositories are organized by technology, not by domain

---

