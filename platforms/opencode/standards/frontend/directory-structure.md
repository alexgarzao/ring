## Directory Structure

```text
/src
  /app                 # Next.js App Router
    /api               # API routes
    /(auth)            # Auth route group
    /(dashboard)       # Dashboard route group
    layout.tsx
    page.tsx
  /components
    /ui                # Primitive UI components
      button.tsx
      input.tsx
      card.tsx
    /features          # Feature-specific components
      /user
        UserProfile.tsx
        UserList.tsx
      /order
        OrderForm.tsx
  /hooks               # Custom hooks
    useUser.ts
    useDebounce.ts
  /lib                 # Utilities
    api.ts
    utils.ts
    cn.ts
  /stores              # Zustand stores
    userStore.ts
    uiStore.ts
  /types               # TypeScript types
    user.ts
    api.ts
/public                # Static assets
```

---

