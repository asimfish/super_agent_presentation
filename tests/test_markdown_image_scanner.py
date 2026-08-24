from __future__ import annotations

import ast
import importlib.util
import json
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCANNER = (
    ROOT
    / "skills"
    / "agentic-reporting"
    / "scripts"
    / "markdown_image_scanner.py"
)
REPORTCTL = ROOT / "skills" / "agentic-reporting" / "scripts" / "reportctl.py"
BENCHMARK = ROOT / "scripts" / "presentation_benchmark.py"
INSTALLER = ROOT / "scripts" / "install.py"

SCANNER_ENGINE_HELPERS = {
    "_commonmark_blank_line",
    "_commonmark_image_block_mask",
    "_commonmark_list_content_indent",
    "_first_fence_like_run",
    "_first_type7_html_tag_marker",
    "_is_canonical_image_position",
    "_markdown_character_is_escaped",
    "_markdown_range_has_unescaped",
    "_portable_markdown_line_ranges",
    "_potential_markdown_image_starts",
    "_potential_raw_html_opening_tags",
    "_skip_markdown_link_whitespace",
}


def load_scanner_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCANNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load shared Markdown image scanner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def top_level_definitions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }


class MarkdownImageScannerContractTests(unittest.TestCase):
    maxDiff = None

    def test_public_contract_loads_by_direct_import_and_runpy(self) -> None:
        namespaces = (
            vars(load_scanner_module("agentic_reporting_scanner_contract_test")),
            runpy.run_path(str(SCANNER), run_name="scanner_runpy_contract_test"),
        )
        source = "![Result &copy;](plot.svg)"

        for namespace in namespaces:
            with self.subTest(loader=namespace["__name__"]):
                candidate_type = namespace["MarkdownImageCandidate"]
                self.assertEqual(
                    candidate_type._fields,
                    ("alt", "target", "start", "end", "canonical"),
                )
                records = namespace["scan_markdown_images"](
                    source,
                    record_limit=4,
                )
                self.assertEqual(len(records), 1)
                self.assertIsInstance(records[0], candidate_type)
                self.assertEqual(
                    tuple(records[0]),
                    ("Result ©", "plot.svg", 0, len(source), True),
                )
                self.assertEqual(
                    namespace["decode_commonmark_entities"]("&copy; &#169; &#xA9;"),
                    "© © ©",
                )
                self.assertEqual(
                    namespace["decode_commonmark_entities"](
                        r"\&copy; \&#169; \&#xA9; \\&copy; \\&#169; \\&#xA9;"
                    ),
                    r"\&copy; \&#169; \&#xA9; \\© \\© \\©",
                )
                self.assertFalse(namespace["has_visible_alt_text"](" \t\n"))
                self.assertTrue(namespace["has_visible_alt_text"]("©"))

    def test_shared_scanner_and_compatibility_wrappers_have_exact_parity(self) -> None:
        scanner = load_scanner_module("agentic_reporting_scanner_parity_test")
        reportctl = runpy.run_path(str(REPORTCTL), run_name="reportctl_scanner_parity_test")
        benchmark = runpy.run_path(str(BENCHMARK), run_name="benchmark_scanner_parity_test")
        text = (
            "![Alpha &copy;](alpha.svg)\n\n"
            "`![inline literal](ignored.svg)`\n\n"
            "<!-- ![comment literal](hidden.svg) -->\n\n"
            "<img src=\"raw.png\">\n\n"
            '![escaped \\] alt](beta.png "held-out result")\n\n'
            "![unterminated"
        )

        shared_records = scanner.scan_markdown_images(text, record_limit=1_001)
        shared_five_tuples = [tuple(record) for record in shared_records]
        reportctl_records = [
            tuple(record) for record in reportctl["_scan_markdown_images"](text)
        ]
        benchmark_records = benchmark["markdown_images"](text)

        self.assertEqual(reportctl_records, shared_five_tuples)
        self.assertEqual(
            benchmark_records,
            [
                (record.alt, record.target, record.canonical)
                for record in shared_records
            ],
        )
        self.assertEqual(
            [record.start for record in shared_records],
            sorted(record.start for record in shared_records),
        )

    def test_record_limit_caps_merged_candidates_without_changing_source_order(self) -> None:
        scanner = load_scanner_module("agentic_reporting_scanner_cap_test")
        reportctl = runpy.run_path(str(REPORTCTL), run_name="reportctl_scanner_cap_test")
        text = (
            "![one](one.svg)\n"
            "<x>\n"
            "![two](two.svg)\n"
            "<y>\n"
            "![three](three.svg)\n"
        )
        expected_starts = [
            text.index("![one"),
            text.index("<x>"),
            text.index("![two"),
        ]

        shared_records = scanner.scan_markdown_images(text, record_limit=3)

        self.assertEqual(len(shared_records), 3)
        self.assertEqual([record.start for record in shared_records], expected_starts)
        self.assertEqual(
            [tuple(record) for record in shared_records],
            [tuple(record) for record in reportctl["_scan_markdown_images"](text, 3)],
        )

    def test_installed_audit_loads_scanner_from_outside_repository_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = base / "project"
            project.mkdir()
            (project / ".git").mkdir()
            installed = subprocess.run(
                [
                    sys.executable,
                    str(INSTALLER),
                    "apply",
                    "--target",
                    str(project),
                    "--host",
                    "agents",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)

            skill_scripts = project / ".agents" / "skills" / "agentic-reporting" / "scripts"
            installed_cli = skill_scripts / "reportctl.py"
            installed_scanner = skill_scripts / "markdown_image_scanner.py"
            self.assertTrue(installed_scanner.is_file())
            (project / "plot.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                encoding="utf-8",
            )
            report = project / "report.md"
            report.write_text(
                "Outcome: Completed within the stated boundary.\n\n"
                "Figure 1. Verified parser output.\n\n"
                "![plot](plot.svg)\n",
                encoding="utf-8",
            )
            outside_cwd = base / "outside-cwd"
            outside_cwd.mkdir()
            environment = os.environ.copy()
            environment.pop("PYTHONPATH", None)

            # A command that does not scan Markdown must remain usable without
            # importing the optional scanner sibling.
            parked_scanner = skill_scripts / "markdown_image_scanner.py.parked"
            installed_scanner.replace(parked_scanner)
            try:
                listed = subprocess.run(
                    [sys.executable, "-I", str(installed_cli), "list", "--json"],
                    cwd=outside_cwd,
                    env=environment,
                    text=True,
                    capture_output=True,
                    check=False,
                )
            finally:
                parked_scanner.replace(installed_scanner)
            self.assertEqual(listed.returncode, 0, listed.stdout + listed.stderr)

            audited = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    str(installed_cli),
                    "audit",
                    "--file",
                    str(report),
                    "--mode",
                    "concise-answer",
                    "--strict",
                    "--json",
                ],
                cwd=outside_cwd,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(audited.returncode, 0, audited.stdout + audited.stderr)
            self.assertEqual(json.loads(audited.stdout)["findings"], [])

    def test_consumers_keep_only_thin_wrappers_not_scanner_engine_helpers(self) -> None:
        shared_definitions = top_level_definitions(SCANNER)
        reportctl_definitions = top_level_definitions(REPORTCTL)
        benchmark_definitions = top_level_definitions(BENCHMARK)

        self.assertIn("MarkdownImageCandidate", shared_definitions)
        self.assertIn("scan_markdown_images", shared_definitions)
        self.assertIn("decode_commonmark_entities", shared_definitions)
        self.assertIn("has_visible_alt_text", shared_definitions)
        self.assertIn("_scan_markdown_images", reportctl_definitions)
        self.assertIn("markdown_images", benchmark_definitions)

        for consumer, definitions in (
            (REPORTCTL, reportctl_definitions),
            (BENCHMARK, benchmark_definitions),
        ):
            with self.subTest(consumer=consumer.relative_to(ROOT)):
                self.assertEqual(
                    definitions & SCANNER_ENGINE_HELPERS,
                    set(),
                    "scanner engine helpers must have one implementation in "
                    "markdown_image_scanner.py",
                )
                self.assertNotIn("_decode_commonmark_entities", definitions)
                self.assertNotIn("_has_visible_alt_text", definitions)


if __name__ == "__main__":
    unittest.main()
