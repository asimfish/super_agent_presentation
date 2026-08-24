#!/usr/bin/env python3
"""Bounded, deterministic Markdown image candidate scanner.

This module is the single scanner implementation shared by the installed reporting
Skill and the repository benchmark.  It implements a conservative credit subset;
it is not a general CommonMark or HTML renderer and performs no I/O.
"""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Iterable, NamedTuple


MAX_MARKDOWN_IMAGE_ALT_CHARS = 2_048
MAX_MARKDOWN_IMAGE_TARGET_CHARS = 4_096
COMMONMARK_ENTITY_PATTERN = re.compile(
    r"&(?:#[Xx][0-9A-Fa-f]{1,6}|#[0-9]{1,7}|[A-Za-z][A-Za-z0-9]{1,31});"
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
    r"(?:[ \t]*=[ \t]*(?:[^ \t\"'=<>\x60]+|'[^']*'|\"[^\"]*\"))?"
    r")*[ \t]*/?>"
    r")[ \t]*"
)


class MarkdownImageCandidate(NamedTuple):
    """One source-ordered image or raw-HTML visual candidate."""

    alt: str
    target: str
    start: int
    end: int
    canonical: bool


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
        # CommonMark applies backslash escapes before entity decoding.  An odd
        # backslash run therefore makes the ampersand literal; an even run
        # leaves it eligible for decoding.
        if _markdown_character_is_escaped(value, match.start()):
            return token
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


def scan_markdown_images(
    text: str,
    *,
    record_limit: int,
) -> list[MarkdownImageCandidate]:
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

    if not isinstance(record_limit, int) or isinstance(record_limit, bool) or record_limit < 0:
        raise ValueError("record_limit must be a non-negative integer")
    if record_limit == 0:
        return []

    literal_mask = _commonmark_image_block_mask(text)
    potential_starts = _potential_markdown_image_starts(text, record_limit)
    raw_html_tags = _potential_raw_html_opening_tags(text, record_limit)
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
            if len(images) >= record_limit:
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
    return [MarkdownImageCandidate(*item) for item in images[:record_limit]]


def decode_commonmark_entities(value: str) -> str:
    """Decode the semicolon-terminated entity subset used by the scanner."""

    return _decode_commonmark_entities(value)


def has_visible_alt_text(value: str) -> bool:
    """Return whether alternative text contains a reader-visible character."""

    return _has_visible_alt_text(value)


def commonmark_image_block_mask(text: str) -> bytearray:
    """Expose the scanner's conservative block-literal mask to its host."""

    return _commonmark_image_block_mask(text)


def markdown_character_is_escaped(text: str, index: int) -> bool:
    """Expose the scanner's Markdown backslash-escape predicate to its host."""

    return _markdown_character_is_escaped(text, index)


def portable_markdown_line_ranges(text: str) -> Iterable[tuple[int, int]]:
    """Expose portable Markdown line ranges to its host."""

    return _portable_markdown_line_ranges(text)


__all__ = (
    "MarkdownImageCandidate",
    "commonmark_image_block_mask",
    "decode_commonmark_entities",
    "has_visible_alt_text",
    "markdown_character_is_escaped",
    "portable_markdown_line_ranges",
    "scan_markdown_images",
)
