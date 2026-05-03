## Error Handling

### Rules

```go
// always check errors
if err != nil {
    return fmt.Errorf("context: %w", err)
}

// always wrap errors with context
if err != nil {
    return fmt.Errorf("failed to create user %s: %w", userID, err)
}

// Use custom error types for domain errors
var ErrUserNotFound = errors.New("user not found")

// Check specific errors with errors.Is
if errors.Is(err, ErrUserNotFound) {
    return nil, status.Error(codes.NotFound, "user not found")
}
```

### Forbidden

```go
// never use panic for business logic
panic(err) // FORBIDDEN

// never ignore errors
result, _ := doSomething() // FORBIDDEN

// never return nil error without checking
return nil, nil // SUSPICIOUS - check if error is possible
```

---

