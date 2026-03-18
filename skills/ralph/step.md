---
name: ralph:step
description: Execute one Ralph build task from IMPLEMENTATION_PLAN.md and hand control back. No Beads required. Run repeatedly for human checkpoints between tasks, or use /ralph:go to loop autonomously. For Beads projects, use /bd:step instead.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
model: opus
---

# Ralph: Execute One Task (No Beads)

Execute exactly ONE task from `IMPLEMENTATION_PLAN.md`, then stop and report. This is the single-task version of `/ralph:go` same rules, same process, stops after one task instead of looping. Use `/ralph:go` to loop autonomously instead.

`IMPLEMENTATION_PLAN.md` is scoped to the current feature branch — all tasks in it are in scope.

## Task State Convention

- `[ ]` — not started
- `[~]` — in progress
- `[x]` — complete (only after commit + push)
- `[!]` — blocked (explain inline)

---

## Process

### 1. Orient

- Read `IMPLEMENTATION_PLAN.md` — find the next `[ ]` task, respecting any noted dependencies
- If no `[ ]` tasks remain: run the Session Close Protocol and stop
- Read `specs/*.md` — understand the acceptance criteria for this task
- Read `AGENTS.md` — find the exact commands for type checking, linting, tests, and build

### 2. Claim

Mark the task `[~]` in `IMPLEMENTATION_PLAN.md` before touching any code.

### 3. Study Before Building

Ultrathink before implementing: don't assume something isn't implemented. Search the codebase for existing implementations, related tests, and partial work. If the functionality already exists (fully or partially), update the task with what you found rather than reimplementing. If it is fully complete, mark the task `[x]` in `IMPLEMENTATION_PLAN.md` and move on to the next ready task. If functionality is missing then it's your job to add it.

### 4. Implement

- Implement the task using the opus model
- Use TDD where possible — write a failing test, then make it pass
- Use only 1 subagent for build and tests — backpressure must be serialized. Never parallelize test execution with implementation — finish building, then run ALL backpressure

### 5. Backpressure

Run ALL of the following in order. Do not skip. Fix failures and re-run before continuing:

1. Type checking
2. Linting
3. Tests
4. Build

If the same check fails 3 times on the same issue: mark the task `[!]` in the plan with an explanation and **stop**. Do not loop or guess.

### 6. Record Discovered Work

If you found scope not in the plan during implementation, add it as a new `[ ]` task in `IMPLEMENTATION_PLAN.md` with a note explaining why it's needed -- don't just say what, explain the reason. Do not silently skip it.

### 7. Commit and Close

Stage and commit all files changed for this task — be specific, do not use `git add .`:

```bash
git add <specific files changed for this task>
git commit -m "<task title>"
git push
```

Mark the task `[x]` in `IMPLEMENTATION_PLAN.md` **only after the commit**.

### 8. Summarize and repeat

Report what was done and what tasks are ready next.

---

## Rules

- **One task at a time** — do not batch
- **`IMPLEMENTATION_PLAN.md` is the source of truth** — not memory, not prior context
- **Study before building** — the #1 failure mode is reimplementing something that already exists
- **Stage specifically** — `git add <files>`, never `git add .`
- **Never mark `[x]` without committing first** — the commit is proof of work. Order is always: claim → implement → backpressure → commit → push → close
- **Push after every commit** — do not accumulate unpushed commits
- **If a task is unclear, STOP and ask** — do not guess and proceed
- **If backpressure fails 3 times, STOP and report** — mark blocked, do not loop indefinitely
- **Never silently skip** — ambiguities and conflicts go into the plan as notes or `[!]` blocked tasks or as new discovered-from tasks
- **Keep tasks up-to-date** - progress notes, status changes, discovered work - all in real time, not after the fact
- If a task is blocked, update it to `[!]` and explain why

---

Report: what was completed this session, what remains, and any blockers.
