---
name: review-pr-multi-model
description: >
  Multi-model code review that uses a panel of diverse AI reviewers (Haiku, Sonnet, Opus) to review a PR or branch diff,
  then filters findings through a jury vote and judge synthesis to produce high-signal feedback.
  Use this skill whenever the user wants a thorough, multi-perspective code review of a pull request or branch,
  especially when they mention "review code", "code review", "review this PR", "review my branch",
  "multi-model review", "panel review", or "diverse review". Also use when the user provides a GitHub PR URL
  and asks for review feedback, or mentions wanting different perspectives on their code changes.
argument-hint: <pr-url-or-branch-name>
---

# Multi-Model Code Review

A three-phase code review system that leverages model diversity to catch more issues and filter out noise.
The premise: different models notice different things. By combining their perspectives and filtering through a jury + judge process, you get higher-signal feedback than any single model alone.

## Input Parsing

Parse `$ARGUMENTS` to determine the review target:

- **GitHub PR URL** (e.g., `https://github.com/org/repo/pull/123`): Extract `owner`, `repo`, and `pullNumber`. Use `pull_request_read` with `method: get_diff` to fetch the diff, and `method: get` for PR metadata.
- **Branch name** (e.g., `feature/my-branch`): Run `git diff main...HEAD` (or the appropriate base branch) to get the diff. If the branch is ambiguous, ask the user to clarify.

If no argument is provided, ask the user for a PR URL or branch name before proceeding.

Once you have the diff, also gather context: read the files that were changed so reviewers understand the surrounding code, not just the diff lines.

## Phase 0: Diff Analysis

Before spawning reviewers, parse the diff to extract the valid commentable lines. This gives reviewers an explicit list to pick from instead of computing line numbers from hunk headers (which LLMs are bad at).

**Save the diff to a temp file and run:**

```bash
python3 /Users/janessa.garrow/.claude/skills/review-code/scripts/validate_lines.py \
  --diff $TMPDIR/review-diff.txt \
  --valid-lines-only
```

This outputs an annotated diff showing each commentable line with its line number and code content:

```
src/components/Foo.tsx:
     94 + const handleClick = () => {
     95 +   setOpen(true);
     96 + };
     97
     98   return (

src/utils/bar.ts:
     12 + import { helper } from './helper';
     13   import { utils } from './utils';
     14 +
     15 + export function doThing() {
     16 +   return helper();
     17 + }
```

Lines prefixed with `+` are additions. Lines prefixed with a space are unchanged context lines.
The number on the left is the exact line number reviewers must use when referencing that line.

Save this output as `{valid_lines_map}` — it gets injected into the reviewer prompt below.

## Phase 1: Investigate

Spawn **three subagent reviewers in parallel**, each using a different model. Each reviewer is a senior engineer conducting a thorough, independent code review. They don't know about each other.

### Reviewer Panel

| Reviewer | Model    | Persona                                                                                                 |
| -------- | -------- | ------------------------------------------------------------------------------------------------------- |
| Alpha    | `haiku`  | Fast pattern-matcher. Focuses on obvious bugs, typos, unused imports, naming issues, and style.         |
| Beta     | `sonnet` | Balanced reviewer. Covers correctness, edge cases, error handling, test coverage gaps, and readability. |
| Gamma    | `opus`   | Deep thinker. Focuses on architecture, security, performance, race conditions, and subtle logic errors. |

### Reviewer Prompt Template

Each reviewer gets the same core prompt (with their persona injected):

