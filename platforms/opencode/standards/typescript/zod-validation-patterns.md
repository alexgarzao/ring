## Zod Validation Patterns

### Schema Definition

```typescript
import { z } from 'zod';

// Reusable primitives
const emailSchema = z.string().email();
const uuidSchema = z.string().uuid();
const moneySchema = z.number().positive().multipleOf(0.01);

// Compose schemas
const createUserSchema = z.object({
    email: emailSchema,
    name: z.string().min(1).max(100),
    role: z.enum(['admin', 'user', 'guest']),
    preferences: z.object({
        theme: z.enum(['light', 'dark']).default('light'),
        notifications: z.boolean().default(true),
    }).optional(),
});

// Infer TypeScript type from schema
type CreateUserInput = z.infer<typeof createUserSchema>;

// Runtime validation
function createUser(input: unknown): CreateUserInput {
    return createUserSchema.parse(input); // Throws on invalid
}

// Safe parsing (returns Result-like)
function validateUser(input: unknown) {
    const result = createUserSchema.safeParse(input);
    if (!result.success) {
        return { error: result.error.flatten() };
    }
    return { data: result.data };
}
```

### Schema Composition

```typescript
// Base schemas
const timestampSchema = z.object({
    createdAt: z.date(),
    updatedAt: z.date(),
});

const identifiableSchema = z.object({
    id: uuidSchema,
});

// Compose for full entity
const userSchema = identifiableSchema
    .merge(timestampSchema)
    .extend({
        email: emailSchema,
        name: z.string(),
    });
```

---

