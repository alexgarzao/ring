## Custom Hooks Patterns

### Pagination Hooks (MANDATORY for lists)

#### usePagination (Offset-based)

```tsx
import { useState, useCallback, useMemo } from 'react';

interface UsePaginationOptions {
    initialPage?: number;
    initialPageSize?: number;
    pageSizeOptions?: number[];
}

interface UsePaginationReturn {
    page: number;
    pageSize: number;
    offset: number;
    setPage: (page: number) => void;
    setPageSize: (size: number) => void;
    nextPage: () => void;
    prevPage: () => void;
    canNextPage: (totalItems: number) => boolean;
    canPrevPage: boolean;
    pageSizeOptions: number[];
    totalPages: (totalItems: number) => number;
}

export function usePagination({
    initialPage = 1,
    initialPageSize = 10,
    pageSizeOptions = [10, 20, 50, 100],
}: UsePaginationOptions = {}): UsePaginationReturn {
    const [page, setPage] = useState(initialPage);
    const [pageSize, setPageSize] = useState(initialPageSize);

    const offset = useMemo(() => (page - 1) * pageSize, [page, pageSize]);

    const nextPage = useCallback(() => setPage((p) => p + 1), []);
    const prevPage = useCallback(() => setPage((p) => Math.max(1, p - 1)), []);

    const canNextPage = useCallback(
        (totalItems: number) => page * pageSize < totalItems,
        [page, pageSize]
    );
    const canPrevPage = page > 1;

    const totalPages = useCallback(
        (totalItems: number) => Math.ceil(totalItems / pageSize),
        [pageSize]
    );

    const handleSetPageSize = useCallback((size: number) => {
        setPageSize(size);
        setPage(1); // Reset to first page on size change
    }, []);

    return {
        page,
        pageSize,
        offset,
        setPage,
        setPageSize: handleSetPageSize,
        nextPage,
        prevPage,
        canNextPage,
        canPrevPage,
        pageSizeOptions,
        totalPages,
    };
}
```

#### useCursorPagination (Cursor-based)

```tsx
import { useState, useCallback } from 'react';

interface CursorPaginationState {
    cursor: string | null;
    direction: 'next' | 'prev';
}

interface UseCursorPaginationOptions {
    initialPageSize?: number;
}

interface UseCursorPaginationReturn {
    cursor: string | null;
    pageSize: number;
    setPageSize: (size: number) => void;
    goToNext: (nextCursor: string) => void;
    goToPrev: (prevCursor: string) => void;
    reset: () => void;
    hasNext: boolean;
    hasPrev: boolean;
    setHasNext: (value: boolean) => void;
    setHasPrev: (value: boolean) => void;
}

export function useCursorPagination({
    initialPageSize = 10,
}: UseCursorPaginationOptions = {}): UseCursorPaginationReturn {
    const [state, setState] = useState<CursorPaginationState>({
        cursor: null,
        direction: 'next',
    });
    const [pageSize, setPageSize] = useState(initialPageSize);
    const [hasNext, setHasNext] = useState(false);
    const [hasPrev, setHasPrev] = useState(false);

    const goToNext = useCallback((nextCursor: string) => {
        setState({ cursor: nextCursor, direction: 'next' });
    }, []);

    const goToPrev = useCallback((prevCursor: string) => {
        setState({ cursor: prevCursor, direction: 'prev' });
    }, []);

    const reset = useCallback(() => {
        setState({ cursor: null, direction: 'next' });
    }, []);

    return {
        cursor: state.cursor,
        pageSize,
        setPageSize,
        goToNext,
        goToPrev,
        reset,
        hasNext,
        hasPrev,
        setHasNext,
        setHasPrev,
    };
}
```

### CRUD Sheet Hook Pattern

```tsx
import { useState, useCallback } from 'react';

type SheetMode = 'create' | 'edit' | 'view' | 'closed';

interface UseSheetOptions<T> {
    onSuccess?: (data: T) => void;
}

interface UseSheetReturn<T> {
    isOpen: boolean;
    mode: SheetMode;
    data: T | null;
    openCreate: () => void;
    openEdit: (item: T) => void;
    openView: (item: T) => void;
    close: () => void;
    isCreateMode: boolean;
    isEditMode: boolean;
    isViewMode: boolean;
}

export function useCreateUpdateSheet<T>({
    onSuccess,
}: UseSheetOptions<T> = {}): UseSheetReturn<T> {
    const [mode, setMode] = useState<SheetMode>('closed');
    const [data, setData] = useState<T | null>(null);

    const openCreate = useCallback(() => {
        setData(null);
        setMode('create');
    }, []);

    const openEdit = useCallback((item: T) => {
        setData(item);
        setMode('edit');
    }, []);

    const openView = useCallback((item: T) => {
        setData(item);
        setMode('view');
    }, []);

    const close = useCallback(() => {
        setMode('closed');
        setData(null);
    }, []);

    return {
        isOpen: mode !== 'closed',
        mode,
        data,
        openCreate,
        openEdit,
        openView,
        close,
        isCreateMode: mode === 'create',
        isEditMode: mode === 'edit',
        isViewMode: mode === 'view',
    };
}
```

### Utility Hooks

#### useDebounce

```tsx
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number = 300): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useEffect(() => {
        const timer = setTimeout(() => setDebouncedValue(value), delay);
        return () => clearTimeout(timer);
    }, [value, delay]);

    return debouncedValue;
}
```

#### useStepper

```tsx
import { useState, useCallback } from 'react';

interface UseStepperOptions {
    initialStep?: number;
    totalSteps: number;
}

interface UseStepperReturn {
    currentStep: number;
    totalSteps: number;
    isFirstStep: boolean;
    isLastStep: boolean;
    nextStep: () => void;
    prevStep: () => void;
    goToStep: (step: number) => void;
    reset: () => void;
    progress: number;
}

export function useStepper({
    initialStep = 0,
    totalSteps,
}: UseStepperOptions): UseStepperReturn {
    const [currentStep, setCurrentStep] = useState(initialStep);

    const nextStep = useCallback(() => {
        setCurrentStep((s) => Math.min(s + 1, totalSteps - 1));
    }, [totalSteps]);

    const prevStep = useCallback(() => {
        setCurrentStep((s) => Math.max(s - 1, 0));
    }, []);

    const goToStep = useCallback(
        (step: number) => {
            if (step >= 0 && step < totalSteps) {
                setCurrentStep(step);
            }
        },
        [totalSteps]
    );

    const reset = useCallback(() => setCurrentStep(initialStep), [initialStep]);

    return {
        currentStep,
        totalSteps,
        isFirstStep: currentStep === 0,
        isLastStep: currentStep === totalSteps - 1,
        nextStep,
        prevStep,
        goToStep,
        reset,
        progress: ((currentStep + 1) / totalSteps) * 100,
    };
}
```

---

