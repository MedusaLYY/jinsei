"""Structured extraction model: entities, facts, timeline, and knowledge.

All records carry verbatim evidence (volume + line ranges) and confidence,
so the raw text stays the authority. Dates use the canon calendar
(year 408..426, 1-based month) and remain integers everywhere.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

_CANON_DATE = re.compile(r"^(\d{3})-(\d{1,2})$")
_CANON_MIN_YEAR = 380
_CANON_MAX_YEAR = 440


class Confidence(Enum):
    """How directly the evidence states the fact."""

    EXPLICIT = "EXPLICIT"
    STRONG_INFERENCE = "STRONG_INFERENCE"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"


class DatePrecision(Enum):
    """Precision of a canon date value."""

    EXACT = "EXACT"
    YEAR_ONLY = "YEAR_ONLY"
    RELATIVE = "RELATIVE"
    UNKNOWN = "UNKNOWN"


class EntityKind(Enum):
    CHARACTER = "CHARACTER"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    ITEM = "ITEM"
    ABILITY = "ABILITY"
    UNKNOWN = "UNKNOWN"


class RelationshipKind(Enum):
    FAMILY = "FAMILY"
    FRIEND = "FRIEND"
    ENEMY = "ENEMY"
    ROMANTIC = "ROMANTIC"
    MENTOR = "MENTOR"
    ORGANIZATIONAL = "ORGANIZATIONAL"
    UNKNOWN = "UNKNOWN"


def parse_canon_date(value: str | None) -> tuple[int, int] | None:
    """Parse "YYYY-M" into (year, month); returns None for None."""
    if value is None:
        return None
    match = _CANON_DATE.fullmatch(value)
    if match is None:
        raise ValueError(f"invalid canon date: {value!r} (expected YYYY-M)")
    year, month = int(match.group(1)), int(match.group(2))
    if not _CANON_MIN_YEAR <= year <= _CANON_MAX_YEAR or not 1 <= month <= 12:
        raise ValueError(f"invalid canon date: {value!r} (year 380..440, month 1..12)")
    return year, month


def canon_date_sort_key(value: str) -> tuple[int, int]:
    return parse_canon_date(value) or (0, 0)


def _from_json(document: dict[str, Any], cls: type[Any]) -> Any:
    return cls.from_json(document)


@dataclass(frozen=True)
class Entity:
    entity_id: str
    name: str
    aliases: tuple[str, ...]
    kind: EntityKind
    introduced_volume: int
    introduced_line: int
    description: str

    def to_json(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "aliases": list(self.aliases),
            "kind": self.kind.value,
            "introduced_volume": self.introduced_volume,
            "introduced_line": self.introduced_line,
            "description": self.description,
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> Entity:
        return cls(
            entity_id=document["entity_id"],
            name=document["name"],
            aliases=tuple(document["aliases"]),
            kind=EntityKind(document["kind"]),
            introduced_volume=document["introduced_volume"],
            introduced_line=document["introduced_line"],
            description=document["description"],
        )


@dataclass(frozen=True)
class Fact:
    fact_id: str
    entity_id: str
    predicate: str
    object_value: str
    start_date: str | None
    end_date: str | None
    date_precision: DatePrecision
    evidence_volumes: tuple[int, ...]
    evidence_lines: tuple[tuple[int, int], ...]
    confidence: Confidence
    visible_from_volume: int
    visible_to_volume: int | None

    def to_json(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "entity_id": self.entity_id,
            "predicate": self.predicate,
            "object_value": self.object_value,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "date_precision": self.date_precision.value,
            "evidence_volumes": list(self.evidence_volumes),
            "evidence_lines": [list(pair) for pair in self.evidence_lines],
            "confidence": self.confidence.value,
            "visible_from_volume": self.visible_from_volume,
            "visible_to_volume": self.visible_to_volume,
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> Fact:
        return cls(
            fact_id=document["fact_id"],
            entity_id=document["entity_id"],
            predicate=document["predicate"],
            object_value=document["object_value"],
            start_date=document["start_date"],
            end_date=document["end_date"],
            date_precision=DatePrecision(document["date_precision"]),
            evidence_volumes=tuple(document["evidence_volumes"]),
            evidence_lines=tuple(tuple(pair) for pair in document["evidence_lines"]),
            confidence=Confidence(document["confidence"]),
            visible_from_volume=document["visible_from_volume"],
            visible_to_volume=document["visible_to_volume"],
        )


@dataclass(frozen=True)
class Relationship:
    relationship_id: str
    source_id: str
    target_id: str
    rel_type: str
    evidence_volumes: tuple[int, ...]
    evidence_lines: tuple[tuple[int, int], ...]
    confidence: Confidence
    visible_from_volume: int
    visible_to_volume: int | None = None
    kind: RelationshipKind = RelationshipKind.UNKNOWN

    def to_json(self) -> dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "rel_type": self.rel_type,
            "kind": self.kind.value,
            "evidence_volumes": list(self.evidence_volumes),
            "evidence_lines": [list(pair) for pair in self.evidence_lines],
            "confidence": self.confidence.value,
            "visible_from_volume": self.visible_from_volume,
            "visible_to_volume": self.visible_to_volume,
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> Relationship:
        return cls(
            relationship_id=document["relationship_id"],
            source_id=document["source_id"],
            target_id=document["target_id"],
            rel_type=document["rel_type"],
            kind=RelationshipKind(document["kind"]),
            evidence_volumes=tuple(document["evidence_volumes"]),
            evidence_lines=tuple(tuple(pair) for pair in document["evidence_lines"]),
            confidence=Confidence(document["confidence"]),
            visible_from_volume=document["visible_from_volume"],
            visible_to_volume=document["visible_to_volume"],
        )


@dataclass(frozen=True)
class Knowledge:
    knowledge_id: str
    owner_id: str
    fact_id: str
    certainty: Confidence
    note: str

    def to_json(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "owner_id": self.owner_id,
            "fact_id": self.fact_id,
            "certainty": self.certainty.value,
            "note": self.note,
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> Knowledge:
        return cls(
            knowledge_id=document["knowledge_id"],
            owner_id=document["owner_id"],
            fact_id=document["fact_id"],
            certainty=Confidence(document["certainty"]),
            note=document["note"],
        )


@dataclass(frozen=True)
class TimelineEvent:
    event_id: str
    title: str
    description: str
    date: str | None
    date_precision: DatePrecision
    participants: tuple[str, ...]
    evidence_volumes: tuple[int, ...]
    evidence_lines: tuple[tuple[int, int], ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "description": self.description,
            "date": self.date,
            "date_precision": self.date_precision.value,
            "participants": list(self.participants),
            "evidence_volumes": list(self.evidence_volumes),
            "evidence_lines": [list(pair) for pair in self.evidence_lines],
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> TimelineEvent:
        return cls(
            event_id=document["event_id"],
            title=document["title"],
            description=document["description"],
            date=document["date"],
            date_precision=DatePrecision(document["date_precision"]),
            participants=tuple(document["participants"]),
            evidence_volumes=tuple(document["evidence_volumes"]),
            evidence_lines=tuple(tuple(pair) for pair in document["evidence_lines"]),
        )


@dataclass(frozen=True)
class CharacterPhase:
    phase_id: str
    character_id: str
    name: str
    start_date: str | None
    end_date: str | None
    date_precision: DatePrecision
    summary: str
    evidence_volumes: tuple[int, ...]
    evidence_lines: tuple[tuple[int, int], ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "character_id": self.character_id,
            "name": self.name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "date_precision": self.date_precision.value,
            "summary": self.summary,
            "evidence_volumes": list(self.evidence_volumes),
            "evidence_lines": [list(pair) for pair in self.evidence_lines],
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> CharacterPhase:
        return cls(
            phase_id=document["phase_id"],
            character_id=document["character_id"],
            name=document["name"],
            start_date=document["start_date"],
            end_date=document["end_date"],
            date_precision=DatePrecision(document["date_precision"]),
            summary=document["summary"],
            evidence_volumes=tuple(document["evidence_volumes"]),
            evidence_lines=tuple(tuple(pair) for pair in document["evidence_lines"]),
        )


@dataclass(frozen=True)
class ExtractionBatch:
    """One verified batch of structured extraction for a source volume."""

    batch_id: str
    source_volume: int
    source_unit_ids: tuple[str, ...]
    entities: tuple[Entity, ...]
    facts: tuple[Fact, ...]
    relationships: tuple[Relationship, ...]
    knowledge: tuple[Knowledge, ...]
    events: tuple[TimelineEvent, ...]
    phases: tuple[CharacterPhase, ...]

    EXTRACTION_BATCH_VERSION: ClassVar[str] = "1.0.0"

    def to_json(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "source_volume": self.source_volume,
            "source_unit_ids": list(self.source_unit_ids),
            "entities": [entity.to_json() for entity in self.entities],
            "facts": [fact.to_json() for fact in self.facts],
            "relationships": [relationship.to_json() for relationship in self.relationships],
            "knowledge": [knowledge.to_json() for knowledge in self.knowledge],
            "events": [event.to_json() for event in self.events],
            "phases": [phase.to_json() for phase in self.phases],
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> ExtractionBatch:
        return cls(
            batch_id=document["batch_id"],
            source_volume=document["source_volume"],
            source_unit_ids=tuple(document["source_unit_ids"]),
            entities=tuple(_from_json(entry, Entity) for entry in document["entities"]),
            facts=tuple(_from_json(entry, Fact) for entry in document["facts"]),
            relationships=tuple(
                _from_json(entry, Relationship) for entry in document["relationships"]
            ),
            knowledge=tuple(_from_json(entry, Knowledge) for entry in document["knowledge"]),
            events=tuple(_from_json(entry, TimelineEvent) for entry in document["events"]),
            phases=tuple(_from_json(entry, CharacterPhase) for entry in document["phases"]),
        )
