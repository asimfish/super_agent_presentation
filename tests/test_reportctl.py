from __future__ import annotations

import copy
import json
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills" / "agentic-reporting" / "scripts" / "reportctl.py"


def run_cli(*arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *arguments],
        cwd=cwd or ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class ReportCtlTests(unittest.TestCase):
    def assert_terminal_safe(self, value: str) -> None:
        unsafe = [
            f"U+{ord(character):04X}"
            for character in value
            if (
                (ord(character) < 0x20 and character != "\n")
                or ord(character) == 0x7F
                or 0x80 <= ord(character) <= 0x9F
                or 0xD800 <= ord(character) <= 0xDFFF
                or ord(character) in {
                    0x061C, 0x200E, 0x200F, 0x2028, 0x2029,
                    *range(0x202A, 0x202F), *range(0x2066, 0x206A),
                }
            )
        ]
        self.assertEqual(unsafe, [], f"unsafe terminal controls: {unsafe}")

    def test_list_contains_all_protocol_families(self) -> None:
        result = run_cli("list", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(len(payload["modes"]), 11)
        self.assertEqual(len(payload["modules"]), 5)

    def test_every_mode_has_a_scaffold(self) -> None:
        listed = json.loads(run_cli("list", "--json").stdout)
        for item in listed["modes"]:
            with self.subTest(mode=item["id"]):
                result = run_cli("scaffold", "--mode", item["id"])
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(result.stdout.strip())

    def test_chinese_implementation_request_routes_correctly(self) -> None:
        result = run_cli("route", "--task", "实现修改后汇报文件、测试结果和剩余风险", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["mode"], "implementation-handoff")

    def test_explicit_intent_outranks_cross_domain_vocabulary(self) -> None:
        cases = {
            "Investigate and diagnose the root cause of the late-training mean return drop in this training curve benchmark.": "investigation-report",
            "Write an academic synthesis of this paper's benchmark evaluation results, statistical analysis, and mean return.": "academic-synthesis",
            "Give a decision brief recommending which benchmark method to choose based on the trade-off and evaluation results.": "decision-brief",
            "Review this decision brief.": "review-report",
            "Critique this academic synthesis.": "review-report",
            "Audit this experiment report.": "review-report",
            "Review the experiment report for blocking findings.": "review-report",
            "Review an academic synthesis for errors.": "review-report",
            "Review the decision brief against the requirements.": "review-report",
            "Please review the incident update for unsupported resolution claims.": "review-report",
            "请审查这份实验报告，不要表格。": "review-report",
        }
        for task, expected in cases.items():
            with self.subTest(task=task):
                result = run_cli("route", "--task", task, "--json")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["mode"], expected)

    def test_negated_display_types_are_suppressed_in_auto_routing(self) -> None:
        cases = {
            "Give a concise answer. Do not use a table or image.": ("concise-answer", []),
            "请简短回答，不要使用表格或图片。": ("concise-answer", []),
            "请给出实验汇报，但不要表格和图片。": ("experiment-report", ["conclusions"]),
            "不要使用图表，只给文字结论。": ("concise-answer", ["conclusions"]),
            "请审查这份实验报告，不要表格。": ("review-report", ["evidence"]),
            "Give an experiment report and avoid tables.": ("experiment-report", ["conclusions"]),
        }
        for task, (mode, modules) in cases.items():
            with self.subTest(task=task):
                result = run_cli("route", "--task", task, "--json")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["mode"], mode)
                self.assertEqual(payload["modules"], modules)

    def test_double_negative_display_requests_are_not_suppressed(self) -> None:
        for task in (
            "请给出实验汇报，不要省略表格。",
            "请给出实验汇报，不应省略图表。",
            "Give an experiment report. Must not omit the table.",
            "Give an experiment report without omitting the table.",
            "Give an experiment report and avoid omitting the table.",
        ):
            with self.subTest(task=task):
                result = run_cli("route", "--task", task, "--json")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("tables", json.loads(result.stdout)["modules"])

    def test_explicit_route_limits_modules(self) -> None:
        result = run_cli(
            "route",
            "--task",
            "Present the experiment",
            "--mode",
            "experiment-report",
            "--module",
            "tables",
            "--module",
            "conclusions",
            "--module",
            "evidence",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("at most two", result.stderr)

    def test_bundle_is_bounded_and_mode_specific(self) -> None:
        result = run_cli(
            "bundle",
            "--task",
            "Five-seed benchmark with a comparison table",
            "--mode",
            "experiment-report",
            "--module",
            "tables",
            "--max-chars",
            "16000",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLessEqual(len(result.stdout), 16000)
        self.assertIn("Primary mode: `experiment-report`", result.stdout)
        self.assertIn("Display module: tables", result.stdout)
        self.assertNotIn("Display module: visuals", result.stdout)

    def test_checkpoint_round_trip_and_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "report.json"
            created = run_cli(
                "checkpoint",
                "--task",
                "Summarize implementation and tests",
                "--mode",
                "implementation-handoff",
                "--output",
                str(path),
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            routed = run_cli("route", "--checkpoint", str(path), "--json")
            self.assertEqual(routed.returncode, 0, routed.stderr)
            self.assertEqual(json.loads(routed.stdout)["mode"], "implementation-handoff")
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["task"] = "tampered"
            path.write_text(json.dumps(payload), encoding="utf-8")
            rejected = run_cli("route", "--checkpoint", str(path))
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("fingerprint", rejected.stderr)

    def test_checkpoint_writer_rejects_unreadable_task_and_audience_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cases = (
                ("blank-task", ("--task", " \t ")),
                ("blank-audience", ("--task", "Summarize status", "--audience", "")),
                ("long-audience", ("--task", "Summarize status", "--audience", "a" * 501)),
            )
            for name, arguments in cases:
                with self.subTest(name=name):
                    output = root / f"{name}.json"
                    result = run_cli("checkpoint", *arguments, "--output", str(output))
                    self.assertEqual(result.returncode, 2)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertFalse(output.exists())

    def test_checkpoint_audience_round_trips_through_loader(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "checkpoint.json"
            created = run_cli(
                "checkpoint",
                "--task",
                "Summarize status",
                "--audience",
                "research team",
                "--output",
                str(checkpoint),
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            loaded = run_cli("route", "--checkpoint", str(checkpoint), "--json")
            self.assertEqual(loaded.returncode, 0, loaded.stdout + loaded.stderr)
            self.assertEqual(json.loads(loaded.stdout)["audience"], "research team")

    def test_checkpoint_requires_an_object_root_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "checkpoint.json"
            checkpoint.write_text("[]", encoding="utf-8")
            result = run_cli("route", "--checkpoint", str(checkpoint))
            self.assertEqual(result.returncode, 2)
            self.assertIn("root must be an object", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_checkpoint_rejects_malformed_routing_fields_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "checkpoint.json"
            created = run_cli(
                "checkpoint",
                "--task",
                "Summarize status",
                "--mode",
                "status-update",
                "--output",
                str(checkpoint),
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            for field, bad_value in (
                ("mode", []),
                ("surface", "telepathy"),
                ("modules", ["unknown-module"]),
                ("must_show", "not-a-list"),
            ):
                payload = json.loads(checkpoint.read_text(encoding="utf-8"))
                payload[field] = bad_value
                checkpoint.write_text(json.dumps(payload), encoding="utf-8")
                result = run_cli("route", "--checkpoint", str(checkpoint))
                self.assertEqual(result.returncode, 2, (field, result.stdout, result.stderr))
                self.assertNotIn("Traceback", result.stderr)

    def test_checkpoint_rejects_symlinked_output_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            outside = base / "outside"
            outside.mkdir()
            linked = base / "linked"
            linked.symlink_to(outside, target_is_directory=True)
            result = run_cli(
                "checkpoint",
                "--task",
                "Summarize status",
                "--mode",
                "status-update",
                "--output",
                str(linked / "checkpoint.json"),
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("symlink component", result.stderr)
            self.assertEqual(list(outside.iterdir()), [])

    def test_audit_rejects_placeholder_empty_alt_and_missing_image(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            report.write_text(
                "# Result\n\nCompleted the change.\n\n![ ](missing.png)\n\nTODO\n",
                encoding="utf-8",
            )
            result = run_cli("audit", "--file", str(report), "--mode", "implementation-handoff", "--json")
            self.assertEqual(result.returncode, 1)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertTrue({"unresolved-placeholder", "missing-image-alt", "missing-image-file"} <= codes)

    def test_audit_reports_malformed_image_targets_without_traceback(self) -> None:
        for target in ("//[", "%00.png"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temporary:
                report = Path(temporary) / "report.md"
                report.write_text(
                    f"# Result\n\nCompleted with verified evidence and a stated boundary.\n\n"
                    f"Figure 1. Parser output.\n\n![plot]({target})\n",
                    encoding="utf-8",
                )
                result = run_cli("audit", "--file", str(report), "--mode", "concise-answer", "--json")
                self.assertEqual(result.returncode, 1)
                self.assertNotIn("Traceback", result.stderr)
                payload = json.loads(result.stdout)
                self.assertIn("invalid-image-target", {item["code"] for item in payload["findings"]})

    def test_audit_accepts_supported_remote_image_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            report.write_text(
                "# Result\n\nCompleted with verified evidence and a stated boundary.\n\n"
                "Figure 1. Remote plot.\n\n![remote plot](HTTPS://example.com/plot.png)\n",
                encoding="utf-8",
            )
            result = run_cli("audit", "--file", str(report), "--mode", "concise-answer", "--json")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            payload = json.loads(result.stdout)
            codes = {item["code"] for item in payload["findings"]}
            self.assertNotIn("invalid-image-target", codes)
            self.assertNotIn("missing-image-file", codes)

    def test_audit_rejects_fragment_and_data_image_targets(self) -> None:
        targets = (
            "#plot",
            "?plot",
            "data:image/png;base64,AA==",
            "DATA:image/svg+xml,%3Csvg%3E%3C/svg%3E",
        )
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            for target in targets:
                with self.subTest(target=target):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"Figure 1. Supplied plot.\n\n![plot]({target})\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    codes = {finding["code"] for finding in json.loads(result.stdout)["findings"]}
                    self.assertIn("invalid-image-target", codes)
                    self.assertNotIn("missing-image-file", codes)

    def test_audit_rejects_malformed_http_image_authorities(self) -> None:
        targets = (
            "https://:443/x",
            "https://user@/x",
            "https://@/x",
            "https://user@:80/x",
            "https://host:bad/x",
            "https://[bad/x",
            "https://host:99999/x",
            "HTTP://:80/x",
        )
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            for target in targets:
                with self.subTest(target=target):
                    report.write_text(
                        "Outcome: Completed with a stated boundary.\n\n"
                        f"Figure 1. Remote result.\n\n![plot]({target})\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                    )
                    self.assertEqual(result.returncode, 1)
                    codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
                    self.assertIn("invalid-image-target", codes)

    def test_audit_decodes_local_image_target_character_references_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "report.md"
            literal_entity_name = root / "plot&amp;.svg"
            literal_entity_name.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report.write_text(
                "Outcome: Completed within the stated boundary.\n\n"
                "Figure 1. Verified parser output.\n\n![plot](plot&amp;.svg)\n",
                encoding="utf-8",
            )

            missing_decoded_target = run_cli(
                "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
            )
            self.assertEqual(
                missing_decoded_target.returncode,
                1,
                missing_decoded_target.stdout + missing_decoded_target.stderr,
            )
            missing_codes = {
                finding["code"]
                for finding in json.loads(missing_decoded_target.stdout)["findings"]
            }
            self.assertIn("missing-image-file", missing_codes)

            (root / "plot&.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            decoded_target_exists = run_cli(
                "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
            )
            self.assertEqual(
                decoded_target_exists.returncode,
                0,
                decoded_target_exists.stdout + decoded_target_exists.stderr,
            )
            self.assertEqual(json.loads(decoded_target_exists.stdout)["findings"], [])

    def test_audit_does_not_decode_non_commonmark_target_entity_forms(self) -> None:
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
                backing = root / "backing.svg"
                backing.write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                    encoding="utf-8",
                )
                report = root / "report.md"
                report.write_text(
                    "Outcome: Completed within the stated boundary.\n\n"
                    f"Figure 1. Verified parser output.\n\n![plot]({target})\n",
                    encoding="utf-8",
                )
                literal = root / literal_path
                literal.symlink_to(backing)

                literal_result = run_cli(
                    "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                )
                self.assertEqual(
                    literal_result.returncode,
                    0,
                    literal_result.stdout + literal_result.stderr,
                )
                self.assertEqual(json.loads(literal_result.stdout)["findings"], [])

                literal.unlink()
                (root / permissive_decoded_path).symlink_to(backing)
                decoded_only_result = run_cli(
                    "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                )
                self.assertEqual(
                    decoded_only_result.returncode,
                    1,
                    decoded_only_result.stdout + decoded_only_result.stderr,
                )
                codes = {
                    finding["code"]
                    for finding in json.loads(decoded_only_result.stdout)["findings"]
                }
                self.assertIn("missing-image-file", codes)
                self.assertNotIn("invalid-image-target", codes)

    def test_audit_uses_scalar_numeric_entities_without_legacy_remap_or_drop(self) -> None:
        legacy_paths = {
            "deleted-del": ("plot&#127;.svg", "plot.svg"),
            "remapped-euro": ("plot&#128;.svg", "plot€.svg"),
            "remapped-ellipsis": ("plot&#133;.svg", "plot….svg"),
            "deleted-max-scalar": ("plot&#x10FFFF;.svg", "plot.svg"),
        }
        for name, (target, legacy_path) in legacy_paths.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                backing = root / "backing.svg"
                backing.write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                    encoding="utf-8",
                )
                (root / legacy_path).symlink_to(backing)
                report = root / "report.md"
                report.write_text(
                    "Outcome: Completed within the stated boundary.\n\n"
                    f"Figure 1. Verified parser output.\n\n![plot]({target})\n",
                    encoding="utf-8",
                )
                result = run_cli(
                    "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                )
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                codes = {finding["code"] for finding in json.loads(result.stdout)["findings"]}
                self.assertTrue(
                    codes
                    & {
                        "noncanonical-image-syntax",
                        "invalid-image-target",
                        "missing-image-file",
                    },
                    codes,
                )

    def test_audit_maps_invalid_numeric_scalars_to_exact_replacement_path(self) -> None:
        targets = (
            "plot&#0;.svg",
            "plot&#xD800;.svg",
            "plot&#x110000;.svg",
        )
        for target in targets:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                backing = root / "backing.svg"
                backing.write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                    encoding="utf-8",
                )
                (root / "plot�.svg").symlink_to(backing)
                report = root / "report.md"
                report.write_text(
                    "Outcome: Completed within the stated boundary.\n\n"
                    f"Figure 1. Verified parser output.\n\n![plot]({target})\n",
                    encoding="utf-8",
                )
                result = run_cli(
                    "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["findings"], [])

    def test_audit_rejects_entity_escapes_for_target_whitespace_and_delimiters(self) -> None:
        cases = {
            "decoded-space": ("plot&#32;one.svg", "plot one.svg"),
            "decoded-parenthesis": ("plot&#40;one.svg", "plot(one.svg"),
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "report.md"
            for name, (target, decoded_path) in cases.items():
                with self.subTest(name=name):
                    (root / decoded_path).write_text(
                        '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                        encoding="utf-8",
                    )
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"Figure 1. Verified parser output.\n\n![plot]({target})\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    codes = {finding["code"] for finding in json.loads(result.stdout)["findings"]}
                    self.assertIn("noncanonical-image-syntax", codes)
                    self.assertNotIn("invalid-image-target", codes)
                    self.assertNotIn("missing-image-file", codes)

    def test_audit_decodes_and_validates_alt_text_character_references(self) -> None:
        empty_alt_references = ("&Tab;", "&nbsp;", "&#9;", "&NewLine;")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "plot.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"
            for alt in empty_alt_references:
                with self.subTest(kind="empty", alt=alt):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"Figure 1. Verified parser output.\n\n![{alt}](plot.svg)\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    codes = {finding["code"] for finding in json.loads(result.stdout)["findings"]}
                    self.assertIn("missing-image-alt", codes)
                    self.assertNotIn("invalid-image-alt", codes)

            report.write_text(
                "Outcome: Completed within the stated boundary.\n\n"
                "Figure 1. Verified parser output.\n\n![&#x202E;](plot.svg)\n",
                encoding="utf-8",
            )
            unsafe = run_cli(
                "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
            )
            self.assertEqual(unsafe.returncode, 1, unsafe.stdout + unsafe.stderr)
            unsafe_codes = {finding["code"] for finding in json.loads(unsafe.stdout)["findings"]}
            self.assertIn("invalid-image-alt", unsafe_codes)
            self.assertNotIn("missing-image-alt", unsafe_codes)

            report.write_text(
                "Outcome: Completed within the stated boundary.\n\n"
                "Figure 1. Verified parser output.\n\n![&copy;](plot.svg)\n",
                encoding="utf-8",
            )
            visible = run_cli(
                "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
            )
            self.assertEqual(visible.returncode, 0, visible.stdout + visible.stderr)
            self.assertEqual(json.loads(visible.stdout)["findings"], [])

    def test_audit_rejects_angle_delimited_target_even_if_literal_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "<plot.svg>").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"
            report.write_text(
                "Outcome: Completed within the stated boundary.\n\n"
                "Figure 1. Verified parser output.\n\n![plot](<plot.svg>)\n",
                encoding="utf-8",
            )
            result = run_cli(
                "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            codes = {finding["code"] for finding in json.loads(result.stdout)["findings"]}
            self.assertIn("noncanonical-image-syntax", codes)
            self.assertNotIn("missing-image-file", codes)

    def test_audit_rejects_nonfiles_and_unsupported_image_suffixes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "plot.svg").mkdir()
            (root / "note.txt").write_text("not an image", encoding="utf-8")
            report = root / "report.md"
            for target in ("plot.svg", "note.txt"):
                with self.subTest(target=target):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"Figure 1. Verified parser output.\n\n![plot]({target})\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    codes = {finding["code"] for finding in json.loads(result.stdout)["findings"]}
                    self.assertIn("invalid-image-target", codes)
                    self.assertNotIn("missing-image-file", codes)

    def test_image_scanner_supports_escaped_alt_text_and_quoted_title(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "plot.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"
            report.write_text(
                "# Result\n\nCompleted with verified evidence and a stated boundary.\n\n"
                'Figure 1. Parser plot.\n\n![plot \\] detail](plot.svg "held-out result")\n',
                encoding="utf-8",
            )
            result = run_cli("audit", "--file", str(report), "--mode", "concise-answer", "--json")
            payload = json.loads(result.stdout)
            codes = {item["code"] for item in payload["findings"]}
            self.assertNotIn("invalid-image-target", codes)
            self.assertNotIn("missing-image-file", codes)
            self.assertNotIn("missing-image-alt", codes)

    def test_audit_malformed_image_scan_completes_within_wide_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "adversarial.md"
            report.write_text("![" * 32_768, encoding="utf-8")
            try:
                result = subprocess.run(
                    [sys.executable, str(CLI), "audit", "--file", str(report), "--mode", "concise-answer", "--json"],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=5,
                )
            except subprocess.TimeoutExpired as exc:
                self.fail(f"malformed image scan exceeded the 5-second regression ceiling: {exc}")
            self.assertNotIn("Traceback", result.stderr)
            json.loads(result.stdout)

    def test_audit_caps_image_and_finding_amplification(self) -> None:
        workloads = (
            ("many-images", "![](missing.png)\n" * 40_000, "image-scan-limit", 5),
            ("many-placeholders", "TODO\n" * 2_000, "audit-finding-limit", 501),
        )
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "adversarial.md"
            for name, content, expected_code, maximum_findings in workloads:
                with self.subTest(name=name):
                    report.write_text(content, encoding="utf-8")
                    try:
                        result = subprocess.run(
                            [
                                sys.executable,
                                str(CLI),
                                "audit",
                                "--file",
                                str(report),
                                "--mode",
                                "concise-answer",
                                "--json",
                            ],
                            cwd=ROOT,
                            text=True,
                            capture_output=True,
                            check=False,
                            timeout=5,
                        )
                    except subprocess.TimeoutExpired as exc:
                        self.fail(f"{name} exceeded the 5-second regression ceiling: {exc}")
                    self.assertEqual(result.returncode, 1)
                    payload = json.loads(result.stdout)
                    self.assertIn(expected_code, {item["code"] for item in payload["findings"]})
                    self.assertLessEqual(len(payload["findings"]), maximum_findings)

    def test_audit_accepts_structurally_safe_concise_answer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            report.write_text("Yes. The parser now preserves empty fields; no other behavior changed.\n", encoding="utf-8")
            result = run_cli("audit", "--file", str(report), "--mode", "concise-answer", "--json")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["errors"], 0)

    def test_audit_does_not_treat_encoded_details_literal_as_a_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            report.write_text(
                "Answer: complete.\n\n&lt;details&gt;&lt;summary&gt;Evidence&lt;/summary&gt;"
                "Verified locally. Boundary: local check only.&lt;/details&gt;\n",
                encoding="utf-8",
            )
            result = run_cli("audit", "--file", str(report), "--mode", "concise-answer", "--json")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertNotIn("unresolved-placeholder", codes)

    def test_audit_rejects_invalid_markdown_table_separator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            report.write_text(
                "# Results\n\nTable 1 compares methods.\n\n| Method | Score |\n|:--|--:|\n| A | 1 |\n",
                encoding="utf-8",
            )
            result = run_cli("audit", "--file", str(report), "--mode", "experiment-report", "--json")
            self.assertEqual(result.returncode, 1)
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("invalid-table-separator", codes)

    def valid_spec(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "report_type": "implementation-handoff",
            "status": "completed",
            "headline": "Parser update complete",
            "summary": "The parser now preserves empty fields.",
            "claims": [
                {
                    "text": "The regression test passes.",
                    "kind": "verified",
                    "roles": ["outcome", "changes", "verification", "boundary", "next_action"],
                    "evidence_refs": ["test-1"],
                    "confidence": "high",
                }
            ],
            "evidence": [
                {"id": "test-1", "label": "unit test", "locator": "tests/test_parser.py", "verification": "passed"}
            ],
            "metrics": [],
            "visuals": [],
            "actions": [],
            "artifacts": [{"label": "parser", "path": "src/parser.py"}],
            "limitations": [],
            "open_questions": [],
        }

    def test_validate_and_render_structured_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            output = Path(temporary) / "report.md"
            spec.write_text(json.dumps(self.valid_spec()), encoding="utf-8")
            valid = run_cli("validate-spec", "--file", str(spec))
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
            rendered = run_cli("render", "--file", str(spec), "--output", str(output))
            self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
            text = output.read_text(encoding="utf-8")
            self.assertIn("# Parser update complete", text)
            self.assertIn("[test-1](tests/test_parser.py)", text)

    def test_artifact_hash_query_paths_encode_without_changing_evidence_or_remote_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / "report.json"
            output = root / "report.md"
            payload = self.valid_spec()
            payload["evidence"][0]["locator"] = "#section"  # type: ignore[index]
            payload["artifacts"] = [
                {"label": "hash artifact", "path": "#artifact.txt"},
                {"label": "query artifact", "path": "?artifact.txt"},
                {
                    "label": "remote artifact",
                    "url": "https://example.com/artifact.txt?x=1&y=2#section",
                },
            ]
            spec.write_text(json.dumps(payload), encoding="utf-8")

            validated = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            rendered = run_cli("render", "--file", str(spec), "--output", str(output))
            self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
            text = output.read_text(encoding="utf-8")
            self.assertIn("[hash artifact](%23artifact.txt)", text)
            self.assertIn("[query artifact](%3Fartifact.txt)", text)
            self.assertIn("[test-1](#section)", text)
            self.assertIn(
                "[remote artifact](https://example.com/artifact.txt?x=1&amp;y=2#section)",
                text,
            )

    def test_verified_claim_requires_known_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            payload = self.valid_spec()
            payload["claims"][0]["evidence_refs"] = ["unknown"]  # type: ignore[index]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            result = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(result.returncode, 1)
            self.assertIn("unknown evidence id", result.stdout)

    def test_unedited_strict_template_fails_placeholder_gate(self) -> None:
        template = ROOT / "skills" / "agentic-reporting" / "assets" / "templates" / "report-spec.json"
        result = run_cli("validate-spec", "--file", str(template), "--json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("unresolved placeholder", result.stdout)

    def test_report_spec_schema_is_valid_json(self) -> None:
        schema = ROOT / "skills" / "agentic-reporting" / "assets" / "templates" / "report-spec.schema.json"
        payload = json.loads(schema.read_text(encoding="utf-8"))
        self.assertEqual(payload["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertTrue(payload["allOf"])
        self.assertIn("pattern", payload["$defs"]["artifact"]["properties"]["path"])

    def test_lone_surrogates_are_invalid_data_and_never_escape_as_tracebacks(self) -> None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.fail("jsonschema is a required validation-only test dependency")
        schema_path = (
            ROOT
            / "skills"
            / "agentic-reporting"
            / "assets"
            / "templates"
            / "report-spec.schema.json"
        )
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        payloads = {}
        locator = self.valid_spec()
        locator["artifacts"] = [{"label": "bad", "path": "plot\ud800.svg"}]
        payloads["locator-value"] = locator
        headline = self.valid_spec()
        headline["headline"] = "bad\udfffheadline"
        payloads["ordinary-string-value"] = headline
        unknown_key = self.valid_spec()
        unknown_key["\ud800"] = True
        payloads["object-key"] = unknown_key

        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            for name, payload in payloads.items():
                with self.subTest(name=name):
                    self.assertTrue(list(validator.iter_errors(payload)))
                    # json.dumps emits the lone surrogate as a legal JSON escape,
                    # exercising the post-parse Unicode-scalar guard.
                    spec.write_text(json.dumps(payload), encoding="utf-8")
                    validated = run_cli("validate-spec", "--file", str(spec), "--json")
                    self.assertEqual(validated.returncode, 1, validated.stdout + validated.stderr)
                    self.assertIn("Unicode scalar values", validated.stdout)
                    self.assertNotIn("Traceback", validated.stdout + validated.stderr)
                    rendered = run_cli("render", "--file", str(spec))
                    self.assertEqual(rendered.returncode, 2, rendered.stdout + rendered.stderr)
                    self.assertIn("Unicode scalar values", rendered.stderr)
                    self.assertNotIn("Traceback", rendered.stdout + rendered.stderr)

    def test_validate_spec_is_authoritative_for_duplicate_evidence_ids(self) -> None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.fail("jsonschema is a required validation-only test dependency")
        schema_path = (
            ROOT
            / "skills"
            / "agentic-reporting"
            / "assets"
            / "templates"
            / "report-spec.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        description = schema.get("description", "")
        self.assertIn("validate-spec is authoritative", description)
        self.assertIn("identifier uniqueness", description)

        payload = self.valid_spec()
        payload["evidence"].append(  # type: ignore[union-attr]
            {
                "id": "test-1",
                "label": "different evidence record",
                "locator": "tests/test_other_parser.py",
                "verification": "failed",
            }
        )
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(payload)), [])

        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            spec.write_text(json.dumps(payload), encoding="utf-8")
            result = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("duplicate evidence id: test-1", result.stdout)

    def test_cli_and_draft_schema_agree_on_boundary_corpus_when_jsonschema_is_available(self) -> None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest("optional jsonschema package is not installed")
        schema_path = ROOT / "skills" / "agentic-reporting" / "assets" / "templates" / "report-spec.schema.json"
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        cases: list[tuple[str, dict[str, object], bool]] = []

        valid = self.valid_spec()
        cases.append(("valid", valid, True))
        boolean_version = copy.deepcopy(valid)
        boolean_version["schema_version"] = True
        cases.append(("boolean-schema-version", boolean_version, False))
        empty_postmortem = copy.deepcopy(valid)
        empty_postmortem.update({"report_type": "postmortem", "claims": [], "evidence": [], "actions": []})
        cases.append(("empty-postmortem", empty_postmortem, False))
        generic_postmortem = copy.deepcopy(valid)
        generic_postmortem.update(
            {
                "report_type": "postmortem",
                "actions": [
                    {
                        "text": "Follow up",
                        "owner": "agent",
                        "status": "proposed",
                        "acceptance_check": "Review is complete",
                    }
                ],
            }
        )
        cases.append(("postmortem-missing-semantic-roles", generic_postmortem, False))
        numeric_version = copy.deepcopy(valid)
        numeric_version["schema_version"] = 1.0
        cases.append(("numeric-schema-version", numeric_version, True))
        integer_valued_observations = copy.deepcopy(valid)
        integer_valued_observations["metrics"] = [
            {"name": "runs", "value": 1, "unit": "run", "independent_observations": 1.0}
        ]
        cases.append(("integer-valued-observations", integer_valued_observations, True))
        non_integer_observations = copy.deepcopy(integer_valued_observations)
        non_integer_observations["metrics"][0]["independent_observations"] = 1.5
        cases.append(("non-integer-observations", non_integer_observations, False))
        maximum_finite_metric = copy.deepcopy(valid)
        maximum_finite_metric["metrics"] = [
            {"name": "large", "value": 1.7976931348623157e308, "unit": "score"}
        ]
        cases.append(("maximum-finite-metric", maximum_finite_metric, True))
        infinite_metric = copy.deepcopy(valid)
        infinite_metric["metrics"] = [{"name": "infinite", "value": float("inf"), "unit": "score"}]
        cases.append(("infinite-metric", infinite_metric, False))
        oversized_integer_metric = copy.deepcopy(valid)
        oversized_integer_metric["metrics"] = [{"name": "huge", "value": 10**400, "unit": "score"}]
        cases.append(("oversized-integer-metric", oversized_integer_metric, False))
        blank_headline = copy.deepcopy(valid)
        blank_headline["headline"] = " \t "
        cases.append(("blank-headline", blank_headline, False))
        blank_claim = copy.deepcopy(valid)
        blank_claim["claims"][0]["text"] = "   "
        cases.append(("blank-claim", blank_claim, False))
        blank_evidence_label = copy.deepcopy(valid)
        blank_evidence_label["evidence"][0]["label"] = "   "
        cases.append(("blank-evidence-label", blank_evidence_label, False))
        blank_artifact_path = copy.deepcopy(valid)
        blank_artifact_path["artifacts"] = [{"label": "artifact", "path": "   "}]
        cases.append(("blank-artifact-path", blank_artifact_path, False))
        for name, path in (("leading-space-path", " plot.svg"), ("trailing-space-path", "plot.svg ")):
            padded_path = copy.deepcopy(valid)
            padded_path["artifacts"] = [{"label": "artifact", "path": path}]
            cases.append((name, padded_path, False))
        terminal_lf_artifact_url = copy.deepcopy(valid)
        terminal_lf_artifact_url["artifacts"] = [
            {"label": "artifact", "url": "https://example.com/x\n"}
        ]
        cases.append(("terminal-lf-artifact-url", terminal_lf_artifact_url, False))
        terminal_lf_artifact_path = copy.deepcopy(valid)
        terminal_lf_artifact_path["artifacts"] = [{"label": "artifact", "path": "plot.svg\n"}]
        cases.append(("terminal-lf-artifact-path", terminal_lf_artifact_path, False))
        terminal_lf_evidence = copy.deepcopy(valid)
        terminal_lf_evidence["evidence"][0]["locator"] = "plot.svg\n"
        cases.append(("terminal-lf-evidence-locator", terminal_lf_evidence, False))
        terminal_lf_visual = copy.deepcopy(valid)
        terminal_lf_visual["visuals"] = [
            {
                "path": "plot.svg\n",
                "alt_text": "Plot",
                "caption": "Figure 1. Plot.",
                "takeaway": "The artifact is shown.",
                "source": "test-1",
            }
        ]
        cases.append(("terminal-lf-visual-path", terminal_lf_visual, False))
        terminal_lf_evidence_id = copy.deepcopy(valid)
        terminal_lf_evidence_id["evidence"][0]["id"] = "test-1\n"
        terminal_lf_evidence_id["claims"][0]["evidence_refs"] = ["test-1\n"]
        cases.append(("terminal-lf-evidence-id", terminal_lf_evidence_id, False))
        tabbed_artifact_path = copy.deepcopy(valid)
        tabbed_artifact_path["artifacts"] = [
            {"label": "artifact", "path": "java\tscript:alert(1)"}
        ]
        cases.append(("tabbed-artifact-path", tabbed_artifact_path, False))
        tabbed_evidence_locator = copy.deepcopy(valid)
        tabbed_evidence_locator["evidence"][0]["locator"] = "java\tscript:alert(1)"
        cases.append(("tabbed-evidence-locator", tabbed_evidence_locator, False))
        tabbed_visual_path = copy.deepcopy(valid)
        tabbed_visual_path["visuals"] = [
            {
                "path": "java\tscript:alert(1)",
                "alt_text": "Plot",
                "caption": "Figure 1. Plot.",
                "takeaway": "The artifact is shown.",
                "source": "test-1",
            }
        ]
        cases.append(("tabbed-visual-path", tabbed_visual_path, False))
        for label, control in (
            ("c1-next-line", "\u0085"),
            ("unicode-line-separator", "\u2028"),
            ("unicode-paragraph-separator", "\u2029"),
            ("bidi-override", "\u202e"),
        ):
            controlled_artifact_path = copy.deepcopy(valid)
            controlled_artifact_path["artifacts"] = [
                {"label": "artifact", "path": f"plot{control}.svg"}
            ]
            cases.append((f"{label}-artifact-path", controlled_artifact_path, False))
            controlled_artifact_url = copy.deepcopy(valid)
            controlled_artifact_url["artifacts"] = [
                {"label": "artifact", "url": f"https://example.com/plot{control}.svg"}
            ]
            cases.append((f"{label}-artifact-url", controlled_artifact_url, False))
            controlled_evidence = copy.deepcopy(valid)
            controlled_evidence["evidence"][0]["locator"] = f"plot{control}.svg"
            cases.append((f"{label}-evidence-locator", controlled_evidence, False))
            controlled_visual = copy.deepcopy(valid)
            controlled_visual["visuals"] = [
                {
                    "path": f"plot{control}.svg",
                    "alt_text": "Plot",
                    "caption": "Figure 1. Plot.",
                    "takeaway": "The artifact is shown.",
                    "source": "test-1",
                }
            ]
            cases.append((f"{label}-visual-path", controlled_visual, False))
        for label, nonprinting in (
            ("zero-width-space", "\u200b"),
            ("byte-order-mark", "\ufeff"),
        ):
            nonprinting_artifact = copy.deepcopy(valid)
            nonprinting_artifact["artifacts"] = [
                {"label": "artifact", "path": f"plot{nonprinting}.svg"}
            ]
            cases.append((f"{label}-artifact-path", nonprinting_artifact, False))
            nonprinting_evidence = copy.deepcopy(valid)
            nonprinting_evidence["evidence"][0]["locator"] = f"plot{nonprinting}.svg"
            cases.append((f"{label}-evidence-locator", nonprinting_evidence, False))
            nonprinting_visual = copy.deepcopy(valid)
            nonprinting_visual["visuals"] = [
                {
                    "path": f"plot{nonprinting}.svg",
                    "alt_text": "Plot",
                    "caption": "Figure 1. Plot.",
                    "takeaway": "The artifact is shown.",
                    "source": "test-1",
                }
            ]
            cases.append((f"{label}-visual-path", nonprinting_visual, False))
        empty_experiment = copy.deepcopy(valid)
        empty_experiment.update({"report_type": "experiment-report", "metrics": []})
        cases.append(("empty-experiment", empty_experiment, False))
        uppercase_url = copy.deepcopy(valid)
        uppercase_url["artifacts"] = [{"label": "remote", "url": "HTTPS://example.com/check"}]
        cases.append(("uppercase-url", uppercase_url, True))
        localhost_with_port = copy.deepcopy(valid)
        localhost_with_port["artifacts"] = [{"label": "remote", "url": "https://localhost:8000/check"}]
        cases.append(("localhost-with-port", localhost_with_port, True))
        missing_host = copy.deepcopy(valid)
        missing_host["artifacts"] = [{"label": "remote", "url": "https:///missing-host"}]
        cases.append(("missing-host", missing_host, False))
        query_without_host = copy.deepcopy(valid)
        query_without_host["artifacts"] = [{"label": "remote", "url": "https://?x"}]
        cases.append(("query-without-host", query_without_host, False))
        fragment_without_host = copy.deepcopy(valid)
        fragment_without_host["artifacts"] = [{"label": "remote", "url": "https://#x"}]
        cases.append(("fragment-without-host", fragment_without_host, False))
        malformed_bracket_host = copy.deepcopy(valid)
        malformed_bracket_host["artifacts"] = [{"label": "remote", "url": "http://["}]
        cases.append(("malformed-bracket-host", malformed_bracket_host, False))
        for name, url in (
            ("port-without-host", "https://:443/x"),
            ("userinfo-without-host", "https://user@/x"),
            ("empty-userinfo-without-host", "https://@/x"),
            ("userinfo-and-port-without-host", "https://user@:80/x"),
            ("non-numeric-port", "https://host:bad/x"),
            ("out-of-range-port", "https://host:99999/x"),
        ):
            malformed_authority = copy.deepcopy(valid)
            malformed_authority["artifacts"] = [{"label": "remote", "url": url}]
            cases.append((name, malformed_authority, False))
        unsafe_path = copy.deepcopy(valid)
        unsafe_path["artifacts"] = [{"label": "local", "path": "javascript:alert(1)"}]
        cases.append(("unsafe-local-path", unsafe_path, False))
        dual_locator = copy.deepcopy(valid)
        dual_locator["artifacts"] = [{"label": "dual", "path": 1, "url": "https://example.com/a"}]
        cases.append(("dual-locator", dual_locator, False))

        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            for name, payload, expected in cases:
                with self.subTest(name=name):
                    schema_valid = not list(validator.iter_errors(payload))
                    spec.write_text(json.dumps(payload), encoding="utf-8")
                    cli_valid = run_cli("validate-spec", "--file", str(spec)).returncode == 0
                    self.assertEqual(schema_valid, expected)
                    self.assertEqual(cli_valid, expected)

    def test_validator_rejects_nested_fields_and_invalid_enums(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            payload = self.valid_spec()
            payload["claims"][0]["invented"] = True  # type: ignore[index]
            payload["actions"] = [
                {
                    "text": "Re-run the benchmark",
                    "owner": "agent",
                    "status": "done-ish",
                    "acceptance_check": "Benchmark exits zero",
                }
            ]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            result = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(result.returncode, 1)
            self.assertIn("unknown field: invented", result.stdout)
            self.assertIn("actions[0].status must be one of", result.stdout)

    def test_validator_rejects_empty_substantive_postmortem(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            payload = self.valid_spec()
            payload["report_type"] = "postmortem"
            payload["claims"] = []
            payload["evidence"] = []
            payload["actions"] = []
            spec.write_text(json.dumps(payload), encoding="utf-8")
            result = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(result.returncode, 1)
            self.assertIn("requires at least one claim", result.stdout)
            self.assertIn("requires at least one evidence item", result.stdout)
            self.assertIn("requires at least one action", result.stdout)

    def test_postmortem_requires_explicit_impact_timeline_and_cause_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            payload = self.valid_spec()
            payload["report_type"] = "postmortem"
            payload["actions"] = [
                {
                    "text": "Add a regression guard",
                    "owner": "agent",
                    "status": "proposed",
                    "acceptance_check": "Guard fails on the incident fixture",
                }
            ]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            missing = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(missing.returncode, 1)
            self.assertIn("requires semantic coverage: impact", missing.stdout)
            self.assertIn("requires semantic coverage: timeline", missing.stdout)
            self.assertIn("requires semantic coverage: cause", missing.stdout)

            payload["claims"][0]["roles"] = ["impact", "timeline", "cause"]  # type: ignore[index]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            valid = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)

    def test_strict_semantic_coverage_tracks_every_catalog_mode(self) -> None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.fail("jsonschema is a required validation-only test dependency")
        catalog = json.loads(
            (ROOT / "skills" / "agentic-reporting" / "references" / "protocols.json").read_text(encoding="utf-8")
        )
        schema = json.loads(
            (ROOT / "skills" / "agentic-reporting" / "assets" / "templates" / "report-spec.schema.json").read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(schema)
        structural_roles = {"outcome", "evidence", "metrics", "uncertainty"}
        action_required_modes = {"incident-update", "postmortem", "risk-report"}
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            for mode, protocol in catalog["modes"].items():
                with self.subTest(mode=mode, case="complete"):
                    payload = self.valid_spec()
                    payload["report_type"] = mode
                    required = list(protocol["required_semantics"])
                    payload["claims"][0]["roles"] = required  # type: ignore[index]
                    if mode == "experiment-report":
                        payload["metrics"] = [
                            {
                                "name": "score",
                                "value": 1,
                                "unit": "point",
                                "uncertainty": "one supplied observation; interval unavailable",
                            }
                        ]
                    if mode in action_required_modes:
                        payload["actions"] = [
                            {
                                "text": "Complete the owned follow-up",
                                "owner": "agent",
                                "status": "proposed",
                                "acceptance_check": "Follow-up evidence is recorded",
                            }
                        ]
                    spec.write_text(json.dumps(payload), encoding="utf-8")
                    cli_valid = run_cli("validate-spec", "--file", str(spec))
                    self.assertEqual(cli_valid.returncode, 0, cli_valid.stdout + cli_valid.stderr)
                    self.assertEqual(list(validator.iter_errors(payload)), [])

                    externally_covered = set(structural_roles)
                    if mode in action_required_modes:
                        externally_covered.add("next_action")
                    for semantic in required:
                        if semantic in externally_covered:
                            continue
                        missing = copy.deepcopy(payload)
                        missing["claims"][0]["roles"].remove(semantic)
                        if not missing["claims"][0]["roles"]:
                            missing["claims"][0]["roles"] = ["outcome"]
                        spec.write_text(json.dumps(missing), encoding="utf-8")
                        with self.subTest(mode=mode, missing=semantic):
                            self.assertEqual(run_cli("validate-spec", "--file", str(spec)).returncode, 1)
                            self.assertTrue(list(validator.iter_errors(missing)))

    def test_artifact_locator_requires_exactly_one_typed_safe_locator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            payload = self.valid_spec()
            payload["artifacts"] = [{"label": "bad", "path": 1, "url": "https://example.com/a"}]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            result = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(result.returncode, 1)
            self.assertIn("exactly one of path or url", result.stdout)

            payload["artifacts"] = [{"label": "bad", "path": "javascript:alert(1)"}]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            result = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(result.returncode, 1)
            self.assertIn("local path", result.stdout)

    def test_validator_matches_nullable_metric_value_in_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            payload = self.valid_spec()
            payload["metrics"] = [{"name": "Unavailable metric", "value": None, "unit": "n/a"}]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            result = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_rejects_non_finite_metric_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            payload = self.valid_spec()
            payload["metrics"] = [{"name": "Exploded metric", "value": float("inf"), "unit": "score"}]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            result = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(result.returncode, 2)
            self.assertIn("non-standard numeric constant", result.stderr)

            spec.write_text(json.dumps(payload).replace("Infinity", "1e999"), encoding="utf-8")
            result = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(result.returncode, 1)
            self.assertIn("finite number", result.stdout)

    def test_strict_renderer_rejects_unsafe_locator_scheme(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            payload = self.valid_spec()
            payload["evidence"][0]["locator"] = "javascript:alert(1)"  # type: ignore[index]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            result = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(result.returncode, 1)
            self.assertIn("unsupported URI scheme", result.stdout)

            payload["evidence"][0]["locator"] = "http://["  # type: ignore[index]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            result = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(result.returncode, 1)
            self.assertIn("well-formed", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

    def test_structured_visual_line_separators_are_rejected_before_render(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            for separator in ("\u2028", "\u2029"):
                with self.subTest(codepoint=f"U+{ord(separator):04X}"):
                    payload = self.valid_spec()
                    payload["visuals"] = [
                        {
                            "path": f"plot{separator}.svg",
                            "alt_text": "Plot",
                            "caption": "Figure 1. Plot.",
                            "takeaway": "The supplied result is preserved.",
                            "source": "test-1",
                        }
                    ]
                    spec.write_text(json.dumps(payload), encoding="utf-8")
                    validated = run_cli("validate-spec", "--file", str(spec), "--json")
                    self.assertEqual(validated.returncode, 1)
                    rendered = run_cli("render", "--file", str(spec))
                    self.assertEqual(rendered.returncode, 2)
                    self.assertEqual(rendered.stdout, "")
                    self.assertNotIn("Traceback", rendered.stderr)

    def test_uppercase_remote_visual_survives_render_and_strict_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            output = Path(temporary) / "report.md"
            payload = self.valid_spec()
            payload["visuals"] = [
                {
                    "path": "HTTPS://example.com/plot.svg",
                    "alt_text": "Verified parser result",
                    "caption": "Figure 1. Verified parser result.",
                    "takeaway": "The supplied result is preserved.",
                    "source": "test-1",
                    "evidence_refs": ["test-1"],
                }
            ]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            rendered = run_cli("render", "--file", str(spec), "--output", str(output))
            self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
            audited = run_cli(
                "audit", "--file", str(output), "--mode", "implementation-handoff", "--strict", "--json"
            )
            self.assertEqual(audited.returncode, 0, audited.stdout + audited.stderr)
            findings = json.loads(audited.stdout)["findings"]
            self.assertNotIn("missing-image-file", {finding["code"] for finding in findings})

    def test_local_visual_delimiters_round_trip_through_render_and_strict_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / "report.json"
            output = root / "report.md"
            filenames = ("plot#final.svg", "plot?final.svg", "plot%20final.svg")
            for filename in filenames:
                (root / filename).write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                    encoding="utf-8",
                )
            payload = self.valid_spec()
            payload["visuals"] = [
                {
                    "id": f"Figure {index}",
                    "path": filename,
                    "alt_text": f"Verified output {index}",
                    "caption": f"Figure {index}. Verified parser output.",
                    "takeaway": "The supplied artifact exists.",
                    "source": "test-1",
                    "evidence_refs": ["test-1"],
                }
                for index, filename in enumerate(filenames, start=1)
            ]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            rendered = run_cli("render", "--file", str(spec), "--output", str(output))
            self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
            text = output.read_text(encoding="utf-8")
            self.assertIn("plot%23final.svg", text)
            self.assertIn("plot%3Ffinal.svg", text)
            self.assertIn("plot%2520final.svg", text)
            audited = run_cli(
                "audit", "--file", str(output), "--mode", "implementation-handoff", "--strict", "--json"
            )
            self.assertEqual(audited.returncode, 0, audited.stdout + audited.stderr)
            codes = {finding["code"] for finding in json.loads(audited.stdout)["findings"]}
            self.assertNotIn("missing-image-file", codes)
            self.assertNotIn("invalid-image-target", codes)

    def test_structured_visual_ampersands_round_trip_through_strict_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / "report.json"
            output = root / "report.md"
            (root / "plot&.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            payload = self.valid_spec()
            payload["visuals"] = [
                {
                    "id": "Figure 1",
                    "path": "plot&.svg",
                    "alt_text": "Verified local output",
                    "caption": "Figure 1. Verified local parser output.",
                    "takeaway": "The supplied local artifact exists.",
                    "source": "test-1",
                    "evidence_refs": ["test-1"],
                },
                {
                    "id": "Figure 2",
                    "path": "https://example.com/plot.svg?a=1&b=2",
                    "alt_text": "Verified remote output",
                    "caption": "Figure 2. Verified remote parser output.",
                    "takeaway": "The remote target retains both query parameters.",
                    "source": "test-1",
                    "evidence_refs": ["test-1"],
                },
            ]
            spec.write_text(json.dumps(payload), encoding="utf-8")

            rendered = run_cli("render", "--file", str(spec), "--output", str(output))
            self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
            text = output.read_text(encoding="utf-8")
            self.assertIn("](plot%26.svg)", text)
            self.assertIn("](https://example.com/plot.svg?a=1&amp;b=2)", text)

            audited = run_cli(
                "audit", "--file", str(output), "--mode", "implementation-handoff", "--strict", "--json"
            )
            self.assertEqual(audited.returncode, 0, audited.stdout + audited.stderr)
            self.assertEqual(json.loads(audited.stdout)["findings"], [])

    def test_structured_visual_backticks_render_escaped_and_pass_strict_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / "report.json"
            output = root / "report.md"
            (root / "plot.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            payload = self.valid_spec()
            payload["visuals"] = [
                {
                    "path": "plot.svg",
                    "alt_text": "Plot `code` result",
                    "caption": "Figure 1. Verified parser output.",
                    "takeaway": "The supplied artifact exists.",
                    "source": "test-1",
                    "evidence_refs": ["test-1"],
                }
            ]
            spec.write_text(json.dumps(payload), encoding="utf-8")

            validated = run_cli("validate-spec", "--file", str(spec), "--json")
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            rendered = run_cli("render", "--file", str(spec), "--output", str(output))
            self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
            self.assertIn(
                r"![Plot \`code\` result](plot.svg)",
                output.read_text(encoding="utf-8"),
            )
            audited = run_cli(
                "audit", "--file", str(output), "--mode", "implementation-handoff", "--strict", "--json"
            )
            self.assertEqual(audited.returncode, 0, audited.stdout + audited.stderr)
            self.assertEqual(json.loads(audited.stdout)["findings"], [])

    def test_handwritten_unescaped_or_even_escaped_alt_backticks_are_noncanonical(self) -> None:
        alt_texts = {
            "unescaped": "Plot `code` result",
            "even-backslashes": r"Plot \\`code\\` result",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "plot.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"
            for name, alt in alt_texts.items():
                with self.subTest(name=name):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"Figure 1. Verified parser output.\n\n![{alt}](plot.svg)\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    codes = {finding["code"] for finding in json.loads(result.stdout)["findings"]}
                    self.assertIn("noncanonical-image-syntax", codes)
                    self.assertNotIn("missing-image-file", codes)

    def test_structured_fragment_and_query_visuals_are_rejected_by_schema_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / "report.json"
            try:
                from jsonschema import Draft202012Validator
            except ImportError:
                self.fail("jsonschema is a required validation-only test dependency")
            schema_path = (
                ROOT
                / "skills"
                / "agentic-reporting"
                / "assets"
                / "templates"
                / "report-spec.schema.json"
            )
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            for index, path in enumerate(("#plot", "?plot"), start=1):
                with self.subTest(path=path):
                    output = root / f"report-{index}.md"
                    payload = self.valid_spec()
                    payload["visuals"] = [
                        {
                            "path": path,
                            "alt_text": "Inline plot",
                            "caption": "Figure 1. Inline plot.",
                            "takeaway": "The plot is supplied by the final document surface.",
                            "source": "test-1",
                            "evidence_refs": ["test-1"],
                        }
                    ]
                    spec.write_text(json.dumps(payload), encoding="utf-8")
                    self.assertTrue(list(Draft202012Validator(schema).iter_errors(payload)))

                    validated = run_cli("validate-spec", "--file", str(spec), "--json")
                    self.assertEqual(validated.returncode, 1, validated.stdout + validated.stderr)
                    rendered = run_cli("render", "--file", str(spec), "--output", str(output))
                    self.assertEqual(rendered.returncode, 2, rendered.stdout + rendered.stderr)
                    self.assertFalse(output.exists())

    def test_structured_visual_rejects_leading_or_trailing_path_whitespace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / "report.json"
            output = root / "report.md"
            for path in (" plot.svg", "plot.svg "):
                with self.subTest(path=path):
                    payload = self.valid_spec()
                    payload["visuals"] = [
                        {
                            "path": path,
                            "alt_text": "Plot",
                            "caption": "Figure 1. Plot.",
                            "takeaway": "The supplied artifact is shown.",
                            "source": "test-1",
                        }
                    ]
                    spec.write_text(json.dumps(payload), encoding="utf-8")
                    validated = run_cli("validate-spec", "--file", str(spec), "--json")
                    self.assertEqual(validated.returncode, 1)
                    self.assertIn("must not begin or end with whitespace", validated.stdout)
                    rendered = run_cli("render", "--file", str(spec), "--output", str(output))
                    self.assertEqual(rendered.returncode, 2)
                    self.assertFalse(output.exists())

    def test_strict_renderer_escapes_markdown_and_html_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            spec = Path(temporary) / "report.json"
            payload = self.valid_spec()
            payload["headline"] = "Research & results"
            payload["summary"] = "**not emphasis**"
            spec.write_text(json.dumps(payload), encoding="utf-8")
            result = run_cli("render", "--file", str(spec))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Research &amp; results", result.stdout)
            self.assertIn("\\*\\*not emphasis\\*\\*", result.stdout)
            self.assertNotIn("**not emphasis**", result.stdout)

    def test_strict_renderer_preserves_semantic_fields_and_audits_its_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / "report.json"
            output = root / "report.md"
            image = root / "plot one.svg"
            image.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>", encoding="utf-8")
            payload = self.valid_spec()
            payload["claims"][0]["confidence"] = "low"  # type: ignore[index]
            payload["claims"][0]["boundary"] = "Only the supplied test is verified."  # type: ignore[index]
            payload["metrics"] = [
                {
                    "name": "Accuracy | held-out",
                    "value": 91.2,
                    "unit": "%",
                    "direction": "higher-is-better",
                    "denominator": "100 tasks",
                    "baseline": "parser v1",
                    "time_window": "2026-08-24",
                    "independent_observations": 5,
                    "uncertainty": "mean across five runs; interval unavailable",
                    "evidence_refs": ["test-1"],
                }
            ]
            payload["visuals"] = [
                {
                    "id": "Figure 1",
                    "type": "line chart",
                    "purpose": "show the observed trend",
                    "path": image.name,
                    "alt_text": "Accuracy [held-out] over five runs",
                    "caption": "Observed held-out accuracy",
                    "takeaway": "The plot displays the five supplied observations.",
                    "source": "test-1",
                    "evidence_refs": ["test-1"],
                }
            ]
            payload["actions"] = [
                {
                    "text": "Repeat the held-out run",
                    "owner": "agent",
                    "status": "in-progress",
                    "deadline": "2026-08-25",
                    "acceptance_check": "Five new runs are recorded",
                }
            ]
            payload["limitations"] = ["No confidence interval is available."]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            rendered = run_cli("render", "--file", str(spec), "--output", str(output))
            self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
            text = output.read_text(encoding="utf-8")
            for expected in (
                "low confidence",
                "changes / verification",
                "Verification: passed",
                "higher-is-better",
                "denominator: 100 tasks",
                "parser v1",
                "2026-08-24",
                "| 5 |",
                "test-1",
                "Type: line chart",
                "Purpose: show the observed trend",
                "2026-08-25",
                "Five new runs are recorded",
                "Accuracy \\| held-out",
                "plot%20one.svg",
            ):
                self.assertIn(expected, text)
            audited = run_cli(
                "audit", "--file", str(output), "--mode", "implementation-handoff", "--strict", "--json"
            )
            self.assertEqual(audited.returncode, 0, audited.stdout + audited.stderr)
            report = json.loads(audited.stdout)
            self.assertEqual(report["errors"], 0)
            self.assertEqual(report["warnings"], 0)

    def test_file_inputs_reject_directories_without_tracebacks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            for command in (
                ("validate-spec", "--file", temporary),
                ("audit", "--file", temporary, "--mode", "concise-answer"),
            ):
                result = run_cli(*command)
                self.assertEqual(result.returncode, 2)
                self.assertIn("regular file", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_deep_json_inputs_fail_with_controlled_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "deep.json"
            bounded_depth = 150
            payloads = (
                "[" * 2000 + "0" + "]" * 2000,
                '{"extra":' + "[" * bounded_depth + "0" + "]" * bounded_depth + "}",
            )
            for index, payload in enumerate(payloads):
                with self.subTest(index=index):
                    path.write_text(payload, encoding="utf-8")
                    result = run_cli("validate-spec", "--file", str(path), "--json")
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("reportctl: Invalid JSON", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_unknown_user_output_paths_fail_with_controlled_errors(self) -> None:
        impossible = "~__reportctl_no_such_user__/output"
        commands = (
            ("checkpoint", "--task", "Summarize status", "--output", impossible + ".json"),
            ("build-dist", "--output", impossible + "-dist"),
        )
        for command in commands:
            with self.subTest(command=command[0]):
                result = run_cli(*command)
                self.assertEqual(result.returncode, 2)
                self.assertIn("Cannot expand", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_overlong_output_component_fails_without_traceback_or_partial_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / "report.json"
            spec.write_text(json.dumps(self.valid_spec()), encoding="utf-8")
            overlong = "a" * 300
            commands = (
                ("checkpoint", "--task", "Summarize status", "--output", str(root / overlong / "c.json")),
                ("build-dist", "--output", str(root / overlong / "dist")),
                ("render", "--file", str(spec), "--output", str(root / overlong / "report.md")),
            )
            for command in commands:
                with self.subTest(command=command[0]):
                    result = run_cli(*command)
                    self.assertEqual(result.returncode, 2)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertEqual([item.name for item in root.iterdir()], ["report.json"])

    def test_audit_symlink_loop_image_target_is_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "loop").symlink_to("loop")
            report = root / "report.md"
            report.write_text(
                "# Result\n\nCompleted with a stated boundary.\n\n"
                "Figure 1. Parser output.\n\n![plot](loop/x.png)\n",
                encoding="utf-8",
            )
            result = run_cli("audit", "--file", str(report), "--mode", "concise-answer", "--json")
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("invalid-image-target", {item["code"] for item in payload["findings"]})

    def test_audit_rejects_nonportable_control_delimited_image_targets(self) -> None:
        controls = ("\x0b", "\x0c", "\u2028", "\u2029")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "plot.svg"
            image.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>", encoding="utf-8")
            report = root / "report.md"
            for control in controls:
                for target in (
                    f"plot.svg{control}\"title\"",
                    f"plot.svg#{control} \"title\"",
                ):
                    with self.subTest(codepoint=f"U+{ord(control):04X}", target=target):
                        report.write_text(
                            "# Result\n\nCompleted with a stated boundary.\n\n"
                            f"Figure 1. Parser output.\n\n![plot]({target})\n",
                            encoding="utf-8",
                        )
                        result = run_cli(
                            "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                        )
                        self.assertEqual(result.returncode, 1)
                        self.assertNotIn("Traceback", result.stderr)
                        payload = json.loads(result.stdout)
                        codes = {item["code"] for item in payload["findings"]}
                        self.assertIn("noncanonical-image-syntax", codes)
                        self.assertNotIn("invalid-image-target", codes)

    def test_audit_enforces_canonical_and_conservative_image_markers(self) -> None:
        masked_examples = {
            "escaped-bang": r"\![plot](missing.png)",
            "encoded-raw-html": "`&lt;img src='missing.png'>`",
            "inline-code": r"`![plot](missing.png)`",
            "inline-code-raw-html": r"`<img src='missing.png'>`",
            "fenced-code": "```markdown\n![plot](missing.png)\n```",
            "fenced-code-raw-html": "```html\n<img src='missing.png'>\n```",
            "tilde-fence": "~~~markdown\n![plot](missing.png)\n~~~",
            "html-comment": "<!-- ![plot](missing.png) -->",
            "html-comment-raw-html": "<!-- <img src='missing.png'> -->",
            "html-div": "<div>\n![plot](missing.png)\n</div>\n",
            "html-processing-instruction": "<?xml\n![plot](missing.png)\n?>",
            "html-declaration": "<!DOCTYPE html\n![plot](missing.png)\n>",
            "html-cdata": "<![CDATA[\n![plot](missing.png)\n]]>",
            "html-type-seven": "<span>\n![plot](missing.png)\n</span>\n",
            "html-raw-script": "<script>\n\n![plot](missing.png)\n</script>",
        }
        image_codes = {
            "invalid-image-target", "missing-image-alt", "missing-image-file",
            "image-without-context", "noncanonical-image-syntax",
        }
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            for name, example in masked_examples.items():
                with self.subTest(kind="masked", name=name):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"Example only:\n\n{example}\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                    )
                    self.assertNotIn("Traceback", result.stderr)
                    codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
                    if name in {"escaped-bang", "encoded-raw-html"}:
                        self.assertTrue(codes.isdisjoint(image_codes), codes)
                    else:
                        self.assertIn("noncanonical-image-syntax", codes)
                        self.assertNotIn("missing-image-file", codes)

            noncanonical_examples = {
                "three-space-indent": "   ![plot](missing.png)",
                "indented": "    ![plot](missing.png)",
                "list-continuation": "- item\n\n    ![plot](missing.png)",
                "list-lazy-continuation": "- item\n![plot](missing.png)",
                "blockquote-indented": ">     ![plot](missing.png)",
                "blockquote-lazy-continuation": "> item\n![plot](missing.png)",
                "mixed-trailing-prose": "![plot](missing.png) trailing",
                "preceding-line-without-blank": "context\n![plot](missing.png)",
                "following-line-without-blank": "![plot](missing.png)\ncontext",
                "setext-following-line": "![plot](missing.png)\n---",
                "nested-alt": "![a [x](missing.png)",
                "inline-code-in-alt": "![a `code`](missing.png)",
                "escaped-bang-in-alt": r"![\![x](missing.png)",
                "blank-alt-line": "![alt\n\nx](missing.png)",
                "blank-title-line": "![alt](missing.png \"ti\n\ntle\")",
                "raw-parenthesis-target": "![alt](missing.png#(x))",
                "escaped-parenthesis-target": r"![alt](missing.png#\))",
                "angle-target": "![alt](<missing image.png>)",
                "empty-target": "![alt]()",
                "parenthesized-title": "![alt](missing.png (title))",
                "full-reference": "![alt][plot]\n\n[plot]: missing.png",
                "collapsed-reference": "![alt][]\n\n[alt]: missing.png",
                "shortcut-reference": "![alt]\n\n[alt]: missing.png",
                "raw-html-image": "<img src='missing.png' alt='plot'>",
                "nested-raw-html-image": "<div><img src='missing.png' alt='plot'></div>",
            }
            for name, example in noncanonical_examples.items():
                with self.subTest(kind="noncanonical", name=name):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"Figure example:\n\n{example}\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                    )
                    self.assertEqual(result.returncode, 1)
                    codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
                    self.assertIn("noncanonical-image-syntax", codes)
                    self.assertNotIn("missing-image-file", codes)

    def test_type_seven_html_block_cannot_interrupt_a_paragraph(self) -> None:
        examples = (
            "context\n<span>\n![plot](missing.png)\n",
            "context\n</span>\n![plot](missing.png)\n",
            "- item\n<span>\n![plot](missing.png)\n",
        )
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            for example in examples:
                with self.subTest(example=example):
                    report.write_text(example, encoding="utf-8")
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                    )
                    self.assertEqual(result.returncode, 1)
                    codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
                    self.assertIn("noncanonical-image-syntax", codes)

    def test_pre_image_fence_or_type7_syntax_uses_conservative_credit(self) -> None:
        visible = "![plot](missing.png)"
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
            report = Path(temporary) / "report.md"
            for name, prefix in prefixes.items():
                with self.subTest(name=name):
                    report.write_text(f"{prefix}\n\n{visible}\n", encoding="utf-8")
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                    )
                    self.assertEqual(result.returncode, 1)
                    codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
                    if name in conservative:
                        self.assertIn("noncanonical-image-syntax", codes)
                        self.assertNotIn("missing-image-file", codes)
                    else:
                        self.assertIn("missing-image-file", codes)

    def test_commonmark_html_terminators_restore_a_later_canonical_image(self) -> None:
        prefixes = {
            "overlapping-comment-close": "<!-->",
            "overlapping-comment-dash-close": "<!--->",
            "overlapping-processing-instruction-close": "<?>",
            "raw-tag-family-close": "<script>\n</style>",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "plot.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"
            for name, prefix in prefixes.items():
                with self.subTest(name=name):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"{prefix}\n\n"
                        "Figure 1. Verified parser output.\n\n![plot](plot.svg)\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                    )
                    payload = json.loads(result.stdout)
                    if name == "raw-tag-family-close":
                        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                        self.assertEqual(
                            [finding["code"] for finding in payload["findings"]],
                            ["noncanonical-image-syntax"],
                        )
                    else:
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        self.assertEqual(payload["findings"], [])

    def test_isolated_type1_closing_tags_do_not_consume_an_unclosed_fence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "plot.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"
            for tag in ("pre", "script", "style", "textarea"):
                with self.subTest(tag=tag):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"text\n</{tag}>\n```\n\n"
                        "Figure 1. Verified parser output.\n\n![plot](plot.svg)\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    findings = json.loads(result.stdout)["findings"]
                    image_findings = [
                        finding
                        for finding in findings
                        if finding["code"] == "noncanonical-image-syntax"
                    ]
                    self.assertEqual(
                        [finding["code"] for finding in image_findings],
                        ["noncanonical-image-syntax"],
                    )

    def test_type1_openings_still_end_on_any_type1_closing_tag(self) -> None:
        tag_pairs = {
            "pre": "script",
            "script": "style",
            "style": "textarea",
            "textarea": "pre",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "plot.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"
            for opening, closing in tag_pairs.items():
                with self.subTest(opening=opening, closing=closing):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"<{opening}>\n![hidden](missing.svg)\n</{closing}>\n\n"
                        "Figure 1. Verified parser output.\n\n![plot](plot.svg)\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    findings = json.loads(result.stdout)["findings"]
                    image_findings = [
                        finding
                        for finding in findings
                        if finding["code"] == "noncanonical-image-syntax"
                    ]
                    self.assertEqual(
                        [finding["code"] for finding in image_findings],
                        ["noncanonical-image-syntax", "noncanonical-image-syntax"],
                    )
                    self.assertNotIn(
                        "missing-image-file",
                        {finding["code"] for finding in findings},
                    )

    def test_nonportable_separators_cannot_forge_a_fence_closer(self) -> None:
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
            root = Path(temporary)
            (root / "plot.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"
            for name, separator in separators.items():
                with self.subTest(name=name, codepoint=f"U+{ord(separator):04X}"):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"```\npayload{separator}```\n\n"
                        "Figure 1. Verified parser output.\n\n![plot](plot.svg)\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    findings = json.loads(result.stdout)["findings"]
                    self.assertEqual(
                        [finding["code"] for finding in findings],
                        ["noncanonical-image-syntax"],
                    )

    def test_portable_fence_closers_remain_conservative_before_image_credit(self) -> None:
        line_endings = {"lf": "\n", "crlf": "\r\n", "cr": "\r"}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "plot.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"
            for name, ending in line_endings.items():
                with self.subTest(name=name):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"```{ending}payload{ending}```{ending} \n"
                        "![plot](plot.svg)\n\nFigure 1. Verified parser output.\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertEqual(
                        [
                            finding["code"]
                            for finding in json.loads(result.stdout)["findings"]
                            if finding["code"] == "noncanonical-image-syntax"
                        ],
                        ["noncanonical-image-syntax"],
                    )

    def test_setext_and_type7_sequences_cannot_hide_an_unclosed_fence(self) -> None:
        probes = {
            "setext": "===\n<br>\n```\n\n![probe](existing.svg)\n",
            "blockquote-setext": "> quote\n===\n<br>\n```\n\n![probe](existing.svg)\n",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "existing.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"
            for name, probe in probes.items():
                with self.subTest(name=name):
                    report.write_text(
                        probe + "\nFigure 1. Existing parser output.\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    findings = json.loads(result.stdout)["findings"]
                    image_findings = [
                        finding
                        for finding in findings
                        if finding["code"] == "noncanonical-image-syntax"
                    ]
                    self.assertEqual(
                        [finding["code"] for finding in image_findings],
                        ["noncanonical-image-syntax", "noncanonical-image-syntax"],
                    )
                    self.assertNotIn(
                        "missing-image-file",
                        {finding["code"] for finding in findings},
                    )

    def test_link_definition_respects_existing_paragraph_state_and_blank_termination(self) -> None:
        hidden_probe = (
            "text\n[ref]: /url\n<br>\n```\n\n![probe](existing.svg)\n"
            "\nFigure 1. Existing parser output.\n"
        )
        visible_probe = (
            "[ref]: /url\n<br>\n\n![probe](existing.svg)\n"
            "\nFigure 1. Existing parser output.\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "existing.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"

            report.write_text(hidden_probe, encoding="utf-8")
            hidden = run_cli(
                "audit", "--file", str(report), "--mode", "concise-answer", "--json"
            )
            self.assertEqual(hidden.returncode, 1, hidden.stdout + hidden.stderr)
            hidden_findings = json.loads(hidden.stdout)["findings"]
            self.assertEqual(
                [
                    finding["code"]
                    for finding in hidden_findings
                    if finding["code"] == "noncanonical-image-syntax"
                ],
                ["noncanonical-image-syntax", "noncanonical-image-syntax"],
            )
            self.assertNotIn(
                "missing-image-file",
                {finding["code"] for finding in hidden_findings},
            )

            report.write_text(visible_probe, encoding="utf-8")
            visible = run_cli(
                "audit", "--file", str(report), "--mode", "concise-answer", "--json"
            )
            self.assertEqual(visible.returncode, 1, visible.stdout + visible.stderr)
            visible_findings = json.loads(visible.stdout)["findings"]
            self.assertEqual(
                [
                    finding["code"]
                    for finding in visible_findings
                    if finding["code"] == "noncanonical-image-syntax"
                ],
                ["noncanonical-image-syntax", "noncanonical-image-syntax"],
            )
            self.assertNotIn(
                "missing-image-file",
                {finding["code"] for finding in visible_findings},
            )

    def test_container_owned_fences_ignore_root_level_closer_lookalikes(self) -> None:
        probes = {
            "unordered-list": "- item\n  ```\n```\n\n![probe](existing.svg)\n",
            "ordered-list": "1. item\n   ~~~\n~~~\n\n![probe](existing.svg)\n",
            "empty-list": "-\n\n  ```\n\n![probe](existing.svg)\n",
            "empty-list-lazy-text": "-\ntext\n  ```\n\n![probe](existing.svg)\n",
            "dedented-blockquote": "- item\n> ~~~\n   ~~~~\n\n![probe](existing.svg)\n",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "existing.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"
            for name, probe in probes.items():
                with self.subTest(name=name):
                    report.write_text(
                        probe + "\nFigure 1. Existing parser output.\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    findings = json.loads(result.stdout)["findings"]
                    image_findings = [
                        finding
                        for finding in findings
                        if finding["code"] == "noncanonical-image-syntax"
                    ]
                    self.assertEqual(
                        [finding["code"] for finding in image_findings],
                        ["noncanonical-image-syntax"],
                    )
                    self.assertNotIn(
                        "missing-image-file",
                        {finding["code"] for finding in findings},
                    )

    def test_unsupported_type7_contexts_never_receive_required_image_credit(self) -> None:
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
            (root / "existing.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = root / "report.md"
            for name, probe in probes.items():
                with self.subTest(name=name):
                    report.write_text(probe, encoding="utf-8")
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    codes = {finding["code"] for finding in json.loads(result.stdout)["findings"]}
                    self.assertIn("noncanonical-image-syntax", codes)
                    self.assertNotIn("missing-image-file", codes)

    def test_true_comment_literal_is_a_conservative_noncanonical_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            report.write_text(
                "Outcome: Completed within the stated boundary.\n\n"
                "<!--\n![hidden](missing.png)\n-->\n",
                encoding="utf-8",
            )
            result = run_cli(
                "audit", "--file", str(report), "--mode", "concise-answer", "--json"
            )
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertNotIn("missing-image-file", codes)
            self.assertIn("noncanonical-image-syntax", codes)

    def test_inline_literals_stop_at_commonmark_inline_block_boundaries(self) -> None:
        visible = "![plot](missing.png)"
        visible_cases = {
            "code-blank-line": f"`open\n\n{visible}\n\nclose`",
            "code-heading": f"open `\n# heading\n{visible}\nclose `",
            "code-thematic-break": f"open `\n---\n{visible}\nclose `",
            "code-setext-h1": f"open `\n===\n{visible}\nclose `",
            "code-setext-h2": f"open `\n-\n{visible}\nclose `",
            "code-blockquote": f"open `\n> quote\n{visible}\nclose `",
            "code-list": f"open `\n- item\n{visible}\nclose `",
            "comment-blank-line": f"text <!-- open\n\n{visible}\n\nclose -->",
            "comment-heading": f"text <!-- open\n# heading\n{visible}\nclose -->",
        }
        literal_cases = {
            "code-softbreak": f"`open\n{visible}\nclose`",
            "comment-softbreak": f"text <!-- open\n{visible}\nclose -->",
            "block-comment": f"<!-- open\n\n{visible}\n\nclose -->",
        }
        image_codes = {"missing-image-file", "noncanonical-image-syntax"}
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            for name, content in visible_cases.items():
                with self.subTest(kind="visible", name=name):
                    report.write_text(content, encoding="utf-8")
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                    )
                    codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
                    self.assertTrue(codes & image_codes, codes)
            for name, content in literal_cases.items():
                with self.subTest(kind="literal", name=name):
                    report.write_text(content, encoding="utf-8")
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                    )
                    codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
                    self.assertIn("noncanonical-image-syntax", codes)
                    self.assertNotIn("missing-image-file", codes)

    def test_broad_image_gate_fails_closed_on_ambiguous_commonmark_contexts(self) -> None:
        image = "![plot](missing.png)"
        cases = {
            "link-destination-backtick": f"[x](https://x/`) {image} `",
            "link-title-backtick": f'[x](/url "`") {image} `',
            "autolink-backtick": f"<https://x/`> {image} `",
            "inline-pi-comment": f"text <?x <!-- ?>\n{image}\n-->",
            "inline-declaration-comment": f'text <!X "<!--" >\n{image}\n-->',
            "autolink-comment": f"text <https://x/<!-->\n{image}\n-->",
            "invalid-comment-short": f"<!-->\n{image}\n-->",
            "invalid-comment-dash": f"<!--->\n{image}\n-->",
            "raw-html-with-backslash": r"\<img src='missing.png' alt='plot'>",
            "raw-html-inside-code": r"`<img src='missing.png' alt='plot'>`",
        }
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            for name, content in cases.items():
                with self.subTest(name=name):
                    report.write_text(content, encoding="utf-8")
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                    )
                    self.assertEqual(result.returncode, 1)
                    codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
                    self.assertIn("noncanonical-image-syntax", codes)

    def test_audit_broad_gate_fails_closed_on_common_raw_visual_tags(self) -> None:
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
            report = Path(temporary) / "report.md"
            for tag, raw_visual in raw_visuals.items():
                with self.subTest(tag=tag):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"{raw_visual}\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    codes = {finding["code"] for finding in json.loads(result.stdout)["findings"]}
                    self.assertIn("noncanonical-image-syntax", codes)

    def test_audit_broad_gate_covers_all_raw_opening_tags_but_not_encoded_literals(self) -> None:
        raw_opening_tags = {
            "styled-div": '<div style="background-image:url(plot.svg)"></div>',
            "harmless-break": "<br>",
        }
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            for tag, raw_html in raw_opening_tags.items():
                with self.subTest(kind="raw", tag=tag):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"{raw_html}\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--json"
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    codes = {finding["code"] for finding in json.loads(result.stdout)["findings"]}
                    self.assertIn("noncanonical-image-syntax", codes)

            report.write_text(
                "Outcome: Completed within the stated boundary.\n\n"
                '&lt;div style="background-image:url(plot.svg)"&gt;\n',
                encoding="utf-8",
            )
            encoded = run_cli(
                "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
            )
            self.assertEqual(encoded.returncode, 0, encoded.stdout + encoded.stderr)
            self.assertEqual(json.loads(encoded.stdout)["findings"], [])

    def test_audit_raw_tag_gate_does_not_misclassify_uri_autolinks(self) -> None:
        autolinks = (
            "<https://example.com/report>",
            "<mailto:user@example.com>",
            "<urn:isbn:9780131103627>",
        )
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            for autolink in autolinks:
                with self.subTest(kind="autolink", autolink=autolink):
                    report.write_text(
                        "Outcome: Completed within the stated boundary.\n\n"
                        f"Evidence: {autolink}\n",
                        encoding="utf-8",
                    )
                    result = run_cli(
                        "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    codes = {finding["code"] for finding in json.loads(result.stdout)["findings"]}
                    self.assertNotIn("noncanonical-image-syntax", codes)

            report.write_text(
                "Outcome: Completed within the stated boundary.\n\n"
                '<x-report style="background-image:url(plot.svg)"></x-report>\n',
                encoding="utf-8",
            )
            custom_tag = run_cli(
                "audit", "--file", str(report), "--mode", "concise-answer", "--json"
            )
            self.assertEqual(custom_tag.returncode, 1, custom_tag.stdout + custom_tag.stderr)
            custom_codes = {
                finding["code"] for finding in json.loads(custom_tag.stdout)["findings"]
            }
            self.assertIn("noncanonical-image-syntax", custom_codes)

    def test_html_block_blank_line_restores_image_scanning_while_raw_tag_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "plot.svg").write_text(
                "<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>",
                encoding="utf-8",
            )
            report = root / "report.md"
            report.write_text(
                "Outcome: Completed within the stated boundary.\n\n"
                "<div>\nraw html\n\n"
                "Figure 1. Verified output.\n\n![plot](plot.svg)\n",
                encoding="utf-8",
            )
            result = run_cli(
                "audit", "--file", str(report), "--mode", "concise-answer", "--strict", "--json"
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            findings = json.loads(result.stdout)["findings"]
            self.assertEqual(
                [finding["code"] for finding in findings],
                ["noncanonical-image-syntax"],
            )

    def test_all_human_and_json_output_surfaces_escape_terminal_controls(self) -> None:
        route = run_cli(
            "route", "--task", "Summarize", "--audience", "team\x1bc\u202e",
            "--must-show", "boundary\x7f",
        )
        self.assertEqual(route.returncode, 0, route.stderr)
        self.assert_terminal_safe(route.stdout)
        self.assertIn(r"\x1b", route.stdout)
        self.assertIn(r"\x7f", route.stdout)
        self.assertIn(r"\u202e", route.stdout)

        route_json = run_cli(
            "route", "--task", "Summarize", "--audience", "中文\x7f\u202e", "--json",
        )
        self.assertEqual(route_json.returncode, 0, route_json.stderr)
        self.assert_terminal_safe(route_json.stdout)
        self.assertEqual(json.loads(route_json.stdout)["audience"], "中文\x7f\u202e")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / "report.json"
            payload = self.valid_spec()
            payload["headline"] = "Parser complete\x1bc"
            payload["claims"][0]["text"] = "Verified claim\u202e"  # type: ignore[index]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            rendered = run_cli("render", "--file", str(spec))
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assert_terminal_safe(rendered.stdout)
            self.assertIn(r"\x1b", rendered.stdout)
            self.assertIn(r"\u202e", rendered.stdout)

            report = root / "unsafe.md"
            report.write_text(
                "# Result\n\nCompleted with a boundary.\n\n"
                "Figure 1. Output.\n\n![plot](missing\x1bc.png)\n",
                encoding="utf-8",
            )
            audited = run_cli("audit", "--file", str(report), "--mode", "concise-answer")
            self.assertEqual(audited.returncode, 1)
            self.assert_terminal_safe(audited.stdout)
            self.assertIn(r"\x1b", audited.stdout)

            invalid = self.valid_spec()
            invalid["unknown\x1bc"] = True
            spec.write_text(json.dumps(invalid), encoding="utf-8")
            validated = run_cli("validate-spec", "--file", str(spec))
            self.assertEqual(validated.returncode, 1)
            self.assert_terminal_safe(validated.stdout)

        missing = run_cli("validate-spec", "--file", "missing\x1bc.json")
        self.assertEqual(missing.returncode, 2)
        self.assert_terminal_safe(missing.stderr)

        newline_path = run_cli(
            "validate-spec", "--file", "missing\nFAKE-SUCCESS.json"
        )
        self.assertEqual(newline_path.returncode, 2)
        self.assertNotIn("\nFAKE-SUCCESS", newline_path.stderr)
        self.assertIn(r"\nFAKE-SUCCESS", newline_path.stderr)

        argparse_error = run_cli("scaffold", "--mode", "bad\x1bc")
        self.assertEqual(argparse_error.returncode, 2)
        self.assert_terminal_safe(argparse_error.stderr)

        newline_argument = run_cli("list", "--bad\nFAKE-SUCCESS")
        self.assertEqual(newline_argument.returncode, 2)
        self.assertNotIn("\nFAKE-SUCCESS", newline_argument.stderr)
        self.assertIn(r"\nFAKE-SUCCESS", newline_argument.stderr)

    def test_audit_rejects_oversized_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "large.md"
            report.write_text("x" * (4 * 1024 * 1024 + 1), encoding="utf-8")
            result = run_cli("audit", "--file", str(report), "--mode", "concise-answer")
            self.assertEqual(result.returncode, 2)
            self.assertIn("limit", result.stderr)

    def test_audit_rejects_excessive_line_count_without_expanding_structures(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "many-lines.md"
            report.write_text("x\n" * 100_001, encoding="utf-8")
            result = run_cli("audit", "--file", str(report), "--mode", "concise-answer", "--json")
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual([item["code"] for item in payload["findings"]], ["report-line-limit"])

    def test_build_dist_creates_one_file_per_route_and_module(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "dist"
            result = run_cli("build-dist", "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(len(list((output / "routes").glob("*.md"))), 11)
            self.assertEqual(len(list((output / "modules").glob("*.md"))), 5)
            self.assertTrue((output / "agent-index.md").is_file())
            self.assertTrue((output / ".agentic-reporting-dist.json").is_file())

    def test_build_dist_preflights_existing_outputs_without_partial_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "dist"
            routes = output / "routes"
            routes.mkdir(parents=True)
            sentinel = routes / "status-update.md"
            sentinel.write_text("keep", encoding="utf-8")
            result = run_cli("build-dist", "--output", str(output))
            self.assertEqual(result.returncode, 2)
            self.assertIn("already contains generated files", result.stderr)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
            self.assertEqual(list(routes.iterdir()), [sentinel])

    def test_build_dist_force_removes_only_manifest_tracked_stale_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "dist"
            created = run_cli("build-dist", "--output", str(output))
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            stale = output / "routes" / "legacy-mode.md"
            stale.write_text("old generated route", encoding="utf-8")
            untracked = output / "routes" / "user-note.txt"
            untracked.write_text("keep", encoding="utf-8")
            manifest_path = output / ".agentic-reporting-dist.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["generated_files"].append("routes/legacy-mode.md")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            rebuilt = run_cli("build-dist", "--output", str(output), "--force")
            self.assertEqual(rebuilt.returncode, 0, rebuilt.stdout + rebuilt.stderr)
            self.assertFalse(stale.exists())
            self.assertEqual(untracked.read_text(encoding="utf-8"), "keep")

    def test_build_dist_preflights_stale_type_without_partial_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "dist"
            created = run_cli("build-dist", "--output", str(output))
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            sentinel = output / "routes" / "concise-answer.md"
            sentinel.write_text("SENTINEL\n", encoding="utf-8")
            stale = output / "routes" / "legacy.md"
            stale.mkdir()
            manifest_path = output / ".agentic-reporting-dist.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["generated_files"].append("routes/legacy.md")
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            before = {
                path.relative_to(output): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }

            rebuilt = run_cli("build-dist", "--output", str(output), "--force")
            self.assertEqual(rebuilt.returncode, 2)
            self.assertIn("stale output is not a regular file", rebuilt.stderr)
            after = {
                path.relative_to(output): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, before)
            self.assertTrue(stale.is_dir())

    def test_build_dist_permission_failure_does_not_partially_refresh(self) -> None:
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.skipTest("permission-mode reproduction is not meaningful as root")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "dist"
            created = run_cli("build-dist", "--output", str(output))
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            sentinel = output / "routes" / "concise-answer.md"
            sentinel.write_text("SENTINEL\n", encoding="utf-8")
            before = {
                path.relative_to(output): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
            module_dir = output / "modules"
            original_mode = module_dir.stat().st_mode & 0o777
            module_dir.chmod(0o555)
            try:
                rebuilt = run_cli("build-dist", "--output", str(output), "--force")
            finally:
                module_dir.chmod(original_mode)
            self.assertEqual(rebuilt.returncode, 2)
            self.assertIn("stage distribution", rebuilt.stderr)
            after = {
                path.relative_to(output): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, before)

    def test_build_dist_commit_failure_rolls_back_replaced_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "dist"
            created = run_cli("build-dist", "--output", str(output))
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            targets = [
                output / "routes" / "concise-answer.md",
                output / "routes" / "status-update.md",
            ]
            targets[0].write_text("SENTINEL\n", encoding="utf-8")
            before = {path: (path.read_bytes(), path.stat().st_mode & 0o777) for path in targets}
            namespace = runpy.run_path(str(CLI), run_name="reportctl_transaction_test")
            real_replace = os.replace
            replace_calls = 0

            def fail_second_replace(source: object, destination: object) -> None:
                nonlocal replace_calls
                replace_calls += 1
                if replace_calls == 2:
                    raise PermissionError("injected commit failure")
                real_replace(source, destination)

            with mock.patch.object(namespace["os"], "replace", side_effect=fail_second_replace):
                with self.assertRaises(namespace["ReportCtlError"]):
                    namespace["_transactional_distribution_write"](
                        [(targets[0], "NEW-ONE\n"), (targets[1], "NEW-TWO\n")],
                        [],
                    )
            after = {path: (path.read_bytes(), path.stat().st_mode & 0o777) for path in targets}
            self.assertEqual(after, before)
            self.assertEqual(list(Path(temporary).glob(".agentic-reporting-dist-*")), [])

    def test_build_dist_supports_new_nested_parents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "new" / "nested" / "dist"
            result = run_cli("build-dist", "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((output / "agent-index.md").is_file())
            self.assertTrue((output / ".agentic-reporting-dist.json").is_file())
            self.assertEqual(len(list((output / "routes").glob("*.md"))), 11)
            self.assertEqual(len(list((output / "modules").glob("*.md"))), 5)

    def test_build_dist_nested_commit_failure_removes_new_parents_and_staging(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            distribution = root / "new" / "nested" / "dist"
            outputs = [
                (distribution / "routes" / "one.md", "ONE\n"),
                (distribution / "modules" / "two.md", "TWO\n"),
            ]
            namespace = runpy.run_path(str(CLI), run_name="reportctl_nested_transaction_test")
            real_replace = os.replace
            replace_calls = 0

            def fail_second_replace(source: object, destination: object) -> None:
                nonlocal replace_calls
                replace_calls += 1
                if replace_calls == 2:
                    raise PermissionError("injected nested commit failure")
                real_replace(source, destination)

            with mock.patch.object(namespace["os"], "replace", side_effect=fail_second_replace):
                with self.assertRaises(namespace["ReportCtlError"]):
                    namespace["_transactional_distribution_write"](outputs, [])
            self.assertFalse((root / "new").exists())
            self.assertEqual(list(root.glob(".agentic-reporting-dist-*")), [])

    def test_build_dist_preflights_late_symlink_without_writing_early_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "dist"
            output.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (output / "modules").symlink_to(outside, target_is_directory=True)
            result = run_cli("build-dist", "--output", str(output), "--force")
            self.assertEqual(result.returncode, 2)
            self.assertIn("symlink component", result.stderr)
            self.assertFalse((output / "routes").exists())
            self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
