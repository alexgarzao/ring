## File Organization (MANDATORY)

**Single Responsibility per File:** Each component file MUST represent ONE UI concern.

### Rules

| Rule | Description |
|------|-------------|
| **One component per file** | A file exports ONE primary component |
| **Max 200 lines per component file** | If longer, extract sub-components or hooks |
| **Co-locate related files** | Component, hook, types, test in same feature folder |
| **Hooks in separate files** | Custom hooks that exceed 20 lines get their own file |
| **Separate data from presentation** | Container (data-fetching) and presentational components split |

### Examples

```tsx
// ❌ BAD - UserDashboard.tsx (400 lines, mixed concerns)
export function UserDashboard() {
    // 30 lines of state management
    const [users, setUsers] = useState<User[]>([]);
    const [filters, setFilters] = useState<UserFilters>({});
    const [sortConfig, setSortConfig] = useState<SortConfig>({});
    const [isExportModalOpen, setIsExportModalOpen] = useState(false);

    // 40 lines of data fetching
    useEffect(() => {
        fetchUsers(filters).then(setUsers);
    }, [filters]);

    // 50 lines of event handlers
    const handleSort = (column: string) => { ... };
    const handleFilter = (key: string, value: unknown) => { ... };
    const handleExport = (format: string) => { ... };
    const handleBulkAction = (action: string, ids: string[]) => { ... };

    // 280 lines of mixed JSX (filters + table + pagination + modal)
    return (
        <div>
            {/* 80 lines of filter panel */}
            {/* 100 lines of data table */}
            {/* 50 lines of pagination */}
            {/* 50 lines of export modal */}
        </div>
    );
}
```

```tsx
// ✅ GOOD - Split by concern

// UserDashboard.tsx (~50 lines) - Composition root
export function UserDashboard() {
    const { users, pagination, isLoading } = useUsers();
    const { filters, updateFilter, resetFilters } = useUserFilters();

    return (
        <div>
            <UserFilters filters={filters} onChange={updateFilter} onReset={resetFilters} />
            <UserTable users={users} isLoading={isLoading} />
            <Pagination {...pagination} />
        </div>
    );
}

// useUsers.ts (~60 lines) - Data fetching hook
export function useUsers(filters?: UserFilters) {
    return useQuery({
        queryKey: ['users', filters],
        queryFn: () => fetchUsers(filters),
    });
}

// useUserFilters.ts (~40 lines) - Filter state hook
export function useUserFilters() {
    const [filters, setFilters] = useState<UserFilters>({});

    const updateFilter = useCallback((key: string, value: unknown) => {
        setFilters((prev) => ({ ...prev, [key]: value }));
    }, []);

    const resetFilters = useCallback(() => setFilters({}), []);

    return { filters, updateFilter, resetFilters };
}

// UserFilters.tsx (~70 lines) - Filter panel component
interface UserFiltersProps {
    filters: UserFilters;
    onChange: (key: string, value: unknown) => void;
    onReset: () => void;
}

export function UserFilters({ filters, onChange, onReset }: UserFiltersProps) {
    return (
        <div className="flex gap-4">
            <InputField value={filters.name} onChange={(v) => onChange('name', v)} />
            <SelectField value={filters.role} onChange={(v) => onChange('role', v)} options={roleOptions} />
            <Button variant="ghost" onClick={onReset}>Reset</Button>
        </div>
    );
}

// UserTable.tsx (~80 lines) - Table component
interface UserTableProps {
    users: User[];
    isLoading: boolean;
}

export function UserTable({ users, isLoading }: UserTableProps) {
    if (isLoading) return <TableSkeleton />;

    return (
        <DataTable columns={userColumns} data={users} />
    );
}
```

### Signs a File Needs Splitting

| Sign | Action |
|------|--------|
| Component file exceeds 200 lines | Extract sub-components or hooks |
| More than 3 `useState`/`useEffect` in one file | Extract to custom hook |
| JSX return exceeds 100 lines | Extract child components |
| File mixes data fetching and presentation | Split container and presentational components |
| Multiple `useQuery`/`useMutation` in one file | Extract to dedicated hook files |
| Component accepts more than 5 props | Consider composition or compound component pattern |

---

