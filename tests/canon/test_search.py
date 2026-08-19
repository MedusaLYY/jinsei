"""Tests for full-text search over the canon database."""

from __future__ import annotations

from pathlib import Path

import pytest

from overlord_worldsim.canon.fts import SearchHit, search_canon_text
from overlord_worldsim.canon.loader import build_canon_db
from overlord_worldsim.canon.parse import parse_source

CORPUS = (
    "第一卷 幼年期 序章\n"
    "\n"
    "    希露菲的头发是银色的。\n"
    "\n"
    "    鲁迪乌斯记得上辈子的记忆。\n"
    "\n"
    "第一卷 幼年期 第一话「测试章节」\n"
    "\n"
    "    保罗是鲁迪乌斯的父亲。\n"
    "\n"
    "短篇 广播剧特典 特典短篇\n"
    "\n"
    "    特典里鲁迪乌斯遇见了希露菲。\n"
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    doc = parse_source(CORPUS, source_name="corpus.txt")
    return build_canon_db(doc, tmp_path / "canon.sqlite3", sha256="abc123")


def test_search_canon_text_returns_bm25_ranked_hits(db_path: Path) -> None:
    hits = search_canon_text(db_path, "希露菲")
    assert len(hits) == 2
    assert all(isinstance(hit, SearchHit) for hit in hits)
    assert {hit.chunk_id for hit in hits} == {"C000001", "C000003"}
    assert all("希露菲" in hit.text for hit in hits)
    core = next(hit for hit in hits if hit.volume_no == 1)
    assert core.chapter_title == "序章"
    assert core.source_start_line == 3
    assert core.source_end_line == 5
    assert "希露菲的头发" in core.text
    bonus = next(hit for hit in hits if hit.volume_no is None)
    assert bonus.chapter_title == "短篇 广播剧特典 特典短篇"


def test_search_canon_text_filters_by_volume(db_path: Path) -> None:
    hits = search_canon_text(db_path, "鲁迪乌斯", volume_no=1)
    assert len(hits) == 2
    hits = search_canon_text(db_path, "鲁迪乌斯", volume_no=2)
    assert hits == []


def test_search_canon_text_filters_by_canon_layer(db_path: Path) -> None:
    hits = search_canon_text(db_path, "鲁迪乌斯", canon_layer="CORE")
    assert len(hits) == 2
    hits = search_canon_text(db_path, "鲁迪乌斯", canon_layer="UNKNOWN")
    assert len(hits) == 1


def test_search_canon_text_respects_limit_and_order(db_path: Path) -> None:
    hits = search_canon_text(db_path, "希露菲", limit=1)
    assert len(hits) == 1
    assert hits[0].chunk_id in {"C000001", "C000003"}


def test_search_canon_text_validates_query(db_path: Path) -> None:
    with pytest.raises(ValueError, match="query"):
        search_canon_text(db_path, "")
    with pytest.raises(ValueError, match="query"):
        search_canon_text(db_path, '"unbalanced')
    with pytest.raises(ValueError, match="query"):
        search_canon_text(db_path, "x" * 300)
    with pytest.raises(ValueError, match="query"):
        search_canon_text(db_path, "bad\x00query")
    with pytest.raises(ValueError, match="OR"):
        search_canon_text(db_path, "希露菲 OR 保罗")
    with pytest.raises(ValueError, match="volume_no"):
        search_canon_text(db_path, "希露菲", volume_no=0)
    with pytest.raises(ValueError, match="canon_layer"):
        search_canon_text(db_path, "希露菲", canon_layer="BOGUS")
    with pytest.raises(ValueError, match="limit"):
        search_canon_text(db_path, "希露菲", limit=0)


def test_search_canon_text_maps_fts_syntax_errors(db_path: Path) -> None:
    with pytest.raises(ValueError, match="invalid search query"):
        search_canon_text(db_path, "希露菲 AND")
