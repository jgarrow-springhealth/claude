---
name: review-pr
description: Perform a comprehensive code review using the Courtroom agent. Accepts an optional mode argument to control depth and model.
argument-hint: [branch-or-pr-url] [fast|deep]
---

# Courtroom Code Review

Launch the `courtroom` agent to review the branch or PR in `$ARGUMENTS`.

## Model selection

Parse `$ARGUMENTS` for a mode keyword and select the model accordingly:

- If `$ARGUMENTS` contains `--fast` (like a bash script flag): use `model: haiku`
- If `$ARGUMENTS` contains `--deep` (like a bash script flag): use `model: opus`
- Otherwise: use `model: sonnet`

Strip the mode flag/word from the target before passing it to the agent (e.g. `"https://github.com/org/repo/pull/142 --fast"` → target is the URL, model is haiku).

## Instructions

Launch the courtroom agent with the selected model and pass the branch name or PR URL as the target to review. If no branch or PR is specified, ask the user before proceeding.
