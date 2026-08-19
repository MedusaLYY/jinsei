"""Tests for the canon extraction data model and canonical date helpers."""

from __future__ import annotations

import pytest

from overlord_worldsim.canon.extract_model import (
    CharacterPhase,
    Confidence,
    DatePrecision,
    Entity,
    EntityKind,
    ExtractionBatch,
    Fact,
    Knowledge,
    Relationship,
    RelationshipKind,
    TimelineEvent,
    canon_date_sort_key,
    parse_canon_date,
)


def test_parse_canon_date() -> None:
    assert parse_canon_date("408-1") == (408, 1)
    assert parse_canon_date("426-12") == (426, 12)
    assert parse_canon_date(None) is None


def test_parse_canon_date_rejects_bad_input() -> None:
    for bad in ("408", "408-13", "408-0", "abc", "408-1-1"):
        with pytest.raises(ValueError, match="canon date"):
            parse_canon_date(bad)


def test_canon_date_sort_key() -> None:
    assert canon_date_sort_key("408-1") < canon_date_sort_key("408-12")
    assert canon_date_sort_key("408-12") < canon_date_sort_key("409-1")
    assert canon_date_sort_key("409-1") < canon_date_sort_key("426-12")


def test_entity_round_trip() -> None:
    entity = Entity(
        entity_id="E0001",
        name="鲁迪乌斯·格雷拉特",
        aliases=("鲁迪", "ルーデウス"),
        kind=EntityKind.CHARACTER,
        introduced_volume=1,
        introduced_line=230,
        description="主角。",
    )
    document = entity.to_json()
    assert document["entity_id"] == "E0001"
    assert Entity.from_json(document) == entity


def test_fact_round_trip() -> None:
    fact = Fact(
        fact_id="F0001",
        entity_id="E0001",
        predicate="出生",
        object_value="亚尔斯",
        start_date="408-4",
        end_date=None,
        date_precision=DatePrecision.EXACT,
        evidence_volumes=(1,),
        evidence_lines=((230, 235),),
        confidence=Confidence.EXPLICIT,
        visible_from_volume=1,
        visible_to_volume=None,
    )
    assert Fact.from_json(fact.to_json()) == fact


def test_extraction_batch_json_round_trip() -> None:
    batch = ExtractionBatch(
        batch_id="batch-1",
        source_volume=1,
        source_unit_ids=("U0002",),
        entities=(),
        facts=(),
        relationships=(),
        knowledge=(),
        events=(),
        phases=(),
    )
    document = batch.to_json()
    assert ExtractionBatch.from_json(document) == batch


def test_relationship_kind_values() -> None:
    assert RelationshipKind.FAMILY.value == "FAMILY"
    assert RelationshipKind.FRIEND.value == "FRIEND"
    assert RelationshipKind.ENEMY.value == "ENEMY"
    assert RelationshipKind.ROMANTIC.value == "ROMANTIC"
    assert RelationshipKind.MENTOR.value == "MENTOR"
    assert RelationshipKind.ORGANIZATIONAL.value == "ORGANIZATIONAL"
    assert RelationshipKind.UNKNOWN.value == "UNKNOWN"


def test_relationship_default_kind() -> None:
    relationship = Relationship(
        relationship_id="R0001",
        source_id="E0001",
        target_id="E0002",
        rel_type="父子",
        evidence_volumes=(1,),
        evidence_lines=((300, 305),),
        confidence=Confidence.EXPLICIT,
        visible_from_volume=1,
    )
    assert relationship.kind is RelationshipKind.UNKNOWN


def test_knowledge_round_trip() -> None:
    knowledge = Knowledge(
        knowledge_id="K0001",
        owner_id="E0001",
        fact_id="F0001",
        certainty=Confidence.STRONG_INFERENCE,
        note="鲁迪从利希德口中得知。",
    )
    assert Knowledge.from_json(knowledge.to_json()) == knowledge


def test_timeline_event_round_trip() -> None:
    event = TimelineEvent(
        event_id="T0001",
        title="魔大陆大转移",
        description="菲托亚领被转移。",
        date="408-4",
        date_precision=DatePrecision.EXACT,
        participants=("E0001",),
        evidence_volumes=(6,),
        evidence_lines=((100, 120),),
    )
    assert TimelineEvent.from_json(event.to_json()) == event


def test_character_phase_round_trip() -> None:
    phase = CharacterPhase(
        phase_id="P0001",
        character_id="E0001",
        name="幼年期",
        start_date="408-4",
        end_date="410-1",
        date_precision=DatePrecision.YEAR_ONLY,
        summary="布埃纳村的生活。",
        evidence_volumes=(1,),
        evidence_lines=((10, 20),),
    )
    assert CharacterPhase.from_json(phase.to_json()) == phase
