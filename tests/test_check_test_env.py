from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_test_env.py"

sys.path.insert(0, str(ROOT / "scripts"))
import check_test_env  # noqa: E402


def run_check(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )


class SyncZoneReasonTests(unittest.TestCase):
    def test_icloud_drive_scope_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            target = home / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "repo"
            target.mkdir(parents=True)
            reason = check_test_env.sync_zone_reason(target, home=home)
            self.assertIsNotNone(reason)
            self.assertIn("iCloud Drive", reason)

    def test_desktop_and_documents_scopes_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            for folder in ("Desktop", "Documents"):
                target = home / folder / "research" / "repo"
                target.mkdir(parents=True)
                reason = check_test_env.sync_zone_reason(target, home=home)
                self.assertIsNotNone(reason, folder)
                self.assertIn(folder, reason)

    def test_neutral_path_is_not_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            target = home / "Code" / "repo"
            target.mkdir(parents=True)
            self.assertIsNone(check_test_env.sync_zone_reason(target, home=home))


class FindEvictedFilesTests(unittest.TestCase):
    def test_icloud_placeholder_names_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "kept.py").write_text("print('ok')\n", encoding="utf-8")
            (root / ".evicted.py.icloud").write_bytes(b"plist-placeholder")
            findings, truncated = check_test_env.find_evicted_files(root)
            self.assertFalse(truncated)
            self.assertEqual([path.name for path in findings], [".evicted.py.icloud"])

    def test_skip_directories_are_not_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            hidden = root / ".git" / "objects"
            hidden.mkdir(parents=True)
            (hidden / ".pack.icloud").write_bytes(b"x")
            findings, truncated = check_test_env.find_evicted_files(root)
            self.assertFalse(truncated)
            self.assertEqual(findings, [])

    def test_scan_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index in range(12):
                (root / f"file-{index}.txt").write_text("x", encoding="utf-8")
            findings, truncated = check_test_env.find_evicted_files(root, limit=5)
            self.assertTrue(truncated)
            self.assertEqual(findings, [])


class CliTests(unittest.TestCase):
    def test_clean_tree_outside_sync_scope_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_check("--root", temporary)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_evicted_placeholder_fails_even_without_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".asset.png.icloud").write_bytes(b"x")
            result = run_check("--root", str(root))
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("dataless", result.stdout)

    def test_missing_root_is_a_usage_error(self) -> None:
        result = run_check("--root", "/nonexistent/definitely-missing")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
