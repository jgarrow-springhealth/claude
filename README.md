# Claude Code Setup

This repo contains custom Claude Code agents, skills, commands, and configuration that Janessa has built and uses day-to-day. Feel free to use them, adapt them, or use them as a reference for building your own.

> Use at your own risk 😉

## Table of Contents

- [Getting Started](#getting-started)
- [MCP Servers](#mcp-servers)
- [settings.json Hooks](#settingsjson-hooks)
  - [PostToolUse — Auto-format on file write/edit](#posttooluse--auto-format-on-file-writeedit)
  - [Stop — Desktop notification when Claude finishes](#stop--desktop-notification-when-claude-finishes)
  - [Notification — Desktop notification when Claude is waiting for input](#notification--desktop-notification-when-claude-is-waiting-for-input)
- [Agents](#agents)
  - [bug-investigator](#bug-investigator)
  - [jira-ticket-planner](#jira-ticket-planner)
- [Skills](#skills)
  - [bug-investigator](#bug-investigator-1)
  - [Ralph — Spec-Driven Development Workflow](#ralph--spec-driven-development-workflow)
  - [Beads — Issue Tracking for AI Agents](#beads--issue-tracking-for-ai-agents)
- [Workflow Patterns](#workflow-patterns)
  - [Starting from a JIRA ticket (with Beads)](#starting-from-a-jira-ticket-with-beads)
  - [Starting from a JIRA ticket (without Beads)](#starting-from-a-jira-ticket-without-beads)
  - [Starting fresh (no JIRA ticket)](#starting-fresh-no-jira-ticket)
  - [Why these tools aren't duplicates](#why-these-tools-arent-duplicates)
- [Commands](#commands)
  - [/diagram](#diagram)
- [Tips](#tips)

---

## Getting Started

To use these, copy what you need into your own `~/.claude/` directory:

- `agents/` → `~/.claude/agents/`
- `commands/` → `~/.claude/commands/`
- `skills/` → `~/.claude/skills/`
- `settings.json` → `~/.claude/settings.json` (or merge into your existing one)

Claude Code automatically picks up files in these directories.

---

## MCP Servers

The following MCP servers are configured and available:

| Server           | What it does                                                                                                      |
| ---------------- | ----------------------------------------------------------------------------------------------------------------- |
| **GitHub**       | Read/write PRs, issues, branches, files, and code search across GitHub repos                                      |
| **Slack**        | Read channels, search messages, send messages and drafts, read threads                                            |
| **Atlassian**    | Read/write Jira tickets and Confluence pages                                                                      |
| **MixPanel**     | Query analytics events, dashboards, and user replay data                                                          |
| **Datadog**      | Observability platform access (MCP connected; full permissions TBD)                                               |
| **Figma**        | Read Figma/FigJam designs, generate diagrams, manage Code Connect mappings                                        |
| **Playwright**   | Automate browser interactions for testing and bug reproduction                                                    |
| **LaunchDarkly** | Read and inspect feature flag configurations, targeting rules, rollout state, and flag health across environments |

---

## settings.json Hooks

Hooks are shell commands that Claude Code runs automatically in response to certain events. The `settings.json` in this repo configures three hooks:

### `PostToolUse` — Auto-format on file write/edit

**Trigger:** Any time Claude uses the `Write` or `Edit` tools.

**What it does:** Runs `prettier --write` on the modified file immediately after Claude writes it.

**Why:** Keeps generated code consistently formatted without needing to manually run a formatter or ask Claude to format its output.

**Requirement:** `prettier` must be available via `npx` (standard in most JS/TS projects).

---

### `Stop` — Desktop notification when Claude finishes

**Trigger:** When Claude finishes a task and stops (the `Stop` event).

**What it does:** Sends a macOS desktop notification — "✅ Claude has finished a task." — with the current project directory as the subtitle. It also focuses the correct terminal window (Cursor, VS Code, iTerm2, or Terminal.app).

**Why:** Useful when running Claude on longer tasks. You can switch away and get a native notification when it's done rather than watching the terminal.

**Requirement:** `terminal-notifier` must be installed (`brew install terminal-notifier`). The hook also expects a helper script at `/tmp/activate-window.sh` to handle window focus — you may need to create this or remove that part if you don't need the focus behavior.

---

### `Notification` — Desktop notification when Claude is waiting for input

**Trigger:** The `Notification` event with matcher `idle_prompt` — i.e., when Claude is blocked waiting for you to respond.

**What it does:** Sends a macOS desktop notification — "⏳ Claude is waiting for your input." — so you know it needs you.

**Why:** Pairs with the Stop hook. If you're running a long task and Claude gets blocked on a clarifying question, you'll know right away rather than coming back to find it has been waiting.

**Requirement:** Same as the Stop hook (`terminal-notifier` + the activate-window helper).

---

## Agents

Agents are subprocesses that Claude can spin up to handle specialized tasks autonomously. They live in `agents/` and are loaded by Claude Code as available agent types.

### `bug-investigator`

**File:** `agents/bug-investigator.md`

**Model:** Opus (more capable for complex investigation work)

**What it does:** Orchestrates a team of subagents to investigate a reported bug from multiple angles — data, logs, code, Slack history, and live browser reproduction. Produces an RCA-style report. **Does not make any code changes.**

**Investigation phases:**

1. **Bug Intake** — Parses the Jira ticket or Slack link, identifies ambiguities, asks clarifying questions before diving in.
2. **Parallel Investigation** — Launches subagent teams for:
   - Data investigation (Snowflake queries, Datadog logs, MixPanel analytics)
   - Slack research (related threads, prior incidents, customer complaints)
   - Codebase investigation (GitHub — primarily `rotom` for backend, plus client repos)
   - Bug reproduction via Playwright on `dev` environments
3. **Synthesis** — Cross-references findings, flags gaps and unknowns.
4. **RCA Documentation** — Produces a structured RCA doc following the SpringCare Confluence template.

**When to use it:** Give it a Jira ticket URL or Slack link describing the bug. Example:

```
Can you investigate this bug? https://springcare.atlassian.net/browse/ENG-1234
```

**Persistent memory:** This agent maintains its own memory at `~/.claude/agent-memory/bug-investigator/` to build up institutional knowledge across investigations (table schemas, log patterns, known flaky behaviors, etc.).

---

### `jira-ticket-planner`

**File:** `agents/jira-ticket-planner.md`

**Model:** Opus (more capable for nuanced discovery and decomposition work)

**What it does:** Acts as a Technical Product Analyst and Engineering Lead to help you go from a JIRA ticket to a clear, actionable plan. It fetches ticket details via the Atlassian MCP, asks targeted clarifying questions, explores the codebase for relevant context, and either produces a Discovery Summary (for tasks) or breaks the work into well-scoped child tickets (for epics and stories). **Does not write code or make code changes.**

**Workflows by ticket type:**

- **Epics / Stories** — Fetches the ticket, reviews any linked Figma designs (via the Figma MCP), proposes a breakdown of independently deliverable tasks, and (after your approval) creates them in JIRA as child tickets.
- **Tasks** — Fetches the ticket, explores the codebase to identify relevant files and patterns, and produces a Discovery Summary with a plain-English restatement, files likely to change, an implementation plan, and open questions/risks.

**When to use it:** Any time you're handed a JIRA ticket and want clarity on scope, a decomposition into subtasks, or a codebase-grounded implementation plan before writing any code. Example:

```
Can you help me break down ENG-42?
Let's work on ENG-87
ENG-55 is really vague — can you help me figure out what we're actually building?
```

**Persistent memory:** This agent maintains its own memory at `~/.claude/agent-memory/jira-ticket-planner/` to build up institutional knowledge across planning sessions (frequently touched files, team naming conventions, common decomposition patterns, recurring ambiguities, etc.).

---

## Skills

Skills are reusable prompt templates that Claude loads when invoked via `/skill-name`. They live in `skills/` and appear in Claude's available skill list.

### `bug-investigator`

**File:** `skills/bug-investigator.md`

**Invocation:** `/bug-investigator [bug-ticket-url]`

**What it does:** Thin wrapper that triggers the `bug-investigator` agent (above) with the provided bug ticket URL as input. This is the primary way to kick off a bug investigation — just type the slash command followed by a Jira or Slack link.

**Example:**

```
/bug-investigator https://springcare.atlassian.net/browse/ENG-5678
```

---

## Ralph — Spec-Driven Development Workflow

A structured Requirements → Plan → Build loop for building features with Claude. Skills:

- `/ralph:create-requirements`
- `/ralph:loop`
- `/ralph:plan`
- `/ralph:start-project`
- `/ralph:status`
- `/ralph:step`

See [`skills/ralph/README.md`](skills/ralph/README.md) for full documentation.

\*\*You would put these flat in your `.claude/skills` folder. I've nested them for clearer organization in this repo for easier human readability.

> The Ralph commands are written to be able to work without Beads, but I still prefer to use Beads anyway. Personally, I feel that if it's worth reaching for a Ralph loop, there's no harm or extra work on my part to leverage Beads. But to each their own!

---

## Beads — Issue Tracking for AI Agents

A git-native, dependency-aware issue tracker built for AI agent workflows. Replaces markdown TODOs with tracked, committable issues. Skills:

- `/beads:create`
- `/beads:loop`
- `/beads:ready`
- `/beads:review`
- `/beads:start-project`
- `beads:status`
- `/beads:step`

See [`skills/beads/README.md`](skills/beads/README.md) for full documentation.

\*\*You would put these flat in your `.claude/skills` folder. I've nested them for clearer organization in this repo for easier human readability.

---

## Workflow Patterns

These tools are designed to work together. Here's how they fit depending on whether you're starting from a JIRA ticket or from scratch.

### Tool responsibilities at a glance

| Tool                        | Job                                                                          | Produces                              |
| --------------------------- | ---------------------------------------------------------------------------- | ------------------------------------- |
| `jira-ticket-planner`       | Translate a JIRA ticket into grounded clarity — scope, AC, unknowns resolved | Discovery Summary or JIRA child tasks |
| `ralph:create-requirements` | Formalize what to build into a structured spec                               | `specs/<name>.md`                     |
| `ralph:plan`                | Codebase-verified gap analysis                                               | `IMPLEMENTATION_PLAN.md`              |
| `beads:create`              | Convert plan into tracked, dependency-aware issues                           | Beads issues                          |
| `beads:loop` / `ralph:loop` | Execute autonomously                                                         | Committed code                        |

Each tool does a distinct job. The ticket planner and `create-requirements` are **not** duplicates — the planner translates JIRA context into human clarity; `create-requirements` formalizes that clarity into the machine-readable spec that the rest of the pipeline depends on. The planner makes `create-requirements` faster (the discovery questions are already answered), but doesn't replace it.

---

### Starting from a JIRA ticket (with Beads)

Use this when your work originates from a JIRA epic or story and you want full dependency-aware task tracking.

```
jira-ticket-planner [TICKET-ID]      ← resolve scope, acceptance criteria, unknowns; create JIRA child tasks
        ↓
/beads:start-project <name>          ← branch + spec template + beads epic
        ↓
/ralph:create-requirements <name>    ← formalize the spec using ticket planner output as pre-answered context
        ↓
/ralph:plan                          ← codebase-verified gap analysis → IMPLEMENTATION_PLAN.md
        ↓
/beads:create                        ← convert plan into tracked issues with dependencies
        ↓
/beads:loop <epic-id>                ← autonomous build
  — or —
/beads:step <epic-id>                ← one task at a time with human checkpoints
        ↓
/beads:review                        ← review implementation, file follow-up beads
```

**Note on `ralph:create-requirements`:** Because the ticket planner already surfaced the scope, acceptance criteria, and open questions, this phase moves faster — you're formalizing known answers into `specs/<name>.md` rather than running a full discovery conversation. If the ticket was already extremely detailed and well-scoped, you can sometimes write the spec manually and skip the interactive conversation, going straight to `/ralph:plan`.

---

### Starting from a JIRA ticket (without Beads)

Use this for shorter features that fit in one or two sessions and don't need dependency tracking.

```
jira-ticket-planner [TICKET-ID]      ← resolve scope, acceptance criteria, unknowns; create JIRA child tasks
        ↓
/ralph:start-project <name>          ← branch + spec template
        ↓
/ralph:create-requirements <name>    ← formalize the spec using ticket planner output as pre-answered context
        ↓
/ralph:plan                          ← codebase-verified gap analysis → IMPLEMENTATION_PLAN.md
        ↓
/ralph:loop                          ← autonomous build
  — or —
/ralph:step                          ← one task at a time with human checkpoints
```

---

### Starting fresh (no JIRA ticket)

Use this for work that has no associated JIRA ticket.

**With Beads:**

```
/beads:start-project <name>          ← branch + spec template + beads epic
        ↓
/ralph:create-requirements <name>    ← full discovery conversation → spec
        ↓
/ralph:plan                          ← gap analysis → IMPLEMENTATION_PLAN.md
        ↓
/beads:create                        ← tracked issues
        ↓
/beads:loop or /beads:step
        ↓
/beads:review
```

**Without Beads:**

```
/ralph:start-project <name>
        ↓
/ralph:create-requirements <name>
        ↓
/ralph:plan
        ↓
/ralph:loop or /ralph:step
```

---

### Why these tools aren't duplicates

It's easy to look at `jira-ticket-planner`, `ralph:create-requirements`, and the `start-project` skills and think they all do the same thing. They don't:

- **`jira-ticket-planner`** works in JIRA's context — it fetches ticket history, linked issues, parent epics, and Figma designs, then asks clarifying questions to resolve ambiguities that exist in the _ticket_. Its output is human-readable clarity and, for epics, JIRA child tasks. It has no concept of specs, branches, or the build pipeline.

- **`ralph:create-requirements`** works in the codebase's context — it produces the structured `specs/<name>.md` file that `ralph:plan`, `beads:create`, and the build loop all depend on as their source of truth. Without this file, the rest of the Ralph/Beads pipeline has nothing to work from.

- **`start-project` skills** are pure scaffolding — they create the branch and the empty spec template. They ask no questions and make no decisions.

- **`ralph:plan`** is a codebase read — it does a gap analysis between the spec and what actually exists in the code. The ticket planner's informal "implementation plan" in a Discovery Summary is not a substitute for this; it doesn't verify against the real codebase.

The practical rule: **use the ticket planner when your work starts in JIRA. Skip it when it doesn't.** Never skip `ralph:create-requirements` — the spec file it produces is the foundation everything else builds on.

---

## Commands

Commands are slash commands that load a prompt into Claude's context when invoked. They live in `commands/` and show up as `/command-name` in Claude Code.

### `/diagram`

**File:** `commands/diagram.md`

**Invocation:** `/diagram [description or doc_filepath.md]`

**What it does:** Creates diagrams in two formats simultaneously:

1. A **FigJam diagram** (via the Figma MCP) with a shareable link
2. **Mermaid syntax** in a code block you can paste into docs, GitHub, Notion, etc.

**Usage examples:**

```
/diagram flowchart for the deployment process
/diagram sequence diagram for the payment authorization flow
/diagram convert this ASCII: [paste ASCII art]
/diagram path/to/file-with-ascii-art.md
```

**Why both outputs:** FigJam is great for sharing with non-engineers or for visual polish. Mermaid is great for embedding directly in docs and code. You can even port Mermaid code into Excalidraw, if that's more your cup of tea. The command gives you both so you can pick what fits your context and preference.

> This command needs some polish. As it's currently written, Claude seems to struggle sometimes with larger diagrams or those that need to handle a lot of text.

---

## Tips

- **Hooks require macOS tools.** The notification hooks use `terminal-notifier`. Install it with `brew install terminal-notifier` or remove those hooks if you're not on Mac.
- **Prettier hook is project-aware.** It only formats if `prettier` is available in the project — the `|| true` at the end means it fails silently if not found, so it won't break anything.
- **Agents vs. Skills vs. Commands:** Agents are specialized Claude subprocesses with their own instructions. Skills are prompt templates that can invoke agents. Commands are slash commands that load a prompt directly. For complex multi-step work, use a skill or agent; for quick prompts and utilities, use a command.
- **Extending this setup.** Claude Code docs: https://docs.anthropic.com/en/docs/claude-code
