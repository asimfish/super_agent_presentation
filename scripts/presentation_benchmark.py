#!/usr/bin/env python3
"""Deterministic evaluation harness for agentic-reporting presentation cases.

The checked-in smoke suite evaluates known-good and intentionally mutated fixtures.
It never calls a model and therefore cannot establish framework effectiveness.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import stat
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit


REPO_ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = REPO_ROOT / "evals" / "presentation-cases.json"
ACTIVATION_PATH = REPO_ROOT / "skills" / "agentic-reporting" / "evals" / "activation.json"
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "responses"
REPORTCTL_PATH = REPO_ROOT / "skills" / "agentic-reporting" / "scripts" / "reportctl.py"
MODE_IDS = {
    "concise-answer", "implementation-handoff", "status-update", "investigation-report",
    "experiment-report", "decision-brief", "academic-synthesis", "research-idea", "review-report",
    "incident-update", "postmortem", "risk-report",
}
# Kept in sync with reportctl.MODULE_IDS by a drift test; the harness never imports
# reportctl so that a broken skill cannot take the evaluator down with it.
MODULE_IDS = {
    "visuals", "tables", "conclusions", "evidence", "academic-display",
    "ablation", "benchmarking", "natural-tone",
}
PROFILE_IDS = {"reinforcement-learning", "embodied-ai", "world-models", "vla"}
ACTIVATION_CATEGORIES = {
    "explicit_positive", "natural_positive", "adjacent_negative", "explicit_exclusion",
}
POSITIVE_ACTIVATION_CATEGORIES = {"explicit_positive", "natural_positive"}
ACTIVATION_RUBRICS = {"security", "correctness", "discoverability", "effectiveness", "efficiency"}
RUBRIC_ASSESSMENTS = {
    "host_or_human", "host_observation", "human_comparative", "local_proxy_plus_telemetry",
}
DISCLAIMER = (
    "Harness-only result: no real model was run, so this result cannot support "
    "a claim that the framework improves agent reports."
)
REGEX_FLAGS = re.IGNORECASE | re.MULTILINE | re.DOTALL
MAX_BENCHMARK_BYTES = 2 * 1024 * 1024
MAX_JSON_NUMBER_CHARS = 128
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_RESPONSE_LINES = 100_000
RENDERABLE_IMAGE_SUFFIXES = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
UNSAFE_MARKDOWN_FORMAT_CONTROLS = frozenset(
    {
        0x061C, 0x200E, 0x200F, 0x2028, 0x2029,
        *range(0x202A, 0x202F), *range(0x2066, 0x206A),
    }
)


class BenchmarkError(ValueError):
    """Raised for invalid benchmark data or CLI inputs."""


_MARKDOWN_IMAGE_SCANNER: ModuleType | None = None


def _load_markdown_image_scanner() -> ModuleType:
    """Load the Skill-owned scanner by fixed path without changing ``sys.path``."""

    global _MARKDOWN_IMAGE_SCANNER
    if _MARKDOWN_IMAGE_SCANNER is not None:
        return _MARKDOWN_IMAGE_SCANNER
    scanner_path = REPORTCTL_PATH.with_name("markdown_image_scanner.py")
    try:
        spec = importlib.util.spec_from_file_location(
            "_agentic_reporting_benchmark_markdown_image_scanner",
            scanner_path,
        )
        if spec is None or spec.loader is None:
            raise ImportError("no module loader is available")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name in (
            "decode_commonmark_entities",
            "has_visible_alt_text",
            "scan_markdown_images",
        ):
            if not callable(getattr(module, name, None)):
                raise ImportError(f"scanner export is missing: {name}")
    except Exception as exc:
        raise BenchmarkError(
            f"Cannot load shared Markdown image scanner {scanner_path}: {exc}"
        ) from exc
    _MARKDOWN_IMAGE_SCANNER = module
    return module


def _is_unsafe_terminal_codepoint(codepoint: int) -> bool:
    return (
        codepoint < 0x20
        or codepoint == 0x7F
        or 0x80 <= codepoint <= 0x9F
        or codepoint in UNSAFE_MARKDOWN_FORMAT_CONTROLS
    )


def _terminal_safe_text(value: Any, *, preserve_newlines: bool = False) -> str:
    output: list[str] = []
    for character in str(value):
        codepoint = ord(character)
        if character == "\n" and preserve_newlines:
            output.append(character)
        elif codepoint < 0x20 or codepoint == 0x7F:
            escapes = {0x09: r"\t", 0x0A: r"\n", 0x0D: r"\r"}
            output.append(escapes.get(codepoint, f"\\x{codepoint:02x}"))
        elif _is_unsafe_terminal_codepoint(codepoint):
            output.append(f"\\u{codepoint:04x}")
        else:
            output.append(character)
    return "".join(output)


def _safe_print(value: Any = "", *, file: Any = None, preserve_newlines: bool = False) -> None:
    print(_terminal_safe_text(value, preserve_newlines=preserve_newlines), file=file)


def _safe_json_dumps(value: Any) -> str:
    rendered = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)
    return "".join(
        f"\\u{ord(character):04x}"
        if (
            ord(character) == 0x7F
            or 0x80 <= ord(character) <= 0x9F
            or ord(character) in UNSAFE_MARKDOWN_FORMAT_CONTROLS
        )
        else character
        for character in rendered
    )


class _SafeArgumentParser(argparse.ArgumentParser):
    def _print_message(self, message: str | None, file: Any = None) -> None:
        if message:
            super()._print_message(
                _terminal_safe_text(message, preserve_newlines=True),
                file,
            )

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {_terminal_safe_text(message)}\n")


def _read_json(path: Path) -> dict[str, Any]:
    def reject_nonstandard_constant(value: str) -> None:
        raise ValueError(f"non-standard numeric constant {value}")

    def parse_bounded_int(value: str) -> int:
        if len(value) > MAX_JSON_NUMBER_CHARS:
            raise ValueError(
                f"integer literal exceeds {MAX_JSON_NUMBER_CHARS} characters"
            )
        return int(value)

    def parse_bounded_float(value: str) -> float:
        if len(value) > MAX_JSON_NUMBER_CHARS:
            raise ValueError(
                f"floating-point literal exceeds {MAX_JSON_NUMBER_CHARS} characters"
            )
        return float(value)

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise BenchmarkError(f"Cannot inspect benchmark JSON {path}: {exc}") from exc
    if not path.is_file():
        raise BenchmarkError(f"Benchmark JSON must be a regular file: {path}")
    if size > MAX_BENCHMARK_BYTES:
        raise BenchmarkError(f"Benchmark JSON exceeds {MAX_BENCHMARK_BYTES} bytes: {path}")
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_nonstandard_constant,
            parse_float=parse_bounded_float,
            parse_int=parse_bounded_int,
        )
    except UnicodeDecodeError as exc:
        raise BenchmarkError(f"Benchmark JSON must be UTF-8: {path}") from exc
    except OSError as exc:
        raise BenchmarkError(f"Cannot read benchmark JSON {path}: {exc}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise BenchmarkError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BenchmarkError(f"Expected a JSON object in {path}")
    return value


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkError(f"{label} must be a nonempty string")
    return value


def _require_string_list(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        suffix = " nonempty" if nonempty else ""
        raise BenchmarkError(f"{label} must be a{suffix} list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise BenchmarkError(f"{label} must contain only nonempty strings")
    return value


def _require_object_shape(
    value: dict[str, Any],
    label: str,
    *,
    required: Iterable[str],
    optional: Iterable[str] = (),
) -> None:
    required_set = set(required)
    allowed = required_set | set(optional)
    missing = sorted(required_set - set(value))
    unknown = sorted(set(value) - allowed)
    if missing:
        raise BenchmarkError(f"{label} is missing required fields: {', '.join(missing)}")
    if unknown:
        raise BenchmarkError(f"{label} has unknown fields: {', '.join(unknown)}")


def _require_identifier(value: Any, label: str) -> str:
    identifier = _require_string(value, label)
    if not re.fullmatch(r"[a-z0-9-]+", identifier):
        raise BenchmarkError(f"{label} must match ^[a-z0-9-]+$")
    return identifier


def _resolve_artifact_root(artifact_root: Path) -> Path:
    try:
        resolved_root = Path(artifact_root).expanduser().resolve(strict=True)
        if not resolved_root.is_dir():
            raise BenchmarkError(f"artifact root must be a directory: {artifact_root}")
    except BenchmarkError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise BenchmarkError(f"cannot resolve artifact root {artifact_root}: {exc}") from exc
    return resolved_root


def _resolve_declared_artifact(
    artifact_root: Path,
    artifact: str,
    *,
    label: str,
) -> Path:
    artifact_path = Path(artifact)
    if artifact_path.is_absolute() or ".." in artifact_path.parts:
        raise BenchmarkError(f"{label} must be a safe artifact-root-relative path: {artifact}")
    try:
        resolved_artifact = (artifact_root / artifact_path).resolve(strict=True)
        resolved_artifact.relative_to(artifact_root)
        mode = resolved_artifact.stat().st_mode
    except ValueError as exc:
        raise BenchmarkError(f"{label} escapes the artifact root: {artifact}") from exc
    except (OSError, RuntimeError) as exc:
        raise BenchmarkError(f"{label} cannot be resolved within the artifact root: {artifact}") from exc
    if not stat.S_ISREG(mode):
        raise BenchmarkError(f"{label} must resolve to a regular file: {artifact}")
    return resolved_artifact


def load_benchmark(
    path: Path = CASES_PATH,
    *,
    artifact_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    data = _read_json(Path(path))
    validate_benchmark(data, artifact_root=artifact_root)
    return data


def load_activation() -> dict[str, Any]:
    data = _read_json(ACTIVATION_PATH)
    validate_activation(data)
    return data


def validate_activation(data: dict[str, Any]) -> None:
    _require_object_shape(
        data,
        "activation root",
        required=(
            "schema_version", "benchmark_id", "skill", "description",
            "claim_boundary", "rubrics", "cases",
        ),
        optional=("$schema",),
    )
    if data.get("schema_version") != "1.0":
        raise BenchmarkError("activation schema_version must be 1.0")
    if "$schema" in data:
        _require_string(data["$schema"], "activation $schema")
    _require_string(data.get("benchmark_id"), "activation benchmark_id")
    if data.get("skill") != "agentic-reporting":
        raise BenchmarkError("activation skill must be agentic-reporting")
    _require_string(data.get("description"), "activation description")
    _require_string(data.get("claim_boundary"), "activation claim_boundary")
    rubrics = data.get("rubrics")
    if not isinstance(rubrics, dict):
        raise BenchmarkError("activation rubrics must be an object")
    _require_object_shape(
        rubrics,
        "activation rubrics",
        required=ACTIVATION_RUBRICS,
    )
    for rubric_id, rubric in rubrics.items():
        if not isinstance(rubric, dict):
            raise BenchmarkError(f"activation rubric {rubric_id} must be an object")
        _require_object_shape(
            rubric,
            f"activation rubric {rubric_id}",
            required=("criterion", "assessment"),
        )
        _require_string(rubric.get("criterion"), f"activation rubric {rubric_id} criterion")
        if rubric.get("assessment") not in RUBRIC_ASSESSMENTS:
            raise BenchmarkError(f"activation rubric {rubric_id} has an invalid assessment")
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 8:
        raise BenchmarkError("activation cases must contain at least eight records")
    ids: set[str] = set()
    categories: set[str] = set()
    covered_rubrics: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise BenchmarkError(f"activation case {index} must be an object")
        _require_object_shape(
            case,
            f"activation case {index}",
            required=(
                "id", "category", "prompt", "expected_activation", "expected_route",
                "reason", "expected_behavior", "rubric_categories", "tags",
            ),
        )
        case_id = _require_identifier(case.get("id"), f"activation case {index} id")
        if case_id in ids:
            raise BenchmarkError(f"duplicate activation case id: {case_id}")
        ids.add(case_id)
        category = case.get("category")
        if category not in ACTIVATION_CATEGORIES:
            raise BenchmarkError(f"invalid activation category for {case_id}: {category}")
        categories.add(category)
        _require_string(case.get("prompt"), f"activation case {case_id} prompt")
        _require_string(case.get("reason"), f"activation case {case_id} reason")
        expected_activation = case.get("expected_activation")
        if not isinstance(expected_activation, bool):
            raise BenchmarkError(f"activation case {case_id} expected_activation must be boolean")
        should_activate = category in POSITIVE_ACTIVATION_CATEGORIES
        if expected_activation is not should_activate:
            raise BenchmarkError(f"activation case {case_id} category and expected_activation disagree")
        route = case.get("expected_route")
        if should_activate:
            if not isinstance(route, dict):
                raise BenchmarkError(f"positive activation case {case_id} requires expected_route")
            _require_object_shape(
                route,
                f"activation case {case_id} route",
                required=("mode", "modules"),
                optional=("profile",),
            )
            if route.get("mode") not in MODE_IDS:
                raise BenchmarkError(f"activation case {case_id} has an invalid route mode")
            if "profile" in route and route["profile"] not in PROFILE_IDS:
                raise BenchmarkError(f"activation case {case_id} has an invalid route profile")
            modules = _require_string_list(route.get("modules"), f"activation case {case_id} route modules")
            if len(modules) > 2 or len(modules) != len(set(modules)) or set(modules) - MODULE_IDS:
                raise BenchmarkError(f"activation case {case_id} route modules must be at most two unique known modules")
        elif route is not None:
            raise BenchmarkError(f"negative activation case {case_id} expected_route must be null")
        expected_behavior = _require_string_list(
            case.get("expected_behavior"), f"activation case {case_id} expected_behavior", nonempty=True
        )
        if len(expected_behavior) != len(set(expected_behavior)):
            raise BenchmarkError(f"activation case {case_id} expected_behavior must be unique")
        rubric_categories = _require_string_list(
            case.get("rubric_categories"), f"activation case {case_id} rubric_categories", nonempty=True
        )
        if len(rubric_categories) != len(set(rubric_categories)) or set(rubric_categories) - ACTIVATION_RUBRICS:
            raise BenchmarkError(f"activation case {case_id} rubric_categories must be unique known rubric IDs")
        covered_rubrics.update(rubric_categories)
        tags = _require_string_list(case.get("tags"), f"activation case {case_id} tags")
        if len(tags) != len(set(tags)):
            raise BenchmarkError(f"activation case {case_id} tags must be unique")
    missing_categories = sorted(ACTIVATION_CATEGORIES - categories)
    if missing_categories:
        raise BenchmarkError(f"activation contract is missing categories: {', '.join(missing_categories)}")
    missing_rubrics = sorted(ACTIVATION_RUBRICS - covered_rubrics)
    if missing_rubrics:
        raise BenchmarkError(f"activation contract is missing rubric coverage: {', '.join(missing_rubrics)}")


def validate_benchmark(
    data: dict[str, Any],
    *,
    artifact_root: Path = REPO_ROOT,
) -> None:
    _require_object_shape(
        data,
        "presentation root",
        required=("schema_version", "benchmark_id", "claim_boundary", "suites", "cases"),
        optional=("$schema",),
    )
    if data.get("schema_version") != "1.0":
        raise BenchmarkError("presentation schema_version must be 1.0")
    if "$schema" in data:
        _require_string(data["$schema"], "presentation $schema")
    _require_string(data.get("benchmark_id"), "benchmark_id")
    _require_string(data.get("claim_boundary"), "claim_boundary")
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 7:
        raise BenchmarkError("presentation benchmark must contain at least seven cases")
    resolved_artifact_root = _resolve_artifact_root(artifact_root)

    ids: set[str] = set()
    scenarios: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise BenchmarkError(f"case {index} must be an object")
        _require_object_shape(
            case,
            f"case {index}",
            required=(
                "id", "scenario", "request", "facts", "evidence_boundary",
                "artifacts", "report_profile", "required_semantic_slots",
                "expected_route", "visual_oracle", "budgets", "machine_checks",
            ),
            optional=("allowed_citations",),
        )
        case_id = _require_identifier(case.get("id"), f"case {index} id")
        if case_id in ids:
            raise BenchmarkError(f"duplicate case id: {case_id}")
        ids.add(case_id)
        scenarios.add(_require_string(case.get("scenario"), f"case {case_id} scenario"))
        _require_string(case.get("request"), f"case {case_id} request")
        _require_string_list(case.get("facts"), f"case {case_id} facts", nonempty=True)
        _require_string(case.get("evidence_boundary"), f"case {case_id} evidence_boundary")
        _require_string_list(case.get("artifacts"), f"case {case_id} artifacts")
        for artifact in case["artifacts"]:
            _resolve_declared_artifact(
                resolved_artifact_root,
                artifact,
                label=f"case {case_id} artifact",
            )
        _require_string(case.get("report_profile"), f"case {case_id} report_profile")
        expected_route = case.get("expected_route")
        if not isinstance(expected_route, dict) or set(expected_route) != {"mode", "modules"}:
            raise BenchmarkError(f"case {case_id} expected_route must contain only mode and modules")
        if expected_route.get("mode") not in MODE_IDS:
            raise BenchmarkError(f"case {case_id} has an invalid expected route mode")
        route_modules = _require_string_list(
            expected_route.get("modules"), f"case {case_id} expected route modules"
        )
        if len(route_modules) > 2 or len(route_modules) != len(set(route_modules)):
            raise BenchmarkError(f"case {case_id} expected route must contain at most two unique modules")
        unknown_modules = sorted(set(route_modules) - MODULE_IDS)
        if unknown_modules:
            raise BenchmarkError(f"case {case_id} has unknown expected modules: {', '.join(unknown_modules)}")
        profile_parts = case["report_profile"].split("+")
        if profile_parts[0] != expected_route["mode"] or set(profile_parts[1:]) != set(route_modules):
            raise BenchmarkError(f"case {case_id} report_profile and expected_route disagree")
        semantic_slots = _require_string_list(
            case.get("required_semantic_slots"),
            f"case {case_id} required_semantic_slots",
            nonempty=True,
        )
        if len(semantic_slots) != len(set(semantic_slots)):
            raise BenchmarkError(f"case {case_id} required_semantic_slots must be unique")
        visual = case.get("visual_oracle")
        if not isinstance(visual, dict) or visual.get("necessity") not in {
            "required",
            "optional",
            "forbidden",
        }:
            raise BenchmarkError(f"case {case_id} has an invalid visual oracle")
        _require_object_shape(
            visual,
            f"case {case_id} visual oracle",
            required=("necessity", "allowed_types", "rationale"),
        )
        allowed_types = _require_string_list(visual.get("allowed_types"), f"case {case_id} visual allowed_types")
        if len(allowed_types) != len(set(allowed_types)):
            raise BenchmarkError(f"case {case_id} visual allowed_types must be unique")
        _require_string(visual.get("rationale"), f"case {case_id} visual rationale")
        budgets = case.get("budgets")
        if (
            not isinstance(budgets, dict)
            or not isinstance(budgets.get("max_output_words"), int)
            or isinstance(budgets.get("max_output_words"), bool)
        ):
            raise BenchmarkError(f"case {case_id} needs an integer max_output_words budget")
        _require_object_shape(
            budgets,
            f"case {case_id} budgets",
            required=("max_output_words",),
        )
        if budgets["max_output_words"] < 1:
            raise BenchmarkError(f"case {case_id} max_output_words must be positive")
        checks = case.get("machine_checks")
        if not isinstance(checks, list) or not checks:
            raise BenchmarkError(f"case {case_id} must declare machine checks")
        check_ids: set[str] = set()
        for check in checks:
            if not isinstance(check, dict):
                raise BenchmarkError(f"case {case_id} contains a non-object machine check")
            _require_object_shape(
                check,
                f"check {case_id}",
                required=("id", "type", "message"),
                optional=("pattern", "value", "must_exist"),
            )
            check_id = _require_identifier(check.get("id"), f"case {case_id} check id")
            if check_id in check_ids:
                raise BenchmarkError(f"duplicate check id in {case_id}: {check_id}")
            check_ids.add(check_id)
            check_type = _require_string(check.get("type"), f"check {case_id}/{check_id} type")
            _require_string(check.get("message"), f"check {case_id}/{check_id} message")
            if "pattern" in check and (
                not isinstance(check["pattern"], str) or not check["pattern"].strip()
            ):
                raise BenchmarkError(f"check {case_id}/{check_id} pattern must be a nonempty string")
            if "value" in check and (
                not isinstance(check["value"], int) or isinstance(check["value"], bool) or check["value"] < 0
            ):
                raise BenchmarkError(f"check {case_id}/{check_id} value must be a nonnegative integer")
            if check_type in {"required_regex", "forbidden_regex"}:
                pattern = _require_string(check.get("pattern"), f"check {case_id}/{check_id} pattern")
                try:
                    re.compile(pattern, REGEX_FLAGS)
                except re.error as exc:
                    raise BenchmarkError(f"invalid regex in {case_id}/{check_id}: {exc}") from exc
            elif check_type in {
                "max_words",
                "max_headings",
                "min_markdown_tables",
                "max_markdown_tables",
            }:
                if (
                    not isinstance(check.get("value"), int)
                    or isinstance(check.get("value"), bool)
                    or check["value"] < 0
                ):
                    raise BenchmarkError(f"check {case_id}/{check_id} requires a nonnegative integer value")
            elif check_type not in {
                "required_image",
                "forbidden_image",
                "citation_allowlist",
                "forbidden_placeholder",
            }:
                raise BenchmarkError(f"unsupported check type in {case_id}/{check_id}: {check_type}")
            if "must_exist" in check and not isinstance(check["must_exist"], bool):
                raise BenchmarkError(f"check {case_id}/{check_id} must_exist must be boolean")
        allowed_citations = case.get("allowed_citations", [])
        allowed_citations = _require_string_list(
            allowed_citations,
            f"case {case_id} allowed_citations",
        )
        if len(allowed_citations) != len(set(allowed_citations)):
            raise BenchmarkError(f"case {case_id} allowed_citations must be unique")

    required_scenarios = {
        "short_answer",
        "long_engineering",
        "experiment_analysis",
        "image_presentation",
        "multi_table",
        "academic_paper_summary",
        "failure_risk",
    }
    missing = sorted(required_scenarios - scenarios)
    if missing:
        raise BenchmarkError(f"presentation cases are missing required scenarios: {', '.join(missing)}")

    suites = data.get("suites")
    if not isinstance(suites, list) or not suites:
        raise BenchmarkError("presentation benchmark must declare suites")
    suite_ids: set[str] = set()
    for suite in suites:
        if not isinstance(suite, dict):
            raise BenchmarkError("suite must be an object")
        _require_object_shape(suite, "suite", required=("id", "kind", "case_ids"))
        suite_id = _require_identifier(suite.get("id"), "suite id")
        if suite_id in suite_ids:
            raise BenchmarkError(f"duplicate suite id: {suite_id}")
        suite_ids.add(suite_id)
        if suite.get("kind") not in {"harness_only", "generation"}:
            raise BenchmarkError(f"suite {suite_id} has invalid kind")
        case_ids = _require_string_list(suite.get("case_ids"), f"suite {suite_id} case_ids", nonempty=True)
        if len(case_ids) != len(set(case_ids)):
            raise BenchmarkError(f"suite {suite_id} case_ids must be unique")
        unknown = sorted(set(case_ids) - ids)
        if unknown:
            raise BenchmarkError(f"suite {suite_id} references unknown cases: {', '.join(unknown)}")


def cases_by_id(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {case["id"]: case for case in data["cases"]}


def get_case(data: dict[str, Any], case_id: str) -> dict[str, Any]:
    try:
        return cases_by_id(data)[case_id]
    except KeyError as exc:
        available = ", ".join(sorted(cases_by_id(data)))
        raise BenchmarkError(f"unknown case '{case_id}'. Available cases: {available}") from exc


def get_suite(data: dict[str, Any], suite_id: str) -> dict[str, Any]:
    for suite in data["suites"]:
        if suite["id"] == suite_id:
            return suite
    available = ", ".join(sorted(suite["id"] for suite in data["suites"]))
    raise BenchmarkError(f"unknown suite '{suite_id}'. Available suites: {available}")


def render_prompt(case: dict[str, Any]) -> str:
    lines = [case["request"], "", "Supplied facts:"]
    lines.extend(f"- {fact}" for fact in case["facts"])
    lines.extend(["", f"Evidence boundary: {case['evidence_boundary']}"])
    if case["artifacts"]:
        lines.append("")
        lines.append("Supplied artifacts:")
        lines.extend(f"- {artifact}" for artifact in case["artifacts"])
    lines.extend(["", f"Maximum output length: {case['budgets']['max_output_words']} words."])
    return "\n".join(lines)


def _strip_fenced_code(text: str) -> str:
    return re.sub(r"^\s*(```|~~~).*?^\s*\1\s*$", "", text, flags=REGEX_FLAGS)


def _strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=REGEX_FLAGS)


def _prose_markdown(text: str) -> str:
    return _strip_fenced_code(_strip_html_comments(text))


def word_count(text: str) -> int:
    # Fenced code and quoted logs are still visible output and consume the user's
    # requested budget; only non-rendered HTML comments are excluded.
    visible = _strip_html_comments(text)
    return sum(1 for _ in re.finditer(r"\b[\w]+(?:[-'][\w]+)*\b", visible, flags=re.UNICODE))


def heading_count(text: str) -> int:
    visible = _prose_markdown(text)
    return sum(1 for line in visible.splitlines() if re.match(r"^\s{0,3}#{1,6}\s+\S", line))


def markdown_table_count(text: str) -> int:
    visible = _prose_markdown(text)
    count = 0
    for line in visible.splitlines():
        stripped = line.strip().strip("|")
        if "|" not in stripped:
            continue
        cells = [cell.strip() for cell in stripped.split("|")]
        if len(cells) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            count += 1
    return count


MAX_MARKDOWN_IMAGES = 1_000


def _contains_unsafe_markdown_control(value: str) -> bool:
    """Keep benchmark-owned terminal/control policy outside the shared parser."""

    return any(_is_unsafe_terminal_codepoint(ord(character)) for character in value)


def markdown_images(text: str) -> list[tuple[str, str, bool]]:
    """Project shared scanner records onto the benchmark's stable tuple API."""

    scanner = _load_markdown_image_scanner()
    try:
        records = scanner.scan_markdown_images(
            text,
            record_limit=MAX_MARKDOWN_IMAGES + 1,
        )
    except (TypeError, ValueError) as exc:
        raise BenchmarkError(f"Cannot scan Markdown images: {exc}") from exc
    return [(record.alt, record.target, record.canonical) for record in records]


