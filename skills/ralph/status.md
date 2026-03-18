---
name: ralph:status
description: Show current Ralph workflow status (no Beads) across specs, plan, and git. Use to get oriented at the start of a session or check progress. For projects using Beads, use beads:status instead.
---

# Ralph Status Check (No Beads)

Give the user a quick orientation. Use up to 3 parallel subagents to gather information simultaneously:

- Subagent 1: Study all `specs/*.md` files — list with one-line summaries
- Subagent 2: Study `IMPLEMENTATION_PLAN.md` — count `[ ]` not started, `[~]` in-progress, `[x]` complete, `[!]` blocked. Summarize tasks' state
- Subagent 3: Run `git status` and `git log --oneline -5` for recent activity

Then synthesize into a concise dashboard:

1. **Specs**: Files and their coverage status
2. **Plan**: Task counts by status — not started / in-progress / complete / blocked
3. **Git**: Current branch, uncommitted changes, recent commits
4. **Discrepancies**: Flag any drift between specs and plan — tasks in the plan with no corresponding spec coverage, or spec requirements with no plan entry -- resolve them or document them

Don't assume something isn't implemented — if the plan shows a task open but the code already handles it, flag that for cleanup.

Keep it up-to-date — if you spot stale plan entries or completed work not yet marked `[x]` during this check, note them explicitly.
