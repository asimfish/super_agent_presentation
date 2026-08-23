#!/usr/bin/env python3
"""Route, checkpoint, scaffold, render, and structurally audit agent reports.

The tool is intentionally standard-library-only. It never evaluates report content,
fetches remote resources, or treats a successful lint as evidence that claims are true.
"""

from __future__ import annotations

import argparse
from bisect import bisect_right
import hashlib
import html
import json
import math
import os
import re
import shutil
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote, unquote, urlsplit


SKILL_DIR = Path(__file__).resolve().parent.parent
REFERENCE_DIR = SKILL_DIR / "references"
CATALOG_PATH = REFERENCE_DIR / "protocols.json"
CORE_PATH = REFERENCE_DIR / "core-contract.md"
REPO_ROOT = SKILL_DIR.parent.parent

MODE_IDS = (
    "concise-answer",
    "implementation-handoff",
    "status-update",
    "investigation-report",
    "experiment-report",
    "decision-brief",
    "academic-synthesis",
    "review-report",
    "incident-update",
    "postmortem",
    "risk-report",
)
MODULE_IDS = ("visuals", "tables", "conclusions", "evidence", "academic-display")
SURFACES = ("chat", "markdown", "issue-pr", "document", "slide")
STATUS_VALUES = ("informational", "completed", "partial", "blocked", "failed")
CLAIM_KINDS = ("verified", "inference", "recommendation")
CONFIDENCE_VALUES = ("high", "medium", "low", "unknown")
METRIC_DIRECTIONS = (
    "higher-is-better",
    "lower-is-better",
    "target-is-better",
    "descriptive",
    "not-applicable",
)
ACTION_STATUS_VALUES = ("proposed", "accepted", "in-progress", "blocked", "completed", "deferred")
CLAIM_EVIDENCE_REQUIRED_MODES = tuple(mode for mode in MODE_IDS if mode != "concise-answer")
ACTION_REQUIRED_MODES = ("incident-update", "postmortem", "risk-report")
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_REPORT_BYTES = 4 * 1024 * 1024
MAX_TASK_CHARS = 20_000
MAX_JSON_DEPTH = 100
MAX_JSON_NODES = 100_000
MAX_JSON_NUMBER_MAGNITUDE = 1.7976931348623157e308
MAX_MARKDOWN_IMAGE_ALT_CHARS = 2_048
MAX_MARKDOWN_IMAGE_TARGET_CHARS = 4_096
MAX_AUDIT_IMAGES = 1_000
MAX_AUDIT_FINDINGS = 500
MAX_AUDIT_LINES = 100_000
DIST_MANIFEST_NAME = ".agentic-reporting-dist.json"
RENDERABLE_IMAGE_SUFFIXES = frozenset({".avif", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"})
COMMONMARK_ENTITY_PATTERN = re.compile(
    r"&(?:#[Xx][0-9A-Fa-f]{1,6}|#[0-9]{1,7}|[A-Za-z][A-Za-z0-9]{1,31});"
)

STRICT_HTTP_HOST_PATTERN = (
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*"
)
STRICT_HTTP_PORT_PATTERN = (
    r"(?:[0-9]{1,4}|[0-5][0-9]{4}|6[0-4][0-9]{3}|"
    r"65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])"
)
STRICT_HTTP_AUTHORITY_PATTERN = rf"{STRICT_HTTP_HOST_PATTERN}(?::{STRICT_HTTP_PORT_PATTERN})?"

SEMANTIC_TERMS: dict[str, tuple[str, ...]] = {
    "outcome": ("outcome", "result", "answer", "headline", "结果", "答案", "结论"),
    "current_status": ("status", "current", "completed", "partial", "blocked", "状态", "进展", "完成", "阻塞"),
    "evidence": ("evidence", "verified", "observed", "source", "证据", "验证", "观察", "来源"),
    "verification": ("verification", "test", "check", "validated", "验证", "测试", "检查"),
    "changes": ("changed", "implemented", "files", "artifact", "修改", "实现", "文件", "产物"),
    "boundary": ("limitation", "uncertainty", "boundary", "caveat", "risk", "限制", "不确定", "边界", "风险"),
    "next_action": ("next", "action", "decision", "follow-up", "下一步", "行动", "决策", "后续"),
    "question": ("question", "objective", "hypothesis", "问题", "目标", "假设"),
    "method": ("method", "approach", "protocol", "setup", "方法", "方案", "协议", "设置"),
    "metrics": ("metric", "unit", "baseline", "denominator", "指标", "单位", "基线", "分母"),
    "uncertainty": ("uncertainty", "run", "trial", "seed", "confidence interval", "std", "sem", "不确定", "运行", "种子", "置信区间", "标准差", "标准误"),
    "impact": ("impact", "affected", "user", "影响", "受影响", "用户"),
    "timeline": ("timeline", "detected", "mitigated", "recovered", "时间线", "检测", "缓解", "恢复"),
    "cause": ("cause", "root", "contributing", "原因", "根因", "促成"),
    "options": ("option", "alternative", "trade-off", "选项", "备选", "权衡"),
    "decision": ("decision", "recommend", "rationale", "决定", "建议", "理由"),
    "paper_identity": ("title", "author", "venue", "doi", "paper", "标题", "作者", "会议", "论文"),
    "limitations": ("limitation", "failure", "not evaluate", "局限", "失败", "未评估"),
    "findings": ("finding", "severity", "issue", "发现", "严重", "问题"),
    "risk": ("risk", "probability", "likelihood", "residual", "风险", "概率", "可能性", "残余"),
}

CLAIM_ROLES = tuple(SEMANTIC_TERMS)

MODULE_NEGATION_TERMS: dict[str, tuple[str, ...]] = {
    "visuals": ("figure", "figures", "image", "images", "chart", "charts", "plot", "plots", "diagram", "diagrams", "screenshot", "screenshots", "visual", "visuals", "图片", "图表", "曲线图", "截图", "流程图", "可视化"),
    "tables": ("table", "tables", "matrix", "matrices", "表格", "数据表", "对比表", "矩阵"),
    "conclusions": ("conclusion section", "recommendation section", "结论部分", "建议部分"),
    "academic-display": ("paper card", "claim-evidence map", "论文卡片", "主张证据图"),
}


class ReportCtlError(RuntimeError):
    """Actionable user-facing error."""


TERMINAL_FORMAT_CONTROLS = frozenset(
    {
        0x061C,  # Arabic letter mark
        0x200E,  # left-to-right mark
        0x200F,  # right-to-left mark
        *range(0x202A, 0x202F),  # bidi embeddings/overrides and pop
        *range(0x2066, 0x206A),  # bidi isolates and pop
        0x2028,  # line separator
        0x2029,  # paragraph separator
    }
)
PORTABLE_MARKDOWN_WHITESPACE = frozenset(" \t\r\n")
HTML_BLOCK_TAGS = frozenset(
    {
        "address", "article", "aside", "base", "basefont", "blockquote", "body",
        "caption", "center", "col", "colgroup", "dd", "details", "dialog", "dir",
        "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form",
        "frame", "frameset", "h1", "h2", "h3", "h4", "h5", "h6", "head",
        "header", "hr", "html", "iframe", "legend", "li", "link", "main", "menu",
        "menuitem", "nav", "noframes", "ol", "optgroup", "option", "p", "param",
        "search", "section", "summary", "table", "tbody", "td", "tfoot", "th",
        "thead", "title", "tr", "track", "ul",
    }
)
HTML_RAW_UNTIL_CLOSE_TAGS = frozenset({"pre", "script", "style", "textarea"})
COMPLETE_HTML_TAG_PATTERN = (
    r"(?:"
    r"</[A-Za-z][A-Za-z0-9-]*[ \t]*>"
    r"|"
    r"<[A-Za-z][A-Za-z0-9-]*"
    r"(?:[ \t]+[A-Za-z_:][A-Za-z0-9_.:-]*"
    r"(?:[ \t]*=[ \t]*(?:[^ \t\"'=<>`]+|'[^']*'|\"[^\"]*\"))?"
    r")*[ \t]*/?>"
    r")[ \t]*"
)


def _is_unsafe_control(codepoint: int) -> bool:
    return (
        codepoint < 0x20
        or codepoint == 0x7F
        or 0x80 <= codepoint <= 0x9F
        or 0xD800 <= codepoint <= 0xDFFF
        or codepoint in TERMINAL_FORMAT_CONTROLS
    )


def _contains_unsafe_control(value: str) -> bool:
    return any(_is_unsafe_control(ord(character)) for character in value)


def _strict_http_url_error(value: str) -> str | None:
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        return "is not a well-formed HTTP(S) URL"
    if parsed.scheme.casefold() not in ("http", "https"):
        return "must use HTTP or HTTPS"
    if not hostname:
        return "must use an absolute HTTP(S) URL with a host"
    if not re.fullmatch(STRICT_HTTP_AUTHORITY_PATTERN, parsed.netloc):
        return "uses an unsupported HTTP(S) authority; use an ASCII hostname and optional port"
    if re.search(r"\s", value):
        return "must percent-encode whitespace in an HTTP(S) URL"
    return None


def _terminal_safe_text(value: Any, *, preserve_newlines: bool = False) -> str:
    """Make untrusted text visible without emitting terminal control sequences."""

    output: list[str] = []
    for character in str(value):
        codepoint = ord(character)
        if character == "\n" and preserve_newlines:
            output.append(character)
        elif codepoint < 0x20 or codepoint == 0x7F:
            escapes = {0x09: r"\t", 0x0A: r"\n", 0x0D: r"\r"}
            output.append(escapes.get(codepoint, f"\\x{codepoint:02x}"))
        elif _is_unsafe_control(codepoint):
            output.append(f"\\u{codepoint:04x}")
        else:
            output.append(character)
    return "".join(output)


def _safe_print(
    value: Any = "",
    *,
    file: Any = None,
    end: str = "\n",
    preserve_newlines: bool = False,
) -> None:
    print(
        _terminal_safe_text(value, preserve_newlines=preserve_newlines),
        file=file,
        end=end,
    )


def _safe_json_dumps(value: Any, *, indent: int = 2) -> str:
    """Serialize valid JSON while escaping terminal-spoofing code points."""

    rendered = json.dumps(value, ensure_ascii=False, indent=indent)
    output: list[str] = []
    for character in rendered:
        codepoint = ord(character)
        if (
            codepoint == 0x7F
            or 0x80 <= codepoint <= 0x9F
            or 0xD800 <= codepoint <= 0xDFFF
            or codepoint in TERMINAL_FORMAT_CONTROLS
        ):
            output.append(f"\\u{codepoint:04x}")
        else:
            output.append(character)
    return "".join(output)


class _SafeArgumentParser(argparse.ArgumentParser):
    """Prevent argparse diagnostics from replaying terminal controls."""

    def _print_message(self, message: str | None, file: Any = None) -> None:
        if message:
            super()._print_message(
                _terminal_safe_text(message, preserve_newlines=True),
                file,
            )

    def error(self, message: str) -> None:
        # `message` can contain an unrecognized user token. Sanitize it before
        # adding argparse's trusted diagnostic line structure.
        self.print_usage(sys.stderr)
        safe_message = _terminal_safe_text(message)
        self.exit(2, f"{self.prog}: error: {safe_message}\n")


def _read_text_bounded(path: Path, max_bytes: int, label: str) -> str:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ReportCtlError(f"Cannot inspect {label.lower()} {path}: {exc}") from exc
    if not path.is_file():
        raise ReportCtlError(f"{label} must be a regular file: {path}")
    if size > max_bytes:
        raise ReportCtlError(f"{label} is {size} bytes; limit is {max_bytes} bytes")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ReportCtlError(f"{label} must be UTF-8 text: {path}") from exc
    except OSError as exc:
        raise ReportCtlError(f"Cannot read {label.lower()} {path}: {exc}") from exc


def _json_structure_limit_error(value: Any) -> str | None:
    stack: list[tuple[Any, int]] = [(value, 0)]
    seen_containers: set[int] = set()
    visited = 0
    while stack:
        item, depth = stack.pop()
        visited += 1
        if visited > MAX_JSON_NODES:
            return f"JSON structure exceeds {MAX_JSON_NODES} values"
        if depth > MAX_JSON_DEPTH:
            return f"JSON nesting exceeds {MAX_JSON_DEPTH} levels"
        if isinstance(item, (dict, list)):
            identity = id(item)
            if identity in seen_containers:
                continue
            seen_containers.add(identity)
            children = item.values() if isinstance(item, dict) else item
            stack.extend((child, depth + 1) for child in children)
    return None


def _json_unicode_scalar_error(value: Any) -> str | None:
    """Reject lone UTF-16 surrogates in every JSON key and string scalar."""

    stack = [value]
    seen_containers: set[int] = set()
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            if any(0xD800 <= ord(character) <= 0xDFFF for character in item):
                return "JSON strings must contain Unicode scalar values, not lone surrogates"
        elif isinstance(item, dict):
            identity = id(item)
            if identity in seen_containers:
                continue
            seen_containers.add(identity)
            for key, child in item.items():
                if any(0xD800 <= ord(character) <= 0xDFFF for character in key):
                    return "JSON object keys must contain Unicode scalar values, not lone surrogates"
                stack.append(child)
        elif isinstance(item, list):
            identity = id(item)
            if identity in seen_containers:
                continue
            seen_containers.add(identity)
            stack.extend(item)
    return None


def _load_json(path: Path) -> Any:
    def reject_nonstandard_constant(value: str) -> None:
        raise ValueError(f"non-standard numeric constant {value}")

    try:
        data = json.loads(
            _read_text_bounded(path, MAX_JSON_BYTES, "JSON file"),
            parse_constant=reject_nonstandard_constant,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ReportCtlError(f"Invalid JSON in {path}: {exc}") from exc
    limit_error = _json_structure_limit_error(data)
    if limit_error:
        raise ReportCtlError(f"Invalid JSON in {path}: {limit_error}")
    return data


def load_catalog() -> dict[str, Any]:
    catalog = _load_json(CATALOG_PATH)
    if not isinstance(catalog, dict):
        raise ReportCtlError("protocols.json root must be an object")
    if not isinstance(catalog.get("schema_version"), int) or isinstance(catalog.get("schema_version"), bool) or catalog.get("schema_version") != 1:
        raise ReportCtlError("Unsupported protocols.json schema_version; expected 1")
    modes = catalog.get("modes")
    modules = catalog.get("modules")
    if not isinstance(modes, dict) or not isinstance(modules, dict):
        raise ReportCtlError("protocols.json must contain object-valued modes and modules")
    missing_modes = sorted(set(MODE_IDS) - set(modes))
    missing_modules = sorted(set(MODULE_IDS) - set(modules))
    if missing_modes or missing_modules:
        raise ReportCtlError(
            "protocol catalog is incomplete: "
            f"missing modes={missing_modes}, missing modules={missing_modules}"
        )
    return catalog


def _read_reference(relative: str) -> str:
    candidate = (REFERENCE_DIR / relative).resolve()
    if REFERENCE_DIR.resolve() not in candidate.parents:
        raise ReportCtlError(f"Reference escapes skill directory: {relative}")
    try:
        return candidate.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise ReportCtlError(f"Routed reference does not exist: {candidate}") from exc


def _signal_score(text: str, signals: Iterable[str]) -> int:
    lowered = text.casefold()
    score = 0
    for signal in signals:
        token = str(signal).casefold().strip()
        if token and token in lowered:
            score += max(1, min(4, len(token) // 5 + 1))
    return score


def _normalized_leading_text(text: str) -> str:
    return re.sub(
        r"^(?:\s*(?:please[, ]*|could you\s+|can you\s+|would you\s+|请你?\s*))",
        "",
        text.casefold(),
        count=1,
    ).lstrip()


def _leading_signal_score(text: str, signals: Iterable[str]) -> int:
    lowered = _normalized_leading_text(text)
    score = 0
    for signal in signals:
        token = str(signal).casefold().strip()
        if token and lowered.startswith(token):
            score += max(1, min(4, len(token) // 5 + 1))
    return score


def _leading_imperative_mode(text: str) -> str | None:
    leading = _normalized_leading_text(text)
    if re.match(r"(?:review|audit|critique)\b|(?:审查|评审|审计|点评|批评)", leading):
        return "review-report"
    return None


def infer_mode(task: str, catalog: dict[str, Any]) -> tuple[str, dict[str, int]]:
    request_focus = task
    for marker in ("\n\nSupplied facts:", "\n\nEvidence boundary:", "\n\nSupplied artifacts:"):
        if marker in request_focus:
            request_focus = request_focus.split(marker, 1)[0]
    intent_scores = {
        mode_id: _signal_score(request_focus, catalog["modes"][mode_id].get("intent_signals", []))
        for mode_id in MODE_IDS
    }
    imperative_mode = _leading_imperative_mode(request_focus)
    scores = {
        mode_id: _signal_score(task, catalog["modes"][mode_id].get("signals", []))
        + 3 * _signal_score(request_focus, catalog["modes"][mode_id].get("signals", []))
        + 100 * intent_scores[mode_id]
        + 10_000 * _leading_signal_score(
            request_focus,
            catalog["modes"][mode_id].get("intent_signals", []),
        )
        + (1_000_000 if mode_id == imperative_mode else 0)
        for mode_id in MODE_IDS
    }
    best = max(scores, key=lambda item: (scores[item], -MODE_IDS.index(item)))
    if scores[best] == 0:
        compact = re.sub(r"\s+", " ", task).strip()
        best = "concise-answer" if len(compact) <= 120 else "investigation-report"
    return best, scores


def select_modules(
    task: str,
    mode: str,
    explicit: list[str] | None,
    catalog: dict[str, Any],
) -> list[str]:
    if explicit is not None:
        unknown = sorted(set(explicit) - set(catalog["modules"]))
        if unknown:
            raise ReportCtlError(f"Unknown module(s): {', '.join(unknown)}")
        selected = list(dict.fromkeys(explicit))
    else:
        suppressed: set[str] = set()
        clauses = re.findall(
            r"\b(?:no|without|do not|don't|must not|avoid)\b[^.;\n]{0,120}",
            task.casefold(),
        )
        clauses.extend(
            re.findall(r"(?:不要|不使用|无需|请勿|避免|不能|不可)[^。；;.\n]{0,120}", task.casefold())
        )
        for clause in clauses:
            clause = re.split(r"\b(?:but|however)\b", clause, maxsplit=1)[0]
            if re.search(
                r"\b(?:(?:do not|don't|must not)\s+(?:omit|remove|exclude|hide)"
                r"|(?:without|avoid)\s+(?:omitting|removing|excluding|hiding))\b",
                clause,
            ):
                continue
            if re.search(
                r"(?:不要|请勿|不能|不可|避免)(?:再)?(?:省略|删除|移除|排除|隐藏|不使用|不展示)",
                clause,
            ):
                continue
            for module_id, terms in MODULE_NEGATION_TERMS.items():
                if any(
                    term in clause
                    if re.search(r"[^\x00-\x7f]", term)
                    else re.search(rf"\b{re.escape(term)}\b", clause) is not None
                    for term in terms
                ):
                    suppressed.add(module_id)
        scored = [
            (module_id, _signal_score(task, record.get("signals", [])))
            for module_id, record in catalog["modules"].items()
            if module_id not in suppressed
        ]
        selected = [item for item, score in sorted(scored, key=lambda row: -row[1]) if score > 0]
        selected.extend(
            item
            for item in catalog["modes"][mode].get("default_modules", [])
            if item not in suppressed
        )
        selected = list(dict.fromkeys(selected))
    if len(selected) > 2:
        selected = selected[:2]
    return selected


def _validated_task_text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReportCtlError("Task text must be a non-empty string")
    if len(value) > MAX_TASK_CHARS:
        raise ReportCtlError(
            f"Task text exceeds {MAX_TASK_CHARS} characters; checkpoint a concise reporting objective"
        )
    return value


def _validated_audience(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 500:
        raise ReportCtlError("Audience must be a non-empty string of at most 500 characters")
    return value


def _load_checkpoint(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    if not isinstance(data, dict):
        raise ReportCtlError(f"Checkpoint root must be an object: {path}")
    required = {
        "schema_version", "kind", "created_at", "task", "task_sha256", "mode",
        "surface", "audience", "modules", "must_show",
    }
    missing = sorted(required - set(data))
    unknown = sorted(set(data) - required)
    if missing:
        raise ReportCtlError(f"Checkpoint is missing required fields: {', '.join(missing)}")
    if unknown:
        raise ReportCtlError(f"Checkpoint has unknown fields: {', '.join(unknown)}")
    if (
        not isinstance(data.get("schema_version"), int)
        or isinstance(data.get("schema_version"), bool)
        or data.get("schema_version") != 1
        or data.get("kind") != "agentic-report-checkpoint"
    ):
        raise ReportCtlError(f"Not an agentic reporting checkpoint: {path}")
    if not isinstance(data.get("created_at"), str) or not data["created_at"].strip():
        raise ReportCtlError("Checkpoint created_at must be a non-empty string")
    task = _validated_task_text(data.get("task"))
    if data.get("mode") not in MODE_IDS:
        raise ReportCtlError(f"Checkpoint mode must be one of: {', '.join(MODE_IDS)}")
    if data.get("surface") not in SURFACES:
        raise ReportCtlError(f"Checkpoint surface must be one of: {', '.join(SURFACES)}")
    _validated_audience(data.get("audience"))
    modules = data.get("modules")
    if (
        not isinstance(modules, list)
        or len(modules) > 2
        or len(modules) != len(set(item for item in modules if isinstance(item, str)))
        or any(not isinstance(item, str) or item not in MODULE_IDS for item in modules)
    ):
        raise ReportCtlError("Checkpoint modules must contain at most two unique known module IDs")
    must_show = data.get("must_show")
    if (
        not isinstance(must_show, list)
        or len(must_show) > 20
        or any(not isinstance(item, str) or len(item) > 2000 for item in must_show)
    ):
        raise ReportCtlError("Checkpoint must_show must contain at most 20 strings of at most 2000 characters")
    if not isinstance(data.get("task_sha256"), str):
        raise ReportCtlError("Checkpoint task_sha256 must be a string")
    expected = hashlib.sha256(task.encode("utf-8")).hexdigest()
    if data.get("task_sha256") != expected:
        raise ReportCtlError("Checkpoint task fingerprint does not match its content")
    return data


def resolve_plan(args: argparse.Namespace, catalog: dict[str, Any]) -> dict[str, Any]:
    checkpoint = _load_checkpoint(Path(args.checkpoint)) if getattr(args, "checkpoint", None) else None
    task = checkpoint["task"] if checkpoint else getattr(args, "task", None)
    if task is None:
        raise ReportCtlError("Provide --task or --checkpoint")
    task = _validated_task_text(task)

    requested_mode = checkpoint.get("mode") if checkpoint else getattr(args, "mode", "auto")
    inferred_mode, scores = infer_mode(task, catalog)
    mode = inferred_mode if requested_mode in (None, "auto") else requested_mode
    if mode not in catalog["modes"]:
        raise ReportCtlError(f"Unknown mode: {mode}")

    surface = checkpoint.get("surface", "chat") if checkpoint else getattr(args, "surface", "chat")
    if surface not in SURFACES:
        raise ReportCtlError(f"Unknown surface: {surface}")
    audience = _validated_audience(
        checkpoint.get("audience", "user") if checkpoint else getattr(args, "audience", "user")
    )
    explicit_modules = checkpoint.get("modules") if checkpoint else getattr(args, "module", None)
    modules = select_modules(task, mode, explicit_modules, catalog)
    must_show = checkpoint.get("must_show", []) if checkpoint else getattr(args, "must_show", [])
    if not isinstance(must_show, list) or len(must_show) > 20 or any(not isinstance(item, str) or len(item) > 2000 for item in must_show):
        raise ReportCtlError("must_show must contain at most 20 strings of at most 2000 characters each")

    return {
        "schema_version": 1,
        "mode": mode,
        "mode_inferred": requested_mode in (None, "auto"),
        "surface": surface,
        "audience": audience,
        "modules": modules,
        "task": task,
        "must_show": list(must_show or []),
        "route_scores": scores,
        "mode_reference": catalog["modes"][mode]["file"],
        "module_references": [catalog["modules"][item]["file"] for item in modules],
    }


def _plan_markdown(plan: dict[str, Any], catalog: dict[str, Any]) -> str:
    module_text = ", ".join(plan["modules"]) if plan["modules"] else "none"
    required = catalog["modes"][plan["mode"]].get("required_semantics", [])
    audience = _escape_inline(plan["audience"])
    must_show = "; ".join(_escape_inline(item) for item in plan["must_show"]) if plan["must_show"] else "none specified"
    return "\n".join(
        [
            f"Primary mode: `{plan['mode']}`",
            f"Surface: `{plan['surface']}`; audience: {audience}",
            f"Display modules: {module_text}",
            f"Required semantics: {', '.join(required)}",
            f"Must show: {must_show}",
            f"Read: `references/core-contract.md`, `{plan['mode_reference']}`",
            *(f"Read: `{item}`" for item in plan["module_references"]),
        ]
    )


def command_list(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    payload = {
        "schema_version": 1,
        "modes": [
            {"id": key, "summary": catalog["modes"][key]["summary"]} for key in MODE_IDS
        ],
        "modules": [
            {"id": key, "summary": catalog["modules"][key]["summary"]} for key in MODULE_IDS
        ],
        "surfaces": list(SURFACES),
    }
    if args.json:
        print(_safe_json_dumps(payload))
    else:
        _safe_print("Primary modes:")
        for item in payload["modes"]:
            _safe_print(f"  {item['id']:<24} {item['summary']}")
        _safe_print("\nDisplay modules (select at most two):", preserve_newlines=True)
        for item in payload["modules"]:
            _safe_print(f"  {item['id']:<24} {item['summary']}")
        _safe_print("\nSurfaces: " + ", ".join(SURFACES), preserve_newlines=True)
    return 0


def command_route(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    plan = resolve_plan(args, catalog)
    if args.json:
        print(_safe_json_dumps(plan))
    else:
        _safe_print(_plan_markdown(plan, catalog), preserve_newlines=True)
    return 0


def _bundle_text(plan: dict[str, Any], catalog: dict[str, Any]) -> str:
    sections = [
        "# Routed reporting bundle",
        _plan_markdown(plan, catalog),
        "\n## Universal contract\n\n" + CORE_PATH.read_text(encoding="utf-8").strip(),
        "\n## Primary mode protocol\n\n" + _read_reference(plan["mode_reference"]),
    ]
    for module_id, relative in zip(plan["modules"], plan["module_references"]):
        sections.append(f"\n## Display module: {module_id}\n\n" + _read_reference(relative))
    return "\n\n".join(sections).strip() + "\n"


def command_bundle(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    plan = resolve_plan(args, catalog)
    output = _bundle_text(plan, catalog)
    if len(output) > args.max_chars:
        raise ReportCtlError(
            f"Bundle is {len(output)} characters, above --max-chars={args.max_chars}. "
            "Remove a module or increase the explicit bound."
        )
    _safe_print(output, end="", preserve_newlines=True)
    return 0


def _reject_symlink_chain(path: Path, label: str) -> None:
    try:
        for component in [*reversed(path.parents), path]:
            # Root-level aliases such as macOS /var -> /private/var are privileged
            # platform layout, not a project-controlled redirection.
            if component.parent != Path(component.anchor) and component.is_symlink():
                raise ReportCtlError(f"Refusing {label} with symlink component: {component}")
    except ReportCtlError:
        raise
    except (OSError, RuntimeError) as exc:
        raise ReportCtlError(f"Cannot inspect {label} path {path}: {exc}") from exc


def _resolve_checked_path(path: Path, label: str) -> Path:
    _reject_symlink_chain(path, label)
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ReportCtlError(f"Cannot resolve {label} path {path}: {exc}") from exc


def _safe_write(path: Path, text: str, force: bool = False) -> None:
    try:
        original = path.expanduser()
    except (OSError, RuntimeError) as exc:
        raise ReportCtlError(f"Cannot expand output path {path}: {exc}") from exc
    candidate = original if original.is_absolute() else Path.cwd() / original
    path = _resolve_checked_path(candidate, "output")
    if path.exists() and not force:
        raise ReportCtlError(f"Output exists; pass --force to replace it: {path}")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    except OSError as exc:
        raise ReportCtlError(f"Cannot prepare output path {path}: {exc}") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary, path)
    except Exception as exc:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise ReportCtlError(f"Cannot write output {path}: {exc}") from exc


def command_checkpoint(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    plan = resolve_plan(args, catalog)
    payload = {
        "schema_version": 1,
        "kind": "agentic-report-checkpoint",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task": plan["task"],
        "task_sha256": hashlib.sha256(plan["task"].encode("utf-8")).hexdigest(),
        "mode": plan["mode"],
        "surface": plan["surface"],
        "audience": plan["audience"],
        "modules": plan["modules"],
        "must_show": plan["must_show"],
    }
    output = Path(args.output)
    _safe_write(output, _safe_json_dumps(payload) + "\n", args.force)
    _safe_print(f"Saved reporting checkpoint: {output}")
    return 0


def command_scaffold(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    if args.mode not in catalog["modes"]:
        raise ReportCtlError(f"Unknown mode: {args.mode}")
    relative = catalog["modes"][args.mode].get("template")
    if not relative:
        raise ReportCtlError(f"Mode has no scaffold template: {args.mode}")
    path = (SKILL_DIR / relative).resolve()
    if SKILL_DIR.resolve() not in path.parents or not path.is_file():
        raise ReportCtlError(f"Invalid template path for {args.mode}: {relative}")
    _safe_print(path.read_text(encoding="utf-8"), end="", preserve_newlines=True)
    return 0


def _finding(code: str, severity: str, message: str, line: int | None = None) -> dict[str, Any]:
    finding: dict[str, Any] = {"code": code, "severity": severity, "message": message}
    if line is not None:
        finding["line"] = line
    return finding


def _line_starts(text: str) -> list[int]:
    return [0, *(match.end() for match in re.finditer("\n", text))]


def _line_number(starts: list[int], offset: int) -> int:
    return bisect_right(starts, max(0, offset))


def _table_blocks(lines: list[str]) -> list[tuple[int, list[str]]]:
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] = []
    start = 0
    for number, line in enumerate(lines, start=1):
        if line.strip().startswith("|") and line.strip().endswith("|"):
            if not current:
                start = number
            current.append(line)
        elif current:
            if len(current) >= 2:
                blocks.append((start, current))
            current = []
    if current and len(current) >= 2:
        blocks.append((start, current))
    return blocks


def _split_table_row(row: str) -> list[str]:
    content = row.strip()
    if content.startswith("|"):
        content = content[1:]
    if content.endswith("|"):
        content = content[:-1]
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for character in content:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            current.append(character)
            escaped = True
        elif character == "|":
            cells.append("".join(current))
            current = []
        else:
            current.append(character)
    cells.append("".join(current))
    return cells


def _markdown_character_is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def _markdown_range_has_unescaped(
    text: str,
    start: int,
    end: int,
    characters: str,
) -> bool:
    cursor = start
    while cursor < end:
        if text[cursor] == "\\" and cursor + 1 < end:
            cursor += 2
            continue
        if text[cursor] in characters:
            return True
        cursor += 1
    return False


def _portable_markdown_line_ranges(text: str) -> Iterable[tuple[int, int]]:
    """Yield LF, CRLF, or CR lines without treating other controls as breaks."""

    start = 0
    for ending in re.finditer(r"\r\n|[\r\n]", text):
        yield start, ending.end()
        start = ending.end()
    if start < len(text):
        yield start, len(text)


def _commonmark_blank_line(body: str) -> bool:
    return re.fullmatch(r"[ \t]*", body) is not None


def _commonmark_list_content_indent(body: str, active_indent: int = 0) -> int:
    """Return the raw-space continuation indent for a CommonMark list marker.

    The block mask only needs the container's ownership boundary, not a full
    inline parse.  Tabs are intentionally left to the conservative fallback;
    the deterministic renderer never emits tab-indented containers.
    """

    marker = re.match(r"^( *)([*+-]|[0-9]{1,9}[.)])(?:( +)(.*)|$)", body)
    if marker is None:
        return 0
    leading = len(marker.group(1))
    if leading > 3 and not (
        active_indent and leading >= active_indent and leading - active_indent <= 3
    ):
        return 0
    padding = len(marker.group(3) or "")
    # CommonMark uses one column when more than four spaces follow a marker;
    # a marker-only item also owns one continuation column.
    continuation_padding = padding if 1 <= padding <= 4 else 1
    return leading + len(marker.group(2)) + continuation_padding




def _commonmark_image_block_mask(text: str) -> bytearray:
    """Mask fenced-code and CommonMark HTML blocks for canonical image credit."""

    markdown_mask = bytearray(len(text))

    def mark(start: int, end: int) -> None:
        if end > start:
            markdown_mask[start:end] = b"\x01" * (end - start)

    block_mode: str | None = None
    block_marker = ""
    fence_character = ""
    fence_length = 0
    fence_container_indent = 0
    paragraph_open = False
    list_content_indent = 0
    list_had_blank = False
    for offset, line_end in _portable_markdown_line_ranges(text):
        line = text[offset:line_end]
        body = line.rstrip("\r\n")
        if block_mode == "fence":
            mark(offset, line_end)
            container_body = body[fence_container_indent:]
            stripped = container_body.lstrip(" ")
            indentation = len(container_body) - len(stripped)
            closer = re.fullmatch(
                re.escape(fence_character) + "{" + str(fence_length) + r",}[ \t]*",
                stripped,
            )
            if indentation <= 3 and closer:
                block_mode = None
                fence_character = ""
                fence_length = 0
                fence_container_indent = 0
            paragraph_open = False
            offset = line_end
            continue

        if block_mode is not None:
            if block_mode == "html-blank" and _commonmark_blank_line(body):
                block_mode = None
                block_marker = ""
                paragraph_open = False
            else:
                if (
                    block_mode in {"html-comment", "html-literal"}
                    or (block_mode == "html-tag" and block_marker in {"script", "style", "textarea"})
                ):
                    mark(offset, line_end)
                else:
                    mark(offset, line_end)
                if (
                    (block_mode == "html-tag" and re.search(
                        r"</(?:pre|script|style|textarea)[ \t]*>", body, flags=re.IGNORECASE
                    ))
                    or (block_mode in {"html-comment", "html-literal"} and block_marker in body)
                ):
                    block_mode = None
                    block_marker = ""
                paragraph_open = False
            offset = line_end
            continue

        body_end = offset + len(body)
        raw_content_start = offset
        while raw_content_start < body_end and text[raw_content_start] == " ":
            raw_content_start += 1
        raw_indentation = raw_content_start - offset
        line_list_indent = _commonmark_list_content_indent(body, list_content_indent)
        container_indent = 0
        if line_list_indent:
            container_indent = line_list_indent
        elif list_content_indent and raw_indentation >= list_content_indent:
            container_indent = list_content_indent
        content_start = offset + container_indent
        while content_start < body_end and text[content_start] == " ":
            content_start += 1
        indentation = content_start - offset - container_indent
        stripped = text[content_start:body_end] if indentation <= 3 else ""
        opener = re.match(r"(`{3,}|~{3,})(.*)$", stripped) if stripped else None
        if opener and (opener.group(1)[0] == "~" or "`" not in opener.group(2)):
            mark(offset, line_end)
            block_mode = "fence"
            fence_character = opener.group(1)[0]
            fence_length = len(opener.group(1))
            fence_container_indent = container_indent
            if container_indent == 0:
                list_content_indent = 0
                list_had_blank = False
            elif line_list_indent:
                list_content_indent = line_list_indent
                list_had_blank = False
            paragraph_open = False
            offset = line_end
            continue

        raw_opening = re.match(
            r"<(pre|script|style|textarea)(?:[ \t]|>|$)", stripped, flags=re.IGNORECASE
        ) if stripped else None
        block_tag = re.match(
            r"</?([A-Za-z][A-Za-z0-9-]*)(?:[ \t]|/?>)", stripped
        ) if stripped else None
        complete_tag = re.fullmatch(COMPLETE_HTML_TAG_PATTERN, stripped) if stripped else None
        html_started = False
        if raw_opening:
            tag = raw_opening.group(1).casefold()
            if tag in {"script", "style", "textarea"}:
                mark(offset, line_end)
            else:
                mark(offset, line_end)
            if not re.search(
                r"</(?:pre|script|style|textarea)[ \t]*>", stripped, flags=re.IGNORECASE
            ):
                block_mode, block_marker = "html-tag", tag
            html_started = True
        elif stripped.startswith("<!--"):
            mark(offset, line_end)
            if "-->" not in stripped:
                block_mode, block_marker = "html-comment", "-->"
            html_started = True
        elif stripped.startswith("<?"):
            mark(offset, line_end)
            if "?>" not in stripped:
                block_mode, block_marker = "html-literal", "?>"
            html_started = True
        elif stripped.startswith("<![CDATA["):
            mark(offset, line_end)
            if "]]>" not in stripped:
                block_mode, block_marker = "html-literal", "]]>"
            html_started = True
        elif re.match(r"<![A-Z]", stripped):
            mark(offset, line_end)
            if ">" not in stripped:
                block_mode, block_marker = "html-literal", ">"
            html_started = True
        elif block_tag and block_tag.group(1).casefold() in HTML_BLOCK_TAGS:
            mark(offset, line_end)
            block_mode = "html-blank"
            html_started = True
        elif complete_tag and not paragraph_open:
            mark(offset, line_end)
            block_mode = "html-blank"
            html_started = True

        if html_started:
            if list_content_indent and raw_indentation < list_content_indent:
                list_content_indent = 0
                list_had_blank = False
            paragraph_open = False
        elif _commonmark_blank_line(body):
            if list_content_indent:
                list_had_blank = True
            paragraph_open = False
        else:
            visible = body.lstrip(" ")
            visible_indent = len(body) - len(visible)
            atx_heading = visible_indent <= 3 and re.match(r"#{1,6}(?:[ \t]+|$)", visible)
            thematic_break = visible_indent <= 3 and any(
                re.fullmatch(pattern, visible)
                for pattern in (
                    r"(?:\*[ \t]*){3,}",
                    r"(?:_[ \t]*){3,}",
                    r"(?:-[ \t]*){3,}",
                )
            )
            container_marker = visible_indent <= 3 and re.match(
                r"(?:>[ \t]?|(?:[*+-]|[0-9]{1,9}[.)])[ \t]+)", visible
            )
            empty_container = visible_indent <= 3 and re.fullmatch(
                r"(?:>[ \t]?|(?:[*+-]|[0-9]{1,9}[.)])[ \t]*)",
                visible,
            )
            link_definition = visible_indent <= 3 and re.match(r"\[[^\]\n]+\]:", visible)
            indented_code = (
                not paragraph_open
                and container_indent == 0
                and (raw_indentation >= 4 or body.startswith("\t"))
            )
            # List/quote lines and setext-looking lines have container-sensitive
            # lazy-continuation semantics. Keep paragraph state conservative so a
            # type-7 tag cannot hide a later fence opener. Definite leaf blocks end
            # the paragraph.
            definition_leaf = bool(link_definition) and not paragraph_open
            paragraph_open = (
                bool(container_marker) and not bool(empty_container)
            ) or not bool(
                atx_heading
                or thematic_break
                or definition_leaf
                or indented_code
                or empty_container
            )
            if line_list_indent:
                list_content_indent = line_list_indent
                list_had_blank = False
            elif list_content_indent and raw_indentation >= list_content_indent:
                list_had_blank = False
            elif list_content_indent and (
                list_had_blank
                or atx_heading
                or thematic_break
                or definition_leaf
                or container_marker
                or indented_code
                or empty_container
            ):
                list_content_indent = 0
                list_had_blank = False
        offset = line_end

    return markdown_mask


def _skip_markdown_link_whitespace(
    text: str,
    start: int,
    literal_mask: bytearray,
) -> tuple[int, bool]:
    """Skip portable link whitespace without crossing a blank line."""

    cursor = start
    line_endings = 0
    while cursor < len(text) and text[cursor] in PORTABLE_MARKDOWN_WHITESPACE:
        if literal_mask[cursor]:
            return cursor, False
        if text[cursor] == "\r":
            line_endings += 1
            cursor += 1
            if cursor < len(text) and text[cursor] == "\n":
                cursor += 1
        elif text[cursor] == "\n":
            line_endings += 1
            cursor += 1
        else:
            cursor += 1
        if line_endings > 1:
            return cursor, False
    return cursor, True


def _is_canonical_image_position(text: str, start: int, end: int) -> bool:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end < 0:
        line_end = len(text)
    if text[line_start:start] or text[end:line_end].strip(" \t\r"):
        return False

    if line_start:
        previous_end = line_start - 1
        previous_start = text.rfind("\n", 0, previous_end) + 1
        if text[previous_start:previous_end].strip(" \t\r"):
            return False

    if line_end < len(text):
        next_start = line_end + 1
        next_end = text.find("\n", next_start)
        if next_end < 0:
            next_end = len(text)
        if text[next_start:next_end].strip(" \t\r"):
            return False
    return True


def _potential_markdown_image_starts(
    text: str,
    limit: int,
) -> list[int]:
    starts: list[int] = []
    cursor = 0
    while len(starts) < limit:
        start = text.find("![", cursor)
        if start < 0:
            break
        if not _markdown_character_is_escaped(text, start):
            starts.append(start)
        cursor = start + 2
    return starts


def _potential_raw_html_opening_tags(
    text: str,
    limit: int,
) -> list[tuple[int, int]]:
    tags: list[tuple[int, int]] = []
    pattern = r"<[A-Za-z][A-Za-z0-9-]*(?=[\t\n\f\r />])"
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        tags.append((match.start(), match.end()))
        if len(tags) >= limit:
            break
    return tags


def _first_type7_html_tag_marker(text: str) -> int | None:
    """Return the first paragraph-sensitive type-7 tag marker, if any."""

    pattern = r"<(/?)([A-Za-z][A-Za-z0-9-]*)(?=[\t\n\f\r />])"
    raw_type1_open = False
    for match in re.finditer(pattern, text):
        closing, raw_name = match.groups()
        name = raw_name.casefold()
        if raw_type1_open:
            if closing and name in HTML_RAW_UNTIL_CLOSE_TAGS:
                raw_type1_open = False
            continue
        if name in HTML_BLOCK_TAGS:
            continue
        if not closing and name in HTML_RAW_UNTIL_CLOSE_TAGS:
            raw_type1_open = True
            continue
        return match.start()
    return None


def _first_fence_like_run(text: str) -> int | None:
    """Return the first raw fence run in the conservative image-credit subset."""

    positions = [position for position in (text.find("```"), text.find("~~~")) if position >= 0]
    return min(positions) if positions else None


def _decode_commonmark_entities(value: str) -> str:
    """Decode only semicolon-terminated references recognized by CommonMark."""

    def replacement(match: re.Match[str]) -> str:
        token = match.group(0)
        if token[1] != "#":
            return html.entities.html5.get(token[1:], token)
        digits = token[2:-1]
        base = 10
        if digits[:1] in ("x", "X"):
            digits = digits[1:]
            base = 16
        codepoint = int(digits, base)
        if codepoint == 0 or 0xD800 <= codepoint <= 0xDFFF or codepoint > 0x10FFFF:
            return "\uFFFD"
        return chr(codepoint)

    return COMMONMARK_ENTITY_PATTERN.sub(replacement, value)


def _has_visible_alt_text(value: str) -> bool:
    return any(unicodedata.category(character)[0] in "LNPS" for character in value)


def _scan_markdown_images(
    text: str,
    max_images: int = MAX_AUDIT_IMAGES + 1,
) -> list[tuple[str, str, int, int, bool]]:
    """Scan potential inline images and classify the canonical audit subset.

    The bounded state machine avoids regex backtracking on malformed runs of `![`.
    It supports escaped alt characters and an optional quoted Markdown title. A
    canonical image is an independent, single-line, column-zero paragraph with
    simple alt text and a target that does not depend on renderer-specific escapes.
    Required credit also stops after raw triple-backtick/triple-tilde syntax or a
    paragraph-sensitive type-7 HTML tag marker; this deliberately conservative
    subset avoids claiming full CommonMark parser equivalence.
    Every remaining unescaped Markdown marker and raw HTML opening tag is retained
    as a noncanonical candidate for fail-closed audit and forbidden-image checks.
    Rejecting all raw HTML closes CSS and custom-element visual sinks without
    pretending to implement an HTML/CSS renderer.
    """

    literal_mask = _commonmark_image_block_mask(text)
    potential_starts = _potential_markdown_image_starts(text, max_images)
    raw_html_tags = _potential_raw_html_opening_tags(text, max_images)
    first_type7_tag = _first_type7_html_tag_marker(text)
    first_fence_run = _first_fence_like_run(text)
    images: list[tuple[str, str, int, int, bool]] = []
    length = len(text)
    cursor = 0
    while cursor < length - 1:
        start = text.find("![", cursor)
        if start < 0:
            break
        if literal_mask[start] or _markdown_character_is_escaped(text, start):
            cursor = start + 2
            continue

        alt_start = start + 2
        scan = alt_start
        alt_end: int | None = None
        simple_alt = True
        while scan < length and scan - alt_start <= MAX_MARKDOWN_IMAGE_ALT_CHARS:
            if literal_mask[scan]:
                break
            if text.startswith("![", scan):
                # A newer candidate supersedes an unclosed one without rescanning.
                start = scan
                alt_start = scan + 2
                scan = alt_start
                simple_alt = True
                continue
            character = text[scan]
            if character == "\\" and scan + 1 < length:
                scan += 2
                continue
            if character == "[":
                simple_alt = False
            if character == "]":
                if scan + 1 < length and text[scan + 1] == "(":
                    alt_end = scan
                else:
                    cursor = scan + 1
                break
            scan += 1
        if alt_end is None:
            if scan >= length:
                break
            if cursor <= start:
                cursor = max(scan + 1, start + 2)
            continue

        target_start = alt_end + 2
        scan = target_start
        target_end: int | None = None
        image_end: int | None = None
        while scan < length and scan - target_start <= MAX_MARKDOWN_IMAGE_TARGET_CHARS:
            if literal_mask[scan]:
                break
            character = text[scan]
            if character == ")":
                if scan > target_start:
                    target_end = scan
                    image_end = scan + 1
                break
            if character in PORTABLE_MARKDOWN_WHITESPACE:
                if scan == target_start:
                    break
                target_end = scan
                title_cursor, portable_spacing = _skip_markdown_link_whitespace(text, scan, literal_mask)
                if not portable_spacing:
                    target_end = None
                    scan = title_cursor
                    break
                if title_cursor < length and text[title_cursor] in ("'", '"'):
                    quote_character = text[title_cursor]
                    title_cursor += 1
                    while (
                        title_cursor < length
                        and title_cursor - target_start <= MAX_MARKDOWN_IMAGE_TARGET_CHARS
                    ):
                        if literal_mask[title_cursor]:
                            break
                        if text[title_cursor] == "\\" and title_cursor + 1 < length:
                            title_cursor += 2
                            continue
                        if text[title_cursor] == quote_character:
                            title_cursor += 1
                            title_cursor, portable_spacing = _skip_markdown_link_whitespace(
                                text,
                                title_cursor,
                                literal_mask,
                            )
                            if not portable_spacing:
                                break
                            if title_cursor < length and text[title_cursor] == ")":
                                image_end = title_cursor + 1
                            break
                        title_cursor += 1
                scan = title_cursor
                break
            scan += 1

        if target_end is not None and image_end is not None:
            target = text[target_start:target_end]
            decoded_target = _decode_commonmark_entities(target)
            canonical = (
                _is_canonical_image_position(text, start, image_end)
                and (first_type7_tag is None or start < first_type7_tag)
                and (first_fence_run is None or start < first_fence_run)
                and simple_alt
                and not _markdown_range_has_unescaped(text, alt_start, alt_end, "`")
                and not any(character in text[alt_start:alt_end] for character in "<>")
                and "\n" not in text[start:image_end]
                and "\r" not in text[start:image_end]
                and not any(character in target for character in "\\()<>")
                and not any(character.isspace() for character in decoded_target)
                and not any(character in decoded_target for character in "\\()<>")
            )
            decoded_alt = _decode_commonmark_entities(text[alt_start:alt_end]).strip()
            images.append(
                (
                    decoded_alt,
                    target,
                    start,
                    image_end,
                    canonical,
                )
            )
            if len(images) >= max_images:
                break
            cursor = image_end
        else:
            cursor = max(scan + 1, target_start + 1)
    represented_starts = {item[2] for item in images}
    for start in potential_starts:
        if start not in represented_starts:
            images.append(("", "", start, min(start + 2, length), False))
    for start, end in raw_html_tags:
        if start not in represented_starts:
            images.append(("", "", start, end, False))
    images.sort(key=lambda item: item[2])
    return images[:max_images]


class _AuditFindingLimit(RuntimeError):
    def __init__(self, findings: list[dict[str, Any]]) -> None:
        super().__init__("audit finding limit reached")
        self.findings = findings


class _BoundedFindings(list[dict[str, Any]]):
    def append(self, item: dict[str, Any]) -> None:
        if len(self) >= MAX_AUDIT_FINDINGS:
            raise _AuditFindingLimit(list(self))
        super().append(item)


def _audit_markdown_impl(
    text: str,
    report_path: Path,
    mode: str,
    catalog: dict[str, Any],
) -> list[dict[str, Any]]:
    findings: _BoundedFindings = _BoundedFindings()
    if not text.strip():
        return [_finding("empty-report", "error", "Report is empty")]
    line_count = text.count("\n") + 1
    if line_count > MAX_AUDIT_LINES:
        return [
            _finding(
                "report-line-limit",
                "error",
                f"Report has {line_count} lines, above the audit limit of {MAX_AUDIT_LINES}",
            )
        ]
    text_line_starts = _line_starts(text)

    placeholder = re.compile(
        r"(?ms)(?:(?i:\b(?:TODO|TBD|XXX)\b)|<!--(?:(?!-->).){1,500}-->|"
        r"<[A-Z][A-Z0-9_. -]{1,58}>|"
        r"<(?i:(?:insert|replace|your|owner|date|path|value|result|status|summary)(?:[-_ ][a-z0-9.]+)*)>)"
    )
    for match in placeholder.finditer(text):
        if match.group(0).casefold() in {"<details>", "</details>", "<summary>", "</summary>"}:
            continue
        findings.append(
            _finding("unresolved-placeholder", "error", f"Unresolved placeholder: {match.group(0)}", _line_number(text_line_starts, match.start()))
        )

    non_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    non_code_line_starts = _line_starts(non_code)
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", non_code) if item.strip()]
    paragraph_search_start = 0
    for paragraph in paragraphs:
        plain = re.sub(r"^#{1,6}\s+", "", paragraph).strip()
        if len(plain) > 1200:
            offset = text.find(paragraph, paragraph_search_start)
            findings.append(_finding("dense-paragraph", "warning", "Paragraph exceeds 1200 characters; split only if it improves scanning", _line_number(text_line_starts, max(0, offset))))
            if offset >= 0:
                paragraph_search_start = offset + len(paragraph)

    first_plain = " ".join(re.sub(r"[#>*`\[\]()]", " ", item) for item in paragraphs[:2]).casefold()
    outcome_terms = SEMANTIC_TERMS["outcome"] + SEMANTIC_TERMS["current_status"]
    opening_terms_by_mode = {
        "academic-synthesis": ("paper", "presents", "proposes", "studies", "addresses", "论文", "提出", "研究"),
        "decision-brief": ("recommend", "decision", "choose", "建议", "决定", "选择"),
        "review-report": ("finding", "review", "no finding", "发现", "审查", "未发现"),
        "incident-update": ("impact", "incident", "outage", "影响", "事故", "中断"),
        "risk-report": ("risk", "exposure", "风险", "暴露"),
        "postmortem": ("incident", "impact", "recovered", "事故", "影响", "恢复"),
    }
    outcome_terms += opening_terms_by_mode.get(mode, ())
    if mode != "concise-answer" and not any(term.casefold() in first_plain[:700] for term in outcome_terms):
        findings.append(_finding("outcome-not-first", "warning", "The opening does not clearly expose the outcome or current status"))
    diary_terms = ("first i ", "i first ", "then i ", "首先我", "然后我", "接着我")
    if any(term in first_plain[:500] for term in diary_terms):
        findings.append(_finding("process-diary-opening", "warning", "Opening reads like a process diary; lead with the result or status"))

    heading_total = sum(1 for _ in re.finditer(r"(?m)^#{1,6}\s+", text))
    if len(text) < 1200 and heading_total > 5:
        findings.append(_finding("over-sectioned", "warning", "Short report has more than five headings"))

    scanned_images = _scan_markdown_images(text)
    if len(scanned_images) > MAX_AUDIT_IMAGES:
        findings.append(
            _finding(
                "image-scan-limit",
                "error",
                f"Report contains more than {MAX_AUDIT_IMAGES} Markdown images; remaining images were not audited",
            )
        )
        return list(findings)
    for alt, target, image_start, image_end, canonical in scanned_images:
        line = _line_number(text_line_starts, image_start)
        if not canonical:
            findings.append(
                _finding(
                    "noncanonical-image-syntax",
                    "error",
                    "Potential visual sources must use a blank-line-bounded, column-zero inline Markdown image paragraph before any raw triple-backtick/triple-tilde run or paragraph-sensitive HTML tag marker; reference images, raw HTML opening tags, containers, mixed prose, and unescaped literal image markers are noncanonical (use \\![...] or entity-encode the opening < for examples)",
                    line,
                )
            )
            continue
        if _contains_unsafe_control(alt):
            findings.append(
                _finding(
                    "invalid-image-alt",
                    "error",
                    "Image alternative text contains a control or directional-format character",
                    line,
                )
            )
        elif not _has_visible_alt_text(alt):
            findings.append(
                _finding(
                    "missing-image-alt",
                    "error",
                    "Informative Markdown image has no visible alternative text",
                    line,
                )
            )
        normalized_target = _decode_commonmark_entities(target)
        if (
            _contains_unsafe_control(target)
            or _contains_unsafe_control(normalized_target)
            or any(not character.isprintable() for character in normalized_target)
            or any(character.isspace() for character in normalized_target)
            or any(character in normalized_target for character in "\\()<>")
        ):
            findings.append(
                _finding(
                    "invalid-image-target",
                    "error",
                    f"Image target contains decoded whitespace, an unsafe delimiter, control, or directional-format character: {target}",
                    line,
                )
            )
        elif re.match(r"^https?://", normalized_target, flags=re.IGNORECASE):
            issue = _strict_http_url_error(normalized_target)
            if issue:
                findings.append(
                    _finding(
                        "invalid-image-target",
                        "error",
                        f"Image target {issue}: {target}",
                        line,
                    )
                )
        else:
            try:
                parsed_target = urlsplit(normalized_target)
                if parsed_target.scheme or parsed_target.netloc:
                    raise ValueError("unsupported image target authority or scheme")
                local_target = unquote(parsed_target.path)
                if (
                    not local_target
                    or _contains_unsafe_control(local_target)
                    or any(not character.isprintable() for character in local_target)
                ):
                    raise ValueError("empty or control-bearing local image path")
                candidate = report_path.parent / local_target
                # Python 3.13+ no longer raises from resolve(strict=False) for
                # symlink loops.  A stat probe preserves the distinction between
                # an ordinary missing image and an unresolvable local target.
                try:
                    candidate_stat = candidate.stat()
                except FileNotFoundError:
                    candidate_stat = None
                except OSError as exc:
                    raise ValueError("unresolvable local image target") from exc
                local = candidate.resolve(strict=False)
                exists = candidate_stat is not None
                if exists and (
                    not local.is_file()
                    or local.suffix.casefold() not in RENDERABLE_IMAGE_SUFFIXES
                ):
                    raise ValueError("local target is not a supported regular image file")
            except (OSError, RuntimeError, ValueError):
                findings.append(
                    _finding(
                        "invalid-image-target",
                        "error",
                        f"Image target is not a safe local path or supported remote URL: {target}",
                        line,
                    )
                )
            else:
                if not exists:
                    findings.append(_finding("missing-image-file", "error", f"Local image does not exist: {target}", line))
        nearby = text[max(0, image_start - 350) : min(len(text), image_end + 350)].casefold()
        if not any(token in nearby for token in ("figure", "fig.", "caption", "图", "说明", "takeaway", "观察")):
            findings.append(_finding("image-without-context", "warning", "Image lacks an adjacent identifier, caption, or explanatory sentence", line))

    if "```mermaid" in text:
        for block in re.findall(r"```mermaid\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE):
            if "accTitle" not in block or "accDescr" not in block:
                findings.append(_finding("mermaid-accessibility", "warning", "Mermaid diagram should include accTitle and accDescr"))

    lines = text.splitlines()
    for start, table in _table_blocks(lines):
        widths = [len(_split_table_row(row)) for row in table]
        if len(set(widths)) != 1:
            findings.append(_finding("malformed-table", "error", f"Markdown table rows have inconsistent column counts: {widths}", start))
            continue
        separator_cells = [cell.strip() for cell in _split_table_row(table[1])]
        if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator_cells):
            findings.append(
                _finding(
                    "invalid-table-separator",
                    "error",
                    "Markdown table separator cells require at least three hyphens, with optional alignment colons",
                    start + 1,
                )
            )
        if widths[0] > 10:
            findings.append(_finding("wide-table", "warning", f"Table has {widths[0]} columns; split or move detail unless exact lookup requires it", start))
        context = " ".join(lines[max(0, start - 3) : start - 1]).casefold()
        if not any(
            token in context
            for token in ("table", "表", "comparison", "比较", "results", "结果", "metrics", "指标", "actions", "行动")
        ):
            findings.append(_finding("table-without-context", "warning", "Table lacks a nearby identifying or explanatory sentence", start))

    required = catalog["modes"][mode].get("required_semantics", [])
    lowered = non_code.casefold()
    for semantic in required:
        terms = (semantic.replace("_", " "),) + SEMANTIC_TERMS.get(semantic, ())
        if not any(term.casefold() in lowered for term in terms):
            findings.append(_finding("missing-semantic", "warning", f"Could not find evidence of required semantic role: {semantic}"))

    strong_claims = re.compile(r"(?i)\b(state[- ]of[- ]the[- ]art|sota|statistically significant|proves?|guarantees?)\b|最先进|显著优于|证明了|保证")
    for match in strong_claims.finditer(non_code):
        nearby = non_code[max(0, match.start() - 250) : match.end() + 250]
        if not re.search(r"(?:\[[^\]]+\]\([^)]+\)|\[[0-9, -]+\]|\d)", nearby):
            findings.append(_finding("strong-claim-boundary", "warning", f"Strong claim may lack nearby comparison or evidence context: {match.group(0)}", _line_number(non_code_line_starts, match.start())))

    return list(findings)


def audit_markdown(text: str, report_path: Path, mode: str, catalog: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        return _audit_markdown_impl(text, report_path, mode, catalog)
    except _AuditFindingLimit as exc:
        return exc.findings + [
            _finding(
                "audit-finding-limit",
                "error",
                f"Audit stopped after {MAX_AUDIT_FINDINGS} findings; remaining content was not fully audited",
            )
        ]


def command_audit(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    if args.mode not in catalog["modes"]:
        raise ReportCtlError(f"Unknown mode: {args.mode}")
    path = Path(args.file)
    try:
        text = _read_text_bounded(path, MAX_REPORT_BYTES, "Report file")
    except ReportCtlError:
        raise
    findings = audit_markdown(text, path.resolve(), args.mode, catalog)
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    payload = {
        "schema_version": 1,
        "file": str(path),
        "mode": args.mode,
        "errors": errors,
        "warnings": warnings,
        "manual_checks_required": [
            "latest-state accuracy",
            "claim and number fidelity",
            "evidence and citation validity",
            "uncertainty and comparison boundaries",
            "visual interpretability in the final surface",
            "explicit user-format compliance",
        ],
        "findings": findings,
    }
    if args.json:
        print(_safe_json_dumps(payload))
    else:
        for item in findings:
            location = f":{item['line']}" if "line" in item else ""
            _safe_print(f"{item['severity'].upper():7} {item['code']}{location} — {item['message']}")
        _safe_print(f"Audit: {errors} error(s), {warnings} warning(s). Structural checks only; manual verification remains required.")
    return 1 if errors or (args.strict and warnings) else 0


def validate_report_spec(data: Any) -> list[str]:
    errors: list[str] = []
    limit_error = _json_structure_limit_error(data)
    if limit_error:
        return [limit_error]
    scalar_error = _json_unicode_scalar_error(data)
    if scalar_error:
        return [scalar_error]
    if not isinstance(data, dict):
        return ["root must be an object"]
    required = (
        "schema_version",
        "report_type",
        "status",
        "headline",
        "summary",
        "claims",
        "evidence",
        "metrics",
        "visuals",
        "actions",
        "artifacts",
        "limitations",
        "open_questions",
    )
    for key in required:
        if key not in data:
            errors.append(f"missing required field: {key}")
    allowed = set(required) | {"$schema", "as_of"}
    for key in sorted(set(data) - allowed):
        errors.append(f"unknown top-level field: {key}")
    if (
        not isinstance(data.get("schema_version"), (int, float))
        or isinstance(data.get("schema_version"), bool)
        or data.get("schema_version") != 1
    ):
        errors.append("schema_version must equal 1")
    if data.get("report_type") not in MODE_IDS:
        errors.append(f"report_type must be one of: {', '.join(MODE_IDS)}")
    if data.get("status") not in STATUS_VALUES:
        errors.append(f"status must be one of: {', '.join(STATUS_VALUES)}")
    for key in ("headline", "summary"):
        if key in data and (not isinstance(data[key], str) or not data[key].strip()):
            errors.append(f"{key} must be a non-empty string")
    if "$schema" in data and not isinstance(data["$schema"], str):
        errors.append("$schema must be a string when present")
    if "as_of" in data and (not isinstance(data["as_of"], str) or not data["as_of"].strip()):
        errors.append("as_of must be a non-empty string when present")

    def reject_unknown_fields(value: dict[str, Any], prefix: str, allowed_fields: Iterable[str]) -> None:
        for key in sorted(set(value) - set(allowed_fields)):
            errors.append(f"{prefix} has unknown field: {key}")

    def require_fields(value: dict[str, Any], prefix: str, required_fields: Iterable[str]) -> None:
        for key in required_fields:
            if key not in value:
                errors.append(f"{prefix} is missing required field: {key}")

    def validate_unique_string_refs(value: Any, prefix: str) -> list[str] | None:
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            errors.append(f"{prefix} must be an array of non-empty strings")
            return None
        if len(value) != len(set(value)):
            errors.append(f"{prefix} must not contain duplicates")
        return value

    def locator_error(value: Any, *, url_only: bool = False, local_only: bool = False) -> str | None:
        if not isinstance(value, str) or not value.strip():
            return "must be a non-empty string"
        if value != value.strip():
            return "must not begin or end with whitespace"
        if _contains_unsafe_control(value):
            return "contains a forbidden control or directional-format character"
        if any(not character.isprintable() for character in value):
            return "contains a nonprinting Unicode character"
        if any(character in value for character in ("<", ">")):
            return "contains a forbidden control or delimiter character"
        try:
            parsed = urlsplit(value)
            hostname = parsed.hostname
            _ = parsed.port
        except ValueError:
            return "is not a well-formed URL or local path"
        if url_only and parsed.scheme not in ("http", "https"):
            return "must use http or https"
        if local_only and parsed.scheme:
            return "must be a local path without a URI scheme"
        if not url_only and parsed.scheme not in ("", "http", "https"):
            return "uses an unsupported URI scheme"
        if parsed.scheme in ("http", "https") and not hostname:
            return "must use an absolute http(s) URL with a host"
        if parsed.scheme in ("http", "https") and not re.fullmatch(
            STRICT_HTTP_AUTHORITY_PATTERN,
            parsed.netloc,
        ):
            return "uses an unsupported http(s) authority; use an ASCII hostname and optional port"
        if parsed.scheme in ("http", "https") and re.search(r"\s", value):
            return "must percent-encode whitespace in an http(s) URL"
        if not parsed.scheme and value.startswith("//"):
            return "network-path references are not allowed"
        return None

    def contains_placeholder(value: Any) -> bool:
        stack = [value]
        seen_containers: set[int] = set()
        while stack:
            item = stack.pop()
            if isinstance(item, str):
                if re.search(r"(?i)\b(?:TODO|TBD|XXX)\b|<[^>\n]{2,60}>|\breplace with\b", item):
                    return True
            elif isinstance(item, (dict, list)):
                identity = id(item)
                if identity in seen_containers:
                    continue
                seen_containers.add(identity)
                stack.extend(item.values() if isinstance(item, dict) else item)
        return False

    if contains_placeholder(data):
        errors.append("report spec contains an unresolved placeholder")

    claims = data.get("claims")
    if not isinstance(claims, list):
        errors.append("claims must be an array")
    else:
        for index, claim in enumerate(claims):
            prefix = f"claims[{index}]"
            if not isinstance(claim, dict):
                errors.append(f"{prefix} must be an object")
                continue
            reject_unknown_fields(claim, prefix, ("text", "kind", "roles", "evidence_refs", "confidence", "boundary"))
            require_fields(claim, prefix, ("text", "kind", "roles", "evidence_refs", "confidence"))
            if not isinstance(claim.get("text"), str) or not claim.get("text", "").strip():
                errors.append(f"{prefix}.text must be a non-empty string")
            if claim.get("kind") not in CLAIM_KINDS:
                errors.append(f"{prefix}.kind must be one of: {', '.join(CLAIM_KINDS)}")
            roles = validate_unique_string_refs(claim.get("roles"), f"{prefix}.roles")
            if roles is not None:
                if not roles:
                    errors.append(f"{prefix}.roles must contain at least one semantic role")
                for role in roles:
                    if role not in CLAIM_ROLES:
                        errors.append(f"{prefix}.roles contains an unknown semantic role: {role}")
            refs = validate_unique_string_refs(claim.get("evidence_refs"), f"{prefix}.evidence_refs")
            if claim.get("kind") == "verified" and not refs:
                errors.append(f"{prefix} is verified but has no evidence_refs")
            confidence = claim.get("confidence")
            if confidence not in CONFIDENCE_VALUES:
                errors.append(f"{prefix}.confidence must be one of: {', '.join(CONFIDENCE_VALUES)}")
            if "boundary" in claim and (not isinstance(claim["boundary"], str) or not claim["boundary"].strip()):
                errors.append(f"{prefix}.boundary must be a non-empty string when present")

    evidence = data.get("evidence", [])
    evidence_ids: set[str] = set()
    if not isinstance(evidence, list):
        errors.append("evidence must be an array when present")
    else:
        for index, item in enumerate(evidence):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item.get("id"):
                errors.append(f"evidence[{index}] must be an object with a non-empty id")
                continue
            reject_unknown_fields(item, f"evidence[{index}]", ("id", "label", "locator", "verification"))
            require_fields(item, f"evidence[{index}]", ("id", "label", "locator", "verification"))
            if item["id"] in evidence_ids:
                errors.append(f"duplicate evidence id: {item['id']}")
            else:
                evidence_ids.add(item["id"])
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]*", item["id"]):
                errors.append(f"evidence[{index}].id has an invalid format")
            for key in ("label", "locator", "verification"):
                if not isinstance(item.get(key), str) or not item.get(key, "").strip():
                    errors.append(f"evidence[{index}].{key} must be a non-empty string")
            if isinstance(item.get("locator"), str):
                issue = locator_error(item["locator"])
                if issue:
                    errors.append(f"evidence[{index}].locator {issue}")
    if isinstance(claims, list):
        for index, claim in enumerate(claims):
            if isinstance(claim, dict):
                for ref in claim.get("evidence_refs", []) if isinstance(claim.get("evidence_refs"), list) else []:
                    if isinstance(ref, str) and ref not in evidence_ids:
                        errors.append(f"claims[{index}] references unknown evidence id: {ref}")

    array_fields = ("metrics", "visuals", "actions", "artifacts", "limitations", "open_questions")
    for key in array_fields:
        if key in data and not isinstance(data[key], list):
            errors.append(f"{key} must be an array when present")

    report_type = data.get("report_type")
    if report_type in CLAIM_EVIDENCE_REQUIRED_MODES:
        if not isinstance(claims, list) or not claims:
            errors.append(f"{report_type} requires at least one claim")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{report_type} requires at least one evidence item")
    if isinstance(claims, list) and report_type in MODE_IDS:
        semantic_coverage = {
            role
            for claim in claims
            if isinstance(claim, dict) and isinstance(claim.get("roles"), list)
            for role in claim["roles"]
            if isinstance(role, str)
        }
        semantic_coverage.add("outcome")
        if isinstance(evidence, list) and evidence:
            semantic_coverage.add("evidence")
        metrics_for_coverage = data.get("metrics")
        if isinstance(metrics_for_coverage, list) and metrics_for_coverage:
            semantic_coverage.add("metrics")
            if all(isinstance(item, dict) and item.get("uncertainty") for item in metrics_for_coverage):
                semantic_coverage.add("uncertainty")
        actions_for_coverage = data.get("actions")
        if isinstance(actions_for_coverage, list) and actions_for_coverage:
            semantic_coverage.add("next_action")
        limitations_for_coverage = data.get("limitations")
        if isinstance(limitations_for_coverage, list) and limitations_for_coverage:
            semantic_coverage.update(("boundary", "limitations"))
        required_semantics = load_catalog()["modes"][report_type].get("required_semantics", [])
        for semantic in required_semantics:
            if semantic not in semantic_coverage:
                errors.append(f"{report_type} requires semantic coverage: {semantic}")

    metrics = data.get("metrics", [])
    if isinstance(metrics, list):
        for index, item in enumerate(metrics):
            prefix = f"metrics[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            reject_unknown_fields(
                item,
                prefix,
                (
                    "name", "value", "unit", "direction", "denominator", "time_window",
                    "baseline", "independent_observations", "uncertainty", "evidence_refs",
                ),
            )
            require_fields(item, prefix, ("name", "value", "unit"))
            if not isinstance(item.get("name"), str) or not item.get("name", "").strip():
                errors.append(f"{prefix}.name must be a non-empty string")
            if "value" in item and not (
                item["value"] is None
                or isinstance(item["value"], str)
                or (
                    isinstance(item["value"], (int, float))
                    and not isinstance(item["value"], bool)
                    and (not isinstance(item["value"], float) or math.isfinite(item["value"]))
                    and abs(item["value"]) <= MAX_JSON_NUMBER_MAGNITUDE
                )
            ):
                errors.append(f"{prefix}.value must be a supported finite number, string, or null")
            if not isinstance(item.get("unit"), str) or not item.get("unit", "").strip():
                errors.append(f"{prefix}.unit must be a non-empty string")
            if "direction" in item and item["direction"] not in METRIC_DIRECTIONS:
                errors.append(f"{prefix}.direction must be one of: {', '.join(METRIC_DIRECTIONS)}")
            for key in ("denominator", "time_window", "baseline"):
                if key in item and not isinstance(item[key], str):
                    errors.append(f"{prefix}.{key} must be a string when present")
            if "independent_observations" in item:
                observations = item["independent_observations"]
                is_json_integer = (
                    isinstance(observations, int)
                    and not isinstance(observations, bool)
                ) or (
                    isinstance(observations, float)
                    and math.isfinite(observations)
                    and observations.is_integer()
                )
                if not is_json_integer or observations < 0:
                    errors.append(f"{prefix}.independent_observations must be a non-negative integer")
            if "uncertainty" in item and (
                not isinstance(item["uncertainty"], str) or not item["uncertainty"].strip()
            ):
                errors.append(f"{prefix}.uncertainty must be a non-empty string when present")
            if "evidence_refs" in item:
                refs = validate_unique_string_refs(item["evidence_refs"], f"{prefix}.evidence_refs")
                if refs is not None:
                    for ref in refs:
                        if ref not in evidence_ids:
                            errors.append(f"{prefix} references unknown evidence id: {ref}")
    if data.get("report_type") == "experiment-report":
        if not isinstance(metrics, list) or not metrics:
            errors.append("experiment-report requires at least one metric")
        elif not all(isinstance(item, dict) and item.get("uncertainty") for item in metrics):
            errors.append("experiment-report metrics require an uncertainty field or an explicit unavailable marker")

    visuals = data.get("visuals", [])
    if isinstance(visuals, list):
        for index, item in enumerate(visuals):
            prefix = f"visuals[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            reject_unknown_fields(
                item,
                prefix,
                ("id", "type", "purpose", "path", "alt_text", "caption", "takeaway", "source", "evidence_refs"),
            )
            require_fields(item, prefix, ("path", "alt_text", "caption", "takeaway", "source"))
            for key in ("path", "alt_text", "caption", "takeaway", "source"):
                if not isinstance(item.get(key), str) or not item.get(key, "").strip():
                    errors.append(f"{prefix}.{key} must be a non-empty string")
            for key in ("id", "type", "purpose"):
                if key in item and not isinstance(item[key], str):
                    errors.append(f"{prefix}.{key} must be a string when present")
            if isinstance(item.get("path"), str):
                issue = (
                    "must use a nonempty local image path or an absolute http(s) URL, not a query or fragment"
                    if item["path"].startswith(("#", "?"))
                    else locator_error(item["path"])
                )
                if issue:
                    errors.append(f"{prefix}.path {issue}")
            if "evidence_refs" in item:
                refs = item["evidence_refs"]
                if not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs):
                    errors.append(f"{prefix}.evidence_refs must be an array of strings")
                else:
                    for ref in refs:
                        if ref not in evidence_ids:
                            errors.append(f"{prefix} references unknown evidence id: {ref}")

    actions = data.get("actions", [])
    if isinstance(actions, list):
        for index, item in enumerate(actions):
            prefix = f"actions[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            reject_unknown_fields(item, prefix, ("text", "owner", "status", "deadline", "acceptance_check"))
            require_fields(item, prefix, ("text", "owner", "status"))
            if not isinstance(item.get("text"), str) or not item.get("text", "").strip():
                errors.append(f"{prefix}.text must be a non-empty string")
            if not isinstance(item.get("owner"), str) or not item.get("owner", "").strip():
                errors.append(f"{prefix}.owner must be a non-empty string or an explicit unassigned marker")
            if item.get("status") not in ACTION_STATUS_VALUES:
                errors.append(f"{prefix}.status must be one of: {', '.join(ACTION_STATUS_VALUES)}")
            for key in ("deadline", "acceptance_check"):
                if key in item and (not isinstance(item[key], str) or not item[key].strip()):
                    errors.append(f"{prefix}.{key} must be a non-empty string when present")
            if not (item.get("deadline") or item.get("acceptance_check")):
                errors.append(f"{prefix} requires deadline or acceptance_check")
    if (
        report_type in ACTION_REQUIRED_MODES
        or data.get("status") in ("partial", "blocked", "failed")
    ) and (not isinstance(actions, list) or not actions):
        errors.append(f"{report_type} with status {data.get('status')} requires at least one action")

    artifacts = data.get("artifacts", [])
    if isinstance(artifacts, list):
        for index, item in enumerate(artifacts):
            prefix = f"artifacts[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            reject_unknown_fields(item, prefix, ("label", "path", "url"))
            require_fields(item, prefix, ("label",))
            if not isinstance(item.get("label"), str) or not item.get("label", "").strip():
                errors.append(f"{prefix}.label must be a non-empty string")
            present_locators = [key for key in ("path", "url") if key in item]
            if len(present_locators) != 1:
                errors.append(f"{prefix} requires exactly one of path or url")
            elif present_locators[0] == "url":
                issue = locator_error(item["url"], url_only=True)
                if issue:
                    errors.append(f"{prefix}.url {issue}")
            else:
                issue = locator_error(item["path"], local_only=True)
                if issue:
                    errors.append(f"{prefix}.path {issue}")

    for key in ("limitations", "open_questions"):
        values = data.get(key, [])
        if isinstance(values, list):
            for index, value in enumerate(values):
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{key}[{index}] must be a non-empty string")
    return errors


def command_validate_spec(args: argparse.Namespace) -> int:
    data = _load_json(Path(args.file))
    errors = validate_report_spec(data)
    payload = {"schema_version": 1, "file": args.file, "valid": not errors, "errors": errors}
    if args.json:
        print(_safe_json_dumps(payload))
    else:
        if errors:
            for error in errors:
                _safe_print(f"ERROR   {error}")
        else:
            _safe_print(f"Valid report spec: {args.file}")
    return 1 if errors else 0


def _escape_inline(value: Any) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for character in ("\\", "`", "*", "_", "[", "]", "#"):
        text = text.replace(character, "\\" + character)
    return _terminal_safe_text(text)


def _escape_cell(value: Any) -> str:
    return _escape_inline(value).replace("|", "\\|")


def _markdown_target(value: Any, *, allow_fragment: bool = False) -> str:
    raw = str(value).strip()
    if allow_fragment and raw.startswith("#"):
        return "#" + quote(raw[1:], safe="+,-._~")
    try:
        parsed = urlsplit(raw)
    except ValueError:
        parsed = None
    if parsed is not None and parsed.scheme in ("http", "https"):
        # Markdown resolves HTML character references in destinations. Escape
        # literal ampersands so one parse round preserves the caller's URL.
        return quote(raw, safe="/:@?&=;#%+,-._~").replace("&", "&amp;")
    # A local filename may literally contain URL delimiters or percent escapes.
    # Encode them here; the audit path decodes exactly once before filesystem lookup.
    return quote(raw, safe="/:@=+,-._~")


def render_report_spec(data: dict[str, Any]) -> str:
    lines = [f"# {_escape_inline(data['headline'])}", "", f"Status: **{_escape_inline(data['status'])}**"]
    if data.get("as_of"):
        lines[-1] += f" · As of: {_escape_inline(data['as_of'])}"
    lines.extend(["", f"Outcome: {_escape_inline(data['summary'])}"])

    evidence_by_id = {item["id"]: item for item in data.get("evidence", []) if isinstance(item, dict) and item.get("id")}
    if data.get("claims"):
        lines.extend(["", "## Findings", ""])
        for claim in data["claims"]:
            label = claim["kind"].capitalize()
            confidence = _escape_inline(claim.get("confidence", "unknown"))
            roles = " / ".join(_escape_inline(role.replace("_", " ")) for role in claim.get("roles", []))
            role_label = f" · {roles}" if roles else ""
            line = f"- **{label}{role_label} ({confidence} confidence):** {_escape_inline(claim['text'])}"
            refs = claim.get("evidence_refs", [])
            if refs:
                rendered_refs = []
                for ref in refs:
                    evidence = evidence_by_id.get(ref, {})
                    locator = evidence.get("locator")
                    rendered_refs.append(
                        f"[{_escape_inline(ref)}]({_markdown_target(locator, allow_fragment=True)})"
                        if locator
                        else f"`{_escape_inline(ref)}`"
                    )
                line += " Evidence: " + ", ".join(rendered_refs) + "."
            if claim.get("boundary"):
                line += " Boundary: " + _escape_inline(claim["boundary"])
            lines.append(line)

    if data.get("evidence"):
        lines.extend(["", "## Evidence", ""])
        for item in data["evidence"]:
            locator = item["locator"]
            source = f"[{_escape_inline(item['id'])}]({_markdown_target(locator, allow_fragment=True)})"
            lines.append(
                f"- **{source} — {_escape_inline(item['label'])}.** "
                f"Verification: {_escape_inline(item['verification'])}"
            )

    if data.get("metrics"):
        lines.extend(
            [
                "",
                "## Metrics",
                "",
                "| Metric | Value | Unit | Direction | Denominator / baseline / window | Independent observations | Uncertainty | Evidence |",
                "|---|---:|---|---|---|---:|---|---|",
            ]
        )
        for item in data["metrics"]:
            context_parts = []
            if "denominator" in item:
                context_parts.append(f"denominator: {item['denominator']}")
            if "baseline" in item:
                context_parts.append(f"baseline: {item['baseline']}")
            if "time_window" in item:
                context_parts.append(f"window: {item['time_window']}")
            context = "; ".join(context_parts) or "—"
            observations = item.get("independent_observations", "—")
            if isinstance(observations, float) and observations.is_integer():
                observations = int(observations)
            rendered_value = "null" if item.get("value") is None else item.get("value", "")
            evidence_refs = ", ".join(item.get("evidence_refs", [])) or "—"
            lines.append(
                "| " + " | ".join(
                    _escape_cell(cell)
                    for cell in (
                        item.get("name", ""),
                        rendered_value,
                        item.get("unit", "—"),
                        item.get("direction", "—"),
                        context,
                        observations,
                        item.get("uncertainty", "—"),
                        evidence_refs,
                    )
                ) + " |"
            )

    if data.get("visuals"):
        lines.extend(["", "## Visual evidence", ""])
        for index, item in enumerate(data["visuals"], start=1):
            figure_id = _escape_inline(item.get("id", f"Figure {index}"))
            lines.extend(
                [
                    f"**{figure_id}. {_escape_inline(item.get('caption', 'Visual evidence'))}**",
                    "",
                    f"![{_escape_inline(item.get('alt_text', ''))}]({_markdown_target(item.get('path', ''))})",
                    "",
                    _escape_inline(item.get("takeaway", "")),
                ]
            )
            if item.get("source"):
                lines.append(f"Source: {_escape_inline(item['source'])}")
            metadata = []
            if item.get("type"):
                metadata.append(f"Type: {_escape_inline(item['type'])}")
            if item.get("purpose"):
                metadata.append(f"Purpose: {_escape_inline(item['purpose'])}")
            if item.get("evidence_refs"):
                metadata.append("Evidence: " + ", ".join(_escape_inline(ref) for ref in item["evidence_refs"]))
            if metadata:
                lines.append(" · ".join(metadata))

    if data.get("limitations"):
        lines.extend(["", "## Boundaries", ""])
        lines.extend(f"- {_escape_inline(item)}" for item in data["limitations"])

    if data.get("actions"):
        lines.extend(
            [
                "",
                "## Actions",
                "",
                "| Action | Owner | Status | Deadline | Acceptance check |",
                "|---|---|---|---|---|",
            ]
        )
        for item in data["actions"]:
            lines.append(
                "| " + " | ".join(
                    _escape_cell(value)
                    for value in (
                        item.get("text", ""),
                        item.get("owner", "—"),
                        item.get("status", "open"),
                        item.get("deadline", "—"),
                        item.get("acceptance_check", "—"),
                    )
                ) + " |"
            )

    if data.get("artifacts"):
        lines.extend(["", "## Artifacts", ""])
        for item in data["artifacts"]:
            if isinstance(item, dict):
                label = item.get("label", item.get("path", "artifact"))
                locator = item.get("path") or item.get("url")
                lines.append(
                    f"- [{_escape_inline(label)}]({_markdown_target(locator)})"
                    if locator
                    else f"- {_escape_inline(label)}"
                )
            else:
                lines.append(f"- {_escape_inline(item)}")

    if data.get("open_questions"):
        lines.extend(["", "## Open questions", ""])
        lines.extend(f"- {_escape_inline(item)}" for item in data["open_questions"])
    return "\n".join(lines).rstrip() + "\n"


def command_render(args: argparse.Namespace) -> int:
    data = _load_json(Path(args.file))
    errors = validate_report_spec(data)
    if errors:
        raise ReportCtlError("Report spec is invalid:\n- " + "\n- ".join(errors))
    output = render_report_spec(data)
    if args.output:
        _safe_write(Path(args.output), output, args.force)
        _safe_print(f"Rendered Markdown report: {args.output}")
    else:
        _safe_print(output, end="", preserve_newlines=True)
    return 0


def _transactional_distribution_write(
    outputs: list[tuple[Path, str]],
    stale_paths: list[Path],
) -> None:
    """Stage every file, then deploy with rollback across the generated set."""

    distribution_dir = outputs[0][0].parent.parent
    transaction_parent = distribution_dir.parent
    while not transaction_parent.exists() and transaction_parent != transaction_parent.parent:
        transaction_parent = transaction_parent.parent
    if not transaction_parent.is_dir():
        raise ReportCtlError(f"Distribution ancestor must be a directory: {transaction_parent}")
    transaction_root: Path | None = None
    staged: list[tuple[Path, Path]] = []
    backups: dict[Path, Path] = {}
    created_dirs: list[Path] = []
    deployed: list[Path] = []
    removed_stale: list[Path] = []
    completed = False

    def cleanup_created_dirs() -> None:
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass

    try:
        transaction_root = Path(
            tempfile.mkdtemp(prefix=".agentic-reporting-dist-", dir=str(transaction_parent))
        )
        required_dirs = sorted({path.parent for path, _ in outputs}, key=lambda item: len(item.parts))
        for directory in required_dirs:
            missing: list[Path] = []
            cursor = directory
            while not cursor.exists():
                missing.append(cursor)
                cursor = cursor.parent
            if not cursor.is_dir():
                raise OSError(f"ancestor is not a directory: {cursor}")
            for candidate in reversed(missing):
                candidate.mkdir()
                created_dirs.append(candidate)

        # Fully materialize every new file next to its destination. A permission or
        # capacity error here happens before any published path is replaced.
        for target, content in outputs:
            fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
            temporary = Path(temporary_name)
            try:
                mode = target.stat().st_mode & 0o777 if target.exists() else 0o644
                os.fchmod(fd, mode)
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(content)
            except Exception:
                try:
                    os.close(fd)
                except OSError:
                    pass
                temporary.unlink(missing_ok=True)
                raise
            staged.append((target, temporary))

        # Preserve every path that the commit phase may replace or remove.
        mutation_paths = list(dict.fromkeys(
            [target for target, _ in outputs] + [path for path in stale_paths if path.exists()]
        ))
        for index, path in enumerate(mutation_paths):
            if path.exists():
                backup = transaction_root / f"{index:04d}.backup"
                shutil.copy2(path, backup)
                backups[path] = backup

        try:
            for target, temporary in staged:
                os.replace(temporary, target)
                deployed.append(target)
            for stale in stale_paths:
                if stale.exists():
                    stale.unlink()
                    removed_stale.append(stale)
        except OSError as exc:
            rollback_errors: list[str] = []
            affected = list(dict.fromkeys(deployed + removed_stale))
            for path in reversed(affected):
                try:
                    backup = backups.get(path)
                    if backup is not None and backup.exists():
                        os.replace(backup, path)
                    elif path.exists():
                        path.unlink()
                except OSError as rollback_exc:
                    rollback_errors.append(f"{path}: {rollback_exc}")
            detail = (
                "; rollback errors: " + " | ".join(rollback_errors)
                if rollback_errors
                else "; prior generated files restored"
            )
            raise ReportCtlError(f"Cannot commit distribution: {exc}{detail}") from exc
        completed = True
    except ReportCtlError:
        raise
    except OSError as exc:
        raise ReportCtlError(f"Cannot stage distribution without changing published files: {exc}") from exc
    finally:
        for _, temporary in staged:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        if transaction_root is not None:
            shutil.rmtree(transaction_root, ignore_errors=True)
        if not completed:
            cleanup_created_dirs()


def command_build_dist(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    try:
        raw_output = Path(args.output).expanduser()
    except (OSError, RuntimeError) as exc:
        raise ReportCtlError(f"Cannot expand distribution output path {args.output}: {exc}") from exc
    candidate = raw_output if raw_output.is_absolute() else Path.cwd() / raw_output
    output_dir = _resolve_checked_path(candidate, "distribution output")
    if output_dir == Path("/") or output_dir == Path.home().resolve():
        raise ReportCtlError(f"Refusing broad output directory: {output_dir}")
    if output_dir.exists() and not output_dir.is_dir():
        raise ReportCtlError(f"Distribution output must be a directory: {output_dir}")
    route_dir = output_dir / "routes"
    module_dir = output_dir / "modules"
    outputs: list[tuple[Path, str]] = []
    index_lines = [
        "# Agent reporting index",
        "",
        "Choose exactly one primary route. Read no other route. Add at most two display modules only when the content requires them. Explicit user format wins.",
        "",
        "## Primary routes",
        "",
    ]
    for mode_id in MODE_IDS:
        record = catalog["modes"][mode_id]
        index_lines.append(f"- [`{mode_id}`](routes/{mode_id}.md) — {record['summary']}")
        plan = {
            "mode": mode_id,
            "surface": "markdown",
            "audience": "user",
            "modules": [],
            "must_show": [],
            "mode_reference": record["file"],
            "module_references": [],
        }
        route_text = _bundle_text(plan, catalog)
        outputs.append((route_dir / f"{mode_id}.md", route_text))
    index_lines.extend(["", "## Optional display modules", ""])
    for module_id in MODULE_IDS:
        record = catalog["modules"][module_id]
        index_lines.append(f"- [`{module_id}`](modules/{module_id}.md) — {record['summary']}")
        module_text = f"# Display module: {module_id}\n\n" + _read_reference(record["file"]) + "\n"
        outputs.append((module_dir / f"{module_id}.md", module_text))
    index_lines.extend(
        [
            "",
            "Before delivery, manually verify facts, latest state, evidence, numbers, uncertainty, and the user's requested format. A repository link is not an installation or instruction-elevation mechanism.",
            "",
        ]
    )
    outputs.append((output_dir / "agent-index.md", "\n".join(index_lines)))
    generated_relative = [path.relative_to(output_dir).as_posix() for path, _ in outputs]
    manifest_path = output_dir / DIST_MANIFEST_NAME
    manifest = {
        "schema_version": 1,
        "kind": "agentic-reporting-distribution",
        "generated_files": generated_relative,
    }
    outputs.append((manifest_path, _safe_json_dumps(manifest) + "\n"))

    # Validate every destination before the first write so a bad later path cannot
    # leave a partially refreshed distribution.
    for path, _ in outputs:
        _reject_symlink_chain(path, "distribution output")
        if path.exists() and not path.is_file():
            raise ReportCtlError(f"Distribution output must be a regular file: {path}")
        existing_parent = path.parent
        while not existing_parent.exists() and existing_parent != existing_parent.parent:
            existing_parent = existing_parent.parent
        if not existing_parent.is_dir():
            raise ReportCtlError(f"Distribution output parent must be a directory: {existing_parent}")

    stale_paths: list[Path] = []
    if args.force and manifest_path.exists():
        previous = _load_json(manifest_path)
        if (
            not isinstance(previous, dict)
            or not isinstance(previous.get("schema_version"), int)
            or isinstance(previous.get("schema_version"), bool)
            or previous.get("schema_version") != 1
            or previous.get("kind") != "agentic-reporting-distribution"
        ):
            raise ReportCtlError(f"Invalid existing distribution manifest: {manifest_path}")
        previous_files = previous.get("generated_files")
        if not isinstance(previous_files, list) or not all(isinstance(item, str) for item in previous_files):
            raise ReportCtlError(f"Invalid generated_files in distribution manifest: {manifest_path}")
        current_files = set(generated_relative)
        for item in previous_files:
            relative = Path(item)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or len(relative.parts) != 2
                or relative.parts[0] not in ("routes", "modules")
                or relative.suffix != ".md"
            ):
                if item not in current_files:
                    raise ReportCtlError(f"Refusing unsafe stale path in distribution manifest: {item}")
                continue
            if item not in current_files:
                stale = output_dir / relative
                _reject_symlink_chain(stale, "stale distribution output")
                stale_paths.append(stale)
    for stale in stale_paths:
        if stale.exists() and not stale.is_file():
            raise ReportCtlError(f"Tracked stale output is not a regular file: {stale}")
    if not args.force:
        existing = [path for path, _ in outputs if path.exists()]
        if existing:
            raise ReportCtlError(
                "Distribution output already contains generated files; pass --force to replace them: "
                + ", ".join(str(path) for path in existing[:5])
            )
    _transactional_distribution_write(outputs, stale_paths)
    _safe_print(f"Built {len(MODE_IDS)} routes and {len(MODULE_IDS)} modules in {output_dir}")
    return 0


def add_route_arguments(parser: argparse.ArgumentParser, include_output: bool = False) -> None:
    parser.add_argument("--task", help="The reporting objective or user request")
    parser.add_argument("--checkpoint", help="Resume a saved reporting checkpoint")
    parser.add_argument("--mode", choices=("auto",) + MODE_IDS, default="auto")
    parser.add_argument("--surface", choices=SURFACES, default="chat")
    parser.add_argument("--audience", default="user")
    parser.add_argument("--module", action="append", choices=MODULE_IDS, help="Display module; repeat at most twice")
    parser.add_argument("--must-show", action="append", default=[], help="Evidence or conclusion that must remain visible")
    if include_output:
        parser.add_argument("--output", required=True)
        parser.add_argument("--force", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(prog="reportctl", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List primary modes and display modules")
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=command_list)

    route_parser = subparsers.add_parser("route", help="Select one mode and bounded modules")
    add_route_arguments(route_parser)
    route_parser.add_argument("--json", action="store_true")
    route_parser.set_defaults(handler=command_route)

    bundle_parser = subparsers.add_parser("bundle", help="Print the selected bounded reporting context")
    add_route_arguments(bundle_parser)
    bundle_parser.add_argument("--max-chars", type=int, default=16000)
    bundle_parser.set_defaults(handler=command_bundle)

    checkpoint_parser = subparsers.add_parser("checkpoint", help="Save a compact long-task reporting manifest")
    add_route_arguments(checkpoint_parser, include_output=True)
    checkpoint_parser.set_defaults(handler=command_checkpoint)

    scaffold_parser = subparsers.add_parser("scaffold", help="Print a mode-specific Markdown skeleton")
    scaffold_parser.add_argument("--mode", choices=MODE_IDS, required=True)
    scaffold_parser.set_defaults(handler=command_scaffold)

    audit_parser = subparsers.add_parser("audit", help="Run limited structural checks on Markdown")
    audit_parser.add_argument("--file", required=True)
    audit_parser.add_argument("--mode", choices=MODE_IDS, required=True)
    audit_parser.add_argument("--json", action="store_true")
    audit_parser.add_argument("--strict", action="store_true", help="Treat warnings as a failing exit status")
    audit_parser.set_defaults(handler=command_audit)

    validate_parser = subparsers.add_parser("validate-spec", help="Validate a structured report specification")
    validate_parser.add_argument("--file", required=True)
    validate_parser.add_argument("--json", action="store_true")
    validate_parser.set_defaults(handler=command_validate_spec)

    render_parser = subparsers.add_parser("render", help="Render a valid structured report as Markdown")
    render_parser.add_argument("--file", required=True)
    render_parser.add_argument("--output")
    render_parser.add_argument("--force", action="store_true")
    render_parser.set_defaults(handler=command_render)

    build_parser_ = subparsers.add_parser("build-dist", help="Build link-only route bundles")
    build_parser_.add_argument("--output", default=str(REPO_ROOT / "dist"))
    build_parser_.add_argument("--force", action="store_true")
    build_parser_.set_defaults(handler=command_build_dist)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if getattr(args, "module", None) and len(args.module) > 2:
            raise ReportCtlError("Select at most two display modules")
        if hasattr(args, "max_chars") and args.max_chars < 1000:
            raise ReportCtlError("--max-chars must be at least 1000")
        return int(args.handler(args))
    except ReportCtlError as exc:
        _safe_print(f"reportctl: {exc}", file=sys.stderr)
        return 2
    except UnicodeError as exc:
        _safe_print(f"reportctl: Unicode input or output failed safely: {exc}", file=sys.stderr)
        return 2
    except (OSError, RuntimeError) as exc:
        _safe_print(f"reportctl: path or filesystem operation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