def _local_image_path(target: str, response_path: Path) -> Path | None:
    try:
        normalized_target = _load_markdown_image_scanner().decode_commonmark_entities(target)
        if (
            _contains_unsafe_markdown_control(target)
            or _contains_unsafe_markdown_control(normalized_target)
            or any(not character.isprintable() for character in normalized_target)
            or any(character.isspace() for character in normalized_target)
            or any(character in normalized_target for character in "\\()<>")
        ):
            return None
        parsed = urlsplit(normalized_target)
        if parsed.scheme or parsed.netloc or normalized_target.startswith("//"):
            return None
        clean_target = unquote(parsed.path)
        if (
            not clean_target
            or _contains_unsafe_markdown_control(clean_target)
            or any(not character.isprintable() for character in clean_target)
        ):
            return None
        path = Path(clean_target)
        if not path.is_absolute():
            path = response_path.parent / path
        return path.resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def _check_one(
    case: dict[str, Any],
    check: dict[str, Any],
    text: str,
    response_path: Path,
    artifact_root: Path,
) -> tuple[bool, str]:
    check_type = check["type"]
    if check_type == "required_regex":
        # Required evidence may legitimately appear in a visible fenced log.
        passed = re.search(check["pattern"], _strip_html_comments(text), flags=REGEX_FLAGS) is not None
        observed = "required pattern found" if passed else "required pattern missing"
    elif check_type == "forbidden_regex":
        # A quoted log is not itself the report's narrative claim.
        passed = re.search(check["pattern"], _prose_markdown(text), flags=REGEX_FLAGS) is None
        observed = "forbidden pattern absent" if passed else "forbidden pattern found"
    elif check_type == "max_words":
        observed_value = word_count(text)
        passed = observed_value <= check["value"]
        observed = f"{observed_value} words (maximum {check['value']})"
    elif check_type == "max_headings":
        observed_value = heading_count(text)
        passed = observed_value <= check["value"]
        observed = f"{observed_value} headings (maximum {check['value']})"
    elif check_type == "min_markdown_tables":
        observed_value = markdown_table_count(text)
        passed = observed_value >= check["value"]
        observed = f"{observed_value} Markdown tables (minimum {check['value']})"
    elif check_type == "max_markdown_tables":
        observed_value = markdown_table_count(text)
        passed = observed_value <= check["value"]
        observed = f"{observed_value} Markdown tables (maximum {check['value']})"
    elif check_type == "required_image":
        scanned_images = markdown_images(text)
        image_limit_exceeded = len(scanned_images) > MAX_MARKDOWN_IMAGES
        candidates = scanned_images[:MAX_MARKDOWN_IMAGES]
        images = [(alt, target) for alt, target, canonical in candidates if canonical]
        nonempty_alt = bool(images) and all(
            _load_markdown_image_scanner().has_visible_alt_text(alt)
            and not _contains_unsafe_markdown_control(alt)
            for alt, _ in images
        )
        resolved_images = [_local_image_path(target, response_path) for _, target in images]
        local_ok = True
        if check.get("must_exist"):
            local_ok = bool(images) and all(
                path is not None
                and path.is_file()
                and path.suffix.casefold() in RENDERABLE_IMAGE_SUFFIXES
                for path in resolved_images
            )
        allowed_artifacts = {
            _resolve_declared_artifact(
                artifact_root,
                artifact,
                label=f"case {case['id']} artifact",
            )
            for artifact in case.get("artifacts", [])
        }
        artifact_match = bool(images) and bool(allowed_artifacts) and any(
            path in allowed_artifacts for path in resolved_images if path is not None
        )
        passed = bool(images) and not image_limit_exceeded and nonempty_alt and local_ok and artifact_match
        observed = (
            f"{len(images)} images; alt_text={nonempty_alt}; "
            f"local_targets_exist={local_ok}; supplied_artifact_match={artifact_match}; "
            f"noncanonical_candidates={len(candidates) - len(images)}; "
            f"image_scan_truncated={image_limit_exceeded}"
        )
    elif check_type == "forbidden_image":
        images = markdown_images(text)
        mermaid_fences = re.findall(
            r"(?im)^[ \t]{0,3}(?:`{3,}|~{3,})[ \t]*mermaid(?=[ \t\r\n]|$)",
            text,
        )
        visual_markers = len(images) + len(mermaid_fences)
        passed = visual_markers == 0
        observed = f"{visual_markers} images (maximum 0)"
    elif check_type == "citation_allowlist":
        observed_citations = set(re.findall(r"\[([A-Z][A-Z0-9_-]*\d+)\]", _prose_markdown(text)))
        allowed = set(case.get("allowed_citations", []))
        unexpected = sorted(observed_citations - allowed)
        passed = not unexpected
        observed = f"citations={sorted(observed_citations)}; unexpected={unexpected}"
    elif check_type == "forbidden_placeholder":
        placeholder = re.search(
            r"\b(?:TODO|TBD|FIXME|XXX)\b|\{\{[^}]+\}\}|<[^>\n]*(?:placeholder|fill[^>\n]*)>",
            _prose_markdown(text),
            flags=REGEX_FLAGS,
        )
        passed = placeholder is None
        observed = "no unresolved placeholder" if passed else f"placeholder found: {placeholder.group(0)}"
    else:  # validate_benchmark should make this unreachable.
        raise BenchmarkError(f"unsupported machine check type: {check_type}")
    return passed, observed


