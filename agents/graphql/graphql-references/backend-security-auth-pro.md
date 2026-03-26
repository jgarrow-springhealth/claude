# Backend: Security, Authorization, Pundit & GraphQL Pro Features

## Security Standards

- Authentication at controller/middleware level (NOT in GraphQL)
- Authorization at type, field, and mutation levels
- `max_depth` and `max_complexity` MUST be set
- Disable introspection in production: `disable_introspection_entry_points`
- Use OperationStore as query allowlist in production
- Never expose raw database IDs
- Use `rescue_from` for all unhandled exceptions — never leak stack traces

---

## Authorization with Pundit Integration (GraphQL Pro)

### Context Setup

Every GraphQL execution must include the current user:

```ruby
class GraphqlController < ApplicationController
  def execute
    context = { current_user: current_user }
    result = MySchema.execute(params[:query], variables: params[:variables], context: context)
    render json: result
  end
end
```

### Full Base Class Setup

```ruby
# app/graphql/types/base_object.rb
class Types::BaseObject < GraphQL::Schema::Object
  include GraphQL::Pro::PunditIntegration::ObjectIntegration
  field_class Types::BaseField
  pundit_role :show  # default: every type requires show? — aligns with Pundit conventions
end

# app/graphql/types/base_field.rb
class Types::BaseField < GraphQL::Schema::Field
  include GraphQL::Pro::PunditIntegration::FieldIntegration
  argument_class Types::BaseArgument
  pundit_role nil  # no field-level auth by default (type-level handles it)
end

# app/graphql/types/base_argument.rb
class Types::BaseArgument < GraphQL::Schema::Argument
  include GraphQL::Pro::PunditIntegration::ArgumentIntegration
  pundit_role nil
end

# app/graphql/mutations/base_mutation.rb
# Use GraphQL::Schema::Mutation (NOT RelayClassicMutation — it adds a mandatory
# clientMutationId field that modern clients like Apollo and Relay Modern don't use).
class Mutations::BaseMutation < GraphQL::Schema::Mutation
  include GraphQL::Pro::PunditIntegration::MutationIntegration
  object_class Types::BaseMutationPayload
  field_class Types::BaseField
  argument_class Types::BaseArgument

  # Standard error field on all mutations
  field :errors, [Types::UserErrorType], null: false,
        description: "Validation and business rule errors. Empty on success."

  # Pundit hook: return errors-as-data when mutation-level auth fails
  def unauthorized_by_pundit(_owner, _value)
    { errors: [{ message: "You are not authorized to perform this action.", code: "UNAUTHORIZED", path: [] }] }
  end
end

# app/graphql/types/base_mutation_payload.rb
class Types::BaseMutationPayload < Types::BaseObject
  pundit_role nil  # anyone who ran the mutation can read its results
end

# app/graphql/resolvers/base_resolver.rb
class Resolvers::BaseResolver < GraphQL::Schema::Resolver
  include GraphQL::Pro::PunditIntegration::ResolverIntegration
  argument_class Types::BaseArgument
  pundit_role nil

  # Resolvers raise (queries use the top-level errors array).
  # Mutations return errors-as-data (mutations have their own errors field).
  def unauthorized_by_pundit(_owner, _value)
    raise GraphQL::ExecutionError.new(
      "You are not authorized.",
      extensions: { code: "UNAUTHORIZED" }
    )
  end
end

# Also available: UnionIntegration, InterfaceIntegration
```

**Key setup decisions:**

- `pundit_role :show` on `BaseObject` — every type requires `show?` by default, matching Pundit conventions (`show?`, `create?`, `update?`, `destroy?`)
- `pundit_role nil` on `BaseField` — fields don't have their own auth by default (type-level handles it)
- `pundit_role nil` on `BaseMutationPayload` — anyone who ran the mutation can read the result
- `pundit_role nil` on `QueryType` — skip auth on the root query type
- `unauthorized_by_pundit` differs between mutations (errors-as-data) and resolvers (raise `ExecutionError`)

**`pundit_role` naming convention:** The integration appends `?` automatically when calling the policy method. Use the method name **without** the `?` suffix: `pundit_role :show` calls `policy.show?`, `pundit_role :admin` calls `policy.admin?`. Never write `pundit_role :show?` — that would call `policy.show??`.

---

## Core Principle: All Auth Logic Lives in Pundit Policies

**Every authorization check must go through a Pundit policy.** The GraphQL layer decides _when_ to check; the policy decides _what_ the rule is. Never inline auth logic (`context[:current_user].admin?`) in the GraphQL layer.

