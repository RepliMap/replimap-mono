#!/usr/bin/env python3
"""
Pre-commit hook: Check for stdout hygiene violations in CLI commands.

This script ensures that commands in replimap/cli/commands/ do not
use direct print() or other stdout methods, enforcing the use of
ctx.obj.output.* methods instead.

Prohibited:
- print()
- console.print()
- sys.stdout.write()

Allowed:
- ctx.obj.output.* (all methods)

Usage:
    python scripts/check_stdout_hygiene.py replimap/cli/commands/scan.py
    python scripts/check_stdout_hygiene.py replimap/cli/commands/*.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Patterns that indicate stdout hygiene violations
FORBIDDEN_PATTERNS = [
    # Direct print() calls (but not ctx.obj.output.print or similar)
    (r"(?<![.\w])print\s*\(", "Use ctx.obj.output methods instead of print()"),
    # Rich console.print()
    (r"console\.print\s*\(", "Use ctx.obj.output methods instead of console.print()"),
    # sys.stdout.write()
    (r"sys\.stdout\.write\s*\(", "Use ctx.obj.output methods instead of sys.stdout.write()"),
]

# Files/patterns to skip
SKIP_PATTERNS = [
    r"__pycache__",
    r"\.pyc$",
    r"test_",  # Test files can use print
]


def should_skip_file(filepath: str) -> bool:
    """Check if file should be skipped."""
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, filepath):
            return True
    return False


def check_file(filepath: str) -> list[str]:
    """
    Check a file for stdout hygiene violations.

    Args:
        filepath: Path to the file to check

    Returns:
        List of violation messages
    """
    violations: list[str] = []

    if should_skip_file(filepath):
        return violations

    path = Path(filepath)
    if not path.exists():
        return violations

    try:
        content = path.read_text()
    except (OSError, UnicodeDecodeError):
        return violations

    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        # Skip string definitions (multiline strings, etc.)
        # This is a simple heuristic - may need refinement
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        for pattern, message in FORBIDDEN_PATTERNS:
            if re.search(pattern, line):
                # Check if it's in a comment at end of line
                if "#" in line:
                    before_comment = line.split("#")[0]
                    if not re.search(pattern, before_comment):
                        continue

                violations.append(f"{filepath}:{i}: {message}")
                violations.append(f"  → {stripped}")

    return violations


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: check_stdout_hygiene.py <file1.py> [file2.py ...]")
        return 1

    all_violations: list[str] = []

    for filepath in sys.argv[1:]:
        violations = check_file(filepath)
        all_violations.extend(violations)

    if all_violations:
        print("❌ Stdout Hygiene Violations Found:")
        print()
        for v in all_violations:
            print(v)
        print()
        print("Fix: Use ctx.obj.output.present() for final output")
        print("     Use ctx.obj.output.log() for progress/info messages")
        print("     Use ctx.obj.output.progress() for status updates")
        return 1

    if sys.argv[1:]:  # Only print if files were checked
        print("✅ Stdout hygiene check passed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
