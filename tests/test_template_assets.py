from __future__ import annotations

from html.parser import HTMLParser
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "agentic-reporting"
CATALOG = SKILL / "references" / "protocols.json"


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
        path = SKILL / "assets" / "presentations" / "academic-talk.html"
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
