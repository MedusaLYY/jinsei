"""Edge tests covering the remaining verifier and query branches."""

from __future__ import annotations

from pathlib import Path

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
    facts: tuple[Fact, ...] = (_valid_fact(),),
    relationships: tuple[Relationship, ...] = (),
    events: tuple[TimelineEvent, ...] = (),
    phases: tuple[CharacterPhase, ...] = (),
    source_volume: int = 1,
) -> ExtractionBatch:
    return ExtractionBatch(
        batch_id="b1",
        source_volume=source_volume,
        source_unit_ids=("U0001", "U0002"),
        entities=(ENTITY,),
        facts=facts,
        relationships=relationships,
        knowledge=(),
        events=events,
        phases=phases,
    )


def test_verification_error_to_json() -> None:
    report = verify_batch(
        _batch(
            facts=(
                Fact(
                    **{
                        **_valid_fact().to_json(),
                        "evidence_volumes": (1,),
                        "evidence_lines": ((9, 9), (10, 10)),
                    }
                ),
            )
        ),
        DOC,
    )
    assert not report.is_clean
    payload = report.errors[0].to_json()
    assert set(payload) == {"code", "path", "message"}


def test_verifier_rejects_evidence_arity_mismatch() -> None:
    fact = Fact(**{**_valid_fact().to_json(), "evidence_lines": ((9, 9), (10, 10))})
    report = verify_batch(_batch(facts=(fact,)), DOC)
    assert any(error.code == "evidence_arity" for error in report.errors)


def test_verifier_rejects_reversed_evidence_range() -> None:
    fact = Fact(**{**_valid_fact().to_json(), "evidence_lines": ((8, 7),)})
    report = verify_batch(_batch(facts=(fact,)), DOC)
    assert any(error.code == "evidence_order" for error in report.errors)


def test_verifier_rejects_fact_unknown_entity() -> None:
    fact = Fact(**{**_valid_fact().to_json(), "entity_id": "E9999"})
    report = verify_batch(_batch(facts=(fact,)), DOC)
    assert any(error.code == "fact_entity" for error in report.errors)


def test_verifier_rejects_visible_window_inverted() -> None:
    fact = Fact(**{**_valid_fact().to_json(), "visible_from_volume": 2, "visible_to_volume": 1})
    report = verify_batch(_batch(facts=(fact,)), DOC)
    assert any(error.code == "fact_visible_window" for error in report.errors)


def test_verifier_rejects_relationship_unknown_source() -> None:
    relationship = Relationship(
        relationship_id="R0001",
        source_id="E9999",
        target_id="E0001",
        rel_type="父子",
        evidence_volumes=(1,),
        evidence_lines=((8, 8),),
        confidence=Confidence.EXPLICIT,
        visible_from_volume=1,
    )
    report = verify_batch(_batch(relationships=(relationship,)), DOC)
    assert any(error.code == "relationship_source" for error in report.errors)


def test_verifier_rejects_event_unknown_participant_and_bad_date() -> None:
    event = TimelineEvent(
        event_id="T0001",
        title="搬家",
        description="",
        date="999-99",
        date_precision=DatePrecision.EXACT,
        participants=("E9999",),
        evidence_volumes=(1,),
        evidence_lines=((8, 8),),
    )
    report = verify_batch(_batch(events=(event,)), DOC)
    assert any(error.code == "event_participant" for error in report.errors)
    assert any(error.code == "event_date" for error in report.errors)


def test_verifier_rejects_phase_unknown_character() -> None:
    phase = CharacterPhase(
        phase_id="P0001",
        character_id="E9999",
        name="幼年期",
        start_date="408-1",
        end_date=None,
        date_precision=DatePrecision.YEAR_ONLY,
        summary="",
        evidence_volumes=(1,),
        evidence_lines=((4, 4),),
    )
    report = verify_batch(_batch(phases=(phase,)), DOC)
    assert any(error.code == "phase_character" for error in report.errors)


def test_verifier_rejects_unparsed_source_volume() -> None:
    report = verify_batch(_batch(source_volume=9), DOC)
    assert any(error.code == "batch_volume" for error in report.errors)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    from overlord_worldsim.canon.loader import apply_extraction_batch, build_canon_db, open_canon_db

    facts: list[Fact] = []
    for index in range(1, 6):
        facts.append(
            Fact(
                fact_id=f"F{index:04d}",
                entity_id="E0001",
                predicate="年纪",
                object_value=str(index),
                start_date=f"4{index:02d}-1",
                end_date=f"4{index + 1:02d}-1",
                date_precision=DatePrecision.YEAR_ONLY,
                evidence_volumes=(1,),
                evidence_lines=((9, 9),),
                confidence=Confidence.EXPLICIT,
                visible_from_volume=index,
                visible_to_volume=index,
            )
        )
    batch = ExtractionBatch(
        batch_id="b2",
        source_volume=1,
        source_unit_ids=("U0001", "U0002"),
        entities=(
            ENTITY,
            Entity(
                entity_id="E0002",
                name="诺伦",
                aliases=(),
                kind=EntityKind.CHARACTER,
                introduced_volume=1,
                introduced_line=8,
                description="",
            ),
        ),
        facts=tuple(facts),
        relationships=(),
        knowledge=(),
        events=(),
        phases=(
            CharacterPhase(
                phase_id="P0001",
                character_id="E0001",
                name="幼年期",
                start_date="401-1",
                end_date="405-1",
                date_precision=DatePrecision.YEAR_ONLY,
                summary="",
                evidence_volumes=(1,),
                evidence_lines=((4, 4),),
            ),
            CharacterPhase(
                phase_id="P0002",
                character_id="E0001",
                name="少年期",
                start_date="406-1",
                end_date=None,
                date_precision=DatePrecision.YEAR_ONLY,
                summary="",
                evidence_volumes=(1,),
                evidence_lines=((4, 4),),
            ),
        ),
    )
    path = build_canon_db(DOC, tmp_path / "canon.sqlite3", sha256="abc123")
    connection = open_canon_db(path)
    try:
        with connection:
            apply_extraction_batch(connection, batch)
    finally:
        connection.close()
    return path


