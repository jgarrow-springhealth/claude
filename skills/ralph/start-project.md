---
name: ralph:start-project
description: Start a new feature branch with Ralph scaffolding (no Beads). Creates branch and initializes spec. For projects using Beads, use beads:start-project instead.
argument-hint: <branch-name>
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Glob
---

# Start New Feature (No Beads)

1. Study the existing repo state first — don't assume this feature doesn't partially exist. Check for related specs and code.
2. Switch to branch: `git checkout -b feature/$ARGUMENTS`. Create the branch if it doesn't already exist.
3. Create `specs/$ARGUMENTS.md` with a template header including:
   - Audience
   - JTBDs (to be filled in during requirements)
   - Acceptance Criteria (to be filled in)
   - Rationale / The Why (to be filled in)
4. Capture the why — note in the spec template why this feature is being started now and what outcome it serves
5. Print next steps:
   - "1. Run `/ralph:create-requirements $ARGUMENTS` to define the spec"
   - "2. Run `/ralph:plan` when specs are approved"
   - "3. In `AGENTS.md`, create backpressure commands for tests, typechecks, lints, build, etc."
   - "4. To build:
     - `/ralph:loop` — run autonomously until all tasks are complete
     - `/ralph:step` — step through one task at a time with human checkpoints between each"

Keep it up-to-date — if a feature branch already exists for this name, warn the human rather than creating a duplicate.
