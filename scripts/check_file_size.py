"""Fail CI when a Python file grows past the agreed size limit.

Small files keep each module focused on one responsibility and readable on one
screen (see docs/04-engineering-guidelines.md). The limit counts physical lines,
including docstrings, so the rule is simple to explain and to check.

Usage:
    python scripts/check_file_size.py --max 120 src tests scripts
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

DEFAULT_ROOTS = ("src", "tests", "scripts")


def find_oversized(roots: Sequence[Path], max_lines: int) -> list[tuple[Path, int]]:
    """Return every Python file under ``roots`` that exceeds ``max_lines``.

    Args:
        roots: Directories to search recursively.
        max_lines: Largest allowed number of physical lines per file.

    Returns:
        ``(path, line_count)`` pairs for offending files, sorted by path.
    """
    counted = ((path, _count_lines(path)) for root in roots for path in root.rglob("*.py"))
    return sorted((path, lines) for path, lines in counted if lines > max_lines)


def _count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def main(argv: Sequence[str] | None = None) -> int:
    """Run the check from the command line.

    Args:
        argv: Arguments without the program name; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code: 0 when every file fits, 1 otherwise.
    """
    args = _parse_args(argv)
    offenders = find_oversized([Path(root) for root in args.roots], args.max)
    for path, lines in offenders:
        print(f"{path}: {lines} lines (max {args.max})")
    return 1 if offenders else 0


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max", type=int, default=120, help="maximum lines per file")
    parser.add_argument("roots", nargs="*", default=DEFAULT_ROOTS, help="directories to scan")
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
