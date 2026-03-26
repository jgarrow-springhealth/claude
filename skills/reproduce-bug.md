---
name: reproduce-bug
description: Attempt to reproduce a bug on SpringCare dev environments using Playwright. Handles credential lookup automatically based on user role or email. Use this to run bug reproduction in isolation without a full investigation.
argument-hint: [bug description, repro steps, and optionally a role or email]
agent: playwright-bug-reproducer
model: sonnet
---

# Reproduce Bug Skill

Launches the `playwright-bug-reproducer` agent to attempt to reproduce a bug on SpringCare's deployed dev environments.

Provide "$ARGUMENTS" with as much of the following as you have:

- A description of the bug (what's happening vs. what should happen)
- The steps to reproduce
- The affected app (Compass, Member Portal, and/or Admin Portal)
- Either the **user role** to test as (e.g., "therapist", "care navigator", "member") OR a **specific email address** to log in with

The agent will resolve dev credentials automatically and return a structured reproduction report with screenshots, observed behavior, and whether the bug was reproduced.
