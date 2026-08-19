"""Deterministic verification of extraction batches against the parsed source.

The verifier enforces structural invariants only: evidence ranges must exist
inside the batch's source units, ids must be unique, references must resolve,
and dates must be parseable and ordered. It never invents content — semantic
correctness stays with the extractor, evidence stays with the raw text.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from overlord_worldsim.canon.extract_model import (
    CharacterPhase,
    Entity,
    ExtractionBatch,
    Fact,
    Relationship,
    TimelineEvent,
    parse_canon_date,
)
from overlord_worldsim.canon.parse import ParsedDocument


@dataclass(frozen=True)
class VerificationError:
    code: str
    path: str
    message: str

    def to_json(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


@dataclass(frozen=True)
class VerificationReport:
    batch_id: str
    errors: tuple[VerificationError, ...] = field(default_factory=tuple)

    @property
    def is_clean(self) -> bool:
        return not self.errors


def _volume_line_ranges(doc: ParsedDocument, volume_no: int) -> tuple[tuple[int, int], ...]:
    """Line ranges of all units in a volume, for evidence containment checks."""
    return tuple(
        (unit.start_line, unit.end_line) for unit in doc.units if unit.volume_no == volume_no
    )


def _line_in_ranges(line: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(start <= line <= end for start, end in ranges)


def _check_evidence(
    errors: list[VerificationError],
    path: str,
    evidence_volumes: tuple[int, ...],
    evidence_lines: tuple[tuple[int, int], ...],
    volume_ranges: dict[int, tuple[tuple[int, int], ...]],
) -> None:
    if len(evidence_volumes) != len(evidence_lines):
        errors.append(
            VerificationError(
                "evidence_arity",
                path,
                f"evidence_volumes ({len(evidence_volumes)}) and evidence_lines "
                f"({len(evidence_lines)}) must match",
            )
        )
        return
    for volume_no, (start, end) in zip(evidence_volumes, evidence_lines, strict=True):
        ranges = volume_ranges.get(volume_no)
        if ranges is None:
            errors.append(
                VerificationError(
                    "evidence_volume", path, f"evidence volume {volume_no} is not parsed"
                )
            )
            continue
        if not _line_in_ranges(start, ranges) or not _line_in_ranges(end, ranges):
            errors.append(
                VerificationError(
                    "evidence_lines",
                    path,
                    f"evidence lines {start}-{end} fall outside volume {volume_no} units",
                )
            )
        if start > end:
            errors.append(
                VerificationError(
                    "evidence_order", path, f"evidence line start {start} > end {end}"
                )
            )


def _check_entity(
    errors: list[VerificationError],
    entity: Entity,
    volume_ranges: dict[int, tuple[tuple[int, int], ...]],
) -> None:
    if entity.introduced_volume not in volume_ranges:
        errors.append(
            VerificationError(
                "entity_introduced_volume",
                f"entities.{entity.entity_id}",
                f"introduced_volume {entity.introduced_volume} is not parsed",
            )
        )
        return
    if not _line_in_ranges(entity.introduced_line, volume_ranges[entity.introduced_volume]):
        errors.append(
            VerificationError(
                "entity_introduced_line",
                f"entities.{entity.entity_id}",
                f"introduced_line {entity.introduced_line} falls outside "
                f"volume {entity.introduced_volume}",
            )
        )


def _check_fact(
    errors: list[VerificationError],
    fact: Fact,
    entity_ids: set[str],
    volume_ranges: dict[int, tuple[tuple[int, int], ...]],
    source_volume: int,
) -> None:
    path = f"facts.{fact.fact_id}"
    if fact.entity_id not in entity_ids:
        errors.append(VerificationError("fact_entity", path, f"unknown entity {fact.entity_id}"))
    if fact.visible_from_volume > source_volume:
        errors.append(
            VerificationError(
                "fact_visible_from",
                path,
                f"visible_from_volume {fact.visible_from_volume} is after source volume "
                f"{source_volume}",
            )
        )
    if fact.visible_to_volume is not None and fact.visible_to_volume < fact.visible_from_volume:
        errors.append(
            VerificationError(
                "fact_visible_window", path, "visible_to_volume precedes visible_from_volume"
            )
        )
    for label, value in (("start_date", fact.start_date), ("end_date", fact.end_date)):
        if value is not None:
            try:
                parse_canon_date(value)
            except ValueError as error:
                errors.append(VerificationError("fact_date", path, f"{label}: {error}"))
    _check_evidence(errors, path, fact.evidence_volumes, fact.evidence_lines, volume_ranges)


def _check_relationship(
    errors: list[VerificationError],
    relationship: Relationship,
    entity_ids: set[str],
    volume_ranges: dict[int, tuple[tuple[int, int], ...]],
) -> None:
    path = f"relationships.{relationship.relationship_id}"
    if relationship.source_id not in entity_ids:
        errors.append(
            VerificationError(
                "relationship_source", path, f"unknown source {relationship.source_id}"
            )
        )
    if relationship.target_id not in entity_ids:
        errors.append(
            VerificationError(
                "relationship_target", path, f"unknown target {relationship.target_id}"
            )
        )
    _check_evidence(
        errors, path, relationship.evidence_volumes, relationship.evidence_lines, volume_ranges
    )


def _check_event(
    errors: list[VerificationError],
    event: TimelineEvent,
    entity_ids: set[str],
    volume_ranges: dict[int, tuple[tuple[int, int], ...]],
) -> None:
    path = f"events.{event.event_id}"
    for participant in event.participants:
        if participant not in entity_ids:
            errors.append(
                VerificationError("event_participant", path, f"unknown participant {participant}")
            )
    if event.date is not None:
        try:
            parse_canon_date(event.date)
        except ValueError as error:
            errors.append(VerificationError("event_date", path, str(error)))
    _check_evidence(errors, path, event.evidence_volumes, event.evidence_lines, volume_ranges)


def _check_phase(
    errors: list[VerificationError],
    phase: CharacterPhase,
    entity_ids: set[str],
    volume_ranges: dict[int, tuple[tuple[int, int], ...]],
) -> None:
    path = f"phases.{phase.phase_id}"
    if phase.character_id not in entity_ids:
        errors.append(
            VerificationError("phase_character", path, f"unknown character {phase.character_id}")
        )
    start = parse_canon_date(phase.start_date) if phase.start_date else None
    end = parse_canon_date(phase.end_date) if phase.end_date else None
    if start is not None and end is not None and start > end:
        errors.append(
            VerificationError("phase_date_order", path, "start_date must not be after end_date")
        )
    _check_evidence(errors, path, phase.evidence_volumes, phase.evidence_lines, volume_ranges)


def verify_batch(batch: ExtractionBatch, doc: ParsedDocument) -> VerificationReport:
    """Verify a batch against the parsed document; returns a deterministic report."""
    errors: list[VerificationError] = []
    volume_ranges: dict[int, tuple[tuple[int, int], ...]] = {}
    for unit in doc.units:
        if unit.volume_no is not None and unit.volume_no not in volume_ranges:
            volume_ranges[unit.volume_no] = _volume_line_ranges(doc, unit.volume_no)
    if batch.source_volume not in volume_ranges:
        errors.append(
            VerificationError(
                "batch_volume", "batch", f"source_volume {batch.source_volume} is not parsed"
            )
        )

    entity_ids = {entity.entity_id for entity in batch.entities}
    seen_ids: set[str] = set()
    for entity in batch.entities:
        if entity.entity_id in seen_ids:
            errors.append(
                VerificationError(
                    "duplicate_entity", f"entities.{entity.entity_id}", "duplicate entity_id"
                )
            )
        seen_ids.add(entity.entity_id)
        _check_entity(errors, entity, volume_ranges)
    for fact in batch.facts:
        _check_fact(errors, fact, entity_ids, volume_ranges, batch.source_volume)
    for relationship in batch.relationships:
        _check_relationship(errors, relationship, entity_ids, volume_ranges)
    for event in batch.events:
        _check_event(errors, event, entity_ids, volume_ranges)
    for phase in batch.phases:
        _check_phase(errors, phase, entity_ids, volume_ranges)

    errors.sort(key=lambda error: (error.path, error.code, error.message))
    return VerificationReport(batch_id=batch.batch_id, errors=tuple(errors))
