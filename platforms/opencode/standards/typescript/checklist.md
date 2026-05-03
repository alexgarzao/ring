## Checklist

Before submitting TypeScript code, verify:

### Type Safety
- [ ] No `any` types (use `unknown` with narrowing)
- [ ] Strict mode enabled in tsconfig.json
- [ ] Zod validation for all external input
- [ ] Branded types for IDs
- [ ] Discriminated unions for state machines
- [ ] Type inference used where possible (avoid redundant annotations)
- [ ] No `@ts-ignore` or `@ts-expect-error` without explanation

### Error Handling
- [ ] Error classes extend base AppError
- [ ] All async functions have proper error handling
- [ ] Result type used for operations that can fail

### DDD (if enabled)
- [ ] Entities have identity comparison (`equals` method)
- [ ] Value Objects are immutable (private constructor, factory methods)
- [ ] Aggregates enforce invariants before state changes
- [ ] Domain Events emitted for significant state changes
- [ ] Repository interfaces defined in domain layer
- [ ] No infrastructure dependencies in domain layer
