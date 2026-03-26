# GraphQL Specialist Agents

Three specialized Claude Code agents for writing and reviewing GraphQL code across the full stack. Each agent is scoped to a specific technology — pick the one that matches your app's stack, and it handles the rest (including consulting the right reference files automatically).

## Agents

### `graphql-apollo-client-expert`

**File:** `graphql-apollo-client-expert.md`
**Model:** Opus

For React apps that consume GraphQL APIs using **Apollo Client**. Covers codegen setup, cache configuration, link chains, mutations, optimistic updates, and testing — all through the Apollo lens.

**When to use it:** Your app imports from `@apollo/client`. You're writing queries/mutations with `useQuery`/`useMutation`, configuring `InMemoryCache` and `typePolicies`, or setting up the Apollo link chain.

**Do not use it** if your app uses React Query / TanStack Query — use `graphql-react-query-expert` instead.

| Reference file | What it covers |
| --- | --- |
| `graphql-references/apollo-codegen-operations.md` | Codegen config, TypedDocumentNode, operations, fragments, component patterns |
| `graphql-references/apollo-cache-mutations.md` | InMemoryCache, typePolicies, keyFields, mutations, optimistic updates, pagination |
| `graphql-references/apollo-client-setup-testing.md` | Link chain setup, client configuration, testing with MSW, performance, SSR |

---

### `graphql-react-query-expert`

**File:** `graphql-react-query-expert.md`
**Model:** Opus

For React apps that consume GraphQL APIs using **TanStack Query (React Query)** with `graphql-request`. Covers codegen with `client-preset`, query key management, mutations, cache invalidation, and testing.

**When to use it:** Your app uses `@tanstack/react-query` with `graphql-request` for GraphQL. You're working with query keys, `staleTime` configuration, cache invalidation, or fragment masking via codegen's `client-preset`.

**Do not use it** if your app uses Apollo Client — use `graphql-apollo-client-expert` instead.

| Reference file | What it covers |
| --- | --- |
| `graphql-references/react-query-codegen-setup.md` | Codegen config with `documentMode: 'string'`, client-preset, QueryClient setup |
| `graphql-references/react-query-patterns.md` | Query hooks, query key conventions, mutations, pagination, prefetching |
| `graphql-references/react-query-testing-perf.md` | MSW testing setup, performance tuning, state management, SSR, file organization |

---

### `graphql-backend-expert`

**File:** `graphql-backend-expert.md`
**Model:** Opus

For **GraphQL Ruby** (including Pro) backend APIs in Rails applications. Covers schema design, resolver architecture, Dataloader for N+1 prevention, error handling, authorization with Pundit, and testing.

**When to use it:** You're writing or reviewing server-side GraphQL code — types, mutations, queries, subscriptions, resolvers, or schema design in a Rails app using `graphql-ruby`.

**This is the only backend agent.** The other two are frontend-only. If you need to work on both the API and the client in the same session, use this agent for the backend work and the appropriate frontend agent for the client work.

| Reference file | What it covers |
| --- | --- |
| `graphql-references/backend-schema-design.md` | Graph thinking vs REST anti-patterns, domain modeling, type design |
| `graphql-references/backend-error-handling.md` | Mutation standards, input/payload patterns, errors-as-data, query conventions |
| `graphql-references/backend-performance-dataloader.md` | N+1 prevention, GraphQL::Dataloader sources, performance optimization |
| `graphql-references/backend-architecture-resolvers.md` | File structure, base classes, resolver patterns, service object delegation |
| `graphql-references/backend-security-auth-pro.md` | Authentication, Pundit authorization, query complexity limits, Pro features, testing |

---

## Quick Reference: Picking the Right Agent

| Your stack | Agent to use |
| --- | --- |
| React + Apollo Client | `graphql-apollo-client-expert` |
| React + TanStack Query + graphql-request | `graphql-react-query-expert` |
| Rails + graphql-ruby (backend) | `graphql-backend-expert` |

---

## How Reference Files Work

Each agent has a set of reference files in `graphql-references/` that define canonical patterns and best practices. The agents consult these files automatically based on the task — you don't need to point them at specific references or read them yourself.

The reference files represent the **target state**, not necessarily what all existing code looks like today. When an agent reviews code, it flags deviations from these patterns as suggestions, even if the existing pattern is widespread in the codebase.
