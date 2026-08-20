"""Tests for the enrichment verifier (structural and referential invariants)."""

from __future__ import annotations

from dataclasses import replace

from overlord_worldsim.canon.enrich_model import (
    DatePrecision,
    EnrichmentBatch,
    EventDependency,
    EventDependencyKind,
    EventPrerequisite,
    EventPrerequisiteKind,
)
from overlord_worldsim.canon.enrich_verifier import (
    verify_enrichment,
)

from .enrich_fixtures import (
    DOC,
    REGISTRY,
    make_batch,
    make_belief,
    make_instance,
    make_profile,
    make_rule,
)


def _codes(batches: list[EnrichmentBatch]) -> set[str]:
    report = verify_enrichment(batches, DOC, REGISTRY)
    return {error.code for error in report.errors}


def test_clean_corpus_passes() -> None:
    report = verify_enrichment([make_batch()], DOC, REGISTRY)
    assert report.is_clean, [error.to_json() for error in report.errors]


def test_bad_evidence_ref_rejected() -> None:
    batch = make_batch()
    profile = replace(make_profile(), evidence_refs=("EV9999",))
    batch = replace(batch, character_profiles=(profile,))
    assert "evidence_ref" in _codes([batch])


def test_evidence_outside_unit_lines_rejected() -> None:
    batch = make_batch()
    evidence = replace(batch.evidence[0], source_start_line=1000, source_end_line=1000)
    batch = replace(batch, evidence=(evidence, *batch.evidence[1:]))
    assert "evidence_lines" in _codes([batch])


def test_evidence_volume_not_parsed_rejected() -> None:
    batch = make_batch()
    evidence = replace(batch.evidence[0], volume_no=99)
    batch = replace(batch, evidence=(evidence, *batch.evidence[1:]))
    assert "evidence_volume" in _codes([batch])


def test_evidence_unit_mismatch_rejected() -> None:
    batch = make_batch()
    evidence = replace(batch.evidence[0], unit_id="U0003", source_start_line=3, source_end_line=3)
    batch = replace(batch, evidence=(evidence, *batch.evidence[1:]))
    # U0003 spans lines 13-17; line 3 lies outside it.
    assert "evidence_lines" in _codes([batch])


def test_unknown_entity_ref_rejected() -> None:
    batch = make_batch()
    profile = replace(make_profile(), character_id="E9999")
    batch = replace(batch, character_profiles=(profile,))
    assert "entity_ref" in _codes([batch])


def test_entity_kind_mismatch_rejected() -> None:
    batch = make_batch()
    event = batch.detailed_events[0]
    event = replace(event, location_id="E0001")  # E0001 is a CHARACTER
    batch = replace(batch, detailed_events=(event, *batch.detailed_events[1:]))
    assert "entity_kind" in _codes([batch])


def test_unknown_timeline_event_rejected() -> None:
    batch = make_batch()
    event = replace(batch.detailed_events[0], timeline_event_id="T9999")
    batch = replace(batch, detailed_events=(event, *batch.detailed_events[1:]))
    assert "timeline_event_ref" in _codes([batch])


def test_unknown_prerequisite_item_rejected() -> None:
    batch = make_batch()
    prerequisite = EventPrerequisite(
        prerequisite_id="EP0002",
        prerequisite_type=EventPrerequisiteKind.ITEM,
        ref_id="IT9999",
        statement="需要未知物品",
    )
    event = replace(
        batch.detailed_events[0],
        prerequisites=(prerequisite, *batch.detailed_events[0].prerequisites),
    )
    batch = replace(batch, detailed_events=(event, *batch.detailed_events[1:]))
    assert "prereq_item_ref" in _codes([batch])


def test_unknown_dependency_target_rejected() -> None:
    batch = make_batch()
    event = batch.detailed_events[0]
    event = replace(
        event,
        dependencies=(
            EventDependency(
                dependency_id="ED0002",
                dependency_type=EventDependencyKind.REQUIRES,
                target_event_id="DE9999",
                statement="依赖测试",
            ),
            *event.dependencies,
        ),
    )
    batch = replace(batch, detailed_events=(event, *batch.detailed_events[1:]))
    assert "dependency_event_ref" in _codes([batch])


def test_instance_unknown_definition_rejected() -> None:
    batch = make_batch()
    instance = replace(make_instance(), definition_id="IT9999")
    batch = replace(batch, item_instances=(instance,))
    assert "instance_definition" in _codes([batch])


def test_belief_learned_window_rejected() -> None:
    batch = make_batch()
    belief = replace(make_belief(), learned_at_volume=3, visible_from_volume=1)
    batch = replace(batch, beliefs=(belief,))
    assert "belief_learned_window" in _codes([batch])


def test_profile_date_order_rejected() -> None:
    batch = make_batch()
    profile = replace(
        make_profile(),
        start_date="409-3",
        end_date="408-1",
        date_precision=DatePrecision.EXACT,
    )
    batch = replace(batch, character_profiles=(profile,))
    assert "date_order" in _codes([batch])


def test_duplicate_id_across_batches_rejected() -> None:
    batch_a = make_batch()
    batch_b = make_batch(batch_id="ENRICH_V002")
    batch_b = replace(batch_b, source_volume=2)
    assert "duplicate_id" in _codes([batch_a, batch_b])


def test_duplicate_item_name_rejected() -> None:
    batch_a = make_batch()
    batch_b = make_batch(batch_id="ENRICH_V002")
    batch_b = replace(batch_b, source_volume=2)
    item = batch_b.items[0]
    item = replace(item, item_id="IT0002")
    batch_b = replace(batch_b, items=(item,))
    assert "duplicate_name" in _codes([batch_a, batch_b])


def test_batch_unknown_unit_rejected() -> None:
    batch = make_batch()
    batch = replace(batch, source_unit_ids=("U9999",))
    assert "batch_unit" in _codes([batch])


def test_wrong_schema_version_rejected() -> None:
    batch = make_batch()
    batch = replace(batch, schema_version="0.0.0")
    assert "schema_version" in _codes([batch])


def test_world_rule_requires_evidence_gate() -> None:
    batch = make_batch()
    rule = replace(make_rule(), evidence_refs=())
    batch = replace(batch, world_rules=(rule,))
    # Empty evidence is structurally allowed; the rule statement itself is the
    # semantic gate — the verifier must not fabricate claims for it.
    assert "evidence_ref" not in _codes([batch])


def test_gap_searched_volume_rejected() -> None:
    batch = make_batch()
    gap = replace(batch.canon_gaps[0], searched_volumes=(99,))
    batch = replace(batch, canon_gaps=(gap,))
    assert "gap_volume" in _codes([batch])
