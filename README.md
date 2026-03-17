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
- [Skills](#skills)
  - [bug-investigator](#bug-investigator-1)
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

| Server         | What it does                                                                 |
| -------------- | ---------------------------------------------------------------------------- |
| **GitHub**     | Read/write PRs, issues, branches, files, and code search across GitHub repos |
| **Slack**      | Read channels, search messages, send messages and drafts, read threads       |
| **Atlassian**  | Read/write Jira tickets and Confluence pages                                 |
| **MixPanel**   | Query analytics events, dashboards, and user replay data                     |
| **Datadog**    | Observability platform access (MCP connected; full permissions TBD)          |
| **Figma**      | Read Figma/FigJam designs, generate diagrams, manage Code Connect mappings   |
| **Playwright** | Automate browser interactions for testing and bug reproduction               |

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

## Commands

Commands are slash commands that load a prompt into Claude's context when invoked. They live in `commands/` and show up as `/command-name` in Claude Code.

### `/diagram`

**File:** `commands/diagram.md`

**Invocation:** `/diagram [description or ASCII art]`

**What it does:** Creates diagrams in two formats simultaneously:

1. A **FigJam diagram** (via the Figma MCP) with a shareable link
2. **Mermaid syntax** in a code block you can paste into docs, GitHub, Notion, etc.

**Supported diagram types:** Flowchart, sequence diagram, state diagram, Gantt chart, decision tree.

**Usage examples:**

```
/diagram flowchart for the deployment process
/diagram sequence diagram for the payment authorization flow
/diagram convert this ASCII: [paste ASCII art]
/diagram path/to/file-with-ascii-art.md
```

**Why both outputs:** FigJam is great for sharing with non-engineers or for visual polish. Mermaid is great for embedding directly in docs and code. The command gives you both so you can pick what fits your context.

---

## Tips

- **Hooks require macOS tools.** The notification hooks use `terminal-notifier`. Install it with `brew install terminal-notifier` or remove those hooks if you're not on Mac.
- **Prettier hook is project-aware.** It only formats if `prettier` is available in the project — the `|| true` at the end means it fails silently if not found, so it won't break anything.
- **Agents vs. Skills vs. Commands:** Agents are specialized Claude subprocesses with their own instructions. Skills are prompt templates that can invoke agents. Commands are slash commands that load a prompt directly. For complex multi-step work, use a skill or agent; for quick prompts and utilities, use a command.
- **Extending this setup.** Claude Code docs: https://docs.anthropic.com/en/docs/claude-code
