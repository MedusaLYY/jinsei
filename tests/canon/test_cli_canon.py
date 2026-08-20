"""Tests for the canon CLI subcommands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from overlord_worldsim.__main__ import main

CORPUS = (
    "★☆★☆★☆轻小说文库(Www.WenKu8.Com)☆★☆★☆★\n"
    "<无职转生～到了异世界就拿出真本事～(无职转生~在异世界认真地活下去~)>\n"
    "第一卷 幼年期 序章\n"
    "\n"
    "    第一段正文。\n"
    "\n"
    "    第二段正文。\n"
)


def test_canon_parse_command_writes_artifacts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source.txt"
    source.write_text(CORPUS, encoding="utf-8")
    out_dir = tmp_path / "parsed"

    assert main(["canon", "parse", "--source", str(source), "--out", str(out_dir)]) == 0

    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert summary["volume_count"] == 1
    assert summary["unit_count"] == 1
    assert summary["chunk_count"] == 1
    assert (out_dir / "volumes.json").is_file()
    assert (out_dir / "chunks.jsonl").is_file()
    assert captured.err == ""


def test_canon_parse_command_missing_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing.txt"
    out_dir = tmp_path / "parsed"
    assert main(["canon", "parse", "--source", str(missing), "--out", str(out_dir)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "cannot read source" in captured.err
    assert "Traceback" not in captured.err
    assert len(captured.err) < 500


def test_canon_parse_command_rejects_non_utf8(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "bad.txt"
    source.write_bytes(b"\xff\xfe\x00garbage")
    out_dir = tmp_path / "parsed"
    assert main(["canon", "parse", "--source", str(source), "--out", str(out_dir)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "cannot read source" in captured.err
    assert "Traceback" not in captured.err


def test_canon_build_command_creates_database(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source.txt"
    source.write_text(CORPUS, encoding="utf-8")
    db_path = tmp_path / "canon.sqlite3"

    assert main(["canon", "build", "--source", str(source), "--db", str(db_path)]) == 0

    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert summary["volume_count"] == 1
    assert summary["unit_count"] == 1
    assert summary["chunk_count"] == 1
    assert db_path.is_file()
    assert captured.err == ""


def test_canon_build_command_records_source_hash(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import hashlib
    import sqlite3

    source = tmp_path / "source.txt"
    source.write_text(CORPUS, encoding="utf-8")
    db_path = tmp_path / "canon.sqlite3"
    expected = hashlib.sha256(source.read_bytes()).hexdigest()

    assert main(["canon", "build", "--source", str(source), "--db", str(db_path)]) == 0

    connection = sqlite3.connect(db_path)
    try:
        stored = connection.execute(
            "SELECT sha256 FROM content_hashes WHERE kind='source_txt'"
        ).fetchone()[0]
    finally:
        connection.close()
    assert stored == expected


def test_canon_build_command_missing_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing.txt"
    db_path = tmp_path / "canon.sqlite3"
    assert main(["canon", "build", "--source", str(missing), "--db", str(db_path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "cannot read source" in captured.err
    assert not db_path.exists()


def test_canon_search_command_prints_hits(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source.txt"
    source.write_text(CORPUS, encoding="utf-8")
    db_path = tmp_path / "canon.sqlite3"
    assert main(["canon", "build", "--source", str(source), "--db", str(db_path)]) == 0
    capsys.readouterr()

    assert main(["canon", "search", "--db", str(db_path), "--query", "第一段正文"]) == 0
    captured = capsys.readouterr()
    hits = json.loads(captured.out)
    assert len(hits) == 1
    assert hits[0]["chapter_title"] == "序章"
    assert hits[0]["text"] == "第一段正文。\n第二段正文。"
    assert captured.err == ""


def test_canon_search_command_bad_query(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "source.txt"
    source.write_text(CORPUS, encoding="utf-8")
    db_path = tmp_path / "canon.sqlite3"
    assert main(["canon", "build", "--source", str(source), "--db", str(db_path)]) == 0
    capsys.readouterr()

    assert main(["canon", "search", "--db", str(db_path), "--query", ""]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "query" in captured.err
    assert "Traceback" not in captured.err


def test_canon_build_embeddings_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import sqlite3

    source = tmp_path / "source.txt"
    source.write_text(CORPUS, encoding="utf-8")
    db_path = tmp_path / "canon.sqlite3"
    index_path = tmp_path / "embeddings.sqlite3"
    assert main(["canon", "build", "--source", str(source), "--db", str(db_path)]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "canon",
                "build-embeddings",
                "--db",
                str(db_path),
                "--index",
                str(index_path),
                "--provider",
                "hash",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert json.loads(captured.out)["embedded"] == 1
    connection = sqlite3.connect(index_path)
    try:
        row = connection.execute("SELECT value FROM index_meta WHERE key='provider'").fetchone()
        assert row[0] == "hash-ngram-v1"
    finally:
        connection.close()


def test_canon_build_embeddings_unknown_provider(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source.txt"
    source.write_text(CORPUS, encoding="utf-8")
    db_path = tmp_path / "canon.sqlite3"
    index_path = tmp_path / "embeddings.sqlite3"
    assert main(["canon", "build", "--source", str(source), "--db", str(db_path)]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "canon",
                "build-embeddings",
                "--db",
                str(db_path),
                "--index",
                str(index_path),
                "--provider",
                "openai",
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unknown embedding provider" in captured.err
    assert "Traceback" not in captured.err


def _candidate_batch(tmp_path: Path) -> Path:
    candidate = {
        "batch_id": "V001",
        "source_volume": 1,
        "source_unit_ids": ["U0001"],
        "entities": [
            {
                "entity_id": "E0001",
                "name": "鲁迪乌斯",
                "aliases": ["鲁迪"],
                "kind": "CHARACTER",
                "introduced_volume": 1,
                "introduced_line": 3,
                "description": "主角。",
            }
        ],
        "facts": [
            {
                "fact_id": "F0001",
                "entity_id": "E0001",
                "predicate": "爱好",
                "object_value": "读书",
                "start_date": "408-1",
                "end_date": None,
                "date_precision": "YEAR_ONLY",
                "evidence_volumes": [1],
                "evidence_lines": [[4, 5]],
                "confidence": "EXPLICIT",
                "visible_from_volume": 1,
                "visible_to_volume": None,
            }
        ],
        "relationships": [],
        "knowledge": [],
        "events": [],
        "phases": [],
    }
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")
    return path


def test_canon_verify_command_clean_batch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source.txt"
    source.write_text(CORPUS, encoding="utf-8")
    candidate = _candidate_batch(tmp_path)
    report = tmp_path / "report.json"

    assert (
        main(
            [
                "canon",
                "verify",
                "--source",
                str(source),
                "--candidate",
                str(candidate),
                "--out",
                str(report),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["is_clean"] is True
    assert payload["errors"] == []
    assert report.is_file()


def test_canon_verify_command_dirty_batch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source.txt"
    source.write_text(CORPUS, encoding="utf-8")
    candidate = _candidate_batch(tmp_path)
    report = tmp_path / "report.json"
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    payload["facts"][0]["evidence_lines"] = [[90, 95]]
    candidate.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    assert (
        main(
            [
                "canon",
                "verify",
                "--source",
                str(source),
                "--candidate",
                str(candidate),
                "--out",
                str(report),
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["is_clean"] is False
    assert any(error["code"] == "evidence_lines" for error in result["errors"])
    assert "cannot apply" in captured.err


def test_canon_verify_command_missing_candidate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source.txt"
    source.write_text(CORPUS, encoding="utf-8")
    report = tmp_path / "report.json"

    assert (
        main(
            [
                "canon",
                "verify",
                "--source",
                str(source),
                "--candidate",
                str(tmp_path / "nope.json"),
                "--out",
                str(report),
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert "cannot read candidate" in captured.err
    assert "Traceback" not in captured.err


def test_canon_apply_command_applies_clean_batch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import sqlite3

    source = tmp_path / "source.txt"
    source.write_text(CORPUS, encoding="utf-8")
    candidate = _candidate_batch(tmp_path)
    db_path = tmp_path / "canon.sqlite3"
    assert main(["canon", "build", "--source", str(source), "--db", str(db_path)]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "canon",
                "apply",
                "--db",
                str(db_path),
                "--source",
                str(source),
                "--candidate",
                str(candidate),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert summary["batch_id"] == "V001"
    assert summary["entities"] == 1
    assert summary["facts"] == 1
    connection = sqlite3.connect(db_path)
    try:
        count = connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        assert count == 1
        batch = connection.execute(
            "SELECT verified_at FROM extraction_batches WHERE batch_id='V001'"
        ).fetchone()[0]
        assert batch == "verified"
    finally:
        connection.close()


def test_canon_apply_command_refuses_dirty_batch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import sqlite3

    source = tmp_path / "source.txt"
    source.write_text(CORPUS, encoding="utf-8")
    candidate = _candidate_batch(tmp_path)
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    payload["facts"][0]["evidence_lines"] = [[90, 95]]
    candidate.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    db_path = tmp_path / "canon.sqlite3"
    assert main(["canon", "build", "--source", str(source), "--db", str(db_path)]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "canon",
                "apply",
                "--db",
                str(db_path),
                "--source",
                str(source),
                "--candidate",
                str(candidate),
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert "verification failed" in captured.err
    connection = sqlite3.connect(db_path)
    try:
        count = connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        assert count == 0
    finally:
        connection.close()


def test_canon_enrich_apply_command_applies_clean_batch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import sqlite3

    from overlord_worldsim.canon.extract_model import ExtractionBatch

    from .enrich_fixtures import (
        CORPUS as ENRICH_CORPUS,
    )
    from .enrich_fixtures import (
        ENTITIES,
        RELATIONSHIPS,
        TIMELINE_EVENTS,
        make_batch,
    )

    source = tmp_path / "source.txt"
    source.write_text(ENRICH_CORPUS, encoding="utf-8")

    canon_dir = tmp_path / "canon"
    canon_dir.mkdir()
    registry_batch = ExtractionBatch(
        batch_id="V001",
        source_volume=1,
        source_unit_ids=("U0001", "U0002", "U0003"),
        entities=ENTITIES,
        facts=(),
        relationships=RELATIONSHIPS,
        knowledge=(),
        events=TIMELINE_EVENTS,
        phases=(),
    )
    (canon_dir / "V001.json").write_text(
        json.dumps(registry_batch.to_json(), ensure_ascii=False), encoding="utf-8"
    )

    content_dir = tmp_path / "enrich"
    content_dir.mkdir()
    (content_dir / "V001.json").write_text(
        json.dumps(make_batch().to_json(), ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "canon.sqlite3"
    assert main(["canon", "build", "--source", str(source), "--db", str(db_path)]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "canon",
                "enrich-apply",
                "--db",
                str(db_path),
                "--content",
                str(content_dir),
                "--source",
                str(source),
                "--canon",
                str(canon_dir),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["summary"]["character_profiles"] == 1
    assert payload["summary"]["behavior_cases"] == 1
    assert payload["manifest"]["content_sha256"]

    connection = sqlite3.connect(db_path)
    try:
        profiles = connection.execute("SELECT COUNT(*) FROM character_profiles").fetchone()[0]
        assert profiles == 1
        cases = connection.execute("SELECT COUNT(*) FROM behavior_cases").fetchone()[0]
        assert cases == 1
    finally:
        connection.close()