```ruby
# BAD — auth logic scattered in GraphQL layer
def authorized?(employee:)
  super && context[:current_user].manager_of?(employee)
end

# GOOD — auth logic centralized in Pundit policy
def authorized?(employee:)
  super && Pundit.policy!(context[:current_user], employee).can_fire?
end

class EmployeePolicy < ApplicationPolicy
  def can_fire?
    user.manager_of?(record)
  end
end
```

---

## Where to Put Authorization Checks

There are five distinct locations for authorization, each with different semantics. Choosing the wrong location is one of the most common mistakes.

### 1. Type-Level (`pundit_role` on the type class)

**Purpose:** "Can this user see objects of this type at all?"

Fires **after resolution**, on the **returned object**, every time an object of this type is about to be returned — from queries, mutations, lists, or `loads:`. On failure, the object becomes `nil` (customize via `Schema.unauthorized_object`).

```ruby
class Types::EmployeeType < Types::BaseObject
  pundit_role :employer_or_self  # calls EmployeePolicy#employer_or_self?
end
```

**Use when:** Universal visibility rules — "only admins and the user themselves can see Employee objects."

### 2. Field-Level (`pundit_role:` on a field definition)

**Purpose:** "Can this user see this specific field on the parent?"

Fires **before field resolution**, checked against the **parent object** (not the field's return value). On failure, the field returns `nil` (customize via `Schema.unauthorized_field`).

```ruby
class Types::EmployeeType < Types::BaseObject
  pundit_role :employer_or_self  # type-level: can you see this employee?

  field :salary, Integer, null: true,
    pundit_role: :admin  # EmployeePolicy#admin? — checked against the Employee (parent)
  field :ssn, String, null: true,
    pundit_role: :admin
  field :name, String, null: false
    # no field-level auth — type-level is sufficient
end
```

**Use when:** A specific field on an otherwise-visible type contains sensitive data.

**Critical distinction:** Field auth and type auth check **different objects**. Field auth asks "can you access this field on this parent?" (checked against parent, before resolution). Type auth asks "can you see the object this field returned?" (checked against result, after resolution). Different policies, different objects.

### 3. Mutation Class-Level (`pundit_role` on the mutation)

**Purpose:** "Can this user even attempt this mutation?"

Fires **first**, before `ready?`, before `loads:`, before `authorized?`.

```ruby
class Mutations::PromoteEmployee < Mutations::BaseMutation
  pundit_role :admin  # calls PromoteEmployeePolicy#admin?

  argument :employee_id, ID, loads: Types::EmployeeType
  argument :new_title, String, required: true

  field :employee, Types::EmployeeType, null: true
  field :errors, [Types::UserErrorType], null: false

  def resolve(employee:, new_title:)
    # only reached if admin? passed AND employee was authorized via loads:
    result = Employees::PromoteService.call(employee: employee, title: new_title)
    if result.success?
      { employee: result.employee, errors: [] }
    else
      { employee: nil, errors: result.errors }
    end
  end
end
```

**Use when:** Certain mutations should be restricted to specific roles regardless of the target object.

### 4. Instance-Level `authorized?` on Mutations/Resolvers

**Purpose:** "Can this user act on this specific loaded object?"

Fires **after** objects are loaded via `loads:`, so you can make decisions based on the specific object. Always delegate the actual check to a Pundit policy — `authorized?` decides _when_ to check, the policy decides _what_ the rule is.

```ruby
class Mutations::FireEmployee < Mutations::BaseMutation
  pundit_role :manager  # class-level: must be a manager to attempt this

  argument :employee_id, ID, loads: Types::EmployeeType

  def authorized?(employee:)
    super && Pundit.policy!(context[:current_user], employee).can_fire?
  end

  def resolve(employee:)
    # reached only if:
    # 1. FireEmployeePolicy#manager? passed (class-level)
    # 2. EmployeePolicy#employer_or_self? passed (type-level from loads:)
    # 3. EmployeePolicy#can_fire? passed (instance-level authorized?)
    Employees::TerminateService.call(employee: employee, fired_by: context[:current_user])
  end
end
```

**Return values from `authorized?`:**

- `true` — proceed to `resolve`
- `false` — halt, return `nil`
- `[false, { errors: [...] }]` — halt, return errors-as-data (preferred for mutations)
- Raise `GraphQL::ExecutionError` — add error to response `errors` array

```ruby
# Errors-as-data pattern (preferred):
def authorized?(employee:)
  if Pundit.policy!(context[:current_user], employee).can_fire?
    true
  else
    return false, { errors: [{ message: "You can only fire employees you manage", path: ["employeeId"] }] }
  end
end
```

**Use when:** Authorization depends on the relationship between the current user and a specific loaded object.

### 5. Inside `resolve` via Service Object

**Purpose:** Complex business rules deeply intertwined with business logic.

```ruby
def resolve(employee:, new_salary:)
  result = Employees::UpdateSalaryService.call(
    employee: employee,
    new_salary: new_salary,
    current_user: context[:current_user]
  )
  # The service object handles authorization internally (using Pundit policies)
  if result.success?
    { employee: result.employee, errors: [] }
  else
    { employee: nil, errors: result.errors }
  end
end
```

**Use when:** Authorization depends on budget, reporting chain, pay grade, or other complex domain rules. The service object should itself use Pundit policies for the auth checks.

---

## Authorization Execution Order

### For queries:

1. Resolver class `pundit_role` — "Are you signed in?"
2. Resolver `#authorized?` — Custom pre-resolution checks
3. Resolver `#resolve` — Fetch data
4. Type `pundit_role` on **returned object** — "Can you see this object?"
5. Field `pundit_role` per field (checked against **parent**, before resolving each field)
6. If a field returns an object, type auth fires on that result (repeat from step 4)

### For mutations:

1. Mutation class `pundit_role` — "Can you attempt this mutation?" (fires before anything loads)
2. `loads:` resolution — fetch object via `Schema.object_from_id` → type auth on loaded object → argument `pundit_role`
3. Mutation `#authorized?(**loaded_args)` — user-to-object relationship checks
4. Mutation `#resolve` — delegate to service object
5. Type auth on returned objects in payload

### Key rules:

- **Auth is top-down.** A child's auth cannot run until the parent's type-level auth passes.
- **Field auth short-circuits.** If field auth fails, the entire subtree is `nil` — the child is never fetched from the database.
- **Field auth checks the parent. Type auth checks the result.** These are different policies on different objects.
- **Partial data is normal.** A manager may see `department.name` but not `department.budget`.

---

## `loads:` Authorization Flow

```ruby
argument :employee_id, ID,
  loads: Types::EmployeeType,   # 1. Schema.object_from_id fetches the object
  pundit_role: :supervisor       # 2. Type-level auth on EmployeeType runs
                                 # 3. Argument-level pundit_role check runs
                                 # 4. Object passed to authorized?(**args) as keyword arg
```

If any step fails, execution halts before `resolve` is called.

---

## List Scoping

The Pundit integration **automatically** applies `Pundit.policy_scope!` to all list and connection fields.

```ruby
class EmployeePolicy < ApplicationPolicy
  class Scope < Scope
    def resolve
      if user.admin?
        scope.all
      else
        scope.where(company: user.company)
      end
    end
  end
end
```

**Missing scopes crash the query.** If you return a list of `Employee` objects but `EmployeePolicy::Scope` doesn't exist, the query raises. This is intentional — crashing is safer than leaking unfiltered data.

```ruby
# Disable scoping per field:
field :all_statuses, [Types::StatusEnum], null: false, scope: false

# Skip per-item type auth after scoping (if scope already filters):
class Types::EmployeeType < Types::BaseObject
  reauthorize_scoped_objects(false)
end
```

---

## Schema-Level Hooks for Unauthorized Access

```ruby
class MySchema < GraphQL::Schema
  # When type-level auth fails — return nil to prevent existence oracles.
  # Returning an error message like "You don't have permission to view Employee"
  # reveals that the record exists. Returning nil is the secure default.
  def self.unauthorized_object(error)
    nil
  end

  # When field-level auth fails — raise so the client knows WHY the field is null.
  # This is safe because the parent object already passed type-level auth
  # (its existence is not a secret at this point).
  def self.unauthorized_field(error)
    raise GraphQL::ExecutionError.new(
      "You are not authorized to access this field.",
      extensions: { code: "UNAUTHORIZED", field: error.field.graphql_name }
    )
  end
end
```

**Note:** `unauthorized_by_pundit` is configured separately on `BaseMutation` and `BaseResolver` in the base class setup above — mutations return errors-as-data, resolvers raise.

---

## `visible?` vs `authorized?`

| Aspect                    | `visible?`                                    | `authorized?`                            |
| ------------------------- | --------------------------------------------- | ---------------------------------------- |
| **When**                  | Schema build / validation                     | Runtime, during execution                |
| **Effect of `false`**     | Element doesn't exist in schema               | Element exists but returns `nil`/error   |
| **Affects introspection** | Yes — hidden from `__schema`                  | No — still visible                       |
| **Use case**              | Feature flags, beta fields, role-based schema | Per-object/per-request permission checks |

---

## Decision Guide: Where to Put Which Checks

| What You're Checking                       | Where                                | Mechanism              |
| ------------------------------------------ | ------------------------------------ | ---------------------- |
| "Can this user see objects of this type?"  | Type class (`pundit_role`)           | `ObjectIntegration`    |
| "Can this user see this sensitive field?"  | Field definition (`pundit_role:`)    | `FieldIntegration`     |
| "Can this user use this argument?"         | Argument definition (`pundit_role:`) | `ArgumentIntegration`  |
| "Can this user attempt this mutation?"     | Mutation class (`pundit_role`)       | `MutationIntegration`  |
| "Can this user act on this loaded object?" | `authorized?` instance method        | Mutation/Resolver hook |
| "Complex business rules"                   | Service object from `resolve`        | Domain layer           |
| "Filter list to what user can see"         | Automatic (`Scope` class)            | List scoping           |
| "Should this field/type exist in schema?"  | `visible?` method                    | Schema visibility      |

---

## Anti-patterns to Flag

- **Direct user checks in GraphQL layer**: Never `context[:current_user].admin?` — always delegate to Pundit policy
- **All auth in `resolve`**: Use `pundit_role` or `authorized?` instead of `return unless current_user.admin?` at the top of every resolve
- **No type-level auth**: Every type representing a protected resource needs a `pundit_role`
- **Missing Pundit scopes**: List fields MUST have `Scope` classes (or explicit `scope: false`)
- **Auth on mutation payloads**: Set `pundit_role nil` — if they ran the mutation, they can read the result
- **Forgetting `pundit_role nil` on QueryType**: Root query doesn't represent a domain object
- **Existence oracles in mutations**: Mutations that fetch a record by ID should apply Pundit scope BEFORE `find_by`, so out-of-scope records return `NOT_FOUND` (not `UNAUTHORIZED`). Returning `UNAUTHORIZED` reveals the record exists.

```ruby
# BAD — leaks existence
def resolve(id:)
  appointment = Appointment.find_by(id: id)
  return not_found_error unless appointment
  authorize appointment, :cancel?  # returns UNAUTHORIZED if out of scope
  ...
end

# GOOD — scope-then-find prevents existence oracle
def resolve(id:)
  appointment = policy_scope(Appointment).find_by(id: id)
  return not_found_error unless appointment  # NOT_FOUND for both "doesn't exist" and "out of scope"
  ...
end
```

---

## GraphQL Ruby Pro Features

### OperationStore (Persisted Queries)

- Use in production for security (query allowlisting) and performance
- Track field/type usage for deprecation decisions

### Encrypted Cursors

```ruby
class MyCursorEncoder < GraphQL::Pro::Encoder
  key("secret_key")
  tag("auth_tag")
end
```

- Use versioned encoders for cursor migration

### Subscriptions

- Use ActionCable for subscriptions
- Trigger via `MySchema.subscriptions.trigger(:event, args, object)`

---

## Testing Standards

### Integration Tests (Primary)

```ruby
result = MySchema.execute(query, variables: vars, context: { current_user: user })
expect(result["errors"]).to be_nil
expect(result.dig("data", "user", "name")).to eq("Jane")
```

### Testing Authorization

```ruby
RSpec.describe "employee query authorization" do
  let(:query) { "{ employee(id: \"#{global_id}\") { name salary } }" }

  it "returns employee for their manager" do
    result = MySchema.execute(query, context: { current_user: manager })
    expect(result.dig("data", "employee", "name")).to eq("Jane")
  end

  it "returns nil for unauthorized users" do
    result = MySchema.execute(query, context: { current_user: stranger })
    expect(result.dig("data", "employee")).to be_nil
  end

  it "hides salary from non-admins" do
    result = MySchema.execute(query, context: { current_user: manager })
    expect(result.dig("data", "employee", "salary")).to be_nil
  end

  it "shows salary to admins" do
    result = MySchema.execute(query, context: { current_user: admin })
    expect(result.dig("data", "employee", "salary")).to eq(100_000)
  end
end
```

### Test Hierarchy

1. **Unit tests**: Pundit policies directly (`EmployeePolicy.new(user, employee).show?`)
2. **Integration tests**: Full `Schema.execute` for auth scenarios
3. **Transport tests**: Controller specs for HTTP/auth header concerns

### Must Test

- Success and error paths for every mutation
- Authorization at each level: type-level, field-level, mutation-level
- List scoping (verify users only see what they should)
- Schema validity (`expect { MySchema.to_definition }.not_to raise_error`)
