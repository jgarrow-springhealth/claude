---
name: ralph:plan
description: Run Ralph planning phase. Performs gap analysis between specs and current code, outputs a prioritized IMPLEMENTATION_PLAN.md. Use after specs are approved.
model: opus
agent: gap-analyzer
---

# Ralph Phase 2: Planning (Gap Analysis)

Perform gap analysis and create a prioritized implementation plan.

## Process:

1. Study ALL files in `specs/` — these are the source of truth
2. Study `AGENTS.md` to understand build/test/lint commands
3. Ultrathink: Thoroughly analyze the current codebase against spec requirements. Don't assume something isn't implemented — study the actual code, tests, and configuration to verify what exists before declaring any gap. This is critical — the #1 failure mode is re-implementing things that already work.
4. Use up to 4 parallel subagents to study different areas of the codebase
   simultaneously:
   - Subagent 1: Study source code for existing implementations
   - Subagent 2: Study tests for existing coverage
   - Subagent 3: Study configs, schemas, and infrastructure
   - Subagent 4: Study specs and cross-reference against findings
5. Synthesize findings and identify genuine gaps: what exists, what's partially done, what's truly missing
6. Create/update `IMPLEMENTATION_PLAN.md` with:
   - Prioritized bullet-point task list
   - Each task scoped to ONE atomic unit of work
   - Dependencies noted where relevant
   - Each task should be completable in a single iteration
   - Capture the why for prioritization decisions

## Rules:

- NO code changes — planning only
- NO commits
- Don't assume not implemented — verify everything against actual code before listing it as a gap. Study imports, study function calls, study test files. If it exists, acknowledge it.
- Tasks should be ordered so each builds on the last
- If specs are ambiguous, list questions at the top of the plan and resolve them or document them — don't proceed with assumptions
- If functionality is missing from the codebase that the specs require, note it clearly — that's what becomes a task
- Keep it up-to-date — if a plan already exists, diff against it rather than regenerating from scratch
- Present the plan to the human for review before finalizing