def test_get_character_filters_by_date(db_path: Path) -> None:
    from overlord_worldsim.canon.query import get_character

    character = get_character(db_path, "E0001", at_volume=3, at_date="403-6")
    assert {fact["predicate"] for fact in character["facts"]} == {"年纪"}


def test_get_character_phase_filters_by_date(db_path: Path) -> None:
    from overlord_worldsim.canon.query import get_character_phase

    phases = get_character_phase(db_path, "E0001", at_date="403-6")
    assert [phase["name"] for phase in phases] == ["幼年期"]
    later = get_character_phase(db_path, "E0001", at_date="408-1")
    assert [phase["name"] for phase in later] == ["少年期"]


def test_get_character_knowledge_projection_filters(db_path: Path) -> None:
    from overlord_worldsim.canon.query import get_character_knowledge

    empty = get_character_knowledge(db_path, "E0001")
    assert empty == []


def test_get_character_knowledge_volume_window(db_path: Path) -> None:
    from overlord_worldsim.canon.loader import apply_extraction_batch, open_canon_db
    from overlord_worldsim.canon.query import get_character_knowledge

    knowledge = tuple(
        Knowledge(
            knowledge_id=f"K{index:04d}",
            owner_id="E0002",
            fact_id=f"F{index:04d}",
            certainty=Confidence.EXPLICIT,
            note="",
        )
        for index in range(1, 6)
    )
    connection = open_canon_db(db_path)
    try:
        with connection:
            apply_extraction_batch(
                connection,
                ExtractionBatch(
                    batch_id="b5",
                    source_volume=1,
                    source_unit_ids=(),
                    entities=(),
                    facts=(),
                    relationships=(),
                    knowledge=knowledge,
                    events=(),
                    phases=(),
                ),
            )
    finally:
        connection.close()
    early = get_character_knowledge(db_path, "E0002", at_volume=2)
    assert {item["fact_id"] for item in early} == {"F0002"}
    mid = get_character_knowledge(db_path, "E0002", at_volume=3, at_date="403-6")
    assert {item["fact_id"] for item in mid} == {"F0003"}
    topic = get_character_knowledge(db_path, "E0002", topic="年纪")
    assert len(topic) == 5
    other_topic = get_character_knowledge(db_path, "E0002", topic="地位")
    assert other_topic == []


def test_get_relationship_filters_by_volume(db_path: Path) -> None:
    from overlord_worldsim.canon.query import get_relationship

    relationship = Relationship(
        relationship_id="R0002",
        source_id="E0001",
        target_id="E0002",
        rel_type="兄妹",
        evidence_volumes=(1,),
        evidence_lines=((8, 8),),
        confidence=Confidence.EXPLICIT,
        visible_from_volume=2,
        visible_to_volume=3,
    )
    from overlord_worldsim.canon.loader import apply_extraction_batch, open_canon_db

    connection = open_canon_db(db_path)
    try:
        with connection:
            apply_extraction_batch(
                connection,
                ExtractionBatch(
                    batch_id="b3",
                    source_volume=1,
                    source_unit_ids=(),
                    entities=(),
                    facts=(),
                    relationships=(relationship,),
                    knowledge=(),
                    events=(),
                    phases=(),
                ),
            )
    finally:
        connection.close()
    assert get_relationship(db_path, "E0001", "E0002", at_volume=1) == []
    assert len(get_relationship(db_path, "E0001", "E0002", at_volume=2)) == 1
    assert get_relationship(db_path, "E0001", "E0002", at_volume=4) == []


def test_get_canon_events_end_date_filter(db_path: Path) -> None:
    from overlord_worldsim.canon.query import get_canon_events

    assert get_canon_events(db_path, end_date="404-1") == []


def test_get_fact_requires_lookup_arguments(db_path: Path) -> None:
    from overlord_worldsim.canon.query import get_fact

    with pytest.raises(ValueError, match="requires"):
        get_fact(db_path)


def test_get_canon_rudeus_state_without_location_or_age(db_path: Path) -> None:
    from overlord_worldsim.canon.loader import apply_extraction_batch, open_canon_db
    from overlord_worldsim.canon.query import get_canon_rudeus_state

    connection = open_canon_db(db_path)
    try:
        with connection:
            apply_extraction_batch(
                connection,
                ExtractionBatch(
                    batch_id="b4",
                    source_volume=1,
                    source_unit_ids=(),
                    entities=(
                        Entity(
                            entity_id="E0009",
                            name="鲁迪乌斯·格雷拉特",
                            aliases=(),
                            kind=EntityKind.CHARACTER,
                            introduced_volume=1,
                            introduced_line=4,
                            description="",
                        ),
                    ),
                    facts=(),
                    relationships=(),
                    knowledge=(),
                    events=(),
                    phases=(),
                ),
            )
    finally:
        connection.close()
    state = get_canon_rudeus_state(db_path, rudeus_entity_id="E0009")
    assert state is not None
    assert state["age"] is None
    assert state["location"] is None
    assert state["phase"] is None
    assert state["facts"] == []
