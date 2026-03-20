---
name: beads:loop
description:
  Loop autonomously through all ready Beads tasks in a given epic until
  none remain. Beads-driven build loop — self-contained with all rules inlined.
  For single-task with checkpoints, use bd:step instead.
argument-hint: "[epic-id-or-name]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
model: opus
---

# bd:go — Autonomous Beads Build Loop

Loop through all ready tasks in scope until none remain. Use `/bd:step` instead to stop after each task for human checkpoints.

## Scoping (Important)

`bd ready` returns all unblocked tasks across every epic. If there are multiple epics, **always pass an epic ID or name** to avoid working on unrelated tasks.

```
/bd:go <epic-id-or-name>   ← recommended: scope to one epic
/bd:go                     ← works on ALL ready tasks across all epics
```

**Step 0 — Resolve scope before the loop begins:**

- If `$ARGUMENTS` is provided: run `bd list --json`, find the epic whose title or ID matches, and confirm it exists. If no match is found, stop and ask the user to clarify.
- If no argument is provided: warn — "No epic specified. This will work through ALL ready tasks across all epics. Confirm to proceed or re-run with an epic name/ID." — then wait for confirmation before continuing.

To filter ready tasks to a specific epic:

```bash
bd ready --json | jq '[.[] | select(.parent == "<epic-id>")]'
```

---

## Loop

Repeat the following until no scoped ready tasks remain:

### 1. Orient

- Get the next unblocked task in scope (filtered to the epic if one was specified)
- If no ready tasks remain in scope: run the Session Close Protocol and stop
- Run `bd show <id> --json` — study the task details
- Read `specs/*.md` — find acceptance criteria relevant to this task
- Read `AGENTS.md` — find the exact commands for type checking, linting, tests, and build

### 2. Claim

`bd update <id> --status in_progress --json`

### 3. Study Before Building

Ultrathink before implementing: don't assume something isn't implemented. Study the codebase first for existing implementations, related tests, and partial work. If the functionality already exists (fully or partially), update the bead with what you found rather than reimplementing. If functionality is missing then it's your job to add it.

### 4. Implement

- Use TDD where possible — write a failing test, then make it pass
- Use only 1 subagent for build and tests — backpressure must be serialized. Never parallelize test execution with implementation — finish building, then run ALL backpressure

### 5. Backpressure

Run ALL of the following in order. Do not skip. Fix failures and re-run before continuing:

1. Type checking
2. Linting
3. Tests
4. Build

If the same check fails 3 times on the same issue: mark the bead blocked (`bd update <id> --status blocked`), add a note explaining why, and **stop**. Do not loop or guess.

### 6. Record Discovered Work

If you found scope not covered by the current task during implementation, file it:

```bash
bd create "<title>" -p <priority> --deps discovered-from:<current-id> --json
bd update <new-id> --description "<what's needed and why>"
```

Capture the why — don't just say what, explain the reason.

### 7. Commit and Close

Update the bead with a progress note before closing:

```bash
bd update <id> --notes "COMPLETED: <what was done and why this approach>"
```

Stage and commit — be specific, do not use `git add .`:

```bash
git add <specific files changed for this task>
git commit -m "<description> (<bead-id>)"
```

Close the bead **only after the commit**:

```bash
bd close <id> --reason "<summary of what was done>"
```

### 8. Summarize and Repeat

Report what was done and what `bd ready` shows next, then loop back to step 1.

---

## Rules

- **Scope first** — always confirm the epic scope before the loop begins
- **One task at a time** — do not batch
- **Beads is the source of truth** — not `IMPLEMENTATION_PLAN.md`, not memory
- **Study before building** — the #1 failure mode is reimplementing something that already exists
- **Stage specifically** — `git add <files>`, never `git add .`
- **Never close a bead without committing first** — the commit is proof of work. Order is always: claim → implement → backpressure → commit → close
- **If a task is unclear, STOP and ask** — do not guess and proceed
- **If backpressure fails 3 times, STOP and report** — mark blocked, do not loop indefinitely
- **Never silently skip** — ambiguities and conflicts go into bead notes or as new discovered-from issues
- **Keep beads up-to-date** — progress notes, status changes, discovered work — all in real time, not after the fact

---

## Session Close Protocol

Before stopping (all tasks done, blocked, or asked to stop):

```bash
bd sync --flush-only
git status   # verify clean working tree — nothing uncommitted
```

Report: what was completed this session, what remains in scope, and any blockers.
