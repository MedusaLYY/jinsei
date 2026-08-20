"""Entity registry loader for enrichment verification.

The enrichment layer references entities by id (participants, owners,
location ids, …). The authoritative registry is the set of extraction batches
in `data/canon/V###.json` — never a hand-maintained list. This module rebuilds
the registry deterministically from those batches and resolves references.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from overlord_worldsim.canon.enrich_model import EnrichmentBatch
from overlord_worldsim.canon.extract_model import (
    Entity,
    EntityKind,
    ExtractionBatch,
    Relationship,
    TimelineEvent,
)

_BATCH_PATTERN = "V*.json"


@dataclass(frozen=True)
class EntityRegistry:
    """Resolved entity and timeline registry built from extraction batches."""

    entities: tuple[Entity, ...]
    timeline_events: tuple[TimelineEvent, ...]
    relationships: tuple[Relationship, ...]

    def by_id(self, entity_id: str) -> Entity | None:
        for entity in self.entities:
            if entity.entity_id == entity_id:
                return entity
        return None

    def has(self, entity_id: str) -> bool:
        return self.by_id(entity_id) is not None

    def has_kind(self, entity_id: str, kind: EntityKind) -> bool:
        entity = self.by_id(entity_id)
        return entity is not None and entity.kind == kind

    def timeline_event_ids(self) -> set[str]:
        return {event.event_id for event in self.timeline_events}

    def names(self) -> dict[str, str]:
        return {entity.entity_id: entity.name for entity in self.entities}

    def canonical_json(self) -> dict[str, object]:
        return {
            "entities": [entity.to_json() for entity in self.entities],
            "timeline_events": [event.to_json() for event in self.timeline_events],
            "relationships": [relationship.to_json() for relationship in self.relationships],
        }


def load_entity_registry(canon_dir: Path) -> EntityRegistry:
    """Build the entity registry from every V###.json extraction batch."""
    entities: dict[str, Entity] = {}
    events: dict[str, TimelineEvent] = {}
    relationships: dict[str, Relationship] = {}
    paths = sorted(canon_dir.glob(_BATCH_PATTERN))
    if not paths:
        raise FileNotFoundError(f"no extraction batches found under {canon_dir}")
    for path in paths:
        if path.name.endswith(".report.json"):
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        batch = ExtractionBatch.from_json(document)
        for entity in batch.entities:
            entities[entity.entity_id] = entity
        for event in batch.events:
            events[event.event_id] = event
        for relationship in batch.relationships:
            relationships[relationship.relationship_id] = relationship
    return EntityRegistry(
        entities=tuple(sorted(entities.values(), key=lambda e: e.entity_id)),
        timeline_events=tuple(sorted(events.values(), key=lambda e: e.event_id)),
        relationships=tuple(
            sorted(relationships.values(), key=lambda r: r.relationship_id)
        ),
    )


def load_enrichment_batches(enrich_dir: Path) -> list[EnrichmentBatch]:
    """Load every enrichment batch, sorted by source volume then batch id.

    Raises FileNotFoundError when the directory contains no batches.
    """
    batches: list[EnrichmentBatch] = []
    paths = sorted(enrich_dir.glob(_BATCH_PATTERN))
    if not paths:
        raise FileNotFoundError(f"no enrichment batches found under {enrich_dir}")
    for path in paths:
        if path.name.endswith(".report.json"):
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        batches.append(EnrichmentBatch.from_json(document))
    batches.sort(key=lambda batch: (batch.source_volume, batch.batch_id))
    return batches