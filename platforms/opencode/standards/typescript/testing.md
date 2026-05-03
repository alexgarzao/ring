## Testing

### Type-Safe Mocks

```typescript
import { vi, describe, it, expect } from 'vitest';

// Create typed mock
const mockUserRepository: jest.Mocked<UserRepository> = {
    findById: vi.fn(),
    save: vi.fn(),
};

describe('UserService', () => {
    it('returns user when found', async () => {
        // Arrange
        const user: User = { id: 'usr_123', name: 'John', email: 'john@example.com' };
        mockUserRepository.findById.mockResolvedValue(user);

        const service = new UserService(mockUserRepository);

        // Act
        const result = await service.getUser('usr_123');

        // Assert
        expect(result).toEqual(user);
        expect(mockUserRepository.findById).toHaveBeenCalledWith('usr_123');
    });

    it('throws NotFoundError when user not found', async () => {
        // Arrange
        mockUserRepository.findById.mockResolvedValue(null);

        const service = new UserService(mockUserRepository);

        // Act & Assert
        await expect(service.getUser('usr_999')).rejects.toThrow(NotFoundError);
    });
});
```

### Type-Safe Fixtures

```typescript
// fixtures/user.ts
import { faker } from '@faker-js/faker';

export function createUserFixture(overrides: Partial<User> = {}): User {
    return {
        id: `usr_${faker.string.uuid()}`,
        name: faker.person.fullName(),
        email: faker.internet.email(),
        createdAt: faker.date.past(),
        updatedAt: new Date(),
        ...overrides,
    };
}

// Usage in tests
const user = createUserFixture({ name: 'Test User' });
```

### Edge Case Coverage (MANDATORY)

**Every acceptance criterion MUST have edge case tests beyond the happy path.**

| AC Type | Required Edge Cases | Minimum Count |
|---------|---------------------|---------------|
| Input validation | null, undefined, empty string, boundary values, invalid format, special chars | 3+ |
| CRUD operations | not found, duplicate, concurrent access, large payload | 3+ |
| Business logic | zero, negative, overflow, boundary conditions, invalid state | 3+ |
| Error handling | timeout, connection refused, invalid response, retry exhausted | 2+ |
| Authentication | expired token, invalid token, missing token, revoked token | 2+ |

**Edge Case Test Pattern:**

```typescript
describe('UserService', () => {
    describe('createUser', () => {
        // Happy path
        it('creates user with valid input', async () => {
            const result = await service.createUser(validInput);
            expect(result.id).toBeDefined();
        });

        // Edge cases (MANDATORY - minimum 3)
        it('throws ValidationError for null input', async () => {
            await expect(service.createUser(null as any)).rejects.toThrow(ValidationError);
        });

        it('throws ValidationError for empty email', async () => {
            await expect(service.createUser({ ...validInput, email: '' })).rejects.toThrow(ValidationError);
        });

        it('throws ValidationError for invalid email format', async () => {
            await expect(service.createUser({ ...validInput, email: 'invalid' })).rejects.toThrow(ValidationError);
        });

        it('throws ValidationError for email exceeding max length', async () => {
            const longEmail = 'a'.repeat(256) + '@test.com';
            await expect(service.createUser({ ...validInput, email: longEmail })).rejects.toThrow(ValidationError);
        });

        it('throws DuplicateError for existing email', async () => {
            mockRepo.findByEmail.mockResolvedValue(existingUser);
            await expect(service.createUser(validInput)).rejects.toThrow(DuplicateError);
        });
    });
});
```

**Anti-Pattern (FORBIDDEN):**

```typescript
// ❌ WRONG: Only happy path
describe('UserService', () => {
    it('creates user', async () => {
        const result = await service.createUser(validInput);
        expect(result).toBeDefined();  // No edge cases = incomplete test
    });
});
```

---

