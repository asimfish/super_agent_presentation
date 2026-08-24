#!/usr/bin/env python3
"""Typed, side-effect-free host command builders for presentation studies.

This module never launches a process.  The study controller owns authorization,
filesystem receipts, subprocess limits, and evidence persistence.  Adapters only
turn validated fields into a fixed argument vector and interpret bounded event
streams produced by that host.
"""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol


MAX_EVENT_LINES = 100_000
MAX_JSON_NUMBER_CHARS = 128
MAX_EVENT_DEPTH = 100
MAX_EVENT_VALUES = 10_000


class HostAdapterError(ValueError):
    """Raised when a host command or transcript violates the adapter contract."""


@dataclass(frozen=True)
class HostCommand:
    """A shell-free command plus the adapter capabilities relevant to a study."""

    argv: tuple[str, ...]
    output_token_cap_enforced: bool
    transcript_format: str


@dataclass(frozen=True)
class HostTelemetry:
    """Conservative observations derived from one host event stream."""

    input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    skill_read: bool
    checkpoint_created: bool
    checkpoint_reloaded: bool
    checkpoint_audit_passed: bool
    final_audit_passed: bool
    checkpoint_receipt_verified: bool
    event_count: int


class HostAdapter(Protocol):
    """Narrow protocol implemented by every executable study host."""

    host_id: str

    def build_command(
        self,
        *,
        executable: Path,
        workspace: Path,
        response_path: Path,
        model: str,
        max_output_tokens: int,
    ) -> HostCommand:
        """Return a fixed argument vector without performing I/O."""

    def parse_transcript(self, lines: Iterable[str]) -> HostTelemetry:
        """Extract conservative telemetry from a bounded host event stream."""