def evaluate_response(
    case: dict[str, Any],
    response_path: Path,
    *,
    artifact_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    resolved_artifact_root = _resolve_artifact_root(artifact_root)
    try:
        size = response_path.stat().st_size
        if not response_path.is_file():
            raise BenchmarkError(f"response path must be a regular file: {response_path}")
        if size > MAX_RESPONSE_BYTES:
            raise BenchmarkError(f"response file exceeds {MAX_RESPONSE_BYTES} bytes: {response_path}")
        # Leading indentation and trailing line endings are Markdown semantics;
        # never normalize them before presentation checks.
        text = response_path.read_text(encoding="utf-8")
        line_count = text.count("\n") + 1
        if line_count > MAX_RESPONSE_LINES:
            raise BenchmarkError(
                f"response file has {line_count} lines, above the limit of {MAX_RESPONSE_LINES}: {response_path}"
            )
    except BenchmarkError:
        raise
    except UnicodeDecodeError as exc:
        raise BenchmarkError(f"response file must be UTF-8: {response_path}") from exc
    except OSError as exc:
        raise BenchmarkError(f"cannot read response file {response_path}: {exc}") from exc
    results = []
    for check in case["machine_checks"]:
        passed, observed = _check_one(
            case,
            check,
            text,
            response_path,
            resolved_artifact_root,
        )
        results.append(
            {
                "id": check["id"],
                "type": check["type"],
                "passed": passed,
                "message": check["message"],
                "observed": observed,
            }
        )
    passed_count = sum(result["passed"] for result in results)
    scanned_images = markdown_images(text)
    return {
        "case_id": case["id"],
        "response": str(response_path),
        "passed": passed_count == len(results),
        "checks_passed": passed_count,
        "checks_total": len(results),
        "word_count": word_count(text),
        "heading_count": heading_count(text),
        "markdown_table_count": markdown_table_count(text),
        "image_count": min(len(scanned_images), MAX_MARKDOWN_IMAGES),
        "image_scan_truncated": len(scanned_images) > MAX_MARKDOWN_IMAGES,
        "checks": results,
        "semantic_limit": (
            "Machine checks do not establish factual truth, scientific validity, "
            "visual necessity, accessibility, or professional readability."
        ),
    }


def _evaluate_expected_route(case_id: str, task: str, expected: dict[str, Any]) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(REPORTCTL_PATH),
            "route",
            "--task",
            task,
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "case_id": case_id,
            "passed": False,
            "expected": expected,
            "actual": None,
            "observed": f"reportctl exited {completed.returncode}: {completed.stderr.strip()}",
        }
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return {
            "case_id": case_id,
            "passed": False,
            "expected": expected,
            "actual": None,
            "observed": f"reportctl emitted invalid JSON: {exc}",
        }
    actual = {"mode": payload.get("mode"), "modules": payload.get("modules")}
    if "profile" in expected:
        actual["profile"] = payload.get("profile")
    passed = (
        actual["mode"] == expected["mode"]
        and isinstance(actual["modules"], list)
        and set(actual["modules"]) == set(expected["modules"])
        and len(actual["modules"]) == len(expected["modules"])
        and ("profile" not in expected or actual["profile"] == expected["profile"])
    )
    return {
        "case_id": case_id,
        "passed": passed,
        "expected": expected,
        "actual": actual,
        "observed": "route matched" if passed else "route/profile mismatch",
    }


