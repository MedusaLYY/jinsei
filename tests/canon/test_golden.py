"""Golden tests against the real raw source file.

These pin the full-file parse to reproducible counts and spot values. They
require data/raw/无职转生TXT合集.txt (present after M1 copy; git-ignored).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from overlord_worldsim.canon.model import UnitKind
from overlord_worldsim.canon.parse import parse_source

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "无职转生TXT合集.txt"

pytestmark = pytest.mark.skipif(not RAW.exists(), reason="raw source not present")


def test_full_file_structure() -> None:
    text = RAW.read_text(encoding="utf-8")
    doc = parse_source(text, source_name=RAW.name)
    summary = doc.to_summary()
    assert summary["volume_count"] == 26
    assert summary["unit_count"] == 541
    assert summary["scene_count"] == 526
    assert summary["chunk_count"] == 2731
    assert summary["skipped_count"] == 125
    assert summary["total_paragraphs"] == 135_127
    assert summary["total_chars"] == 3_481_474
    assert doc.volumes[0].volume_no == 1
    assert doc.volumes[0].title == "第一卷 幼年期"
    assert doc.volumes[25].volume_no == 26
    assert doc.volumes[25].title == "第二十六卷 青年期"
    assert doc.units[0].unit_id == "U0001"
    assert doc.units[0].raw_title == "第一卷 幼年期 序章"
    assert doc.units[-1].unit_id == "U0541"
    assert doc.units[-1].canon_layer == "UNKNOWN"
    assert all(unit.end_line >= unit.start_line for unit in doc.units)


def test_full_file_unit_kind_distribution() -> None:
    text = RAW.read_text(encoding="utf-8")
    doc = parse_source(text, source_name=RAW.name)
    kinds = {unit.kind for unit in doc.units}
    assert kinds == {
        UnitKind.STORY,
        UnitKind.PROLOGUE,
        UnitKind.EPILOGUE,
        UnitKind.FINALE,
        UnitKind.BONUS,
        UnitKind.ILLUSTRATION,
        UnitKind.AFTERWORD,
        UnitKind.GAIDEN,
        UnitKind.SIDE,
        UnitKind.INTERLUDE,
    }
    story = [u for u in doc.units if u.unit_id == "U0002"]
    assert story and story[0].kind is UnitKind.STORY
    assert story[0].title == "第一话「难道是：异世界」"


def test_full_file_chunk_invariants() -> None:
    text = RAW.read_text(encoding="utf-8")
    doc = parse_source(text, source_name=RAW.name)
    summary = doc.to_summary()
    chunks = doc.chunks
    assert len(chunks) == summary["chunk_count"]
    scene_ids = {scene.scene_id for scene in doc.scenes}
    unit_ids = {unit.unit_id for unit in doc.units}
    for chunk in chunks:
        assert chunk.scene_id in scene_ids
        assert chunk.unit_id in unit_ids
        assert chunk.source_start_line <= chunk.source_end_line
        assert chunk.text
        assert len(chunk.paragraph_lines) == chunk.text.count("\n") + 1
    assert chunks[0].chunk_id == "C000001"
    assert chunks[0].chapter_title == "序章"


def test_full_file_known_anchor() -> None:
    text = RAW.read_text(encoding="utf-8")
    doc = parse_source(text, source_name=RAW.name)
    story = next(u for u in doc.units if u.title == "第二话「心生反感的女仆」")
    assert story.volume_no == 1
    assert story.start_line == 592
    chunk = next(c for c in doc.chunks if c.unit_id == story.unit_id)
    assert "莉莉雅原本是阿斯拉王国后宫的禁卫侍女" in chunk.text


def test_full_file_tail_units_are_headed() -> None:
    text = RAW.read_text(encoding="utf-8")
    doc = parse_source(text, source_name=RAW.name)
    tail = [u for u in doc.units if u.volume_no is None]
    assert len(tail) == 84
    assert any(u.raw_title == "第二季BD特典 BD1 狂犬来过了" for u in tail)
    assert any(u.raw_title == "Special book 长篇访谈" for u in tail)
    crossover = next(
        u for u in tail if u.raw_title.startswith("主线漫画附录短篇 第九卷『从零开始的无职转生』")
    )
    assert crossover.start_line == 250114
    chapter_markers = [s for s in doc.skipped if s.reason == "chapter_marker"]
    assert [s.line_no for s in chapter_markers] == [250116, 250540, 250982, 251440]
    assert any(u.raw_title == "保罗外传 冒险者隐退篇 第一话【简妮斯】" for u in tail)
