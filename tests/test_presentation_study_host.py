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


def study_plan(
    *,
    study_id: str,
    host: str = "manual",
    executable_sha256: str | None = None,
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
                "abaa134681e6180ef59cc70ecf35332a5fa9cd50dc0dfcea7d0a7860e4d45749"
            ),
            "adapter_sha256": (
                "c04ab462b766baaf60bbb38e9fffe0555e71ec6d5fb2255bcd93eb2d47108080"
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
            "case_ids": [CASE_ID],
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

    def host_unit_id(self, condition: str) -> str:
        return f"{CASE_ID}--{MODEL_ID}--{CONTEXT_ID}--s{SEED}--{condition}"

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
        self.assertEqual(telemetry.event_count, 5)

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
