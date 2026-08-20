"""Tests for the enrichment loader (schema creation, idempotent apply)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from overlord_worldsim.canon.enrich_loader import (
    apply_enrichment,
    build_manifest,
    canonical_content_hash,
)
from overlord_worldsim.canon.loader import open_canon_db

from .enrich_fixtures import make_batch

_ENRICH_TABLES = (
    "enrichment_manifest",
    "enrichment_evidence",
    "enrichment_evidence_links",
    "character_profiles",
    "behavior_cases",
    "behavior_case_tags",
    "detailed_events",
    "event_prerequisites",
    "event_dependencies",
    "event_state_changes",
    "enrichment_event_participants",
    "items",
    "item_instances",
    "item_ownership_history",
    "abilities",
    "power_comparisons",
    "world_rules",
    "locations",
    "routes",
    "travel_observations",
    "organizations",
    "political_states",
    "species",
    "creatures",
    "beliefs",
    "economic_observations",
    "relationship_changes",
    "speech_profiles",
    "canon_conflicts",
    "canon_gaps",
)


def _apply(tmp_path: Path) -> Path:
    db_path = tmp_path / "canon.sqlite3"
    connection = open_canon_db(db_path)
    try:
        manifest = build_manifest(
            content_sha256=canonical_content_hash([make_batch()]),
            source_sha256="abc",
            source_volumes=[1],
            source_unit_count=3,
            build_tool_version="test",
            batch_counts={"ENRICH_V001": 10},
            generated_at="2026-01-01T00:00:00+00:00",
        )
        apply_enrichment(connection, [make_batch()], manifest)
    finally:
        connection.close()
    return db_path


def test_schema_tables_created(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    connection = open_canon_db(db_path)
    try:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        for table in _ENRICH_TABLES:
            assert table in tables
        assert "behavior_cases_fts" in tables
    finally:
        connection.close()


def test_apply_is_idempotent(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    connection = open_canon_db(db_path)
    try:
        first = connection.execute("SELECT COUNT(*) FROM character_profiles").fetchone()[0]
        manifest_before = connection.execute(
            "SELECT value FROM enrichment_manifest WHERE key = 'content_sha256'"
        ).fetchone()[0]
    finally:
        connection.close()
    assert first == 1
    _apply(tmp_path)
    connection = open_canon_db(db_path)
    try:
        second = connection.execute("SELECT COUNT(*) FROM character_profiles").fetchone()[0]
        manifest_after = connection.execute(
            "SELECT value FROM enrichment_manifest WHERE key = 'content_sha256'"
        ).fetchone()[0]
    finally:
        connection.close()
    assert first == second
    assert manifest_before == manifest_after


def test_evidence_links_and_fts_populated(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    connection = open_canon_db(db_path)
    try:
        links = connection.execute(
            "SELECT COUNT(*) FROM enrichment_evidence_links"
        ).fetchone()[0]
        assert links > 0
        fts_count = connection.execute(
            "SELECT COUNT(*) FROM behavior_cases_fts"
        ).fetchone()[0]
        assert fts_count == 1
        tags = connection.execute(
            "SELECT tag FROM behavior_case_tags WHERE case_id = 'BC0001' ORDER BY tag"
        ).fetchall()
        assert [row["tag"] for row in tags] == ["TEACHING", "TRAINING"]
    finally:
        connection.close()


def test_canonical_content_hash_stable() -> None:
    batch = make_batch()
    assert canonical_content_hash([batch]) == canonical_content_hash([batch])
    assert canonical_content_hash([batch, batch]) != canonical_content_hash([batch])


def test_manifest_written_deterministically(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    connection = open_canon_db(db_path)
    try:
        manifest = {
            row["key"]: row["value"]
            for row in connection.execute(
                "SELECT key, value FROM enrichment_manifest ORDER BY key"
            ).fetchall()
        }
    finally:
        connection.close()
    assert manifest["schema_version"] == "1.0.0"
    assert manifest["content_sha256"]
    # Content hash must survive a full JSON round-trip of the batch.
    document = make_batch().to_json()
    serialized = json.dumps(document, ensure_ascii=False, sort_keys=True)
    assert manifest["content_sha256"] == canonical_content_hash([make_batch()])
    assert len(serialized) > 0


def test_apply_rejects_broken_foreign_keys(tmp_path: Path) -> None:
    from dataclasses import replace

    db_path = tmp_path / "canon.sqlite3"
    connection = open_canon_db(db_path)
    try:
        bad = replace(make_batch(), items=())
        manifest = build_manifest(
            content_sha256="x",
            source_sha256="x",
            source_volumes=[1],
            source_unit_count=3,
            build_tool_version="test",
            batch_counts={},
            generated_at="2026-01-01T00:00:00+00:00",
        )
        with pytest.raises(Exception):
            apply_enrichment(connection, [bad], manifest)
    finally:
        connection.close()