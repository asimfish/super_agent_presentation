from __future__ import annotations

import importlib.util
import subprocess
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install.py"


def load_installer_module():
    spec = importlib.util.spec_from_file_location("agentic_reporting_installer", INSTALLER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load installer module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_installer(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INSTALLER), *arguments],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class InstallerTests(unittest.TestCase):
    def project(self, temporary: str) -> Path:
        project = Path(temporary) / "project"
        project.mkdir()
        (project / ".git").mkdir()
        return project

    def test_host_microcontracts_are_bounded_and_include_both_bookends(self) -> None:
        installer = load_installer_module()
        sources = {ROOT / "AGENTS.md"}
        for host in installer.HOSTS.values():
            for scope in host.values():
                sources.add(ROOT / scope["adapter_source"])

        for source in sorted(sources):
            with self.subTest(source=source.relative_to(ROOT)):
                text = source.read_text(encoding="utf-8")
                normalized = " ".join(text.split()).casefold()
                self.assertLessEqual(len(text.split()), 150)
                self.assertIn("likely long", normalized)
                self.assertIn("at the start", normalized)
                self.assertIn("mode", normalized)
                self.assertIn("must-show", normalized)
                self.assertIn("do not retain the bundle", normalized)
                self.assertIn("reporting boundary", normalized)
                self.assertIn("audit", normalized)

    def test_plan_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            result = run_installer("plan", "--target", str(project), "--host", "agents")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Skill copies", result.stdout)
            self.assertFalse((project / ".agents").exists())
            self.assertFalse((project / "AGENTS.md").exists())

    def test_cli_outputs_escape_terminal_controls_and_dynamic_newlines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project\nFAKE-SUCCESS\x1b"
            project.mkdir()
            (project / ".git").mkdir()
            planned = run_installer(
                "plan", "--target", str(project), "--host", "agents"
            )
            self.assertEqual(planned.returncode, 0, planned.stderr)
            self.assertNotIn("\nFAKE-SUCCESS", planned.stdout)
            self.assertNotIn("\x1b", planned.stdout)
            self.assertIn(r"\nFAKE-SUCCESS", planned.stdout)
            self.assertIn(r"\x1b", planned.stdout)

        missing = run_installer(
            "plan", "--target", "missing\nFAKE-SUCCESS\x7f", "--host", "agents"
        )
        self.assertEqual(missing.returncode, 2)
        self.assertNotIn("\nFAKE-SUCCESS", missing.stderr)
        self.assertNotIn("\x7f", missing.stderr)
        self.assertIn(r"\nFAKE-SUCCESS", missing.stderr)
        self.assertIn(r"\x7f", missing.stderr)

        argparse_error = run_installer(
            "plan", "--target", ".", "--host", "bad\nFAKE-SUCCESS"
        )
        self.assertEqual(argparse_error.returncode, 2)
        self.assertNotIn("\nFAKE-SUCCESS", argparse_error.stderr)
        self.assertIn(r"\nFAKE-SUCCESS", argparse_error.stderr)

    def test_apply_installs_self_contained_skill_and_new_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            result = run_installer("apply", "--target", str(project), "--host", "agents")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            skill = project / ".agents" / "skills" / "agentic-reporting"
            self.assertTrue((skill / "SKILL.md").is_file())
            self.assertTrue((skill / "scripts" / "reportctl.py").is_file())
            self.assertIn("agentic-reporting:begin", (project / "AGENTS.md").read_text(encoding="utf-8"))

    def test_existing_instruction_is_preserved_without_append(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            instruction = project / "AGENTS.md"
            instruction.write_text("existing rule\n", encoding="utf-8")
            result = run_installer("apply", "--target", str(project), "--host", "agents")
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertEqual(instruction.read_text(encoding="utf-8"), "existing rule\n")
            self.assertTrue((project / ".agents" / "skills" / "agentic-reporting" / "SKILL.md").is_file())

    def test_pending_merge_can_reuse_identical_skill_for_explicit_append(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            instruction = project / "AGENTS.md"
            instruction.write_text("existing rule\n", encoding="utf-8")
            first = run_installer("apply", "--target", str(project), "--host", "agents")
            self.assertEqual(first.returncode, 3, first.stdout + first.stderr)
            second = run_installer(
                "apply",
                "--target",
                str(project),
                "--host",
                "agents",
                "--append-adapter",
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertIn("Reused identical installed skill", second.stdout)
            self.assertIn("agentic-reporting:begin", instruction.read_text(encoding="utf-8"))
            self.assertEqual(len(list(project.glob("AGENTS.md.bak.*"))), 1)

    def test_explicit_append_backs_up_existing_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            instruction = project / "AGENTS.md"
            instruction.write_text("existing rule\n", encoding="utf-8")
            instruction.chmod(0o644)
            result = run_installer(
                "apply",
                "--target",
                str(project),
                "--host",
                "agents",
                "--append-adapter",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("existing rule", instruction.read_text(encoding="utf-8"))
            self.assertIn("agentic-reporting:begin", instruction.read_text(encoding="utf-8"))
            self.assertEqual(len(list(project.glob("AGENTS.md.bak.*"))), 1)
            self.assertEqual(stat.S_IMODE(instruction.stat().st_mode), 0o644)

    def test_existing_skill_is_never_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            destination = project / ".agents" / "skills" / "agentic-reporting"
            destination.mkdir(parents=True)
            marker = destination / "user-file.txt"
            marker.write_text("keep", encoding="utf-8")
            result = run_installer("apply", "--target", str(project), "--host", "agents")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_user_scope_paths_are_host_specific(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            result = run_installer(
                "plan",
                "--scope",
                "user",
                "--target",
                str(base),
                "--host",
                "codex",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(base / ".agents" / "skills" / "agentic-reporting"), result.stdout)
            self.assertIn(str(base / ".codex" / "AGENTS.md"), result.stdout)

    def test_codex_user_scope_targets_active_nonempty_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            codex_dir = base / ".codex"
            codex_dir.mkdir()
            override = codex_dir / "AGENTS.override.md"
            override.write_text("active override\n", encoding="utf-8")
            first = run_installer(
                "apply",
                "--scope",
                "user",
                "--target",
                str(base),
                "--host",
                "codex",
            )
            self.assertEqual(first.returncode, 3, first.stdout + first.stderr)
            self.assertEqual(override.read_text(encoding="utf-8"), "active override\n")
            self.assertFalse((codex_dir / "AGENTS.md").exists())

            second = run_installer(
                "apply",
                "--scope",
                "user",
                "--target",
                str(base),
                "--host",
                "codex",
                "--append-adapter",
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertIn("agentic-reporting:begin", override.read_text(encoding="utf-8"))
            self.assertEqual(len(list(codex_dir.glob("AGENTS.override.md.bak.*"))), 1)
            self.assertFalse((codex_dir / "AGENTS.md").exists())

    def test_codex_project_scope_targets_active_nonempty_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            override = project / "AGENTS.override.md"
            override.write_text("project override\n", encoding="utf-8")
            result = run_installer(
                "apply",
                "--target",
                str(project),
                "--host",
                "codex",
            )
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn(str(override), result.stdout)
            self.assertEqual(override.read_text(encoding="utf-8"), "project override\n")
            self.assertFalse((project / "AGENTS.md").exists())

    def test_unsupported_user_scope_host_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_installer(
                "plan",
                "--scope",
                "user",
                "--target",
                temporary,
                "--host",
                "copilot",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("does not define", result.stderr)

    def test_user_scope_requires_a_directory_base(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base_file = Path(temporary) / "not-a-directory"
            base_file.write_text("x", encoding="utf-8")
            result = run_installer(
                "plan",
                "--scope",
                "user",
                "--target",
                str(base_file),
                "--host",
                "codex",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("existing directory", result.stderr)

    def test_cursor_user_scope_fails_closed_pending_manual_user_rule(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_installer(
                "plan",
                "--scope",
                "user",
                "--target",
                temporary,
                "--host",
                "cursor",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("does not define", result.stderr)

    def test_symlinked_destination_parent_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            outside = Path(temporary) / "outside"
            outside.mkdir()
            (project / ".agents").symlink_to(outside, target_is_directory=True)
            result = run_installer("apply", "--target", str(project), "--host", "agents")
            self.assertEqual(result.returncode, 2)
            self.assertIn("symlink component", result.stderr)
            self.assertEqual(list(outside.iterdir()), [])

    def test_symlinked_target_ancestor_is_rejected_before_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            visible = base / "visible"
            outside = base / "outside"
            visible.mkdir()
            project = outside / "project"
            project.mkdir(parents=True)
            (project / ".git").mkdir()
            (visible / "redirect").symlink_to(outside, target_is_directory=True)
            result = run_installer(
                "apply",
                "--target",
                str(visible / "redirect" / "project"),
                "--host",
                "agents",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Target path contains a symlink component", result.stderr)
            self.assertFalse((project / ".agents").exists())
            self.assertFalse((project / "AGENTS.md").exists())

    def test_oversized_existing_instruction_requires_manual_handling(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            (project / "AGENTS.md").write_text("x" * (2 * 1024 * 1024 + 1), encoding="utf-8")
            result = run_installer("plan", "--target", str(project), "--host", "agents")
            self.assertEqual(result.returncode, 2)
            self.assertIn("automatic inspection limit", result.stderr)
            self.assertFalse((project / ".agents").exists())

    def test_apply_preflights_oversized_instruction_before_copying_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            (project / "AGENTS.md").write_text("x" * (2 * 1024 * 1024 + 1), encoding="utf-8")
            result = run_installer("apply", "--target", str(project), "--host", "agents")
            self.assertEqual(result.returncode, 2)
            self.assertIn("automatic inspection limit", result.stderr)
            self.assertFalse((project / ".agents").exists())

    def test_incomplete_adapter_marker_fails_before_copying_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            (project / "AGENTS.md").write_text(
                "<!-- agentic-reporting:begin -->\ntruncated\n",
                encoding="utf-8",
            )
            result = run_installer("apply", "--target", str(project), "--host", "agents")
            self.assertEqual(result.returncode, 2)
            self.assertIn("incomplete or duplicate", result.stderr)
            self.assertFalse((project / ".agents").exists())

    def test_bogus_complete_marker_is_not_accepted_as_installed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            instruction = project / "AGENTS.md"
            bogus = (
                "<!-- agentic-reporting:begin -->\n"
                "bogus content that does not activate the Skill\n"
                "<!-- agentic-reporting:end -->\n"
            )
            instruction.write_text(bogus, encoding="utf-8")
            result = run_installer("apply", "--target", str(project), "--host", "agents")
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn("marker content differs", result.stdout)
            self.assertEqual(instruction.read_text(encoding="utf-8"), bogus)
            self.assertTrue((project / ".agents" / "skills" / "agentic-reporting" / "SKILL.md").is_file())

            retry = run_installer(
                "apply",
                "--target",
                str(project),
                "--host",
                "agents",
                "--append-adapter",
            )
            self.assertEqual(retry.returncode, 2)
            self.assertIn("differs from the selected adapter", retry.stderr)
            self.assertEqual(instruction.read_text(encoding="utf-8"), bogus)

    def test_apply_preflights_regular_file_parent_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            (project / ".agents").write_text("not a directory", encoding="utf-8")
            result = run_installer("apply", "--target", str(project), "--host", "agents")
            self.assertEqual(result.returncode, 2)
            self.assertIn("Destination parent is not a directory", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse((project / "AGENTS.md").exists())

    def test_partial_copytree_failure_is_rolled_back(self) -> None:
        installer = load_installer_module()
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            destination = project / ".agents" / "skills" / "agentic-reporting"

            def fail_after_partial_copy(source, target, **kwargs):
                del source, kwargs
                Path(target).mkdir(parents=True)
                (Path(target) / "partial.txt").write_text("partial", encoding="utf-8")
                raise OSError("injected copy failure")

            with mock.patch.object(installer.shutil, "copytree", side_effect=fail_after_partial_copy):
                with self.assertRaises(installer.InstallError):
                    installer.apply_install(project, ["agents"], "project", False)
            self.assertFalse(destination.exists())
            self.assertFalse((project / ".agents").exists())
            self.assertFalse((project / "AGENTS.md").exists())

    def test_conflicting_adapters_for_same_target_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            result = run_installer(
                "apply",
                "--target",
                str(project),
                "--host",
                "agents",
                "--host",
                "codex",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("different adapters", result.stderr)
            self.assertFalse((project / ".agents").exists())
            self.assertFalse((project / "AGENTS.md").exists())

    def test_plan_exposes_conflicting_adapters_before_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            result = run_installer(
                "plan",
                "--target",
                str(project),
                "--host",
                "agents",
                "--host",
                "codex",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("different adapters", result.stderr)
            self.assertFalse((project / ".agents").exists())


if __name__ == "__main__":
    unittest.main()
