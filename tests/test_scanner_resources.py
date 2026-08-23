from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCANNERS = (
    (ROOT / "skills" / "agentic-reporting" / "scripts" / "reportctl.py", "_scan_markdown_images"),
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


if __name__ == "__main__":
    unittest.main()
