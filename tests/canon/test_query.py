"""Tests for the canon query API (10 read-only interfaces)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

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
from overlord_worldsim.canon.loader import apply_extraction_batch, build_canon_db, open_canon_db
from overlord_worldsim.canon.parse import parse_source
from overlord_worldsim.canon.query import (
    get_canon_events,
    get_canon_rudeus_state,
    get_character,
    get_character_knowledge,
    get_character_location,
    get_character_phase,
    get_fact,
    get_location,
    get_relationship,
)

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
    "\n"
    "第一卷 幼年期 第二话「搬家」\n"
    "\n"
    "    一家搬往布埃纳村。\n"
)

DOC = parse_source(CORPUS, source_name="corpus.txt")

RUDEUS = Entity(
    entity_id="E0001",
    name="鲁迪乌斯·格雷拉特",
    aliases=("鲁迪",),
    kind=EntityKind.CHARACTER,
    introduced_volume=1,
    introduced_line=3,
    description="主角。",
)
PAUL = Entity(
    entity_id="E0002",
    name="保罗·格雷拉特",
    aliases=(),
    kind=EntityKind.CHARACTER,
    introduced_volume=1,
    introduced_line=7,
    description="鲁迪乌斯的父亲。",
)
BUENA = Entity(
    entity_id="E0003",
    name="布埃纳村",
    aliases=(),
    kind=EntityKind.LOCATION,
    introduced_volume=1,
    introduced_line=13,
    description="菲托亚领的村庄。",
)
SILPHIE = Entity(
    entity_id="E0004",
    name="希露菲·格雷拉特",
    aliases=("希露菲",),
    kind=EntityKind.CHARACTER,
    introduced_volume=1,
    introduced_line=3,
    description="银发女孩。",
)

AGE_FACT = Fact(
    fact_id="F0001",
    entity_id="E0001",
    predicate="年纪",
    object_value="四岁",
    start_date="408-1",
    end_date="410-1",
    date_precision=DatePrecision.YEAR_ONLY,
    evidence_volumes=(1,),
    evidence_lines=((9, 9),),
    confidence=Confidence.EXPLICIT,
    visible_from_volume=1,
    visible_to_volume=None,
)
LOCATION_FACT = Fact(
    fact_id="F0002",
    entity_id="E0001",
    predicate="位于",
    object_value="布埃纳村",
    start_date="408-1",
    end_date=None,
    date_precision=DatePrecision.YEAR_ONLY,
    evidence_volumes=(1,),
    evidence_lines=((13, 13),),
    confidence=Confidence.EXPLICIT,
    visible_from_volume=1,
    visible_to_volume=None,
)
FAMILY_REL = Relationship(
    relationship_id="R0001",
    source_id="E0002",
    target_id="E0001",
    rel_type="父子",
    evidence_volumes=(1,),
    evidence_lines=((7, 7),),
    confidence=Confidence.EXPLICIT,
    visible_from_volume=1,
)
LATER_FACT = Fact(
    fact_id="F0003",
    entity_id="E0001",
    predicate="称号",
    object_value="泥沼魔术师",
    start_date="410-1",
    end_date=None,
    date_precision=DatePrecision.YEAR_ONLY,
    evidence_volumes=(1,),
    evidence_lines=((9, 9),),
    confidence=Confidence.INFERENCE,
    visible_from_volume=4,
    visible_to_volume=None,
)
FAMILY_KNOWLEDGE = Knowledge(
    knowledge_id="K0001",
    owner_id="E0001",
    fact_id="F0001",
    certainty=Confidence.EXPLICIT,
    note="鲁迪知道自己的年纪。",
)
EVENT = TimelineEvent(
    event_id="T0001",
    title="搬家",
    description="一家搬往布埃纳村。",
    date="408-3",
    date_precision=DatePrecision.YEAR_ONLY,
    participants=("E0001", "E0002"),
    evidence_volumes=(1,),
    evidence_lines=((13, 13),),
)
PHASE = CharacterPhase(
    phase_id="P0001",
    character_id="E0001",
    name="幼年期",
    start_date="408-1",
    end_date="410-1",
    date_precision=DatePrecision.YEAR_ONLY,
    summary="布埃纳村的生活。",
    evidence_volumes=(1,),
    evidence_lines=((3, 3),),
)

BATCH = ExtractionBatch(
    batch_id="b1",
    source_volume=1,
    source_unit_ids=("U0001", "U0002", "U0003"),
    entities=(RUDEUS, PAUL, BUENA, SILPHIE),
    facts=(AGE_FACT, LOCATION_FACT, LATER_FACT),
    relationships=(FAMILY_REL,),
    knowledge=(FAMILY_KNOWLEDGE,),
    events=(EVENT,),
    phases=(PHASE,),
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = build_canon_db(DOC, tmp_path / "canon.sqlite3", sha256="abc123")
    connection = open_canon_db(path)
    try:
        with connection:
            apply_extraction_batch(connection, BATCH)
            connection.execute(
                "INSERT INTO volume_dates(volume_no, start_date, end_date) "
                "VALUES (1, '408-1', '410-12')"
            )
    finally:
        connection.close()
    return path


def test_get_character_returns_entity_and_visible_facts(db_path: Path) -> None:
    character = cast(dict[str, Any], get_character(db_path, "E0001"))
    assert character["entity"]["name"] == "鲁迪乌斯·格雷拉特"
    assert "鲁迪" in character["entity"]["aliases"]
    predicates = {fact["predicate"] for fact in cast(list[Any], character["facts"])}
    assert {"年纪", "位于", "称号"} <= predicates


def test_get_character_filters_by_volume_window(db_path: Path) -> None:
    early = cast(dict[str, Any], get_character(db_path, "E0001", at_volume=1))
    assert {fact["predicate"] for fact in cast(list[Any], early["facts"])} == {"年纪", "位于"}
    late = cast(dict[str, Any], get_character(db_path, "E0001", at_volume=4))
    late_predicates = {fact["predicate"] for fact in cast(list[Any], late["facts"])}
    assert late_predicates == {"年纪", "位于", "称号"}


def test_get_character_unknown_id_returns_none(db_path: Path) -> None:
    assert get_character(db_path, "E9999") is None


def test_get_character_phase(db_path: Path) -> None:
    phases = get_character_phase(db_path, "E0001")
    assert len(phases) == 1
    assert phases[0]["name"] == "幼年期"
    assert get_character_phase(db_path, "E9999") == []


def test_get_character_location(db_path: Path) -> None:
    locations = get_character_location(db_path, "E0001")
    assert len(locations) == 1
    assert locations[0]["object_value"] == "布埃纳村"


def test_get_character_knowledge(db_path: Path) -> None:
    knowledge = get_character_knowledge(db_path, "E0001")
    assert len(knowledge) == 1
    assert knowledge[0]["knowledge_id"] == "K0001"
    assert knowledge[0]["predicate"] == "年纪"


def test_get_relationship(db_path: Path) -> None:
    relationships = get_relationship(db_path, "E0002", "E0001")
    assert len(relationships) == 1
    assert relationships[0]["rel_type"] == "父子"
    reversed_lookup = get_relationship(db_path, "E0001", "E0002")
    assert len(reversed_lookup) == 1
    assert get_relationship(db_path, "E0001", "E0004") == []


def test_get_canon_events(db_path: Path) -> None:
    events = get_canon_events(db_path)
    assert len(events) == 1
    assert events[0]["title"] == "搬家"
    by_participant = get_canon_events(db_path, entity_id="E0002")
    assert len(by_participant) == 1
    by_date = get_canon_events(db_path, start_date="409-1")
    assert by_date == []


def test_get_location(db_path: Path) -> None:
    facts = get_location(db_path, "E0003")
    assert len(facts) == 1
    assert facts[0]["fact_id"] == "F0002"
    assert get_location(db_path, "E0001") == []


def test_get_fact_with_verbatim_evidence(db_path: Path) -> None:
    fact = cast(dict[str, Any], get_fact(db_path, fact_id="F0001"))
    assert fact is not None
    assert fact["predicate"] == "年纪"
    assert "鲁迪乌斯四岁" in fact["evidence_text"][0]
    assert get_fact(db_path, fact_id="NOPE") is None
    by_query = cast(dict[str, Any], get_fact(db_path, entity_id="E0001", predicate="位于"))
    assert by_query is not None
    assert by_query["fact_id"] == "F0002"


def test_get_canon_rudeus_state(db_path: Path) -> None:
    state = cast(dict[str, Any], get_canon_rudeus_state(db_path, at_volume=1))
    assert state is not None
    assert state["entity"]["name"] == "鲁迪乌斯·格雷拉特"
    assert state["location"] == "布埃纳村"
    assert state["age"]["object_value"] == "四岁"
    assert state["phase"] == "幼年期"
    assert state["facts"] == ["年纪", "位于"]
    late = cast(dict[str, Any], get_canon_rudeus_state(db_path, at_volume=9))
    assert late is not None
    assert late["facts"] == ["年纪", "位于", "称号"]
