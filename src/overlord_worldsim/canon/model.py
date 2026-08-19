"""Canon source model: volumes, units, scenes, chunks, and skipped lines.

The parsed model is a pure index layer over the raw source text. Every record
keeps the original line numbers so the verbatim source remains authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class UnitKind(Enum):
    """Stable classification of a unit's literary kind."""

    PROLOGUE = "PROLOGUE"
    STORY = "STORY"
    SIDE = "SIDE"
    GAIDEN = "GAIDEN"
    INTERLUDE = "INTERLUDE"
    BONUS = "BONUS"
    ILLUSTRATION = "ILLUSTRATION"
    AFTERWORD = "AFTERWORD"
    COMMENTARY = "COMMENTARY"
    FINALE = "FINALE"
    EPILOGUE = "EPILOGUE"
    CHAPTER = "CHAPTER"
    TERMINOLOGY = "TERMINOLOGY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Volume:
    """A mainline volume (1..26). Tail units have no volume."""

    volume_no: int
    title: str
    period: str
    start_line: int
    end_line: int
    part_titles: tuple[str, ...]
    unit_ids: tuple[str, ...]


@dataclass(frozen=True)
class Unit:
    """One headed section: a chapter, prologue, bonus story, afterword, etc."""

    unit_id: str
    volume_no: int | None
    seq_in_volume: int
    kind: UnitKind
    raw_title: str
    title: str
    period: str | None
    part_title: str | None
    start_line: int
    end_line: int
    in_universe: bool
    canon_layer: str
    char_count: int
    paragraph_count: int


@dataclass(frozen=True)
class Scene:
    """A contiguous narrative block within a unit, split at break markers."""

    scene_id: str
    unit_id: str
    seq: int
    start_line: int
    end_line: int
    break_line: int | None
    paragraph_count: int
    char_count: int


@dataclass(frozen=True)
class Chunk:
    """A retrieval unit: consecutive paragraphs, never crossing scenes."""

    chunk_id: str
    unit_id: str
    scene_id: str
    volume_no: int | None
    chapter_title: str
    scene_seq: int
    text: str
    paragraph_lines: tuple[int, ...]
    source_start_line: int
    source_end_line: int
    char_count: int
    sha256: str


@dataclass(frozen=True)
class SkippedLine:
    """A line excluded from body text but retained for full traceability."""

    line_no: int
    reason: str
    text: str


def volume_to_json(volume: Volume) -> dict[str, Any]:
    return {
        "volume_no": volume.volume_no,
        "title": volume.title,
        "period": volume.period,
        "start_line": volume.start_line,
        "end_line": volume.end_line,
        "part_titles": list(volume.part_titles),
        "unit_ids": list(volume.unit_ids),
    }


def unit_to_json(unit: Unit) -> dict[str, Any]:
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


def scene_to_json(scene: Scene) -> dict[str, Any]:
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


def chunk_to_json(chunk: Chunk) -> dict[str, Any]:
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


def skipped_to_json(skipped: SkippedLine) -> dict[str, Any]:
    return {
        "line_no": skipped.line_no,
        "reason": skipped.reason,
        "text": skipped.text,
    }
