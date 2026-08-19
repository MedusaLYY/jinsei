"""Canon database schema and loader (data/db/canon.sqlite3)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from overlord_worldsim.canon.extract_model import ExtractionBatch
from overlord_worldsim.canon.model import Volume
from overlord_worldsim.canon.parse import ParsedDocument

SCHEMA_VERSION = "1.0.0"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS volumes (
    volume_no INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    period TEXT NOT NULL,
    canon_layer TEXT NOT NULL DEFAULT 'CORE'
);
CREATE TABLE IF NOT EXISTS units (
    unit_id TEXT PRIMARY KEY,
    volume_no INTEGER REFERENCES volumes(volume_no),
    canon_layer TEXT NOT NULL,
    kind TEXT NOT NULL,
    raw_title TEXT NOT NULL,
    title TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    in_universe INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_units_volume ON units(volume_no);
CREATE TABLE IF NOT EXISTS scenes (
    scene_id TEXT PRIMARY KEY,
    unit_id TEXT NOT NULL REFERENCES units(unit_id),
    break_line INTEGER,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scenes_unit ON scenes(unit_id);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    unit_id TEXT NOT NULL REFERENCES units(unit_id),
    scene_id TEXT NOT NULL REFERENCES scenes(scene_id),
    volume_no INTEGER REFERENCES volumes(volume_no),
    chapter_title TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    source_start_line INTEGER NOT NULL,
    source_end_line INTEGER NOT NULL,
    text TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    UNIQUE(unit_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS idx_chunks_unit ON chunks(unit_id);
CREATE INDEX IF NOT EXISTS idx_chunks_scene ON chunks(scene_id);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text,
    content='chunks',
    content_rowid='rowid',
    tokenize='trigram'
);
CREATE TABLE IF NOT EXISTS content_hashes (
    kind TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS build_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, text) VALUES (new.rowid, new.text);
END;
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    aliases TEXT NOT NULL,
    kind TEXT NOT NULL,
    introduced_volume INTEGER NOT NULL,
    introduced_line INTEGER NOT NULL,
    description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS facts (
    fact_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    predicate TEXT NOT NULL,
    object_value TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    date_precision TEXT NOT NULL,
    confidence TEXT NOT NULL,
    visible_from_volume INTEGER NOT NULL,
    visible_to_volume INTEGER
);
CREATE TABLE IF NOT EXISTS fact_evidence (
    fact_id TEXT NOT NULL REFERENCES facts(fact_id),
    volume_no INTEGER NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    PRIMARY KEY (fact_id, volume_no, line_start, line_end)
);
CREATE TABLE IF NOT EXISTS relationships (
    relationship_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES entities(entity_id),
    target_id TEXT NOT NULL REFERENCES entities(entity_id),
    rel_type TEXT NOT NULL,
    kind TEXT NOT NULL,
    confidence TEXT NOT NULL,
    visible_from_volume INTEGER NOT NULL,
    visible_to_volume INTEGER
);
CREATE TABLE IF NOT EXISTS relationship_evidence (
    relationship_id TEXT NOT NULL REFERENCES relationships(relationship_id),
    volume_no INTEGER NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    PRIMARY KEY (relationship_id, volume_no, line_start, line_end)
);
CREATE TABLE IF NOT EXISTS knowledge (
    knowledge_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL REFERENCES entities(entity_id),
    fact_id TEXT NOT NULL REFERENCES facts(fact_id),
    certainty TEXT NOT NULL,
    note TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS timeline_events (
    event_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    date TEXT,
    date_precision TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS event_evidence (
    event_id TEXT NOT NULL REFERENCES timeline_events(event_id),
    volume_no INTEGER NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    PRIMARY KEY (event_id, volume_no, line_start, line_end)
);
CREATE TABLE IF NOT EXISTS event_participants (
    event_id TEXT NOT NULL REFERENCES timeline_events(event_id),
    entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    PRIMARY KEY (event_id, entity_id)
);
CREATE TABLE IF NOT EXISTS character_phases (
    phase_id TEXT PRIMARY KEY,
    character_id TEXT NOT NULL REFERENCES entities(entity_id),
    name TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    date_precision TEXT NOT NULL,
    summary TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS phase_evidence (
    phase_id TEXT NOT NULL REFERENCES character_phases(phase_id),
    volume_no INTEGER NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    PRIMARY KEY (phase_id, volume_no, line_start, line_end)
);
CREATE TABLE IF NOT EXISTS volume_dates (
    volume_no INTEGER PRIMARY KEY REFERENCES volumes(volume_no),
    start_date TEXT,
    end_date TEXT
);
CREATE TABLE IF NOT EXISTS extraction_batches (
    batch_id TEXT PRIMARY KEY,
    source_volume INTEGER NOT NULL,
    source_unit_ids TEXT NOT NULL,
    verified_at TEXT NOT NULL
);
"""


