"""Tests for the enrichment entity registry loader and resolution helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from overlord_worldsim.canon.enrich_registry import (
    load_enrichment_batches,
    load_entity_registry,
)
from overlord_worldsim.canon.extract_model import (
    EntityKind,
    ExtractionBatch,
)

from .enrich_fixtures import (
    ENTITIES,
    REGISTRY,
    RELATIONSHIPS,
    TIMELINE_EVENTS,
    make_batch,
)


def test_registry_lookup_helpers() -> None:
    assert REGISTRY.has("E0001")
    assert not REGISTRY.has("E9999")
    assert REGISTRY.has_kind("E0001", EntityKind.CHARACTER)
    assert not REGISTRY.has_kind("E0001", EntityKind.LOCATION)
    assert REGISTRY.names()["E0001"] == "鲁迪乌斯"
    assert REGISTRY.by_id("E0001") is ENTITIES[0]
    assert REGISTRY.by_id("E9999") is None
    assert "T0001" in REGISTRY.timeline_event_ids()


def test_registry_canonical_json() -> None:
    document = cast(dict[str, Any], REGISTRY.canonical_json())
    assert document["entities"][0]["entity_id"] == "E0001"
    assert document["timeline_events"][0]["event_id"] == "T0001"
    assert document["relationships"][0]["relationship_id"] == "R0001"


def _write_registry_batch(directory: Path, *, batch_id: str = "V001") -> None:
    batch = ExtractionBatch(
        batch_id=batch_id,
        source_volume=1,
        source_unit_ids=("U0001", "U0002", "U0003"),
        entities=ENTITIES,
        facts=(),
        relationships=RELATIONSHIPS,
        knowledge=(),
        events=TIMELINE_EVENTS,
        phases=(),
    )
    (directory / f"{batch_id}.json").write_text(
        json.dumps(batch.to_json(), ensure_ascii=False), encoding="utf-8"
    )


def test_load_entity_registry_skips_reports_and_sorts(tmp_path: Path) -> None:
    canon_dir = tmp_path / "canon"
    canon_dir.mkdir()
    _write_registry_batch(canon_dir, batch_id="V002")
    _write_registry_batch(canon_dir, batch_id="V001")
    (canon_dir / "V001.report.json").write_text("{}", encoding="utf-8")
    registry = load_entity_registry(canon_dir)
    assert [entity.entity_id for entity in registry.entities] == [
        entity.entity_id for entity in sorted(ENTITIES, key=lambda e: e.entity_id)
    ]
    assert "T0001" in registry.timeline_event_ids()


def test_load_entity_registry_missing_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="no extraction batches"):
        load_entity_registry(tmp_path / "missing")


def test_load_enrichment_batches_sorts_and_skips_reports(tmp_path: Path) -> None:
    enrich_dir = tmp_path / "enrich"
    enrich_dir.mkdir()
    (enrich_dir / "V002.json").write_text(
        json.dumps(
            make_batch(batch_id="ENRICH_V002").to_json(), ensure_ascii=False, sort_keys=True
        ),
        encoding="utf-8",
    )
    (enrich_dir / "V001.json").write_text(
        json.dumps(
            make_batch(batch_id="ENRICH_V001").to_json(), ensure_ascii=False, sort_keys=True
        ),
        encoding="utf-8",
    )
    (enrich_dir / "V001.report.json").write_text("{}", encoding="utf-8")
    batches = load_enrichment_batches(enrich_dir)
    assert [batch.batch_id for batch in batches] == ["ENRICH_V001", "ENRICH_V002"]
    assert all(batch.source_volume == 1 for batch in batches)


def test_load_enrichment_batches_missing_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="no enrichment batches"):
        load_enrichment_batches(tmp_path / "missing")
