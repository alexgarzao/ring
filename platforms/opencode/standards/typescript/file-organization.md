## File Organization (MANDATORY)

**Single Responsibility per File:** Each file MUST represent ONE cohesive concept.

### Rules

| Rule | Description |
|------|-------------|
| **One concept per file** | A file groups functions/types for a single domain concept |
| **Max 1000 lines (hard block at 1500)** | Cohesion judgment applies — see shared-patterns/file-size-enforcement.md |
| **File name = content** | `user-validator.ts` MUST only contain user validation logic |
| **One class per file** | Each class gets its own file |
| **Co-locate types with usage** | Types used by one file live in that file, shared types in `/types` |

### Examples

```typescript
// ❌ BAD - transaction-service.ts (1200 lines, multiple concerns — fragmentable without artificial boundaries)
export class TransactionService {
    constructor(
        private readonly repo: TransactionRepository,
        private readonly logger: Logger,
    ) {}

    // CRUD operations
    async createTransaction(input: CreateTransactionInput): Promise<Transaction> { ... }
    async updateTransaction(id: string, input: UpdateTransactionInput): Promise<Transaction> { ... }
    async getTransaction(id: string): Promise<Transaction> { ... }
    async listTransactions(filter: TransactionFilter): Promise<Transaction[]> { ... }

    // Validation (different concern)
    async validateAmount(amount: number, currency: string): Promise<void> { ... }
    async validateParties(from: string, to: string): Promise<void> { ... }

    // Fee calculation (different concern)
    async calculateFees(amount: number, type: TransactionType): Promise<Fee> { ... }
    async applyExchangeRate(amount: number, from: string, to: string): Promise<number> { ... }

    // Export (different concern)
    async generateReceipt(id: string): Promise<Receipt> { ... }
    async exportToOFX(id: string): Promise<Buffer> { ... }
}
```

```typescript
// ✅ GOOD - Split by responsibility

// create-transaction.command.ts (~80 lines) - Write operation
export class CreateTransactionCommand {
    constructor(
        private readonly repo: TransactionRepository,
        private readonly validator: TransactionValidator,
        private readonly logger: Logger,
    ) {}

    async execute(input: CreateTransactionInput): Promise<Transaction> { ... }
}

// update-transaction.command.ts (~70 lines) - Write operation
export class UpdateTransactionCommand {
    constructor(
        private readonly repo: TransactionRepository,
        private readonly logger: Logger,
    ) {}

    async execute(id: string, input: UpdateTransactionInput): Promise<Transaction> { ... }
}

// get-transaction.query.ts (~50 lines) - Read operation
export class GetTransactionQuery {
    constructor(private readonly repo: TransactionRepository) {}

    async execute(id: string): Promise<Transaction> { ... }
}

// list-transactions.query.ts (~60 lines) - Read operation
export class ListTransactionsQuery {
    constructor(private readonly repo: TransactionRepository) {}

    async execute(filter: TransactionFilter): Promise<Transaction[]> { ... }
}

// transaction-validator.ts (~70 lines) - Validation
export function validateAmount(amount: number, currency: string): void { ... }
export function validateParties(from: string, to: string): void { ... }

// transaction-fees.ts (~60 lines) - Fee calculation
export function calculateFees(amount: number, type: TransactionType): Fee { ... }
export function applyExchangeRate(amount: number, from: string, to: string): number { ... }

// transaction-export.ts (~80 lines) - Export/reporting
export function generateReceipt(id: string): Promise<Receipt> { ... }
export function exportToOFX(id: string): Promise<Buffer> { ... }
```

### Signs a File Needs Splitting

| Sign | Action |
|------|--------|
| File exceeds 1000 lines (hard block at 1500) | Apply cohesion judgment; split at responsibility boundaries if fragmentable. See shared-patterns/file-size-enforcement.md |
| Multiple exported classes | One class per file |
| `// ===== Section =====` separator comments | Each section becomes its own file |
| Mix of commands + queries in one service | Split into separate command/query files |
| File name requires "and" to describe content | Split into separate files |
| More than 5 unrelated exports | Group related exports into separate modules |
| Types block at top exceeds 50 lines | Extract to dedicated `types.ts` or co-located type file |

---

