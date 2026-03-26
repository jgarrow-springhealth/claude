# React Query: Query Patterns, Mutations & Pagination

## Query Patterns

### Basic Query Hook

```typescript
const GetUserProfileQuery = graphql(`
  query GetUserProfile($userId: ID!) {
    user(id: $userId) {
      id
      name
      email
      ...Avatar_UserFragment
    }
  }
`);

export function useUserProfile(userId: string) {
  return useQuery({
    queryKey: ["user", userId],
    queryFn: () => execute(GetUserProfileQuery, { userId }),
    enabled: !!userId,
  });
}
```

### Query Key Conventions (CRITICAL)

```typescript
queryKey: ["users"]; // all users
queryKey: ["users", { filter, sort }]; // filtered
queryKey: ["user", userId]; // single
queryKey: ["user", userId, "posts"]; // nested
queryKey: ["user", userId, "posts", { status: "published" }]; // filtered nested
```

### Query Key Factory Pattern

```typescript
export const userKeys = {
  all: ["users"] as const,
  lists: () => [...userKeys.all, "list"] as const,
  list: (filters: UserFilters) => [...userKeys.lists(), filters] as const,
  details: () => [...userKeys.all, "detail"] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
};
```

### Conditional & Dependent Queries

```typescript
// Conditional
const { data } = useQuery({ queryKey: ["user", userId], queryFn: ..., enabled: !!userId });

// Dependent
const { data: user } = useQuery({ queryKey: ["user", userId], ... });
const { data: posts } = useQuery({ queryKey: ["user", userId, "posts"], ..., enabled: !!user });
```

### Suspense Queries

```typescript
function UserProfile({ userId }: { userId: string }) {
  const { data } = useSuspenseQuery({
    queryKey: ["user", userId],
    queryFn: () => execute(GetUserProfileQuery, { userId }),
  });
  return <Profile user={data.user} />;
}
```

### `select` for Transformation

```typescript
const { data } = useQuery({
  queryKey: ["users"],
  queryFn: () => execute(GetUsersQuery),
  select: (data) => data.users.filter((u) => u.active),
});
```

## Mutations

### Basic Mutation

```typescript
export function useCreateTodo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateTodoInput) =>
      execute(CreateTodoMutation, { input }),
    onSuccess: (data) => {
      if (data.createTodo.errors.length > 0) return;
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}
```

### Optimistic Updates

```typescript
export function useUpdateTodo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...input }) =>
      execute(UpdateTodoMutation, { id, input }),
    onMutate: async (newTodo) => {
      await queryClient.cancelQueries({ queryKey: ["todos"] });
      const previous = queryClient.getQueryData(["todos"]);
      queryClient.setQueryData(["todos"], (old) => ({
        todos: old.todos.map((t) =>
          t.id === newTodo.id ? { ...t, ...newTodo } : t,
        ),
      }));
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous)
        queryClient.setQueryData(["todos"], context.previous);
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["todos"] }),
  });
}
```

### Mutation Error Handling (Two Layers)

- `onSuccess`: Check `data.createUser.errors` (validation/business errors)
- `onError`: Handle network/system errors (graphql-request threw)

### Mutation Rules

- ALWAYS invalidate in `onSettled` (not just `onSuccess`)
- ALWAYS cancel queries before optimistic updates
- ALWAYS return rollback context from `onMutate`
- NEVER retry mutations

## Infinite Queries (Pagination)

```typescript
export function useFeed() {
  return useInfiniteQuery({
    queryKey: ["feed"],
    queryFn: ({ pageParam }) =>
      execute(GetFeedQuery, { cursor: pageParam, limit: 10 }),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) =>
      lastPage.feed.pageInfo.hasNextPage
        ? lastPage.feed.pageInfo.endCursor
        : undefined,
  });
}
```

### Keep Previous Data

```typescript
import { keepPreviousData } from "@tanstack/react-query";
const { data } = useQuery({ ..., placeholderData: keepPreviousData });
```

## Prefetching

```typescript
// On hover
queryClient.prefetchQuery({
  queryKey: ["todo", id],
  queryFn: () => execute(GetTodoQuery, { id }),
  staleTime: 5 * 60 * 1000,
});

// Route loader
await queryClient.ensureQueryData({ queryKey: ["user", userId], queryFn: ... });
```
