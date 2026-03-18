---
name: beads:start-project
description: Start a new feature branch with Ralph + Beads scaffolding. Creates branch, initializes spec, and sets up a Beads epic. For projects not using Beads, use ralph:start-project instead.
argument-hint: <branch-name>
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Glob
---

# Start New Feature (With Beads)

1. Study the existing repo state first — don't assume this feature doesn't partially exist. Check for related specs, existing beads, and code.
2. Switch to branch: `git checkout -b feature/$ARGUMENTS`. Create the branch if it doesn't already exist.
3. Create `specs/$ARGUMENTS.md` with a template header including:
   - Audience
   - JTBDs (to be filled in during requirements)
   - Acceptance Criteria (to be filled in)
   - Rationale / The Why (to be filled in)
4. Create a beads epic:
   ```bash
   bd create "$ARGUMENTS" -t epic -p 1 --json
   bd update <id> --description "Epic for $ARGUMENTS feature. Specs: specs/$ARGUMENTS.md"
   ```
5. If related beads or specs exist, link them:
   ```bash
   bd dep add <new-epic> <related-id> --type relates_to
   ```
6. Capture the why — note in the spec template why this feature is being started now and what outcome it serves
7. Print next steps:
   - "1. Run `/ralph:create-requirements $ARGUMENTS` to define the spec"
   - "2. Run `/ralph:plan` when specs are approved"
   - "3. Run `/beads:create $ARGUMENTS` to populate tracked issues"
   - "4. In `AGENTS.md`, create backpressure commands for tests, typechecks, lints, build, etc. that will reject invalid/unacceptable work."
   - "5. To build:
     - `/bd:go <epic-id>` — run autonomously until all beads are complete
     - `/bd:step <epic-id>` — step through one bead at a time with human checkpoints between each"
   - "6. Once the build is complete, run `/beads-review` to review the implementation:
     - Checks that the work meets the acceptance criteria in `specs/$ARGUMENTS.md`
     - Reviews for sound design and code architecture, logic correctness, test coverage, and security/performance issues
     - Files any follow-up work as new tracked beads linked to the epic"

Keep it up-to-date — if a feature branch already exists for this name, warn the human rather than creating a duplicate.
