---
name: beads:review
description: Review recent code changes and file beads issues for any problems found. Use for code review sessions that produce actionable tracked items.
argument-hint: [branch or commit range, e.g. "main..HEAD"]
allowed-tools: Read, Bash, Glob, Grep
---

# Code Review → Beads Issues

Review code changes and file beads for anything found.

1. Run `git diff $ARGUMENTS` (default: `main..HEAD`)
2. Ultrathink: Study changes thoroughly using up to 3 parallel subagents
   for different review dimensions:
   - Subagent 1: Logic correctness, edge cases, potential bugs
   - Subagent 2: Test coverage gaps and missing assertions
   - Subagent 3: Security concerns, performance issues, style violations
3. Only 1 subagent for any fix-and-verify work — backpressure is serialized
4. For each finding, file a bead with full context:
   `bd create "<finding>" -t bug -p <severity> --json`
   `bd update <id> --description "<what's wrong and why it matters>"`
   Capture the why — don't just say "missing null check", explain what
   breaks and under what conditions
5. Link discovered issues to the work that produced them:
   `bd dep add <new-id> <originating-id> --type discovered-from`
6. Present summary of findings and filed issues

## Rules:

- Don't assume not implemented — if something looks like a bug, study the
  surrounding code and tests to confirm it's actually a problem, not an
  intentional pattern
- If you find ambiguities (could be a bug OR intentional), resolve them or
  document them in the bead — never silently skip
- If functionality is missing (e.g., no error handling for a new path),
  it's your job to add it as a tracked bead
- Keep it up to date — if reviewing surfaces issues that overlap with
  existing beads, link them rather than creating duplicates