def _bounded_nonnegative_integer(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if value < 0 or value > 10**12:
        return None
    return value


def _completed_command(event: dict[str, Any]) -> tuple[list[str], int] | None:
    """Return one successful/failed completed command as safely tokenized argv."""

    if event.get("type") != "item.completed":
        return None
    item = event.get("item")
    if not isinstance(item, dict) or item.get("type") != "command_execution":
        return None
    command = item.get("command")
    exit_code = item.get("exit_code")
    if not isinstance(command, str) or isinstance(exit_code, bool) or not isinstance(exit_code, int):
        return None
    try:
        argv = shlex.split(command, posix=True)
        if (
            len(argv) == 3
            and argv[0] in {
                "bash", "sh", "zsh", "/bin/bash", "/bin/sh", "/bin/zsh"
            }
            and argv[1] in {"-c", "-lc"}
        ):
            argv = shlex.split(argv[2], posix=True)
    except ValueError:
        return None
    if not argv or any(token in {";", "&&", "||", "|", ">", ">>", "<", "<<"} for token in argv):
        return None
    return argv, exit_code


def _is_skill_read(argv: list[str]) -> bool:
    def is_skill_path(token: str) -> bool:
        return token == ".agents/skills/agentic-reporting/SKILL.md"

    executable = argv[0]
    if executable == "cat":
        return (len(argv) == 2 and is_skill_path(argv[1])) or (
            len(argv) == 3 and argv[1] == "--" and is_skill_path(argv[2])
        )
    if executable in {"head", "tail"}:
        return (
            len(argv) == 4
            and argv[1] == "-n"
            and argv[2].isdigit()
            and is_skill_path(argv[3])
        ) or (
            len(argv) == 3
            and re.fullmatch(r"-[0-9]+", argv[1]) is not None
            and is_skill_path(argv[2])
        )
    if executable == "sed":
        return (
            len(argv) == 4
            and argv[1] == "-n"
            and re.fullmatch(r"[0-9]+(?:,[0-9]+)?p", argv[2]) is not None
            and is_skill_path(argv[3])
        )
    return False


def _reportctl_invocation(argv: list[str]) -> tuple[str, list[str]] | None:
    if not argv:
        return None
    executable = argv[0]
    if executable in {"python", "python3"} and len(argv) >= 3:
        script = argv[1]
        if script != ".agents/skills/agentic-reporting/scripts/reportctl.py":
            return None
        return argv[2], argv[3:]
    script = argv[0]
    if script == ".agents/skills/agentic-reporting/scripts/reportctl.py" and len(argv) >= 2:
        return argv[1], argv[2:]
    return None


def _parse_known_options(
    arguments: list[str],
    *,
    value_options: set[str],
    flag_options: set[str] = frozenset(),
    repeatable: set[str] = frozenset(),
) -> dict[str, list[str]] | None:
    """Parse one allowlisted option grammar; reject help, unknowns and positionals."""

    parsed: dict[str, list[str]] = {}
    index = 0
    while index < len(arguments):
        option = arguments[index]
        if option in flag_options:
            if option in parsed:
                return None
            parsed[option] = []
            index += 1
            continue
        if option not in value_options or index + 1 >= len(arguments):
            return None
        value = arguments[index + 1]
        if value.startswith("-") or (option in parsed and option not in repeatable):
            return None
        parsed.setdefault(option, []).append(value)
        index += 2
    return parsed


def _parse_event(line: str, index: int) -> dict[str, Any]:
    def bounded_int(value: str) -> int:
        if len(value) > MAX_JSON_NUMBER_CHARS:
            raise ValueError(f"integer literal exceeds {MAX_JSON_NUMBER_CHARS} characters")
        return int(value)

    def bounded_float(value: str) -> float:
        if len(value) > MAX_JSON_NUMBER_CHARS:
            raise ValueError(f"floating-point literal exceeds {MAX_JSON_NUMBER_CHARS} characters")
        return float(value)

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-standard numeric constant {value}")

    try:
        parsed = json.loads(
            line,
            parse_constant=reject_constant,
            parse_float=bounded_float,
            parse_int=bounded_int,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise HostAdapterError(f"Codex transcript line {index} is not bounded JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise HostAdapterError(f"Codex transcript line {index} must be a JSON object")
    stack: list[tuple[Any, int]] = [(parsed, 1)]
    count = 0
    while stack:
        value, depth = stack.pop()
        count += 1
        if count > MAX_EVENT_VALUES:
            raise HostAdapterError(
                f"Codex transcript line {index} exceeds {MAX_EVENT_VALUES} JSON values"
            )
        if depth > MAX_EVENT_DEPTH:
            raise HostAdapterError(
                f"Codex transcript line {index} exceeds JSON depth {MAX_EVENT_DEPTH}"
            )
        if isinstance(value, dict):
            stack.extend((nested, depth + 1) for nested in value.values())
        elif isinstance(value, list):
            stack.extend((nested, depth + 1) for nested in value)
    return parsed


class CodexAdapter:
    """Adapter for OpenAI Codex CLI's documented non-interactive JSONL mode."""

    host_id = "codex"

    def build_command(
        self,
        *,
        executable: Path,
        workspace: Path,
        response_path: Path,
        model: str,
        max_output_tokens: int,
    ) -> HostCommand:
        # Codex currently has no documented exec flag that hard-caps output tokens.
        # Keep the preregistered value in the study receipt and prompt, but do not
        # pretend that it is enforced by this adapter.
        del max_output_tokens
        return HostCommand(
            argv=(
                str(executable),
                "exec",
                "-C",
                str(workspace),
                "--sandbox",
                "workspace-write",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--json",
                "--color",
                "never",
                "--model",
                model,
                "--output-last-message",
                str(response_path),
                "-",
            ),
            output_token_cap_enforced=False,
            transcript_format="codex-jsonl-v1",
        )

    def parse_transcript(self, lines: Iterable[str]) -> HostTelemetry:
        events: list[dict[str, Any]] = []
        completed_commands: list[tuple[list[str], int]] = []
        for index, line in enumerate(lines, start=1):
            if index > MAX_EVENT_LINES:
                raise HostAdapterError(f"Codex transcript exceeds {MAX_EVENT_LINES} events")
            if not line.strip():
                continue
            value = _parse_event(line, index)
            events.append(value)
            command = _completed_command(value)
            if command is not None:
                completed_commands.append(command)

        if not events:
            raise HostAdapterError("Codex transcript contains no events")
        completed = [
            event for event in events
            if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict)
        ]
        usage = completed[-1]["usage"] if completed else {}
        successful = [argv for argv, exit_code in completed_commands if exit_code == 0]
        skill_read = any(_is_skill_read(argv) for argv in successful)
        created_paths: set[str] = set()
        reloaded_paths: set[str] = set()
        audited_paths: set[str] = set()
        mode_audit_passed = False
        for argv in successful:
            invocation = _reportctl_invocation(argv)
            if invocation is None:
                continue
            subcommand, arguments = invocation
            if subcommand == "checkpoint":
                parsed = _parse_known_options(
                    arguments,
                    value_options={
                        "--task", "--checkpoint", "--mode", "--surface",
                        "--audience", "--module", "--must-show", "--output",
                    },
                    flag_options={"--force"},
                    repeatable={"--module", "--must-show"},
                )
                if parsed is not None and len(parsed.get("--output", [])) == 1:
                    created_paths.add(parsed["--output"][0])
            elif subcommand == "bundle":
                parsed = _parse_known_options(
                    arguments,
                    value_options={
                        "--task", "--checkpoint", "--mode", "--surface",
                        "--audience", "--module", "--must-show", "--max-chars",
                    },
                    repeatable={"--module", "--must-show"},
                )
                if parsed is not None and len(parsed.get("--checkpoint", [])) == 1:
                    reloaded_paths.add(parsed["--checkpoint"][0])
            elif subcommand == "audit":
                parsed = _parse_known_options(
                    arguments,
                    value_options={"--file", "--mode", "--checkpoint"},
                    flag_options={"--json", "--strict"},
                )
                if (
                    parsed is not None
                    and "--strict" in parsed
                    and len(parsed.get("--file", [])) == 1
                ):
                    checkpoint_values = parsed.get("--checkpoint", [])
                    mode_values = parsed.get("--mode", [])
                    if len(checkpoint_values) == 1 and not mode_values:
                        audited_paths.add(checkpoint_values[0])
                    elif len(mode_values) == 1 and not checkpoint_values:
                        mode_audit_passed = True
        created_and_reloaded = created_paths & reloaded_paths
        complete_checkpoint_paths = created_and_reloaded & audited_paths
        checkpoint_created = bool(created_paths)
        checkpoint_reloaded = bool(created_and_reloaded)
        checkpoint_audit_passed = bool(complete_checkpoint_paths)
        # A checkpoint-based final audit is only credible when the same checkpoint
        # was created and reloaded successfully.  A mode-only audit is intentionally
        # independent because short tasks do not create a checkpoint.
        final_audit_passed = checkpoint_audit_passed or mode_audit_passed
        return HostTelemetry(
            input_tokens=_bounded_nonnegative_integer(usage.get("input_tokens")),
            cached_input_tokens=_bounded_nonnegative_integer(usage.get("cached_input_tokens")),
            output_tokens=_bounded_nonnegative_integer(usage.get("output_tokens")),
            skill_read=skill_read,
            checkpoint_created=checkpoint_created,
            checkpoint_reloaded=checkpoint_reloaded,
            checkpoint_audit_passed=checkpoint_audit_passed,
            final_audit_passed=final_audit_passed,
            # Transcript commands are observations, not a controller-side receipt
            # proving that the persisted checkpoint/report bytes were the audited
            # artifacts. No current adapter implements that stronger binding.
            checkpoint_receipt_verified=False,
            event_count=len(events),
        )


ADAPTERS: dict[str, HostAdapter] = {"codex": CodexAdapter()}


def get_adapter(host: str) -> HostAdapter:
    try:
        return ADAPTERS[host]
    except KeyError as exc:
        raise HostAdapterError(f"No executable study adapter is registered for host: {host}") from exc
