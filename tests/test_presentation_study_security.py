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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def pilot_plan() -> dict[str, object]:
    return {
        "$schema": "../schema/study-plan.schema.json",
        "schema_version": "1.0",
        "study_id": "security-pilot",
        "study_kind": "pilot",
        "claim_boundary": "Pilot data cannot support an effectiveness claim.",
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
    lead = "The framework report is calibrated." if condition == "framework" else "Results follow."
    return (
        f"{lead}\n\n"
        "| Method | Accuracy (%) \u2191 | Latency (ms) \u2193 |\n"
        "|---|---:|---:|\n"
        "| A | 72.4 \u00b1 1.1 | 31 |\n"
        "| B | 74.0 \u00b1 1.0 | 38 |\n"
        "| C | 73.9 \u00b1 0.9 | 29 |\n\n"
        "Accuracy is higher-is-better and latency is lower-is-better. Accuracy is the mean \u00b1 "
        "standard deviation over five seeds. No statistical significance test was run, so B "
        "and C cannot be declared statistically different. C offers the lowest observed "
        "latency while its mean accuracy is close to B; no universal winner is established.\n"
    )


class PresentationStudySecurityTests(unittest.TestCase):
    """Denied-path tests for private inputs, evidence locks, and claim boundaries."""

    def prepare(self, root: Path, *, plan: dict[str, object] | None = None) -> Path:
        plan_path = root / "plan.json"
        plan_path.write_text(json.dumps(plan or pilot_plan()), encoding="utf-8")
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

    def import_condition(
        self,
        root: Path,
        run_dir: Path,
        condition: str,
        *,
        telemetry_source: object = "manual",
        output_token_cap_enforced: bool | None = None,
        checkpoint_receipt_verified: bool | None = None,
        unit_id_override: object | None = None,
        expect_success: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        response = root / f"{condition}.md"
        response.write_text(response_text(condition), encoding="utf-8")
        prompt = run_dir / "prompts" / "experiment-null-result--manual-model--fresh--s7.txt"
        record = {
            "$schema": "generation-record.schema.json",
            "schema_version": "1.0",
            "study_id": "security-pilot",
            "unit_id": (
                f"experiment-null-result--manual-model--fresh--s7--{condition}"
                if unit_id_override is None
                else unit_id_override
            ),
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
                "telemetry_source": telemetry_source,
                "host_activation_observed": None if condition == "baseline" else True,
                "skill_read": None if condition == "baseline" else True,
                "checkpoint_created": None,
                "checkpoint_reloaded": None,
                "checkpoint_audit_passed": None,
                "final_audit_passed": None,
                "checkpoint_receipt_verified": checkpoint_receipt_verified,
                "output_token_cap_enforced": output_token_cap_enforced,
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
        if expect_success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def complete_and_blind(self, root: Path, run_dir: Path) -> dict[str, object]:
        self.import_condition(root, run_dir, "baseline")
        self.import_condition(root, run_dir, "framework")
        result = run_cli("blind", "--run-dir", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(
            (run_dir / "private" / "assignment-key.json").read_text(encoding="utf-8")
        )

    def valid_rating(self, key: dict[str, object], rater_id: str) -> dict[str, object]:
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
        return {
            "$schema": "rating-batch.schema.json",
            "schema_version": "1.0",
            "study_id": "security-pilot",
            "rater_id": rater_id,
            "qualified": True,
            "independent": True,
            "ratings": [
                {
                    "pair_id": assignment["pair_id"],
                    "sides": sides,
                    "preference": preferred,
                    "notes": "Synthetic security-boundary rating.",
                }
            ],
        }

    def write_rating(self, root: Path, rating: dict[str, object]) -> Path:
        path = root / f"{rating['rater_id']}.json"
        path.write_text(json.dumps(rating), encoding="utf-8")
        return path

    def test_init_rejects_nonstandard_and_overlong_json_numbers_before_conversion(self) -> None:
        valid = json.dumps(pilot_plan(), separators=(",", ":"))
        probes = (
            (
                "nonstandard",
                valid.replace('"target_occupancy_percent":10', '"target_occupancy_percent":NaN'),
                "non-standard numeric constant NaN",
            ),
            (
                "long-integer",
                valid.replace('"max_output_tokens":1200', '"max_output_tokens":' + "9" * 129),
                "integer literal exceeds 128 characters",
            ),
            (
                "long-float",
                valid.replace(
                    '"target_occupancy_percent":10',
                    '"target_occupancy_percent":0.' + "0" * 128 + "1",
                ),
                "floating-point literal exceeds 128 characters",
            ),
            (
                "deep-json",
                '{"a":' * 101 + "0" + "}" * 101,
                "JSON exceeds nesting depth 100",
            ),
        )
        for name, payload, expected_error in probes:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                plan_path = root / "plan.json"
                plan_path.write_text(payload, encoding="utf-8")
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
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(expected_error, result.stderr)
                self.assertFalse(run_dir.exists())

    def test_unhashable_plan_elements_fail_without_traceback(self) -> None:
        probes = (
            ("case-ids", ("benchmark", "case_ids"), [{}], "case_id must be a nonempty string"),
            (
                "primary-contexts",
                ("analysis", "primary_context_ids"),
                [{}],
                "primary context id must be a nonempty string",
            ),
            (
                "primary-dimensions",
                ("analysis", "primary_dimensions"),
                [{}],
                "primary_dimensions must be unique known rating dimensions",
            ),
            ("benchmark", ("benchmark",), [], "benchmark must be an object"),
            ("study-kind", ("study_kind",), {}, "study_kind is unsupported"),
            (
                "baseline-isolation",
                ("execution", "baseline_isolation"),
                {},
                "execution baseline_isolation is unsupported",
            ),
            (
                "model-host",
                ("models", 0, "host"),
                {},
                "model manual-model host is unsupported",
            ),
        )
        for name, path, value, message in probes:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                plan = pilot_plan()
                target = plan
                for component in path[:-1]:
                    target = target[component]
                target[path[-1]] = value
                plan_path = root / "plan.json"
                plan_path.write_text(json.dumps(plan), encoding="utf-8")
                result = run_cli(
                    "init",
                    "--plan",
                    str(plan_path),
                    "--cases-file",
                    str(CASES),
                    "--output",
                    str(root / "run"),
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(message, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_runtime_enforces_versioned_bootstrap_and_threshold_profile(self) -> None:
        probes = (
            ("bootstrap", ("analysis", "bootstrap_resamples"), 9999, "10000 to 1000000"),
            (
                "bootstrap-seed",
                ("analysis", "bootstrap_seed"),
                -1,
                "integer from 0 to 2147483647",
            ),
            (
                "threshold",
                ("analysis", "thresholds", "machine_pass_rate_min"),
                0.0,
                "must equal the versioned release value 0.98",
            ),
        )
        for name, path, value, message in probes:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                plan = pilot_plan()
                target = plan
                for component in path[:-1]:
                    target = target[component]
                target[path[-1]] = value
                plan_path = root / "plan.json"
                plan_path.write_text(json.dumps(plan), encoding="utf-8")
                result = run_cli(
                    "init",
                    "--plan",
                    str(plan_path),
                    "--cases-file",
                    str(CASES),
                    "--output",
                    str(root / "run"),
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(message, result.stderr)

    def test_manual_import_cannot_self_report_host_adapter_or_enforced_cap(self) -> None:
        probes = (
            ("host_adapter", None, "Manual model records must use manual telemetry"),
            (
                "manual",
                True,
                "enforced output-token cap requires a controller-owned host execution binding",
            ),
        )
        for telemetry_source, enforced, message in probes:
            with self.subTest(telemetry_source=telemetry_source, enforced=enforced):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    run_dir = self.prepare(root)
                    result = self.import_condition(
                        root,
                        run_dir,
                        "baseline",
                        telemetry_source=telemetry_source,
                        output_token_cap_enforced=enforced,
                        expect_success=False,
                    )
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn(message, result.stderr)
                    self.assertFalse(
                        (run_dir / "records" / "experiment-null-result--manual-model--fresh--s7--baseline").exists()
                    )

    def test_manual_import_cannot_self_report_checkpoint_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.prepare(root)

            result = self.import_condition(
                root,
                run_dir,
                "framework",
                checkpoint_receipt_verified=True,
                expect_success=False,
            )

            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn(
                "verified checkpoint receipt requires a controller-owned host execution binding",
                result.stderr.casefold(),
            )
            self.assertFalse(
                (
                    run_dir
                    / "records"
                    / "experiment-null-result--manual-model--fresh--s7--framework"
                ).exists()
            )

    def test_unhashable_generation_fields_fail_without_traceback(self) -> None:
        probes = (
            ({"unit_id_override": {}}, "generation record unit_id must be a bounded string"),
            ({"telemetry_source": {}}, "telemetry_source is unsupported"),
        )
        for overrides, message in probes:
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                run_dir = self.prepare(root)
                result = self.import_condition(
                    root,
                    run_dir,
                    "baseline",
                    expect_success=False,
                    **overrides,
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(message, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_manual_generation_record_is_digest_locked_after_import(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.prepare(root)
            self.import_condition(root, run_dir, "baseline")
            stored = (
                run_dir
                / "records"
                / "experiment-null-result--manual-model--fresh--s7--baseline"
                / "record.json"
            )
            record = json.loads(stored.read_text(encoding="utf-8"))
            record["usage"]["output_tokens"] = 999
            stored.write_text(json.dumps(record), encoding="utf-8")
            result = run_cli("validate", "--run-dir", str(run_dir), "--json")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["invalid_record_count"], 1)

    def test_init_rejects_colliding_composed_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = pilot_plan()
            plan["models"] = [
                {
                    "id": model_id,
                    "host": "manual",
                    "host_version": "manual",
                    "model": "synthetic-model",
                    "revision": f"revision-{index}",
                    "revision_receipt": None,
                    "executable_sha256": None,
                }
                for index, model_id in enumerate(("a--b", "a"))
            ]
            plan["contexts"] = [
                {
                    "id": context_id,
                    "target_occupancy_percent": 10,
                    "compaction_required": False,
                }
                for context_id in ("cc", "b--cc")
            ]
            plan["analysis"]["primary_context_ids"] = ["cc"]
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
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("colliding composed pair key", result.stderr)
            self.assertFalse(run_dir.exists())

    def test_init_rejects_cartesian_generation_matrix_before_writing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = pilot_plan()
            plan["models"] = [
                {
                    "id": f"model-{index}",
                    "host": "manual",
                    "host_version": "manual",
                    "model": "synthetic-model",
                    "revision": f"synthetic-{index}",
                    "revision_receipt": None,
                    "executable_sha256": None,
                }
                for index in range(20)
            ]
            plan["contexts"] = [
                {
                    "id": f"context-{index}",
                    "target_occupancy_percent": index,
                    "compaction_required": False,
                }
                for index in range(20)
            ]
            plan["analysis"]["primary_context_ids"] = ["context-0"]
            plan["seeds"] = list(range(100))
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
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("1500-record safety limit", result.stderr)
            self.assertFalse(run_dir.exists())

    @unittest.skipIf(os.name == "nt", "symbolic-link policy is POSIX-specific")
    def test_symlinked_input_output_component_and_run_directory_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = root / "plan.json"
            plan.write_text(json.dumps(pilot_plan()), encoding="utf-8")
            plan_link = root / "plan-link.json"
            plan_link.symlink_to(plan)
            result = run_cli(
                "init",
                "--plan",
                str(plan_link),
                "--cases-file",
                str(CASES),
                "--output",
                str(root / "linked-input-run"),
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("symlink component", result.stderr)
            self.assertFalse((root / "linked-input-run").exists())

            real_parent = root / "real-parent"
            real_parent.mkdir()
            parent_link = root / "parent-link"
            parent_link.symlink_to(real_parent, target_is_directory=True)
            result = run_cli(
                "init",
                "--plan",
                str(plan),
                "--cases-file",
                str(CASES),
                "--output",
                str(parent_link / "run"),
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("symlink component", result.stderr)
            self.assertFalse((real_parent / "run").exists())

            run_dir = self.prepare(root)
            run_link = root / "run-link"
            run_link.symlink_to(run_dir, target_is_directory=True)
            result = run_cli("validate", "--run-dir", str(run_link), "--json")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("symlink component", result.stderr)

    @unittest.skipIf(os.name == "nt", "POSIX mode-bit policy is not portable to Windows")
    def test_run_directory_with_group_or_other_permissions_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.prepare(root)
            os.chmod(run_dir, 0o750)
            try:
                result = run_cli("validate", "--run-dir", str(run_dir), "--json")
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(
                    "Run directory must not grant group or other permissions",
                    result.stderr,
                )
            finally:
                os.chmod(run_dir, 0o700)

    def test_each_digest_locked_run_input_detects_post_init_mutation(self) -> None:
        for filename in ("plan.json", "cases.json", "expected-records.json"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                run_dir = self.prepare(root)
                frozen = run_dir / filename
                frozen.write_text(frozen.read_text(encoding="utf-8") + " \n", encoding="utf-8")
                result = run_cli("validate", "--run-dir", str(run_dir), "--json")
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(f"Frozen run input changed after init: {filename}", result.stderr)

    @unittest.skipIf(os.name == "nt", "POSIX mode-bit policy is not portable to Windows")
    def test_blind_assignment_key_with_broad_permissions_cannot_be_consumed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.prepare(root)
            self.complete_and_blind(root, run_dir)
            key_path = run_dir / "private" / "assignment-key.json"
            self.assertEqual(stat.S_IMODE(key_path.stat().st_mode), 0o600)
            os.chmod(key_path, 0o644)
            try:
                result = run_cli(
                    "freeze-ratings",
                    "--run-dir",
                    str(run_dir),
                    "--rating",
                    str(root / "unused.json"),
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(
                    "Assignment key must not grant group or other permissions",
                    result.stderr,
                )
                self.assertFalse((run_dir / "ratings").exists())
                self.assertFalse((run_dir / "ratings-lock.json").exists())
            finally:
                os.chmod(key_path, 0o600)

    def test_rating_batches_reject_out_of_range_scores_and_missing_fields_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.prepare(root)
            key = self.complete_and_blind(root, run_dir)
            valid_second = self.write_rating(root, self.valid_rating(key, "rater-2"))

            invalid_score = self.valid_rating(key, "invalid-score")
            invalid_score["ratings"][0]["sides"]["A"]["scores"]["task_fidelity"] = 6

            missing_dimension = self.valid_rating(key, "missing-dimension")
            del missing_dimension["ratings"][0]["sides"]["A"]["scores"]["evidence_calibration"]

            missing_side_field = self.valid_rating(key, "missing-side-field")
            del missing_side_field["ratings"][0]["sides"]["B"]["comprehension"]

            unhashable_semantic_slot = self.valid_rating(key, "unhashable-slot")
            unhashable_semantic_slot["ratings"][0]["sides"]["A"][
                "semantic_slots_present"
            ] = [{}]

            unhashable_preference = self.valid_rating(key, "unhashable-preference")
            unhashable_preference["ratings"][0]["preference"] = {}

            unhashable_critical_label = self.valid_rating(key, "unhashable-critical-label")
            unhashable_critical_label["ratings"][0]["sides"]["A"]["critical_errors"] = [
                {"label": {}, "evidence": "bounded evidence"}
            ]

            probes = (
                (invalid_score, "must be an integer from 1 to 5"),
                (missing_dimension, "must contain exactly the seven dimensions"),
                (missing_side_field, "is missing required fields: comprehension"),
                (unhashable_semantic_slot, "must be a unique subset of required slots"),
                (unhashable_preference, "rating preference must be A, B, or tie"),
                (unhashable_critical_label, "critical error label is unsupported"),
            )
            for rating, expected_error in probes:
                with self.subTest(rater_id=rating["rater_id"]):
                    invalid_path = self.write_rating(root, copy.deepcopy(rating))
                    result = run_cli(
                        "freeze-ratings",
                        "--run-dir",
                        str(run_dir),
                        "--rating",
                        str(invalid_path),
                        "--rating",
                        str(valid_second),
                    )
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn(expected_error, result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertFalse((run_dir / "ratings").exists())
                    self.assertFalse((run_dir / "ratings-lock.json").exists())

    def test_pilot_with_favorable_ratings_remains_ineligible_for_effectiveness_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = pilot_plan()
            plan["contexts"][0]["compaction_required"] = True
            run_dir = self.prepare(root, plan=plan)
            key = self.complete_and_blind(root, run_dir)
            ratings = [
                self.write_rating(root, self.valid_rating(key, "rater-1")),
                self.write_rating(root, self.valid_rating(key, "rater-2")),
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
            self.assertGreater(report["metrics"]["primary_composite"]["difference"], 0)
            self.assertEqual(report["claim"]["status"], "insufficient_evidence")
            self.assertFalse(report["claim"]["effectiveness_claim_eligible"])
            self.assertIn("pilot", report["claim"]["missing_prerequisites"])
            self.assertIn(
                "framework-checkpoint-contract",
                report["claim"]["missing_prerequisites"],
            )
            self.assertIn(
                "framework-checkpoint-receipts",
                report["claim"]["missing_prerequisites"],
            )


if __name__ == "__main__":
    unittest.main()
