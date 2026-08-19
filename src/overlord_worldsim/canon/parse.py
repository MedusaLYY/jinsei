"""Parsing of the raw Mushoku Tensei TXT into units, scenes, and chunks.

Every unit heading is a 0-indent line; body paragraphs are 4-space-indented
lines. The parser never modifies or summarizes source text: chunk text is the
verbatim paragraph lines (minus the uniform 4-space indent) and every record
retains exact source line numbers.

The pipeline is deterministic: identical input produces identical ids, line
ranges, and chunk hashes.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

from overlord_worldsim.canon.model import (
    Chunk,
    Scene,
    SkippedLine,
    Unit,
    UnitKind,
    Volume,
)

PARSED_ARTIFACT_VERSION = "1.0.0"

_CN_DIGIT = "[一二三四五六七八九十百零〇]+"
_HEADER_MAIN = re.compile(rf"^第({_CN_DIGIT}|\d+)卷[ ]+(.+)$")
_BARE_CHAPTER = re.compile(rf"^第({_CN_DIGIT}|\d+)章$")
_MAIN_STORY = re.compile(rf"^第({_CN_DIGIT}|\d+)话")
_METADATA_LINE = re.compile(r"^(网译版|翻译[：:].*|著[：:].*|转自.*)$")
_BANNER_LINE = re.compile(r"(轻小说文库|WenKu8)")
_ORNAMENT_LINE = re.compile(r"^[◆◇☆★✦✧＝=*\-]{4,}$")
_TITLE_LINE = re.compile(r"^<.*>$")
_BREAK_MARKER = re.compile(r"^[※＊✳✻✥]{1,4}$")
_ZERO_WIDTH = re.compile(r"&#8203;")
_BRACKET_PREFIX = re.compile(r"^[「『〔（(]+")
_PERIODS = ("幼年期", "少年期", "青少年期", "青年期")

_CN_NAMES = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
    10: "十",
    11: "十一",
    12: "十二",
    13: "十三",
    14: "十四",
    15: "十五",
    16: "十六",
    17: "十七",
    18: "十八",
    19: "十九",
    20: "二十",
    21: "二十一",
    22: "二十二",
    23: "二十三",
    24: "二十四",
    25: "二十五",
    26: "二十六",
}

_MAIN_KIND_RULES: tuple[tuple[str, UnitKind], ...] = (
    ("序章", UnitKind.PROLOGUE),
    ("终章", UnitKind.EPILOGUE),
    ("最终章", UnitKind.EPILOGUE),
    ("最终话", UnitKind.FINALE),
    ("闲话", UnitKind.SIDE),
    ("外传", UnitKind.GAIDEN),
    ("间话", UnitKind.INTERLUDE),
    ("插图", UnitKind.ILLUSTRATION),
    ("后记", UnitKind.AFTERWORD),
    ("解说", UnitKind.COMMENTARY),
    ("术语", UnitKind.TERMINOLOGY),
    ("特典", UnitKind.BONUS),
    ("特稿", UnitKind.BONUS),
)

_TAIL_KIND_RULES: tuple[tuple[str, UnitKind], ...] = (
    ("第二季BD特典", UnitKind.BONUS),
    ("短篇", UnitKind.BONUS),
    ("广播剧", UnitKind.BONUS),
    ("BD特典", UnitKind.BONUS),
    ("漫画附录", UnitKind.BONUS),
    ("主线", UnitKind.BONUS),
    ("其它", UnitKind.BONUS),
    ("保罗外传", UnitKind.GAIDEN),
    ("Special book", UnitKind.BONUS),
)


def _cn_numeral(value: str) -> int:
    """Convert a Chinese numeral to an integer (one .. twenty-six)."""
    if value.isdigit():
        return int(value)
    digits = {
        "零": 0,
        "〇": 0,
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
        "百": 100,
    }
    total = 0
    if "百" in value:
        head, tail = value.split("百", 1)
        total += digits[head] * 100 if head else 100
        value = tail
    if "十" in value:
        head, tail = value.split("十", 1)
        total += digits[head] * 10 if head else 10
        value = tail
    if value:
        total += digits[value]
    return total


def _unit_id(seq: int) -> str:
    return f"U{seq:04d}"


def _scene_id(seq: int) -> str:
    return f"S{seq:06d}"


def _chunk_id(seq: int) -> str:
    return f"C{seq:06d}"


def _classify_kind(token: str, is_tail: bool) -> UnitKind:
    """Classify a single token that may carry the unit kind."""
    normalized = _BRACKET_PREFIX.sub("", token)
    if is_tail:
        if _BARE_CHAPTER.match(token):
            return UnitKind.CHAPTER
        for prefix, kind in _TAIL_KIND_RULES:
            if token.startswith(prefix):
                return kind
        if "特典" in token or "特稿" in token:
            return UnitKind.BONUS
        return UnitKind.UNKNOWN
    if _MAIN_STORY.match(token):
        return UnitKind.STORY
    for prefix, kind in _MAIN_KIND_RULES:
        if normalized.startswith(prefix):
            return kind
    if "特典" in token or "特稿" in token or "联动" in token or "人物录" in token:
        return UnitKind.BONUS
    return UnitKind.UNKNOWN


def _find_kind_token(tokens: list[str], is_tail: bool) -> tuple[UnitKind, int, str]:
    """Return (kind, index of the first kind-bearing token, normalized title)."""
    for index, token in enumerate(tokens):
        kind = _classify_kind(token, is_tail)
        if kind is not UnitKind.UNKNOWN:
            return kind, index, " ".join(tokens[index:])
    return UnitKind.UNKNOWN, 0, " ".join(tokens)


@dataclass(frozen=True)
class UnitHeader:
    """Parsed metadata from a unit heading line."""

    volume_no: int | None
    period: str | None
    part_title: str | None
    kind: UnitKind
    title: str
    raw_title: str
    in_universe: bool
    is_tail: bool


def parse_header_line(line: str) -> UnitHeader | None:
    """Parse a 0-indent heading line into a UnitHeader, or None if not a heading."""
    stripped = line.strip()
    if not stripped or line[0].isspace():
        return None
    if _BANNER_LINE.search(stripped) or _TITLE_LINE.match(stripped):
        return None
    match = _HEADER_MAIN.match(stripped)
    if match:
        volume_no = _cn_numeral(match.group(1))
        rest = match.group(2)
        tokens = [_ZERO_WIDTH.sub("", token) for token in rest.split(" ")]
        period = tokens[0] if tokens and tokens[0] in _PERIODS else None
        kind, kind_index, title = _find_kind_token(tokens[1:], is_tail=False)
        part_title = " ".join(tokens[1 : 1 + kind_index]) if kind_index >= 1 else None
        return UnitHeader(
            volume_no=volume_no,
            period=period,
            part_title=part_title or None,
            kind=kind,
            title=title,
            raw_title=stripped,
            in_universe=kind not in (UnitKind.AFTERWORD, UnitKind.COMMENTARY, UnitKind.TERMINOLOGY),
            is_tail=False,
        )
    kind = _classify_kind(stripped, is_tail=True)
    if kind is UnitKind.UNKNOWN:
        return None
    return UnitHeader(
        volume_no=None,
        period=None,
        part_title=None,
        kind=kind,
        title=stripped,
        raw_title=stripped,
        in_universe="访谈" not in stripped,
        is_tail=True,
    )


@dataclass
class _RawUnit:
    header: UnitHeader
    header_line: int
    paragraphs: list[tuple[int, str]] = field(default_factory=list)
    break_markers: list[int] = field(default_factory=list)


@dataclass
class ParsedDocument:
    """Fully parsed source: volumes, units, scenes, chunks, and skipped lines."""

    volumes: list[Volume]
    units: list[Unit]
    scenes: list[Scene]
    chunks: list[Chunk]
    skipped: list[SkippedLine]
    source_name: str | None = None

    def to_volumes_json(self) -> dict[str, Any]:
        return {
            "version": PARSED_ARTIFACT_VERSION,
            "source": self.source_name,
            "volumes": [_volume_to_json(v) for v in self.volumes],
        }

    def to_units_json(self) -> dict[str, Any]:
        return {
            "version": PARSED_ARTIFACT_VERSION,
            "source": self.source_name,
            "units": [_unit_to_json(u) for u in self.units],
        }

    def to_scenes_jsonl(self) -> list[dict[str, Any]]:
        return [_scene_to_json(s) for s in self.scenes]

    def to_chunks_jsonl(self) -> list[dict[str, Any]]:
        return [_chunk_to_json(c) for c in self.chunks]

    def to_report_jsonl(self) -> list[dict[str, Any]]:
        return [
            {"line_no": skipped.line_no, "reason": skipped.reason, "text": skipped.text}
            for skipped in self.skipped
        ]

    def to_summary(self) -> dict[str, Any]:
        return {
            "version": PARSED_ARTIFACT_VERSION,
            "source": self.source_name,
            "volume_count": len(self.volumes),
            "unit_count": len(self.units),
            "scene_count": len(self.scenes),
            "chunk_count": len(self.chunks),
            "skipped_count": len(self.skipped),
            "total_chars": sum(unit.char_count for unit in self.units),
            "total_paragraphs": sum(unit.paragraph_count for unit in self.units),
        }


def _volume_to_json(volume: Volume) -> dict[str, Any]:
    return {
        "volume_no": volume.volume_no,
        "title": volume.title,
        "period": volume.period,
        "start_line": volume.start_line,
        "end_line": volume.end_line,
        "part_titles": list(volume.part_titles),
        "unit_ids": list(volume.unit_ids),
    }


def _unit_to_json(unit: Unit) -> dict[str, Any]:
    return {
        "unit_id": unit.unit_id,
        "volume_no": unit.volume_no,
        "seq_in_volume": unit.seq_in_volume,
        "kind": unit.kind.value,
        "raw_title": unit.raw_title,
        "title": unit.title,
        "period": unit.period,
        "part_title": unit.part_title,
        "start_line": unit.start_line,
        "end_line": unit.end_line,
        "in_universe": unit.in_universe,
        "canon_layer": unit.canon_layer,
        "char_count": unit.char_count,
        "paragraph_count": unit.paragraph_count,
    }


def _scene_to_json(scene: Scene) -> dict[str, Any]:
    return {
        "scene_id": scene.scene_id,
        "unit_id": scene.unit_id,
        "seq": scene.seq,
        "start_line": scene.start_line,
        "end_line": scene.end_line,
        "break_line": scene.break_line,
        "paragraph_count": scene.paragraph_count,
        "char_count": scene.char_count,
    }


def _chunk_to_json(chunk: Chunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "unit_id": chunk.unit_id,
        "scene_id": chunk.scene_id,
        "volume_no": chunk.volume_no,
        "chapter_title": chunk.chapter_title,
        "scene_seq": chunk.scene_seq,
        "text": chunk.text,
        "paragraph_lines": list(chunk.paragraph_lines),
        "source_start_line": chunk.source_start_line,
        "source_end_line": chunk.source_end_line,
        "char_count": chunk.char_count,
        "sha256": chunk.sha256,
    }


def _build_units(raw_units: list[_RawUnit]) -> list[Unit]:
    units: list[Unit] = []
    per_volume: dict[int | None, int] = {}
    for seq, raw in enumerate(raw_units, start=1):
        volume_no = raw.header.volume_no
        per_volume[volume_no] = per_volume.get(volume_no, 0) + 1
        paragraphs = raw.paragraphs
        last_line = (
            paragraphs[-1][0]
            if paragraphs
            else (raw.break_markers[-1] if raw.break_markers else raw.header_line)
        )
        units.append(
            Unit(
                unit_id=_unit_id(seq),
                volume_no=volume_no,
                seq_in_volume=per_volume[volume_no],
                kind=raw.header.kind,
                raw_title=raw.header.raw_title,
                title=raw.header.title,
                period=raw.header.period,
                part_title=raw.header.part_title,
                start_line=raw.header_line,
                end_line=last_line,
                in_universe=raw.header.in_universe,
                canon_layer="CORE" if volume_no is not None else "UNKNOWN",
                char_count=sum(len(text) for _, text in paragraphs),
                paragraph_count=len(paragraphs),
            )
        )
    for index in range(len(units) - 1):
        units[index] = _replace(units[index], end_line=units[index + 1].start_line - 1)
    return units


def _replace(unit: Unit, **changes: Any) -> Unit:
    values = dict(unit.__dict__)
    values.update(changes)
    return Unit(**values)


def _assemble_volumes(units: list[Unit]) -> list[Volume]:
    by_volume: dict[int, list[Unit]] = {}
    for unit in units:
        if unit.volume_no is not None:
            by_volume.setdefault(unit.volume_no, []).append(unit)
    volumes: list[Volume] = []
    for volume_no in sorted(by_volume):
        entries = by_volume[volume_no]
        part_titles: list[str] = []
        for unit in entries:
            if unit.part_title and unit.part_title not in part_titles:
                part_titles.append(unit.part_title)
        period = next((unit.period for unit in entries if unit.period), None)
        volumes.append(
            Volume(
                volume_no=volume_no,
                title=f"第{_CN_NAMES[volume_no]}卷 {period}" if period else f"第{volume_no}卷",
                period=period or "",
                start_line=min(unit.start_line for unit in entries),
                end_line=max(unit.end_line for unit in entries),
                part_titles=tuple(part_titles),
                unit_ids=tuple(unit.unit_id for unit in entries),
            )
        )
    return volumes


def _split_scenes_and_chunks(
    unit: Unit,
    raw: _RawUnit,
    scene_seq_start: int,
    chunk_seq_start: int,
) -> tuple[list[Scene], list[Chunk]]:
    """Split a unit body into scenes (break markers) and chunks (paragraph runs)."""
    scenes: list[Scene] = []
    chunks: list[Chunk] = []
    markers = sorted(raw.break_markers)
    marker_index = 0
    pending_break: int | None = None
    blocks: list[tuple[list[tuple[int, str]], int | None]] = []
    current: list[tuple[int, str]] = []
    for line_no, text in raw.paragraphs:
        while marker_index < len(markers) and markers[marker_index] < line_no:
            if current:
                blocks.append((current, pending_break))
                current = []
            pending_break = markers[marker_index]
            marker_index += 1
        current.append((line_no, text))
    if current:
        blocks.append((current, pending_break))
    for block_index, (paragraphs, break_line) in enumerate(blocks):
        seq = scene_seq_start + block_index + 1
        start_line = paragraphs[0][0] if paragraphs else unit.start_line
        end_line = paragraphs[-1][0] if paragraphs else unit.start_line
        scenes.append(
            Scene(
                scene_id=_scene_id(seq),
                unit_id=unit.unit_id,
                seq=seq,
                start_line=start_line,
                end_line=end_line,
                break_line=break_line,
                paragraph_count=len(paragraphs),
                char_count=sum(len(text) for _, text in paragraphs),
            )
        )
        if not paragraphs:
            continue
        acc: list[tuple[int, str]] = []
        acc_chars = 0
        for line_no, text in paragraphs:
            acc.append((line_no, text))
            acc_chars += len(text)
            if acc_chars >= 1400:
                chunks.append(
                    _build_chunk(unit, scenes[-1], acc, chunk_seq_start + len(chunks) + 1)
                )
                acc = []
                acc_chars = 0
        if acc:
            chunks.append(_build_chunk(unit, scenes[-1], acc, chunk_seq_start + len(chunks) + 1))
    return scenes, chunks


def _build_chunk(
    unit: Unit,
    scene: Scene,
    paragraphs: list[tuple[int, str]],
    seq: int,
) -> Chunk:
    text = "\n".join(text for _, text in paragraphs)
    return Chunk(
        chunk_id=_chunk_id(seq),
        unit_id=unit.unit_id,
        scene_id=scene.scene_id,
        volume_no=unit.volume_no,
        chapter_title=unit.title,
        scene_seq=scene.seq,
        text=text,
        paragraph_lines=tuple(line_no for line_no, _ in paragraphs),
        source_start_line=paragraphs[0][0],
        source_end_line=paragraphs[-1][0],
        char_count=sum(len(text) for _, text in paragraphs),
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def parse_source(
    text: str,
    source_name: str | None = None,
) -> ParsedDocument:
    """Parse the full source text into a deterministic ParsedDocument."""
    lines = text.split("\n")
    raw_units: list[_RawUnit] = []
    skipped: list[SkippedLine] = []
    current: _RawUnit | None = None
    for index, line in enumerate(lines):
        line_no = index + 1
        stripped = line.strip()
        if not stripped:
            continue
        if not line[0].isspace():
            if _BANNER_LINE.search(stripped) or _ORNAMENT_LINE.match(stripped):
                skipped.append(SkippedLine(line_no, "banner", stripped))
                current = None
                continue
            if _TITLE_LINE.match(stripped):
                skipped.append(SkippedLine(line_no, "file_title", stripped))
                current = None
                continue
            header = parse_header_line(line)
            if header is None:
                skipped.append(SkippedLine(line_no, "unknown_heading", stripped))
                current = None
                continue
            raw_units.append(_RawUnit(header=header, header_line=line_no))
            current = raw_units[-1]
            continue
        if current is None:
            skipped.append(SkippedLine(line_no, "orphan_body", stripped))
            continue
        if _BARE_CHAPTER.match(stripped):
            skipped.append(SkippedLine(line_no, "chapter_marker", stripped))
            continue
        if _METADATA_LINE.match(stripped):
            skipped.append(SkippedLine(line_no, "unit_metadata", stripped))
            continue
        if _BREAK_MARKER.match(stripped):
            current.break_markers.append(line_no)
            continue
        current.paragraphs.append((line_no, stripped))
    units = _build_units(raw_units)
    volumes = _assemble_volumes(units)
    scenes: list[Scene] = []
    chunks: list[Chunk] = []
    scene_seq = 0
    chunk_seq = 0
    for unit, raw in zip(units, raw_units, strict=True):
        unit_scenes, unit_chunks = _split_scenes_and_chunks(unit, raw, scene_seq, chunk_seq)
        scenes.extend(unit_scenes)
        chunks.extend(unit_chunks)
        scene_seq += len(unit_scenes)
        chunk_seq += len(unit_chunks)
    return ParsedDocument(
        volumes=volumes,
        units=units,
        scenes=scenes,
        chunks=chunks,
        skipped=skipped,
        source_name=source_name,
    )
