## Form Patterns

### React Hook Form + Zod

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Schema
const createUserSchema = z.object({
    name: z.string().min(1, 'Name is required').max(100),
    email: z.string().email('Invalid email'),
    role: z.enum(['admin', 'user', 'guest']),
    notifications: z.boolean().default(true),
});

type CreateUserInput = z.infer<typeof createUserSchema>;

// Component
function CreateUserForm() {
    const {
        register,
        handleSubmit,
        formState: { errors, isSubmitting },
    } = useForm<CreateUserInput>({
        resolver: zodResolver(createUserSchema),
        defaultValues: {
            notifications: true,
        },
    });

    const createUser = useCreateUser();

    const onSubmit = async (data: CreateUserInput) => {
        await createUser.mutateAsync(data);
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)}>
            <Input
                {...register('name')}
                error={errors.name?.message}
            />
            <Input
                {...register('email')}
                error={errors.email?.message}
            />
            <Select {...register('role')}>
                <option value="user">User</option>
                <option value="admin">Admin</option>
            </Select>
            <Button type="submit" loading={isSubmitting}>
                Create User
            </Button>
        </form>
    );
}
```

---

