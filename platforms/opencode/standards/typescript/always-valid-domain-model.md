## Always-Valid Domain Model (MANDATORY)

**HARD GATE:** All domain entities MUST use the Always-Valid Domain Model pattern. Anemic models (plain objects without validation) are FORBIDDEN.

### Why This Pattern Is Mandatory

| Problem with Anemic Models | Impact |
|---------------------------|--------|
| Objects can exist in invalid state | Bugs propagate through system |
| Validation scattered across codebase | Duplication, inconsistency |
| Business rules not enforced at creation | Invalid data reaches database |
| No single source of truth for validity | Every consumer must re-validate |

### The Pattern

**Core Principle:** An entity can NEVER exist in an invalid state. Validation happens in the factory, not later.

```typescript
// ✅ CORRECT: Always-Valid Domain Model
class Rule {
    private constructor(
        private readonly _id: string,
        private readonly _name: string,
        private readonly _expression: string,
        private readonly _createdAt: Date,
    ) {}

    // Factory method MUST validate and return Result
    static create(name: string, expression: string): Result<Rule, ValidationError> {
        // Validation at construction time
        if (!name || name.trim().length === 0) {
            return err(new ValidationError('name is required'));
        }
        if (name.length > 255) {
            return err(new ValidationError('name exceeds 255 characters'));
        }
        if (!isValidExpression(expression)) {
            return err(new ValidationError('invalid expression syntax'));
        }

        return ok(new Rule(
            crypto.randomUUID(),
            name.trim(),
            expression,
            new Date(),
        ));
    }

    // Getters expose immutable data
    get id(): string { return this._id; }
    get name(): string { return this._name; }
    get expression(): string { return this._expression; }
}
```

```typescript
// ❌ FORBIDDEN: Anemic Model (validation elsewhere)
interface Rule {
    id: string;
    name: string;      // Can be empty - invalid!
    expression: string; // Can be invalid - no validation!
}

// ❌ FORBIDDEN: Factory without validation
function createRule(name: string, expression: string): Rule {
    return {
        id: crypto.randomUUID(),
        name,        // No validation!
        expression,  // No validation!
    };
}
```

### Requirements

| Requirement | Description |
|-------------|-------------|
| **Factory returns Result** | `Entity.create(...): Result<Entity, Error>` - MUST return error if invalid |
| **Private constructor** | Prevent direct instantiation with `new` |
| **Readonly properties** | Use `readonly` or getters to prevent mutation |
| **No Setters** | Mutation through domain methods that validate |
| **Invariants enforced** | Business rules validated at construction |

### Mutation Pattern

When entities need to change state, use domain methods that validate:

```typescript
// ✅ CORRECT: Mutation with validation
class Rule {
    // ...

    updateExpression(newExpression: string): Result<void, ValidationError> {
        if (!isValidExpression(newExpression)) {
            return err(new ValidationError('invalid expression syntax'));
        }
        // TypeScript: use Object.assign or create new instance for immutability
        Object.assign(this, { _expression: newExpression });
        return ok(undefined);
    }
}

// ❌ FORBIDDEN: Direct property assignment
rule.expression = 'invalid!!!';  // Compilation error (readonly)
```

### Reconstruction from Database

When loading from database, use a separate reconstruction method:

```typescript
// For repository use ONLY - reconstructs from trusted storage
static reconstruct(
    id: string,
    name: string,
    expression: string,
    createdAt: Date,
): Rule {
    // Skip validation - data is from trusted storage
    return new Rule(id, name, expression, createdAt);
}
```

**Note:** `reconstruct` methods skip validation because data is from trusted storage (already validated at creation).

### Integration with HTTP Layer

HTTP handlers still use Zod for input validation, but MUST create domain entities via factories:

```typescript
// Zod schema - validation at boundary
const createRuleSchema = z.object({
    name: z.string().min(1).max(255),
    expression: z.string().min(1),
});

// Handler creates domain entity
async function createRule(req: Request): Promise<Response> {
    // Boundary validation
    const parsed = createRuleSchema.safeParse(req.body);
    if (!parsed.success) {
        return errorResponse(parsed.error);
    }

    // Domain entity creation - additional business validation
    const ruleResult = Rule.create(parsed.data.name, parsed.data.expression);
    if (ruleResult.isErr()) {
        return errorResponse(ruleResult.error);
    }

    // ...
}
```

### Result Type Pattern

Use a Result type for operations that can fail:

```typescript
type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };

function ok<T>(value: T): Result<T, never> {
    return { ok: true, value };
}

function err<E>(error: E): Result<never, E> {
    return { ok: false, error };
}

// Usage
const result = Rule.create(name, expression);
if (result.ok) {
    const rule = result.value;
} else {
    const error = result.error;
}
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Zod validation at boundary is enough" | Boundary validation is for input format. Domain validation is for business rules. | **Use both: Zod validation + factory validation** |
| "Adds boilerplate" | Invalid objects cause more work debugging than factories. | **Write the factory. It's an investment.** |
| "We trust our code" | Every consumer must remember to validate. Humans forget. | **Enforce at construction. Forget-proof.** |
| "Performance overhead" | Validation once at creation vs checking everywhere. | **Single validation is MORE efficient** |
| "Existing code doesn't do this" | Technical debt. Refactor when touching the code. | **New code MUST follow. Refactor gradually.** |
| "Plain interfaces are fine for DTOs" | DTOs are fine as plain objects. Domain entities are NOT. | **Distinguish DTO from Domain Entity** |

### Checklist

- [ ] All domain entities use `private constructor` + `static create()` factory
- [ ] Factories return `Result<Entity, Error>` - never throw
- [ ] Properties are `readonly` or accessed via getters
- [ ] Mutation through validated methods only
- [ ] Reconstruct methods for database loading
- [ ] No direct object instantiation outside factories

---

