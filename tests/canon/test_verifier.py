"""Tests for the deterministic extraction verifier."""

from __future__ import annotations

from overlord_worldsim.canon.extract_model import (
    CharacterPhase,
    Confidence,
    DatePrecision,
    Entity,
    EntityKind,
    ExtractionBatch,
    Fact,
    Relationship,
    TimelineEvent,
)
from overlord_worldsim.canon.parse import parse_source
from overlord_worldsim.canon.verifier import verify_batch

CORPUS = (
    "第一卷 幼年期 序章\n"
    "\n"
    "    希露菲的头发是银色的。\n"
    "\n"
    "第一卷 幼年期 第一话「测试章节」\n"
    "\n"
    "    保罗是鲁迪乌斯的父亲。\n"
    "\n"
    "    鲁迪乌斯四岁。\n"
)

DOC = parse_source(CORPUS, source_name="corpus.txt")

ENTITY = Entity(
    entity_id="E0001",
    name="鲁迪乌斯·格雷拉特",
    aliases=("鲁迪",),
    kind=EntityKind.CHARACTER,
    introduced_volume=1,
    introduced_line=4,
    description="主角。",
)


def _valid_fact() -> Fact:
    return Fact(
        fact_id="F0001",
        entity_id="E0001",
        predicate="年纪",
        object_value="四岁",
        start_date="408-1",
        end_date=None,
        date_precision=DatePrecision.YEAR_ONLY,
        evidence_volumes=(1,),
        evidence_lines=((9, 9),),
        confidence=Confidence.EXPLICIT,
        visible_from_volume=1,
        visible_to_volume=None,
    )


def _batch(
    *,
    entities: tuple[Entity, ...] = (ENTITY,),
    facts: tuple[Fact, ...] = (_valid_fact(),),
    relationships: tuple[Relationship, ...] = (),
    events: tuple[TimelineEvent, ...] = (),
    phases: tuple[CharacterPhase, ...] = (),
) -> ExtractionBatch:
    return ExtractionBatch(
        batch_id="b1",
        source_volume=1,
        source_unit_ids=("U0001", "U0002"),
        entities=entities,
        facts=facts,
        relationships=relationships,
        knowledge=(),
        events=events,
        phases=phases,
    )


def test_verify_batch_accepts_valid_batch() -> None:
    report = verify_batch(_batch(), DOC)
    assert report.is_clean
    assert report.errors == ()


def test_verify_batch_rejects_evidence_outside_units() -> None:
    fact = _valid_fact()
    fact = Fact(**{**fact.to_json(), "evidence_lines": ((100, 101),)})
    report = verify_batch(_batch(facts=(fact,)), DOC)
    assert not report.is_clean
    assert any("evidence" in error.message for error in report.errors)


def test_verify_batch_rejects_evidence_in_wrong_volume() -> None:
    fact = _valid_fact()
    fact = Fact(**{**fact.to_json(), "evidence_volumes": (2,)})
    report = verify_batch(_batch(facts=(fact,)), DOC)
    assert not report.is_clean
    assert any("volume" in error.message for error in report.errors)


def test_verify_batch_rejects_entity_without_volume_one_introduction() -> None:
    entity = Entity(
        entity_id="E0001",
        name="希露菲",
        aliases=(),
        kind=EntityKind.CHARACTER,
        introduced_volume=3,
        introduced_line=4,
        description="",
    )
    report = verify_batch(_batch(entities=(entity,)), DOC)
    assert not report.is_clean
    assert any("introduced_volume" in error.message for error in report.errors)


def test_verify_batch_rejects_entity_introduction_line_not_in_volume() -> None:
    entity = Entity(
        entity_id="E0001",
        name="希露菲",
        aliases=(),
        kind=EntityKind.CHARACTER,
        introduced_volume=1,
        introduced_line=100,
        description="",
    )
    report = verify_batch(_batch(entities=(entity,)), DOC)
    assert not report.is_clean
    assert any("introduced_line" in error.message for error in report.errors)


def test_verify_batch_rejects_duplicate_entity_ids() -> None:
    report = verify_batch(_batch(entities=(ENTITY, ENTITY)), DOC)
    assert not report.is_clean
    assert any("duplicate" in error.message.lower() for error in report.errors)


def test_verify_batch_rejects_future_visible_from_volume() -> None:
    fact = _valid_fact()
    fact = Fact(**{**fact.to_json(), "visible_from_volume": 4})
    report = verify_batch(_batch(facts=(fact,)), DOC)
    assert not report.is_clean
    assert any("visible_from_volume" in error.message for error in report.errors)


def test_verify_batch_rejects_relationship_to_unknown_entity() -> None:
    relationship = Relationship(
        relationship_id="R0001",
        source_id="E0001",
        target_id="E9999",
        rel_type="父子",
        evidence_volumes=(1,),
        evidence_lines=((8, 8),),
        confidence=Confidence.EXPLICIT,
        visible_from_volume=1,
    )
    report = verify_batch(_batch(relationships=(relationship,)), DOC)
    assert not report.is_clean
    assert any("target" in error.message for error in report.errors)


def test_verify_batch_rejects_invalid_dates() -> None:
    fact = _valid_fact()
    fact = Fact(**{**fact.to_json(), "start_date": "999-99"})
    report = verify_batch(_batch(facts=(fact,)), DOC)
    assert not report.is_clean
    assert any("date" in error.message for error in report.errors)


def test_verify_batch_rejects_event_outside_source_volume() -> None:
    event = TimelineEvent(
        event_id="T0001",
        title="大转移",
        description="",
        date="408-4",
        date_precision=DatePrecision.EXACT,
        participants=("E0001",),
        evidence_volumes=(6,),
        evidence_lines=((10, 12),),
    )
    report = verify_batch(_batch(events=(event,)), DOC)
    assert not report.is_clean
    assert any("volume" in error.message for error in report.errors)


def test_verify_batch_rejects_phase_date_order() -> None:
    phase = CharacterPhase(
        phase_id="P0001",
        character_id="E0001",
        name="幼年期",
        start_date="410-1",
        end_date="408-1",
        date_precision=DatePrecision.EXACT,
        summary="",
        evidence_volumes=(1,),
        evidence_lines=((4, 4),),
    )
    report = verify_batch(_batch(phases=(phase,)), DOC)
    assert not report.is_clean
    assert any("start_date" in error.message for error in report.errors)


def test_verify_batch_is_deterministic() -> None:
    first = verify_batch(_batch(), DOC)
    second = verify_batch(_batch(), DOC)
    assert first == second
