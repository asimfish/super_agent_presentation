from __future__ import annotations

from html.parser import HTMLParser
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "agentic-reporting"
CATALOG = SKILL / "references" / "protocols.json"
ACADEMIC_TALK = SKILL / "assets" / "presentations" / "academic-talk.html"
PLACEHOLDER = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
PRINT_TITLE_SAFE_LEFT_PT = 60.0


def _chrome_binary() -> str | None:
    configured = os.environ.get("CHROME_BIN")
    candidates = [
        configured,
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    return None


def _filled_academic_talk() -> str:
    values = {
        "TALK_TITLE": "SparseGate 端侧实验：速度与准确率的证据边界",
        "CURRENT_LIMIT_ASSERTION": "当前证据只覆盖设备 X、batch=1 的有限测量",
        "MECHANISM_ASSERTION": "视觉策略 VLA-Adapter 在跨域部署中的 evidence boundary",
        "COMPARABILITY_ASSERTION": "协议差异必须在结果比较之前明确展示",
        "MAIN_RESULT_ASSERTION": "平均延迟下降伴随着准确率降低",
        "BOUNDARY_ASSERTION": "现有证据不能证明能耗、机制或外部最佳水平",
        "FINAL_TAKEAWAY": "保留速度与准确率的权衡，并补齐决定性证据",
        "VALUE_1": "82 ms",
        "VALUE_2": "72.9",
        "N": "3",
    }
    source = ACADEMIC_TALK.read_text(encoding="utf-8")
    rendered = PLACEHOLDER.sub(
        lambda match: values.get(match.group(1), "已填充的本地测试内容"),
        source,
    )
    if PLACEHOLDER.search(rendered):
        raise AssertionError("filled academic-talk fixture retained a placeholder")
    return rendered


def _run_checked(arguments: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        arguments,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"command failed ({completed.returncode}): {' '.join(arguments)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def _ppm_tokens(path: Path) -> tuple[int, int, bytes]:
    with path.open("rb") as handle:
        def token() -> bytes:
            while True:
                value = handle.readline()
                if not value:
                    raise AssertionError(f"truncated PPM header: {path}")
                value = value.strip()
                if value and not value.startswith(b"#"):
                    return value

        if token() != b"P6":
            raise AssertionError(f"expected binary PPM: {path}")
        dimensions = token().split()
        if len(dimensions) != 2:
            raise AssertionError(f"invalid PPM dimensions: {path}")
        width, height = (int(value) for value in dimensions)
        if token() != b"255":
            raise AssertionError(f"unsupported PPM channel range: {path}")
        pixels = handle.read()
    if len(pixels) != width * height * 3:
        raise AssertionError(f"truncated PPM pixels: {path}")
    return width, height, pixels


class _DeckParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.slide_labels: list[str] = []
        self.remote_dependencies: list[str] = []
        self.slide_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.append(str(attributes["id"]))
        classes = set((attributes.get("class") or "").split())
        if tag == "section" and "slide" in classes:
            self.slide_count += 1
            if attributes.get("aria-labelledby"):
                self.slide_labels.append(str(attributes["aria-labelledby"]))
        for key in ("src", "href"):
            value = attributes.get(key)
            if value and urlsplit(value).scheme in {"http", "https"}:
                self.remote_dependencies.append(value)


class TemplateAssetTests(unittest.TestCase):
    def test_registered_template_paths_are_unique_regular_skill_assets(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        paths = [record["path"] for record in catalog["templates"].values()]
        self.assertEqual(len(paths), len(set(paths)))
        for relative in paths:
            with self.subTest(relative=relative):
                path = (SKILL / relative).resolve(strict=True)
                self.assertIn(SKILL.resolve(), path.parents)
                self.assertTrue(path.is_file())

    def test_dependency_free_html_deck_has_accessible_slide_links(self) -> None:
        path = ACADEMIC_TALK
        parser = _DeckParser()
        source = path.read_text(encoding="utf-8")
        parser.feed(source)
        self.assertEqual(parser.slide_count, 7)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertTrue(set(parser.slide_labels).issubset(set(parser.ids)))
        self.assertEqual(parser.remote_dependencies, [])
        self.assertIn(".grid-2 > * { min-width: 0; }", source)
        self.assertIn(".slide:last-child { break-after: auto; }", source)
        self.assertIn(".slide--results .grid-2", source)

    def test_filled_html_deck_print_keeps_long_titles_inside_safe_area(self) -> None:
        chrome = _chrome_binary()
        required_tools = {
            name: shutil.which(name) for name in ("pdfinfo", "pdftotext", "pdftoppm")
        }
        if chrome is None or any(path is None for path in required_tools.values()):
            self.skipTest("Chrome and Poppler are required for the print-layout regression")

        with tempfile.TemporaryDirectory(prefix="academic-talk-print-") as temporary:
            root = Path(temporary)
            html = root / "filled-academic-talk.html"
            pdf = root / "filled-academic-talk.pdf"
            bbox = root / "filled-academic-talk.xml"
            html.write_text(_filled_academic_talk(), encoding="utf-8")

            _run_checked(
                [
                    chrome,
                    "--headless=new",
                    "--disable-gpu",
                    "--disable-background-networking",
                    "--disable-component-update",
                    "--disable-sync",
                    "--metrics-recording-only",
                    "--no-first-run",
                    "--disable-default-apps",
                    "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}",
                    html.as_uri(),
                ]
            )
            metadata = _run_checked([str(required_tools["pdfinfo"]), str(pdf)]).stdout
            self.assertRegex(metadata, r"(?m)^Pages:\s+7$")
            self.assertRegex(metadata, r"(?m)^Page size:\s+1152 x 648 pts")

            _run_checked(
                [
                    str(required_tools["pdftotext"]),
                    "-bbox-layout",
                    str(pdf),
                    str(bbox),
                ]
            )
            document = ElementTree.parse(bbox)
            words = [
                (element.text or "", float(element.attrib["xMin"]))
                for element in document.iter()
                if element.tag.rsplit("}", 1)[-1] == "word"
            ]
            for prefix in ("当前证据", "视觉策略"):
                matches = [x_min for text, x_min in words if text.startswith(prefix)]
                self.assertEqual(len(matches), 1, f"printed title prefix not found: {prefix}")
                self.assertGreaterEqual(
                    matches[0],
                    PRINT_TITLE_SAFE_LEFT_PT,
                    f"printed title lacks left ink guard: {prefix}",
                )

            raster_prefix = root / "slide"
            _run_checked(
                [
                    str(required_tools["pdftoppm"]),
                    "-f",
                    "1",
                    "-l",
                    "7",
                    "-r",
                    "72",
                    str(pdf),
                    str(raster_prefix),
                ]
            )
            pages = sorted(root.glob("slide-*.ppm"))
            self.assertEqual(len(pages), 7)
            for page in pages:
                width, height, pixels = _ppm_tokens(page)
                self.assertEqual((width, height), (1152, 648))
                dark_pixels = 0
                dark_border_pixels = 0
                for y in range(height):
                    for x in range(width):
                        offset = (y * width + x) * 3
                        red, green, blue = pixels[offset : offset + 3]
                        if max(red, green, blue) < 120:
                            dark_pixels += 1
                            if x < 2 or x >= width - 2 or y < 2 or y >= height - 2:
                                dark_border_pixels += 1
                self.assertGreater(dark_pixels, 100, f"rendered page is unexpectedly blank: {page.name}")
                self.assertEqual(
                    dark_border_pixels,
                    0,
                    f"rendered content touches the physical page edge: {page.name}",
                )

    def test_revealjs_source_is_self_contained_and_evidence_bounded(self) -> None:
        source = (
            SKILL / "assets" / "presentations" / "academic-talk-revealjs.qmd"
        ).read_text(encoding="utf-8")
        self.assertIn("format:\n  revealjs:", source)
        self.assertIn("embed-resources: true", source)
        self.assertIn("bibliography: references.bib", source)
        self.assertIn("Observed exceptions", source)
        self.assertIn("Not established", source)

    def test_domain_templates_keep_protocol_and_boundary_fields(self) -> None:
        requirements = {
            "rl-experiment-report.md": ("Seeds/runs", "tuning", "failure"),
            "embodied-experiment-report.md": ("Reset/retry", "Interventions", "Failure"),
            "world-model-experiment-report.md": ("Open-loop", "Closed-loop", "compounding"),
            "vla-experiment-report.md": ("Rollouts/task", "Control rate", "safety"),
        }
        root = SKILL / "assets" / "templates"
        for filename, terms in requirements.items():
            with self.subTest(filename=filename):
                text = (root / filename).read_text(encoding="utf-8").casefold()
                for term in terms:
                    self.assertIn(term.casefold(), text)


if __name__ == "__main__":
    unittest.main()
