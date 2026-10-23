"""Compare two portable release directories for the reproducibility proof."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def _digests(root: Path) -> dict[str, str]:
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")
    return {
        item.name: hashlib.sha256(item.read_bytes()).hexdigest()
        for item in sorted(root.iterdir())
        if item.is_file()
    }


def compare(first: Path, second: Path) -> list[str]:
    left = _digests(first)
    right = _digests(second)
    problems: list[str] = []
    for name in sorted(set(left) | set(right)):
        if name not in left:
            problems.append(f"missing from first: {name}")
        elif name not in right:
            problems.append(f"missing from second: {name}")
        elif left[name] != right[name]:
            problems.append(f"digest differs: {name}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    args = parser.parse_args()
    problems = compare(args.first, args.second)
    if problems:
        for problem in problems:
            print(f"REPRODUCIBILITY FAIL: {problem}")
        raise SystemExit(1)
    print(f"REPRODUCIBILITY PASS: {len(_digests(args.first))} artifacts match")


if __name__ == "__main__":
    main()
