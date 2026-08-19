"""Tests for the canon database schema and loader."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from overlord_worldsim.canon.loader import build_canon_db, open_canon_db
from overlord_worldsim.canon.parse import parse_source

CORPUS = (
    "★☆★☆★☆轻小说文库(Www.WenKu8.Com)☆★☆★☆★\n"
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
    "    保罗挥舞着剑。\n"
)


def _build(tmp_path: Path) -> Path:
    doc = parse_source(CORPUS, source_name="corpus.txt")
    db_path = tmp_path / "canon.sqlite3"
    build_canon_db(doc, db_path, sha256="abc123")
    return db_path


def test_build_canon_db_schema_and_counts(tmp_path: Path) -> None:
    db_path = _build(tmp_path)
    connection = sqlite3.connect(db_path)
    try:
        volumes = connection.execute("SELECT volume_no, title, period FROM volumes").fetchall()
        assert volumes == [(1, "第一卷 幼年期", "幼年期")]
        units = connection.execute("SELECT unit_id, kind, raw_title FROM units").fetchall()
        assert len(units) == 2
        scenes = connection.execute("SELECT COUNT(*) FROM scenes").fetchall()[0][0]
        assert scenes == 2
        chunks = connection.execute("SELECT COUNT(*) FROM chunks").fetchall()[0][0]
        assert chunks == 2
        assert connection.execute(
            "SELECT sha256 FROM content_hashes WHERE kind='source_txt'"
        ).fetchone() == ("abc123",)
        row = connection.execute(
            "SELECT chunk_id, source_start_line, source_end_line, char_count"
            " FROM chunks ORDER BY chunk_id"
        ).fetchall()
        assert row == [("C000001", 4, 6, 24), ("C000002", 10, 12, 18)]
    finally:
        connection.close()


def test_build_canon_db_fts_matches_text(tmp_path: Path) -> None:
    db_path = _build(tmp_path)
    connection = sqlite3.connect(db_path)
    try:
        hits = connection.execute(
            "SELECT c.chunk_id FROM chunks_fts JOIN chunks c ON c.rowid = chunks_fts.rowid "
            "WHERE chunks_fts MATCH '希露菲' ORDER BY bm25(chunks_fts)"
        ).fetchall()
        assert hits == [("C000001",)]
        assert connection.execute("SELECT COUNT(*) FROM chunks_fts").fetchone() == (2,)
    finally:
        connection.close()


def test_build_canon_db_is_idempotent(tmp_path: Path) -> None:
    db_path = _build(tmp_path)
    doc = parse_source(CORPUS, source_name="corpus.txt")
    build_canon_db(doc, db_path, sha256="abc123")
    connection = sqlite3.connect(db_path)
    try:
        assert connection.execute("SELECT COUNT(*) FROM chunks").fetchone() == (2,)
    finally:
        connection.close()


def test_open_canon_db_requires_foreign_keys(tmp_path: Path) -> None:
    db_path = _build(tmp_path)
    connection = open_canon_db(db_path)
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        connection.close()


def test_load_volumes_round_trip(tmp_path: Path) -> None:
    from overlord_worldsim.canon.loader import load_volumes

    db_path = _build(tmp_path)
    connection = open_canon_db(db_path)
    try:
        volumes = load_volumes(connection)
        assert len(volumes) == 1
        assert volumes[0].volume_no == 1
        assert volumes[0].title == "第一卷 幼年期"
        assert volumes[0].period == "幼年期"
    finally:
        connection.close()


def test_apply_extraction_batch_is_idempotent(tmp_path: Path) -> None:
    from overlord_worldsim.canon.extract_model import (
        Confidence,
        DatePrecision,
        Entity,
        EntityKind,
        ExtractionBatch,
        Fact,
    )

    db_path = _build(tmp_path)
    entity = Entity(
        entity_id="E0001",
        name="鲁迪乌斯",
        aliases=(),
        kind=EntityKind.CHARACTER,
        introduced_volume=1,
        introduced_line=4,
        description="",
    )
    fact = Fact(
        fact_id="F0001",
        entity_id="E0001",
        predicate="身份",
        object_value="转生者",
        start_date=None,
        end_date=None,
        date_precision=DatePrecision.UNKNOWN,
        evidence_volumes=(1,),
        evidence_lines=((4, 6),),
        confidence=Confidence.EXPLICIT,
        visible_from_volume=1,
        visible_to_volume=None,
    )
    batch = ExtractionBatch(
        batch_id="V001",
        source_volume=1,
        source_unit_ids=("U0001", "U0002"),
        entities=(entity,),
        facts=(fact,),
        relationships=(),
        knowledge=(),
        events=(),
        phases=(),
    )
    from overlord_worldsim.canon.loader import apply_extraction_batch

    connection = open_canon_db(db_path)
    try:
        with connection:
            apply_extraction_batch(connection, batch)
        with connection:
            apply_extraction_batch(connection, batch)
        assert connection.execute("SELECT COUNT(*) FROM entities").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM fact_evidence").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM extraction_batches").fetchone()[0] == 1
    finally:
        connection.close()


def test_apply_extraction_batch_keeps_shared_entities(tmp_path: Path) -> None:
    from overlord_worldsim.canon.extract_model import (
        Confidence,
        DatePrecision,
        Entity,
        EntityKind,
        ExtractionBatch,
        Fact,
    )
    from overlord_worldsim.canon.loader import apply_extraction_batch

    db_path = _build(tmp_path)
    entity = Entity(
        entity_id="E0001",
        name="鲁迪乌斯",
        aliases=(),
        kind=EntityKind.CHARACTER,
        introduced_volume=1,
        introduced_line=4,
        description="",
    )
    batch_a = ExtractionBatch(
        batch_id="V001",
        source_volume=1,
        source_unit_ids=("U0001", "U0002"),
        entities=(entity,),
        facts=(),
        relationships=(),
        knowledge=(),
        events=(),
        phases=(),
    )
    fact_b = Fact(
        fact_id="F0002",
        entity_id="E0001",
        predicate="身份",
        object_value="转生者",
        start_date=None,
        end_date=None,
        date_precision=DatePrecision.UNKNOWN,
        evidence_volumes=(1,),
        evidence_lines=((4, 6),),
        confidence=Confidence.EXPLICIT,
        visible_from_volume=1,
        visible_to_volume=None,
    )
    batch_b = ExtractionBatch(
        batch_id="V002",
        source_volume=1,
        source_unit_ids=("U0001",),
        entities=(entity,),
        facts=(fact_b,),
        relationships=(),
        knowledge=(),
        events=(),
        phases=(),
    )
    connection = open_canon_db(db_path)
    try:
        with connection:
            apply_extraction_batch(connection, batch_a)
        with connection:
            apply_extraction_batch(connection, batch_b)
        assert connection.execute("SELECT COUNT(*) FROM entities").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM extraction_batches").fetchone()[0] == 2
    finally:
        connection.close()
