# Apollo Client: Code Generation, Operations & Fragments

## Code Generation for Apollo Client

### Recommended Configuration

Apollo's official recommendation is `typescript` + `typescript-operations` + `typed-document-node` plugins rather than `client-preset`.

```typescript
// codegen.ts — Apollo-recommended approach
import type { CodegenConfig } from "@graphql-codegen/cli";

const config: CodegenConfig = {
  schema: "https://api.example.com/graphql",
  documents: ["src/**/*.{ts,tsx}"],
  generates: {
    "./src/gql/types.ts": {
      plugins: ["typescript", "typescript-operations", "typed-document-node"],
      config: {
        useTypeImports: true,
        enumsAsTypes: true,
        strictScalars: true,
        skipTypename: false, // Keep __typename for cache normalization
        scalars: { DateTime: "string", JSON: "Record<string, unknown>" },
      },
    },
  },
};
export default config;
```

**Why NOT `client-preset` for Apollo:**

- `client-preset` generates fragment masking runtime code that adds bundle size
- Apollo already handles fragment type safety through cache normalization
- `useFragment` from `client-preset` is NOT a React hook but looks like one, confusing ESLint
- `TypedDocumentNode` from `typed-document-node` plugin works natively with all Apollo hooks

### TypedDocumentNode (ALWAYS use)

```typescript
// GOOD — types inferred
const { data } = useQuery(GetUsersDocument);

// BAD — manual generics
const { data } = useQuery<GetUsersQuery, GetUsersQueryVariables>(GET_USERS);
```

### Anti-patterns

- Manually writing TypeScript types for GraphQL operations
- Using generic `DocumentNode` instead of `TypedDocumentNode`
- Using manual generics on `useQuery<Type, Vars>()`
- Not validating generated code freshness in CI

## Operation Design

### ALWAYS Name Operations

Apollo uses operation names for cache identification, devtools, and network logging.

### Naming Conventions

- **Queries**: `Get[Resource]` or `List[Resources]`
- **Mutations**: `[Action][Resource]`
- **Subscriptions**: `On[Event]`
- **Fragments**: `[ComponentName]_[TypeName]Fragment`

### Fragment Composition (CRITICAL for Apollo)

```typescript
// Avatar.tsx
export const AVATAR_USER_FRAGMENT = gql`
  fragment Avatar_UserFragment on User {
    avatarUrl
    displayName
  }
`;

// UserCard.tsx — compose child fragments
const GET_USER_CARD = gql`
  query GetUserCard($id: ID!) {
    user(id: $id) {
      id
      name
      ...Avatar_UserFragment
      ...UserBio_UserFragment
    }
  }
  ${AVATAR_USER_FRAGMENT}
  ${USER_BIO_FRAGMENT}
`;
```

With `typed-document-node` plugin, fragments compose via `${FRAGMENT}`. With `client-preset`, the `graphql()` tag handles this automatically.

## TypeScript Integration

- Enable `strictScalars: true` in codegen
- NEVER use `any` for GraphQL data
- NEVER set `skipTypename: true` — Apollo needs `__typename` for cache normalization
- ALWAYS include `__typename` in optimistic responses and manual cache writes
- Use `as const` for mock data: `__typename: 'User' as const`

### Discriminated Unions

```typescript
function handleResult(result: CreateUserMutation) {
  const r = result.createUser;
  switch (r.__typename) {
    case "User": return <Success user={r} />;
    case "ValidationError": return <FieldError message={r.message} field={r.field} />;
    default: const _exhaustive: never = r; return null;
  }
}
```

## Component Architecture

### Fragment-Driven Components (THE pattern for Apollo)

Every component displaying GraphQL data declares its needs via a colocated fragment.

### Data Fetching Level

- Fetch at route/page level using `useQuery` or `useSuspenseQuery`
- Pass typed fragment data down to children
- NEVER fetch in deeply nested components (waterfalls)

### Loading States with Suspense

```typescript
function UserPage() {
  return (
    <ErrorBoundary fallback={<ErrorMessage />}>
      <Suspense fallback={<UserSkeleton />}>
        <UserProfile userId={id} />
      </Suspense>
    </ErrorBoundary>
  );
}
```

## File Organization

```
src/
  features/users/
    components/UserProfile.tsx   # Component + colocated fragment + query
    hooks/useCreateUser.ts       # Custom hook wrapping useMutation
  gql/types.ts                   # Generated types (codegen output)
  lib/apollo-client.ts           # Client configuration
  codegen.ts
```
