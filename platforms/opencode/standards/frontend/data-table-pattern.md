## Data Table Pattern

### TanStack Table with Pagination

```tsx
// src/components/data-table.tsx
'use client';

import {
    ColumnDef,
    flexRender,
    getCoreRowModel,
    useReactTable,
    getPaginationRowModel,
    SortingState,
    getSortedRowModel,
} from '@tanstack/react-table';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { useState } from 'react';

interface DataTableProps<TData, TValue> {
    columns: ColumnDef<TData, TValue>[];
    data: TData[];
    pageCount?: number;
    pagination?: {
        page: number;
        pageSize: number;
        onPageChange: (page: number) => void;
        onPageSizeChange: (size: number) => void;
    };
    isLoading?: boolean;
}

export function DataTable<TData, TValue>({
    columns,
    data,
    pageCount,
    pagination,
    isLoading,
}: DataTableProps<TData, TValue>) {
    const [sorting, setSorting] = useState<SortingState>([]);

    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        onSortingChange: setSorting,
        state: {
            sorting,
        },
        manualPagination: !!pagination,
        pageCount: pageCount,
    });

    return (
        <div className="space-y-4">
            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        {table.getHeaderGroups().map((headerGroup) => (
                            <TableRow key={headerGroup.id}>
                                {headerGroup.headers.map((header) => (
                                    <TableHead key={header.id}>
                                        {header.isPlaceholder
                                            ? null
                                            : flexRender(
                                                  header.column.columnDef.header,
                                                  header.getContext()
                                              )}
                                    </TableHead>
                                ))}
                            </TableRow>
                        ))}
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell
                                    colSpan={columns.length}
                                    className="h-24 text-center"
                                >
                                    Loading...
                                </TableCell>
                            </TableRow>
                        ) : table.getRowModel().rows?.length ? (
                            table.getRowModel().rows.map((row) => (
                                <TableRow
                                    key={row.id}
                                    data-state={row.getIsSelected() && 'selected'}
                                >
                                    {row.getVisibleCells().map((cell) => (
                                        <TableCell key={cell.id}>
                                            {flexRender(
                                                cell.column.columnDef.cell,
                                                cell.getContext()
                                            )}
                                        </TableCell>
                                    ))}
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell
                                    colSpan={columns.length}
                                    className="h-24 text-center"
                                >
                                    No results.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>

            {pagination && (
                <div className="flex items-center justify-between px-2">
                    <div className="flex items-center space-x-2">
                        <p className="text-sm text-muted-foreground">Rows per page</p>
                        <Select
                            value={String(pagination.pageSize)}
                            onValueChange={(value) =>
                                pagination.onPageSizeChange(Number(value))
                            }
                        >
                            <SelectTrigger className="h-8 w-[70px]">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                {[10, 20, 50, 100].map((size) => (
                                    <SelectItem key={size} value={String(size)}>
                                        {size}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="flex items-center space-x-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => pagination.onPageChange(pagination.page - 1)}
                            disabled={pagination.page <= 1}
                        >
                            Previous
                        </Button>
                        <span className="text-sm text-muted-foreground">
                            Page {pagination.page} of {pageCount || 1}
                        </span>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => pagination.onPageChange(pagination.page + 1)}
                            disabled={pagination.page >= (pageCount || 1)}
                        >
                            Next
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
```

### Usage with Server-Side Pagination

```tsx
// src/app/users/page.tsx
'use client';

import { DataTable } from '@/components/data-table';
import { useUsers } from '@/hooks/use-users';
import { usePagination } from '@/hooks/use-pagination';
import { columns } from './columns';

export default function UsersPage() {
    const pagination = usePagination({ initialPageSize: 20 });
    const { data, isLoading } = useUsers({
        page: pagination.page,
        pageSize: pagination.pageSize,
    });

    return (
        <DataTable
            columns={columns}
            data={data?.data || []}
            pageCount={pagination.totalPages(data?.total || 0)}
            pagination={{
                page: pagination.page,
                pageSize: pagination.pageSize,
                onPageChange: pagination.setPage,
                onPageSizeChange: pagination.setPageSize,
            }}
            isLoading={isLoading}
        />
    );
}
```

### Column Definitions Pattern

```tsx
// src/app/users/columns.tsx
import { ColumnDef } from '@tanstack/react-table';
import { User } from '@/types/user';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Pencil, Trash } from 'lucide-react';

export const columns: ColumnDef<User>[] = [
    {
        accessorKey: 'name',
        header: 'Name',
    },
    {
        accessorKey: 'email',
        header: 'Email',
    },
    {
        accessorKey: 'role',
        header: 'Role',
        cell: ({ row }) => (
            <span className="capitalize">{row.getValue('role')}</span>
        ),
    },
    {
        accessorKey: 'createdAt',
        header: 'Created',
        cell: ({ row }) => (
            new Date(row.getValue('createdAt')).toLocaleDateString()
        ),
    },
    {
        id: 'actions',
        cell: ({ row }) => {
            const user = row.original;

            return (
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleEdit(user)}>
                            <Pencil className="mr-2 h-4 w-4" />
                            Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                            onClick={() => handleDelete(user.id)}
                            className="text-destructive"
                        >
                            <Trash className="mr-2 h-4 w-4" />
                            Delete
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            );
        },
    },
];
```

---