def evaluate_route(case: dict[str, Any]) -> dict[str, Any]:
    return _evaluate_expected_route(case["id"], render_prompt(case), case["expected_route"])


def evaluate_activation_route(case: dict[str, Any]) -> dict[str, Any]:
    return _evaluate_expected_route(case["id"], case["prompt"], case["expected_route"])


def smoke_report(data: dict[str, Any], activation: dict[str, Any], suite_id: str) -> dict[str, Any]:
    suite = get_suite(data, suite_id)
    if suite["kind"] != "harness_only":
        raise BenchmarkError(f"suite '{suite_id}' is not a harness-only smoke suite")
    by_id = cases_by_id(data)
    records: list[dict[str, Any]] = []
    harness_pass = True
    for case_id in suite["case_ids"]:
        case = by_id[case_id]
        for fixture_kind, expected_pass in (("good", True), ("bad", False)):
            response = FIXTURE_ROOT / fixture_kind / f"{case_id}.md"
            evaluation = evaluate_response(case, response)
            expectation_met = evaluation["passed"] is expected_pass
            harness_pass = harness_pass and expectation_met
            records.append(
                {
                    "case_id": case_id,
                    "fixture": fixture_kind,
                    "expected_machine_pass": expected_pass,
                    "observed_machine_pass": evaluation["passed"],
                    "expectation_met": expectation_met,
                    "failed_check_ids": [
                        result["id"] for result in evaluation["checks"] if not result["passed"]
                    ],
                }
            )
    route_records = [evaluate_route(by_id[case_id]) for case_id in suite["case_ids"]]
    harness_pass = harness_pass and all(record["passed"] for record in route_records)
    activation_route_records = [
        evaluate_activation_route(case)
        for case in activation["cases"]
        if case["expected_activation"]
    ]
    harness_pass = harness_pass and all(record["passed"] for record in activation_route_records)
    return {
        "benchmark_id": data["benchmark_id"],
        "suite_id": suite_id,
        "suite_kind": suite["kind"],
        "harness_pass": harness_pass,
        "fixture_evaluations": len(records),
        "expectations_met": sum(record["expectation_met"] for record in records),
        "route_expectations": len(route_records),
        "route_expectations_met": sum(record["passed"] for record in route_records),
        "activation_contract_valid": True,
        "activation_case_count": len(activation["cases"]),
        "positive_route_proxy_expectations": len(activation_route_records),
        "positive_route_proxy_expectations_met": sum(record["passed"] for record in activation_route_records),
        "host_activation_observed": False,
        "activation_effectiveness_claim": False,
        "effectiveness_claim": False,
        "disclaimer": DISCLAIMER,
        "records": records,
        "route_records": route_records,
        "activation_route_proxy_records": activation_route_records,
    }


