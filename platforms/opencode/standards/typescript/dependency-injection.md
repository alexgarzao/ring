## Dependency Injection

### Using TSyringe

```typescript
import { container, injectable, inject } from 'tsyringe';

// Define interface
interface UserRepository {
    findById(id: string): Promise<User | null>;
    save(user: User): Promise<void>;
}

// Implement
@injectable()
class PostgresUserRepository implements UserRepository {
    constructor(
        @inject('Database') private db: Database
    ) {}

    async findById(id: string): Promise<User | null> {
        return this.db.user.findUnique({ where: { id } });
    }

    async save(user: User): Promise<void> {
        await this.db.user.upsert({ where: { id: user.id }, ...user });
    }
}

// Service using repository
@injectable()
class UserService {
    constructor(
        @inject('UserRepository') private repo: UserRepository
    ) {}

    async getUser(id: string): Promise<User> {
        const user = await this.repo.findById(id);
        if (!user) throw new NotFoundError('User not found');
        return user;
    }
}

// Register in container
container.register('Database', { useClass: PrismaDatabase });
container.register('UserRepository', { useClass: PostgresUserRepository });

// Resolve
const userService = container.resolve(UserService);
```

---

