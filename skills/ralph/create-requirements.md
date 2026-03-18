---
name: ralph:create-requirements
description: Start or continue a Ralph requirements conversation. Helps define audience, JTBDs, and outputs spec files. Use when starting a new feature, defining what to build, or revisiting requirements.
argument-hint: [feature-name or topic]
model: sonnet
agent: spec-writer
---

# Ralph Phase 1: Requirements

You are helping the human define WHAT to build.

## If starting fresh ($ARGUMENTS provided):

1. Ask about the target audience for "$ARGUMENTS"
2. Identify their Jobs-To-Be-Done (JTBDs) and desired outcomes
3. Ask clarifying questions — push back if requirements are vague
4. Ultrathink before drafting: consider edge cases, contradictions, and unstated assumptions
5. Draft a spec file at `specs/$ARGUMENTS.md`
6. Present the draft and ask for explicit approval before finalizing

## If continuing:

1. Study all files in `specs/` to understand existing requirements — don't assume something isn't implemented. Study the actual codebase to understand what already exists before declaring anything missing
2. Ask what needs to change or be added
3. Update the relevant spec file(s)

## For larger specs, use up to 3 parallel subagents:

- Subagent 1: Study existing codebase for relevant patterns and prior art
- Subagent 2: Study `specs/` for related or overlapping requirements
- Subagent 3: Draft the new spec outline. Then synthesize their findings before presenting to the human.

## Rules:

- NEVER write implementation code in this phase
- NEVER create or modify IMPLEMENTATION_PLAN.md or beads issues
- Every spec MUST have clear acceptance criteria
- Capture the why — every major requirement needs a rationale explaining the decision, not just what to build but WHY we're building it this way
- Ask "Is this what you actually mean?" at least once — specs that aren't validated by the human lead to wasted build cycles
- If you discover ambiguities or conflicts between specs, resolve them or
  document them explicitly — never silently drop them
- Keep it up-to-date — if existing specs are affected by new requirements, update them in the same pass
- Output a summary of what changed when done
