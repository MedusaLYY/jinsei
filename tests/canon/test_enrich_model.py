"""Tests for the enrichment model (enums, JSON round-trips, id stability)."""

from __future__ import annotations

import json

import pytest

from overlord_worldsim.canon.enrich_model import (
    BehaviorTag,
    BeliefState,
    ConflictStatus,
    EnrichmentBatch,
    EventDependencyKind,
    EventPrerequisiteKind,
    EvidenceType,
    GapStatus,
    LocationType,
    WorldRuleDomain,
)

from .enrich_fixtures import make_batch


def test_stable_enum_values() -> None:
    assert EvidenceType.CANON_EXPLICIT.value == "CANON_EXPLICIT"
    assert EvidenceType.CANON_ANALOGICAL.value == "CANON_ANALOGICAL"
    assert EvidenceType.STRONG_INFERENCE.value == "STRONG_INFERENCE"
    assert EvidenceType.INFERENCE.value == "INFERENCE"
    assert EvidenceType.UNKNOWN.value == "UNKNOWN"
    assert EventDependencyKind.REQUIRES.value == "REQUIRES"
    assert EventDependencyKind.ENABLES.value == "ENABLES"
    assert EventDependencyKind.CAUSES.value == "CAUSES"
    assert EventDependencyKind.INFLUENCES.value == "INFLUENCES"
    assert EventDependencyKind.REVEALS.value == "REVEALS"
    assert EventDependencyKind.INVALIDATES.value == "INVALIDATES"
    assert EventPrerequisiteKind.ITEM.value == "ITEM"
    assert ConflictStatus.POV_DIFFERENCE.value == "POV_DIFFERENCE"
    assert GapStatus.NO_CANON_ANSWER.value == "NO_CANON_ANSWER"
    assert LocationType.SANCTUM.value == "SANCTUM"
    assert WorldRuleDomain.MAGIC.value == "MAGIC"
    assert BeliefState.FALSE_BELIEF.value == "FALSE_BELIEF"


def test_behavior_tag_vocabulary_is_complete() -> None:
    expected = {
        "TEACHING",
        "TRAINING",
        "ROMANCE",
        "EMBARRASSMENT",
        "ANGER",
        "FEAR",
        "COMBAT",
        "PROTECT",
        "RETREAT",
        "NEGOTIATION",
        "MONEY",
        "FAMILY",
        "JEALOUSY",
        "LOYALTY",
        "BETRAYAL",
        "AUTHORITY",
        "NOBILITY",
        "FRIENDSHIP",
        "TRUST",
        "SUSPICION",
        "DANGER",
        "MORAL_CHOICE",
        "REQUEST",
        "REJECTION",
        "ACCEPTANCE",
        "APOLOGY",
        "GRATITUDE",
        "LOSS",
        "GRIEF",
    }
    assert {tag.value for tag in BehaviorTag} == expected


def test_batch_json_round_trip() -> None:
    batch = make_batch()
    restored = EnrichmentBatch.from_json(batch.to_json())
    assert restored == batch
    assert restored.batch_id == "ENRICH_V001"


def test_batch_serialization_is_deterministic() -> None:
    batch = make_batch()
    first = json.dumps(batch.to_json(), ensure_ascii=False, sort_keys=True)
    second = json.dumps(batch.to_json(), ensure_ascii=False, sort_keys=True)
    assert first == second


def test_batch_counts() -> None:
    counts = make_batch().counts()
    assert counts["character_profiles"] == 1
    assert counts["evidence"] == 4
    assert counts["behavior_cases"] == 1
    assert counts["detailed_events"] == 2


def test_schema_version_is_stable() -> None:
    assert EnrichmentBatch.ENRICHMENT_SCHEMA_VERSION == "1.0.0"


def test_invalid_evidence_type_rejected() -> None:
    batch = make_batch()
    document = batch.to_json()
    document["evidence"][0]["evidence_type"] = "NOT_A_TYPE"
    with pytest.raises(ValueError):
        EnrichmentBatch.from_json(document)


def test_invalid_batch_id_rejected() -> None:
    batch = make_batch()
    document = batch.to_json()
    document["batch_id"] = "ENRICH_V001-extra"
    restored = EnrichmentBatch.from_json(document)
    assert restored.batch_id == "ENRICH_V001-extra"