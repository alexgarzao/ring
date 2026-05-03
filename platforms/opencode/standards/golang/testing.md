## Testing

### Table-Driven Tests (MANDATORY)

```go
func TestCreateUser(t *testing.T) {
    tests := []struct {
        name    string
        input   CreateUserInput
        want    *User
        wantErr error
    }{
        {
            name:  "valid user",
            input: CreateUserInput{Name: "John", Email: "john@example.com"},
            want:  &User{Name: "John", Email: "john@example.com"},
        },
        {
            name:    "invalid email",
            input:   CreateUserInput{Name: "John", Email: "invalid"},
            wantErr: ErrInvalidEmail,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := CreateUser(tt.input)

            if tt.wantErr != nil {
                require.ErrorIs(t, err, tt.wantErr)
                return
            }

            require.NoError(t, err)
            assert.Equal(t, tt.want.Name, got.Name)
        })
    }
}
```

### Test Naming Convention

```text
Test{Unit}_{Scenario}_{ExpectedResult}

Examples:
- TestOrderService_CreateOrder_WithValidItems_ReturnsOrder
- TestOrderService_CreateOrder_WithEmptyItems_ReturnsError
- TestMoney_Add_SameCurrency_ReturnsSum
```

### Edge Case Coverage (MANDATORY)

**Every acceptance criterion MUST have edge case tests beyond the happy path.**

| AC Type | Required Edge Cases | Minimum Count |
|---------|---------------------|---------------|
| Input validation | nil, empty string, boundary values, invalid format, special chars, max length | 3+ |
| CRUD operations | not found, duplicate key, concurrent modification, large payload | 3+ |
| Business logic | zero value, negative numbers, overflow, boundary conditions, invalid state | 3+ |
| Error handling | context timeout, connection refused, invalid response, retry exhausted | 2+ |
| Authentication | expired token, invalid signature, missing claims, revoked token | 2+ |

**Table-Driven Edge Cases Pattern:**

```go
func TestUserService_CreateUser(t *testing.T) {
    tests := []struct {
        name    string
        input   CreateUserInput
        wantErr error
    }{
        // Happy path
        {name: "valid user", input: validInput(), wantErr: nil},
        
        // Edge cases (MANDATORY - minimum 3)
        {name: "nil input", input: CreateUserInput{}, wantErr: ErrInvalidInput},
        {name: "empty email", input: CreateUserInput{Name: "John", Email: ""}, wantErr: ErrEmailRequired},
        {name: "invalid email format", input: CreateUserInput{Name: "John", Email: "invalid"}, wantErr: ErrInvalidEmail},
        {name: "email too long", input: CreateUserInput{Name: "John", Email: strings.Repeat("a", 256) + "@test.com"}, wantErr: ErrEmailTooLong},
        {name: "name with special chars", input: CreateUserInput{Name: "<script>", Email: "test@test.com"}, wantErr: ErrInvalidName},
    }
    // ... test execution
}
```

**Anti-Pattern (FORBIDDEN):**

```go
// ❌ WRONG: Only happy path
func TestUserService_CreateUser(t *testing.T) {
    result, err := service.CreateUser(validInput())
    require.NoError(t, err)  // No edge cases = incomplete test
}
```

### Mock Generation (GoMock - MANDATORY)

```go
// GoMock is the MANDATORY mock framework for all Go projects
//go:generate mockgen -source=repository.go -destination=mocks/mock_repository.go -package=mocks

// For interface in external package:
//go:generate mockgen -destination=mocks/mock_service.go -package=mocks github.com/example/pkg Service
```

---

