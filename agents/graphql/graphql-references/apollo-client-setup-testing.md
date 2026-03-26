# Apollo Client: Client Setup, Link Chain, Testing & Performance

## Link Chain Configuration

Order matters. Recommended production setup:

```typescript
// 1. Auth Link
const authLink = setContext(async (_, { headers }) => {
  const token = await getAuthToken();
  return { headers: { ...headers, authorization: token ? `Bearer ${token}` : "" } };
});

// 2. Error Link
const errorLink = onError(({ graphQLErrors, networkError, operation }) => {
  if (graphQLErrors) {
    for (const { message, extensions } of graphQLErrors) {
      if (extensions?.code === "UNAUTHENTICATED") refreshTokenAndRetry();
      logger.error(`[GraphQL error]: ${message}`, { operation: operation.operationName });
    }
  }
  if (networkError) logger.error(`[Network error]: ${networkError.message}`);
});

// 3. Retry Link (queries only)
const retryLink = new RetryLink({
  delay: { initial: 300, max: 3000, jitter: true },
  attempts: {
    max: 3,
    retryIf: (error, operation) => {
      const def = getMainDefinition(operation.query);
      if (def.kind === "OperationDefinition" && def.operation === "mutation") return false;
      return !!error;
    },
  },
});

// 4. HTTP Link (MUST be last)
const httpLink = new HttpLink({ uri: "/graphql", credentials: "include" });

// 5. WebSocket Link (subscriptions)
const wsLink = new GraphQLWsLink(createClient({ url: "ws://localhost:4000/graphql" }));

// 6. Split
const splitLink = ApolloLink.split(
  ({ query }) => {
    const def = getMainDefinition(query);
    return def.kind === "OperationDefinition" && def.operation === "subscription";
  },
  wsLink,
  ApolloLink.from([authLink, errorLink, retryLink, httpLink])
);

const client = new ApolloClient({ link: splitLink, cache, defaultOptions: { ... } });
```

### Link Chain Rules

- `HttpLink` MUST be LAST (terminating)
- `errorLink` before `retryLink`
- `authLink` before everything except logging
- NEVER retry mutations

## Error Type Discrimination

```typescript
function isNetworkError(error: ApolloError): boolean {
  return !!error.networkError;
}
function isAuthError(error: ApolloError): boolean {
  return error.graphQLErrors.some(
    (e) => e.extensions?.code === "UNAUTHENTICATED",
  );
}
```

## Testing

### MSW (Preferred for Apollo 4.0+)

```typescript
const handlers = [
  graphql.query("GetUserProfile", ({ variables }) => {
    return HttpResponse.json({
      data: {
        user: { __typename: "User", id: variables.userId, name: "Jane" },
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
function renderWithApollo(ui: React.ReactElement) {
  const client = new ApolloClient({ uri: "/graphql", cache: new InMemoryCache() });
  return render(
    <ApolloProvider client={client}>
      <Suspense fallback={<div>Loading...</div>}>{ui}</Suspense>
    </ApolloProvider>
  );
}
```

### Testing Rules

- FRESH `ApolloClient` per test (cache leaks)
- Always include `__typename` in mock data
- `MockedProvider` deprecated in Apollo 4.0 — use MSW
- Test error and loading states

## Performance

### Query Splitting

```typescript
const { data: user } = useQuery(GetUserDocument); // cache-first
const { data: orders } = useQuery(GetOrdersDocument); // cache-and-network
```

### Debounce, Flicker Prevention, @defer, APQ

```typescript
const deferredSearch = useDeferredValue(searchTerm);
const { data, previousData } = useQuery(GetDataDocument);
const displayData = data ?? previousData;
```

### Persisted Queries

```typescript
const persistedQueriesLink = createPersistedQueryLink({ sha256 });
```

## Security

- Tokens in httpOnly cookies (not localStorage)
- `connectToDevTools: false` in production
- APQ doubles as operation allowlist

## SSR / Next.js

```typescript
import { PreloadQuery } from "@apollo/client-integration-nextjs";
// In server component:
<PreloadQuery query={GetProductDocument} variables={{ id: "1" }}>
  <Suspense fallback={<Loading />}><ProductDetails id="1" /></Suspense>
</PreloadQuery>
```
