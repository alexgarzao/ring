## Function Design (MANDATORY)

**Single Responsibility Principle (SRP):** Each function MUST have exactly ONE responsibility.

### Rules

| Rule | Description |
|------|-------------|
| **One responsibility per function** | A function should do ONE thing and do it well |
| **Max 20-30 lines** | If longer, break into smaller functions |
| **One level of abstraction** | Don't mix high-level and low-level operations |
| **Descriptive names** | Function name should describe its single responsibility |

### Examples

```typescript
// ❌ BAD - Multiple responsibilities
async function processOrder(order: Order): Promise<void> {
    // Validate order
    if (!order.items?.length) {
        throw new Error('no items');
    }
    // Calculate total
    let total = 0;
    for (const item of order.items) {
        total += item.price * item.quantity;
    }
    // Apply discount
    if (order.couponCode) {
        total = total * 0.9;
    }
    // Save to database
    await db.orders.save(order);
    // Send email
    await sendEmail(order.customerEmail, 'Order confirmed');
}

// ✅ GOOD - Single responsibility per function
async function processOrder(order: Order): Promise<void> {
    validateOrder(order);
    const total = calculateTotal(order.items);
    const finalTotal = applyDiscount(total, order.couponCode);
    await saveOrder(order, finalTotal);
    await notifyCustomer(order.customerEmail);
}

function validateOrder(order: Order): void {
    if (!order.items?.length) {
        throw new ValidationError('Order must have items');
    }
}

function calculateTotal(items: OrderItem[]): number {
    return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

function applyDiscount(total: number, couponCode?: string): number {
    return couponCode ? total * 0.9 : total;
}
```

### Signs a Function Has Multiple Responsibilities

| Sign | Action |
|------|--------|
| Multiple `// section` comments | Split at comment boundaries |
| "and" in function name | Split into separate functions |
| More than 3 parameters | Consider parameter object or splitting |
| Nested conditionals > 2 levels | Extract inner logic to functions |
| Function does validation and processing | Separate validation function |

---

