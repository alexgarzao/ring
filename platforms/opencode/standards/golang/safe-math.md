## Safe Math (commons/safe)

Financial calculations **MUST** use `csafe` to prevent panics on zero division.

```go
// MANDATORY for financial calculations
result, err := csafe.Divide(numerator, denominator)
if err != nil {
    // err == csafe.ErrDivisionByZero
}

// With rounding
result, err := csafe.DivideRound(numerator, denominator, 2)

// Fallback to zero (for display, not transactions)
result := csafe.DivideOrZero(numerator, denominator)
```

---

