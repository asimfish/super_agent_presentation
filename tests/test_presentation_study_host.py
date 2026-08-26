from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
STUDY_SCRIPT = ROOT / "scripts" / "presentation_study.py"
HOSTS_SCRIPT = ROOT / "scripts" / "presentation_hosts.py"
CASES = ROOT / "evals" / "presentation-cases.json"
MODEL_ID = "fake-codex"
CASE_ID = "experiment-null-result"
CONTEXT_ID = "fresh"
SEED = 7


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(STUDY_SCRIPT), *arguments],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def load_hosts_module() -> ModuleType:
    module_name = "_presentation_hosts_contract_test"
    spec = importlib.util.spec_from_file_location(module_name, HOSTS_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {HOSTS_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_study_module() -> ModuleType:
    module_name = "_presentation_study_host_boundary_test"
    spec = importlib.util.spec_from_file_location(module_name, STUDY_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {STUDY_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def response_text(*, image_path: str | None = None) -> str:
    image = f"![Locally generated diagnostic plot]({image_path})\n\n" if image_path else ""
    return (
        image
        + "| Method | Accuracy (%) ↑ | Latency (ms) ↓ |\n"
        "|---|---:|---:|\n"
        "| A | 72.4 ± 1.1 | 31 |\n"
        "| B | 74.0 ± 1.0 | 38 |\n"
        "| C | 73.9 ± 0.9 | 29 |\n\n"
        "Accuracy is higher-is-better and latency is lower-is-better. Accuracy is the "
        "mean ± standard deviation over five seeds. No statistical significance test "
        "was run, so B and C cannot be declared statistically different. C has the "
        "lowest observed latency while its mean accuracy is close to B; the evidence "
        "does not establish a universal winner.\n"
    )


def checkpoint_response_text() -> str:
    return (
        "Objective: compare three methods under a fixed protocol using accuracy and "
        "latency metrics.\n\n"
        "Results table.\n\n"
        "| Method | Accuracy (%) ↑ | Latency (ms) ↓ |\n"
        "|---|---:|---:|\n"
        "| A | 72.4 ± 1.1 | 31 |\n"
        "| B | 74.0 ± 1.0 | 38 |\n"
        "| C | 73.9 ± 0.9 | 29 |\n\n"
        "Accuracy is higher-is-better and latency is lower-is-better. Accuracy is the "
        "mean ± standard deviation over five seeds. No statistical significance test "
        "was run, so B and C cannot be declared statistically different. C has the "
        "lowest observed latency while its mean accuracy is close to B; the evidence "
        "boundary does not establish a universal winner.\n"
    )


def checkpoint_image_response_text() -> str:
    return (
        "Main result: the supplied mean-return curve rises through step 80 and drops "
        "at step 90; this is a visible observation, not a diagnosis of cause.\n\n"
        "Research question and method: we inspect the supplied training curve to "
        "describe the late-training trend. The metric is mean return at each training "
        "step. The shaded band is one standard deviation over five seeds.\n\n"
        "![Line chart showing mean return rising through step 80 and dropping at step "
        "90, with a shaded uncertainty band](evals/fixtures/assets/return-curve.svg)\n\n"
        "*Figure 1. Mean return over training; the shaded band denotes one standard "
        "deviation over five seeds.*\n\n"
        "Conclusion and boundary: the observed return drops at step 90 after rising "
        "through step 80. The plot alone cannot identify the cause of the drop.\n"
    )


def study_plan(
    *,
    study_id: str,
    host: str = "manual",
    executable_sha256: str | None = None,
    case_id: str = CASE_ID,
) -> dict[str, object]:
    if host == "manual":
        model = {
            "id": "manual-model",
            "host": "manual",
            "host_version": "manual",
            "model": "synthetic-model",
            "revision": "synthetic-v1",
            "revision_receipt": None,
            "executable_sha256": None,
        }
    else:
        model = {
            "id": MODEL_ID,
            "host": host,
            "host_version": "fake-cli-v1",
            "model": "fake-model",
            "revision": "fake-model-v1",
            "revision_receipt": None,
            "executable_sha256": executable_sha256,
        }
    return {
        "$schema": "../schema/study-plan.schema.json",
        "schema_version": "1.0",
        "study_id": study_id,
        "study_kind": "pilot",
        "claim_boundary": "This local pilot validates mechanics only, not effectiveness.",
        "framework": {
            "repository": "https://github.com/asimfish/super_agent_presentation",
            "commit_sha": "b4c014d4b87c0d4556908b492dcf35cccb8631d4",
            "skill_manifest_sha256": (
                "5677fb6729572f6a77b4fadda5b08a3a68a5f3dafbff99bdd0284f1c011fe53f"
            ),
            "adapter_sha256": (
                "d9ab6468253d2ea60b04b3ca8cf8d823e90bdf24effb200e74e69d5c77225a7f"
            ),
        },
        "execution": {
            "baseline_isolation": "same-account-workspace",
            "isolation_receipt": None,
            "global_instruction_policy": "unverified",
            "replicate_semantics": "independent-repeat",
        },
        "benchmark": {
            "benchmark_id": "agentic-reporting-presentation-v1",
            "cases_sha256": sha256(CASES),
            "case_ids": [case_id],
            "heldout": False,
            "preregistration_receipt": None,
        },
        "models": [model],
        "conditions": ["baseline", "framework"],
        "seeds": [SEED],
        "contexts": [
            {
                "id": CONTEXT_ID,
                "target_occupancy_percent": 10,
                "compaction_required": False,
            }
        ],
        "generation": {
            "max_output_tokens": 1200,
            "timeout_seconds": 30,
            "locale": "en-US",
            "renderer": "CommonMark",
        },
        "rating": {"required_raters": 2},
        "analysis": {
            "bootstrap_seed": 1729,
            "bootstrap_resamples": 10000,
            "primary_context_ids": [CONTEXT_ID],
            "primary_dimensions": [
                "information_architecture",
                "readability_and_scannability",
                "completeness_and_actionability",
                "evidence_calibration",
            ],
            "thresholds": {
                "machine_pass_rate_min": 0.98,
                "human_dimension_min": 4.0,
                "priority_dimension_min": 4.2,
                "primary_gain_min": 0.30,
                "primary_ci_lower_min": 0.0,
                "task_fidelity_margin": 0.20,
                "win_rate_min": 0.65,
                "loss_rate_max": 0.15,
                "semantic_slot_rate_min": 0.95,
                "semantic_density_difference_min": 0.0,
                "visual_precision_min": 0.90,
                "visual_recall_min": 0.90,
                "token_overhead_median_max": 0.15,
                "token_overhead_p90_max": 0.30,
                "long_soak_pass_rate_min": 0.90,
                "long_soak_fresh_gap_max": 0.05,
                "agreement_within_one_min": 0.85,
            },
        },
    }


class PresentationStudyHostTests(unittest.TestCase):
    def test_checkpoint_receipt_portable_path_schema_matches_runtime_boundaries(self) -> None:
        schema = json.loads(
            (
                ROOT
                / "evals"
                / "schema"
                / "checkpoint-artifact-receipt.schema.json"
            ).read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(schema["$defs"]["portablePath"])
        for accepted in (
            ".agentic-reporting/checkpoint.json",
            "checkpoint-artifacts/events/000001-create-checkpoint.json",
            "a" * 255,
        ):
            with self.subTest(accepted=accepted):
                self.assertEqual(list(validator.iter_errors(accepted)), [])
        for rejected in (
            "../outside.json",
            "a/../outside.json",
            "./checkpoint.json",
            "/absolute/checkpoint.json",
            "a" * 256,
            "a\\checkpoint.json",
        ):
            with self.subTest(rejected=rejected):
                self.assertNotEqual(list(validator.iter_errors(rejected)), [])

    @unittest.skipUnless(os.name == "posix", "checkpoint capture requires POSIX")
    def test_workspace_checkpoint_capture_rejects_links_fifos_permissions_and_escape(self) -> None:
        module = load_study_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            workspace = root / "workspace"
            workspace.mkdir()

            safe = workspace / "safe.json"
            safe.write_bytes(b"{}\n")
            safe.chmod(0o600)
            relative, data, evidence = module._read_workspace_artifact(
                workspace,
                "safe.json",
                maximum=32,
                label="test checkpoint",
            )
            self.assertEqual(relative.as_posix(), "safe.json")
            self.assertEqual(data, b"{}\n")
            self.assertEqual(evidence["bytes"], 3)

            private_parent = workspace / "private-parent"
            private_parent.mkdir(mode=0o700)
            private_parent.chmod(0o700)
            nested = private_parent / "checkpoint.json"
            nested.write_bytes(b"{}\n")
            nested.chmod(0o600)
            module._read_workspace_artifact(
                workspace,
                "private-parent/checkpoint.json",
                maximum=32,
                label="nested checkpoint",
            )
            private_parent.chmod(0o777)
            with self.assertRaisesRegex(module.StudyError, "mode 0700"):
                module._read_workspace_artifact(
                    workspace,
                    "private-parent/checkpoint.json",
                    maximum=32,
                    label="nested checkpoint",
                )
            private_parent.chmod(0o700)

            workspace.chmod(0o777)
            with self.assertRaisesRegex(module.StudyError, "write permissions"):
                module._read_workspace_artifact(
                    workspace,
                    "safe.json",
                    maximum=32,
                    label="test checkpoint",
                )
            workspace.chmod(0o755)

            permissive = workspace / "permissive.json"
            permissive.write_bytes(b"{}")
            permissive.chmod(0o644)
            with self.assertRaisesRegex(module.StudyError, "group or other"):
                module._read_workspace_artifact(
                    workspace,
                    "permissive.json",
                    maximum=32,
                    label="test checkpoint",
                )

            hardlinked = workspace / "hardlinked.json"
            hardlinked.write_bytes(b"{}")
            hardlinked.chmod(0o600)
            os.link(hardlinked, workspace / "hardlink-alias.json")
            with self.assertRaisesRegex(module.StudyError, "exactly one hard link"):
                module._read_workspace_artifact(
                    workspace,
                    "hardlinked.json",
                    maximum=32,
                    label="test checkpoint",
                )

            symlink = workspace / "symlink.json"
            symlink.symlink_to(safe)
            with self.assertRaises(module.StudyError):
                module._read_workspace_artifact(
                    workspace,
                    "symlink.json",
                    maximum=32,
                    label="test checkpoint",
                )

            fifo = workspace / "checkpoint.fifo"
            os.mkfifo(fifo, mode=0o600)
            with self.assertRaisesRegex(module.StudyError, "regular file"):
                module._read_workspace_artifact(
                    workspace,
                    "checkpoint.fifo",
                    maximum=32,
                    label="test checkpoint",
                )

            outside = root / "outside"
            outside.mkdir()
            (outside / "checkpoint.json").write_bytes(b"{}")
            (outside / "checkpoint.json").chmod(0o600)
            (workspace / "aliased-parent").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(module.StudyError):
                module._read_workspace_artifact(
                    workspace,
                    "aliased-parent/checkpoint.json",
                    maximum=32,
                    label="test checkpoint",
                )

            for escaped in (
                "../outside/checkpoint.json",
                str(outside / "checkpoint.json"),
                "./safe.json",
            ):
                with self.subTest(escaped=escaped):
                    with self.assertRaises(module.StudyError):
                        module._read_workspace_artifact(
                            workspace,
                            escaped,
                            maximum=32,
                            label="test checkpoint",
                        )

    def test_skill_tree_receipt_preserves_canonical_manifest_semantics(self) -> None:
        module = load_study_module()
        with tempfile.TemporaryDirectory() as temporary:
            skill_root = Path(temporary).resolve() / "agentic-reporting"
            assets = skill_root / "assets"
            cache = skill_root / "__pycache__"
            assets.mkdir(parents=True)
            cache.mkdir()
            skill_file = skill_root / "SKILL.md"
            asset_file = assets / "example.txt"
            skill_file.write_text("contract\n", encoding="utf-8")
            asset_file.write_text("example\n", encoding="utf-8")
            (skill_root / ".DS_Store").write_bytes(b"ignored")
            (skill_root / "ignored.pyc").write_bytes(b"ignored")
            (cache / "nested.pyc").write_bytes(b"ignored")

            records = [
                {
                    "path": "SKILL.md",
                    "kind": "file",
                    "bytes": skill_file.stat().st_size,
                    "sha256": sha256(skill_file),
                },
                {"path": "assets", "kind": "directory"},
                {
                    "path": "assets/example.txt",
                    "kind": "file",
                    "bytes": asset_file.stat().st_size,
                    "sha256": sha256(asset_file),
                },
            ]
            canonical = json.dumps(
                records,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )

            self.assertEqual(
                module._skill_tree_receipt(skill_root),
                {
                    "path": ".agents/skills/agentic-reporting",
                    "entry_count": 3,
                    "total_bytes": skill_file.stat().st_size + asset_file.stat().st_size,
                    "manifest_sha256": hashlib.sha256(
                        canonical.encode("utf-8")
                    ).hexdigest(),
                },
            )

    def test_skill_tree_receipt_stops_scanning_at_entry_limit(self) -> None:
        module = load_study_module()
        self.assertEqual(module.MAX_SKILL_TREE_ENTRIES, 4096)
        with tempfile.TemporaryDirectory() as temporary:
            skill_root = Path(temporary).resolve() / "agentic-reporting"
            skill_root.mkdir()
            for index in range(6):
                (skill_root / f"ignored-{index}.pyc").touch()

            yielded = 0
            real_scandir = os.scandir

            @contextmanager
            def tracked_scandir(path: object):
                nonlocal yielded
                with real_scandir(path) as entries:
                    def tracked_entries():
                        nonlocal yielded
                        for entry in entries:
                            yielded += 1
                            yield entry

                    yield tracked_entries()

            with patch.object(module, "MAX_SKILL_TREE_ENTRIES", 3), patch.object(
                module.os,
                "scandir",
                side_effect=tracked_scandir,
            ):
                with self.assertRaisesRegex(module.StudyError, "exceeds 3 entries"):
                    module._skill_tree_receipt(skill_root)

            self.assertEqual(yielded, 4)

    def test_skill_tree_receipt_prunes_pycache_subtrees(self) -> None:
        module = load_study_module()
        with tempfile.TemporaryDirectory() as temporary:
            skill_root = Path(temporary).resolve() / "agentic-reporting"
            cache = skill_root / "__pycache__"
            cache.mkdir(parents=True)
            (skill_root / "SKILL.md").write_text("contract\n", encoding="utf-8")
            for index in range(6):
                (cache / f"nested-{index}.pyc").touch()

            with patch.object(module, "MAX_SKILL_TREE_ENTRIES", 2):
                receipt = module._skill_tree_receipt(skill_root)

            self.assertEqual(receipt["entry_count"], 1)

    def test_skill_tree_receipt_rejects_ignored_symlinks_and_nonregulars(self) -> None:
        module = load_study_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for kind in ("symlink", "fifo"):
                with self.subTest(kind=kind):
                    skill_root = root / kind
                    skill_root.mkdir()
                    ignored = skill_root / "ignored.pyc"
                    if kind == "symlink":
                        target = skill_root / "target.txt"
                        target.write_text("target\n", encoding="utf-8")
                        ignored.symlink_to(target)
                        expected = "may not contain symlinks"
                    else:
                        os.mkfifo(ignored)
                        expected = "unsupported entry"
                    with self.assertRaisesRegex(module.StudyError, expected):
                        module._skill_tree_receipt(skill_root)

    def test_skill_tree_receipt_rejects_oversize_file_before_hashing(self) -> None:
        module = load_study_module()
        with tempfile.TemporaryDirectory() as temporary:
            skill_root = Path(temporary).resolve() / "agentic-reporting"
            skill_root.mkdir()
            (skill_root / "large.txt").write_bytes(b"1234")
            with patch.object(module, "MAX_SKILL_TREE_BYTES", 3), patch.object(
                module,
                "_sha256",
            ) as digest:
                with self.assertRaisesRegex(module.StudyError, "exceeds 3 bytes"):
                    module._skill_tree_receipt(skill_root)
            digest.assert_not_called()

    def test_host_timeout_starts_even_when_child_never_reads_large_stdin(self) -> None:
        module = load_study_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "never-read-stdin.py"
            executable.write_text(
                "#!/usr/bin/env python3\nimport time\ntime.sleep(10)\n",
                encoding="utf-8",
            )
            executable.chmod(0o700)
            started = time.monotonic()
            with self.assertRaises(module.StudyError) as raised:
                module._run_bounded_host(
                    argv=(str(executable),),
                    prompt=b"x" * (2 * 1024 * 1024),
                    transcript_path=root / "transcript.jsonl",
                    stderr_path=root / "stderr.log",
                    response_path=root / "response.md",
                    timeout_seconds=1,
                )
            self.assertIn("exceeded 1 seconds", str(raised.exception))
            self.assertLess(time.monotonic() - started, 4.0)

    def make_root(self, temporary: str) -> Path:
        # macOS exposes /tmp through a symlink.  The host contract intentionally
        # requires canonical exact paths, so fixtures use the resolved root.
        return Path(temporary).resolve()

    def initialize(self, root: Path, plan: dict[str, object]) -> Path:
        plan_path = root / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        run_dir = root / "run"
        result = run_cli(
            "init",
            "--plan",
            str(plan_path),
            "--cases-file",
            str(CASES),
            "--output",
            str(run_dir),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return run_dir

    def make_workspace(self, root: Path, name: str, *, framework: bool) -> Path:
        workspace = root / name
        workspace.mkdir()
        (workspace / ".git").mkdir()
        if framework:
            installed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "install.py"),
                    "--target",
                    str(workspace),
                    "--scope",
                    "project",
                    "--host",
                    "codex",
                    "apply",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        return workspace

    def make_fake_codex(self, root: Path) -> Path:
        executable = root / "fake-codex"
        executable.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import json
                import pathlib
                import sys

                arguments = sys.argv[1:]
                workspace = pathlib.Path(arguments[arguments.index("-C") + 1])
                response = pathlib.Path(
                    arguments[arguments.index("--output-last-message") + 1]
                )
                sys.stdin.buffer.read()
                (workspace / ".fake-host-invoked").write_text("executed\\n", encoding="utf-8")
                response.write_text({response_text()!r}, encoding="utf-8")
                print(json.dumps({{
                    "type": "turn.completed",
                    "usage": {{
                        "input_tokens": 321,
                        "cached_input_tokens": 21,
                        "output_tokens": 123
                    }}
                }}))
                """
            ),
            encoding="utf-8",
        )
        executable.chmod(0o700)
        return executable

    def make_checkpoint_fake_codex(
        self,
        root: Path,
        *,
        mutate_before_audit_event: bool = False,
        alternate_paths: bool = False,
        permissive_capture_directory: bool = False,
        report_body: str | None = None,
        must_show: str = "No statistical significance test was run",
        deliver_post_audit_mutation: bool = False,
        symlink_mirror_path_after_audit: str | None = None,
    ) -> Path:
        body = report_body if report_body is not None else checkpoint_response_text()
        evidence_relative = (
            "alternate-evidence" if alternate_paths else ".agentic-reporting"
        )
        checkpoint_relative = f"{evidence_relative}/checkpoint.json"
        draft_relative = f"{evidence_relative}/draft.md"
        executable = root / "fake-codex-checkpoint"
        executable.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import json
                import os
                import pathlib
                import subprocess
                import sys

                arguments = sys.argv[1:]
                workspace = pathlib.Path(arguments[arguments.index("-C") + 1])
                response = pathlib.Path(
                    arguments[arguments.index("--output-last-message") + 1]
                )
                received_prompt = sys.stdin.buffer.read()
                (workspace / ".fake-checkpoint-host-prompt").write_bytes(received_prompt)
                evidence = workspace / {evidence_relative!r}
                evidence.mkdir(mode=0o700, exist_ok=True)
                checkpoint = evidence / "checkpoint.json"
                draft = evidence / "draft.md"
                reportctl = (
                    workspace
                    / ".agents"
                    / "skills"
                    / "agentic-reporting"
                    / "scripts"
                    / "reportctl.py"
                )
                if not reportctl.is_file():
                    response.write_text({body!r}, encoding="utf-8")
                    print(json.dumps({{
                        "type": "turn.completed",
                        "usage": {{
                            "input_tokens": 321,
                            "cached_input_tokens": 21,
                            "output_tokens": 123,
                        }},
                    }}), flush=True)
                    raise SystemExit(0)

                def run_reportctl(*reportctl_arguments):
                    completed = subprocess.run(
                        [sys.executable, str(reportctl), *reportctl_arguments],
                        cwd=workspace,
                        text=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        check=False,
                    )
                    if completed.returncode != 0:
                        sys.stderr.write(completed.stderr)
                        raise SystemExit(completed.returncode)

                def emit(command):
                    print(json.dumps({{
                        "type": "item.completed",
                        "item": {{
                            "type": "command_execution",
                            "command": command,
                            "exit_code": 0,
                        }},
                    }}), flush=True)

                emit("sed -n '1,120p' .agents/skills/agentic-reporting/SKILL.md")
                checkpoint_command = (
                    "python3 .agents/skills/agentic-reporting/scripts/reportctl.py "
                    "checkpoint --task 'Compare the experiment results' "
                    "--mode experiment-report --surface chat "
                    "--must-show {must_show!r} "
                    "--output {checkpoint_relative}"
                )
                run_reportctl(
                    "checkpoint",
                    "--task", "Compare the experiment results",
                    "--mode", "experiment-report",
                    "--surface", "chat",
                    "--must-show", {must_show!r},
                    "--output", {checkpoint_relative!r},
                )
                os.chmod(checkpoint, 0o600)
                emit(checkpoint_command)

                bundle_command = (
                    "python3 .agents/skills/agentic-reporting/scripts/reportctl.py "
                    "bundle --checkpoint {checkpoint_relative}"
                )
                run_reportctl(
                    "bundle", "--checkpoint", {checkpoint_relative!r}
                )
                emit(bundle_command)

                draft.write_text({body!r}, encoding="utf-8")
                os.chmod(draft, 0o600)
                audit_command = (
                    "python3 .agents/skills/agentic-reporting/scripts/reportctl.py "
                    "audit --file {draft_relative} "
                    "--checkpoint {checkpoint_relative} --strict --json"
                )
                run_reportctl(
                    "audit",
                    "--file", {draft_relative!r},
                    "--checkpoint", {checkpoint_relative!r},
                    "--strict",
                    "--json",
                )
                if {mutate_before_audit_event!r}:
                    draft.write_text("mutated after audit\\n", encoding="utf-8")
                    os.chmod(draft, 0o600)
                if {deliver_post_audit_mutation!r}:
                    draft.write_text("mutated after audit\\n", encoding="utf-8")
                    os.chmod(draft, 0o600)
                if {symlink_mirror_path_after_audit!r} is not None:
                    mirror = evidence / {symlink_mirror_path_after_audit!r}
                    mirror.unlink()
                    mirror.symlink_to(workspace / {symlink_mirror_path_after_audit!r})
                if {permissive_capture_directory!r}:
                    os.chmod(evidence, 0o777)
                emit(audit_command)

                response.write_text(
                    "mutated after audit\\n"
                    if {deliver_post_audit_mutation!r}
                    else {body!r},
                    encoding="utf-8",
                )
                print(json.dumps({{
                    "type": "turn.completed",
                    "usage": {{
                        "input_tokens": 321,
                        "cached_input_tokens": 21,
                        "output_tokens": 123,
                    }},
                }}), flush=True)
                """
            ),
            encoding="utf-8",
        )
        executable.chmod(0o700)
        return executable

    def host_unit_id(self, condition: str, *, case_id: str = CASE_ID) -> str:
        return f"{case_id}--{MODEL_ID}--{CONTEXT_ID}--s{SEED}--{condition}"

    def manual_unit_id(self, condition: str) -> str:
        return f"{CASE_ID}--manual-model--{CONTEXT_ID}--s{SEED}--{condition}"

    def import_manual(
        self,
        root: Path,
        run_dir: Path,
        *,
        study_id: str,
        condition: str,
        artifacts: list[dict[str, str]] | None = None,
        artifact_root: Path | None = None,
        image_path: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        response = root / f"{condition}-response.md"
        response.write_text(response_text(image_path=image_path), encoding="utf-8")
        prompt = run_dir / "prompts" / f"{CASE_ID}--manual-model--{CONTEXT_ID}--s{SEED}.txt"
        record = {
            "$schema": "generation-record.schema.json",
            "schema_version": "1.0",
            "study_id": study_id,
            "unit_id": self.manual_unit_id(condition),
            "case_id": CASE_ID,
            "model_id": "manual-model",
            "context_id": CONTEXT_ID,
            "seed": SEED,
            "condition": condition,
            "host": "manual",
            "host_version": "manual",
            "model": "synthetic-model",
            "model_revision": "synthetic-v1",
            "prompt_sha256": sha256(prompt),
            "response_sha256": sha256(response),
            "transcript_sha256": None,
            "artifacts": artifacts or [],
            "usage": {
                "input_tokens": 1000,
                "cached_input_tokens": 0,
                "output_tokens": 200 if condition == "baseline" else 215,
                "latency_ms": 1000,
                "context_occupancy_percent": 10,
                "compaction_observed": False,
            },
            "observations": {
                "telemetry_source": "manual",
                "host_activation_observed": condition == "framework",
                "skill_read": condition == "framework",
                "checkpoint_created": None,
                "checkpoint_reloaded": None,
                "checkpoint_audit_passed": None,
                "final_audit_passed": None,
                "checkpoint_receipt_verified": None,
                "output_token_cap_enforced": None,
            },
        }
        record_path = root / f"{condition}-record.json"
        record_path.write_text(json.dumps(record), encoding="utf-8")
        arguments = [
            "import-output",
            "--run-dir",
            str(run_dir),
            "--record",
            str(record_path),
            "--response",
            str(response),
        ]
        if artifact_root is not None:
            arguments.extend(("--artifact-root", str(artifact_root)))
        return run_cli(*arguments)

    def complete_manual(self, root: Path, run_dir: Path, *, study_id: str) -> None:
        for condition in ("baseline", "framework"):
            result = self.import_manual(
                root,
                run_dir,
                study_id=study_id,
                condition=condition,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_codex_adapter_builds_fixed_shell_free_argv_and_parses_jsonl_telemetry(self) -> None:
        hosts = load_hosts_module()
        adapter = hosts.CodexAdapter()
        executable = Path("/opt/tools/codex")
        workspace = Path("/private/work/unit")
        response = Path("/private/run/response.md")

        command = adapter.build_command(
            executable=executable,
            workspace=workspace,
            response_path=response,
            model="gpt-test-fixed",
            max_output_tokens=900,
        )

        self.assertEqual(
            command.argv,
            (
                str(executable),
                "exec",
                "-C",
                str(workspace),
                "--sandbox",
                "workspace-write",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--json",
                "--color",
                "never",
                "--model",
                "gpt-test-fixed",
                "--output-last-message",
                str(response),
                "-",
            ),
        )
        self.assertFalse(command.output_token_cap_enforced)
        self.assertEqual(command.transcript_format, "codex-jsonl-v1")
        self.assertNotIn("sh", command.argv)
        self.assertNotIn("bash", command.argv)
        self.assertNotIn("-c", command.argv)

        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": "sed -n '1,120p' .agents/skills/agentic-reporting/SKILL.md",
                    "exit_code": 0,
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": "python3 .agents/skills/agentic-reporting/scripts/reportctl.py checkpoint --output /tmp/report.json",
                    "exit_code": 0,
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": "python3 .agents/skills/agentic-reporting/scripts/reportctl.py bundle --checkpoint /tmp/report.json",
                    "exit_code": 0,
                },
            },
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": "python3 .agents/skills/agentic-reporting/scripts/reportctl.py audit --file /tmp/draft.md --checkpoint /tmp/report.json --strict",
                    "exit_code": 0,
                },
            },
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 700,
                    "cached_input_tokens": 125,
                    "output_tokens": 80,
                },
            },
        ]
        telemetry = adapter.parse_transcript(json.dumps(event) for event in events)
        self.assertEqual(telemetry.input_tokens, 700)
        self.assertEqual(telemetry.cached_input_tokens, 125)
        self.assertEqual(telemetry.output_tokens, 80)
        self.assertTrue(telemetry.skill_read)
        self.assertTrue(telemetry.checkpoint_created)
        self.assertTrue(telemetry.checkpoint_reloaded)
        self.assertTrue(telemetry.checkpoint_audit_passed)
        self.assertTrue(telemetry.final_audit_passed)
        self.assertFalse(telemetry.checkpoint_receipt_verified)
        self.assertEqual(
            telemetry.checkpoint_events,
            (
                hosts.HostCheckpointEvent("create", 2, "/tmp/report.json"),
                hosts.HostCheckpointEvent("reload", 3, "/tmp/report.json"),
                hosts.HostCheckpointEvent(
                    "audit", 4, "/tmp/report.json", "/tmp/draft.md"
                ),
            ),
        )
        self.assertEqual(telemetry.event_count, 5)

    def test_codex_checkpoint_contract_requires_create_reload_audit_order(self) -> None:
        hosts = load_hosts_module()
        adapter = hosts.CodexAdapter()
        commands = (
            (
                "python3 .agents/skills/agentic-reporting/scripts/reportctl.py "
                "audit --file .agentic-reporting/draft.md "
                "--checkpoint .agentic-reporting/checkpoint.json --strict"
            ),
            (
                "python3 .agents/skills/agentic-reporting/scripts/reportctl.py "
                "bundle --checkpoint .agentic-reporting/checkpoint.json"
            ),
            (
                "python3 .agents/skills/agentic-reporting/scripts/reportctl.py "
                "checkpoint --output .agentic-reporting/checkpoint.json"
            ),
        )
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": command,
                    "exit_code": 0,
                },
            }
            for command in commands
        ]
        events.append({"type": "turn.completed", "usage": {}})

        telemetry = adapter.parse_transcript(json.dumps(event) for event in events)

        self.assertEqual(
            telemetry.checkpoint_events,
            (),
        )
        self.assertTrue(telemetry.checkpoint_created)
        self.assertFalse(telemetry.checkpoint_reloaded)
        self.assertFalse(telemetry.checkpoint_audit_passed)
        self.assertFalse(telemetry.final_audit_passed)
        self.assertFalse(telemetry.checkpoint_receipt_verified)

    def test_codex_transcript_does_not_credit_echoes_failed_or_mismatched_commands(self) -> None:
        hosts = load_hosts_module()
        adapter = hosts.CodexAdapter()
        commands = (
            "printf 'cat .agents/skills/agentic-reporting/SKILL.md'",
            "echo 'python3 .agents/skills/agentic-reporting/scripts/reportctl.py checkpoint --output /tmp/report.json'",
            "echo 'python3 .agents/skills/agentic-reporting/scripts/reportctl.py bundle --checkpoint /tmp/report.json'",
            "echo 'python3 .agents/skills/agentic-reporting/scripts/reportctl.py audit --file /tmp/draft.md --checkpoint /tmp/report.json --strict'",
            "python3 .agents/skills/agentic-reporting/scripts/reportctl.py checkpoint --output /tmp/failed.json",
            "python3 .agents/skills/agentic-reporting/scripts/reportctl.py bundle --checkpoint /tmp/other.json",
            "python3 .agents/skills/agentic-reporting/scripts/reportctl.py audit --file /tmp/draft.md --checkpoint /tmp/third.json --strict",
            "cat --help .agents/skills/agentic-reporting/SKILL.md",
            "python3 .agents/skills/agentic-reporting/scripts/reportctl.py checkpoint --output /tmp/help.json --help",
            "python3 .agents/skills/agentic-reporting/scripts/reportctl.py bundle --checkpoint /tmp/help.json --help",
            "python3 .agents/skills/agentic-reporting/scripts/reportctl.py audit --file /tmp/draft.md --checkpoint /tmp/help.json --strict --help",
            "./cat .agents/skills/agentic-reporting/SKILL.md",
            "./python3 /tmp/.agents/skills/agentic-reporting/scripts/reportctl.py checkpoint --output /tmp/path-spoof.json",
            "./python3 /tmp/.agents/skills/agentic-reporting/scripts/reportctl.py bundle --checkpoint /tmp/path-spoof.json",
            "./python3 /tmp/.agents/skills/agentic-reporting/scripts/reportctl.py audit --file /tmp/draft.md --checkpoint /tmp/path-spoof.json --strict",
            "python3 /private/work/.agents/skills/agentic-reporting/scripts/reportctl.py checkpoint --output /tmp/absolute.json",
            "python3 /private/work/.agents/skills/agentic-reporting/scripts/reportctl.py bundle --checkpoint /tmp/absolute.json",
            "python3 /private/work/.agents/skills/agentic-reporting/scripts/reportctl.py audit --file /tmp/draft.md --checkpoint /tmp/absolute.json --strict",
        )
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": command,
                    "exit_code": 2 if "failed.json" in command else 0,
                },
            }
            for command in commands
        ]
        events.append({"type": "turn.completed", "usage": {}})
        telemetry = adapter.parse_transcript(json.dumps(event) for event in events)
        self.assertFalse(telemetry.skill_read)
        self.assertFalse(telemetry.checkpoint_created)
        self.assertFalse(telemetry.checkpoint_reloaded)
        self.assertFalse(telemetry.checkpoint_audit_passed)
        self.assertFalse(telemetry.final_audit_passed)
        self.assertFalse(telemetry.checkpoint_receipt_verified)
        self.assertEqual(telemetry.checkpoint_events, ())

    def test_codex_transcript_credits_strict_mode_only_final_audit_without_checkpoint(self) -> None:
        hosts = load_hosts_module()
        adapter = hosts.CodexAdapter()
        events = [
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": (
                        "python3 .agents/skills/agentic-reporting/scripts/reportctl.py "
                        "audit --file /tmp/draft.md --mode concise-answer --strict"
                    ),
                    "exit_code": 0,
                },
            },
            {"type": "turn.completed", "usage": {}},
        ]
        telemetry = adapter.parse_transcript(json.dumps(event) for event in events)
        self.assertTrue(telemetry.final_audit_passed)
        self.assertFalse(telemetry.checkpoint_created)
        self.assertFalse(telemetry.checkpoint_reloaded)
        self.assertFalse(telemetry.checkpoint_audit_passed)
        self.assertFalse(telemetry.checkpoint_receipt_verified)
        self.assertEqual(telemetry.checkpoint_events, ())

    def test_codex_transcript_rejects_unbounded_json_numbers_and_depth(self) -> None:
        hosts = load_hosts_module()
        adapter = hosts.CodexAdapter()
        probes = (
            '{"type":"turn.completed","usage":{"input_tokens":' + "9" * 129 + "}}",
            '{"a":' * 101 + "0" + "}" * 101,
        )
        for probe in probes:
            with self.subTest(prefix=probe[:32]):
                with self.assertRaises(hosts.HostAdapterError):
                    adapter.parse_transcript([probe])

    def test_host_plan_is_pure_and_enforces_clean_vs_installed_workspace_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            executable = self.make_fake_codex(root)
            run_dir = self.initialize(
                root,
                study_plan(
                    study_id="host-plan-pilot",
                    host="codex",
                    executable_sha256=sha256(executable),
                ),
            )
            clean = self.make_workspace(root, "clean-workspace", framework=False)
            installed = self.make_workspace(root, "installed-workspace", framework=True)

            wrong_baseline = run_cli(
                "host-plan",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                self.host_unit_id("baseline"),
                "--executable",
                str(executable),
                "--workspace",
                str(installed),
            )
            self.assertEqual(wrong_baseline.returncode, 2, wrong_baseline.stdout + wrong_baseline.stderr)
            self.assertIn("Baseline workspace", wrong_baseline.stderr)

            wrong_framework = run_cli(
                "host-plan",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                self.host_unit_id("framework"),
                "--executable",
                str(executable),
                "--workspace",
                str(clean),
            )
            self.assertEqual(wrong_framework.returncode, 2, wrong_framework.stdout + wrong_framework.stderr)
            self.assertIn("Framework workspace", wrong_framework.stderr)

            for condition, workspace in (("baseline", clean), ("framework", installed)):
                result = run_cli(
                    "host-plan",
                    "--run-dir",
                    str(run_dir),
                    "--unit-id",
                    self.host_unit_id(condition),
                    "--executable",
                    str(executable),
                    "--workspace",
                    str(workspace),
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            self.assertFalse((clean / ".fake-host-invoked").exists())
            self.assertFalse((installed / ".fake-host-invoked").exists())
            baseline_plan = json.loads(
                (
                    run_dir
                    / "private"
                    / "host-plans"
                    / f"{self.host_unit_id('baseline')}.json"
                ).read_text(encoding="utf-8")
            )
            framework_plan = json.loads(
                (
                    run_dir
                    / "private"
                    / "host-plans"
                    / f"{self.host_unit_id('framework')}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(baseline_plan["executable_sha256"], sha256(executable))
            self.assertEqual(
                baseline_plan["host_adapter_source_sha256"],
                sha256(HOSTS_SCRIPT),
            )
            self.assertEqual(baseline_plan["planned_argv"][0], str(executable))
            self.assertEqual(baseline_plan["planned_argv"][1], "exec")
            self.assertEqual(
                baseline_plan["planned_transcript_format"],
                "codex-jsonl-v1",
            )
            self.assertEqual(baseline_plan["workspace_receipt"]["activation"]["state"], "clean")
            self.assertIsNone(baseline_plan["workspace_receipt"]["activation"]["skill"])
            activation = framework_plan["workspace_receipt"]["activation"]
            self.assertEqual(activation["state"], "installed")
            self.assertEqual(activation["active_instruction"]["path"], "AGENTS.md")
            self.assertRegex(activation["skill"]["manifest_sha256"], r"^[0-9a-f]{64}$")
            self.assertFalse(framework_plan["command_profile"]["shell"])
            self.assertTrue(framework_plan["command_profile"]["explicit_execution_required"])
            self.assertFalse(
                framework_plan["command_profile"]["output_token_cap_enforced"]
            )
            self.assertEqual(
                baseline_plan["host_prompt_sha256"], baseline_plan["prompt_sha256"]
            )
            self.assertNotEqual(
                framework_plan["host_prompt_sha256"],
                framework_plan["prompt_sha256"],
            )
            capture_profile = framework_plan["checkpoint_capture_profile"]
            self.assertEqual(capture_profile["workspace_directory"], ".agentic-reporting")
            self.assertEqual(capture_profile["directory_mode"], "0700")
            self.assertEqual(capture_profile["file_mode"], "0600")
            self.assertIn("Study-only", capture_profile["agent_contract"])
            auditor_receipt = framework_plan["checkpoint_auditor_receipt"]
            self.assertEqual(auditor_receipt["profile"], "reportctl-audit-closure-v1")
            self.assertEqual(
                [item["path"] for item in auditor_receipt["files"]],
                [
                    "scripts/reportctl.py",
                    "scripts/markdown_image_scanner.py",
                    "references/protocols.json",
                ],
            )

            legacy_unit = self.host_unit_id("baseline")
            legacy_plan_path = (
                run_dir / "private" / "host-plans" / f"{legacy_unit}.json"
            )
            legacy_plan = json.loads(legacy_plan_path.read_text(encoding="utf-8"))
            legacy_plan["schema_version"] = "1.0"
            for field in (
                "checkpoint_auditor_sha256",
                "checkpoint_auditor_receipt",
                "checkpoint_capture_profile",
                "host_prompt_sha256",
            ):
                legacy_plan.pop(field)
            legacy_plan_path.write_text(json.dumps(legacy_plan), encoding="utf-8")
            legacy_lock_path = (
                run_dir / "private" / "host-plans" / f"{legacy_unit}.lock.json"
            )
            legacy_lock = json.loads(legacy_lock_path.read_text(encoding="utf-8"))
            legacy_lock["host_plan_sha256"] = sha256(legacy_plan_path)
            legacy_lock_path.write_text(json.dumps(legacy_lock), encoding="utf-8")
            loaded_legacy = load_study_module()._load_host_plan(run_dir, legacy_unit)
            self.assertEqual(loaded_legacy["schema_version"], "1.0")

    def test_host_run_rejects_adapter_source_or_argv_drift_after_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            executable = self.make_fake_codex(root)
            run_dir = self.initialize(
                root,
                study_plan(
                    study_id="adapter-drift-pilot",
                    host="codex",
                    executable_sha256=sha256(executable),
                ),
            )
            workspace = self.make_workspace(root, "clean-workspace", framework=False)
            unit_id = self.host_unit_id("baseline")
            planned = run_cli(
                "host-plan",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--executable",
                str(executable),
                "--workspace",
                str(workspace),
            )
            self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
            module = load_study_module()
            with patch.object(
                module,
                "_host_adapter_source_sha256",
                return_value="f" * 64,
            ):
                with self.assertRaisesRegex(module.StudyError, "adapter source changed"):
                    module.command_host_run(
                        argparse.Namespace(
                            execute=True,
                            run_dir=str(run_dir),
                            unit_id=unit_id,
                        )
                    )
            self.assertFalse((workspace / ".fake-host-invoked").exists())
            self.assertFalse(
                (run_dir / "private" / "host-executions" / unit_id).exists()
            )

            with patch.object(
                module,
                "_checkpoint_auditor_sha256",
                return_value="e" * 64,
            ):
                with self.assertRaisesRegex(module.StudyError, "auditor changed"):
                    module.command_host_run(
                        argparse.Namespace(
                            execute=True,
                            run_dir=str(run_dir),
                            unit_id=unit_id,
                        )
                    )
            self.assertFalse((workspace / ".fake-host-invoked").exists())

            host_plan_path = (
                run_dir / "private" / "host-plans" / f"{unit_id}.json"
            )
            host_plan = json.loads(host_plan_path.read_text(encoding="utf-8"))
            host_plan["planned_argv"][-1] = "unexpected-prompt-source"
            host_plan_path.write_text(json.dumps(host_plan), encoding="utf-8")
            lock_path = (
                run_dir / "private" / "host-plans" / f"{unit_id}.lock.json"
            )
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            lock["host_plan_sha256"] = sha256(host_plan_path)
            lock_path.write_text(json.dumps(lock), encoding="utf-8")
            with self.assertRaisesRegex(module.StudyError, "adapter argv changed"):
                module.command_host_run(
                    argparse.Namespace(
                        execute=True,
                        run_dir=str(run_dir),
                        unit_id=unit_id,
                    )
                )
            self.assertFalse((workspace / ".fake-host-invoked").exists())

    def test_host_run_without_execute_is_inert(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            executable = self.make_fake_codex(root)
            run_dir = self.initialize(
                root,
                study_plan(
                    study_id="inert-host-run",
                    host="codex",
                    executable_sha256=sha256(executable),
                ),
            )
            workspace = self.make_workspace(root, "clean-workspace", framework=False)
            planned = run_cli(
                "host-plan",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                self.host_unit_id("baseline"),
                "--executable",
                str(executable),
                "--workspace",
                str(workspace),
            )
            self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)

            result = run_cli(
                "host-run",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                self.host_unit_id("baseline"),
            )

            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("inert without the explicit --execute flag", result.stderr)
            self.assertFalse((workspace / ".fake-host-invoked").exists())
            self.assertFalse((run_dir / "private" / "host-executions").exists())
            self.assertFalse((run_dir / "records" / self.host_unit_id("baseline")).exists())

    def test_fake_host_execute_writes_jsonl_response_and_auto_imports_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            executable = self.make_fake_codex(root)
            run_dir = self.initialize(
                root,
                study_plan(
                    study_id="fake-execution-pilot",
                    host="codex",
                    executable_sha256=sha256(executable),
                ),
            )
            workspace = self.make_workspace(root, "clean-workspace", framework=False)
            unit_id = self.host_unit_id("baseline")
            planned = run_cli(
                "host-plan",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--executable",
                str(executable),
                "--workspace",
                str(workspace),
            )
            self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)

            result = run_cli(
                "host-run",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--execute",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((workspace / ".fake-host-invoked").is_file())
            execution_root = run_dir / "private" / "host-executions" / unit_id
            transcript = execution_root / "transcript.jsonl"
            response = execution_root / "response.md"
            self.assertTrue(transcript.is_file())
            self.assertEqual(
                json.loads(transcript.read_text(encoding="utf-8"))["type"],
                "turn.completed",
            )
            self.assertEqual(response.read_text(encoding="utf-8"), response_text())
            receipt = json.loads(
                (execution_root / "execution-receipt.json").read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "completed")
            self.assertFalse(receipt["shell"])
            self.assertEqual(receipt["argv"][0], str(executable))
            stored_root = run_dir / "records" / unit_id
            stored = json.loads((stored_root / "record.json").read_text(encoding="utf-8"))
            self.assertEqual(stored["usage"]["input_tokens"], 321)
            self.assertEqual(stored["usage"]["cached_input_tokens"], 21)
            self.assertEqual(stored["usage"]["output_tokens"], 123)
            self.assertTrue(stored["machine_evaluation"]["passed"])
            self.assertEqual(sha256(stored_root / "response.md"), stored["response_sha256"])
            self.assertEqual(sha256(stored_root / "transcript.jsonl"), stored["transcript_sha256"])
            binding_path = stored_root / "host-execution-binding.json"
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            self.assertEqual(binding["unit_id"], unit_id)
            self.assertEqual(binding["stored_record_sha256"], sha256(stored_root / "record.json"))
            validated = run_cli("validate", "--run-dir", str(run_dir), "--json")
            self.assertEqual(validated.returncode, 1, validated.stdout + validated.stderr)
            validation = json.loads(validated.stdout)
            self.assertEqual(validation["invalid_record_count"], 0)

            stored["usage"]["output_tokens"] = 124
            (stored_root / "record.json").write_text(json.dumps(stored), encoding="utf-8")
            tampered = run_cli("validate", "--run-dir", str(run_dir), "--json")
            self.assertEqual(tampered.returncode, 1, tampered.stdout + tampered.stderr)
            self.assertEqual(json.loads(tampered.stdout)["invalid_record_count"], 1)

    def test_framework_host_run_persists_controller_verified_checkpoint_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            executable = self.make_checkpoint_fake_codex(root)
            run_dir = self.initialize(
                root,
                study_plan(
                    study_id="checkpoint-receipt-pilot",
                    host="codex",
                    executable_sha256=sha256(executable),
                ),
            )
            workspace = self.make_workspace(root, "framework-workspace", framework=True)
            unit_id = self.host_unit_id("framework")
            planned = run_cli(
                "host-plan",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--executable",
                str(executable),
                "--workspace",
                str(workspace),
            )
            self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
            host_plan = json.loads(
                (
                    run_dir / "private" / "host-plans" / f"{unit_id}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(host_plan["schema_version"], "1.1")
            self.assertIsInstance(host_plan["checkpoint_capture_profile"], dict)
            self.assertEqual(
                host_plan["checkpoint_capture_profile"]["checkpoint_path"],
                ".agentic-reporting/checkpoint.json",
            )
            self.assertEqual(
                host_plan["checkpoint_capture_profile"]["file_mode"], "0600"
            )

            result = run_cli(
                "host-run",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--execute",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(
                "Study-only checkpoint receipt contract",
                (workspace / ".fake-checkpoint-host-prompt").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertIn(
                "python3 .agents/skills/agentic-reporting/scripts/reportctl.py",
                (workspace / ".fake-checkpoint-host-prompt").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertEqual(
                stat.S_IMODE((workspace / ".agentic-reporting").stat().st_mode),
                0o700,
            )
            self.assertEqual(
                (workspace / ".agentic-reporting" / ".gitignore").read_bytes(),
                b"*\n",
            )
            execution_root = run_dir / "private" / "host-executions" / unit_id
            receipt = json.loads(
                (execution_root / "execution-receipt.json").read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["schema_version"], "1.1")
            checkpoint_receipt = receipt["checkpoint_receipt"]
            self.assertEqual(
                checkpoint_receipt["kind"], "checkpoint-artifact-receipt"
            )
            self.assertEqual(
                checkpoint_receipt["assurance"],
                "controller-event-snapshot-final-audit",
            )
            for field in (
                "checkpoint",
                "report",
                "controller_reaudit",
                "events",
            ):
                self.assertIn(field, checkpoint_receipt)
            reaudit = checkpoint_receipt["controller_reaudit"]
            self.assertEqual(
                reaudit["argv_profile"],
                "python-isolated-audit-captured-byte-pair-strict-json",
            )
            self.assertEqual(
                reaudit["report_sha256"], checkpoint_receipt["report"]["sha256"]
            )
            self.assertEqual(
                reaudit["checkpoint_intent_sha256"],
                checkpoint_receipt["checkpoint"]["intent_sha256"],
            )

            artifacts = execution_root / "checkpoint-artifacts"
            archived_checkpoint = artifacts / "checkpoint.json"
            archived_report = artifacts / "audited-report.md"
            archived_receipt = artifacts / "checkpoint-artifact-receipt.json"
            self.assertEqual(
                stat.S_IMODE(archived_checkpoint.stat().st_mode), 0o600
            )
            self.assertEqual(archived_report.read_text(encoding="utf-8"), checkpoint_response_text())
            archived_receipt_value = json.loads(
                archived_receipt.read_text(encoding="utf-8")
            )
            self.assertEqual(archived_receipt_value, checkpoint_receipt)
            receipt_schema = json.loads(
                (
                    ROOT
                    / "evals"
                    / "schema"
                    / "checkpoint-artifact-receipt.schema.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                list(
                    Draft202012Validator(receipt_schema).iter_errors(
                        archived_receipt_value
                    )
                ),
                [],
            )

            stored_root = run_dir / "records" / unit_id
            stored = json.loads((stored_root / "record.json").read_text(encoding="utf-8"))
            self.assertTrue(stored["observations"]["checkpoint_receipt_verified"])
            validated = run_cli("validate", "--run-dir", str(run_dir), "--json")
            self.assertEqual(validated.returncode, 1, validated.stdout + validated.stderr)
            self.assertEqual(json.loads(validated.stdout)["invalid_record_count"], 0)

            archived_checkpoint.write_bytes(b"{}\n")
            archived_checkpoint.chmod(0o600)
            tampered = run_cli("validate", "--run-dir", str(run_dir), "--json")
            self.assertEqual(tampered.returncode, 1, tampered.stdout + tampered.stderr)
            self.assertEqual(json.loads(tampered.stdout)["invalid_record_count"], 1)

    def test_framework_checkpoint_receipt_detects_report_mutation_before_event_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            executable = self.make_checkpoint_fake_codex(
                root, mutate_before_audit_event=True
            )
            run_dir = self.initialize(
                root,
                study_plan(
                    study_id="checkpoint-mutation-pilot",
                    host="codex",
                    executable_sha256=sha256(executable),
                ),
            )
            workspace = self.make_workspace(root, "framework-workspace", framework=True)
            unit_id = self.host_unit_id("framework")
            planned = run_cli(
                "host-plan",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--executable",
                str(executable),
                "--workspace",
                str(workspace),
            )
            self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)

            result = run_cli(
                "host-run",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--execute",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            execution_root = run_dir / "private" / "host-executions" / unit_id
            execution = json.loads(
                (execution_root / "execution-receipt.json").read_text(encoding="utf-8")
            )
            self.assertIsNone(execution["checkpoint_receipt"])
            stored = json.loads(
                (run_dir / "records" / unit_id / "record.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(stored["observations"]["checkpoint_receipt_verified"])
            validated = run_cli("validate", "--run-dir", str(run_dir), "--json")
            self.assertEqual(json.loads(validated.stdout)["invalid_record_count"], 0)

    def test_controller_reaudit_rejects_captured_bytes_that_only_passed_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            executable = self.make_checkpoint_fake_codex(
                root, deliver_post_audit_mutation=True
            )
            run_dir = self.initialize(
                root,
                study_plan(
                    study_id="checkpoint-memory-reaudit-pilot",
                    host="codex",
                    executable_sha256=sha256(executable),
                ),
            )
            workspace = self.make_workspace(root, "framework-workspace", framework=True)
            unit_id = self.host_unit_id("framework")
            planned = run_cli(
                "host-plan",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--executable",
                str(executable),
                "--workspace",
                str(workspace),
            )
            self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)

            result = run_cli(
                "host-run",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--execute",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            execution_root = run_dir / "private" / "host-executions" / unit_id
            execution = json.loads(
                (execution_root / "execution-receipt.json").read_text(encoding="utf-8")
            )
            self.assertIsNone(execution["checkpoint_receipt"])
            stored = json.loads(
                (run_dir / "records" / unit_id / "record.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(stored["observations"]["checkpoint_receipt_verified"])

    def test_local_image_target_survives_agent_audit_controller_receipt_storage_and_blind_copy(self) -> None:
        image_case = "image-anomaly-boundary"
        image_relative = Path("evals/fixtures/assets/return-curve.svg")
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            executable = self.make_checkpoint_fake_codex(
                root,
                report_body=checkpoint_image_response_text(),
                must_show="The plot alone cannot identify the cause of the drop",
            )
            run_dir = self.initialize(
                root,
                study_plan(
                    study_id="checkpoint-local-image-pilot",
                    host="codex",
                    executable_sha256=sha256(executable),
                    case_id=image_case,
                ),
            )
            unit_ids: dict[str, str] = {}
            workspaces: dict[str, Path] = {}
            for condition in ("baseline", "framework"):
                workspace = self.make_workspace(
                    root,
                    f"{condition}-workspace",
                    framework=condition == "framework",
                )
                workspaces[condition] = workspace
                unit_id = self.host_unit_id(condition, case_id=image_case)
                unit_ids[condition] = unit_id
                planned = run_cli(
                    "host-plan",
                    "--run-dir",
                    str(run_dir),
                    "--unit-id",
                    unit_id,
                    "--executable",
                    str(executable),
                    "--workspace",
                    str(workspace),
                )
                self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
                executed = run_cli(
                    "host-run",
                    "--run-dir",
                    str(run_dir),
                    "--unit-id",
                    unit_id,
                    "--execute",
                )
                self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)

            framework_workspace = workspaces["framework"]
            self.assertTrue(
                (framework_workspace / ".agentic-reporting" / image_relative).is_file()
            )
            framework_execution = (
                run_dir / "private" / "host-executions" / unit_ids["framework"]
            )
            execution_receipt = json.loads(
                (framework_execution / "execution-receipt.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIsNotNone(execution_receipt["checkpoint_receipt"])

            for condition in ("baseline", "framework"):
                stored_root = run_dir / "records" / unit_ids[condition]
                stored = json.loads(
                    (stored_root / "record.json").read_text(encoding="utf-8")
                )
                self.assertTrue(stored["machine_evaluation"]["passed"])
                self.assertTrue((stored_root / image_relative).is_file())

            blinded = run_cli("blind", "--run-dir", str(run_dir))
            self.assertEqual(blinded.returncode, 0, blinded.stdout + blinded.stderr)
            manifest = json.loads(
                (run_dir / "blind" / "manifest.json").read_text(encoding="utf-8")
            )
            pair_id = manifest["pairs"][0]["pair_id"]
            for side in ("A", "B"):
                side_root = run_dir / "blind" / "pairs" / pair_id / side
                self.assertTrue((side_root / image_relative).is_file())
                response = (side_root / "response.md").read_text(encoding="utf-8")
                self.assertIn(f"]({image_relative.as_posix()})", response)

    def test_framework_host_run_rejects_symlinked_checkpoint_artifact_mirror(self) -> None:
        image_case = "image-anomaly-boundary"
        image_path = "evals/fixtures/assets/return-curve.svg"
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            executable = self.make_checkpoint_fake_codex(
                root,
                report_body=checkpoint_image_response_text(),
                must_show="The plot alone cannot identify the cause of the drop",
                symlink_mirror_path_after_audit=image_path,
            )
            run_dir = self.initialize(
                root,
                study_plan(
                    study_id="checkpoint-image-symlink-pilot",
                    host="codex",
                    executable_sha256=sha256(executable),
                    case_id=image_case,
                ),
            )
            workspace = self.make_workspace(root, "framework-workspace", framework=True)
            unit_id = self.host_unit_id("framework", case_id=image_case)
            planned = run_cli(
                "host-plan",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--executable",
                str(executable),
                "--workspace",
                str(workspace),
            )
            self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)

            result = run_cli(
                "host-run",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--execute",
            )

            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("checkpoint artifact mirror", result.stderr.casefold())
            self.assertFalse((run_dir / "records" / unit_id).exists())

    def test_framework_checkpoint_receipt_rejects_noncontract_artifact_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            executable = self.make_checkpoint_fake_codex(root, alternate_paths=True)
            run_dir = self.initialize(
                root,
                study_plan(
                    study_id="checkpoint-alternate-path-pilot",
                    host="codex",
                    executable_sha256=sha256(executable),
                ),
            )
            workspace = self.make_workspace(root, "framework-workspace", framework=True)
            unit_id = self.host_unit_id("framework")
            planned = run_cli(
                "host-plan",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--executable",
                str(executable),
                "--workspace",
                str(workspace),
            )
            self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)

            result = run_cli(
                "host-run",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--execute",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            execution_root = run_dir / "private" / "host-executions" / unit_id
            execution = json.loads(
                (execution_root / "execution-receipt.json").read_text(encoding="utf-8")
            )
            self.assertIsNone(execution["checkpoint_receipt"])
            stored = json.loads(
                (run_dir / "records" / unit_id / "record.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(stored["observations"]["checkpoint_receipt_verified"])

    def test_framework_host_run_fails_closed_when_capture_directory_becomes_permissive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            executable = self.make_checkpoint_fake_codex(
                root, permissive_capture_directory=True
            )
            run_dir = self.initialize(
                root,
                study_plan(
                    study_id="checkpoint-permissive-directory-pilot",
                    host="codex",
                    executable_sha256=sha256(executable),
                ),
            )
            workspace = self.make_workspace(root, "framework-workspace", framework=True)
            unit_id = self.host_unit_id("framework")
            planned = run_cli(
                "host-plan",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--executable",
                str(executable),
                "--workspace",
                str(workspace),
            )
            self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)

            result = run_cli(
                "host-run",
                "--run-dir",
                str(run_dir),
                "--unit-id",
                unit_id,
                "--execute",
            )

            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("mode 0700", result.stderr)
            self.assertFalse((run_dir / "records" / unit_id).exists())

    def test_imported_image_artifacts_are_copied_and_blinded_and_bad_digests_or_paths_fail(self) -> None:
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUB"
            "AScY42YAAAAASUVORK5CYII="
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            study_id = "artifact-pilot"
            run_dir = self.initialize(root, study_plan(study_id=study_id))
            artifact_roots: list[Path] = []
            for condition in ("baseline", "framework"):
                artifact_root = root / f"{condition}-artifacts"
                image = artifact_root / "figures" / "output.png"
                image.parent.mkdir(parents=True)
                image.write_bytes(png)
                artifact_roots.append(artifact_root)
                result = self.import_manual(
                    root,
                    run_dir,
                    study_id=study_id,
                    condition=condition,
                    artifacts=[
                        {
                            "path": "figures/output.png",
                            "sha256": sha256(image),
                            "media_type": "image/png",
                        }
                    ],
                    artifact_root=artifact_root,
                    image_path="figures/output.png",
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                stored = run_dir / "records" / self.manual_unit_id(condition) / "figures" / "output.png"
                self.assertEqual(stored.read_bytes(), png)

            blinded = run_cli("blind", "--run-dir", str(run_dir))
            self.assertEqual(blinded.returncode, 0, blinded.stdout + blinded.stderr)
            manifest_path = run_dir / "blind" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            pair = manifest["pairs"][0]
            self.assertEqual(pair["artifacts"], {"A": ["figures/output.png"], "B": ["figures/output.png"]})
            for side in ("A", "B"):
                copied = run_dir / "blind" / "pairs" / pair["pair_id"] / side / "figures" / "output.png"
                self.assertEqual(copied.read_bytes(), png)
            public_manifest = manifest_path.read_text(encoding="utf-8")
            self.assertNotIn("baseline", public_manifest.casefold())
            self.assertNotIn("framework", public_manifest.casefold())
            self.assertNotIn(sha256(artifact_roots[0] / "figures" / "output.png"), public_manifest)

        for failure_kind in ("digest", "path"):
            with self.subTest(failure_kind=failure_kind), tempfile.TemporaryDirectory() as temporary:
                root = self.make_root(temporary)
                study_id = f"artifact-{failure_kind}-failure"
                run_dir = self.initialize(root, study_plan(study_id=study_id))
                artifact_root = root / "artifact-root"
                (artifact_root / "figures").mkdir(parents=True)
                image = artifact_root / "figures" / "output.png"
                image.write_bytes(png)
                if failure_kind == "digest":
                    artifact_path = "figures/output.png"
                    digest = "0" * 64
                else:
                    artifact_path = "figures/../output.png"
                    digest = sha256(image)
                result = self.import_manual(
                    root,
                    run_dir,
                    study_id=study_id,
                    condition="baseline",
                    artifacts=[
                        {
                            "path": artifact_path,
                            "sha256": digest,
                            "media_type": "image/png",
                        }
                    ],
                    artifact_root=artifact_root,
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                if failure_kind == "digest":
                    self.assertIn("digest mismatch", result.stderr)
                else:
                    self.assertIn("stay within its artifact root", result.stderr)
                self.assertFalse((run_dir / "records" / self.manual_unit_id("baseline")).exists())

    def test_pilot_summary_never_claims_effectiveness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            study_id = "claim-boundary-pilot"
            run_dir = self.initialize(root, study_plan(study_id=study_id))
            self.complete_manual(root, run_dir, study_id=study_id)

            result = run_cli("pilot-summary", "--run-dir", str(run_dir), "--json")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads(result.stdout)
            summary_schema = json.loads(
                (ROOT / "evals" / "schema" / "pilot-summary.schema.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                list(Draft202012Validator(summary_schema).iter_errors(summary)),
                [],
            )
            self.assertEqual(summary["claim"]["status"], "insufficient_evidence")
            self.assertFalse(summary["claim"]["effectiveness_claim_eligible"])
            self.assertEqual(summary["study_kind"], "pilot")
            self.assertEqual(summary["generation"]["record_count"], 2)
            persisted = json.loads(
                (run_dir / "results" / "pilot-summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(persisted["claim"], summary["claim"])

    def test_rating_template_is_owner_only_and_null_fields_cannot_be_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            study_id = "rating-template-pilot"
            run_dir = self.initialize(root, study_plan(study_id=study_id))
            self.complete_manual(root, run_dir, study_id=study_id)
            blinded = run_cli("blind", "--run-dir", str(run_dir))
            self.assertEqual(blinded.returncode, 0, blinded.stdout + blinded.stderr)
            template = root / "rater-one.json"

            created = run_cli(
                "rating-template",
                "--run-dir",
                str(run_dir),
                "--rater-id",
                "rater-one",
                "--output",
                str(template),
            )

            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(template.stat().st_mode), 0o600)
            payload = json.loads(template.read_text(encoding="utf-8"))
            self.assertFalse(payload["qualified"])
            self.assertFalse(payload["independent"])
            self.assertIsNone(payload["ratings"][0]["preference"])
            for side in ("A", "B"):
                self.assertTrue(
                    all(score is None for score in payload["ratings"][0]["sides"][side]["scores"].values())
                )
                self.assertIsNone(
                    payload["ratings"][0]["sides"][side]["comprehension"]["status_correct"]
                )

            frozen = run_cli(
                "freeze-ratings",
                "--run-dir",
                str(run_dir),
                "--rating",
                str(template),
            )
            self.assertEqual(frozen.returncode, 2, frozen.stdout + frozen.stderr)
            self.assertIn("rating preference must be A, B, or tie", frozen.stderr)
            self.assertFalse((run_dir / "ratings").exists())
            self.assertFalse((run_dir / "ratings-lock.json").exists())


if __name__ == "__main__":
    unittest.main()
