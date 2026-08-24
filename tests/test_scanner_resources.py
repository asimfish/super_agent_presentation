from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTCTL = ROOT / "skills" / "agentic-reporting" / "scripts" / "reportctl.py"
SCANNERS = (
    (REPORTCTL, "_scan_markdown_images"),
    (ROOT / "scripts" / "presentation_benchmark.py", "markdown_images"),
)


class ScannerResourceTests(unittest.TestCase):
    def test_four_megabyte_inline_code_scan_has_bounded_peak_memory(self) -> None:
        probe = """
import json
import resource
import runpy
import sys
import time

namespace = runpy.run_path(sys.argv[1], run_name="scanner_resource_probe")
text = "`a" * 2_097_152
started = time.perf_counter()
images = namespace[sys.argv[2]](text)
elapsed = time.perf_counter() - started
raw_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
peak_bytes = raw_peak if sys.platform == "darwin" else raw_peak * 1_024
print(json.dumps({"elapsed": elapsed, "images": len(images), "peak_bytes": peak_bytes}))
"""
        for script, function_name in SCANNERS:
            with self.subTest(scanner=script.name):
                try:
                    completed = subprocess.run(
                        [sys.executable, "-c", probe, str(script), function_name],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                        timeout=15,
                    )
                except subprocess.TimeoutExpired as exc:
                    self.fail(f"{script.name} exceeded the 15-second resource ceiling: {exc}")
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                result = json.loads(completed.stdout)
                self.assertEqual(result["images"], 0)
                self.assertLess(result["elapsed"], 10)
                self.assertLess(
                    result["peak_bytes"],
                    192 * 1_024 * 1_024,
                    f"{script.name} peak memory was {result['peak_bytes']} bytes",
                )

    def test_four_megabyte_checkpoint_prose_mask_is_resource_bounded(self) -> None:
        probe = """
import json
import resource
import runpy
import sys
import time

namespace = runpy.run_path(sys.argv[1], run_name="checkpoint_mask_resource_probe")
text = "`a" * 2_097_152
started = time.perf_counter()
findings = namespace["_checkpoint_must_show_findings"](text, ["Visible result"])
elapsed = time.perf_counter() - started
raw_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
peak_bytes = raw_peak if sys.platform == "darwin" else raw_peak * 1_024
print(json.dumps({"elapsed": elapsed, "findings": findings, "peak_bytes": peak_bytes}))
"""
        try:
            completed = subprocess.run(
                [sys.executable, "-c", probe, str(REPORTCTL)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                timeout=15,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(f"checkpoint prose masking exceeded the 15-second ceiling: {exc}")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(
            [finding["code"] for finding in result["findings"]],
            ["missing-must-show"],
        )
        self.assertLess(result["elapsed"], 10)
        self.assertLess(result["peak_bytes"], 192 * 1_024 * 1_024)

    def test_checkpoint_rejects_adversarial_combining_runs_before_nfc(self) -> None:
        probe = """
import json
import resource
import runpy
import sys
import time

namespace = runpy.run_path(sys.argv[1], run_name="checkpoint_nfc_resource_probe")
marks = "\u0345\u035d\u035c\u0315\u0300\u0316\u031b\u0327\u0334"
text = "Visible result " + (marks * 12_000)
started = time.perf_counter()
findings = namespace["_checkpoint_must_show_findings"](text, ["Visible result"])
elapsed = time.perf_counter() - started
raw_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
peak_bytes = raw_peak if sys.platform == "darwin" else raw_peak * 1_024
print(json.dumps({"elapsed": elapsed, "findings": findings, "peak_bytes": peak_bytes}))
"""
        try:
            completed = subprocess.run(
                [sys.executable, "-c", probe, str(REPORTCTL)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(f"checkpoint NFC guard exceeded the 10-second ceiling: {exc}")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(
            [finding["code"] for finding in result["findings"]],
            ["checkpoint-prose-paragraph-limit", "missing-must-show"],
        )
        self.assertLess(result["elapsed"], 5)
        self.assertLess(result["peak_bytes"], 128 * 1_024 * 1_024)

    def test_checkpoint_rejects_decomposable_mark_runs_before_nfc(self) -> None:
        probe = """
import json
import runpy
import sys
import time

namespace = runpy.run_path(sys.argv[1], run_name="checkpoint_mark_run_probe")
text = "Visible result " + ("\u0f73\u0300" * 40)
started = time.perf_counter()
findings = namespace["_checkpoint_must_show_findings"](text, ["Visible result"])
elapsed = time.perf_counter() - started
print(json.dumps({"elapsed": elapsed, "findings": findings}))
"""
        completed = subprocess.run(
            [sys.executable, "-c", probe, str(REPORTCTL)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(
            [finding["code"] for finding in result["findings"]],
            ["excessive-combining-sequence", "missing-must-show"],
        )
        self.assertLess(result["elapsed"], 2)


if __name__ == "__main__":
    unittest.main()