def _emit_json(value: Any) -> None:
    print(_safe_json_dumps(value))


def _print_check(report: dict[str, Any]) -> None:
    status = "PASS" if report["passed"] else "FAIL"
    _safe_print(f"{status} {report['case_id']}: {report['checks_passed']}/{report['checks_total']} checks")
    for result in report["checks"]:
        marker = "ok" if result["passed"] else "FAIL"
        _safe_print(f"- [{marker}] {result['id']}: {result['observed']}")
        if not result["passed"]:
            _safe_print(f"  {result['message']}")
    _safe_print(report["semantic_limit"])


def command_list(args: argparse.Namespace) -> int:
    data = load_benchmark()
    load_activation()
    cases = data["cases"]
    if args.suite:
        suite = get_suite(data, args.suite)
        wanted = set(suite["case_ids"])
        cases = [case for case in cases if case["id"] in wanted]
    payload = [
        {
            "id": case["id"],
            "scenario": case["scenario"],
            "report_profile": case["report_profile"],
            "visual_necessity": case["visual_oracle"]["necessity"],
            "max_output_words": case["budgets"]["max_output_words"],
        }
        for case in cases
    ]
    if args.json:
        _emit_json({"benchmark_id": data["benchmark_id"], "cases": payload})
    else:
        for item in payload:
            _safe_print(
                f"{item['id']}: scenario={item['scenario']}; "
                f"profile={item['report_profile']}; visual={item['visual_necessity']}; "
                f"max_words={item['max_output_words']}"
            )
    return 0