```
You are a senior software engineer conducting a thorough code review.

Your persona: {persona_description}

Review the following code changes and produce a list of findings. For each finding, provide:

1. **file_path**: The exact file path
2. **line**: The line number where this comment should be placed. You MUST use the line number shown
   in the annotated diff below (the number on the left of each line). Find the code you want to
   comment on in the annotated diff and use the exact number shown next to it. Any line number not
   in the annotated diff will be dropped to a file-level comment.
   DO NOT try to compute line numbers from hunk headers. Just look up the line in the annotated diff.
3. **start_line**: If the comment is about a focused span of code, set `start_line` to the first line
   and `line` to the last line. Both must come from the annotated diff. Good uses: a method body,
   a conditional block, a multi-line expression, a few related assignments.
   Keep ranges tight. Do NOT highlight an entire function or class just because one part has an issue.
   The range should cover only the specific lines your comment is about, not the surrounding context (unless the surrounding context is necessary).
   Set to null for single-line comments (typos, one assignment, one import, etc.).
4. **category**: One of: bug, security, performance, correctness, readability, style, testing, architecture
5. **severity**: One of: critical, warning, nit
6. **comment**: A clear explanation of the issue and WHY it matters
7. **suggestion**: A concrete suggested fix (code snippet or action), or null if the comment is a question

Focus on what matters. Don't pad your review with obvious observations just to seem thorough.
If the code looks good in an area, say nothing about it — silence means approval.

Here is the PR metadata:
{pr_metadata}

Here is the diff:
{diff}

Here is the surrounding file context for changed files:
{file_context}

ANNOTATED DIFF WITH LINE NUMBERS (you MUST use these exact line numbers):
Each line shows: line_number +/space code_content
Use the line number on the left when referencing a line in your findings.
{valid_lines_map}

Return your findings as a JSON array:
[
  {
    "file_path": "src/components/Foo.tsx",
    "line": 108,
    "start_line": 94,
    "category": "correctness",
    "severity": "warning",
    "comment": "This method has an issue across the full block...",
    "suggestion": "..."
  },
  {
    "file_path": "src/components/Foo.tsx",
    "line": 42,
    "start_line": null,
    "category": "bug",
    "severity": "critical",
    "comment": "This single assignment has a typo...",
    "suggestion": "..."
  }
]

If you have no findings, return an empty array [].
```

Collect all findings from all three reviewers into a single list, tagging each with its source reviewer.

## Phase 2: Jury

Take the combined findings from Phase 1 and run them through a **jury vote**. Spawn **three jury
subagents in parallel**, each using a different model (haiku, sonnet, opus). Each juror independently
evaluates every finding.

### Juror Prompt Template

```
You are a senior engineer on a code review jury. Your job is to evaluate the quality and validity
of code review comments that were produced by other reviewers.

For each finding below, provide:
1. **vote**: "upvote" (valid, useful comment), "downvote" (wrong, unhelpful, or nitpicky noise), or "duplicate" (substantially the same point as another finding — specify which one)
2. **reasoning**: Brief explanation of your vote (1-2 sentences)

Consider:
- Is the finding actually correct? Does it identify a real issue?
- Is it actionable? Can the author do something concrete about it?
- Is it proportional? A "critical" tag on a style nit erodes trust.
- Would a human reviewer actually leave this comment, or is it noise?

IMPORTANT: Err on the side of KEEPING findings. Only downvote if the finding is clearly wrong,
unhelpful, or pure noise. Findings about code quality, patterns, architecture, and best practices
are valuable even if they're not bugs. When in doubt, upvote.

ALWAYS downvote these types of findings as noise:
- Import ordering (imports placed after interfaces, between exports, etc.). These are linter territory.
- Formatting-only issues that a linter or auto-formatter would catch.
- Comments about code that is technically correct but doesn't match some style preference.

Here are the findings to evaluate:
{all_findings_as_json}

Return your votes as a JSON array:
[
  {
    "finding_index": 0,
    "vote": "upvote",
    "reasoning": "..."
  }
]
```

### Jury Tally

After all jurors return, tally the votes for each finding:

- **Any upvote** (1/3 or more): include. The bar for inclusion is low because a single reviewer
  seeing value in a finding means it's worth surfacing. The Judge can always soften or merge it.
- **Unanimous downvote** (3/3 downvote): exclude. Only drop a finding if ALL jurors agree it's noise.
- **Flagged as duplicate**: keep the best-worded version, drop the rest.

## Phase 3: Judge

A single subagent (using `opus`) synthesizes the surviving findings into the final review.
The Judge's job is to transform raw reviewer output into comments that match the user's personal
review style.

### Review Style Guide

The final comments should follow this voice and style:

- **Conversational and collaborative.** Frame feedback as questions when possible ("Do we want to...",
  "Can we use...", "What's the difference between...") rather than commands.
- **Use "we" pronouns** to share ownership. Say "we should be safe to remove this" not "you should
  remove this". This shifts blame away from the PR author.
- **Suggestions, not requirements.** Everything is framed as an option or question, never prescriptive.
  Don't say "a better approach would be..." or "Either do X or Y". Instead: "Would it make sense to..."
  or "One option could be..."