def open_canon_db(path: Path) -> sqlite3.Connection:
    """Open the canon database with foreign keys enforced."""
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def build_canon_db(doc: ParsedDocument, db_path: Path, *, sha256: str) -> Path:
    """Build the canon database from a parsed document in one transaction."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(_SCHEMA_SQL)
        connection.execute("DELETE FROM chunks_fts")
        for table in ("chunks", "scenes", "units", "volumes", "content_hashes", "build_meta"):
            connection.execute(f"DELETE FROM {table}")
        connection.executemany(
            "INSERT INTO volumes(volume_no, title, period, canon_layer) VALUES (?, ?, ?, ?)",
            [(v.volume_no, v.title, v.period, "CORE") for v in doc.volumes],
        )
        connection.executemany(
            "INSERT INTO units(unit_id, volume_no, canon_layer, kind, raw_title, title, "
            "start_line, end_line, in_universe) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    u.unit_id,
                    u.volume_no,
                    u.canon_layer,
                    u.kind.value,
                    u.raw_title,
                    u.title,
                    u.start_line,
                    u.end_line,
                    1 if u.in_universe else 0,
                )
                for u in doc.units
            ],
        )
        connection.executemany(
            "INSERT INTO scenes(scene_id, unit_id, break_line, start_line, end_line)"
            " VALUES (?, ?, ?, ?, ?)",
            [(s.scene_id, s.unit_id, s.break_line, s.start_line, s.end_line) for s in doc.scenes],
        )
        ordered = sorted(doc.chunks, key=lambda c: (c.unit_id, c.chunk_id))
        index_by_unit: dict[str, int] = {}
        chunk_rows: list[tuple[object, ...]] = []
        for chunk in ordered:
            index = index_by_unit.get(chunk.unit_id, 0) + 1
            index_by_unit[chunk.unit_id] = index
            chunk_rows.append(
                (
                    chunk.chunk_id,
                    chunk.unit_id,
                    chunk.scene_id,
                    chunk.volume_no,
                    chunk.chapter_title,
                    index,
                    chunk.source_start_line,
                    chunk.source_end_line,
                    chunk.text,
                    chunk.char_count,
                )
            )
        connection.executemany(
            "INSERT INTO chunks(chunk_id, unit_id, scene_id, volume_no, chapter_title, "
            "chunk_index, source_start_line, source_end_line, text, char_count)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            chunk_rows,
        )
        connection.executemany(
            "INSERT INTO content_hashes(kind, sha256) VALUES (?, ?)",
            [("source_txt", sha256), ("schema", SCHEMA_VERSION)],
        )
        connection.executemany(
            "INSERT INTO build_meta(key, value) VALUES (?, ?)",
            [
                ("artifact_version", doc.to_summary()["version"]),
                ("unit_count", str(len(doc.units))),
                ("chunk_count", str(len(doc.chunks))),
            ],
        )
        connection.commit()
    finally:
        connection.close()
    return db_path


def load_volumes(connection: sqlite3.Connection) -> list[Volume]:
    """Read volumes back from the database."""
    rows = connection.execute(
        "SELECT volume_no, title, period FROM volumes ORDER BY volume_no"
    ).fetchall()
    return [
        Volume(
            volume_no=row["volume_no"],
            title=row["title"],
            period=row["period"],
            start_line=0,
            end_line=0,
            part_titles=(),
            unit_ids=(),
        )
        for row in rows
    ]


def apply_extraction_batch(connection: sqlite3.Connection, batch: ExtractionBatch) -> None:
    """Apply (or replace) a verified extraction batch in one transaction.

    Callers must run the verifier (canon.verifier.verify_batch) and only
    apply clean batches. Re-applying the same batch id replaces its rows
    atomically (dependency order, delete-then-insert), so corrected
    candidates can be re-applied without residue.
    """
    import json

    fact_ids = tuple(fact.fact_id for fact in batch.facts)
    relationship_ids = tuple(rel.relationship_id for rel in batch.relationships)
    event_ids = tuple(event.event_id for event in batch.events)
    phase_ids = tuple(phase.phase_id for phase in batch.phases)
    knowledge_ids = tuple(knowledge.knowledge_id for knowledge in batch.knowledge)
    batch_id = batch.batch_id

    def delete_where(table: str, id_column: str, ids: tuple[str, ...]) -> None:
        if ids:
            placeholders = ", ".join("?" for _ in ids)
            connection.execute(f"DELETE FROM {table} WHERE {id_column} IN ({placeholders})", ids)

    delete_where("fact_evidence", "fact_id", fact_ids)
    delete_where("relationship_evidence", "relationship_id", relationship_ids)
    delete_where("event_evidence", "event_id", event_ids)
    delete_where("event_participants", "event_id", event_ids)
    delete_where("phase_evidence", "phase_id", phase_ids)
    delete_where("knowledge", "knowledge_id", knowledge_ids)
    delete_where("knowledge", "fact_id", fact_ids)
    delete_where("facts", "fact_id", fact_ids)
    delete_where("relationships", "relationship_id", relationship_ids)
    delete_where("timeline_events", "event_id", event_ids)
    delete_where("character_phases", "phase_id", phase_ids)
    connection.execute("DELETE FROM extraction_batches WHERE batch_id = ?", (batch_id,))

    connection.execute(
        "INSERT INTO extraction_batches(batch_id, source_volume, source_unit_ids, verified_at) "
        "VALUES (?, ?, ?, ?)",
        (batch_id, batch.source_volume, json.dumps(list(batch.source_unit_ids)), "verified"),
    )
    connection.executemany(
        "INSERT OR REPLACE INTO entities(entity_id, name, aliases, kind, introduced_volume, "
        "introduced_line, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                entity.entity_id,
                entity.name,
                json.dumps(list(entity.aliases), ensure_ascii=False),
                entity.kind.value,
                entity.introduced_volume,
                entity.introduced_line,
                entity.description,
            )
            for entity in batch.entities
        ],
    )
    for fact in batch.facts:
        connection.execute(
            "INSERT INTO facts(fact_id, entity_id, predicate, object_value, start_date, end_date, "
            "date_precision, confidence, visible_from_volume, visible_to_volume) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                fact.fact_id,
                fact.entity_id,
                fact.predicate,
                fact.object_value,
                fact.start_date,
                fact.end_date,
                fact.date_precision.value,
                fact.confidence.value,
                fact.visible_from_volume,
                fact.visible_to_volume,
            ),
        )
        connection.executemany(
            "INSERT INTO fact_evidence(fact_id, volume_no, line_start, line_end) "
            "VALUES (?, ?, ?, ?)",
            [
                (fact.fact_id, volume_no, start, end)
                for volume_no, (start, end) in zip(
                    fact.evidence_volumes, fact.evidence_lines, strict=True
                )
            ],
        )
    for relationship in batch.relationships:
        connection.execute(
            "INSERT INTO relationships(relationship_id, source_id, target_id, rel_type, kind, "
            "confidence, visible_from_volume, visible_to_volume) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                relationship.relationship_id,
                relationship.source_id,
                relationship.target_id,
                relationship.rel_type,
                relationship.kind.value,
                relationship.confidence.value,
                relationship.visible_from_volume,
                relationship.visible_to_volume,
            ),
        )
        connection.executemany(
            "INSERT INTO relationship_evidence(relationship_id, volume_no, line_start, line_end) "
            "VALUES (?, ?, ?, ?)",
            [
                (relationship.relationship_id, volume_no, start, end)
                for volume_no, (start, end) in zip(
                    relationship.evidence_volumes, relationship.evidence_lines, strict=True
                )
            ],
        )
    connection.executemany(
        "INSERT INTO knowledge(knowledge_id, owner_id, fact_id, certainty, note) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            (
                knowledge.knowledge_id,
                knowledge.owner_id,
                knowledge.fact_id,
                knowledge.certainty.value,
                knowledge.note,
            )
            for knowledge in batch.knowledge
        ],
    )
    for event in batch.events:
        connection.execute(
            "INSERT INTO timeline_events(event_id, title, description, date, date_precision) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                event.event_id,
                event.title,
                event.description,
                event.date,
                event.date_precision.value,
            ),
        )
        connection.executemany(
            "INSERT INTO event_evidence(event_id, volume_no, line_start, line_end) "
            "VALUES (?, ?, ?, ?)",
            [
                (event.event_id, volume_no, start, end)
                for volume_no, (start, end) in zip(
                    event.evidence_volumes, event.evidence_lines, strict=True
                )
            ],
        )
        connection.executemany(
            "INSERT INTO event_participants(event_id, entity_id) VALUES (?, ?)",
            [(event.event_id, participant) for participant in event.participants],
        )
    for phase in batch.phases:
        connection.execute(
            "INSERT INTO character_phases(phase_id, character_id, name, start_date, end_date, "
            "date_precision, summary) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                phase.phase_id,
                phase.character_id,
                phase.name,
                phase.start_date,
                phase.end_date,
                phase.date_precision.value,
                phase.summary,
            ),
        )
        connection.executemany(
            "INSERT INTO phase_evidence(phase_id, volume_no, line_start, line_end) "
            "VALUES (?, ?, ?, ?)",
            [
                (phase.phase_id, volume_no, start, end)
                for volume_no, (start, end) in zip(
                    phase.evidence_volumes, phase.evidence_lines, strict=True
                )
            ],
        )
