# React Query: Code Generation, Client Setup & Configuration

## Code Generation

### Recommended Configuration

```typescript
// codegen.ts
import type { CodegenConfig } from "@graphql-codegen/cli";

const config: CodegenConfig = {
  schema: "https://api.example.com/graphql",
  documents: ["src/**/*.{ts,tsx}", "!src/gql/**/*"],
  generates: {
    "./src/gql/": {
      preset: "client",
      config: {
        useTypeImports: true,
        enumsAsTypes: true,
        strictScalars: true,
        documentMode: "string", // IMPORTANT: TypedDocumentString (not AST)
        scalars: { DateTime: "string", JSON: "Record<string, unknown>" },
      },
      presetConfig: { fragmentMasking: true, persistedDocuments: true },
    },
  },
};
export default config;
```

**Why `documentMode: 'string'`:**

- `graphql-request` sends strings, not AST
- Avoids bundling `graphql` parser (~40KB)
- Still fully typed via `TypedDocumentString<TResult, TVariables>`

### Fragment Masking

```typescript
export const Avatar_UserFragment = graphql(`
  fragment Avatar_UserFragment on User { avatarUrl displayName }
`);

type AvatarProps = { user: FragmentType<typeof Avatar_UserFragment> };

export function Avatar(props: AvatarProps) {
  const user = useFragment(Avatar_UserFragment, props.user);
  return <img src={user.avatarUrl} alt={user.displayName} />;
}
```

Key utilities: `FragmentType<T>`, `useFragment()`, `ResultOf<T>`, `makeFragmentData()`

### Anti-patterns

- Using `documentMode: 'documentNode'` (ships AST parser)
- Manually writing types for operations
- Not using `strictScalars`

## graphql-request Client

```typescript
import { GraphQLClient } from "graphql-request";
import type { TypedDocumentString } from "../gql/graphql";

const client = new GraphQLClient("/graphql", {
  headers: () => ({ authorization: `Bearer ${getToken()}` }),
});

export async function execute<TResult, TVariables>(
  query: TypedDocumentString<TResult, TVariables>,
  ...[variables]: TVariables extends Record<string, never> ? [] : [TVariables]
): Promise<TResult> {
  return client.request(query.toString(), variables ?? undefined);
}
```

### Error Handling in Client

```typescript
const client = new GraphQLClient("/graphql", {
  responseMiddleware: (response) => {
    if (response instanceof Error)
      logger.error("[Network error]:", response.message);
    if (response.errors) {
      response.errors.forEach((error) => {
        if (error.extensions?.code === "UNAUTHENTICATED") redirectToLogin();
      });
    }
  },
});
```

## QueryClient Configuration

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,
      retry: (failureCount, error) => {
        if (isAuthError(error)) return false;
        if (isNotFoundError(error)) return false;
        return failureCount < 3;
      },
    },
    mutations: { retry: false },
  },
});
```

### Rules

- ALWAYS set `staleTime` (default 0 = refetch every render)
- ALWAYS set `gcTime` > `staleTime`
- NEVER retry mutations
- Don't retry permanent errors (auth, not found)
