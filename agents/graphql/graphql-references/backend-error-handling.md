# Backend: Mutations, Error Handling & Queries

## Mutation Standards

### Naming

- Verb + Noun: `createUser`, `updatePost`, `deleteComment`, `publishArticle`
- Class naming: `Mutations::CreateUser` (PascalCase)
- One mutation per business action (not `manageUser`)

### Input/Payload Pattern (ALWAYS follow this)

```ruby
class Mutations::CreateUser < Mutations::BaseMutation
  argument :input, Types::CreateUserInput, required: true

  field :user, Types::UserType, null: true   # MUST be nullable
  field :errors, [Types::UserErrorType], null: false

  def resolve(input:)
    user = User.new(input.to_h)
    if user.save
      { user: user, errors: [] }
    else
      { user: nil, errors: format_errors(user) }
    end
  end
end
```

### Error Handling (Three-Tier System)

1. **User errors** (validation): Return as data in the `errors` field on the mutation payload
2. **Authorization errors**: Raise `GraphQL::ExecutionError` with extensions code (`UNAUTHENTICATED`, `FORBIDDEN`)
3. **System errors**: Handle via `rescue_from` at schema level, log internally, return generic message

### User Error Type

```ruby
class Types::UserErrorType < Types::BaseObject
  field :message, String, null: false
  field :path, [String], null: true
  field :code, String, null: true
end
```

### Use `loads:` for Auto-Loading

```ruby
argument :post_id, ID, loads: Types::PostType
# Receives `post` (not `post_id`) in resolve method
```

### Mutation Anti-patterns

- Returning only `true`/`false` from mutations
- Using `null: false` on mutation payload fields
- A single catch-all mutation for CRUD
- Raising exceptions for expected validation failures
- Not returning errors alongside the mutated object

## Query Design Standards

### Root Query Fields

- Noun-based: `user`, `users`, `post`, `currentUser`
- Single resource: `user(id: ID!)`
- Collections: `users(first: Int, after: String, filter: UserFilter)`

### Filtering/Sorting

- Use dedicated input types for filters
- Put filtering/sorting logic in plain Ruby classes (query objects), NOT in resolver methods

```ruby
class Types::UserFilterInput < Types::BaseInputObject
  argument :name_contains, String, required: false
  argument :status, Types::UserStatusEnum, required: false
  argument :created_after, GraphQL::Types::ISO8601DateTime, required: false
end
```

### Complexity and Depth Limits (MUST configure)

```ruby
class MySchema < GraphQL::Schema
  max_depth 15
  max_complexity 300
end
```

- Override complexity for expensive fields: `field :report, ..., complexity: 50`
- Use dynamic complexity for connections based on `first`/`last` args

## Error Handling Standards

### Custom Error Classes (Dual-Message Pattern)

Every `GraphQL::ExecutionError` should carry a **client-safe message** (shown in the response) and an **internal message** (logged to Rails/Datadog). The internal message is never serialized into the response.

```ruby
# app/graphql/errors/base_graphql_error.rb
module Errors
  class BaseGraphqlError < GraphQL::ExecutionError
    attr_reader :internal_message

    def initialize(client_message, internal_message: nil, code:)
      @internal_message = internal_message || client_message
      super(client_message, extensions: { "code" => code })
    end
  end
end

# app/graphql/errors/graphql_auth_error.rb
module Errors
  class GraphqlAuthError < BaseGraphqlError
    # Internal message is the primary arg (what devs write at the call site).
    # Client message has a safe default.
    def initialize(internal_message, client_message: "Authorization error")
      super(client_message, internal_message: internal_message, code: "UNAUTHORIZED")
    end
  end
end

# app/graphql/errors/not_found_error.rb
module Errors
  class NotFoundError < BaseGraphqlError
    def initialize(internal_message = "Resource not found", client_message: "Not found")
      super(client_message, internal_message: internal_message, code: "NOT_FOUND")
    end
  end
end
```

Usage:

