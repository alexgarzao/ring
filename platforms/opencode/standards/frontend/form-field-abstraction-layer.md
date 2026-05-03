## Form Field Abstraction Layer

### Dual-Mode UI Library Support

⛔ **HARD GATE:** All forms MUST use field abstraction wrappers. Direct input usage is FORBIDDEN.

| Mode | Detection | Components |
|------|-----------|------------|
| **sindarian-ui** (primary) | `@lerianstudio/sindarian-ui` in package.json | FormField, FormItem, FormLabel, FormControl, FormMessage, FormTooltip |
| **shadcn/radix** (fallback) | Components not available in sindarian-ui | Place in project `components/ui/` using shadcn/ui + Radix primitives |

### Field Wrapper Components (MANDATORY)

| Component | Purpose | Required Props |
|-----------|---------|----------------|
| `InputField` | Text, number, email, password inputs | name, label, description?, placeholder?, tooltip? |
| `SelectField` | Single select dropdown | name, label, options, placeholder? |
| `ComboBoxField` | Searchable select with filtering | name, label, options, onSearch?, placeholder? |
| `MultiSelectField` | Multiple selection | name, label, options, maxItems? |
| `TextAreaField` | Multi-line text input | name, label, rows?, maxLength? |
| `CheckboxField` | Boolean checkbox | name, label, description? |
| `SwitchField` | Toggle switch | name, label, description? |
| `DatePickerField` | Date selection | name, label, minDate?, maxDate? |

### sindarian-ui Mode Implementation

```tsx
import {
    FormField,
    FormItem,
    FormLabel,
    FormControl,
    FormDescription,
    FormMessage,
    FormTooltip,
    Input,
} from '@lerianstudio/sindarian-ui';
import { useFormContext } from 'react-hook-form';

interface InputFieldProps {
    name: string;
    label: string;
    description?: string;
    placeholder?: string;
    tooltip?: string;
    type?: 'text' | 'email' | 'password' | 'number';
}

export function InputField({
    name,
    label,
    description,
    placeholder,
    tooltip,
    type = 'text',
}: InputFieldProps) {
    const { control } = useFormContext();

    return (
        <FormField
            control={control}
            name={name}
            render={({ field }) => (
                <FormItem>
                    <FormLabel>
                        {label}
                        {tooltip && <FormTooltip>{tooltip}</FormTooltip>}
                    </FormLabel>
                    <FormControl>
                        <Input
                            type={type}
                            placeholder={placeholder}
                            {...field}
                        />
                    </FormControl>
                    {description && <FormDescription>{description}</FormDescription>}
                    <FormMessage />
                </FormItem>
            )}
        />
    );
}
```

### Vanilla Mode Implementation (shadcn/ui)

```tsx
import {
    FormField,
    FormItem,
    FormLabel,
    FormControl,
    FormMessage,
    FormDescription,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { useFormContext } from 'react-hook-form';
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from '@/components/ui/tooltip';
import { HelpCircle } from 'lucide-react';

interface InputFieldProps {
    name: string;
    label: string;
    description?: string;
    placeholder?: string;
    tooltip?: string;
    type?: 'text' | 'email' | 'password' | 'number';
}

export function InputField({
    name,
    label,
    description,
    placeholder,
    tooltip,
    type = 'text',
}: InputFieldProps) {
    const { control } = useFormContext();

    return (
        <FormField
            control={control}
            name={name}
            render={({ field }) => (
                <FormItem>
                    <FormLabel className="flex items-center gap-1">
                        {label}
                        {tooltip && (
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <HelpCircle className="h-4 w-4 text-muted-foreground" />
                                </TooltipTrigger>
                                <TooltipContent>{tooltip}</TooltipContent>
                            </Tooltip>
                        )}
                    </FormLabel>
                    <FormControl>
                        <Input
                            type={type}
                            placeholder={placeholder}
                            {...field}
                        />
                    </FormControl>
                    {description && <FormDescription>{description}</FormDescription>}
                    <FormMessage />
                </FormItem>
            )}
        />
    );
}
```

### Form Usage Pattern

```tsx
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { InputField, SelectField } from '@/components/fields';

const schema = z.object({
    name: z.string().min(1, 'Name is required'),
    email: z.string().email('Invalid email'),
    role: z.enum(['admin', 'user', 'guest']),
});

type FormData = z.infer<typeof schema>;

function CreateUserForm() {
    const form = useForm<FormData>({
        resolver: zodResolver(schema),
        defaultValues: {
            name: '',
            email: '',
            role: 'user',
        },
    });

    const onSubmit = (data: FormData) => {
        // Submit logic
    };

    return (
        <FormProvider {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)}>
                <InputField
                    name="name"
                    label="Name"
                    placeholder="Enter your name"
                    tooltip="Your full legal name"
                />
                <InputField
                    name="email"
                    label="Email"
                    type="email"
                    placeholder="you@example.com"
                />
                <SelectField
                    name="role"
                    label="Role"
                    options={[
                        { value: 'admin', label: 'Administrator' },
                        { value: 'user', label: 'User' },
                        { value: 'guest', label: 'Guest' },
                    ]}
                />
                <Button type="submit">Create User</Button>
            </form>
        </FormProvider>
    );
}
```

### Anti-Patterns (FORBIDDEN)

| Pattern | Why Forbidden | Correct Alternative |
|---------|---------------|---------------------|
| `<Input {...register('name')} />` directly | No label, no error display, no accessibility | Use `<InputField name="name" label="Name" />` |
| Inline error handling | Inconsistent UX | Use FormMessage from wrapper |
| Manual FormField for each input | Code duplication | Use pre-built field wrappers |
| Different field patterns per form | Inconsistent UX | Use shared field components |

---

