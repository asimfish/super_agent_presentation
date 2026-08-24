from __future__ import annotations

import copy
import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.presentation_benchmark import (
    BenchmarkError,
    evaluate_response,
    load_benchmark,
    markdown_images,
    validate_activation,
    validate_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "presentation_benchmark.py"
CASES = ROOT / "evals" / "presentation-cases.json"
ACTIVATION = ROOT / "skills" / "agentic-reporting" / "evals" / "activation.json"
ACTIVATION_SCHEMA = ROOT / "skills" / "agentic-reporting" / "evals" / "activation.schema.json"
FIXTURES = ROOT / "evals" / "fixtures" / "responses"


class PresentationBenchmarkTests(unittest.TestCase):
    maxDiff = None

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def case_ids(self) -> list[str]:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        return [case["id"] for case in data["cases"]]

    def test_cli_outputs_escape_terminal_controls_and_dynamic_newlines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response\x7f.md"
            response.write_text(
                (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            emitted = self.run_cli(
                "check", "--case", "image-anomaly-boundary",
                "--response", str(response), "--json",
            )
            self.assertEqual(emitted.returncode, 1, emitted.stderr)
            self.assertNotIn("\x7f", emitted.stdout)
            self.assertEqual(json.loads(emitted.stdout)["response"], str(response.resolve()))

        dynamic_error = self.run_cli(
            "check", "--case", "missing\nFAKE-SUCCESS", "--response", "unused.md"
        )
        self.assertEqual(dynamic_error.returncode, 2)
        self.assertNotIn("\nFAKE-SUCCESS", dynamic_error.stderr)
        self.assertIn(r"\nFAKE-SUCCESS", dynamic_error.stderr)

        argparse_error = self.run_cli("unknown\nFAKE-SUCCESS")
        self.assertEqual(argparse_error.returncode, 2)
        self.assertNotIn("\nFAKE-SUCCESS", argparse_error.stderr)
        self.assertIn(r"\nFAKE-SUCCESS", argparse_error.stderr)

    def test_data_files_and_schemas_are_valid_json(self) -> None:
        pairs = [
            (CASES, ROOT / "evals" / "schema" / "presentation-cases.schema.json"),
            (ACTIVATION, ACTIVATION_SCHEMA),
        ]
        for data_path, schema_path in pairs:
            with self.subTest(data_path=data_path):
                data = json.loads(data_path.read_text(encoding="utf-8"))
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(schema)
                errors = list(Draft202012Validator(schema).iter_errors(data))
                self.assertEqual(errors, [], [error.message for error in errors])

    def test_external_benchmark_artifact_root_validates_loads_and_evaluates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = root / "plot.svg"
            artifact.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            data = json.loads(CASES.read_text(encoding="utf-8"))
            case = next(item for item in data["cases"] if item["id"] == "image-anomaly-boundary")
            case["artifacts"] = ["plot.svg"]
            external_cases = root / "presentation-cases.json"
            external_cases.write_text(json.dumps(data), encoding="utf-8")

            validate_benchmark(data, artifact_root=root)
            loaded = load_benchmark(external_cases, artifact_root=root)
            self.assertEqual(loaded, data)

            response = root / "response.md"
            good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
            response.write_text(
                good.replace("../../assets/return-curve.svg", "plot.svg"),
                encoding="utf-8",
            )
            report = evaluate_response(case, response, artifact_root=root)
            image_check = next(check for check in report["checks"] if check["id"] == "show-image")
            self.assertTrue(report["passed"])
            self.assertTrue(image_check["passed"])
            self.assertIn("supplied_artifact_match=True", image_check["observed"])

    def test_external_artifact_root_rejects_unsafe_or_nonregular_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "artifacts"
            root.mkdir()
            outside = base / "outside.svg"
            outside.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            (root / "directory.svg").mkdir()
            (root / "escape.svg").symlink_to(outside)

            for name, artifact in (
                ("absolute", str(outside)),
                ("parent-traversal", "../outside.svg"),
                ("symlink-escape", "escape.svg"),
                ("nonregular", "directory.svg"),
            ):
                with self.subTest(name=name):
                    data = json.loads(CASES.read_text(encoding="utf-8"))
                    case = next(
                        item for item in data["cases"]
                        if item["id"] == "image-anomaly-boundary"
                    )
                    case["artifacts"] = [artifact]
                    with self.assertRaises(BenchmarkError):
                        validate_benchmark(data, artifact_root=root)

    def test_evaluate_response_rechecks_artifact_containment_after_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "artifacts"
            root.mkdir()
            artifact = root / "plot.svg"
            artifact.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            data = json.loads(CASES.read_text(encoding="utf-8"))
            case = next(item for item in data["cases"] if item["id"] == "image-anomaly-boundary")
            case["artifacts"] = ["plot.svg"]
            validate_benchmark(data, artifact_root=root)

            response = root / "response.md"
            good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
            response.write_text(
                good.replace("../../assets/return-curve.svg", "plot.svg"),
                encoding="utf-8",
            )
            outside = base / "outside.svg"
            outside.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            artifact.unlink()
            artifact.symlink_to(outside)

            with self.assertRaisesRegex(BenchmarkError, "escapes the artifact root"):
                evaluate_response(case, response, artifact_root=root)

    def test_benchmark_json_number_literals_are_bounded_before_conversion(self) -> None:
        probe = """
import pathlib
import runpy
import sys

namespace = runpy.run_path(sys.argv[1], run_name="benchmark_json_number_probe")
try:
    namespace["_read_json"](pathlib.Path(sys.argv[2]))
except Exception as exc:
    print(type(exc).__name__ + ": " + str(exc))
    raise SystemExit(0)
raise SystemExit(1)
"""
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "oversized-number.json"
            source.write_text(
                '{"schema_version":' + ("9" * 400_000) + "}",
                encoding="utf-8",
            )
            try:
                result = subprocess.run(
                    [sys.executable, "-c", probe, str(SCRIPT), str(source)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=5,
                )
            except subprocess.TimeoutExpired as exc:
                self.fail(f"benchmark integer conversion exceeded the 5-second ceiling: {exc}")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("integer literal exceeds 128 characters", result.stdout)
            self.assertLess(len(result.stdout), 512)

    def test_runtime_and_draft_schemas_reject_same_shape_mutations(self) -> None:
        activation = json.loads(ACTIVATION.read_text(encoding="utf-8"))
        activation_schema = json.loads(
            ACTIVATION_SCHEMA.read_text(encoding="utf-8")
        )
        presentation = json.loads(CASES.read_text(encoding="utf-8"))
        presentation_schema = json.loads(
            (ROOT / "evals" / "schema" / "presentation-cases.schema.json").read_text(encoding="utf-8")
        )

        activation_mutations = []
        missing_description = copy.deepcopy(activation)
        del missing_description["description"]
        activation_mutations.append(missing_description)
        invalid_activation_schema_locator = copy.deepcopy(activation)
        invalid_activation_schema_locator["$schema"] = 1
        activation_mutations.append(invalid_activation_schema_locator)
        unknown_activation_field = copy.deepcopy(activation)
        unknown_activation_field["cases"][0]["unexpected"] = True
        activation_mutations.append(unknown_activation_field)
        invalid_activation_id = copy.deepcopy(activation)
        invalid_activation_id["cases"][0]["id"] = "Bad_ID"
        activation_mutations.append(invalid_activation_id)
        missing_category = copy.deepcopy(activation)
        missing_category["cases"][0]["category"] = "natural_positive"
        activation_mutations.append(missing_category)
        positive_without_route = copy.deepcopy(activation)
        positive_without_route["cases"][0]["expected_route"] = None
        activation_mutations.append(positive_without_route)
        negative_with_route = copy.deepcopy(activation)
        negative_with_route["cases"][-1]["expected_route"] = {
            "mode": "implementation-handoff",
            "modules": ["evidence"],
        }
        activation_mutations.append(negative_with_route)
        missing_rubric_coverage = copy.deepcopy(activation)
        for case in missing_rubric_coverage["cases"]:
            case["rubric_categories"] = [
                rubric for rubric in case["rubric_categories"] if rubric != "effectiveness"
            ]
        activation_mutations.append(missing_rubric_coverage)
        for payload in activation_mutations:
            with self.subTest(kind="activation"):
                self.assertTrue(list(Draft202012Validator(activation_schema).iter_errors(payload)))
                with self.assertRaises(BenchmarkError):
                    validate_activation(payload)

        presentation_mutations = []
        unknown_case_field = copy.deepcopy(presentation)
        unknown_case_field["cases"][0]["unexpected"] = True
        presentation_mutations.append(unknown_case_field)
        invalid_presentation_schema_locator = copy.deepcopy(presentation)
        invalid_presentation_schema_locator["$schema"] = 1
        presentation_mutations.append(invalid_presentation_schema_locator)
        regex_without_pattern = copy.deepcopy(presentation)
        regex_case = next(
            case for case in regex_without_pattern["cases"]
            if any(check["type"] == "required_regex" for check in case["machine_checks"])
        )
        regex_check = next(check for check in regex_case["machine_checks"] if check["type"] == "required_regex")
        del regex_check["pattern"]
        presentation_mutations.append(regex_without_pattern)
        numeric_without_value = copy.deepcopy(presentation)
        numeric_case = next(
            case for case in numeric_without_value["cases"]
            if any(check["type"] == "max_words" for check in case["machine_checks"])
        )
        numeric_check = next(check for check in numeric_case["machine_checks"] if check["type"] == "max_words")
        del numeric_check["value"]
        presentation_mutations.append(numeric_without_value)
        irrelevant_field_wrong_type = copy.deepcopy(presentation)
        regex_case = next(
            case for case in irrelevant_field_wrong_type["cases"]
            if any(check["type"] == "required_regex" for check in case["machine_checks"])
        )
        regex_check = next(check for check in regex_case["machine_checks"] if check["type"] == "required_regex")
        regex_check["value"] = "not-an-integer"
        presentation_mutations.append(irrelevant_field_wrong_type)
        for payload in presentation_mutations:
            with self.subTest(kind="presentation"):
                self.assertTrue(list(Draft202012Validator(presentation_schema).iter_errors(payload)))
                with self.assertRaises(BenchmarkError):
                    validate_benchmark(payload)

    def test_activation_contract_covers_categories_and_rubrics(self) -> None:
        data = json.loads(ACTIVATION.read_text(encoding="utf-8"))
        self.assertEqual(
            {case["category"] for case in data["cases"]},
            {"explicit_positive", "natural_positive", "adjacent_negative", "explicit_exclusion"},
        )
        self.assertEqual(
            set().union(*(set(case["rubric_categories"]) for case in data["cases"])),
            {"security", "correctness", "discoverability", "effectiveness", "efficiency"},
        )
        for case in data["cases"]:
            expected = case["category"] in {"explicit_positive", "natural_positive"}
            self.assertIs(case["expected_activation"], expected)
            self.assertEqual(case["expected_route"] is not None, expected)
        self.assertEqual(len({case["id"] for case in data["cases"]}), len(data["cases"]))
        long_start = next(
            case for case in data["cases"] if case["id"] == "activate-natural-long-task-start"
        )
        self.assertIn("task-start", long_start["tags"])
        self.assertTrue(any("checkpoint" in item for item in long_start["expected_behavior"]))
        vla_idea = next(
            case for case in data["cases"]
            if case["id"] == "activate-natural-vla-research-idea"
        )
        self.assertEqual(vla_idea["expected_route"]["profile"], "vla")

    def test_list_exposes_all_seven_scenarios_without_checks(self) -> None:
        completed = self.run_cli("list", "--suite", "harness-smoke", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(len(payload["cases"]), 7)
        self.assertEqual(
            {item["scenario"] for item in payload["cases"]},
            {
                "short_answer",
                "long_engineering",
                "experiment_analysis",
                "image_presentation",
                "multi_table",
                "academic_paper_summary",
                "failure_risk",
            },
        )
        self.assertTrue(all("machine_checks" not in item for item in payload["cases"]))

    def test_prompt_is_condition_neutral_and_hides_oracles(self) -> None:
        completed = self.run_cli("prompt", "image-anomaly-boundary")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Supplied facts:", completed.stdout)
        self.assertIn("evals/fixtures/assets/return-curve.svg", completed.stdout)
        self.assertIn("Evidence boundary:", completed.stdout)
        self.assertNotIn("machine_checks", completed.stdout)
        self.assertNotIn("required_semantic_slots", completed.stdout)
        self.assertNotIn("visual_oracle", completed.stdout)
        self.assertNotIn("required_image", completed.stdout)

    def test_every_known_good_fixture_passes(self) -> None:
        for case_id in self.case_ids():
            with self.subTest(case_id=case_id):
                response = FIXTURES / "good" / f"{case_id}.md"
                completed = self.run_cli(
                    "check", "--case", case_id, "--response", str(response), "--json"
                )
                self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
                report = json.loads(completed.stdout)
                self.assertTrue(report["passed"])
                self.assertEqual(report["checks_passed"], report["checks_total"])
                self.assertIn("do not establish factual truth", report["semantic_limit"])

    def test_every_mutated_bad_fixture_is_rejected(self) -> None:
        for case_id in self.case_ids():
            with self.subTest(case_id=case_id):
                response = FIXTURES / "bad" / f"{case_id}.md"
                completed = self.run_cli(
                    "check", "--case", case_id, "--response", str(response), "--json"
                )
                self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                report = json.loads(completed.stdout)
                self.assertFalse(report["passed"])
                self.assertTrue(any(not check["passed"] for check in report["checks"]))

    def test_smoke_checks_both_fixture_polarities_and_disclaims_effectiveness(self) -> None:
        completed = self.run_cli("smoke", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        report = json.loads(completed.stdout)
        self.assertTrue(report["harness_pass"])
        self.assertEqual(report["fixture_evaluations"], 14)
        self.assertEqual(report["expectations_met"], 14)
        self.assertTrue(report["activation_contract_valid"])
        self.assertEqual(report["activation_case_count"], 9)
        self.assertEqual(report["positive_route_proxy_expectations"], 6)
        self.assertEqual(report["positive_route_proxy_expectations_met"], 6)
        self.assertFalse(report["host_activation_observed"])
        self.assertFalse(report["activation_effectiveness_claim"])
        self.assertFalse(report["effectiveness_claim"])
        self.assertIn("no real model was run", report["disclaimer"])

    def test_required_image_check_rejects_broken_target_and_empty_alt(self) -> None:
        response = FIXTURES / "bad" / "image-anomaly-boundary.md"
        completed = self.run_cli(
            "check", "--case", "image-anomaly-boundary", "--response", str(response), "--json"
        )
        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        image_check = next(check for check in report["checks"] if check["id"] == "show-image")
        self.assertFalse(image_check["passed"])
        self.assertIn("alt_text=False", image_check["observed"])
        self.assertIn("local_targets_exist=False", image_check["observed"])

    def test_required_image_check_handles_malformed_and_remote_targets_without_traceback(self) -> None:
        for target in ("%00.png", "//[", "HTTPS://example.com/plot.png"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temporary:
                response = Path(temporary) / "response.md"
                response.write_text(
                    f"![Plot]({target})\n\nFigure 1. The plot cannot establish a cause.\n",
                    encoding="utf-8",
                )
                completed = self.run_cli(
                    "check", "--case", "image-anomaly-boundary", "--response", str(response), "--json"
                )
                self.assertEqual(completed.returncode, 1)
                self.assertNotIn("Traceback", completed.stderr)
                report = json.loads(completed.stdout)
                image_check = next(check for check in report["checks"] if check["id"] == "show-image")
                self.assertFalse(image_check["passed"])
                self.assertIn("local_targets_exist=False", image_check["observed"])

    def test_required_image_check_handles_symlink_loop_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "loop").symlink_to("loop")
            response = root / "response.md"
            response.write_text(
                "![Plot](loop/x.png)\n\nFigure 1. The plot cannot establish a cause.\n",
                encoding="utf-8",
            )
            completed = self.run_cli(
                "check", "--case", "image-anomaly-boundary", "--response", str(response), "--json"
            )
            self.assertEqual(completed.returncode, 1)
            self.assertNotIn("Traceback", completed.stderr)
            report = json.loads(completed.stdout)
            image_check = next(check for check in report["checks"] if check["id"] == "show-image")
            self.assertFalse(image_check["passed"])
            self.assertIn("local_targets_exist=False", image_check["observed"])

    def test_required_image_decodes_local_target_character_references_once(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            response = root / "response.md"
            decoded_name = root / "plot&.svg"
            decoded_name.symlink_to(supplied)
            response.write_text(
                f"![Return curve](plot&amp;.svg)\n\n{narrative}",
                encoding="utf-8",
            )

            decoded_target = self.run_cli(
                "check", "--case", "image-anomaly-boundary",
                "--response", str(response), "--json",
            )
            self.assertEqual(decoded_target.returncode, 0, decoded_target.stderr or decoded_target.stdout)
            decoded_report = json.loads(decoded_target.stdout)
            decoded_check = next(
                check for check in decoded_report["checks"] if check["id"] == "show-image"
            )
            self.assertTrue(decoded_check["passed"])
            self.assertIn("local_targets_exist=True", decoded_check["observed"])
            self.assertIn("supplied_artifact_match=True", decoded_check["observed"])

            decoded_name.unlink()
            (root / "plot&amp;.svg").symlink_to(supplied)
            literal_entity_only = self.run_cli(
                "check", "--case", "image-anomaly-boundary",
                "--response", str(response), "--json",
            )
            self.assertEqual(
                literal_entity_only.returncode,
                1,
                literal_entity_only.stderr or literal_entity_only.stdout,
            )
            literal_report = json.loads(literal_entity_only.stdout)
            literal_check = next(
                check for check in literal_report["checks"] if check["id"] == "show-image"
            )
            self.assertFalse(literal_check["passed"])
            self.assertIn("local_targets_exist=False", literal_check["observed"])
            self.assertIn("supplied_artifact_match=False", literal_check["observed"])

    def test_required_image_does_not_decode_non_commonmark_target_entity_forms(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        cases = {
            "missing-semicolon-named": ("&copy.svg", "&copy.svg", "©.svg"),
            "missing-semicolon-amp-prefix": ("&ampb", "&ampb", "&b"),
            "missing-semicolon-decimal": ("&#38b", "&", "&b"),
            "missing-semicolon-hex": ("&#x26b", "&", "ɫ"),
            "invalid-named-reference": ("&notit;", "&notit;", "¬it;"),
            "overlong-decimal-reference": ("&#000000065;", "&", "A"),
            "overlong-hex-reference": ("&#x0000041;", "&", "A"),
        }
        for name, (target, literal_path, permissive_decoded_path) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                response = root / "response.md"
                literal = root / literal_path
                literal.symlink_to(supplied)
                response.write_text(
                    f"![Return curve]({target})\n\n{narrative}",
                    encoding="utf-8",
                )

                literal_result = self.run_cli(
                    "check", "--case", "image-anomaly-boundary",
                    "--response", str(response), "--json",
                )
                self.assertEqual(
                    literal_result.returncode,
                    0,
                    literal_result.stderr or literal_result.stdout,
                )
                literal_report = json.loads(literal_result.stdout)
                literal_check = next(
                    check for check in literal_report["checks"] if check["id"] == "show-image"
                )
                self.assertTrue(literal_check["passed"])
                self.assertIn("supplied_artifact_match=True", literal_check["observed"])

                literal.unlink()
                (root / permissive_decoded_path).symlink_to(supplied)
                decoded_only_result = self.run_cli(
                    "check", "--case", "image-anomaly-boundary",
                    "--response", str(response), "--json",
                )
                self.assertEqual(
                    decoded_only_result.returncode,
                    1,
                    decoded_only_result.stderr or decoded_only_result.stdout,
                )
                decoded_only_report = json.loads(decoded_only_result.stdout)
                decoded_only_check = next(
                    check
                    for check in decoded_only_report["checks"]
                    if check["id"] == "show-image"
                )
                self.assertFalse(decoded_only_check["passed"])
                self.assertIn("local_targets_exist=False", decoded_only_check["observed"])
                self.assertIn("supplied_artifact_match=False", decoded_only_check["observed"])

    def test_required_image_uses_scalar_numeric_entities_without_legacy_remap_or_drop(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        legacy_paths = {
            "deleted-del": ("plot&#127;.svg", "plot.svg"),
            "remapped-euro": ("plot&#128;.svg", "plot€.svg"),
            "remapped-ellipsis": ("plot&#133;.svg", "plot….svg"),
            "deleted-max-scalar": ("plot&#x10FFFF;.svg", "plot.svg"),
        }
        for name, (target, legacy_path) in legacy_paths.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / legacy_path).symlink_to(supplied)
                response = root / "response.md"
                response.write_text(
                    f"![Return curve]({target})\n\n{narrative}",
                    encoding="utf-8",
                )
                completed = self.run_cli(
                    "check", "--case", "image-anomaly-boundary",
                    "--response", str(response), "--json",
                )
                self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                report = json.loads(completed.stdout)
                image_check = next(
                    check for check in report["checks"] if check["id"] == "show-image"
                )
                self.assertFalse(image_check["passed"])
                self.assertIn("local_targets_exist=False", image_check["observed"])
                self.assertIn("supplied_artifact_match=False", image_check["observed"])

    def test_required_image_maps_invalid_numeric_scalars_to_exact_replacement_path(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        targets = (
            "plot&#0;.svg",
            "plot&#xD800;.svg",
            "plot&#x110000;.svg",
        )
        for target in targets:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / "plot�.svg").symlink_to(supplied)
                response = root / "response.md"
                response.write_text(
                    f"![Return curve]({target})\n\n{narrative}",
                    encoding="utf-8",
                )
                completed = self.run_cli(
                    "check", "--case", "image-anomaly-boundary",
                    "--response", str(response), "--json",
                )
                self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
                report = json.loads(completed.stdout)
                image_check = next(
                    check for check in report["checks"] if check["id"] == "show-image"
                )
                self.assertTrue(image_check["passed"])
                self.assertIn("local_targets_exist=True", image_check["observed"])
                self.assertIn("supplied_artifact_match=True", image_check["observed"])

    def test_required_image_rejects_entity_escapes_for_target_delimiters(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        cases = {
            "decoded-space": ("plot&#32;one.svg", "plot one.svg"),
            "decoded-parenthesis": ("plot&#40;one.svg", "plot(one.svg"),
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            response = root / "response.md"
            for name, (target, decoded_path) in cases.items():
                with self.subTest(name=name):
                    (root / decoded_path).symlink_to(supplied)
                    response.write_text(
                        f"![Return curve]({target})\n\n{narrative}",
                        encoding="utf-8",
                    )
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("local_targets_exist=False", image_check["observed"])
                    self.assertIn("supplied_artifact_match=False", image_check["observed"])

    def test_required_image_decodes_and_validates_alt_text_character_references(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for alt in ("&Tab;", "&nbsp;", "&#9;", "&NewLine;"):
                with self.subTest(kind="empty", alt=alt):
                    response.write_text(
                        f"![{alt}]({supplied})\n\n{narrative}",
                        encoding="utf-8",
                    )
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("alt_text=False", image_check["observed"])

            response.write_text(
                f"![&#x202E;]({supplied})\n\n{narrative}",
                encoding="utf-8",
            )
            unsafe = self.run_cli(
                "check", "--case", "image-anomaly-boundary",
                "--response", str(response), "--json",
            )
            self.assertEqual(unsafe.returncode, 1, unsafe.stderr or unsafe.stdout)
            unsafe_report = json.loads(unsafe.stdout)
            unsafe_check = next(
                check for check in unsafe_report["checks"] if check["id"] == "show-image"
            )
            self.assertFalse(unsafe_check["passed"])
            self.assertIn("alt_text=False", unsafe_check["observed"])

            response.write_text(
                f"![&copy;]({supplied})\n\n{narrative}",
                encoding="utf-8",
            )
            visible = self.run_cli(
                "check", "--case", "image-anomaly-boundary",
                "--response", str(response), "--json",
            )
            self.assertEqual(visible.returncode, 0, visible.stderr or visible.stdout)
            visible_report = json.loads(visible.stdout)
            visible_check = next(
                check for check in visible_report["checks"] if check["id"] == "show-image"
            )
            self.assertTrue(visible_check["passed"])
            self.assertIn("alt_text=True", visible_check["observed"])

    def test_required_image_rejects_angle_delimited_target_even_if_literal_file_exists(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "<plot.svg>").symlink_to(supplied)
            response = root / "response.md"
            response.write_text(
                f"![Return curve](<plot.svg>)\n\n{narrative}",
                encoding="utf-8",
            )
            completed = self.run_cli(
                "check", "--case", "image-anomaly-boundary",
                "--response", str(response), "--json",
            )
            self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
            report = json.loads(completed.stdout)
            image_check = next(check for check in report["checks"] if check["id"] == "show-image")
            self.assertFalse(image_check["passed"])
            self.assertIn("0 images", image_check["observed"])
            self.assertIn("noncanonical_candidates=1", image_check["observed"])

    def test_required_image_rejects_directories_and_unsupported_file_suffixes(self) -> None:
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "plot.svg").mkdir()
            (root / "note.txt").write_text("not an image", encoding="utf-8")
            response = root / "response.md"
            for target in ("plot.svg", "note.txt"):
                with self.subTest(target=target):
                    response.write_text(
                        f"![Return curve]({target})\n\n{narrative}",
                        encoding="utf-8",
                    )
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("local_targets_exist=False", image_check["observed"])

    def test_required_image_rejects_nonportable_control_title_delimiters(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        controls = ("\x0b", "\x0c", "\u2028", "\u2029")
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for control in controls:
                for target in (
                    f"{supplied}{control}\"title\"",
                    f"{supplied}#{control} \"title\"",
                ):
                    with self.subTest(codepoint=f"U+{ord(control):04X}", target=target):
                        response.write_text(
                            f"![Return curve]({target})\n\n"
                            "Figure 1. The mean return rises through step 80 and drops at step 90. "
                            "The band is one standard deviation over five seeds, and the plot cannot "
                            "identify the cause.\n",
                            encoding="utf-8",
                        )
                        completed = self.run_cli(
                            "check", "--case", "image-anomaly-boundary",
                            "--response", str(response), "--json",
                        )
                        self.assertEqual(completed.returncode, 1)
                        self.assertNotIn("Traceback", completed.stderr)
                        report = json.loads(completed.stdout)
                        image_check = next(
                            check for check in report["checks"] if check["id"] == "show-image"
                        )
                        self.assertFalse(image_check["passed"])
                        self.assertIn("local_targets_exist=False", image_check["observed"])

    def test_benchmark_malformed_image_scan_completes_within_wide_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            response.write_text("![" * 32_768, encoding="utf-8")
            try:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "check",
                        "--case",
                        "image-anomaly-boundary",
                        "--response",
                        str(response),
                        "--json",
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=5,
                )
            except subprocess.TimeoutExpired as exc:
                self.fail(f"benchmark image scan exceeded the 5-second regression ceiling: {exc}")
            self.assertEqual(completed.returncode, 1)
            self.assertNotIn("Traceback", completed.stderr)
            json.loads(completed.stdout)

    def test_benchmark_caps_image_count_amplification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            response.write_text("![](missing.png)\n" * 40_000, encoding="utf-8")
            try:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "check",
                        "--case",
                        "image-anomaly-boundary",
                        "--response",
                        str(response),
                        "--json",
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=5,
                )
            except subprocess.TimeoutExpired as exc:
                self.fail(f"benchmark image-count workload exceeded the 5-second ceiling: {exc}")
            self.assertEqual(completed.returncode, 1)
            report = json.loads(completed.stdout)
            self.assertEqual(report["image_count"], 1_000)
            self.assertTrue(report["image_scan_truncated"])
            image_check = next(check for check in report["checks"] if check["id"] == "show-image")
            self.assertIn("image_scan_truncated=True", image_check["observed"])

    def test_capped_image_candidates_keep_source_order_across_scanners(self) -> None:
        text = ("<div>\n" * 1_001) + "\n![plot](artifact.png)\n"
        reportctl = runpy.run_path(
            str(ROOT / "skills" / "agentic-reporting" / "scripts" / "reportctl.py"),
            run_name="reportctl_cap_order_test",
        )
        audit_records = reportctl["_scan_markdown_images"](text)
        audit_projection = [
            (alt, target, canonical)
            for alt, target, _, _, canonical in audit_records
        ]
        benchmark_records = markdown_images(text)

        self.assertEqual(len(audit_projection), 1_001)
        self.assertEqual(benchmark_records, audit_projection)
        self.assertFalse(any(canonical for _, _, canonical in benchmark_records))

    def test_required_image_ignores_html_comments_and_requires_supplied_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            response.write_text(
                "<!-- ![Not rendered](/etc/hosts) -->\n\n"
                "Figure 1. The mean return rises through step 80 and drops at step 90. "
                "The band is one standard deviation over five seeds, and the plot cannot "
                "identify the cause.\n",
                encoding="utf-8",
            )
            completed = self.run_cli(
                "check", "--case", "image-anomaly-boundary", "--response", str(response), "--json"
            )
            report = json.loads(completed.stdout)
            image_check = next(check for check in report["checks"] if check["id"] == "show-image")
            self.assertFalse(image_check["passed"])
            self.assertIn("0 images", image_check["observed"])
            self.assertIn("noncanonical_candidates=1", image_check["observed"])
            self.assertEqual(report["image_count"], 1)

            wrong_image = Path(temporary) / "wrong.svg"
            wrong_image.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>", encoding="utf-8")
            response.write_text(
                "![Wrong but existing figure](wrong.svg)\n\n"
                "Figure 1. The mean return rises through step 80 and drops at step 90. "
                "The band is one standard deviation over five seeds, and the plot cannot "
                "identify the cause.\n",
                encoding="utf-8",
            )
            completed = self.run_cli(
                "check", "--case", "image-anomaly-boundary", "--response", str(response), "--json"
            )
            report = json.loads(completed.stdout)
            image_check = next(check for check in report["checks"] if check["id"] == "show-image")
            self.assertFalse(image_check["passed"])
            self.assertIn("local_targets_exist=True", image_check["observed"])
            self.assertIn("supplied_artifact_match=False", image_check["observed"])

    def test_required_image_never_credits_nonrendered_markdown_literals(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        literal = f"![Return curve]({supplied})"
        nonrendered_contexts = {
            "inline-code": f"`{literal}`",
            "fenced-code": f"```markdown\n{literal}\n```",
            "html-comment": f"<!--\n{literal}\n-->",
            "raw-script-block": f"<script>\n{literal}\n</script>",
            "processing-instruction": f"<?report\n{literal}\n?>",
            "declaration": f"<!REPORT\n{literal}\n>",
            "cdata": f"<![CDATA[\n{literal}\n]]>",
            "block-tag": f"<div>\n{literal}",
            "type-7-tag-with-quoted-angle": f'<span title=">">\n{literal}',
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for context, prefix in nonrendered_contexts.items():
                with self.subTest(context=context):
                    response.write_text(f"{prefix}\n\n{narrative}", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    self.assertRegex(
                        image_check["observed"],
                        r"noncanonical_candidates=[1-9][0-9]*",
                    )
                    self.assertGreaterEqual(report["image_count"], 1)

    def test_required_image_accepts_only_top_level_single_line_canonical_syntax(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        top_level_image = f"![Return curve]({supplied})"
        canonical_images = {
            "document-start": top_level_image,
            "blank-line-bounded": f"Context paragraph.\n\n{top_level_image}",
        }
        noncanonical_images = {
            "three-space-indent": f"   {top_level_image}",
            "indented-code": f"    {top_level_image}",
            "mixed-trailing-prose": f"{top_level_image} trailing prose",
            "preceding-line-without-blank": f"Context paragraph.\n{top_level_image}",
            "following-line-without-blank": f"{top_level_image}\nFollowing prose.",
            "setext-following-line": f"{top_level_image}\n---",
            "list-item": f"- {top_level_image}",
            "list-continuation": f"- item\n\n    {top_level_image}",
            "list-lazy-continuation": f"- item\n{top_level_image}",
            "blockquote": f"> {top_level_image}",
            "blockquote-lazy-continuation": f"> quoted\n{top_level_image}",
            "nested-alt": f"![Outer ![Return curve]({supplied})]({supplied})",
            "parenthesized-target": f"![Return curve]({supplied.parent}/return-(curve).svg)",
            "backslash-target": f"![Return curve]({supplied}\\alias)",
            "multiline-alt": f"![Return\ncurve]({supplied})",
            "multiline-title": f'![Return curve]({supplied}\n "training curve")',
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for syntax, image in canonical_images.items():
                with self.subTest(kind="canonical", syntax=syntax):
                    response.write_text(f"{image}\n\n{narrative}", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertTrue(image_check["passed"])
                    self.assertIn("1 images", image_check["observed"])
                    self.assertIn("noncanonical_candidates=0", image_check["observed"])

            for syntax, image in noncanonical_images.items():
                with self.subTest(kind="noncanonical", syntax=syntax):
                    response.write_text(f"{image}\n\n{narrative}", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    if syntax == "nested-alt":
                        self.assertRegex(
                            image_check["observed"],
                            r"noncanonical_candidates=[1-9][0-9]*",
                        )
                        self.assertGreaterEqual(report["image_count"], 1)
                    else:
                        self.assertIn("noncanonical_candidates=1", image_check["observed"])
                        self.assertEqual(report["image_count"], 1)

    def test_required_image_alt_backticks_require_odd_backslash_escaping(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            response.write_text(
                rf"![Plot \`code\` result]({supplied})" + f"\n\n{narrative}",
                encoding="utf-8",
            )
            escaped = self.run_cli(
                "check", "--case", "image-anomaly-boundary",
                "--response", str(response), "--json",
            )
            self.assertEqual(escaped.returncode, 0, escaped.stderr or escaped.stdout)
            escaped_report = json.loads(escaped.stdout)
            escaped_check = next(
                check for check in escaped_report["checks"] if check["id"] == "show-image"
            )
            self.assertTrue(escaped_check["passed"])
            self.assertIn("noncanonical_candidates=0", escaped_check["observed"])

            invalid_alts = {
                "unescaped": "Plot `code` result",
                "even-backslashes": r"Plot \\`code\\` result",
            }
            for name, alt in invalid_alts.items():
                with self.subTest(name=name):
                    response.write_text(
                        f"![{alt}]({supplied})\n\n{narrative}",
                        encoding="utf-8",
                    )
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    self.assertIn("noncanonical_candidates=1", image_check["observed"])
                    self.assertEqual(report["image_count"], 1)

    def test_forbidden_image_fails_closed_on_noncanonical_image_candidates(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        top_level_image = f"![Return curve]({supplied})"
        noncanonical_images = {
            "three-space-indent": f"   {top_level_image}",
            "indented-code": f"    {top_level_image}",
            "mixed-trailing-prose": f"{top_level_image} trailing prose",
            "preceding-line-without-blank": f"Context paragraph.\n{top_level_image}",
            "following-line-without-blank": f"{top_level_image}\nFollowing prose.",
            "setext-following-line": f"{top_level_image}\n---",
            "list-item": f"- {top_level_image}",
            "list-continuation": f"- item\n\n    {top_level_image}",
            "list-lazy-continuation": f"- item\n{top_level_image}",
            "blockquote": f"> {top_level_image}",
            "blockquote-lazy-continuation": f"> quoted\n{top_level_image}",
            "nested-alt": f"![Outer ![Return curve]({supplied})]({supplied})",
            "parenthesized-target": f"![Return curve]({supplied.parent}/return-(curve).svg)",
            "backslash-target": f"![Return curve]({supplied}\\alias)",
            "multiline-alt": f"![Return\ncurve]({supplied})",
            "multiline-title": f'![Return curve]({supplied}\n "training curve")',
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for syntax, image in noncanonical_images.items():
                with self.subTest(syntax=syntax):
                    response.write_text(f"{status}\n\n{image}\n", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "short-direct-status",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "no-image"
                    )
                    self.assertFalse(image_check["passed"])
                    if syntax == "nested-alt":
                        self.assertRegex(
                            image_check["observed"],
                            r"^[1-9][0-9]* images \(maximum 0\)$",
                        )
                        self.assertGreaterEqual(report["image_count"], 1)
                    else:
                        self.assertEqual(image_check["observed"], "1 images (maximum 0)")
                        self.assertEqual(report["image_count"], 1)

    def test_html_block_blank_line_restores_only_unambiguous_image_credit(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        hidden = f"![Hidden curve]({supplied})"
        visible = f"![Return curve]({supplied})"
        html_blocks = {
            "block-tag": f"<div>\n{hidden}",
            "type-7-tag-with-quoted-angle": f'<span title=">">\n{hidden}',
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for block, prefix in html_blocks.items():
                with self.subTest(block=block):
                    response.write_text(
                        f"{prefix}\n\n{visible}\n\n{narrative}",
                        encoding="utf-8",
                    )
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    if block == "block-tag":
                        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
                        self.assertTrue(image_check["passed"])
                        self.assertIn("1 images", image_check["observed"])
                    else:
                        self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                        self.assertFalse(image_check["passed"])
                        self.assertIn("0 images", image_check["observed"])
                    expected_noncanonical = 2 if block == "block-tag" else 3
                    self.assertIn(
                        f"noncanonical_candidates={expected_noncanonical}",
                        image_check["observed"],
                    )
                    self.assertEqual(report["image_count"], 3)

    def test_type_7_tag_cannot_hide_an_image_by_interrupting_a_paragraph(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        image = f"![Return curve]({supplied})"
        paragraph_interruptions = {
            "opening-tag": f"Paragraph text.\n<span>\n{image}",
            "closing-tag": f"Paragraph text.\n</span>\n{image}",
            "list-paragraph": f"- Paragraph text.\n  <span>\n  {image}",
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for syntax, prefix in paragraph_interruptions.items():
                with self.subTest(syntax=syntax):
                    response.write_text(f"{prefix}\n\n{narrative}", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    expected_candidates = 1 if syntax == "closing-tag" else 2
                    self.assertIn(
                        f"noncanonical_candidates={expected_candidates}",
                        image_check["observed"],
                    )
                    self.assertEqual(report["image_count"], expected_candidates)

    def test_forbidden_image_fails_when_type_7_tag_interrupts_a_paragraph(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        image = f"![Return curve]({supplied})"
        paragraph_interruptions = {
            "opening-tag": f"Paragraph text.\n<span>\n{image}",
            "closing-tag": f"Paragraph text.\n</span>\n{image}",
            "list-paragraph": f"- Paragraph text.\n  <span>\n  {image}",
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for syntax, candidate in paragraph_interruptions.items():
                with self.subTest(syntax=syntax):
                    response.write_text(f"{status}\n\n{candidate}\n", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "short-direct-status",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "no-image"
                    )
                    self.assertFalse(image_check["passed"])
                    expected_candidates = 1 if syntax == "closing-tag" else 2
                    self.assertEqual(
                        image_check["observed"],
                        f"{expected_candidates} images (maximum 0)",
                    )
                    self.assertEqual(report["image_count"], expected_candidates)

    def test_type_7_html_block_marker_never_receives_required_image_credit(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        image = f"![Return curve]({supplied})"
        html_blocks = {
            "opening-tag": f"Paragraph text.\n\n<span>\n{image}",
            "closing-tag": f"Paragraph text.\n\n</span>\n{image}",
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for syntax, block in html_blocks.items():
                with self.subTest(syntax=syntax):
                    response.write_text(f"{block}\n\n{narrative}", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    expected_candidates = 2 if syntax == "opening-tag" else 1
                    self.assertIn(
                        f"noncanonical_candidates={expected_candidates}",
                        image_check["observed"],
                    )
                    self.assertEqual(report["image_count"], expected_candidates)

    def test_pre_image_fence_or_type7_syntax_uses_conservative_credit(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        visible = f"![Return curve]({supplied})"
        prefixes = {
            "inline-code-comment-opener": "`<!--`",
            "fence-comment-opener": "```\n<!--\n```",
            "escaped-comment-opener": r"\<!--",
            "html-block-fence": "<div>\n```",
            "type-seven-block-fence": "<span>\n```",
            "comment-block-fence": "<!--\n```\n-->",
            "script-block-fence": "<script>\n```\n</script>",
            "type-seven-quoted-comment-opener": '<span title="<!--">',
            "inline-tag-quoted-comment-opener": 'text <span title="<!--">',
        }
        raw_opening_contexts = {
            "html-block-fence",
            "type-seven-block-fence",
            "script-block-fence",
            "type-seven-quoted-comment-opener",
            "inline-tag-quoted-comment-opener",
        }
        conservative = {
            "fence-comment-opener",
            "html-block-fence",
            "type-seven-block-fence",
            "comment-block-fence",
            "script-block-fence",
            "type-seven-quoted-comment-opener",
            "inline-tag-quoted-comment-opener",
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for context, prefix in prefixes.items():
                with self.subTest(context=context):
                    response.write_text(
                        f"{prefix}\n\n{visible}\n\n{narrative}",
                        encoding="utf-8",
                    )
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    if context in conservative:
                        self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                        self.assertFalse(image_check["passed"])
                        self.assertIn("0 images", image_check["observed"])
                        self.assertRegex(
                            image_check["observed"],
                            r"noncanonical_candidates=[1-9][0-9]*",
                        )
                    else:
                        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
                        self.assertTrue(image_check["passed"])
                        self.assertIn("1 images", image_check["observed"])
                        expected_noncanonical = int(context in raw_opening_contexts)
                        self.assertIn(
                            f"noncanonical_candidates={expected_noncanonical}",
                            image_check["observed"],
                        )

    def test_commonmark_html_terminators_restore_required_image_credit(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        image = f"![Return curve]({supplied})"
        prefixes = {
            "overlapping-comment-close": "<!-->",
            "overlapping-comment-dash-close": "<!--->",
            "overlapping-processing-instruction-close": "<?>",
            "raw-tag-family-close": "<script>\n</style>",
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for terminator, prefix in prefixes.items():
                with self.subTest(terminator=terminator):
                    response.write_text(
                        f"{prefix}\n\n{image}\n\n{narrative}",
                        encoding="utf-8",
                    )
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertTrue(image_check["passed"])
                    self.assertIn("1 images", image_check["observed"])
                    expected_noncanonical = int(terminator == "raw-tag-family-close")
                    self.assertIn(
                        f"noncanonical_candidates={expected_noncanonical}",
                        image_check["observed"],
                    )
                    self.assertEqual(report["image_count"], 1 + expected_noncanonical)

    def test_isolated_type1_closing_tags_do_not_consume_an_unclosed_fence(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for tag in ("pre", "script", "style", "textarea"):
                with self.subTest(tag=tag):
                    response.write_text(
                        f"text\n</{tag}>\n```\n\n"
                        f"![Return curve]({supplied})\n\n{narrative}",
                        encoding="utf-8",
                    )
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    self.assertIn("noncanonical_candidates=1", image_check["observed"])
                    self.assertEqual(report["image_count"], 1)

    def test_type1_openings_still_end_on_any_type1_closing_tag(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        tag_pairs = {
            "pre": "script",
            "script": "style",
            "style": "textarea",
            "textarea": "pre",
        }
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for opening, closing in tag_pairs.items():
                with self.subTest(opening=opening, closing=closing):
                    response.write_text(
                        f"<{opening}>\n![Hidden curve](missing.svg)\n</{closing}>\n\n"
                        f"![Return curve]({supplied})\n\n{narrative}",
                        encoding="utf-8",
                    )
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertTrue(image_check["passed"])
                    self.assertIn("1 images", image_check["observed"])
                    self.assertIn("noncanonical_candidates=2", image_check["observed"])
                    self.assertEqual(report["image_count"], 3)

    def test_nonportable_separators_cannot_forge_a_fence_closer(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        separators = {
            "vertical-tab": "\x0b",
            "form-feed": "\x0c",
            "file-separator": "\x1c",
            "group-separator": "\x1d",
            "record-separator": "\x1e",
            "next-line": "\u0085",
            "line-separator": "\u2028",
            "paragraph-separator": "\u2029",
        }
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for name, separator in separators.items():
                with self.subTest(name=name, codepoint=f"U+{ord(separator):04X}"):
                    response.write_text(
                        f"```\npayload{separator}```\n\n"
                        f"![Return curve]({supplied})\n\n{narrative}",
                        encoding="utf-8",
                    )
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    self.assertIn("noncanonical_candidates=1", image_check["observed"])
                    self.assertEqual(report["image_count"], 1)

    def test_portable_fence_closers_remain_conservative_before_image_credit(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        line_endings = {"lf": "\n", "crlf": "\r\n", "cr": "\r"}
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for name, ending in line_endings.items():
                with self.subTest(name=name):
                    response.write_text(
                        f"```{ending}payload{ending}```{ending} \n"
                        f"![Return curve]({supplied})\n\n{narrative}",
                        encoding="utf-8",
                    )
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    self.assertIn("noncanonical_candidates=1", image_check["observed"])
                    self.assertEqual(report["image_count"], 1)

    def test_setext_and_type7_sequences_cannot_hide_an_unclosed_fence(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        probes = {
            "setext": "===\n<br>\n```\n\n![probe](existing.svg)\n",
            "blockquote-setext": "> quote\n===\n<br>\n```\n\n![probe](existing.svg)\n",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "existing.svg").symlink_to(supplied)
            response = root / "response.md"
            for name, probe in probes.items():
                with self.subTest(name=name):
                    response.write_text(probe + f"\n{narrative}", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    self.assertIn("noncanonical_candidates=2", image_check["observed"])
                    self.assertEqual(report["image_count"], 2)

    def test_link_definition_respects_existing_paragraph_state_and_blank_termination(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        hidden_probe = "text\n[ref]: /url\n<br>\n```\n\n![probe](existing.svg)\n"
        visible_probe = "[ref]: /url\n<br>\n\n![probe](existing.svg)\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "existing.svg").symlink_to(supplied)
            response = root / "response.md"

            response.write_text(hidden_probe + f"\n{narrative}", encoding="utf-8")
            hidden = self.run_cli(
                "check", "--case", "image-anomaly-boundary",
                "--response", str(response), "--json",
            )
            self.assertEqual(hidden.returncode, 1, hidden.stderr or hidden.stdout)
            hidden_report = json.loads(hidden.stdout)
            hidden_check = next(
                check for check in hidden_report["checks"] if check["id"] == "show-image"
            )
            self.assertFalse(hidden_check["passed"])
            self.assertIn("0 images", hidden_check["observed"])
            self.assertIn("noncanonical_candidates=2", hidden_check["observed"])
            self.assertEqual(hidden_report["image_count"], 2)

            response.write_text(visible_probe + f"\n{narrative}", encoding="utf-8")
            visible = self.run_cli(
                "check", "--case", "image-anomaly-boundary",
                "--response", str(response), "--json",
            )
            self.assertEqual(visible.returncode, 1, visible.stderr or visible.stdout)
            visible_report = json.loads(visible.stdout)
            visible_check = next(
                check for check in visible_report["checks"] if check["id"] == "show-image"
            )
            self.assertFalse(visible_check["passed"])
            self.assertIn("0 images", visible_check["observed"])
            self.assertIn("noncanonical_candidates=2", visible_check["observed"])
            self.assertEqual(visible_report["image_count"], 2)

    def test_container_owned_fences_ignore_root_level_closer_lookalikes(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        probes = {
            "unordered-list": "- item\n  ```\n```\n\n![probe](existing.svg)\n",
            "ordered-list": "1. item\n   ~~~\n~~~\n\n![probe](existing.svg)\n",
            "empty-list": "-\n\n  ```\n\n![probe](existing.svg)\n",
            "empty-list-lazy-text": "-\ntext\n  ```\n\n![probe](existing.svg)\n",
            "dedented-blockquote": "- item\n> ~~~\n   ~~~~\n\n![probe](existing.svg)\n",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "existing.svg").symlink_to(supplied)
            response = root / "response.md"
            for name, probe in probes.items():
                with self.subTest(name=name):
                    response.write_text(probe + f"\n{narrative}", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    self.assertIn("noncanonical_candidates=1", image_check["observed"])
                    self.assertEqual(report["image_count"], 1)

    def test_unsupported_type7_contexts_never_receive_required_image_credit(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        probes = {
            "indented-code": "    x\n</span>\n``` py\n\n```\n\n![probe](existing.svg)\n",
            "tab-indented-code": "\tx\n</span>\n``` py\n\n```\n\n![probe](existing.svg)\n",
            "empty-blockquote": ">\n</span>\n``` py\n\n```\n\n![probe](existing.svg)\n",
            "empty-list": "1.\n</span>\n``` py\n\n```\n\n![probe](existing.svg)\n",
            "multiline-reference-title": (
                "[x]: /url\n  \"title\"\n</span>\n``` py\n\n```\n\n"
                "![probe](existing.svg)\n"
            ),
            "multiline-reference-destination": (
                "[x]:\n  /url\n</span>\n``` py\n\n```\n\n"
                "![probe](existing.svg)\n"
            ),
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "existing.svg").symlink_to(supplied)
            response = root / "response.md"
            for name, probe in probes.items():
                with self.subTest(name=name):
                    response.write_text(probe + f"\n{narrative}", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    self.assertRegex(
                        image_check["observed"],
                        r"noncanonical_candidates=[1-9][0-9]*",
                    )

    def test_forbidden_image_fails_closed_on_marker_inside_true_comment(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        hidden = f"![Hidden curve]({supplied})"

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            response.write_text(
                f"{status}\n\n<!--\n{hidden}\n-->\n",
                encoding="utf-8",
            )
            completed = self.run_cli(
                "check", "--case", "short-direct-status",
                "--response", str(response), "--json",
            )
            self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
            report = json.loads(completed.stdout)
            image_check = next(check for check in report["checks"] if check["id"] == "no-image")
            self.assertFalse(image_check["passed"])
            self.assertEqual(image_check["observed"], "1 images (maximum 0)")
            self.assertEqual(report["image_count"], 1)

    def test_forbidden_image_gate_is_fail_closed_across_inline_literal_boundaries(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        visible = f"![Return curve]({supplied})"
        visible_cases = {
            "code-blank-line": f"`open\n\n{visible}\n\nclose`",
            "code-heading": f"open `\n# heading\n{visible}\nclose `",
            "code-thematic-break": f"open `\n---\n{visible}\nclose `",
            "code-setext-h1": f"open `\n===\n{visible}\nclose `",
            "code-setext-h2": f"open `\n-\n{visible}\nclose `",
            "code-blockquote": f"open `\n> quote\n{visible}\nclose `",
            "code-list": f"open `\n- item\n{visible}\nclose `",
            "code-link-definition": f"open `\n[ref]: destination\n{visible}\nclose `",
            "comment-blank-line": f"text <!-- open\n\n{visible}\n\nclose -->",
            "comment-heading": f"text <!-- open\n# heading\n{visible}\nclose -->",
        }
        softbreak_and_block_cases = {
            "code-softbreak": f"`open\n{visible}\nclose`",
            "comment-softbreak": f"text <!-- open\n{visible}\nclose -->",
            "block-comment": f"<!-- open\n\n{visible}\n\nclose -->",
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for boundary, content in visible_cases.items():
                with self.subTest(kind="visible", boundary=boundary):
                    response.write_text(f"{status}\n\n{content}\n", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "short-direct-status",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "no-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertEqual(image_check["observed"], "1 images (maximum 0)")
                    self.assertEqual(report["image_count"], 1)

            for boundary, content in softbreak_and_block_cases.items():
                with self.subTest(kind="literal-context", boundary=boundary):
                    response.write_text(f"{status}\n\n{content}\n", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "short-direct-status",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "no-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertEqual(image_check["observed"], "1 images (maximum 0)")
                    self.assertEqual(report["image_count"], 1)

    def test_reference_style_images_are_noncanonical_required_image_candidates(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        reference_images = {
            "full": f"![Return curve][plot]\n\n[plot]: {supplied}",
            "collapsed": f"![Return curve][]\n\n[Return curve]: {supplied}",
            "shortcut": f"![Return curve]\n\n[Return curve]: {supplied}",
            "full-inline-code": f"`![Return curve][plot]`\n\n[plot]: {supplied}",
            "full-fenced-code": f"```markdown\n![Return curve][plot]\n```\n\n[plot]: {supplied}",
            "full-html-comment": f"<!-- ![Return curve][plot] -->\n\n[plot]: {supplied}",
            "full-html-block": f"<div>\n![Return curve][plot]\n\n[plot]: {supplied}",
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for syntax, image in reference_images.items():
                with self.subTest(syntax=syntax):
                    response.write_text(f"{image}\n\n{narrative}", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    expected_candidates = 2 if syntax == "full-html-block" else 1
                    self.assertIn(
                        f"noncanonical_candidates={expected_candidates}",
                        image_check["observed"],
                    )
                    self.assertEqual(report["image_count"], expected_candidates)

    def test_forbidden_image_fails_closed_on_reference_style_images(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        reference_images = {
            "full": f"![plot][p]\n\n[p]: {supplied}",
            "collapsed": f"![plot][]\n\n[plot]: {supplied}",
            "shortcut": f"![plot]\n\n[plot]: {supplied}",
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for syntax, image in reference_images.items():
                with self.subTest(syntax=syntax):
                    response.write_text(f"{status}\n\n{image}\n", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "short-direct-status",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "no-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertEqual(image_check["observed"], "1 images (maximum 0)")
                    self.assertEqual(report["image_count"], 1)

    def test_forbidden_image_fails_closed_on_reference_markers_in_literal_contexts(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        references = {
            "full": ("![plot][p]", f"[p]: {supplied}"),
            "collapsed": ("![plot][]", f"[plot]: {supplied}"),
            "shortcut": ("![plot]", f"[plot]: {supplied}"),
        }
        wrappers = {
            "inline-code": lambda image: f"`{image}`",
            "fenced-code": lambda image: f"```markdown\n{image}\n```",
            "html-comment": lambda image: f"<!-- {image} -->",
            "html-block": lambda image: f"<div>\n{image}\n\n",
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for syntax, (image, definition) in references.items():
                for context, wrap in wrappers.items():
                    with self.subTest(syntax=syntax, context=context):
                        response.write_text(
                            f"{status}\n\n{wrap(image)}\n{definition}\n",
                            encoding="utf-8",
                        )
                        completed = self.run_cli(
                            "check", "--case", "short-direct-status",
                            "--response", str(response), "--json",
                        )
                        self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                        report = json.loads(completed.stdout)
                        image_check = next(
                            check for check in report["checks"] if check["id"] == "no-image"
                        )
                        self.assertFalse(image_check["passed"])
                        expected_candidates = 2 if context == "html-block" else 1
                        self.assertEqual(
                            image_check["observed"],
                            f"{expected_candidates} images (maximum 0)",
                        )
                        self.assertEqual(report["image_count"], expected_candidates)

    def test_raw_html_images_are_noncanonical_required_image_candidates(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        good = (FIXTURES / "good" / "image-anomaly-boundary.md").read_text(encoding="utf-8")
        narrative = good.split("\n\n", 1)[1]
        raw_images = {
            "top-level-img": f'<img src="{supplied}" alt="Return curve">',
            "img-inside-div": f'<div><img src="{supplied}" alt="Return curve"></div>',
            "img-inline-code": f'`<img src="{supplied}" alt="Return curve">`',
            "img-fenced-code": f'```html\n<img src="{supplied}" alt="Return curve">\n```',
            "img-html-comment": f'<!-- <img src="{supplied}" alt="Return curve"> -->',
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for syntax, image in raw_images.items():
                with self.subTest(syntax=syntax):
                    response.write_text(f"{image}\n\n{narrative}", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "image-anomaly-boundary",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "show-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertIn("0 images", image_check["observed"])
                    expected_candidates = 2 if syntax == "img-inside-div" else 1
                    self.assertIn(
                        f"noncanonical_candidates={expected_candidates}",
                        image_check["observed"],
                    )
                    self.assertEqual(report["image_count"], expected_candidates)

    def test_forbidden_image_fails_closed_on_rendered_raw_html_images(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        raw_images = {
            "top-level-img": f'<img src="{supplied}" alt="plot">',
            "img-inside-div": f'<div><img src="{supplied}" alt="plot"></div>',
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for syntax, image in raw_images.items():
                with self.subTest(syntax=syntax):
                    response.write_text(f"{status}\n\n{image}\n", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "short-direct-status",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "no-image"
                    )
                    self.assertFalse(image_check["passed"])
                    expected_candidates = 2 if syntax == "img-inside-div" else 1
                    self.assertEqual(
                        image_check["observed"],
                        f"{expected_candidates} images (maximum 0)",
                    )
                    self.assertEqual(report["image_count"], expected_candidates)

    def test_forbidden_image_fails_closed_on_common_raw_visual_tags(self) -> None:
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        raw_visuals = {
            "img": "<img src='plot.svg' alt='plot'>",
            "picture": "<picture></picture>",
            "svg": "<svg></svg>",
            "image": "<image href='plot.svg'>",
            "object": "<object data='plot.svg'></object>",
            "embed": "<embed src='plot.svg'>",
            "iframe": "<iframe src='plot.svg'></iframe>",
            "canvas": "<canvas></canvas>",
            "video": "<video src='plot.mp4'></video>",
            "input-image": "<input type='image' src='plot.svg'>",
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for tag, raw_visual in raw_visuals.items():
                with self.subTest(tag=tag):
                    response.write_text(f"{status}\n\n{raw_visual}\n", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "short-direct-status",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "no-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertEqual(image_check["observed"], "1 images (maximum 0)")
                    self.assertEqual(report["image_count"], 1)

    def test_forbidden_image_covers_all_raw_opening_tags_but_not_encoded_literals(self) -> None:
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        raw_opening_tags = {
            "styled-div": '<div style="background-image:url(plot.svg)"></div>',
            "harmless-break": "<br>",
        }
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for tag, raw_html in raw_opening_tags.items():
                with self.subTest(kind="raw", tag=tag):
                    response.write_text(f"{status}\n\n{raw_html}\n", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "short-direct-status",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "no-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertEqual(image_check["observed"], "1 images (maximum 0)")
                    self.assertEqual(report["image_count"], 1)

            response.write_text(
                f'{status}\n\n&lt;div style="background-image:url(plot.svg)"&gt;\n',
                encoding="utf-8",
            )
            encoded = self.run_cli(
                "check", "--case", "short-direct-status",
                "--response", str(response), "--json",
            )
            self.assertEqual(encoded.returncode, 0, encoded.stderr or encoded.stdout)
            encoded_report = json.loads(encoded.stdout)
            encoded_check = next(
                check for check in encoded_report["checks"] if check["id"] == "no-image"
            )
            self.assertTrue(encoded_check["passed"])
            self.assertEqual(encoded_check["observed"], "0 images (maximum 0)")
            self.assertEqual(encoded_report["image_count"], 0)

    def test_forbidden_image_raw_tag_gate_does_not_misclassify_uri_autolinks(self) -> None:
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        autolinks = (
            "<https://example.com/report>",
            "<mailto:user@example.com>",
            "<urn:isbn:9780131103627>",
        )
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for autolink in autolinks:
                with self.subTest(kind="autolink", autolink=autolink):
                    response.write_text(f"{status}\n\n{autolink}\n", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "short-direct-status",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "no-image"
                    )
                    self.assertTrue(image_check["passed"])
                    self.assertEqual(image_check["observed"], "0 images (maximum 0)")
                    self.assertEqual(report["image_count"], 0)

            response.write_text(
                f'{status}\n\n<x-report style="background-image:url(plot.svg)"></x-report>\n',
                encoding="utf-8",
            )
            custom_tag = self.run_cli(
                "check", "--case", "short-direct-status",
                "--response", str(response), "--json",
            )
            self.assertEqual(custom_tag.returncode, 1, custom_tag.stderr or custom_tag.stdout)
            custom_report = json.loads(custom_tag.stdout)
            custom_check = next(
                check for check in custom_report["checks"] if check["id"] == "no-image"
            )
            self.assertFalse(custom_check["passed"])
            self.assertEqual(custom_check["observed"], "1 images (maximum 0)")
            self.assertEqual(custom_report["image_count"], 1)

    def test_forbidden_image_fails_closed_on_raw_html_markers_in_literal_contexts(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        image = f'<img src="{supplied}" alt="plot">'
        nonrendered_contexts = {
            "inline-code": f"`{image}`",
            "fenced-code": f"```html\n{image}\n```",
            "html-comment": f"<!-- {image} -->",
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for context, literal in nonrendered_contexts.items():
                with self.subTest(context=context):
                    response.write_text(f"{status}\n\n{literal}\n", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "short-direct-status",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "no-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertEqual(image_check["observed"], "1 images (maximum 0)")
                    self.assertEqual(report["image_count"], 1)

    def test_forbidden_image_allows_only_explicitly_literalized_image_markers(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        literalized_markers = {
            "escaped-markdown-image": rf"\![plot]({supplied})",
            "encoded-html-image": f'&lt;img src="{supplied}" alt="plot"&gt;',
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for syntax, marker in literalized_markers.items():
                with self.subTest(syntax=syntax):
                    response.write_text(f"{status}\n\n{marker}\n", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "short-direct-status",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "no-image"
                    )
                    self.assertTrue(image_check["passed"])
                    self.assertEqual(image_check["observed"], "0 images (maximum 0)")
                    self.assertEqual(report["image_count"], 0)

    def test_forbidden_image_fail_closed_gate_blocks_delimiter_bypasses(self) -> None:
        supplied = (ROOT / "evals" / "fixtures" / "assets" / "return-curve.svg").resolve()
        status = (FIXTURES / "good" / "short-direct-status.md").read_text(encoding="utf-8")
        marker = f"![plot]({supplied})"
        raw_marker = f'<IMG src="{supplied}" alt="plot">'
        bypasses = {
            "link-destination-backtick": f"[link](https://example.invalid/`)\n{marker}",
            "link-destination-comment-opener": f"[link](https://example.invalid/<!--)\n{marker}",
            "link-title-backtick": f'[link](https://example.invalid "title `")\n{marker}',
            "link-title-comment-opener": f'[link](https://example.invalid "title <!--")\n{marker}',
            "autolink-backtick": f"<https://example.invalid/`>\n{marker}",
            "autolink-comment-opener": f"<https://example.invalid/<!-->\n{marker}",
            "processing-instruction-backtick": f"<?report ` ?>\n{marker}",
            "processing-instruction-comment-opener": f"<?report <!-- ?>\n{marker}",
            "declaration-backtick": f"<!REPORT ` >\n{marker}",
            "declaration-comment-opener": f"<!REPORT <!-- >\n{marker}",
            "malformed-comment-empty": f"<!-->\n{marker}",
            "malformed-comment-single-dash": f"<!--->\n{marker}",
            "code-cross-blank": f"`open\n\n{marker}\n\nclose`",
            "code-cross-heading": f"`open\n# heading\n{marker}\nclose`",
            "comment-cross-blank": f"text <!-- open\n\n{marker}\n\nclose -->",
            "comment-cross-heading": f"text <!-- open\n# heading\n{marker}\nclose -->",
            "backslash-prefixed-raw-html": rf"\{raw_marker}",
        }

        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            for bypass, content in bypasses.items():
                with self.subTest(bypass=bypass):
                    response.write_text(f"{status}\n\n{content}\n", encoding="utf-8")
                    completed = self.run_cli(
                        "check", "--case", "short-direct-status",
                        "--response", str(response), "--json",
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr or completed.stdout)
                    report = json.loads(completed.stdout)
                    image_check = next(
                        check for check in report["checks"] if check["id"] == "no-image"
                    )
                    self.assertFalse(image_check["passed"])
                    self.assertEqual(image_check["observed"], "1 images (maximum 0)")
                    self.assertEqual(report["image_count"], 1)

    def test_nonrendered_comments_do_not_create_tables_headings_or_required_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            response.write_text(
                "<!-- # Hidden heading\n\n| A | B |\n|---|---|\n| 72.4 +/- 1.1 | 31 | -->\n"
                "No visible result.\n",
                encoding="utf-8",
            )
            completed = self.run_cli(
                "check", "--case", "experiment-null-result", "--response", str(response), "--json"
            )
            report = json.loads(completed.stdout)
            self.assertEqual(report["heading_count"], 0)
            self.assertEqual(report["markdown_table_count"], 0)
            method_a = next(check for check in report["checks"] if check["id"] == "method-a-values")
            self.assertFalse(method_a["passed"])

    def test_word_budget_counts_fenced_output_but_forbidden_claims_ignore_quoted_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            response.write_text(
                "Yes. The corpus build succeeded; coverage is 88 of 100, so 12 papers remain.\n\n"
                "```text\n" + "word " * 100 + "\n```\n",
                encoding="utf-8",
            )
            completed = self.run_cli(
                "check", "--case", "short-direct-status", "--response", str(response), "--json"
            )
            report = json.loads(completed.stdout)
            budget = next(check for check in report["checks"] if check["id"] == "short-budget")
            self.assertFalse(budget["passed"])

            source = (FIXTURES / "good" / "engineering-late-failure.md").read_text(encoding="utf-8")
            response.write_text(source + "\n```text\nall tests passed; work complete\n```\n", encoding="utf-8")
            completed = self.run_cli(
                "check", "--case", "engineering-late-failure", "--response", str(response), "--json"
            )
            report = json.loads(completed.stdout)
            false_pass = next(check for check in report["checks"] if check["id"] == "no-false-pass")
            self.assertTrue(false_pass["passed"])

    def test_response_path_requires_a_regular_file_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = self.run_cli(
                "check", "--case", "short-direct-status", "--response", temporary
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("regular file", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)

    def test_response_line_limit_fails_with_controlled_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "many-lines.md"
            response.write_text("x\n" * 100_001, encoding="utf-8")
            completed = self.run_cli(
                "check", "--case", "short-direct-status", "--response", str(response), "--json"
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("above the limit", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)

    def test_resolution_boundary_is_not_mistaken_for_false_resolution(self) -> None:
        response = FIXTURES / "good" / "incident-rollback-not-resolved.md"
        completed = self.run_cli(
            "check",
            "--case",
            "incident-rollback-not-resolved",
            "--response",
            str(response),
            "--json",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        report = json.loads(completed.stdout)
        boundary_check = next(
            check for check in report["checks"] if check["id"] == "no-false-resolution"
        )
        self.assertTrue(boundary_check["passed"])

    def test_unit_evidence_accepts_label_before_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            response.write_text(
                "Status: blocked. `parser.py` changed. Unit tests: all 42 passed. "
                "The integration test exited with status 1 because the registry credential "
                "was rejected. Renew the registry credential and rerun the integration test.\n",
                encoding="utf-8",
            )
            completed = self.run_cli(
                "check", "--case", "engineering-late-failure", "--response", str(response), "--json"
            )
            report = json.loads(completed.stdout)
            unit_check = next(check for check in report["checks"] if check["id"] == "unit-evidence")
            self.assertTrue(unit_check["passed"])

    def test_paper_limitations_accepts_absence_coordination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            response.write_text(
                "Paper [P1] addresses model-based control with an action-conditioned latent transition model.\n\n"
                "It is evaluated on two simulated control benchmarks, and mean return is 4.1 points higher over three seeds.\n\n"
                "The limitations are the absence of a statistical significance test and a real-robot experiment; this is not real-robot validation or a SOTA claim.\n",
                encoding="utf-8",
            )
            completed = self.run_cli(
                "check", "--case", "paper-summary-bounded", "--response", str(response), "--json"
            )
            report = json.loads(completed.stdout)
            limitations = next(check for check in report["checks"] if check["id"] == "limitations")
            self.assertTrue(limitations["passed"])

    def test_paper_case_accepts_explicitly_bounded_sota_language(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            response = Path(temporary) / "response.md"
            response.write_text(
                "LatentPlan uses an action-conditioned latent transition model [P1].\n\n"
                "The paper evaluates two simulated control benchmarks and reports a mean return "
                "4.1 points higher than a behavioral-cloning baseline across three seeds [P1].\n\n"
                "The account reports neither a statistical significance test nor a real-robot "
                "experiment [P1]. It does not establish state-of-the-art performance or broader "
                "generalization.\n",
                encoding="utf-8",
            )
            completed = self.run_cli(
                "check", "--case", "paper-summary-bounded", "--response", str(response), "--json"
            )
            report = json.loads(completed.stdout)
            self.assertTrue(all(check["passed"] for check in report["checks"]))

    def test_unknown_case_fails_closed_with_available_ids(self) -> None:
        completed = self.run_cli("prompt", "not-a-case")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unknown case", completed.stderr)
        self.assertIn("short-direct-status", completed.stderr)

    def test_readme_level_claim_boundary_is_in_data_and_docs(self) -> None:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertIn("cannot support", data["claim_boundary"])
        benchmark_doc = (ROOT / "BENCHMARK.md").read_text(encoding="utf-8")
        self.assertIn("do **not** show that the framework improves", benchmark_doc)
        self.assertIn("baseline-versus-framework", benchmark_doc)
        self.assertIn("long-soak", benchmark_doc)

    def test_router_matches_every_declared_report_profile(self) -> None:
        for case_id in self.case_ids():
            with self.subTest(case_id=case_id):
                completed = self.run_cli("route-check", "--case", case_id, "--json")
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                self.assertTrue(json.loads(completed.stdout)["passed"])


if __name__ == "__main__":
    unittest.main()