def command_prompt(args: argparse.Namespace) -> int:
    data = load_benchmark()
    case = get_case(data, args.case)
    prompt = render_prompt(case)
    if args.json:
        _emit_json({"benchmark_id": data["benchmark_id"], "case_id": case["id"], "prompt": prompt})
    else:
        _safe_print(prompt, preserve_newlines=True)
    return 0


def command_check(args: argparse.Namespace) -> int:
    data = load_benchmark()
    case = get_case(data, args.case)
    report = evaluate_response(case, Path(args.response).expanduser().resolve())
    if args.json:
        _emit_json(report)
    else:
        _print_check(report)
    return 0 if report["passed"] else 1


def command_route_check(args: argparse.Namespace) -> int:
    data = load_benchmark()
    case = get_case(data, args.case)
    report = evaluate_route(case)
    if args.json:
        _emit_json(report)
    else:
        status = "PASS" if report["passed"] else "FAIL"
        _safe_print(f"{status} {report['case_id']}: {report['observed']}")
        _safe_print(f"- expected: {report['expected']}")
        _safe_print(f"- actual: {report['actual']}")
    return 0 if report["passed"] else 1


def command_smoke(args: argparse.Namespace) -> int:
    data = load_benchmark()
    activation = load_activation()
    report = smoke_report(data, activation, args.suite)
    if args.json:
        _emit_json(report)
    else:
        status = "PASS" if report["harness_pass"] else "FAIL"
        _safe_print(
            f"{status} {report['suite_id']}: {report['expectations_met']}/"
            f"{report['fixture_evaluations']} fixture expectations met"
        )
        for record in report["records"]:
            marker = "ok" if record["expectation_met"] else "FAIL"
            failed = ", ".join(record["failed_check_ids"]) or "none"
            _safe_print(f"- [{marker}] {record['case_id']} ({record['fixture']}), failed checks: {failed}")
        for record in report["route_records"]:
            marker = "ok" if record["passed"] else "FAIL"
            _safe_print(
                f"- [{marker}] {record['case_id']} route: "
                f"expected={record['expected']}; actual={record['actual']}"
            )
        for record in report["activation_route_proxy_records"]:
            marker = "ok" if record["passed"] else "FAIL"
            _safe_print(
                f"- [{marker}] {record['case_id']} post-activation route proxy: "
                f"expected={record['expected']}; actual={record['actual']}"
            )
        _safe_print("Host activation observed: no; activation cases are declarative, not an accuracy measurement.")
        _safe_print(report["disclaimer"])
    return 0 if report["harness_pass"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(
        description="List, prompt, and machine-check agentic reporting evaluation cases."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List declared presentation cases.")
    list_parser.add_argument("--suite", help="Restrict output to one declared suite.")
    list_parser.add_argument("--json", action="store_true", help="Emit versioned JSON-compatible output.")
    list_parser.set_defaults(func=command_list)

    prompt_parser = subparsers.add_parser("prompt", help="Emit one condition-neutral generation prompt.")
    prompt_parser.add_argument("case", help="Case identifier from the list command.")
    prompt_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    prompt_parser.set_defaults(func=command_prompt)

    check_parser = subparsers.add_parser("check", help="Run declared machine checks on one response.")
    check_parser.add_argument("--case", required=True, help="Case identifier.")
    check_parser.add_argument("--response", required=True, help="Path to a Markdown response.")
    check_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    check_parser.set_defaults(func=command_check)

    route_check_parser = subparsers.add_parser(
        "route-check", help="Check the router against one declared report profile."
    )
    route_check_parser.add_argument("--case", required=True, help="Case identifier.")
    route_check_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    route_check_parser.set_defaults(func=command_route_check)

    smoke_parser = subparsers.add_parser("smoke", help="Evaluate known-good and mutated smoke fixtures.")
    smoke_parser.add_argument("--suite", default="harness-smoke", help="Harness-only suite identifier.")
    smoke_parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    smoke_parser.set_defaults(func=command_smoke)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return int(args.func(args))
    except BenchmarkError as exc:
        _safe_print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
