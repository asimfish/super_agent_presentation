#!/usr/bin/env python3
"""Private, preregistered baseline-versus-framework study controller.

Deterministic lifecycle commands never call a model. Host execution is added only
through explicit typed adapters; pilots and incomplete designs remain ineligible for
an effectiveness claim regardless of their observed scores.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import random
import re
import secrets
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from pathlib import PurePosixPath
from types import ModuleType
from typing import Any, Callable, Iterable
from urllib.parse import unquote, urlsplit


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_SCRIPT = REPO_ROOT / "scripts" / "presentation_benchmark.py"
HOSTS_SCRIPT = REPO_ROOT / "scripts" / "presentation_hosts.py"
REPORTCTL_SCRIPT = (
    REPO_ROOT / "skills" / "agentic-reporting" / "scripts" / "reportctl.py"
)
CHECKPOINT_AUDITOR_RELATIVE_FILES = (
    PurePosixPath("scripts/reportctl.py"),
    PurePosixPath("scripts/markdown_image_scanner.py"),
    PurePosixPath("references/protocols.json"),
)
CHECKPOINT_CAPTURE_DIRECTORY = ".agentic-reporting"
CHECKPOINT_CAPTURE_PATH = ".agentic-reporting/checkpoint.json"
CHECKPOINT_REPORT_PATH = ".agentic-reporting/draft.md"
CHECKPOINT_CAPTURE_IGNORE_PATH = ".agentic-reporting/.gitignore"
CHECKPOINT_CAPTURE_IGNORE_BYTES = b"*\n"
CHECKPOINT_AGENT_CONTRACT = (
    "Study-only checkpoint receipt contract: use "
    ".agentic-reporting/checkpoint.json for checkpoint creation and the later "
    "bundle reload, then audit .agentic-reporting/draft.md with that checkpoint "
    "in strict mode. Invoke all three receipt commands with the literal prefix "
    "python3 .agents/skills/agentic-reporting/scripts/reportctl.py so the JSONL "
    "adapter can recognize them. The controller precreated and Git-ignored .agentic-reporting "
    "with mode 0700. "
    "For supplied local images, embed the exact workspace-relative artifact path "
    "shown in the task (never prefix ../); the controller mirrors those paths "
    "beneath the draft directory so the same Markdown target remains valid after "
    "storage and blinding. "
    "Keep both files mode 0600 before each successful command event, and deliver "
    "the audited draft bytes exactly as the final response."
)
PUBLIC_CASES = REPO_ROOT / "evals" / "presentation-cases.json"
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_TRANSCRIPT_BYTES = 16 * 1024 * 1024
MAX_HOST_STDERR_BYTES = 2 * 1024 * 1024
MAX_CHECKPOINT_BYTES = 2 * 1024 * 1024
MAX_CHECKPOINT_REPORT_BYTES = 1 * 1024 * 1024
MAX_CHECKPOINT_CAPTURE_EVENTS = 16
MAX_AUDITOR_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
MAX_ARTIFACT_TOTAL_BYTES = 32 * 1024 * 1024
MAX_ARTIFACTS = 32
MAX_SKILL_TREE_BYTES = 32 * 1024 * 1024
MAX_SKILL_TREE_ENTRIES = 4096
MAX_JSON_NUMBER_CHARS = 128
MAX_JSON_DEPTH = 100
MAX_JSON_VALUES = 100_000
MAX_CASE_IDS = 500
# The minimum public-study design needs 1,008 generation records
# (28 cases x 2 revisions x 3 contexts x 3 repeats x 2 conditions).  Keep
# bounded headroom without allowing a Cartesian-product typo to create an
# internally unreadable multi-megabyte run manifest.
MAX_EXPECTED_RECORDS = 1_500
MAX_BLIND_TREE_ENTRIES = 100_000
MAX_BLIND_TREE_BYTES = 2 * 1024 * 1024 * 1024
CONDITIONS = ("baseline", "framework")
HOSTS = {"manual", "codex", "claude", "copilot", "gemini"}
STUDY_KINDS = {"pilot", "controlled", "public"}
DIMENSIONS = (
    "task_fidelity",
    "information_architecture",
    "readability_and_scannability",
    "completeness_and_actionability",
    "evidence_calibration",
    "visual_display_fitness",
    "concision_and_proportionality",
)
PRIORITY_DIMENSIONS = {
    "readability_and_scannability",
    "completeness_and_actionability",
    "evidence_calibration",
}
MANDATORY_DISPLAY_CHECK_TYPES = frozenset(
    {"required_image", "min_markdown_tables", "max_markdown_tables"}
)
THRESHOLD_PROFILE = {
    "machine_pass_rate_min": 0.98,
    "human_dimension_min": 4.0,
    "priority_dimension_min": 4.2,
    "primary_gain_min": 0.3,
    "primary_ci_lower_min": 0.0,
    "task_fidelity_margin": 0.2,
    "win_rate_min": 0.65,
    "loss_rate_max": 0.15,
    "semantic_slot_rate_min": 0.95,
    "semantic_density_difference_min": 0.0,
    "visual_precision_min": 0.9,
    "visual_recall_min": 0.9,
    "token_overhead_median_max": 0.15,
    "token_overhead_p90_max": 0.3,
    "long_soak_pass_rate_min": 0.9,
    "long_soak_fresh_gap_max": 0.05,
    "agreement_within_one_min": 0.85,
}
THRESHOLD_FIELDS = set(THRESHOLD_PROFILE)
CRITICAL_ERROR_LABELS = {
    "fabricated_evidence",
    "numeric_or_unit_drift",
    "negation_or_modality_drift",
    "false_completion_or_stale_status",
    "unsupported_causality_significance_or_ranking",
    "incomparable_protocol_ranking",
    "secret_leakage",
    "materially_misleading_visual",
    "ignored_explicit_format",
}
UNSAFE_TERMINAL_CODEPOINTS = frozenset(
    {
        0x061C,
        0x200E,
        0x200F,
        0x2028,
        0x2029,
        *range(0x202A, 0x202F),
        *range(0x2066, 0x206A),
    }
)
ARTIFACT_MEDIA_TYPES = {
    ".avif": "image/avif",
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}
ARTIFACT_PATH_PATTERN = (
    r"(?:[A-Za-z0-9][A-Za-z0-9._-]*/){0,11}"
    r"[A-Za-z0-9][A-Za-z0-9._-]*\.(?:avif|gif|jpe?g|png|svg|webp)"
)
FRAMEWORK_MARKERS = ("agentic-reporting", "super_agent_presentation", "super agent presentation")


class StudyError(ValueError):
    """Controlled invalid-input or invalid-study-state failure."""


_BENCHMARK_MODULE: ModuleType | None = None
_HOST_MODULE: ModuleType | None = None
_CHECKPOINT_IMAGE_SCANNER: ModuleType | None = None


def _load_benchmark_module() -> ModuleType:
    global _BENCHMARK_MODULE
    if _BENCHMARK_MODULE is not None:
        return _BENCHMARK_MODULE
    try:
        spec = importlib.util.spec_from_file_location(
            "_agentic_reporting_presentation_benchmark", BENCHMARK_SCRIPT
        )
        if spec is None or spec.loader is None:
            raise ImportError("no module loader is available")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name in ("validate_benchmark", "render_prompt", "evaluate_response"):
            if not callable(getattr(module, name, None)):
                raise ImportError(f"benchmark export is missing: {name}")
    except Exception as exc:
        raise StudyError(f"Cannot load benchmark engine {BENCHMARK_SCRIPT}: {exc}") from exc
    _BENCHMARK_MODULE = module
    return module


def _load_host_module() -> ModuleType:
    global _HOST_MODULE
    if _HOST_MODULE is not None:
        return _HOST_MODULE
    module_name = "_agentic_reporting_presentation_hosts"
    try:
        spec = importlib.util.spec_from_file_location(module_name, HOSTS_SCRIPT)
        if spec is None or spec.loader is None:
            raise ImportError("no module loader is available")
        module = importlib.util.module_from_spec(spec)
        # dataclasses resolves postponed annotations through sys.modules.
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        if not callable(getattr(module, "get_adapter", None)):
            raise ImportError("host registry export is missing: get_adapter")
    except Exception as exc:
        sys.modules.pop(module_name, None)
        raise StudyError(f"Cannot load host adapters {HOSTS_SCRIPT}: {exc}") from exc
    _HOST_MODULE = module
    return module


def _load_checkpoint_image_scanner() -> ModuleType:
    """Load the auditor-pinned Markdown image scanner without changing sys.path."""

    global _CHECKPOINT_IMAGE_SCANNER
    if _CHECKPOINT_IMAGE_SCANNER is not None:
        return _CHECKPOINT_IMAGE_SCANNER
    path = REPORTCTL_SCRIPT.with_name("markdown_image_scanner.py")
    module_name = "_agentic_reporting_study_markdown_image_scanner"
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError("no module loader is available")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        for name in ("scan_markdown_images", "decode_commonmark_entities"):
            if not callable(getattr(module, name, None)):
                raise ImportError(f"image scanner export is missing: {name}")
    except Exception as exc:
        sys.modules.pop(module_name, None)
        raise StudyError(f"Cannot load checkpoint image scanner {path}: {exc}") from exc
    _CHECKPOINT_IMAGE_SCANNER = module
    return module


def _terminal_safe_text(value: Any, *, preserve_newlines: bool = False) -> str:
    output: list[str] = []
    for character in str(value):
        codepoint = ord(character)
        if character == "\n" and preserve_newlines:
            output.append(character)
        elif codepoint < 0x20 or codepoint == 0x7F:
            escapes = {0x09: r"\t", 0x0A: r"\n", 0x0D: r"\r"}
            output.append(escapes.get(codepoint, f"\\x{codepoint:02x}"))
        elif 0x80 <= codepoint <= 0x9F or codepoint in UNSAFE_TERMINAL_CODEPOINTS:
            output.append(f"\\u{codepoint:04x}")
        else:
            output.append(character)
    return "".join(output)


def _safe_print(value: Any = "", *, file: Any = None, preserve_newlines: bool = False) -> None:
    print(_terminal_safe_text(value, preserve_newlines=preserve_newlines), file=file)


def _safe_json_dumps(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    return "".join(
        f"\\u{ord(character):04x}"
        if (
            ord(character) == 0x7F
            or 0x80 <= ord(character) <= 0x9F
            or ord(character) in UNSAFE_TERMINAL_CODEPOINTS
        )
        else character
        for character in rendered
    )


class _SafeArgumentParser(argparse.ArgumentParser):
    def _print_message(self, message: str | None, file: Any = None) -> None:
        if message:
            super()._print_message(_terminal_safe_text(message, preserve_newlines=True), file)

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {_terminal_safe_text(message)}\n")


def _reject_symlink_chain(path: Path, label: str) -> None:
    try:
        for component in [*reversed(path.parents), path]:
            if component.parent != Path(component.anchor) and component.is_symlink():
                raise StudyError(f"Refusing {label} with symlink component: {component}")
    except StudyError:
        raise
    except (OSError, RuntimeError) as exc:
        raise StudyError(f"Cannot inspect {label} path {path}: {exc}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
    except OSError as exc:
        raise StudyError(f"Cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def _read_bounded_bytes(path: Path, *, maximum: int, label: str) -> bytes:
    _reject_symlink_chain(path, label)
    try:
        metadata = path.stat()
    except OSError as exc:
        raise StudyError(f"Cannot inspect {label} {path}: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise StudyError(f"{label} must be a regular file: {path}")
    if metadata.st_size > maximum:
        raise StudyError(f"{label} exceeds {maximum} bytes: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise StudyError(f"Cannot read {label} {path}: {exc}") from exc


def _portable_workspace_relative_path(value: str, label: str) -> PurePosixPath:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 4096
        or "\\" in value
        or "\x00" in value
    ):
        raise StudyError(f"{label} must be a bounded portable workspace-relative path")
    relative = PurePosixPath(value)
    if (
        relative.is_absolute()
        or len(relative.parts) > 16
        or any(
            part in {"", ".", ".."}
            or len(part) > 255
            or re.fullmatch(r"[A-Za-z0-9._-]+", part) is None
            for part in relative.parts
        )
        or relative.as_posix() != value
    ):
        raise StudyError(f"{label} must be a canonical portable path inside the workspace")
    return relative


def _read_workspace_artifact(
    workspace: Path,
    path_text: str,
    *,
    maximum: int,
    label: str,
) -> tuple[PurePosixPath, bytes, dict[str, Any]]:
    """Read one agent-owned artifact without following any workspace path link."""

    required_flags = ("O_CLOEXEC", "O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
    if os.name != "posix" or any(not hasattr(os, name) for name in required_flags):
        raise StudyError("Controller checkpoint capture requires POSIX no-follow reads")
    relative = _portable_workspace_relative_path(path_text, label)
    root_descriptor = -1
    descriptor = -1
    opened_directories: list[int] = []
    flags = os.O_RDONLY | os.O_CLOEXEC
    directory_flags = flags | os.O_DIRECTORY | os.O_NOFOLLOW

    def validate_directory(
        metadata: os.stat_result, *, directory_label: str, private: bool
    ) -> None:
        if not stat.S_ISDIR(metadata.st_mode):
            raise StudyError(f"{directory_label} must be a regular directory")
        if metadata.st_uid != os.geteuid():
            raise StudyError(f"{directory_label} must be owned by the controller user")
        mode = stat.S_IMODE(metadata.st_mode)
        if private:
            if mode != 0o700:
                raise StudyError(f"{directory_label} must have mode 0700")
        elif mode & 0o022:
            raise StudyError(
                f"{directory_label} must not grant group or other write permissions"
            )

    try:
        root_descriptor = os.open(str(workspace), directory_flags)
        root_before = os.fstat(root_descriptor)
        validate_directory(
            root_before,
            directory_label=f"{label} workspace root",
            private=False,
        )
        parent_descriptor = root_descriptor
        for component in relative.parts[:-1]:
            next_descriptor = os.open(
                component,
                directory_flags,
                dir_fd=parent_descriptor,
            )
            metadata = os.fstat(next_descriptor)
            validate_directory(
                metadata,
                directory_label=f"{label} parent {component}",
                private=True,
            )
            opened_directories.append(next_descriptor)
            parent_descriptor = next_descriptor
        descriptor = os.open(
            relative.parts[-1],
            flags | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=parent_descriptor,
        )
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise StudyError(f"{label} must be a regular file")
        if before.st_nlink != 1:
            raise StudyError(f"{label} must have exactly one hard link")
        if before.st_uid != os.geteuid():
            raise StudyError(f"{label} must be owned by the controller user")
        if stat.S_IMODE(before.st_mode) != 0o600:
            raise StudyError(
                f"{label} must have mode 0600 without group or other permissions"
            )
        if before.st_size > maximum:
            raise StudyError(f"{label} exceeds {maximum} bytes")
        chunks: list[bytes] = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > maximum:
            raise StudyError(f"{label} exceeds {maximum} bytes")
        after = os.fstat(descriptor)
        stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(before, field) != getattr(after, field) for field in stable_fields):
            raise StudyError(f"{label} changed while the controller read it")
        if len(data) != after.st_size:
            raise StudyError(f"{label} size changed while the controller read it")
        root_after = os.fstat(root_descriptor)
        directory_stable_fields = ("st_dev", "st_ino", "st_mode", "st_uid", "st_ctime_ns")
        if any(
            getattr(root_before, field) != getattr(root_after, field)
            for field in directory_stable_fields
        ):
            raise StudyError(f"{label} workspace root changed during controller capture")
        for directory_descriptor in opened_directories:
            parent_after = os.fstat(directory_descriptor)
            validate_directory(
                parent_after,
                directory_label=f"{label} parent",
                private=True,
            )
        return relative, data, {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    except StudyError:
        raise
    except OSError as exc:
        raise StudyError(f"Cannot securely read {label}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        for directory_descriptor in reversed(opened_directories):
            os.close(directory_descriptor)
        if root_descriptor >= 0:
            os.close(root_descriptor)


def _read_json(path: Path, *, label: str = "JSON") -> dict[str, Any]:
    raw = _read_bounded_bytes(path, maximum=MAX_JSON_BYTES, label=label)

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-standard numeric constant {value}")

    def bounded_int(value: str) -> int:
        if len(value) > MAX_JSON_NUMBER_CHARS:
            raise ValueError(f"integer literal exceeds {MAX_JSON_NUMBER_CHARS} characters")
        return int(value)

    def bounded_float(value: str) -> float:
        if len(value) > MAX_JSON_NUMBER_CHARS:
            raise ValueError(f"floating-point literal exceeds {MAX_JSON_NUMBER_CHARS} characters")
        return float(value)

    try:
        decoded = raw.decode("utf-8")
        value = json.loads(
            decoded,
            parse_constant=reject_constant,
            parse_int=bounded_int,
            parse_float=bounded_float,
        )
    except UnicodeDecodeError as exc:
        raise StudyError(f"{label} must be UTF-8: {path}") from exc
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise StudyError(f"Invalid {label} in {path}: {exc}") from exc
    structure_error = _json_structure_limit_error(value)
    if structure_error:
        raise StudyError(f"Invalid {label} in {path}: {structure_error}")
    if not isinstance(value, dict):
        raise StudyError(f"{label} root must be an object: {path}")
    return value


def _json_structure_limit_error(value: Any) -> str | None:
    stack: list[tuple[Any, int]] = [(value, 1)]
    seen_containers: set[int] = set()
    count = 0
    while stack:
        item, depth = stack.pop()
        count += 1
        if count > MAX_JSON_VALUES:
            return f"JSON exceeds {MAX_JSON_VALUES} values"
        if depth > MAX_JSON_DEPTH:
            return f"JSON exceeds nesting depth {MAX_JSON_DEPTH}"
        if isinstance(item, dict):
            identity = id(item)
            if identity in seen_containers:
                continue
            seen_containers.add(identity)
            stack.extend((nested, depth + 1) for nested in item.values())
        elif isinstance(item, list):
            identity = id(item)
            if identity in seen_containers:
                continue
            seen_containers.add(identity)
            stack.extend((nested, depth + 1) for nested in item)
    return None


def _write_bytes_atomic(path: Path, data: bytes, *, mode: int = 0o600) -> None:
    _reject_symlink_chain(path, "output")
    if not path.parent.is_dir():
        raise StudyError(f"Output parent is not a directory: {path.parent}")
    descriptor = -1
    temporary = ""
    try:
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        raise StudyError(f"Cannot write {path}: {exc}") from exc


def _write_json_atomic(path: Path, value: Any, *, mode: int = 0o600) -> None:
    data = _json_bytes(value)
    _write_bytes_atomic(path, data, mode=mode)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _safe_relative_artifact(value: Any, label: str = "artifact path") -> PurePosixPath:
    if not isinstance(value, str) or not value or len(value) > 240:
        raise StudyError(f"{label} must be a nonempty relative path of at most 240 characters")
    relative = PurePosixPath(value)
    if relative.is_absolute() or len(relative.parts) > 12 or any(part in {"", ".", ".."} for part in relative.parts):
        raise StudyError(f"{label} must stay within its artifact root")
    if "\\" in value or not value.isascii() or not re.fullmatch(ARTIFACT_PATH_PATTERN, value):
        raise StudyError(f"{label} must use the bounded portable POSIX-path subset")
    suffix = relative.suffix
    if suffix not in ARTIFACT_MEDIA_TYPES:
        raise StudyError(f"{label} must use a supported renderable image suffix")
    return relative


def _checkpoint_local_artifact_targets(report_bytes: bytes) -> set[str]:
    """Return portable local image targets that must survive storage and blinding."""

    try:
        text = report_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StudyError("Checkpoint report must be UTF-8") from exc
    scanner = _load_checkpoint_image_scanner()
    try:
        records = scanner.scan_markdown_images(
            text,
            record_limit=MAX_ARTIFACTS + 1,
        )
    except (TypeError, ValueError) as exc:
        raise StudyError(f"Cannot scan checkpoint report images: {exc}") from exc
    if len(records) > MAX_ARTIFACTS:
        raise StudyError(
            f"Checkpoint report contains more than {MAX_ARTIFACTS} image references"
        )
    targets: set[str] = set()
    for index, record in enumerate(records):
        if not record.canonical:
            raise StudyError("Checkpoint report contains noncanonical image syntax")
        normalized = scanner.decode_commonmark_entities(record.target)
        try:
            parsed = urlsplit(normalized)
        except ValueError as exc:
            raise StudyError("Checkpoint report contains an invalid image target") from exc
        if parsed.scheme.casefold() in {"http", "https"} and parsed.netloc:
            continue
        if parsed.scheme or parsed.netloc or normalized.startswith("//"):
            raise StudyError("Checkpoint report contains an unsupported image target")
        local_path = unquote(parsed.path)
        relative = _safe_relative_artifact(
            local_path,
            f"checkpoint report local image {index}",
        )
        targets.add(relative.as_posix())
    return targets


def _artifact_destination(root: Path, relative: PurePosixPath) -> Path:
    destination = root.joinpath(*relative.parts)
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        if current.exists() or current.is_symlink():
            if current.is_symlink() or not current.is_dir():
                raise StudyError(f"Artifact parent is not a regular directory: {current}")
        else:
            current.mkdir(mode=0o700)
    return destination


def _artifact_record(value: Any, *, label: str) -> tuple[PurePosixPath, str, str]:
    if not isinstance(value, dict):
        raise StudyError(f"{label} must be an object")
    _require_object_shape(value, label, required=("path", "sha256", "media_type"))
    relative = _safe_relative_artifact(value["path"], f"{label} path")
    digest = value["sha256"]
    if (
        not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
    ):
        raise StudyError(f"{label} sha256 must be a lowercase SHA-256 digest")
    expected_media = ARTIFACT_MEDIA_TYPES[relative.suffix]
    if value["media_type"] != expected_media:
        raise StudyError(f"{label} media_type must be {expected_media}")
    return relative, digest, expected_media


def _copy_artifact(
    *,
    source_root: Path,
    destination_root: Path,
    relative: PurePosixPath,
    expected_sha256: str,
    label: str,
) -> int:
    source = source_root.joinpath(*relative.parts)
    data = _read_bounded_bytes(source, maximum=MAX_ARTIFACT_BYTES, label=label)
    if _sha256(source) != expected_sha256:
        raise StudyError(f"{label} does not match its declared SHA-256")
    destination = _artifact_destination(destination_root, relative)
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or not destination.is_file() or _sha256(destination) != expected_sha256:
            raise StudyError(f"Refusing to replace a different artifact: {destination}")
        return len(data)
    _write_bytes_atomic(destination, data, mode=0o600)
    return len(data)


def _directory_tree_sha256(root: Path, *, label: str) -> str:
    _reject_symlink_chain(root, label)
    if root.is_symlink() or not root.is_dir():
        raise StudyError(f"{label} must be a regular directory: {root}")
    records: list[dict[str, Any]] = []
    total_bytes = 0
    try:
        paths = sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
        for path in paths:
            if path.is_symlink():
                raise StudyError(f"{label} may not contain symlinks: {path}")
            if path.is_dir():
                continue
            if not path.is_file():
                raise StudyError(f"{label} contains an unsupported entry: {path}")
            if len(records) >= MAX_BLIND_TREE_ENTRIES:
                raise StudyError(f"{label} exceeds {MAX_BLIND_TREE_ENTRIES} files")
            size = path.stat().st_size
            total_bytes += size
            if total_bytes > MAX_BLIND_TREE_BYTES:
                raise StudyError(f"{label} exceeds {MAX_BLIND_TREE_BYTES} bytes")
            records.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": size,
                    "sha256": _sha256(path),
                }
            )
    except StudyError:
        raise
    except (OSError, RuntimeError) as exc:
        raise StudyError(f"Cannot inspect {label} {root}: {exc}") from exc
    canonical = json.dumps(records, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


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
    unknown_count = len(set(value) - allowed)
    if missing:
        raise StudyError(f"{label} is missing required fields: {', '.join(missing)}")
    if unknown_count:
        raise StudyError(f"{label} contains {unknown_count} unknown field(s)")


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 80:
        raise StudyError(f"{label} must be a nonempty string of at most 80 characters")
    if not (value[0].isascii() and (value[0].islower() or value[0].isdigit())):
        raise StudyError(f"{label} must start with a lowercase ASCII letter or digit")
    if not all(
        character.isascii()
        and (character.islower() or character.isdigit() or character == "-")
        for character in value
    ):
        raise StudyError(f"{label} must contain only lowercase ASCII letters, digits, and hyphens")
    return value


def _nonempty_string(value: Any, label: str, *, maximum: int = 1000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise StudyError(f"{label} must be a nonempty string of at most {maximum} characters")
    return value


def _number(value: Any, label: str, *, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise StudyError(f"{label} must be a finite number")
    numeric = float(value)
    if numeric < minimum or numeric > maximum:
        raise StudyError(f"{label} must be between {minimum} and {maximum}")
    return numeric


def _enum(
    value: Any,
    label: str,
    allowed: set[str],
    *,
    error: str | None = None,
) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise StudyError(error or f"{label} is unsupported")
    return value


def _validate_plan(plan: dict[str, Any], cases: dict[str, Any]) -> None:
    _require_object_shape(
        plan,
        "study plan",
        required=(
            "schema_version", "study_id", "study_kind", "claim_boundary", "benchmark",
            "framework", "execution", "models", "conditions", "seeds", "contexts",
            "generation", "rating", "analysis",
        ),
        optional=("$schema",),
    )
    if plan["schema_version"] != "1.0":
        raise StudyError("study plan schema_version must be 1.0")
    if "$schema" in plan:
        _nonempty_string(plan["$schema"], "study plan $schema")
    study_id = _identifier(plan["study_id"], "study_id")
    if len(study_id) < 3:
        raise StudyError("study_id must contain at least 3 characters")
    _enum(plan["study_kind"], "study_kind", STUDY_KINDS)
    _nonempty_string(plan["claim_boundary"], "claim_boundary", maximum=2000)
    benchmark = plan["benchmark"]
    if not isinstance(benchmark, dict):
        raise StudyError("benchmark must be an object")
    _require_object_shape(
        benchmark,
        "benchmark",
        required=(
            "benchmark_id", "cases_sha256", "case_ids", "heldout", "preregistration_receipt"
        ),
    )
    if benchmark["benchmark_id"] != cases.get("benchmark_id"):
        raise StudyError("benchmark_id does not match the supplied cases")
    if not isinstance(benchmark["cases_sha256"], str) or len(benchmark["cases_sha256"]) != 64:
        raise StudyError("cases_sha256 must be a lowercase SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in benchmark["cases_sha256"]):
        raise StudyError("cases_sha256 must be a lowercase SHA-256 hex digest")
    case_ids = benchmark["case_ids"]
    if not isinstance(case_ids, list) or not case_ids or len(case_ids) > MAX_CASE_IDS:
        raise StudyError(f"benchmark case_ids must contain from 1 to {MAX_CASE_IDS} records")
    for case_id in case_ids:
        _identifier(case_id, "case_id")
    if len(case_ids) != len(set(case_ids)):
        raise StudyError("benchmark case_ids must be unique")
    known_cases = {case.get("id") for case in cases.get("cases", []) if isinstance(case, dict)}
    for case_id in case_ids:
        if case_id not in known_cases:
            raise StudyError(f"Unknown case_id in study plan: {case_id}")
    if not isinstance(benchmark["heldout"], bool):
        raise StudyError("benchmark heldout must be boolean")
    if plan["study_kind"] == "pilot" and benchmark["heldout"]:
        raise StudyError("pilot studies must set benchmark heldout to false")
    receipt = benchmark["preregistration_receipt"]
    if receipt is not None:
        _nonempty_string(receipt, "preregistration_receipt", maximum=500)

    framework = plan["framework"]
    if not isinstance(framework, dict):
        raise StudyError("framework must be an object")
    _require_object_shape(
        framework,
        "framework",
        required=("repository", "commit_sha", "skill_manifest_sha256", "adapter_sha256"),
    )
    _nonempty_string(framework["repository"], "framework repository", maximum=500)
    if not isinstance(framework["commit_sha"], str) or not re.fullmatch(r"[0-9a-f]{40}", framework["commit_sha"]):
        raise StudyError("framework commit_sha must be a lowercase 40-character Git digest")
    if framework["commit_sha"] == "0" * 40:
        raise StudyError("framework commit_sha still contains the template placeholder")
    for field in ("skill_manifest_sha256", "adapter_sha256"):
        if not isinstance(framework[field], str) or not re.fullmatch(r"[0-9a-f]{64}", framework[field]):
            raise StudyError(f"framework {field} must be a lowercase SHA-256 digest")
        if framework[field] == "0" * 64:
            raise StudyError(f"framework {field} still contains the template placeholder")

    execution = plan["execution"]
    if not isinstance(execution, dict):
        raise StudyError("execution must be an object")
    _require_object_shape(
        execution,
        "execution",
        required=(
            "baseline_isolation", "isolation_receipt", "global_instruction_policy",
            "replicate_semantics",
        ),
    )
    _enum(
        execution["baseline_isolation"],
        "execution baseline_isolation",
        {"same-account-workspace", "external-sandbox"},
    )
    if execution["isolation_receipt"] is not None:
        _nonempty_string(execution["isolation_receipt"], "execution isolation_receipt", maximum=1000)
    _enum(
        execution["global_instruction_policy"],
        "execution global_instruction_policy",
        {"unverified", "shared-and-audited"},
    )
    _enum(
        execution["replicate_semantics"],
        "execution replicate_semantics",
        {"independent-repeat", "provider-seed"},
    )

    models = plan["models"]
    if not isinstance(models, list) or not models or len(models) > 20:
        raise StudyError("models must be a nonempty list of at most 20 records")
    model_ids: set[str] = set()
    for index, model in enumerate(models):
        if not isinstance(model, dict):
            raise StudyError(f"model {index} must be an object")
        _require_object_shape(
            model,
            f"model {index}",
            required=(
                "id", "host", "host_version", "model", "revision",
                "revision_receipt", "executable_sha256",
            ),
        )
        model_id = _identifier(model["id"], f"model {index} id")
        if model_id in model_ids:
            raise StudyError(f"duplicate model id: {model_id}")
        model_ids.add(model_id)
        _enum(model["host"], f"model {model_id} host", HOSTS)
        _nonempty_string(model["host_version"], f"model {model_id} host_version", maximum=200)
        _nonempty_string(model["model"], f"model {model_id} model", maximum=200)
        _nonempty_string(model["revision"], f"model {model_id} revision", maximum=200)
        if model["revision_receipt"] is not None:
            _nonempty_string(
                model["revision_receipt"],
                f"model {model_id} revision_receipt",
                maximum=1000,
            )
        executable_digest = model["executable_sha256"]
        if executable_digest is not None and (
            not isinstance(executable_digest, str)
            or len(executable_digest) != 64
            or any(character not in "0123456789abcdef" for character in executable_digest)
        ):
            raise StudyError(f"model {model_id} executable_sha256 is invalid")
        if model["host"] == "manual" and executable_digest is not None:
            raise StudyError(f"manual model {model_id} must set executable_sha256 to null")
        if model["host"] != "manual" and executable_digest is None:
            raise StudyError(f"executable host model {model_id} requires executable_sha256")

    if plan["conditions"] != list(CONDITIONS):
        raise StudyError("conditions must be exactly ['baseline', 'framework']")
    seeds = plan["seeds"]
    if not isinstance(seeds, list) or not seeds or len(seeds) > 100:
        raise StudyError("seeds must be a nonempty list of at most 100 integers")
    if any(isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 or seed > 2**31 - 1 for seed in seeds):
        raise StudyError("seeds must contain bounded nonnegative integers")
    if len(seeds) != len(set(seeds)):
        raise StudyError("seeds must be unique")

    contexts = plan["contexts"]
    if not isinstance(contexts, list) or not contexts or len(contexts) > 20:
        raise StudyError("contexts must be a nonempty list of at most 20 records")
    context_ids: set[str] = set()
    for index, context in enumerate(contexts):
        if not isinstance(context, dict):
            raise StudyError(f"context {index} must be an object")
        _require_object_shape(
            context,
            f"context {index}",
            required=("id", "target_occupancy_percent", "compaction_required"),
        )
        context_id = _identifier(context["id"], f"context {index} id")
        if len(context_id) < 2:
            raise StudyError(f"context {index} id must contain at least 2 characters")
        if context_id in context_ids:
            raise StudyError(f"duplicate context id: {context_id}")
        context_ids.add(context_id)
        _number(context["target_occupancy_percent"], f"context {context_id} occupancy", minimum=0, maximum=100)
        if not isinstance(context["compaction_required"], bool):
            raise StudyError(f"context {context_id} compaction_required must be boolean")

    generation = plan["generation"]
    if not isinstance(generation, dict):
        raise StudyError("generation must be an object")
    _require_object_shape(
        generation,
        "generation",
        required=("max_output_tokens", "timeout_seconds", "locale", "renderer"),
    )
    for field, maximum in (("max_output_tokens", 32_768), ("timeout_seconds", 86_400)):
        value = generation[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > maximum:
            raise StudyError(f"generation {field} must be an integer from 1 to {maximum}")
    _nonempty_string(generation["locale"], "generation locale", maximum=100)
    _nonempty_string(generation["renderer"], "generation renderer", maximum=200)

    rating = plan["rating"]
    if not isinstance(rating, dict):
        raise StudyError("rating must be an object")
    _require_object_shape(rating, "rating", required=("required_raters",))
    required_raters = rating["required_raters"]
    if isinstance(required_raters, bool) or not isinstance(required_raters, int) or not 2 <= required_raters <= 20:
        raise StudyError("required_raters must be an integer from 2 to 20")

    analysis = plan["analysis"]
    if not isinstance(analysis, dict):
        raise StudyError("analysis must be an object")
    _require_object_shape(
        analysis,
        "analysis",
        required=(
            "bootstrap_seed", "bootstrap_resamples", "primary_context_ids",
            "primary_dimensions", "thresholds",
        ),
    )
    if (
        isinstance(analysis["bootstrap_seed"], bool)
        or not isinstance(analysis["bootstrap_seed"], int)
        or not 0 <= analysis["bootstrap_seed"] <= 2**31 - 1
    ):
        raise StudyError("bootstrap_seed must be an integer from 0 to 2147483647")
    resamples = analysis["bootstrap_resamples"]
    if isinstance(resamples, bool) or not isinstance(resamples, int) or not 10_000 <= resamples <= 1_000_000:
        raise StudyError("bootstrap_resamples must be an integer from 10000 to 1000000")
    primary_contexts = analysis["primary_context_ids"]
    if not isinstance(primary_contexts, list) or not primary_contexts:
        raise StudyError("primary_context_ids must be a nonempty subset of context ids")
    for context_id in primary_contexts:
        value = _identifier(context_id, "primary context id")
        if len(value) < 2:
            raise StudyError("primary context ids must contain at least 2 characters")
    if len(primary_contexts) != len(set(primary_contexts)) or set(primary_contexts) - context_ids:
        raise StudyError("primary_context_ids must be a unique nonempty subset of context ids")
    primary_dimensions = analysis["primary_dimensions"]
    if not isinstance(primary_dimensions, list) or not primary_dimensions:
        raise StudyError("primary_dimensions must be unique known rating dimensions")
    if any(not isinstance(dimension, str) or dimension not in DIMENSIONS for dimension in primary_dimensions):
        raise StudyError("primary_dimensions must be unique known rating dimensions")
    if len(primary_dimensions) != len(set(primary_dimensions)):
        raise StudyError("primary_dimensions must be unique known rating dimensions")
    thresholds = analysis["thresholds"]
    if not isinstance(thresholds, dict) or set(thresholds) != THRESHOLD_FIELDS:
        raise StudyError("analysis thresholds must contain the complete supported threshold profile")
    for field, value in thresholds.items():
        upper = 10.0 if field in {"human_dimension_min", "priority_dimension_min", "primary_gain_min", "task_fidelity_margin"} else 1.0
        observed = _number(value, f"threshold {field}", minimum=0, maximum=upper)
        if observed != THRESHOLD_PROFILE[field]:
            raise StudyError(
                f"threshold {field} must equal the versioned release value "
                f"{THRESHOLD_PROFILE[field]}"
            )
    expected_records = len(case_ids) * len(models) * len(contexts) * len(seeds) * len(CONDITIONS)
    if expected_records > MAX_EXPECTED_RECORDS:
        raise StudyError(
            f"study matrix exceeds the {MAX_EXPECTED_RECORDS}-record safety limit"
        )
    pair_keys: set[str] = set()
    unit_ids: set[str] = set()
    for case_id in case_ids:
        for model in models:
            for context in contexts:
                for seed in seeds:
                    pair = _pair_key(case_id, model["id"], context["id"], seed)
                    if len(pair) > 240:
                        raise StudyError("composed pair key exceeds the 240-character path limit")
                    if pair in pair_keys:
                        raise StudyError("study identifiers produce a colliding composed pair key")
                    pair_keys.add(pair)
                    for condition in CONDITIONS:
                        unit_id = _record_unit_id(
                            case_id, model["id"], context["id"], seed, condition
                        )
                        if len(unit_id) > 240:
                            raise StudyError(
                                "composed generation unit_id exceeds the 240-character schema limit"
                            )
                        if unit_id in unit_ids:
                            raise StudyError(
                                "study identifiers produce a colliding generation unit_id"
                            )
                        unit_ids.add(unit_id)


def _validate_cases(cases: dict[str, Any], *, artifact_root: Path) -> None:
    module = _load_benchmark_module()
    try:
        module.validate_benchmark(cases, artifact_root=artifact_root)
    except Exception as exc:
        if isinstance(exc, getattr(module, "BenchmarkError", ())):
            raise StudyError(str(exc)) from exc
        raise


def _freeze_case_artifacts(cases: dict[str, Any], *, source_root: Path, run_dir: Path) -> dict[str, Any]:
    inputs_root = run_dir / "inputs"
    records_by_path: dict[str, dict[str, Any]] = {}
    total_bytes = 0
    for case in cases["cases"]:
        for path_text in case.get("artifacts", []):
            relative = _safe_relative_artifact(path_text, f"case {case['id']} artifact")
            source = source_root.joinpath(*relative.parts)
            data = _read_bounded_bytes(
                source,
                maximum=MAX_ARTIFACT_BYTES,
                label=f"case {case['id']} artifact",
            )
            digest = _sha256(source)
            total_bytes += len(data) if path_text not in records_by_path else 0
            if total_bytes > MAX_ARTIFACT_TOTAL_BYTES:
                raise StudyError("Frozen case artifacts exceed the total byte limit")
            record = records_by_path.get(path_text)
            if record is None:
                destination = _artifact_destination(inputs_root, relative)
                _write_bytes_atomic(destination, data, mode=0o600)
                records_by_path[path_text] = {
                    "path": path_text,
                    "sha256": digest,
                    "media_type": ARTIFACT_MEDIA_TYPES[relative.suffix],
                    "case_ids": [case["id"]],
                }
            elif case["id"] not in record["case_ids"]:
                record["case_ids"].append(case["id"])
    if len(records_by_path) > MAX_ARTIFACTS:
        raise StudyError(f"Frozen case artifacts exceed the {MAX_ARTIFACTS}-file limit")
    return {
        "schema_version": "1.0",
        "artifact_count": len(records_by_path),
        "total_bytes": total_bytes,
        "artifacts": [records_by_path[path] for path in sorted(records_by_path)],
    }


def _load_input_manifest(run_dir: Path) -> dict[str, Any]:
    manifest = _read_json(run_dir / "input-artifacts.json", label="frozen input artifact manifest")
    _require_object_shape(
        manifest,
        "frozen input artifact manifest",
        required=("schema_version", "artifact_count", "total_bytes", "artifacts"),
    )
    if manifest["schema_version"] != "1.0" or not isinstance(manifest["artifacts"], list):
        raise StudyError("Invalid frozen input artifact manifest")
    if manifest["artifact_count"] != len(manifest["artifacts"]) or manifest["artifact_count"] > MAX_ARTIFACTS:
        raise StudyError("Frozen input artifact count is invalid")
    observed_total = 0
    seen: set[str] = set()
    for index, record in enumerate(manifest["artifacts"]):
        if not isinstance(record, dict):
            raise StudyError("Frozen input artifact record must be an object")
        _require_object_shape(
            record,
            f"frozen input artifact {index}",
            required=("path", "sha256", "media_type", "case_ids"),
        )
        relative, digest, _ = _artifact_record(
            {field: record[field] for field in ("path", "sha256", "media_type")},
            label=f"frozen input artifact {index}",
        )
        if record["path"] in seen:
            raise StudyError("Frozen input artifact paths must be unique")
        seen.add(record["path"])
        if not isinstance(record["case_ids"], list) or not record["case_ids"]:
            raise StudyError("Frozen input artifact case_ids must be nonempty")
        source = run_dir / "inputs"
        path = source.joinpath(*relative.parts)
        data = _read_bounded_bytes(path, maximum=MAX_ARTIFACT_BYTES, label="frozen input artifact")
        if _sha256(path) != digest:
            raise StudyError(f"Frozen input artifact changed after init: {record['path']}")
        observed_total += len(data)
    if manifest["total_bytes"] != observed_total or observed_total > MAX_ARTIFACT_TOTAL_BYTES:
        raise StudyError("Frozen input artifact byte receipt is invalid")
    return manifest


def _input_artifacts_for_case(run_dir: Path, case_id: str) -> list[dict[str, Any]]:
    manifest = _load_input_manifest(run_dir)
    return [
        {field: record[field] for field in ("path", "sha256", "media_type")}
        for record in manifest["artifacts"]
        if case_id in record["case_ids"]
    ]


def _inside_git_worktree(path: Path) -> bool:
    candidate = path if path.exists() and path.is_dir() else path.parent
    for ancestor in (candidate, *candidate.parents):
        marker = ancestor / ".git"
        if marker.exists() or marker.is_symlink():
            return True
    return False


def _record_unit_id(case_id: str, model_id: str, context_id: str, seed: int, condition: str) -> str:
    return f"{case_id}--{model_id}--{context_id}--s{seed}--{condition}"


def _pair_key(case_id: str, model_id: str, context_id: str, seed: int) -> str:
    return f"{case_id}--{model_id}--{context_id}--s{seed}"


def _case_map(cases: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {case["id"]: case for case in cases["cases"]}


def _expected_records(plan: dict[str, Any], cases: dict[str, Any], prompts: Path) -> list[dict[str, Any]]:
    module = _load_benchmark_module()
    case_lookup = _case_map(cases)
    records: list[dict[str, Any]] = []
    for case_id in plan["benchmark"]["case_ids"]:
        for model in plan["models"]:
            for context in plan["contexts"]:
                for seed in plan["seeds"]:
                    pair = _pair_key(case_id, model["id"], context["id"], seed)
                    prompt_path = prompts / f"{pair}.txt"
                    if not prompt_path.exists():
                        prompt = module.render_prompt(case_lookup[case_id]).encode("utf-8")
                        _write_bytes_atomic(prompt_path, prompt, mode=0o600)
                    prompt_digest = _sha256(prompt_path)
                    for condition in CONDITIONS:
                        records.append(
                            {
                                "unit_id": _record_unit_id(case_id, model["id"], context["id"], seed, condition),
                                "pair_key": pair,
                                "case_id": case_id,
                                "model_id": model["id"],
                                "context_id": context["id"],
                                "seed": seed,
                                "condition": condition,
                                "prompt": f"prompts/{pair}.txt",
                                "prompt_sha256": prompt_digest,
                            }
                        )
    return records


def _load_run(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    _reject_symlink_chain(run_dir, "run directory")
    if not run_dir.is_dir():
        raise StudyError(f"Run directory does not exist: {run_dir}")
    try:
        mode = stat.S_IMODE(run_dir.stat().st_mode)
    except OSError as exc:
        raise StudyError(f"Cannot inspect run directory permissions: {exc}") from exc
    if mode & 0o077:
        raise StudyError("Run directory must not grant group or other permissions")
    plan = _read_json(run_dir / "plan.json", label="frozen plan")
    cases = _read_json(run_dir / "cases.json", label="frozen cases")
    expected = _read_json(run_dir / "expected-records.json", label="expected record matrix")
    lock = _read_json(run_dir / "run-lock.json", label="run lock")
    for filename in ("plan.json", "cases.json", "expected-records.json", "input-artifacts.json"):
        expected_digest = lock.get("sha256", {}).get(filename)
        if not isinstance(expected_digest, str) or _sha256(run_dir / filename) != expected_digest:
            raise StudyError(f"Frozen run input changed after init: {filename}")
    _load_input_manifest(run_dir)
    _validate_cases(cases, artifact_root=run_dir / "inputs")
    _validate_plan(plan, cases)
    return plan, cases, expected


def _copy_regular_file(source: Path, destination: Path, *, maximum: int, label: str) -> None:
    data = _read_bounded_bytes(source, maximum=maximum, label=label)
    _write_bytes_atomic(destination, data, mode=0o600)


def command_init(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    cases_path = Path(args.cases_file)
    output = Path(args.output)
    _reject_symlink_chain(output, "run output")
    if output.exists() or output.is_symlink():
        raise StudyError(f"Run output already exists: {output}")
    if _inside_git_worktree(output):
        raise StudyError("Study run output must be outside a Git worktree")
    plan = _read_json(plan_path, label="study plan")
    cases = _read_json(cases_path, label="benchmark cases")
    artifact_root = Path(args.artifact_root) if args.artifact_root else REPO_ROOT
    _validate_cases(cases, artifact_root=artifact_root)
    _validate_plan(plan, cases)
    if _sha256(cases_path) != plan.get("benchmark", {}).get("cases_sha256"):
        raise StudyError("Supplied cases do not match the preregistered cases_sha256")
    created = False
    try:
        output.mkdir(mode=0o700, parents=False)
        created = True
        for relative in ("private", "records", "prompts", "inputs"):
            (output / relative).mkdir(mode=0o700)
        _write_json_atomic(output / "plan.json", plan)
        _write_json_atomic(output / "cases.json", cases)
        input_manifest = _freeze_case_artifacts(
            cases,
            source_root=artifact_root,
            run_dir=output,
        )
        _write_json_atomic(output / "input-artifacts.json", input_manifest)
        expected_records = _expected_records(plan, cases, output / "prompts")
        expected = {"schema_version": "1.0", "study_id": plan["study_id"], "records": expected_records}
        expected_bytes = _json_bytes(expected)
        if len(expected_bytes) > MAX_JSON_BYTES:
            raise StudyError(
                "Expected record matrix exceeds the frozen JSON read limit; reduce the "
                "case, model, context, or repeat count"
            )
        _write_bytes_atomic(output / "expected-records.json", expected_bytes, mode=0o600)
        lock = {
            "schema_version": "1.0",
            "study_id": plan["study_id"],
            "sha256": {
                filename: _sha256(output / filename)
                for filename in (
                    "plan.json", "cases.json", "expected-records.json", "input-artifacts.json"
                )
            },
        }
        _write_json_atomic(output / "run-lock.json", lock)
    except Exception:
        if created:
            shutil.rmtree(output, ignore_errors=True)
        raise
    _safe_print(f"Initialized private study run: {output}")
    _safe_print(f"Expected generation records: {len(expected_records)}")
    return 0


def _validate_generation_record(
    record: dict[str, Any],
    *,
    plan: dict[str, Any],
    expected_record: dict[str, Any],
    host_execution_bound: bool = False,
) -> None:
    _require_object_shape(
        record,
        "generation record",
        required=(
            "schema_version", "study_id", "unit_id", "case_id", "model_id", "context_id",
            "seed", "condition", "host", "host_version", "model", "model_revision",
            "prompt_sha256", "response_sha256", "transcript_sha256", "artifacts", "usage",
            "observations",
        ),
        optional=("$schema",),
    )
    if record["schema_version"] != "1.0" or record["study_id"] != plan["study_id"]:
        raise StudyError("generation record version or study_id does not match the run")
    if "$schema" in record:
        _nonempty_string(record["$schema"], "generation record $schema")
        if record["$schema"] != "generation-record.schema.json":
            raise StudyError(
                "generation record $schema must identify generation-record.schema.json"
            )
    for field in ("unit_id", "case_id", "model_id", "context_id", "seed", "condition", "prompt_sha256"):
        if record[field] != expected_record[field]:
            raise StudyError(f"generation record {field} does not match the expected matrix")
    model = next(item for item in plan["models"] if item["id"] == record["model_id"])
    for field, expected in (
        ("host", model["host"]),
        ("host_version", model["host_version"]),
        ("model", model["model"]),
        ("model_revision", model["revision"]),
    ):
        if record[field] != expected:
            raise StudyError(f"generation record {field} does not match the frozen model")
    for field in ("response_sha256", "prompt_sha256"):
        digest = record[field]
        if not isinstance(digest, str) or len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise StudyError(f"generation record {field} must be a lowercase SHA-256 digest")
    transcript_digest = record["transcript_sha256"]
    if transcript_digest is not None and (
        not isinstance(transcript_digest, str)
        or len(transcript_digest) != 64
        or any(character not in "0123456789abcdef" for character in transcript_digest)
    ):
        raise StudyError("generation record transcript_sha256 is invalid")
    artifacts = record["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) > MAX_ARTIFACTS:
        raise StudyError(f"generation record artifacts must contain at most {MAX_ARTIFACTS} records")
    artifact_paths: set[str] = set()
    for index, artifact in enumerate(artifacts):
        relative, _, _ = _artifact_record(artifact, label=f"generation artifact {index}")
        path_text = relative.as_posix()
        if path_text in artifact_paths:
            raise StudyError("generation artifact paths must be unique")
        artifact_paths.add(path_text)

    usage = record["usage"]
    if not isinstance(usage, dict):
        raise StudyError("generation record usage must be an object")
    _require_object_shape(
        usage,
        "generation usage",
        required=(
            "input_tokens", "cached_input_tokens", "output_tokens", "latency_ms",
            "context_occupancy_percent", "compaction_observed",
        ),
    )
    for field in ("input_tokens", "cached_input_tokens", "output_tokens", "latency_ms"):
        value = usage[field]
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 10**12
        ):
            raise StudyError(f"generation usage {field} must be null or a bounded nonnegative integer")
    if usage["latency_ms"] is None:
        raise StudyError("generation usage latency_ms is required")
    if usage["context_occupancy_percent"] is not None:
        _number(usage["context_occupancy_percent"], "context occupancy", minimum=0, maximum=100)
    if usage["compaction_observed"] is not None and not isinstance(usage["compaction_observed"], bool):
        raise StudyError("compaction_observed must be boolean or null")

    observations = record["observations"]
    if not isinstance(observations, dict):
        raise StudyError("generation observations must be an object")
    _require_object_shape(
        observations,
        "generation observations",
        required=(
            "telemetry_source", "host_activation_observed", "skill_read", "checkpoint_created",
            "checkpoint_reloaded", "checkpoint_audit_passed", "final_audit_passed",
            "checkpoint_receipt_verified", "output_token_cap_enforced",
        ),
    )
    _enum(observations["telemetry_source"], "telemetry_source", {"manual", "host_adapter"})
    for field in (
        "host_activation_observed", "skill_read", "checkpoint_created",
        "checkpoint_reloaded", "checkpoint_audit_passed", "final_audit_passed",
        "checkpoint_receipt_verified", "output_token_cap_enforced",
    ):
        if observations[field] is not None and not isinstance(observations[field], bool):
            raise StudyError(f"generation observation {field} must be boolean or null")
    if model["host"] == "manual" and observations["telemetry_source"] != "manual":
        raise StudyError("Manual model records must use manual telemetry")
    if observations["telemetry_source"] == "host_adapter" and not host_execution_bound:
        raise StudyError(
            "host_adapter telemetry requires a controller-owned host execution binding"
        )
    if observations["output_token_cap_enforced"] is True and not host_execution_bound:
        raise StudyError(
            "An enforced output-token cap requires a controller-owned host execution binding"
        )
    if observations["checkpoint_receipt_verified"] is True:
        if (
            not host_execution_bound
            or record["condition"] != "framework"
            or observations["telemetry_source"] != "host_adapter"
        ):
            raise StudyError(
                "A verified checkpoint receipt requires a controller-owned host execution binding for a framework record"
            )
        required_observations = (
            "checkpoint_created",
            "checkpoint_reloaded",
            "checkpoint_audit_passed",
            "final_audit_passed",
        )
        if any(observations[field] is not True for field in required_observations):
            raise StudyError(
                "A verified checkpoint receipt requires the complete checkpoint command chain"
            )
    if host_execution_bound and observations["telemetry_source"] != "host_adapter":
        raise StudyError("A host execution binding requires host_adapter telemetry")


def command_import_output(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    plan, cases, expected = _load_run(run_dir)
    record = _read_json(Path(args.record), label="generation record")
    expected_by_id = {item["unit_id"]: item for item in expected["records"]}
    unit_id = record.get("unit_id")
    if not isinstance(unit_id, str) or not unit_id or len(unit_id) > 240:
        raise StudyError("generation record unit_id must be a bounded string")
    if unit_id not in expected_by_id:
        raise StudyError("generation record unit_id is not in the expected matrix")
    expected_record = expected_by_id[unit_id]
    host_binding_source = getattr(args, "host_binding", None)
    _validate_generation_record(
        record,
        plan=plan,
        expected_record=expected_record,
        host_execution_bound=host_binding_source is not None,
    )
    response_path = Path(args.response)
    response_bytes = _read_bounded_bytes(response_path, maximum=MAX_RESPONSE_BYTES, label="response")
    try:
        response_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StudyError("response must be UTF-8 Markdown") from exc
    if _sha256(response_path) != record["response_sha256"]:
        raise StudyError("response does not match response_sha256")
    artifact_root = Path(args.artifact_root) if args.artifact_root else response_path.parent
    _reject_symlink_chain(artifact_root, "generation artifact root")
    if not artifact_root.is_dir():
        raise StudyError(f"Generation artifact root must be a directory: {artifact_root}")
    total_artifact_bytes = 0
    validated_artifacts: list[tuple[PurePosixPath, str, str]] = []
    for index, artifact in enumerate(record["artifacts"]):
        relative, digest, media_type = _artifact_record(
            artifact,
            label=f"generation artifact {index}",
        )
        source = artifact_root.joinpath(*relative.parts)
        data = _read_bounded_bytes(source, maximum=MAX_ARTIFACT_BYTES, label="generation artifact")
        if _sha256(source) != digest:
            raise StudyError(f"generation artifact digest mismatch: {relative.as_posix()}")
        total_artifact_bytes += len(data)
        if total_artifact_bytes > MAX_ARTIFACT_TOTAL_BYTES:
            raise StudyError("Generation artifacts exceed the total byte limit")
        validated_artifacts.append((relative, digest, media_type))
    transcript_path = Path(args.transcript) if args.transcript else None
    if record["transcript_sha256"] is None and transcript_path is not None:
        raise StudyError("transcript was supplied but transcript_sha256 is null")
    if record["transcript_sha256"] is not None:
        if transcript_path is None:
            raise StudyError("transcript_sha256 requires --transcript")
        _read_bounded_bytes(transcript_path, maximum=MAX_TRANSCRIPT_BYTES, label="transcript")
        if _sha256(transcript_path) != record["transcript_sha256"]:
            raise StudyError("transcript does not match transcript_sha256")
    destination = run_dir / "records" / unit_id
    _reject_symlink_chain(destination, "record destination")
    if destination.exists() or destination.is_symlink():
        raise StudyError(f"Generation record already exists: {unit_id}")
    destination.mkdir(mode=0o700)
    try:
        _write_bytes_atomic(destination / "response.md", response_bytes)
        for artifact in _input_artifacts_for_case(run_dir, record["case_id"]):
            relative, digest, _ = _artifact_record(artifact, label="frozen case artifact")
            _copy_artifact(
                source_root=run_dir / "inputs",
                destination_root=destination,
                relative=relative,
                expected_sha256=digest,
                label="frozen case artifact",
            )
        for relative, digest, _ in validated_artifacts:
            _copy_artifact(
                source_root=artifact_root,
                destination_root=destination,
                relative=relative,
                expected_sha256=digest,
                label="generation artifact",
            )
        if transcript_path is not None:
            _copy_regular_file(
                transcript_path,
                destination / "transcript.jsonl",
                maximum=MAX_TRANSCRIPT_BYTES,
                label="transcript",
            )
        module = _load_benchmark_module()
        case = _case_map(cases)[record["case_id"]]
        try:
            machine = module.evaluate_response(
                case,
                destination / "response.md",
                artifact_root=destination,
            )
        except Exception as exc:
            if isinstance(exc, getattr(module, "BenchmarkError", ())):
                raise StudyError(str(exc)) from exc
            raise
        stored = dict(record)
        stored["$schema"] = "stored-generation-record.schema.json"
        stored["machine_evaluation"] = machine
        stored_record_path = destination / "record.json"
        _write_json_atomic(stored_record_path, stored)
        host_binding_path = destination / "host-execution-binding.json"
        if host_binding_source is not None:
            if not isinstance(host_binding_source, dict):
                raise StudyError("Internal host execution binding must be an object")
            _require_object_shape(
                host_binding_source,
                "internal host execution binding",
                required=("host_plan_sha256", "execution_receipt_sha256"),
            )
            for field in ("host_plan_sha256", "execution_receipt_sha256"):
                if not isinstance(host_binding_source[field], str) or not re.fullmatch(
                    r"[0-9a-f]{64}", host_binding_source[field]
                ):
                    raise StudyError(f"Internal host execution binding {field} is invalid")
            _write_json_atomic(
                host_binding_path,
                {
                    "schema_version": "1.0",
                    "study_id": plan["study_id"],
                    "unit_id": unit_id,
                    **host_binding_source,
                    "stored_record_sha256": _sha256(stored_record_path),
                },
                mode=0o600,
            )
        _write_json_atomic(
            destination / "record-lock.json",
            {
                "schema_version": "1.0",
                "study_id": plan["study_id"],
                "unit_id": unit_id,
                "stored_record_sha256": _sha256(stored_record_path),
                "response_sha256": _sha256(destination / "response.md"),
                "transcript_sha256": (
                    _sha256(destination / "transcript.jsonl")
                    if transcript_path is not None
                    else None
                ),
                "host_execution_binding_sha256": (
                    _sha256(host_binding_path) if host_binding_source is not None else None
                ),
            },
            mode=0o600,
        )
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    _safe_print(f"Imported generation record: {unit_id}")
    return 0


def _resolve_executable(path: Path) -> Path:
    if not path.is_absolute() or ".." in path.parts:
        raise StudyError("Host executable must be an exact absolute path without '..'")
    _reject_symlink_chain(path, "host executable")
    try:
        resolved = path.resolve(strict=True)
        metadata = resolved.stat()
    except (OSError, RuntimeError) as exc:
        raise StudyError(f"Cannot resolve host executable {path}: {exc}") from exc
    if resolved != path or not stat.S_ISREG(metadata.st_mode) or not metadata.st_mode & 0o111:
        raise StudyError("Host executable must be an executable regular file, not a symlink or launcher alias")
    return resolved


def _resolve_workspace(path: Path) -> Path:
    if not path.is_absolute() or ".." in path.parts:
        raise StudyError("Host workspace must be an exact absolute path without '..'")
    _reject_symlink_chain(path, "host workspace")
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise StudyError(f"Cannot resolve host workspace {path}: {exc}") from exc
    if resolved != path or not resolved.is_dir():
        raise StudyError("Host workspace must be a regular non-symlink directory")
    git_marker = resolved / ".git"
    if git_marker.is_symlink() or not git_marker.exists():
        raise StudyError("Host workspace must be an isolated Git worktree")
    return resolved


def _bounded_instruction(path: Path) -> tuple[str, str] | None:
    if not path.exists() and not path.is_symlink():
        return None
    raw = _read_bounded_bytes(path, maximum=MAX_JSON_BYTES, label="host instruction")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StudyError(f"Host instruction must be UTF-8: {path}") from exc
    return text, hashlib.sha256(raw).hexdigest()


def _skill_tree_receipt(root: Path) -> dict[str, Any]:
    _reject_symlink_chain(root, "installed Skill")
    if root.is_symlink() or not root.is_dir():
        raise StudyError(f"Installed Skill must be a regular directory: {root}")
    records: list[dict[str, Any]] = []
    total_bytes = 0
    scanned_entries = 0
    pending_directories = [root]
    try:
        while pending_directories:
            directory = pending_directories.pop()
            with os.scandir(directory) as entries:
                for entry in entries:
                    # Count ignored entries too, so cache-like names cannot evade
                    # the traversal resource bound.
                    scanned_entries += 1
                    if scanned_entries > MAX_SKILL_TREE_ENTRIES:
                        raise StudyError(
                            f"Installed Skill exceeds {MAX_SKILL_TREE_ENTRIES} entries"
                        )
                    path = Path(entry.path)
                    relative = path.relative_to(root)
                    metadata = entry.stat(follow_symlinks=False)
                    if stat.S_ISLNK(metadata.st_mode):
                        raise StudyError(f"Installed Skill may not contain symlinks: {path}")
                    is_directory = stat.S_ISDIR(metadata.st_mode)
                    is_file = stat.S_ISREG(metadata.st_mode)
                    if not is_directory and not is_file:
                        raise StudyError(f"Installed Skill contains an unsupported entry: {path}")
                    inside_pycache = "__pycache__" in relative.parts
                    if is_directory and not inside_pycache:
                        pending_directories.append(path)
                    if (
                        inside_pycache
                        or relative.suffix == ".pyc"
                        or relative.name == ".DS_Store"
                    ):
                        continue
                    if is_directory:
                        records.append({"path": relative.as_posix(), "kind": "directory"})
                        continue
                    size = metadata.st_size
                    total_bytes += size
                    if total_bytes > MAX_SKILL_TREE_BYTES:
                        raise StudyError(
                            f"Installed Skill exceeds {MAX_SKILL_TREE_BYTES} bytes"
                        )
                    records.append(
                        {
                            "path": relative.as_posix(),
                            "kind": "file",
                            "bytes": size,
                            "sha256": _sha256(path),
                        }
                    )
    except StudyError:
        raise
    except (OSError, RuntimeError) as exc:
        raise StudyError(f"Cannot inspect installed Skill {root}: {exc}") from exc
    records.sort(key=lambda record: record["path"])
    canonical = json.dumps(records, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return {
        "path": ".agents/skills/agentic-reporting",
        "entry_count": len(records),
        "total_bytes": total_bytes,
        "manifest_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def _workspace_receipt(workspace: Path, condition: str) -> dict[str, Any]:
    instruction_candidates = (workspace / "AGENTS.override.md", workspace / "AGENTS.md")
    active_instruction: Path | None = None
    instruction_text = ""
    instruction_digest: str | None = None
    for candidate in instruction_candidates:
        loaded = _bounded_instruction(candidate)
        if loaded is not None and loaded[0].strip():
            active_instruction = candidate
            instruction_text, instruction_digest = loaded
            break
    marker_present = any(marker in instruction_text.casefold() for marker in FRAMEWORK_MARKERS)
    skill_root = workspace / ".agents" / "skills" / "agentic-reporting"
    alternate_roots = (
        workspace / "skills" / "agentic-reporting",
        workspace / ".codex" / "skills" / "agentic-reporting",
    )
    if condition == "baseline":
        if marker_present or skill_root.exists() or skill_root.is_symlink() or any(
            path.exists() or path.is_symlink() for path in alternate_roots
        ):
            raise StudyError("Baseline workspace contains project-local agentic-reporting material")
        activation = {
            "state": "clean",
            "active_instruction": (
                {
                    "path": active_instruction.relative_to(workspace).as_posix(),
                    "sha256": instruction_digest,
                }
                if active_instruction is not None
                else None
            ),
            "skill": None,
        }
    elif condition == "framework":
        if not marker_present or active_instruction is None:
            raise StudyError("Framework workspace lacks an active project instruction marker")
        if not (skill_root / "SKILL.md").is_file():
            raise StudyError("Framework workspace lacks the installed agentic-reporting Skill")
        activation = {
            "state": "installed",
            "active_instruction": {
                "path": active_instruction.relative_to(workspace).as_posix(),
                "sha256": instruction_digest,
            },
            "skill": _skill_tree_receipt(skill_root),
        }
    else:
        raise StudyError(f"Unsupported study condition: {condition}")
    return {
        "git_marker_kind": "directory" if (workspace / ".git").is_dir() else "file",
        "activation": activation,
    }


def _host_plan_path(run_dir: Path, unit_id: str) -> Path:
    return run_dir / "private" / "host-plans" / f"{unit_id}.json"


def _host_plan_lock_path(run_dir: Path, unit_id: str) -> Path:
    return run_dir / "private" / "host-plans" / f"{unit_id}.lock.json"


def _host_adapter_source_sha256() -> str:
    """Identify the reviewed adapter implementation used to construct host argv."""

    return _sha256(HOSTS_SCRIPT)


def _checkpoint_auditor_receipt(skill_root: Path | None = None) -> dict[str, Any]:
    """Fingerprint the complete fixed-path dependency closure for strict audit."""

    root = (
        skill_root
        if skill_root is not None
        else REPO_ROOT / "skills" / "agentic-reporting"
    )
    files: list[dict[str, Any]] = []
    for relative in CHECKPOINT_AUDITOR_RELATIVE_FILES:
        path = root.joinpath(*relative.parts)
        data = _read_bounded_bytes(
            path,
            maximum=MAX_JSON_BYTES,
            label="checkpoint auditor dependency",
        )
        files.append(
            {
                "path": relative.as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    canonical = json.dumps(
        files, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return {
        "profile": "reportctl-audit-closure-v1",
        "files": files,
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }


def _checkpoint_auditor_sha256() -> str:
    """Identify the controller-owned strict-audit dependency closure."""

    return _checkpoint_auditor_receipt()["sha256"]


def _compose_host_prompt(prompt: bytes, agent_contract: str | None) -> bytes:
    if agent_contract is None:
        return prompt
    separator = b"\n\n" if prompt.endswith(b"\n") else b"\n\n\n"
    return prompt + separator + agent_contract.encode("utf-8") + b"\n"


def _prepare_checkpoint_capture_workspace(
    workspace: Path, profile: dict[str, Any]
) -> None:
    if not profile["enabled"]:
        return
    if os.name != "posix" or not hasattr(os, "geteuid"):
        raise StudyError("Framework checkpoint capture workspace requires POSIX modes")
    capture_directory = workspace / profile["workspace_directory"]
    _reject_symlink_chain(capture_directory, "checkpoint capture directory")
    if capture_directory.exists() or capture_directory.is_symlink():
        raise StudyError(
            "Framework study workspace checkpoint capture directory must start absent"
        )
    try:
        capture_directory.mkdir(mode=0o700)
        capture_directory.chmod(0o700)
        _write_bytes_atomic(
            capture_directory / ".gitignore",
            CHECKPOINT_CAPTURE_IGNORE_BYTES,
            mode=0o600,
        )
        for index, artifact in enumerate(profile["artifact_mirror"]):
            relative, digest, _ = _artifact_record(
                artifact,
                label=f"checkpoint artifact mirror {index}",
            )
            _copy_artifact(
                source_root=workspace,
                destination_root=capture_directory,
                relative=relative,
                expected_sha256=digest,
                label="checkpoint artifact mirror",
            )
        metadata = capture_directory.stat()
    except OSError as exc:
        raise StudyError(f"Cannot prepare checkpoint capture directory: {exc}") from exc
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise StudyError("Checkpoint capture directory is not owner-only")


def _verify_checkpoint_artifact_mirror(
    workspace: Path,
    profile: dict[str, Any],
    *,
    required_paths: set[str] | None = None,
) -> None:
    """Verify private report-relative copies against their frozen artifact receipts."""

    artifacts = {
        artifact["path"]: artifact for artifact in profile["artifact_mirror"]
    }
    selected = set(artifacts) if required_paths is None else required_paths
    if not selected.issubset(artifacts):
        raise StudyError("Checkpoint report references an unmirrored local image")
    for path_text in sorted(selected):
        artifact = artifacts[path_text]
        relative, digest, _ = _artifact_record(
            artifact,
            label="checkpoint artifact mirror",
        )
        mirror_path = PurePosixPath(profile["workspace_directory"]) / relative
        _, _, evidence = _read_workspace_artifact(
            workspace,
            mirror_path.as_posix(),
            maximum=MAX_ARTIFACT_BYTES,
            label="checkpoint artifact mirror",
        )
        if evidence["sha256"] != digest:
            raise StudyError(f"Checkpoint artifact mirror changed: {path_text}")


def command_host_plan(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    plan, _, expected = _load_run(run_dir)
    expected_by_id = {item["unit_id"]: item for item in expected["records"]}
    if args.unit_id not in expected_by_id:
        raise StudyError("host-plan unit_id is not in the expected matrix")
    unit = expected_by_id[args.unit_id]
    model = next(item for item in plan["models"] if item["id"] == unit["model_id"])
    if model["host"] == "manual":
        raise StudyError("Manual generation records do not have an executable host plan")
    adapter_source_digest = _host_adapter_source_sha256()
    host_module = _load_host_module()
    try:
        adapter = host_module.get_adapter(model["host"])
    except Exception as exc:
        raise StudyError(str(exc)) from exc
    executable = _resolve_executable(Path(args.executable))
    executable_digest = _sha256(executable)
    if executable_digest != model["executable_sha256"]:
        raise StudyError("Host executable does not match the preregistered SHA-256")
    workspace = _resolve_workspace(Path(args.workspace))
    workspace_receipt = _workspace_receipt(workspace, unit["condition"])
    checkpoint_auditor_receipt = _checkpoint_auditor_receipt()
    checkpoint_auditor_digest = checkpoint_auditor_receipt["sha256"]
    if unit["condition"] == "framework":
        activation = workspace_receipt["activation"]
        if activation["skill"]["manifest_sha256"] != plan["framework"]["skill_manifest_sha256"]:
            raise StudyError("Installed Skill does not match the preregistered framework manifest")
        if activation["active_instruction"]["sha256"] != plan["framework"]["adapter_sha256"]:
            raise StudyError("Active host instruction does not match the preregistered adapter digest")
        installed_skill_root = workspace / ".agents" / "skills" / "agentic-reporting"
        if _checkpoint_auditor_receipt(installed_skill_root) != checkpoint_auditor_receipt:
            raise StudyError(
                "Installed checkpoint auditor closure does not match the controller-owned implementation"
            )
    context = next(item for item in plan["contexts"] if item["id"] == unit["context_id"])
    capture_enabled = unit["condition"] == "framework"
    agent_contract = CHECKPOINT_AGENT_CONTRACT if capture_enabled else None
    checkpoint_capture_profile = {
        "enabled": capture_enabled,
        "required": capture_enabled and context["compaction_required"],
        "capture_protocol": "posix-openat-event-snapshot-v1",
        "assurance": "controller-event-snapshot-final-audit",
        "workspace_directory": CHECKPOINT_CAPTURE_DIRECTORY,
        "checkpoint_path": CHECKPOINT_CAPTURE_PATH,
        "report_path": CHECKPOINT_REPORT_PATH,
        "ignore_path": CHECKPOINT_CAPTURE_IGNORE_PATH,
        "ignore_sha256": hashlib.sha256(CHECKPOINT_CAPTURE_IGNORE_BYTES).hexdigest(),
        "directory_mode": "0700",
        "file_mode": "0600",
        "artifact_mirror": (
            _input_artifacts_for_case(run_dir, unit["case_id"])
            if capture_enabled
            else []
        ),
        "agent_contract": agent_contract,
        "agent_contract_sha256": (
            hashlib.sha256(agent_contract.encode("utf-8")).hexdigest()
            if agent_contract is not None
            else None
        ),
    }
    prompt_path = run_dir / unit["prompt"]
    prompt_bytes = _read_bounded_bytes(
        prompt_path, maximum=MAX_RESPONSE_BYTES, label="frozen host-plan prompt"
    )
    if hashlib.sha256(prompt_bytes).hexdigest() != unit["prompt_sha256"]:
        raise StudyError("Frozen host-plan prompt changed")
    host_prompt_sha256 = hashlib.sha256(
        _compose_host_prompt(prompt_bytes, agent_contract)
    ).hexdigest()
    planned_command = adapter.build_command(
        executable=executable,
        workspace=workspace,
        response_path=run_dir / "private" / "host-executions" / unit["unit_id"] / "response.md",
        model=model["model"],
        max_output_tokens=plan["generation"]["max_output_tokens"],
    )
    if _host_adapter_source_sha256() != adapter_source_digest:
        raise StudyError("Host adapter source changed while building host-plan")
    host_plan = {
        "schema_version": "1.1",
        "study_id": plan["study_id"],
        "unit_id": unit["unit_id"],
        "condition": unit["condition"],
        "host": model["host"],
        "host_version": model["host_version"],
        "model": model["model"],
        "model_revision": model["revision"],
        "executable": str(executable),
        "executable_sha256": executable_digest,
        "host_adapter_source_sha256": adapter_source_digest,
        "checkpoint_auditor_sha256": checkpoint_auditor_digest,
        "checkpoint_auditor_receipt": checkpoint_auditor_receipt,
        "workspace": str(workspace),
        "workspace_receipt": workspace_receipt,
        "prompt_sha256": unit["prompt_sha256"],
        "host_prompt_sha256": host_prompt_sha256,
        "planned_argv": list(planned_command.argv),
        "planned_transcript_format": planned_command.transcript_format,
        "command_profile": {
            "shell": False,
            "sandbox": "workspace-write",
            "ephemeral": True,
            "ignore_user_config": True,
            "ignore_project_exec_rules": True,
            "transcript": "jsonl",
            "explicit_execution_required": True,
            "output_token_cap_enforced": planned_command.output_token_cap_enforced,
        },
        "checkpoint_capture_profile": checkpoint_capture_profile,
    }
    plans_dir = run_dir / "private" / "host-plans"
    if not plans_dir.exists():
        plans_dir.mkdir(mode=0o700)
    path = _host_plan_path(run_dir, unit["unit_id"])
    lock_path = _host_plan_lock_path(run_dir, unit["unit_id"])
    if path.exists() or path.is_symlink() or lock_path.exists() or lock_path.is_symlink():
        raise StudyError(f"Host plan already exists: {unit['unit_id']}")
    _write_json_atomic(path, host_plan, mode=0o600)
    _write_json_atomic(
        lock_path,
        {
            "schema_version": "1.0",
            "study_id": plan["study_id"],
            "unit_id": unit["unit_id"],
            "host_plan_sha256": _sha256(path),
        },
        mode=0o600,
    )
    _safe_print(f"Frozen host plan without executing: {path}")
    return 0


def _load_host_plan(run_dir: Path, unit_id: str) -> dict[str, Any]:
    path = _host_plan_path(run_dir, unit_id)
    lock = _read_json(_host_plan_lock_path(run_dir, unit_id), label="host plan lock")
    if lock.get("host_plan_sha256") != _sha256(path):
        raise StudyError("Host plan changed after it was frozen")
    host_plan = _read_json(path, label="host plan")
    version = host_plan.get("schema_version")
    if version not in {"1.0", "1.1"}:
        raise StudyError("Unsupported frozen host plan schema version")
    _require_object_shape(
        host_plan,
        "host plan",
        required=(
            "schema_version", "study_id", "unit_id", "condition", "host", "host_version",
            "model", "model_revision", "executable", "executable_sha256",
            "host_adapter_source_sha256", "workspace", "workspace_receipt",
            "prompt_sha256", "planned_argv", "planned_transcript_format",
            "command_profile",
        ) + (
            (
                "checkpoint_auditor_sha256", "checkpoint_auditor_receipt",
                "checkpoint_capture_profile", "host_prompt_sha256",
            )
            if version == "1.1"
            else ()
        ),
    )
    adapter_digest = host_plan["host_adapter_source_sha256"]
    if not isinstance(adapter_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", adapter_digest):
        raise StudyError("Frozen host plan adapter source digest is invalid")
    planned_argv = host_plan["planned_argv"]
    if (
        not isinstance(planned_argv, list)
        or not planned_argv
        or len(planned_argv) > 64
        or any(
            not isinstance(token, str) or not token or len(token) > 4096
            for token in planned_argv
        )
        or sum(len(token) for token in planned_argv) > 32_768
    ):
        raise StudyError("Frozen host plan argv is invalid")
    _nonempty_string(
        host_plan["planned_transcript_format"],
        "frozen host plan transcript format",
        maximum=200,
    )
    if version == "1.1":
        auditor_digest = host_plan["checkpoint_auditor_sha256"]
        if not isinstance(auditor_digest, str) or not re.fullmatch(
            r"[0-9a-f]{64}", auditor_digest
        ):
            raise StudyError("Frozen host plan checkpoint auditor digest is invalid")
        auditor_receipt = host_plan["checkpoint_auditor_receipt"]
        if not isinstance(auditor_receipt, dict):
            raise StudyError("Frozen checkpoint auditor receipt must be an object")
        _require_object_shape(
            auditor_receipt,
            "frozen checkpoint auditor receipt",
            required=("profile", "files", "sha256"),
        )
        if (
            auditor_receipt["profile"] != "reportctl-audit-closure-v1"
            or auditor_receipt["sha256"] != auditor_digest
            or not isinstance(auditor_receipt["files"], list)
            or len(auditor_receipt["files"])
            != len(CHECKPOINT_AUDITOR_RELATIVE_FILES)
        ):
            raise StudyError("Frozen checkpoint auditor receipt is invalid")
        expected_paths = [path.as_posix() for path in CHECKPOINT_AUDITOR_RELATIVE_FILES]
        canonical_files: list[dict[str, Any]] = []
        for index, file_receipt in enumerate(auditor_receipt["files"]):
            if not isinstance(file_receipt, dict):
                raise StudyError("Frozen checkpoint auditor file receipt is invalid")
            _require_object_shape(
                file_receipt,
                "frozen checkpoint auditor file receipt",
                required=("path", "bytes", "sha256"),
            )
            if (
                file_receipt["path"] != expected_paths[index]
                or isinstance(file_receipt["bytes"], bool)
                or not isinstance(file_receipt["bytes"], int)
                or file_receipt["bytes"] < 1
                or file_receipt["bytes"] > MAX_JSON_BYTES
                or not isinstance(file_receipt["sha256"], str)
                or re.fullmatch(r"[0-9a-f]{64}", file_receipt["sha256"]) is None
            ):
                raise StudyError("Frozen checkpoint auditor file receipt is invalid")
            canonical_files.append(file_receipt)
        canonical = json.dumps(
            canonical_files,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        if hashlib.sha256(canonical).hexdigest() != auditor_digest:
            raise StudyError("Frozen checkpoint auditor closure digest is invalid")
        profile = host_plan["checkpoint_capture_profile"]
        if not isinstance(profile, dict):
            raise StudyError("Frozen checkpoint capture profile must be an object")
        _require_object_shape(
            profile,
            "frozen checkpoint capture profile",
            required=(
                "enabled", "required", "capture_protocol", "assurance",
                "workspace_directory", "checkpoint_path", "report_path",
                "ignore_path", "ignore_sha256",
                "directory_mode", "file_mode", "artifact_mirror", "agent_contract",
                "agent_contract_sha256",
            ),
        )
        if not isinstance(profile["enabled"], bool) or not isinstance(
            profile["required"], bool
        ):
            raise StudyError("Frozen checkpoint capture booleans are invalid")
        if profile["required"] and not profile["enabled"]:
            raise StudyError("A required checkpoint capture profile must be enabled")
        if (
            profile["capture_protocol"] != "posix-openat-event-snapshot-v1"
            or profile["assurance"] != "controller-event-snapshot-final-audit"
            or profile["workspace_directory"] != CHECKPOINT_CAPTURE_DIRECTORY
            or profile["checkpoint_path"] != CHECKPOINT_CAPTURE_PATH
            or profile["report_path"] != CHECKPOINT_REPORT_PATH
            or profile["ignore_path"] != CHECKPOINT_CAPTURE_IGNORE_PATH
            or profile["ignore_sha256"]
            != hashlib.sha256(CHECKPOINT_CAPTURE_IGNORE_BYTES).hexdigest()
            or profile["directory_mode"] != "0700"
            or profile["file_mode"] != "0600"
        ):
            raise StudyError("Frozen checkpoint capture profile is unsupported")
        artifact_mirror = profile["artifact_mirror"]
        if (
            not isinstance(artifact_mirror, list)
            or len(artifact_mirror) > MAX_ARTIFACTS
        ):
            raise StudyError("Frozen checkpoint artifact mirror is invalid")
        seen_artifact_paths: set[str] = set()
        for index, artifact in enumerate(artifact_mirror):
            relative, _, _ = _artifact_record(
                artifact,
                label=f"frozen checkpoint artifact mirror {index}",
            )
            if relative.as_posix() in seen_artifact_paths:
                raise StudyError("Frozen checkpoint artifact mirror paths must be unique")
            seen_artifact_paths.add(relative.as_posix())
        if not profile["enabled"] and artifact_mirror:
            raise StudyError("Disabled checkpoint capture cannot mirror artifacts")
        contract = profile["agent_contract"]
        contract_digest = profile["agent_contract_sha256"]
        if profile["enabled"]:
            if (
                not isinstance(contract, str)
                or not contract
                or len(contract) > 2_000
                or not isinstance(contract_digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", contract_digest) is None
                or hashlib.sha256(contract.encode("utf-8")).hexdigest()
                != contract_digest
            ):
                raise StudyError("Frozen checkpoint capture agent contract is invalid")
        elif contract is not None or contract_digest is not None:
            raise StudyError("Frozen checkpoint capture agent contract is invalid")
        host_prompt_digest = host_plan["host_prompt_sha256"]
        if not isinstance(host_prompt_digest, str) or re.fullmatch(
            r"[0-9a-f]{64}", host_prompt_digest
        ) is None:
            raise StudyError("Frozen host prompt digest is invalid")
    return host_plan


def _stage_case_inputs(run_dir: Path, workspace: Path, case_id: str) -> list[dict[str, Any]]:
    staged: list[dict[str, Any]] = []
    for artifact in _input_artifacts_for_case(run_dir, case_id):
        relative, digest, _ = _artifact_record(artifact, label="host input artifact")
        destination = workspace.joinpath(*relative.parts)
        existed = destination.exists() or destination.is_symlink()
        _copy_artifact(
            source_root=run_dir / "inputs",
            destination_root=workspace,
            relative=relative,
            expected_sha256=digest,
            label="host input artifact",
        )
        if not existed:
            try:
                destination.chmod(0o400)
            except OSError as exc:
                raise StudyError(f"Cannot make staged input read-only: {destination}: {exc}") from exc
        staged.append({**artifact, "created_for_run": not existed})
    return staged


def _finalize_checkpoint_artifact_receipt(
    *,
    plan: dict[str, Any],
    unit: dict[str, Any],
    host_plan: dict[str, Any],
    host_plan_sha256: str,
    execution_root: Path,
    response_bytes: bytes,
    transcript_sha256: str,
    telemetry: Any,
    capture_state: dict[str, Any],
) -> dict[str, Any] | None:
    """Promote one unambiguous event-snapshot chain into private evidence."""

    if (
        unit["condition"] != "framework"
        or host_plan.get("schema_version") != "1.1"
        or not host_plan["checkpoint_capture_profile"]["enabled"]
        or capture_state.get("invalid") is True
    ):
        return None
    captures = capture_state.get("events")
    if not isinstance(captures, list) or len(captures) != 3:
        return None
    if [item.get("phase") for item in captures] != ["create", "reload", "audit"]:
        return None
    capture_profile = host_plan["checkpoint_capture_profile"]
    checkpoint_paths = [item.get("checkpoint_path") for item in captures]
    if checkpoint_paths != [capture_profile["checkpoint_path"]] * 3:
        return None
    if [item.get("report_path") for item in captures] != [
        None,
        None,
        capture_profile["report_path"],
    ]:
        return None
    ordinals = [item.get("event_ordinal") for item in captures]
    if (
        any(isinstance(value, bool) or not isinstance(value, int) for value in ordinals)
        or ordinals != sorted(ordinals)
        or len(set(ordinals)) != 3
    ):
        return None
    telemetry_events = [
        (
            event.phase,
            event.event_ordinal,
            event.checkpoint_path,
            event.report_path,
        )
        for event in telemetry.checkpoint_events
    ]
    captured_events = [
        (
            item["phase"],
            item["event_ordinal"],
            item["checkpoint_path"],
            item.get("report_path"),
        )
        for item in captures
    ]
    if telemetry_events != captured_events:
        return None
    if not (
        telemetry.checkpoint_created
        and telemetry.checkpoint_reloaded
        and telemetry.checkpoint_audit_passed
        and telemetry.final_audit_passed
    ):
        return None
    checkpoint_buffers = [item.get("checkpoint_bytes") for item in captures]
    if any(not isinstance(value, bytes) for value in checkpoint_buffers):
        return None
    if not all(value == checkpoint_buffers[0] for value in checkpoint_buffers[1:]):
        return None
    report_bytes = captures[-1].get("report_bytes")
    if not isinstance(report_bytes, bytes) or report_bytes != response_bytes:
        return None
    try:
        local_image_targets = _checkpoint_local_artifact_targets(report_bytes)
    except StudyError:
        return None
    mirrored_artifact_paths = {
        artifact["path"] for artifact in capture_profile["artifact_mirror"]
    }
    if not local_image_targets.issubset(mirrored_artifact_paths):
        return None
    workspace = Path(host_plan["workspace"])
    try:
        _verify_checkpoint_artifact_mirror(
            workspace,
            capture_profile,
            required_paths=local_image_targets,
        )
    except StudyError:
        return None
    if host_plan["checkpoint_auditor_sha256"] != _checkpoint_auditor_sha256():
        return None

    capture_directory = workspace / capture_profile[
        "workspace_directory"
    ]
    checkpoint_descriptor = -1
    report_descriptor = -1
    checkpoint_temporary = ""
    report_temporary = ""
    try:
        checkpoint_descriptor, checkpoint_temporary = tempfile.mkstemp(
            prefix=".controller-reaudit-checkpoint.",
            suffix=".json",
            dir=str(capture_directory),
        )
        os.fchmod(checkpoint_descriptor, 0o600)
        with os.fdopen(checkpoint_descriptor, "wb") as handle:
            checkpoint_descriptor = -1
            handle.write(checkpoint_buffers[0])
            handle.flush()
            os.fsync(handle.fileno())
        report_descriptor, report_temporary = tempfile.mkstemp(
            prefix=".controller-reaudit-report.",
            suffix=".md",
            dir=str(capture_directory),
        )
        os.fchmod(report_descriptor, 0o600)
        with os.fdopen(report_descriptor, "wb") as handle:
            report_descriptor = -1
            handle.write(report_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        checkpoint_path = Path(checkpoint_temporary)
        report_path = Path(report_temporary)
        argv = (
            sys.executable,
            "-I",
            str(REPORTCTL_SCRIPT),
            "audit",
            "--file",
            str(report_path),
            "--checkpoint",
            str(checkpoint_path),
            "--strict",
            "--json",
        )
        audited = subprocess.run(
            list(argv),
            cwd=REPO_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            timeout=15,
            check=False,
            env={
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "PYTHONIOENCODING": "utf-8",
            },
        )
        _verify_checkpoint_artifact_mirror(
            workspace,
            capture_profile,
            required_paths=local_image_targets,
        )
        checkpoint_relative = checkpoint_path.relative_to(
            workspace
        ).as_posix()
        report_relative = report_path.relative_to(workspace).as_posix()
        _, reaudit_checkpoint_bytes, _ = _read_workspace_artifact(
            workspace,
            checkpoint_relative,
            maximum=MAX_CHECKPOINT_BYTES,
            label="controller re-audit checkpoint",
        )
        _, reaudit_report_bytes, _ = _read_workspace_artifact(
            workspace,
            report_relative,
            maximum=MAX_CHECKPOINT_REPORT_BYTES,
            label="controller re-audit report",
        )
    except (OSError, ValueError, StudyError, subprocess.SubprocessError):
        return None
    finally:
        if checkpoint_descriptor >= 0:
            os.close(checkpoint_descriptor)
        if report_descriptor >= 0:
            os.close(report_descriptor)
        for temporary in (checkpoint_temporary, report_temporary):
            if temporary:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass
    if (
        audited.returncode != 0
        or len(audited.stdout) > MAX_AUDITOR_OUTPUT_BYTES
        or len(audited.stderr) > MAX_AUDITOR_OUTPUT_BYTES
        or reaudit_checkpoint_bytes != checkpoint_buffers[0]
        or reaudit_report_bytes != report_bytes
    ):
        return None
    try:
        audit_result = json.loads(audited.stdout.decode("utf-8"))
        checkpoint = json.loads(checkpoint_buffers[0].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return None
    if _json_structure_limit_error(audit_result) or _json_structure_limit_error(checkpoint):
        return None
    checkpoint_audit = audit_result.get("checkpoint") if isinstance(audit_result, dict) else None
    if (
        not isinstance(checkpoint, dict)
        or checkpoint.get("schema_version") != 2
        or checkpoint.get("kind") != "agentic-report-checkpoint"
        or not isinstance(checkpoint.get("intent_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", checkpoint["intent_sha256"]) is None
        or not isinstance(audit_result, dict)
        or audit_result.get("schema_version") != 1
        or audit_result.get("errors") != 0
        or audit_result.get("warnings") != 0
        or not isinstance(checkpoint_audit, dict)
        or checkpoint_audit.get("schema_version") != 2
        or checkpoint_audit.get("must_show_missing") != 0
        or isinstance(checkpoint_audit.get("must_show_checked"), bool)
        or not isinstance(checkpoint_audit.get("must_show_checked"), int)
        or checkpoint_audit["must_show_checked"] < 0
    ):
        return None
    intent_fields = ("task", "mode", "surface", "audience", "modules", "must_show")
    if any(field not in checkpoint for field in intent_fields) or not isinstance(
        checkpoint["must_show"], list
    ):
        return None
    try:
        canonical_intent = json.dumps(
            {field: checkpoint[field] for field in intent_fields},
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError):
        return None
    audit_inputs = audit_result.get("input_receipts")
    audit_report_input = (
        audit_inputs.get("report") if isinstance(audit_inputs, dict) else None
    )
    audit_checkpoint_input = (
        audit_inputs.get("checkpoint") if isinstance(audit_inputs, dict) else None
    )
    if (
        hashlib.sha256(canonical_intent).hexdigest() != checkpoint["intent_sha256"]
        or checkpoint_audit["must_show_checked"] != len(checkpoint["must_show"])
        or not isinstance(audit_report_input, dict)
        or audit_report_input.get("bytes") != len(report_bytes)
        or audit_report_input.get("sha256")
        != hashlib.sha256(report_bytes).hexdigest()
        or not isinstance(audit_checkpoint_input, dict)
        or audit_checkpoint_input.get("intent_sha256")
        != checkpoint["intent_sha256"]
    ):
        return None

    artifact_root = execution_root / "checkpoint-artifacts"
    events_root = artifact_root / "events"
    if artifact_root.exists() or artifact_root.is_symlink():
        return None
    artifact_root.mkdir(mode=0o700)
    events_root.mkdir(mode=0o700)
    event_receipts: list[dict[str, Any]] = []
    for item in captures:
        prefix = f"{item['event_ordinal']:06d}-{item['phase']}"
        checkpoint_stored = f"checkpoint-artifacts/events/{prefix}-checkpoint.json"
        _write_bytes_atomic(
            execution_root / checkpoint_stored,
            item["checkpoint_bytes"],
            mode=0o600,
        )
        event_receipt: dict[str, Any] = {
            "phase": item["phase"],
            "transcript_event_ordinal": item["event_ordinal"],
            "checkpoint": {
                "stored_path": checkpoint_stored,
                "bytes": len(item["checkpoint_bytes"]),
                "sha256": hashlib.sha256(item["checkpoint_bytes"]).hexdigest(),
            },
        }
        if item["phase"] == "audit":
            report_stored = f"checkpoint-artifacts/events/{prefix}-report.md"
            _write_bytes_atomic(
                execution_root / report_stored,
                item["report_bytes"],
                mode=0o600,
            )
            event_receipt["report"] = {
                "stored_path": report_stored,
                "bytes": len(item["report_bytes"]),
                "sha256": hashlib.sha256(item["report_bytes"]).hexdigest(),
            }
        event_receipts.append(event_receipt)

    checkpoint_digest = hashlib.sha256(checkpoint_buffers[0]).hexdigest()
    response_digest = hashlib.sha256(response_bytes).hexdigest()
    _write_bytes_atomic(
        artifact_root / "checkpoint.json", checkpoint_buffers[0], mode=0o600
    )
    _write_bytes_atomic(
        artifact_root / "audited-report.md", report_bytes, mode=0o600
    )
    receipt = {
        "$schema": "checkpoint-artifact-receipt.schema.json",
        "schema_version": "1.0",
        "kind": "checkpoint-artifact-receipt",
        "assurance": "controller-event-snapshot-final-audit",
        "study_id": plan["study_id"],
        "unit_id": unit["unit_id"],
        "condition": "framework",
        "host_plan_sha256": host_plan_sha256,
        "host_adapter_source_sha256": host_plan["host_adapter_source_sha256"],
        "transcript_sha256": transcript_sha256,
        "capture_profile": host_plan["checkpoint_capture_profile"]["capture_protocol"],
        "checkpoint": {
            "workspace_relative_path": checkpoint_paths[0],
            "stored_path": "checkpoint-artifacts/checkpoint.json",
            "bytes": len(checkpoint_buffers[0]),
            "sha256": checkpoint_digest,
            "schema_version": 2,
            "intent_sha256": checkpoint["intent_sha256"],
        },
        "report": {
            "workspace_relative_path": captures[-1]["report_path"],
            "stored_path": "checkpoint-artifacts/audited-report.md",
            "bytes": len(report_bytes),
            "sha256": response_digest,
            "delivered_response_sha256": response_digest,
        },
        "events": event_receipts,
        "controller_reaudit": {
            "auditor_path": REPORTCTL_SCRIPT.relative_to(REPO_ROOT).as_posix(),
            "auditor_profile": host_plan["checkpoint_auditor_receipt"]["profile"],
            "auditor_sha256": host_plan["checkpoint_auditor_sha256"],
            "argv_profile": "python-isolated-audit-captured-byte-pair-strict-json",
            "shell": False,
            "exit_code": 0,
            "schema_version": 1,
            "errors": 0,
            "warnings": 0,
            "report_bytes": len(report_bytes),
            "report_sha256": response_digest,
            "checkpoint_intent_sha256": checkpoint["intent_sha256"],
            "must_show_checked": checkpoint_audit["must_show_checked"],
            "must_show_missing": 0,
        },
    }
    receipt_path = artifact_root / "checkpoint-artifact-receipt.json"
    _write_json_atomic(receipt_path, receipt, mode=0o600)
    return receipt


def _terminate_process_group(process: subprocess.Popen[Any]) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except (OSError, ProcessLookupError):
        pass


def _run_bounded_host(
    *,
    argv: tuple[str, ...],
    prompt: bytes,
    transcript_path: Path,
    stderr_path: Path,
    response_path: Path,
    timeout_seconds: int,
    event_callback: Callable[[str, int], None] | None = None,
) -> tuple[int, int]:
    started = time.monotonic()
    returncode = -1
    try:
        with tempfile.TemporaryFile(mode="w+b") as prompt_handle:
            with transcript_path.open("xb", buffering=0) as stdout_handle, stderr_path.open(
                "xb", buffering=0
            ) as stderr_handle:
                prompt_handle.write(prompt)
                prompt_handle.seek(0)
                os.chmod(transcript_path, 0o600)
                os.chmod(stderr_path, 0o600)
                process = subprocess.Popen(
                    list(argv),
                    stdin=prompt_handle,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    shell=False,
                    start_new_session=(os.name == "posix"),
                )
                try:
                    failure: str | None = None
                    pending = bytearray()
                    transcript_offset = 0
                    event_ordinal = 0

                    def consume_events(reader: Any, *, final: bool) -> None:
                        nonlocal transcript_offset, event_ordinal
                        reader.seek(transcript_offset)
                        chunk = reader.read()
                        transcript_offset += len(chunk)
                        if transcript_offset > MAX_TRANSCRIPT_BYTES:
                            raise StudyError("Host transcript exceeded its byte limit")
                        pending.extend(chunk)
                        while b"\n" in pending:
                            raw, _, remainder = pending.partition(b"\n")
                            pending.clear()
                            pending.extend(remainder)
                            event_ordinal += 1
                            if event_callback is not None and raw.strip():
                                try:
                                    event_callback(raw.decode("utf-8"), event_ordinal)
                                except UnicodeDecodeError as exc:
                                    raise StudyError(
                                        "Host transcript event must be UTF-8"
                                    ) from exc
                        if final and pending:
                            event_ordinal += 1
                            if event_callback is not None and pending.strip():
                                try:
                                    event_callback(pending.decode("utf-8"), event_ordinal)
                                except UnicodeDecodeError as exc:
                                    raise StudyError(
                                        "Host transcript event must be UTF-8"
                                    ) from exc
                            pending.clear()

                    with transcript_path.open("rb", buffering=0) as transcript_reader:
                        while process.poll() is None:
                            elapsed = time.monotonic() - started
                            transcript_size = transcript_path.stat().st_size
                            stderr_size = stderr_path.stat().st_size
                            response_size = (
                                response_path.stat().st_size
                                if response_path.exists()
                                else 0
                            )
                            if transcript_size < transcript_offset:
                                failure = "Host transcript changed size while executing"
                            elif elapsed > timeout_seconds:
                                failure = f"Host execution exceeded {timeout_seconds} seconds"
                            elif transcript_size > MAX_TRANSCRIPT_BYTES:
                                failure = "Host transcript exceeded its byte limit"
                            elif stderr_size > MAX_HOST_STDERR_BYTES:
                                failure = "Host stderr exceeded its byte limit"
                            elif response_size > MAX_RESPONSE_BYTES:
                                failure = "Host response exceeded its byte limit"
                            if failure:
                                _terminate_process_group(process)
                                process.wait(timeout=10)
                                raise StudyError(failure)
                            consume_events(transcript_reader, final=False)
                            time.sleep(0.05)
                        consume_events(transcript_reader, final=True)
                    returncode = int(process.returncode or 0)
                except Exception:
                    if process.poll() is None:
                        _terminate_process_group(process)
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            pass
                    raise
    except StudyError:
        raise
    except (OSError, subprocess.SubprocessError) as exc:
        raise StudyError(f"Cannot execute bounded host process: {exc}") from exc
    if transcript_path.stat().st_size > MAX_TRANSCRIPT_BYTES:
        raise StudyError("Host transcript exceeded its byte limit")
    if stderr_path.stat().st_size > MAX_HOST_STDERR_BYTES:
        raise StudyError("Host stderr exceeded its byte limit")
    if response_path.exists() and response_path.stat().st_size > MAX_RESPONSE_BYTES:
        raise StudyError("Host response exceeded its byte limit")
    latency_ms = int(round((time.monotonic() - started) * 1000))
    return returncode, latency_ms


def command_host_run(args: argparse.Namespace) -> int:
    if not args.execute:
        raise StudyError("host-run is inert without the explicit --execute flag")
    run_dir = Path(args.run_dir)
    plan, _, expected = _load_run(run_dir)
    expected_by_id = {item["unit_id"]: item for item in expected["records"]}
    if args.unit_id not in expected_by_id:
        raise StudyError("host-run unit_id is not in the expected matrix")
    unit = expected_by_id[args.unit_id]
    host_plan = _load_host_plan(run_dir, args.unit_id)
    model = next(item for item in plan["models"] if item["id"] == unit["model_id"])
    expected_identity = {
        "study_id": plan["study_id"],
        "unit_id": unit["unit_id"],
        "condition": unit["condition"],
        "host": model["host"],
        "host_version": model["host_version"],
        "model": model["model"],
        "model_revision": model["revision"],
        "executable_sha256": model["executable_sha256"],
        "prompt_sha256": unit["prompt_sha256"],
    }
    for field, value in expected_identity.items():
        if host_plan.get(field) != value:
            raise StudyError(f"Frozen host plan {field} no longer matches the study")
    if host_plan["schema_version"] == "1.1":
        context = next(
            item for item in plan["contexts"] if item["id"] == unit["context_id"]
        )
        profile = host_plan["checkpoint_capture_profile"]
        if profile["enabled"] is not (unit["condition"] == "framework") or profile[
            "required"
        ] is not (
            unit["condition"] == "framework" and context["compaction_required"]
        ):
            raise StudyError("Frozen checkpoint capture profile no longer matches the study")
        expected_contract = (
            CHECKPOINT_AGENT_CONTRACT if unit["condition"] == "framework" else None
        )
        expected_contract_digest = (
            hashlib.sha256(expected_contract.encode("utf-8")).hexdigest()
            if expected_contract is not None
            else None
        )
        if (
            profile["agent_contract"] != expected_contract
            or profile["agent_contract_sha256"] != expected_contract_digest
        ):
            raise StudyError("Frozen checkpoint capture contract changed after host-plan")
        expected_artifact_mirror = (
            _input_artifacts_for_case(run_dir, unit["case_id"])
            if unit["condition"] == "framework"
            else []
        )
        if profile["artifact_mirror"] != expected_artifact_mirror:
            raise StudyError("Frozen checkpoint artifact mirror changed after host-plan")
    executable = _resolve_executable(Path(host_plan["executable"]))
    if _sha256(executable) != host_plan["executable_sha256"]:
        raise StudyError("Host executable changed after host-plan")
    adapter_source_digest = _host_adapter_source_sha256()
    if adapter_source_digest != host_plan["host_adapter_source_sha256"]:
        raise StudyError("Host adapter source changed after host-plan")
    if (
        host_plan["schema_version"] == "1.1"
        and _checkpoint_auditor_sha256()
        != host_plan["checkpoint_auditor_sha256"]
    ):
        raise StudyError("Checkpoint auditor changed after host-plan")
    workspace = _resolve_workspace(Path(host_plan["workspace"]))
    if _workspace_receipt(workspace, unit["condition"]) != host_plan["workspace_receipt"]:
        raise StudyError("Host workspace activation receipt changed after host-plan")
    prompt_path = run_dir / unit["prompt"]
    prompt = _read_bounded_bytes(prompt_path, maximum=MAX_RESPONSE_BYTES, label="frozen prompt")
    if _sha256(prompt_path) != unit["prompt_sha256"]:
        raise StudyError("Frozen host prompt changed")
    agent_contract = (
        host_plan["checkpoint_capture_profile"]["agent_contract"]
        if host_plan["schema_version"] == "1.1"
        else None
    )
    host_prompt = _compose_host_prompt(prompt, agent_contract)
    if (
        host_plan["schema_version"] == "1.1"
        and hashlib.sha256(host_prompt).hexdigest()
        != host_plan["host_prompt_sha256"]
    ):
        raise StudyError("Frozen delivered host prompt changed after host-plan")

    execution_root = run_dir / "private" / "host-executions" / unit["unit_id"]
    _reject_symlink_chain(execution_root, "host execution directory")
    if execution_root.exists() or execution_root.is_symlink():
        raise StudyError(f"Host execution already exists: {unit['unit_id']}")
    response_path = execution_root / "response.md"
    transcript_path = execution_root / "transcript.jsonl"
    stderr_path = execution_root / "stderr.log"
    host_module = _load_host_module()
    try:
        adapter = host_module.get_adapter(model["host"])
        command = adapter.build_command(
            executable=executable,
            workspace=workspace,
            response_path=response_path,
            model=model["model"],
            max_output_tokens=plan["generation"]["max_output_tokens"],
        )
    except Exception as exc:
        raise StudyError(str(exc)) from exc
    if _host_adapter_source_sha256() != adapter_source_digest:
        raise StudyError("Host adapter source changed while rebuilding frozen argv")
    if list(command.argv) != host_plan["planned_argv"]:
        raise StudyError("Host adapter argv changed after host-plan")
    if command.transcript_format != host_plan["planned_transcript_format"]:
        raise StudyError("Host adapter transcript format changed after host-plan")
    if (
        host_plan["command_profile"].get("output_token_cap_enforced")
        is not command.output_token_cap_enforced
    ):
        raise StudyError("Host adapter output-token capability changed after host-plan")
    staged = _stage_case_inputs(run_dir, workspace, unit["case_id"])
    if host_plan["schema_version"] == "1.1":
        _prepare_checkpoint_capture_workspace(
            workspace, host_plan["checkpoint_capture_profile"]
        )
    execution_root.parent.mkdir(mode=0o700, exist_ok=True)
    execution_root.mkdir(mode=0o700)
    capture_state: dict[str, Any] = {"invalid": False, "events": []}
    event_callback: Callable[[str, int], None] | None = None
    if (
        host_plan["schema_version"] == "1.1"
        and host_plan["checkpoint_capture_profile"]["enabled"]
    ):
        def capture_checkpoint_event(line: str, event_ordinal: int) -> None:
            try:
                event = adapter.parse_checkpoint_event(line, event_ordinal)
            except Exception:
                capture_state["invalid"] = True
                return
            if event is None:
                return
            capture_profile = host_plan["checkpoint_capture_profile"]
            if (
                event.checkpoint_path != capture_profile["checkpoint_path"]
                or (
                    event.phase == "audit"
                    and event.report_path != capture_profile["report_path"]
                )
                or (event.phase != "audit" and event.report_path is not None)
            ):
                capture_state["invalid"] = True
                return
            if len(capture_state["events"]) >= MAX_CHECKPOINT_CAPTURE_EVENTS:
                capture_state["invalid"] = True
                return
            try:
                checkpoint_relative, checkpoint_bytes, _ = _read_workspace_artifact(
                    workspace,
                    event.checkpoint_path,
                    maximum=MAX_CHECKPOINT_BYTES,
                    label="checkpoint event artifact",
                )
                captured: dict[str, Any] = {
                    "phase": event.phase,
                    "event_ordinal": event.event_ordinal,
                    "checkpoint_path": checkpoint_relative.as_posix(),
                    "report_path": event.report_path,
                    "checkpoint_bytes": checkpoint_bytes,
                }
                if event.phase == "audit":
                    if event.report_path is None:
                        raise StudyError("Checkpoint audit event lacks a report path")
                    report_relative, report_bytes, _ = _read_workspace_artifact(
                        workspace,
                        event.report_path,
                        maximum=MAX_CHECKPOINT_REPORT_BYTES,
                        label="checkpoint audit report",
                    )
                    captured.update(
                        {
                            "report_path": report_relative.as_posix(),
                            "report_bytes": report_bytes,
                        }
                    )
                capture_state["events"].append(captured)
            except StudyError:
                capture_state["invalid"] = True

        event_callback = capture_checkpoint_event
    execution_schema_version = host_plan["schema_version"]
    execution_receipt: dict[str, Any] = {
        "schema_version": execution_schema_version,
        "study_id": plan["study_id"],
        "unit_id": unit["unit_id"],
        "host_plan_sha256": _sha256(_host_plan_path(run_dir, unit["unit_id"])),
        "host_adapter_source_sha256": host_plan["host_adapter_source_sha256"],
        "argv": list(command.argv),
        "shell": False,
        "output_token_cap_enforced": command.output_token_cap_enforced,
        "transcript_format": command.transcript_format,
        "staged_artifacts": staged,
        "status": "started",
    }
    if execution_schema_version == "1.1":
        execution_receipt.update(
            {
                "condition": unit["condition"],
                "checkpoint_auditor_sha256": host_plan[
                    "checkpoint_auditor_sha256"
                ],
                "checkpoint_receipt": None,
                "host_prompt_sha256": host_plan["host_prompt_sha256"],
            }
        )
    _write_json_atomic(execution_root / "execution-receipt.json", execution_receipt)
    try:
        returncode, latency_ms = _run_bounded_host(
            argv=command.argv,
            prompt=host_prompt,
            transcript_path=transcript_path,
            stderr_path=stderr_path,
            response_path=response_path,
            timeout_seconds=plan["generation"]["timeout_seconds"],
            event_callback=event_callback,
        )
        execution_outcome = {
            "status": "completed" if returncode == 0 else "host_error",
            "returncode": returncode,
            "latency_ms": latency_ms,
            "transcript_sha256": _sha256(transcript_path),
            "stderr_sha256": _sha256(stderr_path),
            "response_sha256": _sha256(response_path) if response_path.is_file() else None,
        }
        if returncode != 0:
            execution_receipt.update(execution_outcome)
            _write_json_atomic(
                execution_root / "execution-receipt.json", execution_receipt
            )
            raise StudyError(f"Host exited with status {returncode}; private stderr was preserved")
        response_bytes = _read_bounded_bytes(response_path, maximum=MAX_RESPONSE_BYTES, label="host response")
        try:
            response_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise StudyError("Host response must be UTF-8 Markdown") from exc
        transcript_bytes = _read_bounded_bytes(
            transcript_path,
            maximum=MAX_TRANSCRIPT_BYTES,
            label="host transcript",
        )
        try:
            telemetry = adapter.parse_transcript(transcript_bytes.decode("utf-8").splitlines())
        except Exception as exc:
            raise StudyError(f"Cannot parse host transcript: {exc}") from exc
        if _workspace_receipt(workspace, unit["condition"]) != host_plan["workspace_receipt"]:
            raise StudyError("Host workspace activation receipt changed during execution")
        if (
            host_plan["schema_version"] == "1.1"
            and host_plan["checkpoint_capture_profile"]["enabled"]
        ):
            _, ignore_bytes, _ = _read_workspace_artifact(
                workspace,
                host_plan["checkpoint_capture_profile"]["ignore_path"],
                maximum=16,
                label="checkpoint capture ignore marker",
            )
            if ignore_bytes != CHECKPOINT_CAPTURE_IGNORE_BYTES:
                raise StudyError("Checkpoint capture Git ignore marker changed")
        for artifact in staged:
            relative, digest, _ = _artifact_record(
                {field: artifact[field] for field in ("path", "sha256", "media_type")},
                label="staged host artifact",
            )
            path = workspace.joinpath(*relative.parts)
            if not path.is_file() or path.is_symlink() or _sha256(path) != digest:
                raise StudyError(f"Host changed a staged input artifact: {relative.as_posix()}")
        if (
            host_plan["schema_version"] == "1.1"
            and host_plan["checkpoint_capture_profile"]["enabled"]
        ):
            profile = host_plan["checkpoint_capture_profile"]
            _verify_checkpoint_artifact_mirror(workspace, profile)
        checkpoint_receipt = _finalize_checkpoint_artifact_receipt(
            plan=plan,
            unit=unit,
            host_plan=host_plan,
            host_plan_sha256=execution_receipt["host_plan_sha256"],
            execution_root=execution_root,
            response_bytes=response_bytes,
            transcript_sha256=execution_outcome["transcript_sha256"],
            telemetry=telemetry,
            capture_state=capture_state,
        )
        if execution_schema_version == "1.1":
            execution_outcome["checkpoint_receipt"] = checkpoint_receipt
        execution_receipt.update(execution_outcome)
        _write_json_atomic(execution_root / "execution-receipt.json", execution_receipt)
        record = {
            "$schema": "generation-record.schema.json",
            "schema_version": "1.0",
            "study_id": plan["study_id"],
            "unit_id": unit["unit_id"],
            "case_id": unit["case_id"],
            "model_id": unit["model_id"],
            "context_id": unit["context_id"],
            "seed": unit["seed"],
            "condition": unit["condition"],
            "host": model["host"],
            "host_version": model["host_version"],
            "model": model["model"],
            "model_revision": model["revision"],
            "prompt_sha256": unit["prompt_sha256"],
            "response_sha256": _sha256(response_path),
            "transcript_sha256": _sha256(transcript_path),
            "artifacts": [
                {field: artifact[field] for field in ("path", "sha256", "media_type")}
                for artifact in staged
            ],
            "usage": {
                "input_tokens": telemetry.input_tokens,
                "cached_input_tokens": telemetry.cached_input_tokens,
                "output_tokens": telemetry.output_tokens,
                "latency_ms": latency_ms,
                "context_occupancy_percent": None,
                "compaction_observed": None,
            },
            "observations": {
                "telemetry_source": "host_adapter",
                "host_activation_observed": telemetry.skill_read if unit["condition"] == "framework" else False,
                "skill_read": telemetry.skill_read,
                "checkpoint_created": telemetry.checkpoint_created,
                "checkpoint_reloaded": telemetry.checkpoint_reloaded,
                "checkpoint_audit_passed": telemetry.checkpoint_audit_passed,
                "final_audit_passed": telemetry.final_audit_passed,
                "checkpoint_receipt_verified": checkpoint_receipt is not None,
                "output_token_cap_enforced": command.output_token_cap_enforced,
            },
        }
        record_path = execution_root / "generation-record.json"
        _write_json_atomic(record_path, record)
        command_import_output(
            argparse.Namespace(
                run_dir=str(run_dir),
                record=str(record_path),
                response=str(response_path),
                transcript=str(transcript_path),
                artifact_root=str(workspace),
                host_binding={
                    "host_plan_sha256": _sha256(
                        _host_plan_path(run_dir, unit["unit_id"])
                    ),
                    "execution_receipt_sha256": _sha256(
                        execution_root / "execution-receipt.json"
                    ),
                },
            )
        )
    except Exception:
        if execution_receipt.get("status") == "started":
            execution_receipt["status"] = "failed"
            _write_json_atomic(execution_root / "execution-receipt.json", execution_receipt)
        raise
    _safe_print(f"Executed and imported host unit: {unit['unit_id']}")
    return 0


def _validate_record_lock(directory: Path, record: dict[str, Any]) -> None:
    lock = _read_json(directory / "record-lock.json", label="generation record lock")
    _require_object_shape(
        lock,
        "generation record lock",
        required=(
            "schema_version", "study_id", "unit_id", "stored_record_sha256",
            "response_sha256", "transcript_sha256", "host_execution_binding_sha256",
        ),
    )
    if (
        lock["schema_version"] != "1.0"
        or lock["study_id"] != record.get("study_id")
        or lock["unit_id"] != record.get("unit_id")
    ):
        raise StudyError("Generation record lock identity does not match")
    for field in ("stored_record_sha256", "response_sha256"):
        if not isinstance(lock[field], str) or not re.fullmatch(r"[0-9a-f]{64}", lock[field]):
            raise StudyError(f"Generation record lock {field} is invalid")
    for field in ("transcript_sha256", "host_execution_binding_sha256"):
        value = lock[field]
        if value is not None and (
            not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
        ):
            raise StudyError(f"Generation record lock {field} is invalid")
    record_path = directory / "record.json"
    response_path = directory / "response.md"
    if record_path.is_symlink() or response_path.is_symlink():
        raise StudyError("Stored generation record and response must not be symlinks")
    if lock["stored_record_sha256"] != _sha256(record_path):
        raise StudyError("Stored generation record changed after import")
    if lock["response_sha256"] != _sha256(response_path):
        raise StudyError("Stored response changed after import")
    transcript_path = directory / "transcript.jsonl"
    if transcript_path.is_symlink():
        raise StudyError("Stored transcript must not be a symlink")
    observed_transcript = _sha256(transcript_path) if transcript_path.is_file() else None
    if lock["transcript_sha256"] != observed_transcript:
        raise StudyError("Stored transcript changed after import")
    binding_path = directory / "host-execution-binding.json"
    if binding_path.is_symlink():
        raise StudyError("Stored host execution binding must not be a symlink")
    observed_binding = _sha256(binding_path) if binding_path.is_file() else None
    if lock["host_execution_binding_sha256"] != observed_binding:
        raise StudyError("Stored host execution binding changed after import")


def _validate_private_checkpoint_file(
    execution_root: Path,
    stored_path: str,
    *,
    maximum: int,
    expected_bytes: int,
    expected_sha256: str,
    label: str,
) -> bytes:
    if os.name != "posix" or not hasattr(os, "geteuid"):
        raise StudyError("Checkpoint artifact validation requires POSIX ownership metadata")
    relative = _portable_workspace_relative_path(stored_path, label)
    if not relative.parts or relative.parts[0] != "checkpoint-artifacts":
        raise StudyError(f"{label} must remain inside checkpoint-artifacts")
    path = execution_root.joinpath(*relative.parts)
    data = _read_bounded_bytes(path, maximum=maximum, label=label)
    metadata = path.stat()
    if (
        metadata.st_nlink != 1
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) & 0o077
    ):
        raise StudyError(f"{label} has unsafe ownership, links, or permissions")
    if (
        isinstance(expected_bytes, bool)
        or not isinstance(expected_bytes, int)
        or expected_bytes < 0
        or expected_bytes > maximum
        or len(data) != expected_bytes
        or not isinstance(expected_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
        or hashlib.sha256(data).hexdigest() != expected_sha256
    ):
        raise StudyError(f"{label} does not match its receipt")
    return data


def _validate_checkpoint_artifact_receipt(
    *,
    execution_root: Path,
    record: dict[str, Any],
    host_plan: dict[str, Any],
    execution: dict[str, Any],
) -> None:
    if os.name != "posix" or not hasattr(os, "geteuid"):
        raise StudyError("Checkpoint artifact receipts require POSIX validation")
    receipt = execution.get("checkpoint_receipt")
    verified = record["observations"]["checkpoint_receipt_verified"]
    if verified is not True:
        if receipt is not None:
            raise StudyError("Unverified execution may not retain a checkpoint receipt claim")
        return
    if not isinstance(receipt, dict):
        raise StudyError("Verified checkpoint execution lacks its artifact receipt")
    _require_object_shape(
        receipt,
        "checkpoint artifact receipt",
        required=(
            "$schema", "schema_version", "kind", "assurance", "study_id",
            "unit_id", "condition", "host_plan_sha256",
            "host_adapter_source_sha256", "transcript_sha256", "capture_profile",
            "checkpoint", "report", "events", "controller_reaudit",
        ),
    )
    if (
        receipt["$schema"] != "checkpoint-artifact-receipt.schema.json"
        or receipt["schema_version"] != "1.0"
        or receipt["kind"] != "checkpoint-artifact-receipt"
        or receipt["assurance"] != "controller-event-snapshot-final-audit"
        or receipt["study_id"] != record["study_id"]
        or receipt["unit_id"] != record["unit_id"]
        or receipt["condition"] != "framework"
        or record["condition"] != "framework"
        or receipt["host_plan_sha256"] != execution["host_plan_sha256"]
        or receipt["host_adapter_source_sha256"]
        != execution["host_adapter_source_sha256"]
        or receipt["transcript_sha256"] != record["transcript_sha256"]
        or receipt["capture_profile"]
        != host_plan["checkpoint_capture_profile"]["capture_protocol"]
    ):
        raise StudyError("Checkpoint artifact receipt identity is invalid")
    receipt_path = execution_root / "checkpoint-artifacts" / "checkpoint-artifact-receipt.json"
    archived_receipt = _read_json(receipt_path, label="checkpoint artifact receipt archive")
    if archived_receipt != receipt:
        raise StudyError("Archived checkpoint receipt differs from the execution receipt")
    receipt_metadata = receipt_path.stat()
    if (
        receipt_metadata.st_nlink != 1
        or receipt_metadata.st_uid != os.geteuid()
        or stat.S_IMODE(receipt_metadata.st_mode) & 0o077
    ):
        raise StudyError("Archived checkpoint receipt permissions are unsafe")

    checkpoint_record = receipt["checkpoint"]
    report_record = receipt["report"]
    if not isinstance(checkpoint_record, dict) or not isinstance(report_record, dict):
        raise StudyError("Checkpoint receipt artifact records must be objects")
    _require_object_shape(
        checkpoint_record,
        "checkpoint receipt checkpoint",
        required=(
            "workspace_relative_path", "stored_path", "bytes", "sha256",
            "schema_version", "intent_sha256",
        ),
    )
    _require_object_shape(
        report_record,
        "checkpoint receipt report",
        required=(
            "workspace_relative_path", "stored_path", "bytes", "sha256",
            "delivered_response_sha256",
        ),
    )
    _portable_workspace_relative_path(
        checkpoint_record["workspace_relative_path"], "checkpoint workspace path"
    )
    _portable_workspace_relative_path(
        report_record["workspace_relative_path"], "checkpoint report workspace path"
    )
    if (
        checkpoint_record["workspace_relative_path"]
        != host_plan["checkpoint_capture_profile"]["checkpoint_path"]
        or report_record["workspace_relative_path"]
        != host_plan["checkpoint_capture_profile"]["report_path"]
        or checkpoint_record["stored_path"] != "checkpoint-artifacts/checkpoint.json"
        or report_record["stored_path"] != "checkpoint-artifacts/audited-report.md"
        or checkpoint_record["schema_version"] != 2
        or not isinstance(checkpoint_record["intent_sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", checkpoint_record["intent_sha256"]) is None
        or report_record["sha256"] != record["response_sha256"]
        or report_record["delivered_response_sha256"] != record["response_sha256"]
    ):
        raise StudyError("Checkpoint receipt artifact binding is invalid")
    checkpoint_bytes = _validate_private_checkpoint_file(
        execution_root,
        checkpoint_record["stored_path"],
        maximum=MAX_CHECKPOINT_BYTES,
        expected_bytes=checkpoint_record["bytes"],
        expected_sha256=checkpoint_record["sha256"],
        label="archived checkpoint",
    )
    report_bytes = _validate_private_checkpoint_file(
        execution_root,
        report_record["stored_path"],
        maximum=MAX_CHECKPOINT_REPORT_BYTES,
        expected_bytes=report_record["bytes"],
        expected_sha256=report_record["sha256"],
        label="archived audited report",
    )
    if hashlib.sha256(report_bytes).hexdigest() != execution["response_sha256"]:
        raise StudyError("Archived audited report differs from the delivered response")
    local_image_targets = _checkpoint_local_artifact_targets(report_bytes)
    mirrored_artifact_paths = {
        artifact["path"]
        for artifact in host_plan["checkpoint_capture_profile"]["artifact_mirror"]
    }
    if not local_image_targets.issubset(mirrored_artifact_paths):
        raise StudyError("Archived report references an unmirrored local image")
    try:
        checkpoint = json.loads(checkpoint_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise StudyError("Archived checkpoint is not bounded UTF-8 JSON") from exc
    intent_fields = ("task", "mode", "surface", "audience", "modules", "must_show")
    if (
        not isinstance(checkpoint, dict)
        or _json_structure_limit_error(checkpoint)
        or checkpoint.get("schema_version") != 2
        or checkpoint.get("kind") != "agentic-report-checkpoint"
        or any(field not in checkpoint for field in intent_fields)
    ):
        raise StudyError("Archived checkpoint schema is invalid")
    intent = {field: checkpoint[field] for field in intent_fields}
    canonical_intent = json.dumps(
        intent, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    observed_intent = hashlib.sha256(canonical_intent).hexdigest()
    if (
        checkpoint.get("intent_sha256") != observed_intent
        or checkpoint_record["intent_sha256"] != observed_intent
    ):
        raise StudyError("Archived checkpoint intent fingerprint is invalid")

    events = receipt["events"]
    if not isinstance(events, list) or len(events) != 3:
        raise StudyError("Checkpoint receipt must contain exactly three event snapshots")
    if [item.get("phase") for item in events if isinstance(item, dict)] != [
        "create", "reload", "audit"
    ]:
        raise StudyError("Checkpoint receipt event order is invalid")
    ordinals: list[int] = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise StudyError("Checkpoint receipt event must be an object")
        phase = ("create", "reload", "audit")[index]
        _require_object_shape(
            event,
            f"checkpoint {phase} event",
            required=("phase", "transcript_event_ordinal", "checkpoint")
            + (("report",) if phase == "audit" else ()),
        )
        ordinal = event["transcript_event_ordinal"]
        if (
            isinstance(ordinal, bool)
            or not isinstance(ordinal, int)
            or ordinal < 1
            or ordinal > 100_000
        ):
            raise StudyError("Checkpoint receipt event ordinal is invalid")
        ordinals.append(ordinal)
        artifact = event["checkpoint"]
        if not isinstance(artifact, dict):
            raise StudyError("Checkpoint event artifact must be an object")
        _require_object_shape(
            artifact,
            "checkpoint event artifact",
            required=("stored_path", "bytes", "sha256"),
        )
        expected_path = (
            f"checkpoint-artifacts/events/{ordinal:06d}-{phase}-checkpoint.json"
        )
        if artifact["stored_path"] != expected_path:
            raise StudyError("Checkpoint event artifact path is invalid")
        event_bytes = _validate_private_checkpoint_file(
            execution_root,
            artifact["stored_path"],
            maximum=MAX_CHECKPOINT_BYTES,
            expected_bytes=artifact["bytes"],
            expected_sha256=artifact["sha256"],
            label=f"{phase} checkpoint snapshot",
        )
        if event_bytes != checkpoint_bytes:
            raise StudyError("Checkpoint bytes changed across event snapshots")
        if phase == "audit":
            event_report = event["report"]
            if not isinstance(event_report, dict):
                raise StudyError("Checkpoint audit report record must be an object")
            _require_object_shape(
                event_report,
                "checkpoint audit event report",
                required=("stored_path", "bytes", "sha256"),
            )
            expected_report_path = (
                f"checkpoint-artifacts/events/{ordinal:06d}-audit-report.md"
            )
            if event_report["stored_path"] != expected_report_path:
                raise StudyError("Checkpoint audit report snapshot path is invalid")
            event_report_bytes = _validate_private_checkpoint_file(
                execution_root,
                event_report["stored_path"],
                maximum=MAX_CHECKPOINT_REPORT_BYTES,
                expected_bytes=event_report["bytes"],
                expected_sha256=event_report["sha256"],
                label="audit report event snapshot",
            )
            if event_report_bytes != report_bytes:
                raise StudyError("Audit report snapshot differs from the archived report")
    if ordinals != sorted(ordinals) or len(set(ordinals)) != 3:
        raise StudyError("Checkpoint receipt event ordinals are not strictly ordered")

    reaudit = receipt["controller_reaudit"]
    if not isinstance(reaudit, dict):
        raise StudyError("Checkpoint controller re-audit record must be an object")
    _require_object_shape(
        reaudit,
        "checkpoint controller re-audit",
        required=(
            "auditor_path", "auditor_profile", "auditor_sha256", "argv_profile", "shell",
            "exit_code", "schema_version", "errors", "warnings", "report_bytes",
            "report_sha256", "checkpoint_intent_sha256",
            "must_show_checked", "must_show_missing",
        ),
    )
    if (
        reaudit["auditor_path"]
        != REPORTCTL_SCRIPT.relative_to(REPO_ROOT).as_posix()
        or reaudit["auditor_profile"] != "reportctl-audit-closure-v1"
        or reaudit["auditor_sha256"] != host_plan["checkpoint_auditor_sha256"]
        or reaudit["argv_profile"]
        != "python-isolated-audit-captured-byte-pair-strict-json"
        or reaudit["shell"] is not False
        or reaudit["exit_code"] != 0
        or reaudit["schema_version"] != 1
        or reaudit["errors"] != 0
        or reaudit["warnings"] != 0
        or reaudit["report_bytes"] != len(report_bytes)
        or reaudit["report_sha256"] != hashlib.sha256(report_bytes).hexdigest()
        or reaudit["checkpoint_intent_sha256"] != observed_intent
        or reaudit["must_show_missing"] != 0
        or reaudit["must_show_checked"] != len(checkpoint["must_show"])
        or isinstance(reaudit["must_show_checked"], bool)
        or not isinstance(reaudit["must_show_checked"], int)
        or reaudit["must_show_checked"] < 0
        or reaudit["must_show_checked"] > 20
    ):
        raise StudyError("Checkpoint controller re-audit record is invalid")


def _validate_host_execution_binding(
    run_dir: Path,
    directory: Path,
    record: dict[str, Any],
) -> None:
    binding = _read_json(
        directory / "host-execution-binding.json",
        label="host execution binding",
    )
    _require_object_shape(
        binding,
        "host execution binding",
        required=(
            "schema_version", "study_id", "unit_id", "host_plan_sha256",
            "execution_receipt_sha256", "stored_record_sha256",
        ),
    )
    if (
        binding["schema_version"] != "1.0"
        or binding["study_id"] != record["study_id"]
        or binding["unit_id"] != record["unit_id"]
    ):
        raise StudyError("Host execution binding identity does not match the record")
    for field in (
        "host_plan_sha256", "execution_receipt_sha256", "stored_record_sha256"
    ):
        if not isinstance(binding[field], str) or not re.fullmatch(
            r"[0-9a-f]{64}", binding[field]
        ):
            raise StudyError(f"Host execution binding {field} is invalid")
    stored_record_path = directory / "record.json"
    if binding["stored_record_sha256"] != _sha256(stored_record_path):
        raise StudyError("Stored generation record changed after host execution binding")

    host_plan_path = _host_plan_path(run_dir, record["unit_id"])
    if binding["host_plan_sha256"] != _sha256(host_plan_path):
        raise StudyError("Host plan does not match the execution binding")
    host_plan = _load_host_plan(run_dir, record["unit_id"])
    for field in ("study_id", "unit_id", "host", "host_version", "model", "model_revision"):
        if host_plan.get(field) != record[field]:
            raise StudyError(f"Host plan {field} does not match the stored record")

    execution_path = (
        run_dir
        / "private"
        / "host-executions"
        / record["unit_id"]
        / "execution-receipt.json"
    )
    if binding["execution_receipt_sha256"] != _sha256(execution_path):
        raise StudyError("Host execution receipt does not match its record binding")
    execution = _read_json(execution_path, label="host execution receipt")
    common_execution_fields = {
        "schema_version", "study_id", "unit_id", "host_plan_sha256",
        "host_adapter_source_sha256", "argv",
        "shell", "output_token_cap_enforced", "transcript_format", "staged_artifacts",
        "status", "returncode", "latency_ms", "transcript_sha256", "stderr_sha256",
        "response_sha256",
    }
    execution_version = execution.get("schema_version")
    required_execution_fields = common_execution_fields | (
        {
            "condition", "checkpoint_auditor_sha256", "checkpoint_receipt",
            "host_prompt_sha256",
        }
        if execution_version == "1.1"
        else set()
    )
    if set(execution) != required_execution_fields:
        raise StudyError("Completed host execution receipt has an invalid shape")
    if (
        execution_version not in {"1.0", "1.1"}
        or host_plan["schema_version"] != execution_version
        or execution["study_id"] != record["study_id"]
        or execution["unit_id"] != record["unit_id"]
        or execution["status"] != "completed"
        or execution["returncode"] != 0
        or execution["shell"] is not False
        or execution["host_plan_sha256"] != binding["host_plan_sha256"]
        or execution["host_adapter_source_sha256"]
        != host_plan["host_adapter_source_sha256"]
        or execution["argv"] != host_plan["planned_argv"]
        or execution["transcript_format"] != host_plan["planned_transcript_format"]
        or execution["response_sha256"] != record["response_sha256"]
        or execution["transcript_sha256"] != record["transcript_sha256"]
        or execution["output_token_cap_enforced"]
        is not record["observations"]["output_token_cap_enforced"]
        or host_plan["command_profile"].get("output_token_cap_enforced")
        is not execution["output_token_cap_enforced"]
    ):
        raise StudyError("Completed host execution receipt does not match the stored record")
    if execution_version == "1.0":
        if record["observations"]["checkpoint_receipt_verified"] is True:
            raise StudyError("Legacy execution receipts cannot verify checkpoint artifacts")
    else:
        if (
            execution["condition"] != record["condition"]
            or execution["checkpoint_auditor_sha256"]
            != host_plan["checkpoint_auditor_sha256"]
            or execution["host_prompt_sha256"] != host_plan["host_prompt_sha256"]
        ):
            raise StudyError("Checkpoint execution receipt does not match its host plan")
        _validate_checkpoint_artifact_receipt(
            execution_root=execution_path.parent,
            record=record,
            host_plan=host_plan,
            execution=execution,
        )


def _validate_records(run_dir: Path, expected: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    invalid: list[str] = []
    for item in expected["records"]:
        unit_id = item["unit_id"]
        directory = run_dir / "records" / unit_id
        record_path = directory / "record.json"
        response_path = directory / "response.md"
        if not record_path.is_file() or not response_path.is_file():
            missing.append(unit_id)
            continue
        try:
            record = _read_json(record_path, label="stored generation record")
            _validate_record_lock(directory, record)
            if record.get("unit_id") != unit_id or record.get("response_sha256") != _sha256(response_path):
                invalid.append(unit_id)
            observations = record.get("observations")
            if not isinstance(observations, dict):
                invalid.append(unit_id)
            elif observations.get("telemetry_source") == "host_adapter":
                _validate_host_execution_binding(run_dir, directory, record)
            elif (directory / "host-execution-binding.json").exists() or (
                directory / "host-execution-binding.json"
            ).is_symlink():
                invalid.append(unit_id)
            transcript_digest = record.get("transcript_sha256")
            transcript_path = directory / "transcript.jsonl"
            if transcript_digest is not None and (
                not transcript_path.is_file() or _sha256(transcript_path) != transcript_digest
            ):
                invalid.append(unit_id)
            artifacts = record.get("artifacts")
            if not isinstance(artifacts, list) or len(artifacts) > MAX_ARTIFACTS:
                invalid.append(unit_id)
            else:
                for index, artifact in enumerate(artifacts):
                    relative, digest, _ = _artifact_record(
                        artifact,
                        label=f"stored generation artifact {index}",
                    )
                    path = directory.joinpath(*relative.parts)
                    if not path.is_file() or path.is_symlink() or _sha256(path) != digest:
                        invalid.append(unit_id)
                        break
            for artifact in _input_artifacts_for_case(run_dir, item["case_id"]):
                relative, digest, _ = _artifact_record(artifact, label="stored frozen input artifact")
                path = directory.joinpath(*relative.parts)
                if not path.is_file() or path.is_symlink() or _sha256(path) != digest:
                    invalid.append(unit_id)
                    break
        except StudyError:
            invalid.append(unit_id)
    return {
        "complete": not missing and not invalid,
        "expected_record_count": len(expected["records"]),
        "present_record_count": len(expected["records"]) - len(missing),
        "missing_record_count": len(missing),
        "invalid_record_count": len(set(invalid)),
        "missing_record_ordinals": [
            index + 1
            for index, item in enumerate(expected["records"])
            if item["unit_id"] in set(missing)
        ],
        "invalid_record_ordinals": [
            index + 1
            for index, item in enumerate(expected["records"])
            if item["unit_id"] in set(invalid)
        ],
    }


def command_validate(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    _, _, expected = _load_run(run_dir)
    report = _validate_records(run_dir, expected)
    if args.json:
        _safe_print(_safe_json_dumps(report), preserve_newlines=True)
    else:
        _safe_print(
            f"Records: {report['present_record_count']}/{report['expected_record_count']}; "
            f"missing={report['missing_record_count']}; invalid={report['invalid_record_count']}"
        )
    return 0 if report["complete"] else 1


def command_pilot_summary(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    plan, _, expected = _load_run(run_dir)
    if plan["study_kind"] != "pilot":
        raise StudyError("pilot-summary is only available for a study_kind=pilot run")
    validation = _validate_records(run_dir, expected)
    if not validation["complete"]:
        raise StudyError("Cannot summarize an incomplete pilot generation matrix")
    records = [
        _read_json(
            run_dir / "records" / item["unit_id"] / "record.json",
            label="stored generation record",
        )
        for item in expected["records"]
    ]
    by_condition: dict[str, dict[str, Any]] = {}
    for condition in CONDITIONS:
        selected = [record for record in records if record["condition"] == condition]
        checks_passed = sum(record["machine_evaluation"]["checks_passed"] for record in selected)
        checks_total = sum(record["machine_evaluation"]["checks_total"] for record in selected)
        tokens = [record["usage"]["output_tokens"] for record in selected if record["usage"]["output_tokens"] is not None]
        latencies = [record["usage"]["latency_ms"] for record in selected if record["usage"]["latency_ms"] is not None]
        by_condition[condition] = {
            "record_count": len(selected),
            "machine_check_pass_rate": checks_passed / checks_total if checks_total else None,
            "machine_response_pass_count": sum(
                1 for record in selected if record["machine_evaluation"]["passed"]
            ),
            "median_output_tokens": _percentile([float(value) for value in tokens], 0.5),
            "median_latency_ms": _percentile([float(value) for value in latencies], 0.5),
            "skill_read_count": sum(
                1 for record in selected if record["observations"]["skill_read"] is True
            ),
            "checkpoint_audit_pass_count": sum(
                1
                for record in selected
                if record["observations"]["checkpoint_audit_passed"] is True
            ),
        }
    paired_overheads: list[float] = []
    records_by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    expected_by_unit = {item["unit_id"]: item for item in expected["records"]}
    for record in records:
        pair_key = expected_by_unit[record["unit_id"]]["pair_key"]
        records_by_pair.setdefault(pair_key, {})[record["condition"]] = record
    for pair in records_by_pair.values():
        baseline = pair["baseline"]["usage"]["output_tokens"]
        framework = pair["framework"]["usage"]["output_tokens"]
        if isinstance(baseline, int) and isinstance(framework, int) and baseline > 0:
            paired_overheads.append((framework - baseline) / baseline)
    summary = {
        "$schema": "pilot-summary.schema.json",
        "schema_version": "1.0",
        "study_id": plan["study_id"],
        "study_kind": "pilot",
        "input_receipts": {
            "plan_sha256": _sha256(run_dir / "plan.json"),
            "cases_sha256": _sha256(run_dir / "cases.json"),
            "input_artifacts_sha256": _sha256(run_dir / "input-artifacts.json"),
        },
        "generation": {
            "record_count": len(records),
            "pair_count": len(records_by_pair),
            "conditions": by_condition,
            "paired_output_token_overhead_median": _percentile(paired_overheads, 0.5),
        },
        "claim": {
            "status": "insufficient_evidence",
            "effectiveness_claim_eligible": False,
            "reason": (
                "A pilot generation summary has no frozen independent blind ratings, "
                "private held-out design, or preregistered full-study evidence."
            ),
        },
        "limitations": [
            "Machine checks assess declared structural invariants, not truth or human readability.",
            "Host traces are conservative observations and do not prove complete instruction isolation.",
            "A planned output-token value is not evidence of a provider-enforced cap.",
            "A model revision label is not evidence of immutable provider behavior without an external receipt.",
        ],
    }
    results_dir = run_dir / "results"
    if not results_dir.exists():
        results_dir.mkdir(mode=0o700)
    _write_json_atomic(results_dir / "pilot-summary.json", summary, mode=0o600)
    if args.json:
        _safe_print(_safe_json_dumps(summary), preserve_newlines=True)
    else:
        _safe_print(
            f"Pilot {plan['study_id']}: records={len(records)}; claim=insufficient_evidence; eligible=false"
        )
        _safe_print(f"Machine summary: {results_dir / 'pilot-summary.json'}")
    return 0


def command_blind(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    plan, cases, expected = _load_run(run_dir)
    validation = _validate_records(run_dir, expected)
    if not validation["complete"]:
        _safe_print("Cannot blind an incomplete or invalid generation matrix", file=sys.stderr)
        return 1
    blind_dir = run_dir / "blind"
    key_path = run_dir / "private" / "assignment-key.json"
    if blind_dir.exists() or blind_dir.is_symlink() or key_path.exists() or key_path.is_symlink():
        raise StudyError("Blind package or assignment key already exists")
    pairs: dict[str, list[dict[str, Any]]] = {}
    for item in expected["records"]:
        pairs.setdefault(item["pair_key"], []).append(item)
    case_lookup = _case_map(cases)
    assignments: list[dict[str, Any]] = []
    public_pairs: list[dict[str, Any]] = []
    blind_dir.mkdir(mode=0o700)
    try:
        pairs_root = blind_dir / "pairs"
        pairs_root.mkdir(mode=0o700)
        for index, pair_key in enumerate(sorted(pairs), start=1):
            records = pairs[pair_key]
            by_condition = {record["condition"]: record for record in records}
            if set(by_condition) != set(CONDITIONS):
                raise StudyError(f"Pair is not complete: ordinal {index}")
            pair_id = f"pair-{index:04d}"
            if secrets.randbits(1):
                side_conditions = {"A": "framework", "B": "baseline"}
            else:
                side_conditions = {"A": "baseline", "B": "framework"}
            pair_dir = pairs_root / pair_id
            pair_dir.mkdir(mode=0o700)
            prompt_source = run_dir / records[0]["prompt"]
            _copy_regular_file(prompt_source, pair_dir / "prompt.txt", maximum=MAX_RESPONSE_BYTES, label="prompt")
            identity = records[0]
            public_sides: dict[str, str] = {}
            public_artifacts: dict[str, list[str]] = {}
            for side, condition in side_conditions.items():
                side_dir = pair_dir / side
                side_dir.mkdir(mode=0o700)
                record_root = run_dir / "records" / by_condition[condition]["unit_id"]
                response_source = record_root / "response.md"
                _copy_regular_file(
                    response_source,
                    side_dir / "response.md",
                    maximum=MAX_RESPONSE_BYTES,
                    label="response",
                )
                public_sides[side] = f"pairs/{pair_id}/{side}/response.md"
                stored_record = _read_json(record_root / "record.json", label="stored generation record")
                artifact_records = [
                    *_input_artifacts_for_case(run_dir, identity["case_id"]),
                    *stored_record.get("artifacts", []),
                ]
                copied_paths: list[str] = []
                for artifact_index, artifact in enumerate(artifact_records):
                    relative, digest, _ = _artifact_record(
                        artifact,
                        label=f"blind artifact {artifact_index}",
                    )
                    if relative.as_posix() in copied_paths:
                        continue
                    _copy_artifact(
                        source_root=record_root,
                        destination_root=side_dir,
                        relative=relative,
                        expected_sha256=digest,
                        label="blind artifact",
                    )
                    copied_paths.append(relative.as_posix())
                public_artifacts[side] = copied_paths
            assignments.append(
                {
                    "pair_id": pair_id,
                    "case_id": identity["case_id"],
                    "model_id": identity["model_id"],
                    "context_id": identity["context_id"],
                    "seed": identity["seed"],
                    "A": side_conditions["A"],
                    "B": side_conditions["B"],
                }
            )
            public_pairs.append(
                {
                    "pair_id": pair_id,
                    "prompt": f"pairs/{pair_id}/prompt.txt",
                    "sides": public_sides,
                    "artifacts": public_artifacts,
                    "required_semantic_slots": case_lookup[identity["case_id"]]["required_semantic_slots"],
                }
            )
        key = {
            "$schema": "blind-assignment.schema.json",
            "schema_version": "1.0",
            "study_id": plan["study_id"],
            "assignments": assignments,
        }
        manifest = {
            "schema_version": "1.0",
            "study_id": plan["study_id"],
            "instructions": (
                "Score each side independently before recording a pair preference. "
                "Condition names and machine checks are intentionally absent."
            ),
            "dimensions": list(DIMENSIONS),
            "pairs": public_pairs,
        }
        _write_json_atomic(key_path, key, mode=0o600)
        _write_json_atomic(blind_dir / "manifest.json", manifest, mode=0o600)
    except Exception:
        shutil.rmtree(blind_dir, ignore_errors=True)
        try:
            key_path.unlink()
        except OSError:
            pass
        raise
    _safe_print(f"Created blind packet with {len(public_pairs)} pair(s): {blind_dir}")
    _safe_print(f"Private assignment key: {key_path}")
    return 0


def command_rating_template(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    plan, _, _ = _load_run(run_dir)
    blind = _read_json(run_dir / "blind" / "manifest.json", label="blind manifest")
    pairs = blind.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        raise StudyError("Blind manifest contains no rating pairs")
    rater_id = _identifier(args.rater_id, "rater_id")
    output = Path(args.output)
    _reject_symlink_chain(output, "rating template output")
    if output.exists() or output.is_symlink():
        raise StudyError(f"Rating template output already exists: {output}")
    if not output.parent.is_dir():
        raise StudyError(f"Rating template parent does not exist: {output.parent}")
    ratings = []
    for pair in pairs:
        sides = {
            side: {
                "scores": {dimension: None for dimension in DIMENSIONS},
                "critical_errors": [],
                "semantic_slots_present": [],
                "comprehension": {
                    "status_correct": None,
                    "strongest_evidence_correct": None,
                    "next_action_or_limit_correct": None,
                    "elapsed_seconds": None,
                },
            }
            for side in ("A", "B")
        }
        ratings.append(
            {
                "pair_id": pair["pair_id"],
                "sides": sides,
                "preference": None,
                "notes": "",
            }
        )
    template = {
        "$schema": "rating-batch.schema.json",
        "schema_version": "1.0",
        "study_id": plan["study_id"],
        "rater_id": rater_id,
        "qualified": False,
        "independent": False,
        "ratings": ratings,
    }
    _write_json_atomic(output, template, mode=0o600)
    _safe_print(
        "Created an intentionally incomplete rating template; fill every null and set "
        f"qualification fields before freezing: {output}"
    )
    return 0


def _load_assignment_key(run_dir: Path) -> dict[str, Any]:
    key_path = run_dir / "private" / "assignment-key.json"
    _reject_symlink_chain(key_path, "assignment key")
    try:
        mode = stat.S_IMODE(key_path.stat().st_mode)
    except OSError as exc:
        raise StudyError(f"Cannot inspect assignment key: {exc}") from exc
    if mode & 0o077:
        raise StudyError("Assignment key must not grant group or other permissions")
    key = _read_json(key_path, label="assignment key")
    _require_object_shape(
        key,
        "assignment key",
        required=("schema_version", "study_id", "assignments"),
        optional=("$schema",),
    )
    if key["schema_version"] != "1.0" or not isinstance(key["assignments"], list):
        raise StudyError("Invalid assignment key")
    return key


def _validate_rating_batch(
    rating: dict[str, Any],
    *,
    study_id: str,
    pairs: dict[str, dict[str, Any]],
) -> str:
    _require_object_shape(
        rating,
        "rating batch",
        required=("schema_version", "study_id", "rater_id", "qualified", "independent", "ratings"),
        optional=("$schema",),
    )
    if rating["schema_version"] != "1.0" or rating["study_id"] != study_id:
        raise StudyError("rating batch version or study_id does not match")
    if "$schema" in rating:
        _nonempty_string(rating["$schema"], "rating batch $schema")
    rater_id = _identifier(rating["rater_id"], "rater_id")
    if not isinstance(rating["qualified"], bool) or not isinstance(rating["independent"], bool):
        raise StudyError("rating qualified and independent fields must be boolean")
    records = rating["ratings"]
    if not isinstance(records, list) or len(records) != len(pairs):
        raise StudyError("rating batch must contain exactly one record for every blind pair")
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise StudyError(f"rating record {index} must be an object")
        _require_object_shape(
            record,
            f"rating record {index}",
            required=("pair_id", "sides", "preference", "notes"),
        )
        pair_id = _identifier(record["pair_id"], f"rating record {index} pair_id")
        if pair_id not in pairs or pair_id in seen:
            raise StudyError("rating pair ids must be unique and match the blind manifest")
        seen.add(pair_id)
        _enum(
            record["preference"],
            "rating preference",
            {"A", "B", "tie"},
            error="rating preference must be A, B, or tie",
        )
        if not isinstance(record["notes"], str) or len(record["notes"]) > 2000:
            raise StudyError("rating notes must be a string of at most 2000 characters")
        sides = record["sides"]
        if not isinstance(sides, dict) or set(sides) != {"A", "B"}:
            raise StudyError("rating sides must contain exactly A and B")
        required_slots = set(pairs[pair_id]["required_semantic_slots"])
        for side in ("A", "B"):
            side_record = sides[side]
            if not isinstance(side_record, dict):
                raise StudyError(f"rating {pair_id} side {side} must be an object")
            _require_object_shape(
                side_record,
                f"rating {pair_id} side {side}",
                required=("scores", "critical_errors", "semantic_slots_present", "comprehension"),
            )
            scores = side_record["scores"]
            if not isinstance(scores, dict) or set(scores) != set(DIMENSIONS):
                raise StudyError("rating scores must contain exactly the seven dimensions")
            for dimension, score in scores.items():
                if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
                    raise StudyError(f"rating score {dimension} must be an integer from 1 to 5")
            critical = side_record["critical_errors"]
            if not isinstance(critical, list) or len(critical) > 20:
                raise StudyError("critical_errors must be a list of at most 20 records")
            seen_critical: set[tuple[str, str]] = set()
            for finding in critical:
                if not isinstance(finding, dict) or set(finding) != {"label", "evidence"}:
                    raise StudyError("critical error records require label and evidence")
                _enum(finding["label"], "critical error label", CRITICAL_ERROR_LABELS)
                _nonempty_string(finding["evidence"], "critical error evidence", maximum=1000)
                identity = (finding["label"], finding["evidence"])
                if identity in seen_critical:
                    raise StudyError("critical_errors records must be unique")
                seen_critical.add(identity)
            present = side_record["semantic_slots_present"]
            if not isinstance(present, list) or any(
                not isinstance(slot, str) or not re.fullmatch(r"[a-z0-9_]+", slot)
                for slot in present
            ):
                raise StudyError("semantic_slots_present must be a unique subset of required slots")
            if len(present) != len(set(present)) or set(present) - required_slots:
                raise StudyError("semantic_slots_present must be a unique subset of required slots")
            comprehension = side_record["comprehension"]
            if not isinstance(comprehension, dict):
                raise StudyError("comprehension must be an object")
            _require_object_shape(
                comprehension,
                "comprehension",
                required=(
                    "status_correct", "strongest_evidence_correct",
                    "next_action_or_limit_correct", "elapsed_seconds",
                ),
            )
            for field in ("status_correct", "strongest_evidence_correct", "next_action_or_limit_correct"):
                if not isinstance(comprehension[field], bool):
                    raise StudyError(f"comprehension {field} must be boolean")
            _number(comprehension["elapsed_seconds"], "comprehension elapsed_seconds", minimum=0, maximum=3600)
    return rater_id


def command_freeze_ratings(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    plan, _, _ = _load_run(run_dir)
    key = _load_assignment_key(run_dir)
    blind = _read_json(run_dir / "blind" / "manifest.json", label="blind manifest")
    pairs = {record["pair_id"]: record for record in blind.get("pairs", [])}
    if not pairs:
        raise StudyError("Blind manifest contains no pairs")
    ratings_dir = run_dir / "ratings"
    receipt_path = run_dir / "ratings-lock.json"
    if ratings_dir.exists() or ratings_dir.is_symlink() or receipt_path.exists() or receipt_path.is_symlink():
        raise StudyError("Ratings are already frozen")
    if key.get("study_id") != plan["study_id"]:
        raise StudyError("Assignment key study_id does not match")
    loaded: list[tuple[str, Path, bytes]] = []
    seen_raters: set[str] = set()
    for path_text in args.rating:
        path = Path(path_text)
        raw = _read_bounded_bytes(path, maximum=MAX_JSON_BYTES, label="rating batch")
        rating = _read_json(path, label="rating batch")
        rater_id = _validate_rating_batch(rating, study_id=plan["study_id"], pairs=pairs)
        if rater_id in seen_raters:
            raise StudyError(f"duplicate rater_id: {rater_id}")
        seen_raters.add(rater_id)
        loaded.append((rater_id, path, raw))
    if len(loaded) < plan["rating"]["required_raters"]:
        raise StudyError("Not enough independent rating batches to freeze the study")
    ratings_dir.mkdir(mode=0o700)
    try:
        receipt_records: list[dict[str, str]] = []
        for rater_id, _, raw in sorted(loaded):
            destination = ratings_dir / f"{rater_id}.json"
            _write_bytes_atomic(destination, raw, mode=0o600)
            receipt_records.append(
                {"rater_id": rater_id, "path": f"ratings/{rater_id}.json", "sha256": _sha256(destination)}
            )
        receipt = {
            "schema_version": "1.0",
            "study_id": plan["study_id"],
            "assignment_key_sha256": _sha256(run_dir / "private" / "assignment-key.json"),
            "blind_packet_sha256": _directory_tree_sha256(
                run_dir / "blind",
                label="blind packet",
            ),
            "ratings": receipt_records,
        }
        _write_json_atomic(receipt_path, receipt, mode=0o600)
    except Exception:
        shutil.rmtree(ratings_dir, ignore_errors=True)
        try:
            receipt_path.unlink()
        except OSError:
            pass
        raise
    _safe_print(f"Frozen {len(loaded)} rating batch(es): {receipt_path}")
    return 0


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _paired_bootstrap(differences: list[float], *, resamples: int, seed: int) -> dict[str, Any]:
    if not differences:
        return {"estimate": None, "ci95": [None, None], "case_count": 0}
    generator = random.Random(seed)
    count = len(differences)
    samples = [
        sum(differences[generator.randrange(count)] for _ in range(count)) / count
        for _ in range(resamples)
    ]
    return {
        "estimate": _mean(differences),
        "ci95": [_percentile(samples, 0.025), _percentile(samples, 0.975)],
        "case_count": count,
        "resamples": resamples,
        "seed": seed,
    }


def _load_ratings_lock(run_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    receipt = _read_json(run_dir / "ratings-lock.json", label="ratings lock")
    _require_object_shape(
        receipt,
        "ratings lock",
        required=(
            "schema_version", "study_id", "assignment_key_sha256",
            "blind_packet_sha256", "ratings",
        ),
    )
    if receipt["schema_version"] != "1.0" or receipt["study_id"] != plan["study_id"]:
        raise StudyError("Ratings lock version or study_id does not match")
    key_path = run_dir / "private" / "assignment-key.json"
    if receipt["assignment_key_sha256"] != _sha256(key_path):
        raise StudyError("Assignment key changed after ratings were frozen")
    if receipt["blind_packet_sha256"] != _directory_tree_sha256(
        run_dir / "blind",
        label="blind packet",
    ):
        raise StudyError("Blind packet changed after ratings were frozen")
    if not isinstance(receipt["ratings"], list):
        raise StudyError("Ratings lock ratings must be a list")
    return receipt


def _load_frozen_ratings(
    run_dir: Path,
    plan: dict[str, Any],
    pairs: dict[str, dict[str, Any]],
    *,
    receipt: dict[str, Any],
) -> list[dict[str, Any]]:
    loaded: list[dict[str, Any]] = []
    for item in receipt["ratings"]:
        if not isinstance(item, dict) or set(item) != {"rater_id", "path", "sha256"}:
            raise StudyError("Ratings lock contains an invalid record")
        path = run_dir / item["path"]
        if _sha256(path) != item["sha256"]:
            raise StudyError("A rating batch changed after ratings were frozen")
        rating = _read_json(path, label="frozen rating batch")
        _validate_rating_batch(rating, study_id=plan["study_id"], pairs=pairs)
        loaded.append(rating)
    if len(loaded) < plan["rating"]["required_raters"]:
        raise StudyError("Ratings lock does not contain the required number of raters")
    return loaded


def _claim_prerequisites(
    run_dir: Path,
    plan: dict[str, Any],
    cases: dict[str, Any],
    ratings: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> list[str]:
    missing: list[str] = []
    if plan["study_kind"] == "pilot":
        missing.append("pilot")
    if plan["study_kind"] != "public":
        missing.append("public-study-profile")
    if not plan["benchmark"]["heldout"] or plan["benchmark"]["cases_sha256"] == _sha256(PUBLIC_CASES):
        missing.append("private-heldout")
    if not plan["benchmark"]["preregistration_receipt"]:
        missing.append("external-preregistration-receipt")
    if (
        plan["execution"]["baseline_isolation"] != "external-sandbox"
        or not plan["execution"]["isolation_receipt"]
    ):
        missing.append("external-per-unit-isolation-receipt")
    if plan["execution"]["global_instruction_policy"] != "shared-and-audited":
        missing.append("audited-global-instruction-policy")
    case_lookup = _case_map(cases)
    scenario_counts: dict[str, int] = {}
    for case_id in plan["benchmark"]["case_ids"]:
        scenario = case_lookup[case_id]["scenario"]
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
    if len(scenario_counts) < 7 or any(count < 4 for count in scenario_counts.values()):
        missing.append("four-heldout-cases-per-scenario")
    selected_cases = [case_lookup[case_id] for case_id in plan["benchmark"]["case_ids"]]
    visual_necessities = {case["visual_oracle"]["necessity"] for case in selected_cases}
    if "required" not in visual_necessities:
        missing.append("visual-required-oracle-coverage")
    if "forbidden" not in visual_necessities:
        missing.append("visual-forbidden-oracle-coverage")
    selected_check_types = {
        check["type"]
        for case in selected_cases
        for check in case["machine_checks"]
    }
    if "required_image" not in selected_check_types:
        missing.append("required-local-image-check-coverage")
    if not selected_check_types & {"min_markdown_tables", "max_markdown_tables"}:
        missing.append("declared-table-check-coverage")
    if len(plan["seeds"]) < 3:
        missing.append("three-seeds")
    if len({model["revision"] for model in plan["models"]}) < 2:
        missing.append("multiple-model-revisions")
    if any(not model["revision_receipt"] for model in plan["models"]):
        missing.append("model-revision-receipts")
    if any(model["host"] == "manual" for model in plan["models"]):
        missing.append("controller-bound-executable-hosts")
    if plan["execution"]["replicate_semantics"] != "independent-repeat":
        missing.append("declared-independent-repeats")
    if plan["study_kind"] == "public":
        if not _controller_has_unique_workspaces(run_dir, records):
            missing.append("controller-unique-workspaces")
    occupancy = [context["target_occupancy_percent"] for context in plan["contexts"]]
    if not any(value <= 15 for value in occupancy) or not any(45 <= value <= 55 for value in occupancy) or not any(value >= 85 for value in occupancy):
        missing.append("10-50-85-context-strata")
    if not any(context["compaction_required"] for context in plan["contexts"]):
        missing.append("compaction-resume-stratum")
    if len(ratings) < 2 or any(not rating["qualified"] or not rating["independent"] for rating in ratings):
        missing.append("independent-qualified-raters")
    if any(record["observations"]["telemetry_source"] != "host_adapter" for record in records):
        missing.append("host-adapter-telemetry")
    framework_records = [record for record in records if record["condition"] == "framework"]
    baseline_records = [record for record in records if record["condition"] == "baseline"]
    if any(
        record["observations"]["host_activation_observed"] is not True
        or record["observations"]["skill_read"] is not True
        for record in framework_records
    ):
        missing.append("observed-framework-activation")
    if any(
        record["observations"]["final_audit_passed"] is not True
        for record in framework_records
    ):
        missing.append("framework-final-audit-contract")
    if any(record["observations"]["skill_read"] is True for record in baseline_records):
        missing.append("baseline-activation-contamination")
    if any(
        record["usage"][field] is None
        for record in records
        for field in ("input_tokens", "output_tokens")
    ):
        missing.append("complete-token-telemetry")
    if any(
        record["observations"]["output_token_cap_enforced"] is not True
        for record in records
    ):
        missing.append("enforced-output-token-cap")
    if any(record["usage"]["context_occupancy_percent"] is None for record in records):
        missing.append("observed-context-occupancy")
    context_lookup = {context["id"]: context for context in plan["contexts"]}
    if any(
        record["usage"]["context_occupancy_percent"] is not None
        and abs(
            record["usage"]["context_occupancy_percent"]
            - context_lookup[record["context_id"]]["target_occupancy_percent"]
        ) > 5
        for record in records
    ):
        missing.append("observed-context-strata")
    compaction_records = [
        record
        for record in records
        if context_lookup[record["context_id"]]["compaction_required"]
    ]
    if any(record["usage"]["compaction_observed"] is None for record in records):
        missing.append("complete-compaction-telemetry")
    if any(record["usage"]["compaction_observed"] is not True for record in compaction_records):
        missing.append("observed-required-compaction")
    checkpoint_records = [
        record
        for record in framework_records
        if context_lookup[record["context_id"]]["compaction_required"]
    ]
    if any(
        record["observations"][field] is not True
        for record in checkpoint_records
        for field in ("checkpoint_created", "checkpoint_reloaded", "checkpoint_audit_passed")
    ):
        missing.append("framework-checkpoint-contract")
    if any(
        record["observations"]["checkpoint_receipt_verified"] is not True
        for record in checkpoint_records
    ):
        missing.append("framework-checkpoint-receipts")
    return sorted(set(missing))


def _controller_has_unique_workspaces(
    run_dir: Path,
    records: list[dict[str, Any]],
) -> bool:
    """Require one controller-locked host workspace identity per generation unit."""

    workspaces: list[str] = []
    try:
        for record in records:
            host_plan = _load_host_plan(run_dir, record["unit_id"])
            workspace = host_plan.get("workspace")
            if not isinstance(workspace, str) or not workspace:
                return False
            workspaces.append(workspace)
    except (KeyError, OSError, StudyError):
        return False
    return len(workspaces) == len(records) and len(set(workspaces)) == len(workspaces)


def _long_soak_metrics(
    records: list[dict[str, Any]],
    context_lookup: dict[str, dict[str, Any]],
) -> dict[str, float | None]:
    """Compare the common final-audit contract, not checkpoint use, across strata."""

    soak_records = [
        record
        for record in records
        if record["condition"] == "framework"
        and context_lookup[record["context_id"]]["target_occupancy_percent"] >= 85
    ]
    fresh_records = [
        record
        for record in records
        if record["condition"] == "framework"
        and context_lookup[record["context_id"]]["target_occupancy_percent"] <= 15
    ]
    soak_pass = _mean(
        [
            1.0 if record["observations"]["final_audit_passed"] is True else 0.0
            for record in soak_records
            if record["observations"]["final_audit_passed"] is not None
        ]
    )
    fresh_pass = _mean(
        [
            1.0 if record["observations"]["final_audit_passed"] is True else 0.0
            for record in fresh_records
            if record["observations"]["final_audit_passed"] is not None
        ]
    )
    return {
        "fresh_pass_rate": fresh_pass,
        "soak85_pass_rate": soak_pass,
        "gap": (
            fresh_pass - soak_pass
            if fresh_pass is not None and soak_pass is not None
            else None
        ),
    }


def _aggregate(run_dir: Path) -> dict[str, Any]:
    plan, cases, expected = _load_run(run_dir)
    validation = _validate_records(run_dir, expected)
    if not validation["complete"]:
        raise StudyError("Cannot aggregate an incomplete generation matrix")
    key = _load_assignment_key(run_dir)
    ratings_lock = _load_ratings_lock(run_dir, plan)
    blind = _read_json(run_dir / "blind" / "manifest.json", label="blind manifest")
    pairs = {record["pair_id"]: record for record in blind.get("pairs", [])}
    ratings = _load_frozen_ratings(
        run_dir,
        plan,
        pairs,
        receipt=ratings_lock,
    )
    assignments = {record["pair_id"]: record for record in key["assignments"]}
    if set(assignments) != set(pairs):
        raise StudyError("Assignment key and blind manifest pair sets differ")

    records: list[dict[str, Any]] = []
    by_unit: dict[str, dict[str, Any]] = {}
    for expected_record in expected["records"]:
        record = _read_json(
            run_dir / "records" / expected_record["unit_id"] / "record.json",
            label="stored generation record",
        )
        records.append(record)
        by_unit[record["unit_id"]] = record

    dimension_values: dict[str, dict[str, list[float]]] = {
        condition: {dimension: [] for dimension in DIMENSIONS} for condition in CONDITIONS
    }
    primary_values_by_case: dict[str, dict[str, list[float]]] = {}
    task_values_by_case: dict[str, dict[str, list[float]]] = {}
    preference_counts = {"framework": 0, "baseline": 0, "tie": 0}
    critical_error_count = 0
    semantic_present = 0
    semantic_total = 0
    semantic_density_values: dict[str, list[float]] = {
        condition: [] for condition in CONDITIONS
    }
    agreement_groups: dict[tuple[str, str, str], list[int]] = {}
    primary_dimensions = plan["analysis"]["primary_dimensions"]
    primary_context_ids = set(plan["analysis"]["primary_context_ids"])

    for batch in ratings:
        for rating in batch["ratings"]:
            assignment = assignments[rating["pair_id"]]
            preference = rating["preference"]
            if preference == "tie":
                preference_counts["tie"] += 1
            else:
                preference_counts[assignment[preference]] += 1
            for side in ("A", "B"):
                condition = assignment[side]
                side_record = rating["sides"][side]
                for dimension in DIMENSIONS:
                    score = side_record["scores"][dimension]
                    dimension_values[condition][dimension].append(score)
                    agreement_groups.setdefault((rating["pair_id"], side, dimension), []).append(score)
                critical_error_count += len(side_record["critical_errors"])
                required_slots = set(pairs[rating["pair_id"]]["required_semantic_slots"])
                present_slots = len(
                    set(side_record["semantic_slots_present"]) & required_slots
                )
                if condition == "framework":
                    semantic_present += present_slots
                    semantic_total += len(required_slots)
                unit_id = _record_unit_id(
                    assignment["case_id"],
                    assignment["model_id"],
                    assignment["context_id"],
                    assignment["seed"],
                    condition,
                )
                output_tokens = by_unit[unit_id]["usage"]["output_tokens"]
                if isinstance(output_tokens, int) and output_tokens > 0:
                    semantic_density_values[condition].append(
                        1000.0 * present_slots / output_tokens
                    )
                if assignment["context_id"] in primary_context_ids:
                    case_id = assignment["case_id"]
                    primary_values_by_case.setdefault(
                        case_id, {"baseline": [], "framework": []}
                    )[condition].append(
                        sum(side_record["scores"][dimension] for dimension in primary_dimensions)
                        / len(primary_dimensions)
                    )
                    task_values_by_case.setdefault(
                        case_id, {"baseline": [], "framework": []}
                    )[condition].append(side_record["scores"]["task_fidelity"])

    dimension_means = {
        condition: {
            dimension: _mean(values) for dimension, values in dimension_values[condition].items()
        }
        for condition in CONDITIONS
    }
    primary_differences = [
        float(_mean(values["framework"]) - _mean(values["baseline"]))
        for values in primary_values_by_case.values()
        if values["framework"] and values["baseline"]
    ]
    task_differences = [
        float(_mean(values["framework"]) - _mean(values["baseline"]))
        for values in task_values_by_case.values()
        if values["framework"] and values["baseline"]
    ]
    bootstrap_settings = plan["analysis"]
    primary_bootstrap = _paired_bootstrap(
        primary_differences,
        resamples=bootstrap_settings["bootstrap_resamples"],
        seed=bootstrap_settings["bootstrap_seed"],
    )
    task_bootstrap = _paired_bootstrap(
        task_differences,
        resamples=bootstrap_settings["bootstrap_resamples"],
        seed=bootstrap_settings["bootstrap_seed"] + 1,
    )

    agreement_pairs = 0
    agreement_within_one = 0
    for scores in agreement_groups.values():
        for left in range(len(scores)):
            for right in range(left + 1, len(scores)):
                agreement_pairs += 1
                if abs(scores[left] - scores[right]) <= 1:
                    agreement_within_one += 1
    agreement_rate = agreement_within_one / agreement_pairs if agreement_pairs else None

    framework_checks_passed = 0
    framework_checks_total = 0
    mandatory_display_checks_passed = 0
    mandatory_display_checks_total = 0
    visual_counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    case_lookup = _case_map(cases)
    paired_token_overheads: list[float] = []
    expected_by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    for expected_record in expected["records"]:
        expected_by_pair.setdefault(expected_record["pair_key"], {})[expected_record["condition"]] = expected_record
        if expected_record["condition"] != "framework":
            continue
        record = by_unit[expected_record["unit_id"]]
        machine = record["machine_evaluation"]
        framework_checks_passed += machine["checks_passed"]
        framework_checks_total += machine["checks_total"]
        for check in machine["checks"]:
            if check["type"] in MANDATORY_DISPLAY_CHECK_TYPES:
                mandatory_display_checks_total += 1
                mandatory_display_checks_passed += int(check["passed"] is True)
        necessity = case_lookup[record["case_id"]]["visual_oracle"]["necessity"]
        actual = machine["image_count"] > 0 or machine["markdown_table_count"] > 0
        if necessity == "required":
            visual_counts["tp" if actual else "fn"] += 1
        elif necessity == "forbidden":
            visual_counts["fp" if actual else "tn"] += 1
    for condition_records in expected_by_pair.values():
        baseline = by_unit[condition_records["baseline"]["unit_id"]]["usage"]["output_tokens"]
        framework = by_unit[condition_records["framework"]["unit_id"]]["usage"]["output_tokens"]
        if isinstance(baseline, int) and isinstance(framework, int) and baseline > 0:
            paired_token_overheads.append((framework - baseline) / baseline)

    machine_rate = framework_checks_passed / framework_checks_total if framework_checks_total else None
    visual_precision_denominator = visual_counts["tp"] + visual_counts["fp"]
    visual_recall_denominator = visual_counts["tp"] + visual_counts["fn"]
    visual_precision = visual_counts["tp"] / visual_precision_denominator if visual_precision_denominator else None
    visual_recall = visual_counts["tp"] / visual_recall_denominator if visual_recall_denominator else None
    total_preferences = sum(preference_counts.values())
    win_rate = preference_counts["framework"] / total_preferences if total_preferences else None
    loss_rate = preference_counts["baseline"] / total_preferences if total_preferences else None
    semantic_rate = semantic_present / semantic_total if semantic_total else None
    semantic_density_baseline = _mean(semantic_density_values["baseline"])
    semantic_density_framework = _mean(semantic_density_values["framework"])
    semantic_density_difference = (
        semantic_density_framework - semantic_density_baseline
        if semantic_density_framework is not None and semantic_density_baseline is not None
        else None
    )
    mandatory_display_rate = (
        mandatory_display_checks_passed / mandatory_display_checks_total
        if mandatory_display_checks_total
        else None
    )

    context_lookup = {context["id"]: context for context in plan["contexts"]}
    long_soak_metrics = _long_soak_metrics(records, context_lookup)
    soak_pass = long_soak_metrics["soak85_pass_rate"]
    fresh_pass = long_soak_metrics["fresh_pass_rate"]

    metrics = {
        "human_dimension_means": dimension_means,
        "primary_composite": {
            "difference": primary_bootstrap["estimate"],
            "ci95": primary_bootstrap["ci95"],
            "case_count": primary_bootstrap["case_count"],
            "resamples": primary_bootstrap.get("resamples"),
        },
        "task_fidelity_difference": {
            "difference": task_bootstrap["estimate"],
            "ci95": task_bootstrap["ci95"],
        },
        "preference": {**preference_counts, "win_rate": win_rate, "loss_rate": loss_rate},
        "machine_invariant_pass_rate": machine_rate,
        "mandatory_display_checks": {
            "passed": mandatory_display_checks_passed,
            "total": mandatory_display_checks_total,
            "pass_rate": mandatory_display_rate,
        },
        "semantic_slot_adherence": semantic_rate,
        "semantic_slot_density_per_1000_output_tokens": {
            "baseline": semantic_density_baseline,
            "framework": semantic_density_framework,
            "difference": semantic_density_difference,
        },
        "visual_selection": {
            **visual_counts,
            "precision": visual_precision,
            "recall": visual_recall,
        },
        "token_overhead": {
            "median": _percentile(paired_token_overheads, 0.5),
            "p90": _percentile(paired_token_overheads, 0.9),
        },
        "agreement_within_one": agreement_rate,
        "long_soak": long_soak_metrics,
    }

    thresholds = plan["analysis"]["thresholds"]
    gates: dict[str, bool | None] = {
        "zero_critical_errors": critical_error_count == 0,
        "machine_invariant_pass_rate": machine_rate is not None and machine_rate >= thresholds["machine_pass_rate_min"],
        "mandatory_display_checks": (
            mandatory_display_checks_total > 0
            and mandatory_display_checks_passed == mandatory_display_checks_total
        ),
        "primary_gain": primary_bootstrap["estimate"] is not None and primary_bootstrap["estimate"] >= thresholds["primary_gain_min"],
        "primary_ci": primary_bootstrap["ci95"][0] is not None and primary_bootstrap["ci95"][0] > thresholds["primary_ci_lower_min"],
        "task_fidelity_noninferior": task_bootstrap["ci95"][0] is not None and task_bootstrap["ci95"][0] > -thresholds["task_fidelity_margin"],
        "win_rate": win_rate is not None and win_rate >= thresholds["win_rate_min"],
        "loss_rate": loss_rate is not None and loss_rate <= thresholds["loss_rate_max"],
        "semantic_slots": semantic_rate is not None and semantic_rate >= thresholds["semantic_slot_rate_min"],
        "semantic_density_noninferior": (
            semantic_density_difference is not None
            and semantic_density_difference
            >= thresholds["semantic_density_difference_min"]
        ),
        "visual_precision": visual_precision is not None and visual_precision >= thresholds["visual_precision_min"],
        "visual_recall": visual_recall is not None and visual_recall >= thresholds["visual_recall_min"],
        "token_median": metrics["token_overhead"]["median"] is not None and metrics["token_overhead"]["median"] <= thresholds["token_overhead_median_max"],
        "token_p90": metrics["token_overhead"]["p90"] is not None and metrics["token_overhead"]["p90"] <= thresholds["token_overhead_p90_max"],
        "agreement": agreement_rate is not None and agreement_rate >= thresholds["agreement_within_one_min"],
        "long_soak": (
            soak_pass is not None
            and fresh_pass is not None
            and soak_pass >= thresholds["long_soak_pass_rate_min"]
            and fresh_pass - soak_pass <= thresholds["long_soak_fresh_gap_max"]
        ),
    }
    for dimension in DIMENSIONS:
        threshold = (
            thresholds["priority_dimension_min"]
            if dimension in PRIORITY_DIMENSIONS
            else thresholds["human_dimension_min"]
        )
        value = dimension_means["framework"][dimension]
        gates[f"human_{dimension}"] = value is not None and value >= threshold

    missing = _claim_prerequisites(run_dir, plan, cases, ratings, records)
    if missing:
        claim_status = "insufficient_evidence"
    elif all(value is True for value in gates.values()):
        claim_status = "pass"
    else:
        claim_status = "fail"
    report = {
        "$schema": "study-report.schema.json",
        "schema_version": "1.0",
        "study_id": plan["study_id"],
        "study_kind": plan["study_kind"],
        "claim_boundary": plan["claim_boundary"],
        "input_receipts": {
            "plan_sha256": _sha256(run_dir / "plan.json"),
            "cases_sha256": _sha256(run_dir / "cases.json"),
            "input_artifacts_sha256": _sha256(run_dir / "input-artifacts.json"),
            "assignment_key_sha256": _sha256(run_dir / "private" / "assignment-key.json"),
            "ratings_lock_sha256": _sha256(run_dir / "ratings-lock.json"),
        },
        "generation": {
            "record_count": len(records),
            "pair_count": len(assignments),
        },
        "ratings": {
            "rater_count": len(ratings),
            "qualified_independent_count": sum(
                1 for rating in ratings if rating["qualified"] and rating["independent"]
            ),
        },
        "critical_error_count": critical_error_count,
        "metrics": metrics,
        "gates": gates,
        "claim": {
            "status": claim_status,
            "effectiveness_claim_eligible": claim_status == "pass" and plan["study_kind"] == "public",
            "missing_prerequisites": missing,
            "failed_gates": sorted(name for name, value in gates.items() if value is False),
        },
        "limitations": [
            "Unkeyed file digests detect drift but do not authenticate the operator.",
            "Human scores do not verify scientific truth or host isolation by themselves.",
            (
                "A/B packets omit controller condition metadata, but verbatim response "
                "content or style may reveal treatment to raters."
            ),
        ],
    }
    return report


def command_aggregate(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    report = _aggregate(run_dir)
    results_dir = run_dir / "results"
    if not results_dir.exists():
        results_dir.mkdir(mode=0o700)
    _write_json_atomic(results_dir / "study-report.json", report, mode=0o600)
    if args.json:
        _safe_print(_safe_json_dumps(report), preserve_newlines=True)
    else:
        _safe_print(
            f"Study {report['study_id']}: claim={report['claim']['status']}; "
            f"eligible={str(report['claim']['effectiveness_claim_eligible']).lower()}"
        )
        _safe_print(f"Machine report: {results_dir / 'study-report.json'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(
        description="Prepare, blind, rate, and aggregate private reporting studies."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Freeze a preregistered private study run.")
    init_parser.add_argument("--plan", required=True)
    init_parser.add_argument("--cases-file", required=True)
    init_parser.add_argument("--artifact-root")
    init_parser.add_argument("--output", required=True)
    init_parser.set_defaults(func=command_init)

    import_parser = subparsers.add_parser("import-output", help="Import one immutable generation record.")
    import_parser.add_argument("--run-dir", required=True)
    import_parser.add_argument("--record", required=True)
    import_parser.add_argument("--response", required=True)
    import_parser.add_argument("--transcript")
    import_parser.add_argument("--artifact-root")
    import_parser.set_defaults(func=command_import_output)

    host_plan_parser = subparsers.add_parser(
        "host-plan",
        help="Freeze a typed host command receipt without executing the host.",
    )
    host_plan_parser.add_argument("--run-dir", required=True)
    host_plan_parser.add_argument("--unit-id", required=True)
    host_plan_parser.add_argument("--executable", required=True)
    host_plan_parser.add_argument("--workspace", required=True)
    host_plan_parser.set_defaults(func=command_host_plan)

    host_run_parser = subparsers.add_parser(
        "host-run",
        help="Execute one previously frozen host plan only with explicit authorization.",
    )
    host_run_parser.add_argument("--run-dir", required=True)
    host_run_parser.add_argument("--unit-id", required=True)
    host_run_parser.add_argument("--execute", action="store_true")
    host_run_parser.set_defaults(func=command_host_run)

    validate_parser = subparsers.add_parser("validate", help="Check generation matrix completeness and digests.")
    validate_parser.add_argument("--run-dir", required=True)
    validate_parser.add_argument("--json", action="store_true")
    validate_parser.set_defaults(func=command_validate)

    pilot_parser = subparsers.add_parser(
        "pilot-summary",
        help="Summarize a complete pilot generation matrix without making an effectiveness claim.",
    )
    pilot_parser.add_argument("--run-dir", required=True)
    pilot_parser.add_argument("--json", action="store_true")
    pilot_parser.set_defaults(func=command_pilot_summary)

    blind_parser = subparsers.add_parser("blind", help="Create a randomized A/B packet and private key.")
    blind_parser.add_argument("--run-dir", required=True)
    blind_parser.set_defaults(func=command_blind)

    rating_template_parser = subparsers.add_parser(
        "rating-template",
        help="Create one intentionally incomplete blind rating form.",
    )
    rating_template_parser.add_argument("--run-dir", required=True)
    rating_template_parser.add_argument("--rater-id", required=True)
    rating_template_parser.add_argument("--output", required=True)
    rating_template_parser.set_defaults(func=command_rating_template)

    freeze_parser = subparsers.add_parser("freeze-ratings", help="Validate and lock blind rating batches.")
    freeze_parser.add_argument("--run-dir", required=True)
    freeze_parser.add_argument("--rating", action="append", required=True)
    freeze_parser.set_defaults(func=command_freeze_ratings)

    aggregate_parser = subparsers.add_parser("aggregate", help="Deblind and aggregate a frozen study.")
    aggregate_parser.add_argument("--run-dir", required=True)
    aggregate_parser.add_argument("--json", action="store_true")
    aggregate_parser.set_defaults(func=command_aggregate)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return int(args.func(args))
    except StudyError as exc:
        _safe_print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        _safe_print("error: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
