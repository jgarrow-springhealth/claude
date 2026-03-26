# Apollo Client: Cache, Mutations & Data Management

## Cache Configuration (CRITICAL)

```typescript
const cache = new InMemoryCache({
  possibleTypes: {
    SearchResult: ["User", "Post", "Comment"],
    Node: ["User", "Post", "Comment", "Todo"],
  },
  typePolicies: {
    Product: { keyFields: ["upc"] },
    CartItem: { keyFields: ["productId", "size"] },
    CurrentUser: { keyFields: [] },
    PageInfo: { keyFields: false },
    User: {
      keyFields: ["id"],
      fields: {
        fullName: {
          read(_, { readField }) {
            return `${readField("firstName")} ${readField("lastName")}`;
          },
        },
      },
    },
    Query: {
      fields: {
        users: relayStylePagination(["filter"]),
        feed: {
          keyArgs: ["type"],
          merge(existing = [], incoming, { args }) {
            const offset = args?.offset ?? 0;
            const merged = existing.slice(0);
            for (let i = 0; i < incoming.length; i++) {
              merged[offset + i] = incoming[i];
            }
            return merged;
          },
        },
      },
    },
  },
});
```

### keyFields Rules

- ALWAYS set `keyFields` for types with non-standard identifiers
- `keyFields: false` for embedded objects not to normalize
- `keyFields: []` for singletons
- NEVER rely on defaults for `upc`, `slug`, or composite keys

### possibleTypes (REQUIRED for interfaces/unions)

- MUST configure when schema uses interfaces or unions
- Without this, fragment matching silently fails

## Fetch Policies

| Policy              | Use When                                             |
| ------------------- | ---------------------------------------------------- |
| `cache-first`       | Default. Data rarely changes.                        |
| `cache-and-network` | Best for most UI. Show cached, update in background. |
| `network-only`      | Must be fresh. After mutations.                      |
| `no-cache`          | Sensitive data that shouldn't persist.               |
| `standby`           | Only execute when manually triggered.                |

```typescript
const { data } = useQuery(GetUserProfileDocument, {
  fetchPolicy: "cache-and-network",
  nextFetchPolicy: "cache-first",
});
```

## Error Handling

### Error Policy

```typescript
defaultOptions: {
  watchQuery: { errorPolicy: "all" },   // Partial data + errors
  mutate: { errorPolicy: "none" },       // Throw on errors
}
```

### Mutation Error Handling (Two-Layer)

```typescript
const [createUser] = useMutation(CreateUserDocument, {
  onCompleted: (data) => {
    if (data.createUser.errors.length > 0) {
      setFormErrors(data.createUser.errors);
    } else {
      navigate(`/users/${data.createUser.user.id}`);
    }
  },
  onError: (error) => {
    toast.error("Something went wrong.");
  },
});
```

## Optimistic Updates

```typescript
const [updateTodo] = useMutation(UpdateTodoDocument, {
  optimisticResponse: {
    updateTodo: {
      __typename: "UpdateTodoPayload",
      todo: {
        __typename: "Todo",
        id: todoId,
        title: newTitle,
        completed: true,
      },
      errors: [],
    },
  },
});
```

Rules: ALWAYS include `__typename` + `id` on every object.

## Cache Updates After Mutations

### `cache.modify` (preferred)

```typescript
update(cache, { data }) {
  cache.modify({
    fields: {
      todos(existingRefs = [], { toReference }) {
        return [...existingRefs, toReference(data.createTodo.todo)];
      },
    },
  });
}
```

### `cache.evict` + gc (deletions)

```typescript
cache.evict({ id: cache.identify({ __typename: "Todo", id: todoId }) });
cache.gc();
```

### `refetchQueries` (simplest)

```typescript
refetchQueries: ["GetTodos"]; // Use query NAME, not document
```

Rules: Prefer `cache.modify` over `refetchQueries`. Always `cache.gc()` after eviction.

## Pagination

### Relay-Style (Preferred)

```typescript
// typePolicies: users: relayStylePagination(["filter"])
const { data, fetchMore } = useQuery(GetUsersDocument, {
  variables: { first: 20 },
  notifyOnNetworkStatusChange: true,
});
const loadMore = () =>
  fetchMore({ variables: { after: data?.users.pageInfo.endCursor } });
```

## Subscriptions

```typescript
useSubscription(OnTodoUpdatedDocument, {
  onData: ({ client, data }) => {
    client.cache.modify({ id: client.cache.identify(data.data.todoUpdated), fields: { ... } });
  },
});
```

## Reactive Variables (Local State)

```typescript
export const cartItemsVar = makeVar<string[]>([]);
// In components: const items = useReactiveVar(cartItemsVar);
// In typePolicies: cartItems: { read() { return cartItemsVar(); } }
```
