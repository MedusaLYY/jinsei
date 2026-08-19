"""Tests for the canon source model (dataclasses and JSON codecs)."""

from __future__ import annotations

from overlord_worldsim.canon.model import (
    Chunk,
    Scene,
    Unit,
    UnitKind,
    chunk_to_json,
    scene_to_json,
    unit_to_json,
)


def test_unit_kind_members_are_stable() -> None:
    assert UnitKind.PROLOGUE.value == "PROLOGUE"
    assert UnitKind.STORY.value == "STORY"
    assert UnitKind.SIDE.value == "SIDE"
    assert UnitKind.GAIDEN.value == "GAIDEN"
    assert UnitKind.INTERLUDE.value == "INTERLUDE"
    assert UnitKind.BONUS.value == "BONUS"
    assert UnitKind.ILLUSTRATION.value == "ILLUSTRATION"
    assert UnitKind.AFTERWORD.value == "AFTERWORD"
    assert UnitKind.COMMENTARY.value == "COMMENTARY"
    assert UnitKind.FINALE.value == "FINALE"
    assert UnitKind.EPILOGUE.value == "EPILOGUE"
    assert UnitKind.CHAPTER.value == "CHAPTER"
    assert UnitKind.UNKNOWN.value == "UNKNOWN"


def test_unit_json_round_trip_structure() -> None:
    unit = Unit(
        unit_id="U0001",
        volume_no=1,
        seq_in_volume=1,
        kind=UnitKind.PROLOGUE,
        raw_title="第一卷 幼年期 序章",
        title="序章",
        period="幼年期",
        part_title=None,
        start_line=6,
        end_line=283,
        in_universe=True,
        canon_layer="CORE",
        char_count=10,
        paragraph_count=2,
    )
    data = unit_to_json(unit)
    assert data["unit_id"] == "U0001"
    assert data["volume_no"] == 1
    assert data["kind"] == "PROLOGUE"
    assert data["raw_title"] == "第一卷 幼年期 序章"
    assert data["title"] == "序章"
    assert data["period"] == "幼年期"
    assert data["part_title"] is None
    assert data["start_line"] == 6
    assert data["end_line"] == 283
    assert data["in_universe"] is True
    assert data["canon_layer"] == "CORE"
    assert data["char_count"] == 10
    assert data["paragraph_count"] == 2
    assert sorted(data) == sorted(
        [
            "unit_id",
            "volume_no",
            "seq_in_volume",
            "kind",
            "raw_title",
            "title",
            "period",
            "part_title",
            "start_line",
            "end_line",
            "in_universe",
            "canon_layer",
            "char_count",
            "paragraph_count",
        ]
    )


def test_scene_json_round_trip_structure() -> None:
    scene = Scene(
        scene_id="S000001",
        unit_id="U0001",
        seq=1,
        start_line=7,
        end_line=10,
        break_line=8,
        paragraph_count=2,
        char_count=20,
    )
    data = scene_to_json(scene)
    assert data["scene_id"] == "S000001"
    assert data["unit_id"] == "U0001"
    assert data["seq"] == 1
    assert data["start_line"] == 7
    assert data["end_line"] == 10
    assert data["break_line"] == 8
    assert data["paragraph_count"] == 2
    assert data["char_count"] == 20


def test_chunk_json_round_trip_structure() -> None:
    chunk = Chunk(
        chunk_id="C000001",
        unit_id="U0001",
        scene_id="S000001",
        volume_no=1,
        chapter_title="序章",
        scene_seq=1,
        text="第一段\n第二段",
        paragraph_lines=(7, 9),
        source_start_line=7,
        source_end_line=9,
        char_count=5,
        sha256="abc",
    )
    data = chunk_to_json(chunk)
    assert data["chunk_id"] == "C000001"
    assert data["unit_id"] == "U0001"
    assert data["scene_id"] == "S000001"
    assert data["volume_no"] == 1
    assert data["chapter_title"] == "序章"
    assert data["scene_seq"] == 1
    assert data["text"] == "第一段\n第二段"
    assert data["paragraph_lines"] == [7, 9]
    assert data["source_start_line"] == 7
    assert data["source_end_line"] == 9
    assert data["char_count"] == 5
    assert data["sha256"] == "abc"
