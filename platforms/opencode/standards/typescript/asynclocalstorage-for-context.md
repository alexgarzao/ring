## AsyncLocalStorage for Context

```typescript
import { AsyncLocalStorage } from 'async_hooks';

// Define context type
interface RequestContext {
    requestId: string;
    userId?: string;
    tenantId?: string;
}

// Create storage
const asyncLocalStorage = new AsyncLocalStorage<RequestContext>();

// Get current context
export function getContext(): RequestContext {
    const ctx = asyncLocalStorage.getStore();
    if (!ctx) throw new Error('No context available');
    return ctx;
}

// Middleware to set context
export function contextMiddleware(req: Request, res: Response, next: NextFunction) {
    const context: RequestContext = {
        requestId: req.headers['x-request-id'] as string || crypto.randomUUID(),
        userId: req.user?.id,
        tenantId: req.headers['x-tenant-id'] as string,
    };

    asyncLocalStorage.run(context, () => next());
}

// Usage anywhere in call chain
async function processOrder(orderId: string) {
    const { tenantId, userId } = getContext();
    logger.info('Processing order', { orderId, tenantId, userId });
    // ...
}
```

---

