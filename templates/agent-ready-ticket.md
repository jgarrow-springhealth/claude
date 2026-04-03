---
name: agent-ready-ticket
description: Template for implementation tickets. Structures the ticket as a prompt — acceptance criteria, scope boundaries, constraints, and verification steps so an agent has everything needed to execute without drift.
---

# Agent-Ready Ticket Template (Implementation)

> The ticket is the prompt. Include everything needed to execute one chunk of work — no more, no less.

---

## Acceptance Criteria _(required)_

Gherkin-style. Each scenario = one observable behavior.

```
Given <precondition>
When <action>
Then <outcome>
```

Write one scenario per distinct case. If you need more than ~5, the ticket is too big.

---

## In-Scope Paths _(optional)_

Files, directories, or modules the agent should touch.
Omit if obvious from the ACs. Include if ambiguity would cause drift.

```
app/services/foo/
app/graphql/mutations/foo_mutation.rb
```

---

## Explicit Out of Scope _(optional)_

Things an agent might reasonably touch but shouldn't. Prevents scope creep.

```
- Do not change the public API of FooService
- Do not modify existing migrations
```

---

## Constraints & Invariants _(optional)_

Rules that must hold. Edge cases the agent must respect.

```
- FooBar must remain idempotent
- All writes go through the service layer, not directly via the model
```

---

## Known Dependencies _(optional)_

Jira links using "blocked by / blocks" semantics. Prevents executing out of order.

```
Blocked by: CFPL-1234 (the migration that adds the foo column)
Blocks: CFPL-1236 (the UI ticket that reads foo)
```

---

## How to Verify _(optional)_

The specific thing to run or check when done. Skip if ACs are self-verifying.

```
bin/rspec spec/services/foo_service_spec.rb
```

---

## Context Pointers _(optional)_

Links up the context pipeline. Include if the ticket can't stand alone.

```
Epic: CFPL-XXXX — carries the full plan and design decisions
PRD: <Confluence link> — the "why" behind this work
```
