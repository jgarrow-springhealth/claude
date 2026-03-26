---
name: codebase-investigator
description: Investigate a bug in the SpringCare codebase by searching relevant GitHub repos and checking LaunchDarkly flag state. Identifies the responsible code path, looks up live flag state for any flags found in the code, checks for recent regressions, and derives human-readable reproduction steps. Use this for a focused code + flag investigation without running the full bug-investigator flow.
argument-hint: [bug-ticket-url or bug description with affected app]
agent: codebase-investigator
model: opus
---

# Codebase Investigator Skill

Launches the `codebase-investigator` agent to search the SpringCare GitHub repos for the code responsible for a reported bug.

Pass "$ARGUMENTS" — either a Jira ticket URL, a Slack post link, or a plain description of the bug including the affected app.

The agent will:

- Identify the relevant repos and search them in parallel (one subagent per repo)
- Find the code path responsible for the reported behavior, with file paths and line numbers
- Surface any LaunchDarkly feature flag references in the affected code paths
- Check recent commits and PRs for regressions around the time the bug was first reported
- Derive numbered, human-readable reproduction steps from the code flow
- Return a structured report ready to feed into a LaunchDarkly investigation or Playwright reproduction
