---
name: beads:create
description: Convert Ralph specs and implementation plan into Beads epics and
  issues with proper dependencies. Use after planning phase to populate the
  beads database.
argument-hint: [epic-name or "all"]
allowed-tools: Read, Bash, Glob, Grep
---

# Create Beads from Ralph Specs + Plan

Convert the current specs and implementation plan into Beads issues.

## Process:

1. Study `IMPLEMENTATION_PLAN.md` and all `specs/*.md`
2. Study existing beads: `bd list --json` — don't assume no beads exist. Don't create duplicates of existing issues.
3. Ultrathink about the dependency graph before creating anything — what blocks what? What can be parallelized?
4. For "$ARGUMENTS" (or all if "all"), use up to 3 parallel subagents to create issues for independent feature areas simultaneously:
   - Each subagent creates one epic: `bd create "<name>" -t epic -p <pri> --json`
   - Creates child issues: `bd create "<task>" --parent <epic-id> -p <pri> --json`
   - Sets blocking relationships: `bd dep add <child> <blocker> --json`
   - Adds detailed descriptions and acceptance criteria from specs:
     `bd update <id> --description "<from spec>" --acceptance "<criteria>"`
   - Capture the why in descriptions — not just "add auth" but why this
     approach, what problem it solves, what spec drives it
5. Run `bd ready --json` to verify the dependency graph makes sense
6. Present a summary of created issues with their dependency tree

## Rules:

- Don't assume not implemented — study the codebase before filing tasks for things that may already exist
- Don't create issues for already-completed work
- If beads already exist, update rather than duplicate — run `bd duplicates --dry-run` after creation
- Capture the why in every epic and issue description
- If you find ambiguities between specs and the plan, resolve them or document them in the bead description
- Ask clarification questions if specs and the plan are unclear or contradict each other
- If functionality is missing from the plan that the specs require, it's your job to add it as a new bead
- Keep it up-to-date — this skill may be run multiple times as specs evolve. Update existing beads rather than creating parallel sets.
