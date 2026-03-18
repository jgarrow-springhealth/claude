# Beads — Issue Tracking for AI Agents

Beads (`bd`) is a lightweight, git-native issue tracker designed specifically for use by AI agents. It replaces ad-hoc markdown TODOs with a structured, dependency-aware system that syncs to version control automatically.

Based on [steveyegge/beads](https://github.com/steveyegge/beads).

**Install:** `pip install beads` (or `pip install beads-mcp` for the MCP server version)

## Why Beads?

- **Dependency-aware:** knows what blocks what, so `bd ready` always surfaces exactly what can be worked on right now
- **Git-native:** auto-syncs to `.beads/issues.jsonl` — issue state travels with the code in version control
- **Agent-optimized:** JSON output, discovered-from links, and status tracking designed for AI workflows

## Common CLI Commands

```bash
bd ready --json           # what can I work on right now?
bd list --json            # all issues
bd create "title" -t bug|feature|task -p 0-4 --json
bd update <id> --status in_progress --json
bd close <id> --reason "Done" --json
bd show <id> --json
```

**Issue types:** `bug`, `feature`, `task`, `epic`, `chore`
**Priorities:** `0` (critical) → `4` (backlog)

---

## Using Beads with the JIRA Ticket Planner

If your work originates from a JIRA ticket, the [`jira-ticket-planner` agent](../../agents/jira-ticket-planner.md) can slot in before the Beads + Ralph workflow to handle JIRA-specific intake. Run it first to resolve scope, acceptance criteria, and unknowns, then enter the normal Beads flow.

```
jira-ticket-planner [TICKET-ID]      ← JIRA intake: scope, AC, unknowns resolved; epic broken into child tasks
        ↓
/beads:start-project <name>          ← branch + spec template + beads epic
        ↓
/ralph:create-requirements <name>    ← formalize the spec (faster — ticket planner pre-answered discovery questions)
        ↓
/ralph:plan                          ← gap analysis → IMPLEMENTATION_PLAN.md
        ↓
/beads:create                        ← convert plan into tracked issues with dependencies
        ↓
/beads:loop <epic-id>  or  /beads:step <epic-id>
        ↓
/beads:review
```

The ticket planner and `ralph:create-requirements` are not doing the same thing. The ticket planner resolves JIRA context (linked issues, parent epics, Figma designs, ambiguous requirements). `create-requirements` writes the structured spec file that `ralph:plan` and the build loop use as their source of truth. The planner makes the requirements phase faster — it doesn't replace it. See the [root README](../../README.md#workflow-patterns) for the full explanation.

---

## Skills

### `beads:start-project`

**File:** `start-project.md`

**Invocation:** `/beads:start-project <branch-name>`

**What it does:** Bootstraps a new feature branch with full Ralph + Beads scaffolding:

- Creates and switches to `feature/<name>`
- Creates a spec template at `specs/<name>.md`
- Creates a Beads epic linked to the spec
- Links any related existing beads or specs
- Prints the full workflow next steps: requirements → plan → beads-create → build → review

**When to use it:** At the very beginning of a new feature in a project that uses Beads. For projects without Beads, use `/ralph:start-project` instead.

---

### `beads:status`

**File:** `status.md`

**Invocation:** `/beads:status`

**What it does:** Gives a quick orientation dashboard using 4 parallel subagents — specs summary, plan completion count, beads state (open/in-progress/blocked/ready broken down by epic), and recent git activity. Flags any drift between the spec, plan, and beads.

**When to use it:** At the start of any session to reorient, or any time you want a pulse check on where the project stands. For projects without Beads, use `/ralph:status` instead.

---

### `beads:loop`

**File:** `loop.md`

**Invocation:** `/beads:loop [epic-id-or-name]`

**Model:** Opus

**What it does:** Loops autonomously through all ready Beads tasks in scope until none remain. Resolves scope from the argument (warns and confirms if none provided to avoid picking up unrelated work across epics), then repeatedly claims → implements (TDD) → backpressures → commits → closes until the epic is done.

**When to use it:** When you want fully autonomous execution — start it and come back when it's done. Use `/beads:step` instead if you want to review each task before the next begins.

---

### `beads:step`

**File:** `step.md`

**Invocation:** `/beads:step [epic-id-or-name]`

**Model:** Opus

**What it does:** Executes exactly **one** Beads task and hands control back — the single-task version of `/beads:loop`. Scopes to the specified epic, claims the next unblocked task, implements using TDD, runs all backpressure checks, commits, and closes the bead. Warns if no epic is specified to prevent picking up unrelated work.

**When to use it:** When you want a human checkpoint between each task. Run it once, review what was done, then run it again. Use `/beads:loop <epic-id>` to skip the checkpoints and loop autonomously.

---

### `beads:create`

**File:** `create.md`

**Invocation:** `/beads:create [epic-name or "all"]`

**What it does:** Converts `IMPLEMENTATION_PLAN.md` and `specs/*.md` into a full set of Beads epics and issues with proper dependencies. Uses up to 3 parallel subagents to create issues for independent feature areas simultaneously. Sets parent/child relationships and blocking dependencies so `bd ready` works correctly from day one.

**Rules:** Checks for existing beads first to avoid duplicates. Captures the _why_ in every description — not just "add auth" but the rationale from the spec.

**When to use it:** After `/ralph:plan` is approved, to populate beads before the build phase begins. Can be re-run as specs evolve — it updates rather than duplicates.

---

### `beads:ready`

**File:** `ready.md`

**Invocation:** `/beads:ready`

**What it does:** Runs `bd ready` and presents all unblocked issues with their priority, parent epic, acceptance criteria, and what they unblock. Recommends which to tackle first based on priority and downstream unblocking value. Also flags tasks that may already be implemented or that look incorrectly blocked.

**When to use it:** At the start of a build session to pick what to work on, or any time you want a prioritized view of available work.

---

### `beads:review`

**File:** `review.md`

**Invocation:** `/beads:review [branch or commit range]` (default: `main..HEAD`)

**What it does:** Reviews the implementation against specs and files beads for any problems found. Uses 3 parallel subagents to review across three dimensions simultaneously — logic/correctness against acceptance criteria, test coverage gaps, and security/performance/style issues. Files a bead for every finding with full context. Links new issues back to the work that introduced them via `discovered-from` dependencies.

**When to use it:** After the build phase completes, before considering the feature done. Recommended as step 6 in the Beads workflow (prompted automatically by `/beads:start-project` next steps). Also useful at any mid-feature review checkpoint.
