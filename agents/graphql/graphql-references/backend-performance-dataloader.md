# Backend: N+1 Prevention, Performance & Dataloader

## N+1 Prevention (CRITICAL)

### Use `GraphQL::Dataloader` (ALWAYS)

```ruby
class MySchema < GraphQL::Schema
  use GraphQL::Dataloader
end
```

### Dataloader Source Pattern

```ruby
class Sources::RecordById < GraphQL::Dataloader::Source
  def initialize(model_class)
    @model_class = model_class
  end

  def fetch(ids)
    records = @model_class.where(id: ids).index_by(&:id)
    ids.map { |id| records[id] }
  end
end

# In type:
def author
  dataloader.with(Sources::RecordById, User).load(object.author_id)
end
```

### Association Loader

```ruby
class Sources::AssociationLoader < GraphQL::Dataloader::Source
  def initialize(model, association_name)
    @model = model
    @association_name = association_name
  end

  def fetch(records)
    ActiveRecord::Associations::Preloader.new(
      records: records,
      associations: @association_name
    ).call
    records.map { |r| r.public_send(@association_name) }
  end
end
```

### Use `.request` for Concurrent Independent Loads

```ruby
def resolve
  req1 = dataloader.with(Sources::RecordById, User).request(object.user_id)
  req2 = dataloader.with(Sources::RecordById, Team).request(object.team_id)
  { user: req1.load, team: req2.load }
end
```

### Use Lookahead for Conditional Eager Loading

```ruby
field :users, Types::UserType.connection_type, null: false, extras: [:lookahead]

def users(lookahead:)
  scope = User.all
  scope = scope.includes(:posts) if lookahead.selects?(:posts)
  scope
end
```

### Anti-patterns

- Calling `object.association` directly without batch loading
- Using `includes` blindly at the query root
- Not using Dataloader at all
