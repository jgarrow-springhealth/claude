# Backend: Schema Design & Graph Thinking

## FOUNDATIONAL PRINCIPLE: Think in Graphs, Not Endpoints

GraphQL is NOT "REST with a query language." The most common and damaging mistake is designing a GraphQL schema that mirrors REST API endpoints. A GraphQL schema should model your **domain as a graph of interconnected entities**, not as a collection of isolated resources with actions.

**REST thinks in endpoints and actions:**

```
GET    /api/v1/users/:id
GET    /api/v1/users/:id/posts
GET    /api/v1/users/:id/followers
POST   /api/v1/users/:id/change_password
PATCH  /api/v1/users/:id
```

**GraphQL thinks in entities and relationships:**

```graphql
type User {
  id: ID!
  name: String!
  posts(first: Int, after: String): PostConnection!
  followers(first: Int, after: String): UserConnection!
  # No "change_password" field — that's a mutation, not a property of User
}
```

## Common REST-to-GraphQL Anti-patterns

**1. Endpoint-shaped queries (God queries)**

```ruby
# BAD — mirrors REST endpoints
field :get_user, Types::UserType  # "get" prefix is REST thinking
field :fetch_posts, [Types::PostType]  # "fetch" prefix is REST thinking
field :user_posts, [Types::PostType]  # Flat — should be a field ON User

# GOOD — domain-modeled graph
field :user, Types::UserType  # Nouns, not verbs
field :posts, Types::PostType.connection_type  # Top-level entry for browsing
# AND posts are also reachable as user.posts (graph traversal)
```

**2. Wrapper/envelope types that mimic REST responses**

```ruby
# BAD — REST response envelope thinking
class Types::UserResponseType < Types::BaseObject
  field :data, Types::UserType, null: true
  field :status, Integer, null: false
  field :message, String, null: true
end

# GOOD — GraphQL has its own response envelope (data/errors)
# Just return the type directly. Use mutation payloads for mutations.
field :user, Types::UserType, null: true
```

**3. Flat, disconnected types (no graph edges)**

```ruby
# BAD — REST resource thinking (isolated, no relationships)
class Types::PostType < Types::BaseObject
  field :id, ID, null: false
  field :title, String, null: false
  field :author_id, ID, null: false  # Exposing a foreign key, not a relationship
end

# GOOD — graph thinking (connected entities)
class Types::PostType < Types::BaseObject
  field :id, ID, null: false
  field :title, String, null: false
  field :author, Types::UserType, null: false  # Traversable relationship
  field :comments, Types::CommentType.connection_type, null: false
  field :tags, [Types::TagType], null: false
end
```

**4. CRUD-shaped mutations instead of domain operations**

```ruby
# BAD — generic CRUD (REST thinking)
# updateUser(input: { status: "archived" })

# GOOD — domain-specific business operations
# archiveUser(userId: ID!)
# publishPost(postId: ID!)
# assignTicket(ticketId: ID!, assigneeId: ID!)
```

**5. Versioning the schema**

```ruby
# BAD — REST versioning
field :user_v2, Types::UserV2Type  # Never do this

# GOOD — evolve the schema continuously
field :user, Types::UserType  # Add fields, deprecate old ones
field :display_name, String, null: true  # New field
field :full_name, String, null: true,
  deprecation_reason: "Use `displayName` instead. Removal after 2025-09-01."
```

## Schema Design Principles

### 1. Model the domain, not the database

Your schema types should reflect how consumers think about the domain, not your table structure.

```ruby
# BAD — exposes database structure
class Types::UserType < Types::BaseObject
  field :id, ID, null: false
  field :first_name, String, null: false
  field :last_name, String, null: false
  field :address_line_1, String, null: true  # DB column names
  field :address_line_2, String, null: true
  field :address_city, String, null: true
  field :address_state, String, null: true
  field :address_zip, String, null: true
end

# GOOD — models the domain
class Types::UserType < Types::BaseObject
  field :id, ID, null: false
  field :full_name, String, null: false
  field :address, Types::AddressType, null: true  # Composed domain object
  field :primary_email, String, null: false
end

class Types::AddressType < Types::BaseObject
  field :street, String, null: false
  field :city, String, null: false
  field :state, String, null: false
  field :zip_code, String, null: false
  field :formatted, String, null: false  # Computed field for display
end
```

### 2. Design for the client's use cases, not server convenience

Ask: "What does the UI need to render?" not "What columns does the table have?"

```ruby
# BAD — server-centric (exposes internal representation)
class Types::AppointmentType < Types::BaseObject
  field :start_time_utc, GraphQL::Types::ISO8601DateTime, null: false
  field :duration_minutes, Integer, null: false
  field :provider_id, ID, null: false
  field :patient_id, ID, null: false
  field :status_code, Integer, null: false  # Internal enum as integer
end

# GOOD — client-centric (what the UI needs)
class Types::AppointmentType < Types::BaseObject
  field :id, ID, null: false
  field :starts_at, GraphQL::Types::ISO8601DateTime, null: false
  field :ends_at, GraphQL::Types::ISO8601DateTime, null: false  # Computed, saves client math
  field :duration, Types::DurationType, null: false  # Rich type with hours/minutes
  field :provider, Types::ProviderType, null: false  # Traversable, not just an ID
  field :patient, Types::PatientType, null: false
  field :status, Types::AppointmentStatusEnum, null: false  # Semantic enum
  field :is_cancelable, Boolean, null: false  # Business logic the client needs
  field :is_reschedulable, Boolean, null: false
end
```

### 3. Prefer rich, specific types over primitives

