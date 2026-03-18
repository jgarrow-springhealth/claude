# Ralph — Spec-Driven Development Workflow

Ralph is a structured, spec-driven workflow for building features with Claude. It enforces a clear three-phase loop — **Requirements → Plan → Build** — so Claude is always working from an agreed-upon spec rather than guessing what to build.

Based on the [Ralph Playbook](https://github.com/ClaytonFarr/ralph-playbook).

## The Workflow

Ralph can be used standalone or paired with [Beads](../beads/README.md) for issue tracking. The core Requirements → Plan → Build loop is the same either way — Beads just adds dependency-aware task tracking on top of `IMPLEMENTATION_PLAN.md`.

### With Beads (recommended for complex features)

```
/beads:start-project <name>   ← create branch, spec template, and beads epic
        ↓
/ralph:create-requirements <name>    ← define what to build (outputs specs/*.md)
        ↓
/ralph:plan                   ← gap analysis → IMPLEMENTATION_PLAN.md
        ↓
/beads:create                 ← convert plan into tracked beads issues with dependencies
        ↓
/beads:loop <epic-id>            ← loop autonomously until all beads are complete
— or —
/beads:step <epic-id>            ← one bead at a time with human checkpoints
        ↓
/beads-review                 ← review implementation against specs, file follow-up beads
        ↓
/beads-status                 ← check progress at any time
```

**When to use Beads with Ralph:** Multi-session features, work with interdependent tasks, or any time you want Claude to autonomously pick up where it left off. Beads knows exactly what's unblocked, so `/beads:loop` can run fully autonomously without guidance.

### Without Beads (lighter-weight, single-session work)

```
/ralph:start-project <name>   ← create branch and spec template
        ↓
/ralph:create-requirements <name>    ← define what to build (outputs specs/*.md)
        ↓
/ralph:plan                   ← gap analysis → IMPLEMENTATION_PLAN.md
        ↓
/ralph:loop                   ← loop autonomously until all tasks are complete
— or —
/ralph:step                   ← one task at a time with human checkpoints
        ↓
/ralph:status                 ← check progress at any time
```

**When to skip Beads:** Short, focused features that fit in one session, or projects where you'd prefer lighter tooling.

### Setup

Ralph requires `bd` (beads) to be installed if you want to use the Beads-integrated workflow:

```bash
pip install beads
```

Check if beads is available in a project by looking for a `.beads/` directory or running `bd --version`.

---

## Skills

### `ralph:start-project`

**File:** `start-project.md`

**Invocation:** `/ralph:start-project <branch-name>`

**What it does:** Bootstraps a new feature branch without Beads:

- Creates and switches to `feature/<name>`
- Creates a spec template at `specs/<name>.md`
- Prints next steps for the no-Beads workflow

**When to use it:** At the very beginning of a new feature in a project that doesn't use Beads. For Beads projects, use `/beads:start-project` instead.

---

### `ralph:create-requirements`

**File:** `create-requirements.md`

**Invocation:** `/ralph:create-requirements <feature-name>`

**Model:** Sonnet

**What it does:** Guides an interactive requirements conversation to define what you're building. Asks about the target audience, Jobs-To-Be-Done, and acceptance criteria, then drafts or updates a spec file at `specs/<name>.md`. Pushes back on vague requirements and asks for explicit approval before finalizing.

**Rules:** No code changes or beads created during this phase — requirements only.

**When to use it:** After `/ralph:start-project` or `/beads:start-project`, or any time you need to revisit or extend the spec for an existing feature.

---

### `ralph:plan`

**File:** `plan.md`

**Invocation:** `/ralph:plan`

**Model:** Opus

**What it does:** Runs a gap analysis between `specs/*.md` and the current codebase, then produces a prioritized `IMPLEMENTATION_PLAN.md`. Uses up to 4 parallel subagents to study source code, tests, configs, and specs simultaneously. Presents the plan for human review before finalizing.

**Rules:** Read-only — no code changes, no commits. The #1 rule is to not re-implement things that already exist, so it verifies what's actually in the codebase before declaring anything a gap.

**When to use it:** After specs are approved, before creating beads issues or writing any code. Used in both the Beads and no-Beads workflows.

---

### `ralph:loop`

**File:** `loop.md`

**Invocation:** `/ralph:loop`

**Model:** Opus

**What it does:** Loops autonomously through all tasks in `IMPLEMENTATION_PLAN.md` until none remain. Uses `[ ]` / `[~]` / `[x]` / `[!]` checkboxes to track task state in real time. Same rules as `ralph:step` but runs continuously without stopping for checkpoints.

**When to use it:** When you want fully autonomous execution in a no-Beads project — start it and come back when it's done. Use `/ralph:step` instead if you want to review each task before the next begins. For Beads projects, use `/beads:loop` instead.

---

### `ralph:step`

**File:** `step.md`

**Invocation:** `/ralph:step`

**Model:** Opus

**What it does:** Executes exactly **one** task from `IMPLEMENTATION_PLAN.md` and hands control back. Implements using TDD, runs all backpressure checks (type checking, linting, tests, build), commits, and marks the task done. Discovers and records any new work found along the way. Uses `[ ]` / `[~]` / `[x]` / `[!]` checkboxes in the plan to track state.

**Key rules:**

- One task per invocation — no batching
- Study before building — never reimplement something that already exists
- Never mark `[x]` without committing first — commit is proof of work
- If backpressure fails 3 times, stops and marks `[!]` rather than looping

**When to use it:** When you want a human checkpoint between each task in a no-Beads project. Run it once, review what was done, then run it again. Use `/ralph:loop` to skip the checkpoints and loop autonomously. For Beads projects, use `/beads:step` instead.

---

### `ralph:status`

**File:** `status.md`

**Invocation:** `/ralph:status`

**What it does:** Gives a quick orientation dashboard using 3 parallel subagents — specs summary, plan task counts by status (`[ ]` / `[~]` / `[x]` / `[!]`), and recent git activity. Flags drift between specs and plan.

**When to use it:** At the start of any session to reorient, or any time you want a pulse check on where a no-Beads project stands. For Beads projects, use `/beads:status` instead.
