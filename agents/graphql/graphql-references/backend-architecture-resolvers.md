# Backend: Architecture, Resolvers & Service Objects

## File Structure

```
app/graphql/
  my_schema.rb
  types/
    base_object.rb, base_enum.rb, base_field.rb, base_input_object.rb
    base_interface.rb, base_union.rb, base_scalar.rb
    base_connection.rb, base_edge.rb
    query_type.rb, mutation_type.rb, subscription_type.rb
    user_type.rb, post_type.rb
    enums/
    inputs/
    interfaces/
    unions/
  mutations/
    base_mutation.rb
    users/
      create_user.rb, update_user.rb
    posts/
      create_post.rb
  resolvers/
    user_posts_resolver.rb
  sources/
    record_by_id.rb, association_loader.rb
```

## Base Classes (MUST use)

- `Types::BaseObject`, `Types::BaseField`, `Types::BaseEnum`, `Types::BaseInputObject`
- `Mutations::BaseMutation` with shared error handling
- Configure `field_class`, `argument_class`, etc. on base classes

## Resolver Pattern: Methods vs Resolver Classes

The graphql-ruby gem recommends method-based resolution for most fields. The broader GraphQL industry (Apollo Server, Pothos, Strawberry, gqlgen, Hot Chocolate) uniformly favors dedicated resolver functions/classes separated from type definitions. **Both approaches are valid as long as they follow the real principle: resolvers must be thin orchestration layers that delegate to a separate business/domain layer.**

### Use methods on the type for simple fields

Methods work well when resolution is straightforward — computed fields, simple delegations, and basic dataloader calls:

```ruby
class Types::UserType < Types::BaseObject
  field :full_name, String, null: false
  field :avatar_url, String, null: true

  def full_name
    "#{object.first_name} #{object.last_name}"
  end

  def avatar_url
    dataloader.with(Sources::RecordById, Avatar).load(object.avatar_id)&.url
  end
end
```

**Advantages:**

- Less boilerplate for simple fields
- Everything for a type is visible in one file (when the type is small)
- No extra class/file for one-liner computations

**Drawbacks:**

- Type files become unwieldy as they grow (15+ fields with custom resolution = 300+ line files mixing schema declaration and data fetching)
- Methods depend on implicit `object`, `context`, and `dataloader` state — harder to set up in tests
- Doesn't match the pattern used by every other major GraphQL framework

### Use Resolver classes for complex fields

Resolver classes work well when a field has its own arguments, authorization logic, or non-trivial resolution that benefits from encapsulation:

```ruby
class Resolvers::UserPostsResolver < GraphQL::Schema::Resolver
  type Types::PostType.connection_type, null: false

  argument :status, Types::PostStatusEnum, required: false
  argument :order_by, Types::PostOrderEnum, required: false, default_value: "RECENT"

  def authorized?(**args)
    super && context[:current_user]&.can_view_posts_of?(object)
  end

  def resolve(status: nil, order_by: "RECENT")
    PostQuery.new(author: object, status: status, order: order_by).results
  end
end

class Types::UserType < Types::BaseObject
  field :posts, resolver: Resolvers::UserPostsResolver,
    description: "Posts authored by this user"
end
```

**Advantages:**

- **Cohesion**: Arguments, authorization (`authorized?`/`ready?`), and resolution for one field live together
- **Keeps type files clean**: The type file stays focused on schema declaration; resolution logic lives separately
- **Reusability**: The same resolver can be used across multiple types
- **Aligns with broader industry patterns**: Developers from other GraphQL ecosystems will find this familiar
- **Works naturally with graphql-ruby's hooks**: `authorized?`, `ready?`, `loads:` all work well on Resolver classes

**Drawbacks:**

- More boilerplate for simple fields
- Coupled to `GraphQL::Schema::Resolver` (though business logic should still be delegated to service objects)
- Resolver API has changed across gem versions

### Decision guide

| Situation                                                    | Use                                                      |
| ------------------------------------------------------------ | -------------------------------------------------------- |
| Computed field (one-liner)                                   | Method on type                                           |
| Simple delegation to service/dataloader                      | Method on type                                           |
| Field with its own arguments                                 | Either — Resolver if >1 argument                         |
| Field with custom authorization logic                        | Resolver class (co-locate `authorized?` with resolution) |
| Complex field with arguments + auth + non-trivial resolution | Resolver class                                           |
| Resolution logic shared across multiple types                | Resolver class                                           |
| Type file is already >150 lines                              | Move complex methods to Resolver classes                 |

### The REAL principle (industry consensus)

**Resolvers must be thin.** The resolver (whether a method or a class) should only:

1. Translate GraphQL arguments into domain parameters
2. Call a service object / query object / dataloader
3. Translate the result back into the GraphQL response shape

All business logic, validation, data transformation, and side effects belong in service objects.

## Service Object Integration

**Types are the API layer. Service objects are the business logic layer.** Resolvers translate between them.

```ruby
# In a mutation:
def resolve(input:)
  result = Users::CreateService.call(
    params: input.to_h,
    current_user: context[:current_user]
  )
  if result.success?
    { user: result.user, errors: [] }
  else
    { user: nil, errors: result.errors }
  end
end

# In a type method:
def recommendations
  RecommendationService.for_user(object, limit: 10)
end

# In a Resolver class:
def resolve(status: nil, order_by: "RECENT")
  PostQuery.new(author: object, status: status, order: order_by).results
end
```

## Resolver Anti-patterns

- **Fat resolvers**: Business logic living in resolver methods/classes instead of service objects
- **Resolver classes for trivial fields**: If it's `"#{object.first} #{object.last}"`, a method on the type is always better
- **Methods on the type when the type is already bloated**: If the type file is 300+ lines, extract complex resolution to Resolver classes
- **Testing resolution logic through GraphQL**: Test the service object directly
