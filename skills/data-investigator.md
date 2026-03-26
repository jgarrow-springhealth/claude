---
name: data-investigator
description: Query Snowflake, Datadog, and Mixpanel for data signals related to a reported bug. Queries via MCP where possible, generates manual queries where not. Use this for a quick data-only investigation without running the full bug-investigator flow.
argument-hint: [bug-ticket-url or bug description with known identifiers]
agent: data-investigator
model: sonnet
---

# Data Investigator Skill

Launches the `data-investigator` agent to query Snowflake, Datadog, and Mixpanel for signals related to a reported bug.

Pass "$ARGUMENTS" — either a Jira ticket URL, a Slack post link, or a plain description of the bug with any known identifiers (user IDs, session IDs, timestamps, affected app, etc.).

The agent will:

- Query Mixpanel and Datadog directly via MCP where accessible
- Generate targeted Snowflake SQL queries (and fallback manual queries for sources it can't reach) scoped to the known identifiers
- Return a structured findings report with all queries labeled so they can be re-run later
