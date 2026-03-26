# React Query: Testing, Performance, State & Organization

## Testing

### MSW (The Standard)

```typescript
const handlers = [
  graphql.query("GetUserProfile", ({ variables }) => {
    return HttpResponse.json({
      data: {
        user: { __typename: "User", id: variables.userId, name: "Jane Doe" },
      },
    });
  }),
  graphql.mutation("CreateTodo", ({ variables }) => {
    return HttpResponse.json({
      data: {
        createTodo: {
          __typename: "CreateTodoPayload",
          todo: { __typename: "Todo", id: "1", title: variables.input.title },
          errors: [],
        },
      },
    });
  }),
];

const server = setupServer(...handlers);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Test Wrapper

```typescript
function createTestQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
}

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}
```

### Testing Fragment-Masked Components

```typescript
import { makeFragmentData } from "@/gql/fragment-masking";

const mockData = makeFragmentData(
  { avatarUrl: "https://example.com/avatar.png", displayName: "Test User" },
  Avatar_UserFragment
);
render(<Avatar user={mockData} />);
```

### Testing Rules

- FRESH `QueryClient` per test
- `retry: false` in tests
- Mock at network level (MSW), not hooks
- Test loading, success, and error states
- Use `makeFragmentData` for fragments

## Performance

### Debounce Search

```typescript
const deferredSearch = useDeferredValue(searchTerm);
const { data } = useQuery({
  queryKey: ["search", deferredSearch],
  queryFn: () => execute(SearchQuery, { query: deferredSearch }),
  enabled: deferredSearch.length >= 3,
});
```

### `select` to Prevent Re-renders

```typescript
const { data } = useQuery({
  queryKey: ["users"],
  queryFn: () => execute(GetUsersQuery),
  select: (data) => data.users.filter((u) => u.active),
});
```

### Stale Time Tuning

```typescript
useQuery({ queryKey: ["categories"], staleTime: 30 * 60 * 1000 }); // 30 min (reference data)
useQuery({ queryKey: ["user", id], staleTime: 5 * 60 * 1000 }); // 5 min (user data)
useQuery({
  queryKey: ["notifications"],
  staleTime: 0,
  refetchInterval: 30_000,
}); // real-time
```

### Bundle Size

- `graphql-request`: ~5KB, `@tanstack/react-query`: ~13KB → Total ~18KB
- With `documentMode: 'string'`, avoid `graphql` parser (~40KB)

## State Management

### Server State vs Client State

React Query = server state. Use Zustand/Jotai/useState for client state.

### DO NOT duplicate server data

```typescript
// BAD
const { data } = useQuery({ ... });
const [user, setUser] = useState(data); // DON'T

// GOOD — React Query IS the source of truth
const { data: user } = useQuery({ ... });
```

### SSR (Next.js)

```typescript
export async function getServerSideProps() {
  const queryClient = new QueryClient();
  await queryClient.prefetchQuery({ queryKey: ["todos"], queryFn: () => execute(GetTodosQuery) });
  return { props: { dehydratedState: dehydrate(queryClient) } };
}

function Page({ dehydratedState }) {
  return <HydrationBoundary state={dehydratedState}><TodoList /></HydrationBoundary>;
}
```

## Component Architecture

- Fetch at route/page level
- Pass fragments down
- Three layers: Page → Feature Component (fragment) → UI Component (plain props)

## File Organization

```
src/
  features/users/
    components/UserProfile.tsx, UserAvatar.tsx
    hooks/useUserProfile.ts, useCreateUser.ts
    query-keys.ts
  gql/ (generated)
  lib/graphql-client.ts, query-client.ts
  codegen.ts
```

## Security

- Tokens in httpOnly cookies
- `persistedDocuments: true` in codegen
- Server rejects unknown query hashes