```ruby
raise Errors::GraphqlAuthError.new("Password is incorrect for user #{user.id}")
# Client sees: "Authorization error" with code "UNAUTHORIZED"
# Logs see:    "Password is incorrect for user 42"

raise Errors::NotFoundError.new("Appointment #{id} not found in org #{org.id}")
# Client sees: "Not found" with code "NOT_FOUND"
# Logs see:    "Appointment abc-123 not found in org xyz-456"
```

### Schema-Level Rescue (with Dual-Message Logging)

`rescue_from` is the single logging chokepoint for raised errors (queries/resolvers). Register specific handlers **after** `StandardError` — graphql-ruby checks in reverse registration order.

```ruby
class MySchema < GraphQL::Schema
  rescue_from(ActiveRecord::RecordNotFound) do |err, _obj, _args, ctx, _field|
    raise GraphQL::ExecutionError.new(
      "Not found",
      extensions: { "code" => "NOT_FOUND", "requestId" => ctx[:request_id] }
    )
  end

  rescue_from(StandardError) do |err, _obj, _args, ctx, _field|
    request_id = ctx[:request_id] || SecureRandom.uuid
    Rails.logger.error("[GraphQL INTERNAL_ERROR] [#{request_id}] #{err.class}: #{err.message}")
    Rails.logger.error(err.backtrace&.first(10)&.join("\n"))
    Sentry.capture_exception(err) if defined?(Sentry)

    ext = { "code" => "INTERNAL_ERROR", "requestId" => request_id }

    # Development only — never in production
    if Rails.env.development? || Rails.env.test?
      ext[:exception] = err.class.name
      ext[:backtrace] = err.backtrace&.first(5)
    end

    raise GraphQL::ExecutionError.new("Internal error", extensions: ext)
  end

  # Registered AFTER StandardError so it matches first (reverse order)
  rescue_from(Errors::BaseGraphqlError) do |err, _obj, _args, ctx, _field|
    Rails.logger.error(
      "[GraphQL #{err.extensions&.dig("code")}] " \
      "internal_message=#{err.internal_message.inspect} " \
      "user_id=#{ctx[:current_user]&.id} " \
      "path=#{ctx[:current_path]&.join(".")}"
    )
    raise err  # Re-raise as-is — `message` is already client-safe
  end
end
```

### Mutation Auth Error Helper (Dual-Message for Errors-as-Data)

Mutations return errors-as-data, so `rescue_from` never fires. Use a helper on `BaseMutation` that encapsulates both logging and the return value.

```ruby
class Mutations::BaseMutation < GraphQL::Schema::Mutation
  field :errors, [Types::UserErrorType], null: false

  private

  def auth_error(internal_message, client_message: "You are not authorized to perform this action.")
    Rails.logger.error(
      "[GraphQL UNAUTHORIZED] " \
      "internal_message=#{internal_message.inspect} " \
      "mutation=#{self.class.name} " \
      "user_id=#{context[:current_user]&.id}"
    )
    { errors: [{ message: client_message, code: "UNAUTHORIZED", path: [] }] }
  end
end
```

Usage:

```ruby
class Mutations::UpdateUserEmail < Mutations::BaseMutation
  def resolve(input:)
    unless policy.update_email?
      return auth_error(
        "User #{context[:current_user]&.id} cannot update email for user #{input[:user_id]} — not account owner"
      )
    end
    # ...
  end
end
# Client sees: "You are not authorized to perform this action." with code "UNAUTHORIZED"
# Logs see:    "User 42 cannot update email for user 99 — not account owner"
```

### Why Queries and Mutations Use Different Logging Strategies

| Context       | Error mechanism                | Logging hook                  | Reason                                                            |
| ------------- | ------------------------------ | ----------------------------- | ----------------------------------------------------------------- |
| **Queries**   | Raise `GraphqlAuthError`       | `rescue_from` at schema level | Single chokepoint, has access to context                          |
| **Mutations** | Return via `auth_error` helper | Inside the helper method      | Mutations return data, not exceptions — `rescue_from` never fires |

### Error Extensions (ALWAYS use)

