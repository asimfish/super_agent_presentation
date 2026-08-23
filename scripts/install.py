#!/usr/bin/env python3
"""Safely plan or install Agentic Reporting into an agent project.

The default `plan` command is read-only. `apply` copies the self-contained skill and
creates a host adapter only when that adapter path is absent. Existing instruction
files are never replaced; appending requires the explicit --append-adapter flag and
creates a timestamped backup first.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SOURCE = REPO_ROOT / "skills" / "agentic-reporting"
MARKER_START = "<!-- agentic-reporting:begin -->"
MARKER_END = "<!-- agentic-reporting:end -->"
MAX_INSTRUCTION_BYTES = 2 * 1024 * 1024
MAX_SKILL_BYTES = 32 * 1024 * 1024
MAX_SKILL_ENTRIES = 4096
IGNORED_SKILL_NAMES = {".DS_Store", "__pycache__"}

HOSTS = {
    "agents": {
        "project": {
            "skill_dir": ".agents/skills/agentic-reporting",
            "adapter_source": "adapters/agents/AGENTS.snippet.md",
            "adapter_target": "AGENTS.md",
        }
    },
    "codex": {
        "project": {
            "skill_dir": ".agents/skills/agentic-reporting",
            "adapter_source": "adapters/codex/AGENTS.md",
            "adapter_target": "AGENTS.md",
        },
        "user": {
            "skill_dir": ".agents/skills/agentic-reporting",
            "adapter_source": "adapters/codex/AGENTS.md",
            "adapter_target": ".codex/AGENTS.md",
        },
    },
    "claude": {
        "project": {
            "skill_dir": ".claude/skills/agentic-reporting",
            "adapter_source": "adapters/claude/CLAUDE.snippet.md",
            "adapter_target": "CLAUDE.md",
        },
        "user": {
            "skill_dir": ".claude/skills/agentic-reporting",
            "adapter_source": "adapters/claude/CLAUDE.snippet.md",
            "adapter_target": ".claude/CLAUDE.md",
        },
    },
    "cursor": {
        "project": {
            "skill_dir": ".agents/skills/agentic-reporting",
            "adapter_source": "adapters/cursor/agentic-reporting.mdc",
            "adapter_target": ".cursor/rules/agentic-reporting.mdc",
        }
    },
    "copilot": {
        "project": {
            "skill_dir": ".agents/skills/agentic-reporting",
            "adapter_source": "adapters/copilot/copilot-instructions.snippet.md",
            "adapter_target": ".github/copilot-instructions.md",
        }
    },
}


class InstallError(RuntimeError):
    pass


TERMINAL_FORMAT_CONTROLS = frozenset(
    {
        0x061C, 0x200E, 0x200F, 0x2028, 0x2029,
        *range(0x202A, 0x202F), *range(0x2066, 0x206A),
    }
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
        elif 0x80 <= codepoint <= 0x9F or codepoint in TERMINAL_FORMAT_CONTROLS:
            output.append(f"\\u{codepoint:04x}")
        else:
            output.append(character)
    return "".join(output)


def _safe_print(value: Any = "", *, file: Any = None) -> None:
    print(_terminal_safe_text(value), file=file)


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


def safe_text_write(path: Path, text: str, mode: int) -> None:
    if path.is_symlink():
        raise InstallError(f"Refusing to write through symlink: {path}")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    except OSError as exc:
        raise InstallError(f"Cannot prepare instruction write at {path}: {exc}") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except Exception as exc:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise InstallError(f"Cannot write instruction file {path}: {exc}") from exc


def adapter_block(source: Path) -> str:
    if source.is_symlink() or not source.is_file():
        raise InstallError(f"Adapter source must be a regular non-symlink file: {source}")
    try:
        size = source.stat().st_size
        if size > MAX_INSTRUCTION_BYTES:
            raise InstallError(
                f"Adapter source is {size} bytes; limit is {MAX_INSTRUCTION_BYTES}: {source}"
            )
        content = source.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError as exc:
        raise InstallError(f"Adapter source must be UTF-8 text: {source}") from exc
    except OSError as exc:
        raise InstallError(f"Cannot read adapter source {source}: {exc}") from exc
    return f"{MARKER_START}\n{content}\n{MARKER_END}\n"


def read_existing_instruction(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise InstallError(f"Instruction destination must be a regular non-symlink file: {path}")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise InstallError(f"Cannot inspect instruction file {path}: {exc}") from exc
    if size > MAX_INSTRUCTION_BYTES:
        raise InstallError(
            f"Instruction file is {size} bytes; automatic inspection limit is {MAX_INSTRUCTION_BYTES}: {path}"
        )
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise InstallError(f"Instruction file must be UTF-8 text for automatic merge: {path}") from exc
    except OSError as exc:
        raise InstallError(f"Cannot read instruction file {path}: {exc}") from exc


def extract_marker_block(text: str, path: Path) -> str | None:
    starts = text.count(MARKER_START)
    ends = text.count(MARKER_END)
    if starts == 0 and ends == 0:
        return None
    if starts == 1 and ends == 1 and text.index(MARKER_START) < text.index(MARKER_END):
        start = text.index(MARKER_START)
        end = text.index(MARKER_END) + len(MARKER_END)
        return text[start:end]
    raise InstallError(f"Instruction file has an incomplete or duplicate agentic-reporting marker: {path}")


def resolve_actions(target: Path, hosts: list[str], scope: str) -> tuple[dict[Path, list[str]], list[tuple[str, Path, Path]]]:
    skill_destinations: dict[Path, list[str]] = {}
    adapters: list[tuple[str, Path, Path]] = []
    for host in hosts:
        config = HOSTS[host].get(scope)
        if config is None:
            raise InstallError(f"Host '{host}' does not define a supported {scope}-scope installation")
        skill_destination = target / config["skill_dir"]
        skill_destinations.setdefault(skill_destination, []).append(host)
        source = REPO_ROOT / config["adapter_source"]
        destination = target / config["adapter_target"]
        if host == "codex":
            override = (
                target / ".codex" / "AGENTS.override.md"
                if scope == "user"
                else target / "AGENTS.override.md"
            )
            if override.exists() or override.is_symlink():
                reject_symlink_components(target, override)
                if read_existing_instruction(override).strip():
                    destination = override
        adapters.append((host, source, destination))
    return skill_destinations, adapters


def validate_target(target: Path, scope: str) -> Path:
    expanded = target.expanduser()
    if ".." in expanded.parts:
        raise InstallError("Target path may not contain '..' components")
    unresolved = expanded if expanded.is_absolute() else Path.cwd() / expanded
    root = Path(unresolved.anchor)
    for component in [*reversed(unresolved.parents), unresolved]:
        if component == root:
            continue
        if component.is_symlink():
            # macOS exposes privileged root aliases such as /var -> /private/var.
            # Deeper aliases can be controlled by a project or user and fail closed.
            if component.parent == root:
                continue
            raise InstallError(f"Target path contains a symlink component: {component}")
    try:
        resolved = unresolved.resolve(strict=True)
    except OSError as exc:
        raise InstallError(f"Installation target cannot be resolved: {unresolved}: {exc}") from exc
    if resolved == Path("/"):
        raise InstallError("Refusing to use filesystem root as installation target")
    if scope == "project":
        if not resolved.is_dir():
            raise InstallError(f"Project target must already exist: {resolved}")
        if not (resolved / ".git").exists():
            raise InstallError("Project scope requires a target containing .git")
    elif not resolved.is_dir():
        raise InstallError(f"User-scope base must be an existing directory: {resolved}")
    return resolved


def reject_symlink_components(target: Path, destination: Path) -> None:
    try:
        relative = destination.relative_to(target)
    except ValueError as exc:
        raise InstallError(f"Destination escapes target root: {destination}") from exc
    current = target
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise InstallError(f"Refusing destination with symlink component: {current}")


def validate_destination_path(
    target: Path,
    destination: Path,
    *,
    existing_file_ok: bool,
    existing_directory_ok: bool = False,
) -> None:
    reject_symlink_components(target, destination)
    try:
        relative = destination.relative_to(target)
    except ValueError as exc:
        raise InstallError(f"Destination escapes target root: {destination}") from exc
    current = target
    for part in relative.parts[:-1]:
        current = current / part
        if current.exists() and not current.is_dir():
            raise InstallError(f"Destination parent is not a directory: {current}")
    if destination.exists():
        if existing_file_ok and destination.is_file():
            return
        if existing_directory_ok and destination.is_dir():
            return
        if existing_file_ok:
            raise InstallError(f"Instruction destination is not a regular file: {destination}")
        if existing_directory_ok:
            raise InstallError(f"Skill destination is not a directory: {destination}")
        else:
            raise InstallError(
                "Refusing to replace an installed skill; remove or upgrade it deliberately: "
                f"{destination}"
            )


def make_parent(path: Path, created_directories: list[Path]) -> None:
    missing: list[Path] = []
    current = path
    while not current.exists():
        missing.append(current)
        current = current.parent
    if not current.is_dir():
        raise InstallError(f"Destination parent is not a directory: {current}")
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise InstallError(f"Cannot create destination directory {path}: {exc}") from exc
    created_directories.extend(reversed(missing))


def unique_backup_path(destination: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = destination.with_name(f"{destination.name}.bak.{stamp}")
    candidate = base
    suffix = 1
    while candidate.exists() or candidate.is_symlink():
        candidate = destination.with_name(f"{base.name}.{suffix}")
        suffix += 1
    return candidate


def skill_manifest(root: Path) -> tuple[tuple[str, str, int, str], ...]:
    if root.is_symlink() or not root.is_dir():
        raise InstallError(f"Skill tree must be a regular non-symlink directory: {root}")
    records: list[tuple[str, str, int, str]] = []
    total_bytes = 0
    try:
        candidates = sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
        for path in candidates:
            relative = path.relative_to(root)
            if any(part in IGNORED_SKILL_NAMES for part in relative.parts) or path.suffix == ".pyc":
                continue
            if len(records) >= MAX_SKILL_ENTRIES:
                raise InstallError(f"Skill tree exceeds {MAX_SKILL_ENTRIES} entries: {root}")
            if path.is_symlink():
                raise InstallError(f"Skill tree may not contain symlinks: {path}")
            if path.is_dir():
                records.append((relative.as_posix(), "directory", 0, ""))
                continue
            if not path.is_file():
                raise InstallError(f"Skill tree contains an unsupported file type: {path}")
            size = path.stat().st_size
            total_bytes += size
            if total_bytes > MAX_SKILL_BYTES:
                raise InstallError(f"Skill tree exceeds {MAX_SKILL_BYTES} bytes: {root}")
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            records.append((relative.as_posix(), "file", size, digest.hexdigest()))
    except InstallError:
        raise
    except OSError as exc:
        raise InstallError(f"Cannot inspect Skill tree {root}: {exc}") from exc
    return tuple(records)


def print_plan(target: Path, hosts: list[str], scope: str, append_adapter: bool) -> None:
    skill_destinations, adapters = resolve_actions(target, hosts, scope)
    _safe_print(f"Target: {target}")
    _safe_print("Skill copies:")
    for destination, owners in skill_destinations.items():
        state = "EXISTS (apply will verify and reuse only if identical)" if destination.exists() else "new"
        _safe_print(f"  {destination}  [{', '.join(owners)}; {state}]")
    _safe_print("Host adapters:")
    adapter_by_destination: dict[Path, tuple[str, str]] = {}
    for host, source, destination in adapters:
        block = adapter_block(source)
        prior = adapter_by_destination.get(destination)
        if prior:
            prior_host, prior_block = prior
            if prior_block != block:
                raise InstallError(
                    f"Hosts '{prior_host}' and '{host}' target {destination} with different adapters; "
                    "select one of those hosts"
                )
            _safe_print(f"  {host:<8} {destination}  [shared with {prior_host}; no duplicate write]")
            continue
        adapter_by_destination[destination] = (host, block)
        validate_destination_path(target, destination, existing_file_ok=True)
        if destination.exists():
            existing = read_existing_instruction(destination)
            installed_block = extract_marker_block(existing, destination)
            if installed_block is not None and installed_block.strip() == block.strip():
                state = "already installed"
            elif installed_block is not None:
                state = "marker content differs; manual reconciliation required"
            elif append_adapter:
                state = "append with backup"
            else:
                state = "existing file preserved; merge remains pending"
        else:
            state = "new"
        _safe_print(f"  {host:<8} {destination}  [{state}]")


def apply_install(target: Path, hosts: list[str], scope: str, append_adapter: bool) -> int:
    skill_destinations, adapters = resolve_actions(target, hosts, scope)
    if SKILL_SOURCE.is_symlink() or not SKILL_SOURCE.is_dir():
        raise InstallError(f"Skill source missing: {SKILL_SOURCE}")
    source_symlinks = [path for path in SKILL_SOURCE.rglob("*") if path.is_symlink()]
    if source_symlinks:
        raise InstallError("Skill source may not contain symlinks: " + ", ".join(str(item) for item in source_symlinks))
    source_manifest = skill_manifest(SKILL_SOURCE)
    adapter_plans: list[dict[str, object]] = []
    adapter_by_destination: dict[Path, tuple[str, str]] = {}
    for host, source, destination in adapters:
        block = adapter_block(source)
        prior = adapter_by_destination.get(destination)
        if prior:
            prior_host, prior_block = prior
            if prior_block != block:
                raise InstallError(
                    f"Hosts '{prior_host}' and '{host}' target {destination} with different adapters; "
                    "select one of those hosts"
                )
            continue
        adapter_by_destination[destination] = (host, block)
        validate_destination_path(target, destination, existing_file_ok=True)
        existing: str | None = None
        existing_mode: int | None = None
        if destination.exists():
            existing = read_existing_instruction(destination)
            try:
                existing_mode = stat.S_IMODE(destination.stat().st_mode)
            except OSError as exc:
                raise InstallError(f"Cannot inspect instruction permissions {destination}: {exc}") from exc
            installed_block = extract_marker_block(existing, destination)
            if installed_block is not None and installed_block.strip() == block.strip():
                action = "present"
            elif installed_block is not None:
                if append_adapter:
                    raise InstallError(
                        f"Existing agentic-reporting marker differs from the selected adapter; "
                        f"reconcile it manually before appending: {destination}"
                    )
                action = "conflict"
            elif append_adapter:
                action = "append"
            else:
                action = "pending"
        else:
            action = "new"
        adapter_plans.append(
            {
                "host": host,
                "destination": destination,
                "block": block,
                "existing": existing,
                "existing_mode": existing_mode,
                "action": action,
            }
        )

    skills_to_copy: list[Path] = []
    reusable_skills: list[Path] = []
    for destination in skill_destinations:
        validate_destination_path(
            target,
            destination,
            existing_file_ok=False,
            existing_directory_ok=True,
        )
        if destination.exists():
            if skill_manifest(destination) != source_manifest:
                raise InstallError(
                    "Refusing to reuse a different installed skill; compare or upgrade it deliberately: "
                    f"{destination}"
                )
            reusable_skills.append(destination)
        else:
            skills_to_copy.append(destination)

    created_skills: list[Path] = []
    created_adapters: list[Path] = []
    replaced_adapters: list[tuple[Path, str, int]] = []
    created_backups: list[Path] = []
    created_directories: list[Path] = []
    messages: list[str] = []
    pending = 0

    def rollback() -> list[str]:
        cleanup_errors: list[str] = []
        for destination, original, original_mode in reversed(replaced_adapters):
            try:
                safe_text_write(destination, original, original_mode)
            except Exception as exc:  # retain every cleanup failure for the caller
                cleanup_errors.append(f"restore {destination}: {exc}")
        for destination in reversed(created_adapters):
            try:
                destination.unlink(missing_ok=True)
            except OSError as exc:
                cleanup_errors.append(f"remove {destination}: {exc}")
        for backup in reversed(created_backups):
            try:
                backup.unlink(missing_ok=True)
            except OSError as exc:
                cleanup_errors.append(f"remove {backup}: {exc}")
        for destination in reversed(created_skills):
            try:
                if destination.exists():
                    shutil.rmtree(destination)
            except OSError as exc:
                cleanup_errors.append(f"remove {destination}: {exc}")
        for directory in reversed(created_directories):
            try:
                directory.rmdir()
            except OSError:
                pass
        return cleanup_errors

    try:
        for destination in reusable_skills:
            messages.append(f"Reused identical installed skill: {destination}")
        for destination in skills_to_copy:
            make_parent(destination.parent, created_directories)
            created_skills.append(destination)
            shutil.copytree(
                SKILL_SOURCE,
                destination,
                symlinks=False,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
            )
            messages.append(f"Installed skill: {destination}")

        new_mode = 0o644 if scope == "project" else 0o600
        for plan in adapter_plans:
            host = str(plan["host"])
            destination = plan["destination"]
            if not isinstance(destination, Path):
                raise InstallError("Internal adapter destination type error")
            action = str(plan["action"])
            block = str(plan["block"])
            if action == "present":
                messages.append(f"Adapter already present: {destination}")
            elif action == "pending":
                pending += 1
                messages.append(f"Adapter merge pending ({host}); existing file preserved: {destination}")
            elif action == "conflict":
                pending += 1
                messages.append(
                    f"Adapter reconciliation pending ({host}); marker content differs and was preserved: {destination}"
                )
            elif action == "append":
                existing = plan["existing"]
                existing_mode = plan["existing_mode"]
                if not isinstance(existing, str) or not isinstance(existing_mode, int):
                    raise InstallError("Internal adapter append state error")
                backup = unique_backup_path(destination)
                shutil.copy2(destination, backup, follow_symlinks=False)
                created_backups.append(backup)
                replaced_adapters.append((destination, existing, existing_mode))
                safe_text_write(destination, existing.rstrip() + "\n\n" + block, existing_mode)
                messages.append(f"Appended adapter: {destination} (backup: {backup})")
            elif action == "new":
                make_parent(destination.parent, created_directories)
                safe_text_write(destination, block, new_mode)
                created_adapters.append(destination)
                messages.append(f"Installed adapter: {destination}")
            else:
                raise InstallError(f"Internal adapter action error: {action}")
    except Exception as exc:
        cleanup_errors = rollback()
        detail = f"; rollback issues: {'; '.join(cleanup_errors)}" if cleanup_errors else ""
        if isinstance(exc, InstallError):
            raise InstallError(f"{exc}{detail}") from exc
        raise InstallError(f"Installation failed: {exc}{detail}") from exc

    for message in messages:
        _safe_print(message)
    if pending:
        _safe_print(f"Installation copied the skill, but {pending} existing host instruction file(s) still need manual adapter merge.")
        return 3
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "apply"))
    parser.add_argument("--target", required=True, help="Existing project root or explicit user-scope base directory")
    parser.add_argument("--scope", choices=("project", "user"), default="project")
    parser.add_argument("--host", action="append", choices=tuple(HOSTS), required=True)
    parser.add_argument(
        "--append-adapter",
        action="store_true",
        help="Explicitly append a marked adapter to existing instruction files after backing them up",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        target = validate_target(Path(args.target), args.scope)
        hosts = list(dict.fromkeys(args.host))
        if args.command == "plan":
            print_plan(target, hosts, args.scope, args.append_adapter)
            return 0
        return apply_install(target, hosts, args.scope, args.append_adapter)
    except InstallError as exc:
        _safe_print(f"install: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