```ruby
# BAD — primitive obsession
field :price_cents, Integer, null: false
field :currency, String, null: false

# GOOD — rich domain type
field :price, Types::MoneyType, null: false

class Types::MoneyType < Types::BaseObject
  field :amount_cents, Integer, null: false
  field :currency, Types::CurrencyEnum, null: false
  field :formatted, String, null: false  # "$12.99"
end
```

### 4. Make impossible states impossible

Use the type system to encode business rules:

```ruby
# BAD — relies on runtime validation
class Types::ShipmentType < Types::BaseObject
  field :status, Types::ShipmentStatusEnum, null: false
  field :tracking_number, String, null: true  # Required when shipped, but nullable always
  field :delivered_at, GraphQL::Types::ISO8601DateTime, null: true
end

# GOOD — union types enforce valid states
class Types::ShipmentStatusType < Types::BaseUnion
  possible_types Types::PendingShipmentType,
                 Types::ShippedType,
                 Types::DeliveredType

  def self.resolve_type(object, _context)
    case object.status
    when "pending" then Types::PendingShipmentType
    when "shipped" then Types::ShippedType
    when "delivered" then Types::DeliveredType
    end
  end
end

class Types::ShippedType < Types::BaseObject
  field :tracking_number, String, null: false  # Guaranteed present when shipped
  field :carrier, Types::CarrierEnum, null: false
  field :estimated_delivery, GraphQL::Types::ISO8601DateTime, null: true
end

class Types::DeliveredType < Types::BaseObject
  field :tracking_number, String, null: false
  field :delivered_at, GraphQL::Types::ISO8601DateTime, null: false  # Guaranteed present
  field :signed_by, String, null: true
end
```

### 5. Every type should be reachable via graph traversal

If a type can only be accessed via a root query field and has no relationships, it's a sign of REST thinking.

```ruby
# Ask: Can I get from User -> Post -> Comment -> User (back)?
# If not, the graph has dead ends.
```

## Naming Conventions

- **Types**: PascalCase, singular (`User`, not `Users`)
- **Fields**: snake_case in Ruby (auto-converts to camelCase in schema). Example: `first_name` becomes `firstName`
- **Input Types**: Suffix with `Input` (`CreateUserInput`, `UpdatePostInput`)
- **Enums**: PascalCase type name, SCREAMING_SNAKE_CASE values
- **Connections**: Use `.connection_type` (auto-generates `Connection` and `Edge` suffixes)
- **No verb prefixes on query fields**: `user` not `getUser`, `posts` not `fetchPosts`

## Nullability

- **Default to nullable** (`null: true`) for most fields. This is critical.
- Use `null: false` ONLY when the field is **guaranteed** to resolve (e.g., `id`, `__typename`, `created_at` on a persisted record)
- **Mutation payload fields MUST be nullable** — if a non-null field returns nil due to an error, GraphQL removes the entire response including the errors field.

**Null propagation example — why this matters:**

```graphql
# If `email` is non-null and fails to resolve:
type User {
  id: ID!
  name: String!
  email: String! # <-- resolver throws error
  avatar: String
}

# GraphQL CANNOT return { id: "1", name: "Jane", email: null }
# because email is non-null. So it propagates upward:
# The ENTIRE User becomes null.
# If the parent field is also non-null, IT becomes null too.
# This can cascade all the way to the root, wiping out the entire response.
```

## Descriptions (REQUIRED on all public types and fields)

Every type and field visible to clients should have a description. This IS your API documentation.

```ruby
class Types::UserType < Types::BaseObject
  description "A registered user in the system"

  field :id, ID, null: false,
    description: "Globally unique identifier for the user"
  field :display_name, String, null: false,
    description: "The user's preferred display name"
  field :created_at, GraphQL::Types::ISO8601DateTime, null: false,
    description: "When the user account was created"
  field :posts, Types::PostType.connection_type, null: false,
    description: "Posts authored by this user, ordered by most recent"
end
```

## Pagination

- **Use Relay-style cursor connections** for any list that may grow unbounded or needs pagination
- **Use simple lists** `[Type]` only for small, bounded collections (roles, tags, enum-like data)
- Configure `default_max_page_size` and `default_page_size` at the schema level
- Per-field override with `max_page_size:` when needed

## IDs

- Use opaque, globally unique IDs (never expose raw database IDs)
- Use `GraphQL::Pro::Encoder` for encrypted, versioned cursor/ID encoding
- Implement `id_from_object` and `object_from_id` on the schema
- NEVER expose foreign key fields (`author_id`) — expose the relationship (`author`) instead

## Interfaces vs Unions

- **Interfaces**: When types share common fields and are used interchangeably (e.g., `Node`, `Timestamped`)
- **Unions**: When types appear in the same context but share no significant fields (e.g., `SearchResult`, `TimelineEvent`)
- Always implement `resolve_type` for unions
- Use unions to model polymorphic states where different states have different fields

## Custom Scalars

Use custom scalars for domain-specific primitives instead of raw `String`/`Integer`:

```ruby
class Types::EmailScalar < GraphQL::Schema::Scalar
  description "An RFC 5322 email address"

  def self.coerce_input(value, _ctx)
    raise GraphQL::CoercionError, "#{value} is not a valid email" unless value.match?(URI::MailTo::EMAIL_REGEXP)
    value
  end

  def self.coerce_result(value, _ctx)
    value.to_s
  end
end

# Use the built-in scalars where appropriate:
# GraphQL::Types::ISO8601DateTime, GraphQL::Types::ISO8601Date, GraphQL::Types::JSON
```
