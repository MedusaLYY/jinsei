"""Read-only query API over the canon database (10 interfaces).

Every function is a pure read: no writes, no time, no RNG. All queries apply
the requester's knowledge projection: facts are visible only within their
recorded volume window and (when a date is given) their date interval.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from overlord_worldsim.canon.extract_model import canon_date_sort_key
from overlord_worldsim.canon.loader import open_canon_db

_FACT_COLUMNS = (
    "fact_id, entity_id, predicate, object_value, start_date, end_date, "
    "date_precision, confidence, visible_from_volume, visible_to_volume"
)


def _select_facts(
    connection: object,
    *,
    at_volume: int | None,
    at_date: str | None,
    entity_id: str | None = None,
) -> list[dict[str, object]]:
    clauses = []
    parameters: list[object] = []
    if entity_id is not None:
        clauses.append("entity_id = ?")
        parameters.append(entity_id)
    if at_volume is not None:
        clauses.append("visible_from_volume <= ?")
        parameters.append(at_volume)
        clauses.append("(visible_to_volume IS NULL OR visible_to_volume >= ?)")
        parameters.append(at_volume)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = connection.execute(  # type: ignore[attr-defined]
        f"SELECT {_FACT_COLUMNS} FROM facts{where} ORDER BY fact_id", parameters
    ).fetchall()
    facts = [dict(row) for row in rows]
    if at_date is not None:
        key = canon_date_sort_key(at_date)
        facts = [
            fact
            for fact in facts
            if (fact["start_date"] is None or canon_date_sort_key(fact["start_date"]) <= key)
            and (fact["end_date"] is None or canon_date_sort_key(fact["end_date"]) >= key)
        ]
    return facts


def get_character(
    db_path: Path,
    character_id: str,
    *,
    at_volume: int | None = None,
    at_date: str | None = None,
) -> dict[str, object] | None:
    """Entity record plus facts visible at the requested time."""
    connection = open_canon_db(db_path)
    try:
        row = connection.execute(
            "SELECT entity_id, name, aliases, kind, introduced_volume, "
            "introduced_line, description FROM entities WHERE entity_id = ?",
            (character_id,),
        ).fetchone()
        if row is None:
            return None
        entity = dict(row)
        entity["aliases"] = json.loads(entity["aliases"])
        facts = _select_facts(
            connection, at_volume=at_volume, at_date=at_date, entity_id=character_id
        )
        return {"entity": entity, "facts": facts}
    finally:
        connection.close()


def get_character_phase(
    db_path: Path,
    character_id: str,
    *,
    at_date: str | None = None,
) -> list[dict[str, object]]:
    """Character phases, optionally filtered by the date the phase covers."""
    connection = open_canon_db(db_path)
    try:
        rows = connection.execute(
            "SELECT phase_id, character_id, name, start_date, end_date, "
            "date_precision, summary FROM character_phases "
            "WHERE character_id = ? ORDER BY start_date",
            (character_id,),
        ).fetchall()
        phases = [dict(row) for row in rows]
        if at_date is not None:
            key = canon_date_sort_key(at_date)
            phases = [
                phase
                for phase in phases
                if (phase["start_date"] is None or canon_date_sort_key(phase["start_date"]) <= key)
                and (phase["end_date"] is None or canon_date_sort_key(phase["end_date"]) >= key)
            ]
        return phases
    finally:
        connection.close()


def _location_facts(
    connection: object,
    character_id: str,
    *,
    at_volume: int | None,
    at_date: str | None,
) -> list[dict[str, object]]:
    """Facts whose object_value names a registered LOCATION entity."""
    rows = connection.execute(  # type: ignore[attr-defined]
        "SELECT name FROM entities WHERE kind = 'LOCATION'"
    ).fetchall()
    location_names = {row["name"] for row in rows}
    facts = _select_facts(connection, at_volume=at_volume, at_date=at_date, entity_id=character_id)
    return [fact for fact in facts if fact["object_value"] in location_names]


def get_character_location(
    db_path: Path,
    character_id: str,
    *,
    at_volume: int | None = None,
    at_date: str | None = None,
) -> list[dict[str, object]]:
    """Where the character is known to be at the requested time."""
    connection = open_canon_db(db_path)
    try:
        return _location_facts(connection, character_id, at_volume=at_volume, at_date=at_date)
    finally:
        connection.close()


def get_character_knowledge(
    db_path: Path,
    character_id: str,
    *,
    at_volume: int | None = None,
    at_date: str | None = None,
    topic: str | None = None,
) -> list[dict[str, object]]:
    """What the character knows: knowledge rows joined with their facts."""
    connection = open_canon_db(db_path)
    try:
        rows = connection.execute(
            "SELECT k.knowledge_id, k.owner_id, k.fact_id, k.certainty, k.note, "
            f"f.predicate, f.object_value, {_FACT_COLUMNS.replace('fact_id, ', 'f.fact_id, ')} "
            "FROM knowledge k JOIN facts f ON f.fact_id = k.fact_id WHERE k.owner_id = ?",
            (character_id,),
        ).fetchall()
        knowledge = [dict(row) for row in rows]
        if topic is not None:
            knowledge = [item for item in knowledge if item["predicate"] == topic]
        result: list[dict[str, object]] = []
        for item in knowledge:
            visible = True
            if at_volume is not None:
                if item["visible_from_volume"] > at_volume:
                    visible = False
                if item["visible_to_volume"] is not None and item["visible_to_volume"] < at_volume:
                    visible = False
            if at_date is not None:
                key = canon_date_sort_key(at_date)
                if item["start_date"] is not None and canon_date_sort_key(item["start_date"]) > key:
                    visible = False
                if item["end_date"] is not None and canon_date_sort_key(item["end_date"]) < key:
                    visible = False
            if visible:
                result.append(item)
        return result
    finally:
        connection.close()


def get_relationship(
    db_path: Path,
    character_a: str,
    character_b: str,
    *,
    at_volume: int | None = None,
    at_date: str | None = None,
) -> list[dict[str, object]]:
    """Directed relationship facts from A to B (and B to A)."""
    connection = open_canon_db(db_path)
    try:
        rows = connection.execute(
            "SELECT relationship_id, source_id, target_id, rel_type, kind, confidence, "
            "visible_from_volume, visible_to_volume FROM relationships "
            "WHERE (source_id = ? AND target_id = ?) OR (source_id = ? AND target_id = ?) "
            "ORDER BY relationship_id",
            (character_a, character_b, character_b, character_a),
        ).fetchall()
        relationships = [dict(row) for row in rows]
        if at_volume is not None:
            relationships = [
                rel
                for rel in relationships
                if rel["visible_from_volume"] <= at_volume
                and (rel["visible_to_volume"] is None or rel["visible_to_volume"] >= at_volume)
            ]
        return relationships
    finally:
        connection.close()


def get_canon_events(
    db_path: Path,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    entity_id: str | None = None,
) -> list[dict[str, object]]:
    """Timeline events, optionally filtered by date window and participants."""
    connection = open_canon_db(db_path)
    try:
        if entity_id is not None:
            rows = connection.execute(
                "SELECT e.event_id, e.title, e.description, e.date, e.date_precision "
                "FROM timeline_events e JOIN event_participants p ON p.event_id = e.event_id "
                "WHERE p.entity_id = ? ORDER BY e.date",
                (entity_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT event_id, title, description, date, date_precision "
                "FROM timeline_events ORDER BY date"
            ).fetchall()
        events = [dict(row) for row in rows]
        if start_date is not None:
            key = canon_date_sort_key(start_date)
            events = [
                event
                for event in events
                if event["date"] is not None and canon_date_sort_key(event["date"]) >= key
            ]
        if end_date is not None:
            key = canon_date_sort_key(end_date)
            events = [
                event
                for event in events
                if event["date"] is not None and canon_date_sort_key(event["date"]) <= key
            ]
        return events
    finally:
        connection.close()


def get_location(
    db_path: Path,
    location_id: str,
    *,
    at_volume: int | None = None,
    at_date: str | None = None,
) -> list[dict[str, object]]:
    """Facts about a LOCATION-kind entity, if that entity is a location."""
    connection = open_canon_db(db_path)
    try:
        row = connection.execute(
            "SELECT name FROM entities WHERE entity_id = ? AND kind = 'LOCATION'",
            (location_id,),
        ).fetchone()
        if row is None:
            return []
        name = row["name"]
        facts = _select_facts(connection, at_volume=at_volume, at_date=at_date)
        return [
            fact
            for fact in facts
            if fact["entity_id"] == location_id or fact["object_value"] == name
        ]
    finally:
        connection.close()


def get_fact(
    db_path: Path,
    *,
    fact_id: str | None = None,
    entity_id: str | None = None,
    predicate: str | None = None,
) -> dict[str, object] | None:
    """One fact with verbatim evidence text from the original chunks."""
    connection = open_canon_db(db_path)
    try:
        if fact_id is not None:
            rows = connection.execute(
                f"SELECT {_FACT_COLUMNS} FROM facts WHERE fact_id = ?", (fact_id,)
            ).fetchall()
        elif entity_id is not None and predicate is not None:
            rows = connection.execute(
                f"SELECT {_FACT_COLUMNS} FROM facts WHERE entity_id = ? AND predicate = ?",
                (entity_id, predicate),
            ).fetchall()
        else:
            raise ValueError("get_fact requires fact_id or (entity_id and predicate)")
        if not rows:
            return None
        fact = dict(rows[0])
        evidence: list[str] = []
        for volume_no, start, end in connection.execute(
            "SELECT volume_no, line_start, line_end FROM fact_evidence WHERE fact_id = ? "
            "ORDER BY volume_no, line_start",
            (fact_id,),
        ).fetchall():
            chunks = connection.execute(
                "SELECT text FROM chunks WHERE volume_no = ? AND source_start_line <= ? "
                "AND source_end_line >= ? ORDER BY source_start_line",
                (volume_no, start, end),
            ).fetchall()
            evidence.extend(chunk["text"] for chunk in chunks)
        fact["evidence_text"] = evidence
        return fact
    finally:
        connection.close()


def get_canon_rudeus_state(
    db_path: Path,
    *,
    at_volume: int | None = None,
    at_date: str | None = None,
    rudeus_entity_id: str | None = None,
) -> dict[str, object] | None:
    """The canonical Rudeus state: entity, phase, location, age, and facts."""
    connection = open_canon_db(db_path)
    try:
        if rudeus_entity_id is None:
            row = connection.execute(
                "SELECT entity_id FROM entities WHERE name = '鲁迪乌斯·格雷拉特' "
                "ORDER BY entity_id LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            rudeus_entity_id = row["entity_id"]
        character = get_character(db_path, rudeus_entity_id, at_volume=at_volume, at_date=at_date)
        if character is None:
            return None
        facts: list[dict[str, object]] = cast(list[dict[str, object]], character["facts"])
        age = next((fact for fact in facts if fact["predicate"] == "年纪"), None)
        location_facts = _location_facts(
            connection, rudeus_entity_id, at_volume=at_volume, at_date=at_date
        )
        location = location_facts[-1]["object_value"] if location_facts else None
        phases = get_character_phase(db_path, rudeus_entity_id, at_date=at_date)
        phase = phases[-1]["name"] if phases else None
        return {
            "entity": character["entity"],
            "age": age,
            "location": location,
            "phase": phase,
            "facts": [fact["predicate"] for fact in facts],
        }
    finally:
        connection.close()