- **"Nit:" prefix** for minor issues. Keep nits as short as possible. State the change, not the reasoning.
  Good: "Nit: use the `gap="v-16"` design token"
  Bad: "Nit: `gap="16px"` could use the design token `gap="v-16"` for consistency with the rest of the file."
  The bad example over-explains. The good example just says what to change.
- **Context-rich** when relevant. Reference existing patterns/utils in the codebase when you know about them.
- **Include brief reasoning** for non-obvious issues. But don't lecture or over-explain.
- **Casual, human tone.** No formal or academic language. Avoid words like "meanwhile", "furthermore",
  "subsequently". Use simple, direct language.
- **Never use em dashes (--).** Use periods and start new sentences instead. Em dashes are an AI tell.
- **No severity labels or categorization.** Don't label comments as [Bug], [Medium], [Critical], etc.
  The framing itself conveys importance. Nits get the "Nit:" prefix. Everything else is just a comment.
- **No blame or negative intent language.** Never imply laziness, carelessness, or poor judgment.
  Frame everything constructively.
- **"hmm"/"mm" usage is for replies only.** Don't start a first comment on a new topic with "Hmm" or "Mm".
  Those are conversational interjections used when responding to someone else's comment in a thread.
- **Soften absolute language.** Instead of "This is dead code", say "I don't think this code is used
  anymore. We should be safe to remove it." Instead of "This will break", say "This could cause issues if..."
- **Don't abbreviate words.** Write "backwards compatibility" not "backwards-compat". Write
  "configuration" not "config" (unless the code itself uses the abbreviation).
- **Code suggestions** when a concrete fix is obvious. Use GitHub suggestion blocks:
  ````
  ```suggestion
  const result = computeValue(input);
  ```
  ````

### Judge Prompt Template

```
You are the final judge synthesizing code review findings into polished review comments.

Your job:
1. Take the surviving findings (already filtered by jury vote)
2. Group or merge related findings on the same file/area
3. Rewrite each comment in the review style described below
4. Order comments by file path, then by line number
5. For each comment, preserve the file_path and line number exactly as provided — these will be used
   to post inline comments on the PR. Do NOT invent new line numbers. When merging findings, use the
   line number from the most relevant original finding

CRITICAL STYLE RULES — follow these exactly:

Tone and voice:
- Conversational and collaborative. Frame suggestions as questions ("Do we want to...", "Can we...",
  "Would it make sense to..."). Never prescriptive or bossy.
- Use "we" pronouns, not "you". Say "we should be safe to remove this" not "you should remove this".
- Suggestions are options, not requirements. Never say "a better approach would be" or "Either do X or Y".
- Casual and human. No formal/academic words like "meanwhile", "furthermore", "subsequently".
- Soften absolute language. "I don't think this code is used anymore" not "This is dead code".
  "This could cause issues if..." not "This will break".
- No blame or negative intent. Never imply laziness or carelessness.

Formatting rules:
- NEVER use em dashes (--). Use periods and start new sentences instead.
- "Nit:" prefix for minor issues. Keep nits SHORT. "Nit: use design token, change X to Y" is perfect.
  Don't over-explain obvious changes.
- No severity labels or categories like [Bug], [Medium], [Critical]. The framing conveys importance.
- Don't start comments with "Hmm" or "Mm". Those are for reply threads, not initial comments.
- Use code suggestion blocks when a concrete fix is clear.

Here are the filtered findings with jury vote tallies:
{surviving_findings_with_votes}

Here is the original diff for reference:
{diff}

Return the final review as a JSON array:
[
  {
    "file_path": "src/components/Bar.tsx",
    "line": 108,
    "start_line": 94,
    "side": "RIGHT",
    "body": "Comment about a multi-line code span."
  },
  {
    "file_path": "src/components/Foo.tsx",
    "line": 42,
    "start_line": null,
    "side": "RIGHT",
    "body": "Comment about a single line (typo, single assignment, etc.)."
  }
]

IMPORTANT: Preserve `start_line` and `line` from the original findings. The validation script will
verify they're valid. Use `start_line` for focused spans. Do NOT highlight large chunks.
If a finding has an overly broad range, narrow it to just the lines the comment is actually about.

Also return a short top-level comment for the review. This should NOT be a summary of the PR or the
changes. It should be a brief, casual one-liner like a human reviewer would leave.

IMPORTANT: Vary the top comment. Do NOT always use the same phrase. Pick something that fits the
specific review. Here are examples to draw from (but create your own variations too):
- "Left some comments, but nothing blocking."
- "Looking good! A few things to consider."
- "Thanks for tackling this! Couple of questions."
- "LGTM with a few nits."
- "Nice work! Had a few thoughts."
- "Left some questions inline."
- "Clean PR. One thing caught my eye."
- "Solid approach. A couple of things worth discussing."
- "Thanks for this! Left a few comments."
Return this as a separate "top_comment" field.

{
  "comments": [...],
  "top_comment": "..."
}
```

