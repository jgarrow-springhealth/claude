---
name: beads:step
description: Execute one Beads task and hand control back. Single-task version of beads:loop — same rules, stops after one task for human checkpoints. Pass an epic ID or name to scope which tasks are eligible. For autonomous looping, use beads:loop instead.
argument-hint: "[epic-id-or-name]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
model: opus
---

# bd:step — Execute One Beads Task

Execute exactly ONE task, then stop and report. Use `/beads:loop` to loop autonomously instead.

## Scoping (Important)

`bd ready` returns all unblocked tasks across every epic. Pass an epic ID or name to avoid picking up unrelated work.

```
/bd:step <epic-id-or-name>   ← recommended: scope to one epic
/bd:step                     ← picks any ready task across all epics
```

**Resolve scope first:**

- If an argument is provided: run `bd list --json`, find the epic matching the name or ID, and filter ready tasks to that epic:
  ```bash
  bd ready --json | jq '[.[] | select(.parent == "<epic-id>")]'
  ```
  If no matching epic is found, stop and ask the user to clarify.
- If no argument is provided: warn — "No epic specified — will pick any ready task across all epics. Pass an epic name/ID to scope." — then proceed.

---

## Process

### 1. Orient

- Get the next unblocked task in scope
- If no ready tasks remain in scope: report that and stop
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

If the same check fails 3 times on the same issue: `bd update <id> --status blocked`, add a note explaining why, and **stop**. Do not loop or guess.

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
git push
```

Close the bead **only after the commit**:

```bash
bd close <id> --reason "<summary of what was done>"
```

### 8. Summarize

Report what was done and what remains in scope. Recommend that the user run `/beads:ready` to see what's recommended to work on next.

---

## Rules

- **One task per invocation** — do not batch
- **Scope first** — always confirm the epic before starting
- **Beads is the source of truth** — not `IMPLEMENTATION_PLAN.md`, not memory
- **Study before building** — the #1 failure mode is reimplementing something that already exists
- **Stage specifically** — `git add <files>`, never `git add .`
- **Never close a bead without committing first** — the commit is proof of work. Order is always: claim → implement → backpressure → commit → push → close
- **Push after every commit** — do not accumulate unpushed commits
- **If a task is unclear, STOP and ask** — do not guess and proceed
- **If backpressure fails 3 times, STOP and report** — mark blocked, do not loop indefinitely
- **Never silently skip** — ambiguities and conflicts go into bead notes or as new discovered-from issues
- **Keep beads up-to-date** — progress notes, status changes, discovered work — all in real time, not after the fact