- Always include `extensions: { "code" => "ERROR_CODE" }` for machine-readable error classification
- Standard codes: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR`, `INTERNAL_ERROR`

### Common Extension Fields Beyond `code`

| Field        | Purpose                                 | Include when                    |
| ------------ | --------------------------------------- | ------------------------------- |
| `code`       | Machine-readable error classifier       | Always                          |
| `requestId`  | Correlates to server logs for debugging | Always on system errors         |
| `timestamp`  | ISO 8601 server-side time               | System errors, rate limits      |
| `retryable`  | Boolean: can the client retry?          | Rate limits, transient failures |
| `retryAfter` | Seconds until retry is reasonable       | Rate limits                     |
| `field`      | Which schema field caused the error     | Auth errors on specific fields  |
| `argument`   | Which input argument was invalid        | Query-level validation errors   |

### Extensions Anti-Patterns

- **Never include in production:** `stacktrace`, `backtrace`, `exception`, `originalError`, `sql`, `hostname` — these leak internals
- **Don't stuff domain data into extensions.** If the client needs more than a message and code, use a result union type
- **Don't duplicate `path` or `locations`** — the error object already has these per spec
- **Keep extensions flat** — deeply nested objects signal you need a result union instead

## Business Logic Errors in Queries

Mutations use the errors-as-data pattern (errors field on the payload). Queries need a different approach since they don't have a payload wrapper. Use one of two patterns depending on complexity:

### Simple business errors: `ExecutionError` with extensions

When the client only needs a code and a message to branch on:

```ruby
# In a resolver or type method:
raise GraphQL::ExecutionError.new(
  "Member benefits expired on 2026-01-15",
  extensions: { code: "BENEFITS_EXPIRED", expired_at: "2026-01-15" }
)
```

The error lands in the top-level `errors` array with machine-readable metadata. Clients filter by `extensions.code` to handle specific cases.

### Domain errors with structured data: Result union types

When the "error" carries meaningful domain data the client needs to render (expiration dates, conflicting appointments, alternative providers), model it as a union:

```ruby
class Types::EligibilityResultType < Types::BaseUnion
  description "Result of checking a member's benefit eligibility"
  possible_types Types::EligibilitySuccessType,
                 Types::BenefitsExpiredErrorType,
                 Types::PlanNotFoundErrorType

  def self.resolve_type(object, _ctx)
    case object
    when EligibilityResult::Success  then Types::EligibilitySuccessType
    when EligibilityResult::Expired  then Types::BenefitsExpiredErrorType
    when EligibilityResult::NotFound then Types::PlanNotFoundErrorType
    end
  end
end

class Types::BenefitsExpiredErrorType < Types::BaseObject
  pundit_role nil
  description "The member's benefits have expired"

  field :message, String, null: false
  field :expired_at, GraphQL::Types::ISO8601DateTime, null: false
  field :plan_name, String, null: false
end

# On the query:
field :eligibility_check, Types::EligibilityResultType, null: true do
  argument :member_id, ID, required: true
end
```

Clients query with inline fragments — fully typed, code-generation friendly:

```graphql
query CheckEligibility($memberId: ID!) {
  eligibilityCheck(memberId: $memberId) {
    ... on EligibilitySuccess {
      eligible
      remainingSessions
    }
    ... on BenefitsExpiredError {
      message
      expiredAt
      planName
    }
  }
}
```

### Decision guide

| Scenario                                                                                         | Approach                                            |
| ------------------------------------------------------------------------------------------------ | --------------------------------------------------- |
| Auth/system errors                                                                               | `ExecutionError` (exceptional, not business domain) |
| Simple rejection with a code                                                                     | `ExecutionError` with `extensions`                  |
| Client needs to branch on error type and display error-specific data                             | Result union                                        |
| Error is a first-class domain concept (benefits expired, provider unavailable, booking conflict) | Result union                                        |

**Litmus test:** Does the client need more than a message and a code? If yes, use a result union. If a code and message are enough, use `ExecutionError` with extensions.

## Schema Evolution

- **Never version** the GraphQL API
- Add new fields/types freely (non-breaking)
- Deprecate with `deprecation_reason:` including migration instructions and removal timeline
- Monitor usage via OperationStore before removing deprecated fields
- Breaking changes: removing fields, changing return types, making nullable fields non-nullable, adding required arguments
