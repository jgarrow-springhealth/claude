---
name: beads:ready
description: Show all beads issues ready to work on (no unmet dependencies).
  Use to pick the next thing to build or get an overview of available work.
allowed-tools: Bash, Read
---

# Beads: Ready Issues

1. Run `bd ready --json` to get all issues with no uncompleted dependencies
2. For each ready issue, show:
   - ID, title, priority, and parent epic
   - Brief description and acceptance criteria
   - What it blocks (i.e., completing this unblocks what?)
3. Ultrathink about recommendation — suggest which to tackle first based on:
   - Priority level
   - Whether it unblocks other high-value issues
   - Whether specs have been updated since the bead was created
4. Don't assume not implemented — if a ready task looks like it might
   already be done, study the code quickly and flag it:
   "⚠ <bead-id> may already be implemented — study <file> before starting"
5. If there are blocked issues that look incorrectly blocked, flag those too —
   resolve them or document them

Keep it up to date — if you notice beads that are stale (open but the
work is done), recommend closing them.
