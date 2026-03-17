---
name: bug-investigator
description: Investigate and diagnose bugs in SpringCare applications by coordinating multiple subagents to gather data from various sources including logs, analytics, codebases, and user reports.
argument-hint: [bug-ticket-url]
agent: bug-investigator
model: opus
---

# Bug Investigator Skill

Use the bug-investigator agent to investigate, diagnose, and document bugs reported in SpringCare applications. For "$ARGUMENTS" (bug ticket URL), look for the ticket in Jira or Slack and coordinate multiple subagents to gather data from logs, analytics, codebases, and user reports to identify root causes and recommend fixes.

## Rules:

- Don't assume access. Always verify tool availability before attempting to use it. If a tool (MCP, GitHub, Playwright) fails, document the failure and ask the user for guidance.
- Don't fabricate data. If you cannot retrieve real data, say so and provide the user with what to look for.
- Don't make code changes. Ever. Under any circumstances.
- Ask before proceeding when scope is ambiguous or when a step depends on user-provided information.