## Presenting Results

Once the Judge returns its verdict, present the results to the user.

CRITICAL: The output must contain ONLY the final review. Do NOT include:

- Phase 1/2/3 process logs or descriptions of what each reviewer found
- Raw JSON objects or the Judge's JSON response
- Jury vote tallies or tables
- Process summaries or metadata about how the review was conducted
- Any mention of "Alpha", "Beta", "Gamma", "Jury", "Judge", or reviewer personas

The user should see the review as if a human wrote it. No trace of the multi-model process.

### Display Format

Show the top-level comment first, then list each comment grouped by file:

```
{top_comment}

### `src/components/Foo.tsx`

**Line 42:**
{comment body}

**Line 89:**
{comment body}

### `src/utils/bar.ts`

**Line 12:**
{comment body}
```

That's it. Nothing else. The inline comments are the review.

### User Actions

After displaying the review, ask the user what they'd like to do:

1. **View only** (default) — "Looks good, thanks!"
   Put the review findings in a separate file for their reference. They can copy/paste or refer to it as needed.
   Tell the user: "I've saved the review comments to `$TMPDIR/review-comments.txt` for your reference."
2. **Create Pending Review** — Post the comments as a pending GitHub review on the PR.

   DO NOT attempt to validate line numbers yourself. LLMs are bad at counting lines in diffs.
   Use the bundled script to do it deterministically.

   **Step 1: Save the comments to a temp file.**
   - Reuse the diff file from Phase 0 (`$TMPDIR/review-diff.txt`).
   - Save the Judge's comments array as JSON to a temp file (e.g., `$TMPDIR/review-comments.json`).
     The JSON must be an array of objects with `file_path`, `line`, `start_line`, `side`, and `body`.

   **Step 2: Run the validation script.**

   ```bash
   python3 /Users/janessa.garrow/.claude/skills/review-code/scripts/validate_lines.py \
     --diff $TMPDIR/review-diff.txt \
     --comments $TMPDIR/review-comments.json \
     --output $TMPDIR/review-validated.json
   ```

   This script parses the diff deterministically, builds a map of valid commentable lines,
   and validates each comment's line number against the diff. If a line number isn't in the diff,
   the comment is downgraded to a FILE-level comment (no snapping to nearby lines). It prints
   a summary to stderr showing inline vs FILE-level counts and any corrections.

   **Step 3: Read the validated output, report corrections, and post the review.**
   - Read `$TMPDIR/review-validated.json`
   - Before posting, report a summary to the user:
     - How many comments will be posted inline vs FILE-level
     - If any were downgraded to FILE-level, name the affected files so the user is aware
     - Example: "Validated 8 comments: 6 inline, 2 file-level (lines not in diff for `src/utils/helper.ts`)."
   - `pull_request_review_write` with `method: create` (no `event` param) to create the pending review
   - `add_comment_to_pending_review` for each validated comment:
     - `path`: the `file_path`
     - `line`: the validated `line` number
     - `side`: the validated `side`
     - `body`: the comment text
     - `subjectType`: the `subjectType` from the validated output ("LINE" or "FILE")
     - For multi-line comments where `start_line` is set: also pass `startLine` and `startSide`
   - Tell the user: "I've created a pending review with {N} comments. You can view, edit, and submit it on GitHub."

3. **Cancel** — discard everything.

If the input was a branch name (not a PR), the "Create Pending Review" option is unavailable — mention this
and suggest the user open a PR first if they want inline comments.

## Error Handling

- If a reviewer subagent fails or times out, proceed with the findings from the reviewers that did complete.
  Mention which reviewer(s) failed in the output.
- If the diff is empty, tell the user there are no changes to review.
- If the diff is extremely large (>5000 lines), warn the user that the review may take longer and
  consider suggesting they break the PR into smaller chunks.
- If a Pending Review already exists on the PR, inform the user and ask if they want to overwrite it,
  append to it, or cancel.
