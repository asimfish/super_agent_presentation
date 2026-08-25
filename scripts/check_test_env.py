#!/usr/bin/env python3
"""Preflight check for filesystem hazards that make the test suite flaky.

The study and render tests spawn many short-lived subprocesses and read
template assets moments after writing them. Cloud-synced folders (macOS
iCloud Drive most prominently) evict file content on disk pressure and
rematerialize it lazily, which surfaces as impossible-looking failures:
reads hang, freshly written files disappear, and fail-closed validations
observe partial state. This script detects the two observable symptoms —
a repository inside a known sync scope, and evicted (dataless) files —
before any test runs.

Standard library only. Exit code 0 means no blocking finding (warnings
may still print); with ``--strict`` any finding fails. It checks local
filesystem state only and proves nothing about test correctness.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# BSD stat flag macOS sets on files whose content is evicted to iCloud.
UF_DATALESS = 0x40000000

# Directory scan bound: the repository tree is a few thousand entries; a
# runaway walk (e.g. accidentally pointed at $HOME) should stop, not hang.
MAX_ENTRIES = 50_000

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules"}


def sync_zone_reason(path: Path, home: Path | None = None) -> str | None:
    """Return why *path* sits in a cloud-sync scope, or None."""
    home = (home or Path.home()).resolve()
    resolved = path.resolve()
    icloud_root = home / "Library" / "Mobile Documents"
    if resolved == icloud_root or icloud_root in resolved.parents:
        return "inside iCloud Drive (~/Library/Mobile Documents)"
    for folder in ("Desktop", "Documents"):
        scoped = home / folder
        if resolved == scoped or scoped in resolved.parents:
            return (
                f"inside ~/{folder}, which macOS syncs (and evicts) when "
                "iCloud Desktop & Documents is enabled"
            )
    for marker in (".dropbox", "Icon\r"):
        if (resolved / marker).exists():
            return f"contains sync-client marker {marker!r}"
    return None


def find_evicted_files(root: Path, limit: int = MAX_ENTRIES) -> tuple[list[Path], bool]:
    """Return (evicted files, scan_truncated) under *root*.

    Detects macOS dataless files via st_flags and name-based ``.icloud``
    placeholders, without opening file content (opening would block while
    the sync client rematerializes it).
    """
    findings: list[Path] = []
    seen = 0
    for current, directories, files in os.walk(root):
        directories[:] = [d for d in directories if d not in SKIP_DIRS]
        for name in files:
            seen += 1
            if seen > limit:
                return findings, True
            path = Path(current) / name
            if name.endswith(".icloud") and name.startswith("."):
                findings.append(path)
                continue
            try:
                status = os.lstat(path)
            except OSError:
                findings.append(path)
                continue
            if getattr(status, "st_flags", 0) & UF_DATALESS:
                findings.append(path)
    return findings, False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_test_env",
        description="Detect cloud-sync hazards before running the test suite.",
    )
    parser.add_argument("--root", default=str(REPO_ROOT), help="Tree to inspect")
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as a failing exit status"
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"check_test_env: not a directory: {root}", file=sys.stderr)
        return 2

    findings = 0
    zone = sync_zone_reason(root)
    if zone is not None:
        findings += 1
        print(f"[warn] repository is {zone}")
        print(
            "       Subprocess-heavy tests are flaky here; keep the working "
            "clone outside sync scopes (for example ~/Code)."
        )

    evicted, truncated = find_evicted_files(root)
    if truncated:
        findings += 1
        print(f"[warn] scan stopped after {MAX_ENTRIES} entries; tree is unexpectedly large")
    if evicted:
        findings += 1
        print(f"[fail] {len(evicted)} file(s) have evicted (dataless) content:")
        for path in evicted[:10]:
            print(f"       {path}")
        if len(evicted) > 10:
            print(f"       ... and {len(evicted) - 10} more")
        print(
            "       Reads of these files block on network rematerialization; "
            "tests will hang or observe partial state."
        )
        return 1

    if findings == 0:
        print("check_test_env: no cloud-sync hazards detected")
    return 1 if (findings and args.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
