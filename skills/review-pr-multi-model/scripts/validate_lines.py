#!/usr/bin/env python3
"""
Validates and corrects review comment line numbers against a PR diff.

Approach ported from reviewdog's diff package and GitHub service:
- Structured diff parsing with proper old/new line tracking
- Set-based side lookup (no key collisions)
- Three-tier fallback: exact match -> FILE-level (no snapping)

Usage:
  python3 validate_lines.py --diff <diff_file> --comments <comments_json_file> --output <output_json_file>

Input (comments JSON): Array of objects with file_path, line, start_line (nullable), side, body
Output: Same array but with line numbers validated and subjectType set accordingly.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# 1. Structured Diff Parsing (ported from reviewdog hunkParser.Parse())
# ---------------------------------------------------------------------------

@dataclass
class DiffLine:
    """A single parsed line from a unified diff hunk."""
    type: str        # "added", "deleted", or "context"
    lnum_old: int    # old file line number (0 for added lines)
    lnum_new: int    # new file line number (0 for deleted lines)
    content: str = ""  # the line content (without the leading +/-/space prefix)


@dataclass
class FileDiff:
    """All parsed lines for a single file in the diff."""
    lines: list = field(default_factory=list)  # list[DiffLine]


def parse_diff(diff_text):
    """
    Parse a unified diff into structured FileDiff objects.

    Returns:
        dict: {file_path: FileDiff}
    """
    files = {}  # {file_path: FileDiff}
    current_file = None
    old_line = 0
    new_line = 0
    in_hunk = False

    for raw_line in diff_text.splitlines():
        # Detect file path from diff header
        if raw_line.startswith("diff --git"):
            match = re.match(r"diff --git a/(.*) b/(.*)", raw_line)
            if match:
                current_file = match.group(2)
                if current_file not in files:
                    files[current_file] = FileDiff()
                in_hunk = False
            continue

        if raw_line.startswith("+++ b/"):
            current_file = raw_line[6:]
            if current_file not in files:
                files[current_file] = FileDiff()
            continue

        if raw_line.startswith("--- "):
            continue

        # Parse hunk header
        hunk_match = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", raw_line)
        if hunk_match:
            old_line = int(hunk_match.group(1))
            new_line = int(hunk_match.group(3))
            in_hunk = True
            continue

        if current_file is None or not in_hunk:
            continue

        # Ignore "no newline at end of file" markers
        if raw_line.startswith("\\"):
            continue

        # Process diff lines within a hunk
        if raw_line.startswith("+"):
            # Added line: only has a new file line number
            files[current_file].lines.append(DiffLine(
                type="added",
                lnum_old=0,
                lnum_new=new_line,
                content=raw_line[1:],  # strip the leading '+'
            ))
            new_line += 1
        elif raw_line.startswith("-"):
            # Deleted line: only has an old file line number
            files[current_file].lines.append(DiffLine(
                type="deleted",
                lnum_old=old_line,
                lnum_new=0,
                content=raw_line[1:],  # strip the leading '-'
            ))
            old_line += 1
        elif raw_line.startswith(" "):
            # Context line: has both old and new line numbers
            files[current_file].lines.append(DiffLine(
                type="context",
                lnum_old=old_line,
                lnum_new=new_line,
                content=raw_line[1:],  # strip the leading ' '
            ))
            old_line += 1
            new_line += 1
        # NOTE: bare empty strings are NOT treated as context lines.
        # This was a bug in the old script (line == "" matched as context).

    return files


# ---------------------------------------------------------------------------
# 2. Valid Lines Lookup (ported from reviewdog DiffFilter)
# ---------------------------------------------------------------------------

def build_valid_lines(files):
    """
    Build a lookup of valid commentable lines from parsed diff data.

    Returns:
        dict: {file_path: {line_number: set_of_sides}}

    - Lines with lnum_new > 0 are indexed on RIGHT (context + added)
    - Lines with lnum_old > 0 are indexed on LEFT (context + deleted)
    - Context lines appear on BOTH sides (different line numbers)
    """
    valid = {}  # {file_path: {line_num: set(sides)}}

    for file_path, file_diff in files.items():
        line_map = {}  # {line_num: set(sides)}

        for dl in file_diff.lines:
            # RIGHT side uses new file line numbers
            if dl.lnum_new > 0:
                line_map.setdefault(dl.lnum_new, set()).add("RIGHT")

            # LEFT side uses old file line numbers
            if dl.lnum_old > 0:
                line_map.setdefault(dl.lnum_old, set()).add("LEFT")

        valid[file_path] = line_map

    return valid


# ---------------------------------------------------------------------------
# 3. Three-Tier Fallback + Comment Validation
#    (ported from reviewdog GitHub service)
# ---------------------------------------------------------------------------

def make_file_comment(file_path, body, side, reason):
    """Create a FILE-level comment (no line targeting)."""
    return {
        "file_path": file_path,
        "line": None,
        "start_line": None,
        "side": side,
        "body": body,
        "subjectType": "FILE",
        "corrected": True,
        "correction_reason": reason,
    }


def determine_side(sides_set):
    """
    Pick the side for an inline comment.

    Following reviewdog: always prefer RIGHT. Only use LEFT if the line
    is exclusively on the LEFT side (deleted-only line).
    """
    if "RIGHT" in sides_set:
        return "RIGHT"
    return "LEFT"


def validate_comments(valid_lines, files, comments):
    """
    Validate each comment using three-tier fallback:

    1. Exact line match in diff -> inline comment
    2. File in diff but line not -> FILE-level comment (NO snapping)
    3. File not in diff -> FILE-level comment with note
    """
    result = []

    for comment in comments:
        file_path = comment.get("file_path", "")
        line = comment.get("line")
        start_line = comment.get("start_line")
        side = comment.get("side", "RIGHT")
        body = comment.get("body", "")

        file_line_map = valid_lines.get(file_path, {})
        file_in_diff = file_path in files

        # --- Tier 3: File not in diff at all ---
        if not file_in_diff:
            reason = f"File '{file_path}' not found in diff"
            print(f"  [FILE-level] {file_path}: {reason}", file=sys.stderr)
            result.append(make_file_comment(file_path, body, side, reason))
            continue

        # --- Tier 2/1: File is in diff, check line ---
        if line is None or line not in file_line_map:
            # Tier 2: line not in diff -> FILE-level, NO snapping
            if line is None:
                reason = "No line number provided"
            else:
                reason = f"Line {line} not in diff; downgraded to FILE-level comment (no snapping)"
            print(f"  [FILE-level] {file_path}: {reason}", file=sys.stderr)
            result.append(make_file_comment(file_path, body, side, reason))
            continue

        # --- Tier 1: Exact match ---
        validated_side = determine_side(file_line_map[line])
        validated_start_line = None
        validated_start_side = None
        corrected = False
        correction_reason = None

        # Multi-line comment validation
        if start_line is not None:
            if start_line >= line:
                # start_line must be less than line; drop it
                corrected = True
                correction_reason = (
                    f"start_line {start_line} >= line {line}; "
                    f"dropped to single-line comment"
                )
                print(
                    f"  [dropped start_line] {file_path}: {correction_reason}",
                    file=sys.stderr,
                )
            elif start_line not in file_line_map:
                # start_line not in diff; drop it
                corrected = True
                correction_reason = (
                    f"start_line {start_line} not in diff; "
                    f"dropped to single-line comment on line {line}"
                )
                print(
                    f"  [dropped start_line] {file_path}: {correction_reason}",
                    file=sys.stderr,
                )
            else:
                # Both lines valid
                validated_start_line = start_line
                validated_start_side = determine_side(file_line_map[start_line])

        entry = {
            "file_path": file_path,
            "line": line,
            "start_line": validated_start_line,
            "side": validated_side,
            "body": body,
            "subjectType": "LINE",
            "corrected": corrected,
            "correction_reason": correction_reason,
        }
        if validated_start_side is not None:
            entry["start_side"] = validated_start_side

        result.append(entry)

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate PR review comment line numbers against a diff"
    )
    parser.add_argument("--diff", required=True, help="Path to the diff file")
    parser.add_argument("--comments", help="Path to comments JSON file")
    parser.add_argument("--output", help="Path to write validated comments JSON")
    parser.add_argument(
        "--valid-lines-only", action="store_true",
        help="Only output the valid lines map (no comment validation). "
             "Prints a per-file list of valid line numbers for use in reviewer prompts."
    )
    args = parser.parse_args()

    if not args.valid_lines_only and (not args.comments or not args.output):
        parser.error("--comments and --output are required unless --valid-lines-only is set")

    with open(args.diff, "r") as f:
        diff_text = f.read()

    # Parse diff into structured data
    files = parse_diff(diff_text)

    # Build valid-lines lookup with set-based sides
    valid_lines = build_valid_lines(files)

    # --- Valid-lines-only mode: output annotated diff with line numbers ---
    if args.valid_lines_only:
        for fp in sorted(files.keys()):
            file_diff = files[fp]
            # Only show RIGHT-side commentable lines (added + context)
            right_lines = [
                dl for dl in file_diff.lines
                if dl.lnum_new > 0  # added or context
            ]
            if not right_lines:
                print(f"\n{fp}: (no commentable lines)")
                continue
            print(f"\n{fp}:")
            for dl in right_lines:
                prefix = "+" if dl.type == "added" else " "
                print(f"  {dl.lnum_new:>5} {prefix} {dl.content}")
        sys.exit(0)

    # --- Full validation mode ---
    with open(args.comments, "r") as f:
        comments = json.load(f)

    # Print summary of valid lines per file
    print("Valid commentable lines per file:", file=sys.stderr)
    for fp, line_map in valid_lines.items():
        right_lines = sorted(ln for ln, sides in line_map.items() if "RIGHT" in sides)
        left_lines = sorted(ln for ln, sides in line_map.items() if "LEFT" in sides)
        r_range = f"{min(right_lines)}-{max(right_lines)}" if right_lines else "n/a"
        l_range = f"{min(left_lines)}-{max(left_lines)}" if left_lines else "n/a"
        print(
            f"  {fp}: {len(right_lines)} RIGHT [{r_range}], "
            f"{len(left_lines)} LEFT [{l_range}]",
            file=sys.stderr,
        )

    print("\nValidating comments:", file=sys.stderr)
    validated = validate_comments(valid_lines, files, comments)

    # Write output file
    with open(args.output, "w") as f:
        json.dump(validated, f, indent=2)

    # Print correction summary
    corrections = [c for c in validated if c.get("corrected")]
    file_level = [c for c in validated if c.get("subjectType") == "FILE"]
    inline = [c for c in validated if c.get("subjectType") == "LINE"]

    print(f"\nSummary: {len(inline)} inline, {len(file_level)} FILE-level, "
          f"{len(corrections)} corrected", file=sys.stderr)

    if corrections:
        print(f"Corrections:", file=sys.stderr)
        for c in corrections:
            print(f"  {c['file_path']}: {c['correction_reason']}", file=sys.stderr)

    # Also print to stdout for piping
    print(json.dumps(validated, indent=2))


if __name__ == "__main__":
    main()
