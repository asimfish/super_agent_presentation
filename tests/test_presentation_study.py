from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from scripts import presentation_study as study


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "presentation_study.py"
CASES = ROOT / "evals" / "presentation-cases.json"
DIMENSIONS = (
    "task_fidelity",
    "information_architecture",
    "readability_and_scannability",
    "completeness_and_actionability",
    "evidence_calibration",
    "visual_display_fitness",
    "concision_and_proportionality",
)


def schema(name: str) -> dict[str, object]:
    return json.loads((ROOT / "evals" / "schema" / name).read_text(encoding="utf-8"))


def assert_schema_valid(test: unittest.TestCase, name: str, value: object) -> None:
    errors = list(Draft202012Validator(schema(name)).iter_errors(value))
    test.assertEqual(errors, [], [error.message for error in errors])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cli(*arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=cwd or ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def pilot_plan() -> dict[str, object]:
    return {
        "$schema": "../schema/study-plan.schema.json",
        "schema_version": "1.0",
        "study_id": "synthetic-pilot",
        "study_kind": "pilot",
        "claim_boundary": "Synthetic pilot data cannot support an effectiveness claim.",
        "benchmark": {
            "benchmark_id": "agentic-reporting-presentation-v1",
            "cases_sha256": sha256(CASES),
            "case_ids": ["experiment-null-result"],
            "heldout": False,
            "preregistration_receipt": None,
        },
        "framework": {
            "repository": "https://github.com/asimfish/super_agent_presentation",
            "commit_sha": "b4c014d4b87c0d4556908b492dcf35cccb8631d4",
            "skill_manifest_sha256": "c3b9b3ee0ce2ddca2baaa2b542147fc9413b191df0bd6e065cee1700eab7598c",
            "adapter_sha256": "c04ab462b766baaf60bbb38e9fffe0555e71ec6d5fb2255bcd93eb2d47108080",
        },
        "execution": {
            "baseline_isolation": "same-account-workspace",
            "isolation_receipt": None,
            "global_instruction_policy": "unverified",
            "replicate_semantics": "independent-repeat",
        },
        "models": [
            {
                "id": "manual-model",
                "host": "manual",
                "host_version": "manual",
                "model": "synthetic-model",
                "revision": "synthetic-model-v1",
                "revision_receipt": None,
                "executable_sha256": None,
            }
        ],
        "conditions": ["baseline", "framework"],
        "seeds": [7],
        "contexts": [
            {
                "id": "fresh",
                "target_occupancy_percent": 10,
                "compaction_required": False,
            }
        ],
        "generation": {
            "max_output_tokens": 1200,
            "timeout_seconds": 300,
            "locale": "en-US",
            "renderer": "CommonMark",
        },
        "rating": {"required_raters": 2},
        "analysis": {
            "bootstrap_seed": 1729,
            "bootstrap_resamples": 10000,
            "primary_context_ids": ["fresh"],
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


def response_text(condition: str) -> str:
    prefix = "The framework report is calibrated." if condition == "framework" else "Results follow."
    return (
        f"{prefix}\n\n"
        "| Method | Accuracy (%) ↑ | Latency (ms) ↓ |\n"
        "|---|---:|---:|\n"
        "| A | 72.4 ± 1.1 | 31 |\n"
        "| B | 74.0 ± 1.0 | 38 |\n"
        "| C | 73.9 ± 0.9 | 29 |\n\n"
        "Accuracy is higher-is-better and latency is lower-is-better. Accuracy is the mean ± "
        "standard deviation over five seeds. No statistical significance test was run, so B "
        "and C cannot be declared statistically different. C offers the lowest observed "
        "latency while its mean accuracy is close to B; no universal winner is established.\n"
    )


class PresentationStudyTests(unittest.TestCase):
    def test_all_study_schemas_are_meta_valid(self) -> None:
        for path in sorted((ROOT / "evals" / "schema").glob("*.schema.json")):
            with self.subTest(schema=path.name):
                Draft202012Validator.check_schema(
                    json.loads(path.read_text(encoding="utf-8"))
                )

    def test_public_repeat_workspace_evidence_rejects_missing_or_reused_workspaces(self) -> None:
        records = [{"unit_id": "unit-a"}, {"unit_id": "unit-b"}]
        with patch.object(
            study,
            "_load_host_plan",
            side_effect=[{"workspace": "/private/unit-a"}, {"workspace": "/private/unit-b"}],
        ):
            self.assertTrue(study._controller_has_unique_workspaces(Path("/run"), records))
        with patch.object(
            study,
            "_load_host_plan",
            side_effect=[{"workspace": "/private/shared"}, {"workspace": "/private/shared"}],
        ):
            self.assertFalse(study._controller_has_unique_workspaces(Path("/run"), records))
        with patch.object(study, "_load_host_plan", side_effect=study.StudyError("missing")):
            self.assertFalse(study._controller_has_unique_workspaces(Path("/run"), records))

    def test_long_soak_uses_common_final_audit_without_requiring_fresh_checkpoint(self) -> None:
        records = [
            {
                "condition": "framework",
                "context_id": "fresh",
                "observations": {
                    "final_audit_passed": True,
                    "checkpoint_audit_passed": False,
                },
            },
            {
                "condition": "framework",
                "context_id": "soak",
                "observations": {
                    "final_audit_passed": True,
                    "checkpoint_audit_passed": True,
                },
            },
        ]
        contexts = {
            "fresh": {"target_occupancy_percent": 10},
            "soak": {"target_occupancy_percent": 85},
        }
        self.assertEqual(
            study._long_soak_metrics(records, contexts),
            {"fresh_pass_rate": 1.0, "soak85_pass_rate": 1.0, "gap": 0.0},
        )

    def test_input_and_controller_stored_generation_schemas_share_one_payload_contract(self) -> None:
        caller = schema("generation-record.schema.json")
        stored = schema("stored-generation-record.schema.json")
        self.assertEqual(caller["$defs"], stored["$defs"])
        caller_properties = dict(caller["properties"])
        stored_properties = dict(stored["properties"])
        caller_schema_property = caller_properties.pop("$schema")
        stored_schema_property = stored_properties.pop("$schema")
        self.assertEqual(
            caller_schema_property,
            {"const": "generation-record.schema.json"},
        )
        self.assertEqual(
            stored_schema_property,
            {"const": "stored-generation-record.schema.json"},
        )
        self.assertEqual(
            stored_properties.pop("machine_evaluation"),
            {"$ref": "#/$defs/machineEvaluation"},
        )
        self.assertEqual(caller_properties, stored_properties)
        self.assertEqual(
            set(stored["required"]),
            set(caller["required"]) | {"machine_evaluation"},
        )

    def test_schema_and_runtime_share_study_input_boundaries(self) -> None:
        cases = json.loads(CASES.read_text(encoding="utf-8"))
        plan_validator = Draft202012Validator(schema("study-plan.schema.json"))
        valid_plan = pilot_plan()
        self.assertEqual(list(plan_validator.iter_errors(valid_plan)), [])
        study._validate_plan(valid_plan, cases)
        one_character_model = copy.deepcopy(valid_plan)
        one_character_model["models"][0]["id"] = "a"
        self.assertEqual(list(plan_validator.iter_errors(one_character_model)), [])
        study._validate_plan(one_character_model, cases)

        plan_probes: list[tuple[str, dict[str, object]]] = []
        short_study = copy.deepcopy(valid_plan)
        short_study["study_id"] = "a"
        plan_probes.append(("short-study-id", short_study))
        short_context = copy.deepcopy(valid_plan)
        short_context["contexts"][0]["id"] = "a"
        short_context["analysis"]["primary_context_ids"] = ["a"]
        plan_probes.append(("short-context-id", short_context))
        heldout_pilot = copy.deepcopy(valid_plan)
        heldout_pilot["benchmark"]["heldout"] = True
        plan_probes.append(("heldout-pilot", heldout_pilot))
        whitespace_claim = copy.deepcopy(valid_plan)
        whitespace_claim["claim_boundary"] = "   "
        plan_probes.append(("whitespace-claim", whitespace_claim))
        whitespace_model = copy.deepcopy(valid_plan)
        whitespace_model["models"][0]["revision"] = "   "
        plan_probes.append(("whitespace-model-revision", whitespace_model))
        leading_hyphen_model = copy.deepcopy(valid_plan)
        leading_hyphen_model["models"][0]["id"] = "-model"
        plan_probes.append(("leading-hyphen-model-id", leading_hyphen_model))
        for name, value in plan_probes:
            with self.subTest(kind="plan", name=name):
                self.assertTrue(list(plan_validator.iter_errors(value)))
                with self.assertRaises(study.StudyError):
                    study._validate_plan(value, cases)

        expected = {
            "unit_id": "experiment-null-result--manual-model--fresh--s7--baseline",
            "pair_key": "experiment-null-result--manual-model--fresh--s7",
            "case_id": "experiment-null-result",
            "model_id": "manual-model",
            "context_id": "fresh",
            "seed": 7,
            "condition": "baseline",
            "prompt": "prompts/experiment-null-result--manual-model--fresh--s7.txt",
            "prompt_sha256": "0" * 64,
        }
        valid_record = {
            "$schema": "generation-record.schema.json",
            "schema_version": "1.0",
            "study_id": "synthetic-pilot",
            **{field: expected[field] for field in (
                "unit_id", "case_id", "model_id", "context_id", "seed", "condition",
                "prompt_sha256",
            )},
            "host": "manual",
            "host_version": "manual",
            "model": "synthetic-model",
            "model_revision": "synthetic-model-v1",
            "response_sha256": "1" * 64,
            "transcript_sha256": None,
            "artifacts": [],
            "usage": {
                "input_tokens": 1,
                "cached_input_tokens": 0,
                "output_tokens": 1,
                "latency_ms": 1,
                "context_occupancy_percent": 10,
                "compaction_observed": False,
            },
            "observations": {
                "telemetry_source": "manual",
                "host_activation_observed": None,
                "skill_read": None,
                "checkpoint_created": None,
                "checkpoint_reloaded": None,
                "checkpoint_audit_passed": None,
                "final_audit_passed": None,
                "checkpoint_receipt_verified": None,
                "output_token_cap_enforced": None,
            },
        }
        record_validator = Draft202012Validator(schema("generation-record.schema.json"))
        self.assertEqual(list(record_validator.iter_errors(valid_record)), [])
        study._validate_generation_record(
            valid_record,
            plan=valid_plan,
            expected_record=expected,
        )
        valid_artifact_record = copy.deepcopy(valid_record)
        valid_artifact_record["artifacts"] = [
            {
                "path": "plots/figure.png",
                "sha256": "2" * 64,
                "media_type": "image/png",
            }
        ]
        self.assertEqual(list(record_validator.iter_errors(valid_artifact_record)), [])
        study._validate_generation_record(
            valid_artifact_record,
            plan=valid_plan,
            expected_record=expected,
        )
        record_probes: list[tuple[str, dict[str, object]]] = []
        oversized_tokens = copy.deepcopy(valid_record)
        oversized_tokens["usage"]["output_tokens"] = 10**12 + 1
        record_probes.append(("oversized-token-count", oversized_tokens))
        caller_machine = copy.deepcopy(valid_record)
        caller_machine["machine_evaluation"] = {}
        record_probes.append(("caller-machine-evaluation", caller_machine))
        wrong_schema = copy.deepcopy(valid_record)
        wrong_schema["$schema"] = "stored-generation-record.schema.json"
        record_probes.append(("wrong-caller-schema", wrong_schema))
        uppercase_artifact = copy.deepcopy(valid_record)
        uppercase_artifact["artifacts"] = [
            {
                "path": "plots/figure.PNG",
                "sha256": "2" * 64,
                "media_type": "image/png",
            }
        ]
        record_probes.append(("uppercase-artifact-suffix", uppercase_artifact))
        hidden_basename_artifact = copy.deepcopy(valid_record)
        hidden_basename_artifact["artifacts"] = [
            {
                "path": "plots/.png",
                "sha256": "2" * 64,
                "media_type": "image/png",
            }
        ]
        record_probes.append(("hidden-artifact-basename", hidden_basename_artifact))
        for name, value in record_probes:
            with self.subTest(kind="generation", name=name):
                self.assertTrue(list(record_validator.iter_errors(value)))
                with self.assertRaises(study.StudyError):
                    study._validate_generation_record(
                        value,
                        plan=valid_plan,
                        expected_record=expected,
                    )

        scores = {dimension: 4 for dimension in DIMENSIONS}
        side = {
            "scores": scores,
            "critical_errors": [],
            "semantic_slots_present": [],
            "comprehension": {
                "status_correct": True,
                "strongest_evidence_correct": True,
                "next_action_or_limit_correct": True,
                "elapsed_seconds": 1.0,
            },
        }
        valid_rating = {
            "$schema": "rating-batch.schema.json",
            "schema_version": "1.0",
            "study_id": "synthetic-pilot",
            "rater_id": "a",
            "qualified": True,
            "independent": True,
            "ratings": [
                {
                    "pair_id": "pair-0001",
                    "sides": {"A": copy.deepcopy(side), "B": copy.deepcopy(side)},
                    "preference": "tie",
                    "notes": "",
                }
            ],
        }
        pairs = {"pair-0001": {"required_semantic_slots": []}}
        rating_validator = Draft202012Validator(schema("rating-batch.schema.json"))
        self.assertEqual(list(rating_validator.iter_errors(valid_rating)), [])
        self.assertEqual(
            study._validate_rating_batch(
                valid_rating,
                study_id="synthetic-pilot",
                pairs=pairs,
            ),
            "a",
        )
        long_evidence = copy.deepcopy(valid_rating)
        long_evidence["ratings"][0]["sides"]["A"]["critical_errors"] = [
            {"label": "fabricated_evidence", "evidence": "x" * 1001}
        ]
        too_many_errors = copy.deepcopy(valid_rating)
        too_many_errors["ratings"][0]["sides"]["A"]["critical_errors"] = [
            {"label": "fabricated_evidence", "evidence": f"finding-{index}"}
            for index in range(21)
        ]
        duplicate_errors = copy.deepcopy(valid_rating)
        duplicate_errors["ratings"][0]["sides"]["A"]["critical_errors"] = [
            {"label": "fabricated_evidence", "evidence": "duplicate"},
            {"label": "fabricated_evidence", "evidence": "duplicate"},
        ]
        for name, value in (
            ("long-critical-evidence", long_evidence),
            ("too-many-critical-errors", too_many_errors),
            ("duplicate-critical-errors", duplicate_errors),
        ):
            with self.subTest(kind="rating", name=name):
                self.assertTrue(list(rating_validator.iter_errors(value)))
                with self.assertRaises(study.StudyError):
                    study._validate_rating_batch(
                        value,
                        study_id="synthetic-pilot",
                        pairs=pairs,
                    )

    def test_pilot_template_matches_authoritative_study_plan_schema(self) -> None:
        template = json.loads(
            (ROOT / "evals" / "templates" / "pilot-study-plan.json").read_text(encoding="utf-8")
        )
        assert_schema_valid(self, "study-plan.schema.json", template)

    def test_pilot_template_receipts_must_be_replaced_before_init(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = run_cli(
                "init",
                "--plan",
                str(ROOT / "evals" / "templates" / "pilot-study-plan.json"),
                "--cases-file",
                str(CASES),
                "--output",
                str(root / "run"),
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("template placeholder", result.stderr)

    def test_checked_in_real_host_pilot_summary_is_schema_valid_and_redacted(self) -> None:
        path = (
            ROOT
            / "evals"
            / "runs"
            / "pilot"
            / "codex-20260824"
            / "pilot-summary.json"
        )
        summary = json.loads(path.read_text(encoding="utf-8"))
        assert_schema_valid(self, "pilot-summary.schema.json", summary)
        self.assertEqual(summary["claim"]["status"], "insufficient_evidence")
        self.assertFalse(summary["claim"]["effectiveness_claim_eligible"])

        forbidden_keys = {
            "prompt",
            "response",
            "transcript",
            "workspace",
            "executable",
            "assignment_key",
            "ratings",
        }

        def visit(value: object) -> None:
            if isinstance(value, dict):
                self.assertTrue(forbidden_keys.isdisjoint(value))
                for nested in value.values():
                    visit(nested)
            elif isinstance(value, list):
                for nested in value:
                    visit(nested)
            elif isinstance(value, str):
                self.assertNotIn("/private/", value)
                self.assertNotIn("/Users/", value)

        visit(summary)

    def prepare(self, root: Path) -> Path:
        plan_path = root / "plan.json"
        plan_path.write_text(json.dumps(pilot_plan()), encoding="utf-8")
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

    def import_condition(self, root: Path, run_dir: Path, condition: str) -> None:
        response = root / f"{condition}.md"
        response.write_text(response_text(condition), encoding="utf-8")
        prompt = run_dir / "prompts" / "experiment-null-result--manual-model--fresh--s7.txt"
        record = {
            "$schema": "generation-record.schema.json",
            "schema_version": "1.0",
            "study_id": "synthetic-pilot",
            "unit_id": f"experiment-null-result--manual-model--fresh--s7--{condition}",
            "case_id": "experiment-null-result",
            "model_id": "manual-model",
            "context_id": "fresh",
            "seed": 7,
            "condition": condition,
            "host": "manual",
            "host_version": "manual",
            "model": "synthetic-model",
            "model_revision": "synthetic-model-v1",
            "prompt_sha256": sha256(prompt),
            "response_sha256": sha256(response),
            "transcript_sha256": None,
            "artifacts": [],
            "usage": {
                "input_tokens": 1000,
                "cached_input_tokens": 0,
                "output_tokens": 200 if condition == "baseline" else 220,
                "latency_ms": 1000,
                "context_occupancy_percent": 10,
                "compaction_observed": False,
            },
            "observations": {
                "telemetry_source": "manual",
                "host_activation_observed": None if condition == "baseline" else True,
                "skill_read": None if condition == "baseline" else True,
                "checkpoint_created": None,
                "checkpoint_reloaded": None,
                "checkpoint_audit_passed": None,
                "final_audit_passed": None,
                "checkpoint_receipt_verified": None,
                "output_token_cap_enforced": None,
            },
        }
        record_path = root / f"{condition}.record.json"
        record_path.write_text(json.dumps(record), encoding="utf-8")
        result = run_cli(
            "import-output",
            "--run-dir",
            str(run_dir),
            "--record",
            str(record_path),
            "--response",
            str(response),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        stored = json.loads(
            (
                run_dir
                / "records"
                / f"experiment-null-result--manual-model--fresh--s7--{condition}"
                / "record.json"
            ).read_text(encoding="utf-8")
        )
        assert_schema_valid(self, "stored-generation-record.schema.json", stored)

    def complete_outputs(self, root: Path, run_dir: Path) -> None:
        self.import_condition(root, run_dir, "baseline")
        self.import_condition(root, run_dir, "framework")

    def write_rating(self, root: Path, pair_id: str, rater_id: str, key: dict[str, object]) -> Path:
        assignment = key["assignments"][0]
        sides: dict[str, object] = {}
        for side in ("A", "B"):
            condition = assignment[side]
            score = 5 if condition == "framework" else 4
            sides[side] = {
                "scores": {dimension: score for dimension in DIMENSIONS},
                "critical_errors": [],
                "semantic_slots_present": [
                    "protocol",
                    "quantitative_display",
                    "verified_result",
                    "uncertainty_boundary",
                    "tradeoff_conclusion",
                ],
                "comprehension": {
                    "status_correct": True,
                    "strongest_evidence_correct": True,
                    "next_action_or_limit_correct": True,
                    "elapsed_seconds": 20.0,
                },
            }
        preferred = "A" if assignment["A"] == "framework" else "B"
        rating = {
            "$schema": "rating-batch.schema.json",
            "schema_version": "1.0",
            "study_id": "synthetic-pilot",
            "rater_id": rater_id,
            "qualified": True,
            "independent": True,
            "ratings": [
                {
                    "pair_id": pair_id,
                    "sides": sides,
                    "preference": preferred,
                    "notes": "Synthetic test rating.",
                }
            ],
        }
        path = root / f"{rater_id}.json"
        path.write_text(json.dumps(rating), encoding="utf-8")
        return path

    def test_init_freezes_plan_cases_prompts_and_expected_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.prepare(root)
            expected = json.loads((run_dir / "expected-records.json").read_text(encoding="utf-8"))
            self.assertEqual(len(expected["records"]), 2)
            self.assertEqual(
                {record["condition"] for record in expected["records"]},
                {"baseline", "framework"},
            )
            self.assertTrue((run_dir / "plan.json").is_file())
            self.assertTrue((run_dir / "cases.json").is_file())
            self.assertEqual(stat.S_IMODE(run_dir.stat().st_mode), 0o700)

    def test_init_rejects_a_run_directory_inside_a_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            root = Path(temporary)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(pilot_plan()), encoding="utf-8")
            result = run_cli(
                "init", "--plan", str(plan_path), "--cases-file", str(CASES),
                "--output", str(root / "run")
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("outside a Git worktree", result.stderr)
            self.assertFalse((root / "run").exists())

    def test_validate_fails_closed_until_every_pair_is_imported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.prepare(root)
            incomplete = run_cli("validate", "--run-dir", str(run_dir), "--json")
            self.assertEqual(incomplete.returncode, 1)
            self.assertEqual(json.loads(incomplete.stdout)["missing_record_count"], 2)
            self.complete_outputs(root, run_dir)
            complete = run_cli("validate", "--run-dir", str(run_dir), "--json")
            self.assertEqual(complete.returncode, 0, complete.stdout + complete.stderr)
            self.assertEqual(json.loads(complete.stdout)["missing_record_count"], 0)

    def test_blind_packet_contains_no_condition_or_private_source_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.prepare(root)
            self.complete_outputs(root, run_dir)
            result = run_cli("blind", "--run-dir", str(run_dir))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            key_path = run_dir / "private" / "assignment-key.json"
            self.assertEqual(stat.S_IMODE(key_path.stat().st_mode), 0o600)
            manifest_text = (run_dir / "blind" / "manifest.json").read_text(encoding="utf-8")
            self.assertNotIn("baseline", manifest_text)
            self.assertNotIn("framework", manifest_text)
            self.assertNotIn(str(root), manifest_text)
            manifest = json.loads(manifest_text)
            pair_id = manifest["pairs"][0]["pair_id"]
            self.assertTrue((run_dir / "blind" / "pairs" / pair_id / "A" / "response.md").is_file())
            self.assertTrue((run_dir / "blind" / "pairs" / pair_id / "B" / "response.md").is_file())

    def test_rating_lock_detects_post_freeze_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.prepare(root)
            self.complete_outputs(root, run_dir)
            self.assertEqual(run_cli("blind", "--run-dir", str(run_dir)).returncode, 0)
            key = json.loads((run_dir / "private" / "assignment-key.json").read_text(encoding="utf-8"))
            pair_id = key["assignments"][0]["pair_id"]
            paths = [
                self.write_rating(root, pair_id, "rater-1", key),
                self.write_rating(root, pair_id, "rater-2", key),
            ]
            frozen = run_cli(
                "freeze-ratings", "--run-dir", str(run_dir),
                "--rating", str(paths[0]), "--rating", str(paths[1])
            )
            self.assertEqual(frozen.returncode, 0, frozen.stdout + frozen.stderr)
            stored = run_dir / "ratings" / "rater-1.json"
            stored.write_text(stored.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            aggregate = run_cli("aggregate", "--run-dir", str(run_dir), "--json")
            self.assertEqual(aggregate.returncode, 2)
            self.assertIn("changed after ratings were frozen", aggregate.stderr)

    def test_rating_lock_binds_the_entire_blind_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.prepare(root)
            self.complete_outputs(root, run_dir)
            self.assertEqual(run_cli("blind", "--run-dir", str(run_dir)).returncode, 0)
            key = json.loads(
                (run_dir / "private" / "assignment-key.json").read_text(encoding="utf-8")
            )
            pair_id = key["assignments"][0]["pair_id"]
            ratings = [
                self.write_rating(root, pair_id, "rater-1", key),
                self.write_rating(root, pair_id, "rater-2", key),
            ]
            frozen = run_cli(
                "freeze-ratings",
                "--run-dir",
                str(run_dir),
                "--rating",
                str(ratings[0]),
                "--rating",
                str(ratings[1]),
            )
            self.assertEqual(frozen.returncode, 0, frozen.stdout + frozen.stderr)
            manifest = run_dir / "blind" / "manifest.json"
            manifest.write_text(
                manifest.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            aggregate = run_cli("aggregate", "--run-dir", str(run_dir), "--json")
            self.assertEqual(aggregate.returncode, 2, aggregate.stdout + aggregate.stderr)
            self.assertIn("Blind packet changed after ratings were frozen", aggregate.stderr)

    def test_end_to_end_pilot_aggregates_but_never_allows_effectiveness_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.prepare(root)
            self.complete_outputs(root, run_dir)
            self.assertEqual(run_cli("blind", "--run-dir", str(run_dir)).returncode, 0)
            key = json.loads((run_dir / "private" / "assignment-key.json").read_text(encoding="utf-8"))
            pair_id = key["assignments"][0]["pair_id"]
            ratings = [
                self.write_rating(root, pair_id, "rater-1", key),
                self.write_rating(root, pair_id, "rater-2", key),
            ]
            self.assertEqual(
                run_cli(
                    "freeze-ratings", "--run-dir", str(run_dir),
                    "--rating", str(ratings[0]), "--rating", str(ratings[1])
                ).returncode,
                0,
            )
            aggregate = run_cli("aggregate", "--run-dir", str(run_dir), "--json")
            self.assertEqual(aggregate.returncode, 0, aggregate.stdout + aggregate.stderr)
            report = json.loads(aggregate.stdout)
            assert_schema_valid(self, "study-report.schema.json", report)
            self.assertEqual(report["claim"]["status"], "insufficient_evidence")
            self.assertFalse(report["claim"]["effectiveness_claim_eligible"])
            self.assertIn("pilot", report["claim"]["missing_prerequisites"])
            self.assertIn(
                "enforced-output-token-cap",
                report["claim"]["missing_prerequisites"],
            )
            self.assertIn(
                "model-revision-receipts",
                report["claim"]["missing_prerequisites"],
            )
            self.assertIn(
                "controller-bound-executable-hosts",
                report["claim"]["missing_prerequisites"],
            )
            self.assertNotIn(
                "framework-checkpoint-contract",
                report["claim"]["missing_prerequisites"],
            )
            self.assertGreater(report["metrics"]["primary_composite"]["difference"], 0)
            self.assertEqual(report["ratings"]["rater_count"], 2)
            self.assertEqual(report["critical_error_count"], 0)
            self.assertTrue(
                any("reveal treatment" in item for item in report["limitations"])
            )
            self.assertEqual(report["metrics"]["mandatory_display_checks"]["total"], 2)
            self.assertTrue(report["gates"]["mandatory_display_checks"])
            self.assertLess(
                report["metrics"]["semantic_slot_density_per_1000_output_tokens"][
                    "difference"
                ],
                0,
            )
            self.assertFalse(report["gates"]["semantic_density_noninferior"])
            self.assertIn(
                "visual-forbidden-oracle-coverage",
                report["claim"]["missing_prerequisites"],
            )
            self.assertIn(
                "required-local-image-check-coverage",
                report["claim"]["missing_prerequisites"],
            )

    def test_empty_visual_denominators_fail_closed_and_block_public_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cases = json.loads(CASES.read_text(encoding="utf-8"))
            selected = next(
                case for case in cases["cases"] if case["id"] == "experiment-null-result"
            )
            selected["visual_oracle"]["necessity"] = "optional"
            custom_cases = root / "cases.json"
            custom_cases.write_text(json.dumps(cases), encoding="utf-8")
            plan = pilot_plan()
            plan["benchmark"]["cases_sha256"] = sha256(custom_cases)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            run_dir = root / "run"
            initialized = run_cli(
                "init",
                "--plan",
                str(plan_path),
                "--cases-file",
                str(custom_cases),
                "--output",
                str(run_dir),
            )
            self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)
            self.complete_outputs(root, run_dir)
            self.assertEqual(run_cli("blind", "--run-dir", str(run_dir)).returncode, 0)
            key = json.loads(
                (run_dir / "private" / "assignment-key.json").read_text(encoding="utf-8")
            )
            pair_id = key["assignments"][0]["pair_id"]
            ratings = [
                self.write_rating(root, pair_id, "visual-rater-1", key),
                self.write_rating(root, pair_id, "visual-rater-2", key),
            ]
            frozen = run_cli(
                "freeze-ratings",
                "--run-dir",
                str(run_dir),
                "--rating",
                str(ratings[0]),
                "--rating",
                str(ratings[1]),
            )
            self.assertEqual(frozen.returncode, 0, frozen.stdout + frozen.stderr)
            aggregate = run_cli("aggregate", "--run-dir", str(run_dir), "--json")
            self.assertEqual(aggregate.returncode, 0, aggregate.stdout + aggregate.stderr)
            report = json.loads(aggregate.stdout)
            self.assertIsNone(report["metrics"]["visual_selection"]["precision"])
            self.assertIsNone(report["metrics"]["visual_selection"]["recall"])
            self.assertFalse(report["gates"]["visual_precision"])
            self.assertFalse(report["gates"]["visual_recall"])
            self.assertIn(
                "visual-required-oracle-coverage",
                report["claim"]["missing_prerequisites"],
            )
            self.assertIn(
                "visual-forbidden-oracle-coverage",
                report["claim"]["missing_prerequisites"],
            )


if __name__ == "__main__":
    unittest.main()
