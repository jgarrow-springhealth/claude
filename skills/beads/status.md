---
name: beads:status
description:
  Show current Ralph + Beads workflow status across specs, plan, beads,
  and git. Use to get oriented at the start of a session or check progress. For
  projects not using Beads, use ralph:status instead.
---

# Ralph + Beads Status Check

Give the user a quick orientation. Use up to 4 parallel subagents to gather information simultaneously:

- Subagent 1: Study all `specs/*.md` files — list with one-line summaries
- Subagent 2: Study `IMPLEMENTATION_PLAN.md` — count completed vs remaining tasks
- Subagent 3: Run `bd ready --json` and `bd list --json` — summarize beads state
- Subagent 4: Run `git status` and `git log --oneline -5` for recent activity

Then synthesize into a concise dashboard:

1. **Specs**: Files and their coverage status
2. **Plan**: Completed vs remaining task count
3. **Beads**: Open / in-progress / blocked / ready counts, broken down by epic
4. **Git**: Current branch, uncommitted changes, recent commits
5. **Discrepancies**: Flag any drift between specs, plan, and beads — resolve them or document them

Don't assume something isn't implemented — if a bead shows open but the code already handles it, flag that for cleanup.

Keep it up-to-date — if you spot stale beads or outdated plan entries during this check, note them explicitly.
