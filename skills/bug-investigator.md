---
name: bug-investigator
description: Investigate and diagnose bugs in SpringCare applications by coordinating multiple subagents to gather data from various sources including logs, analytics, codebases, and user reports.
argument-hint: [bug-ticket-url]
agent: bug-investigator
model: opus
---

# Bug Investigator Skill

Launches the bug-investigator agent to investigate, diagnose, and document bugs reported in SpringCare applications. Pass "$ARGUMENTS" (a Jira ticket URL or Slack post link) to the agent to begin a full multi-source investigation across logs, analytics, codebases, feature flags, and live reproduction — producing a Confluence RCA draft document as output.
