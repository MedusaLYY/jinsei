"""Tests for the pluggable embedding provider and offline index."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from overlord_worldsim.canon.embeddings import (
    HashEmbeddingProvider,
    build_embedding_index,
    query_embedding_index,
    register_provider,
)
from overlord_worldsim.canon.loader import build_canon_db
from overlord_worldsim.canon.parse import parse_source

CORPUS = (
    "第一卷 幼年期 序章\n"
    "\n"
    "    希露菲的头发是银色的。\n"
    "\n"
    "    鲁迪乌斯记得上辈子的记忆。\n"
    "\n"
    "第一卷 幼年期 第一话「测试章节」\n"
    "\n"
    "    保罗是鲁迪乌斯的父亲。\n"
)


def _db(tmp_path: Path) -> Path:
    doc = parse_source(CORPUS, source_name="corpus.txt")
    return build_canon_db(doc, tmp_path / "canon.sqlite3", sha256="abc123")


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return _db(tmp_path)


def test_hash_provider_is_deterministic_and_registered() -> None:
    provider = HashEmbeddingProvider(dimension=64)
    first = provider.embed(["希露菲的头发是银色的。", "保罗挥舞着剑。"])
    second = provider.embed(["希露菲的头发是银色的。", "保罗挥舞着剑。"])
    assert first == second
    assert all(len(vector) == 64 for vector in first)
    assert isinstance(provider.name, str)
    assert register_provider("hash", provider) is provider


def test_register_provider_rejects_non_provider() -> None:
    with pytest.raises(TypeError, match="EmbeddingProvider"):
        register_provider("bad", object())  # type: ignore[arg-type]


def test_build_embedding_index_writes_rows(db_path: Path) -> None:
    index_path = db_path.parent / "embeddings.sqlite3"
    provider = HashEmbeddingProvider(dimension=32)
    build_embedding_index(db_path, index_path, provider)
    connection = sqlite3.connect(index_path)
    try:
        count = connection.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        assert count == 2
        row = connection.execute("SELECT chunk_id, provider, dimension FROM embeddings").fetchone()
        assert row[0] == "C000001"
        assert row[1] == "hash-ngram-v1"
        assert row[2] == 32
    finally:
        connection.close()


def test_build_embedding_index_is_idempotent(db_path: Path) -> None:
    index_path = db_path.parent / "embeddings.sqlite3"
    provider = HashEmbeddingProvider(dimension=32)
    build_embedding_index(db_path, index_path, provider)
    build_embedding_index(db_path, index_path, provider)
    connection = sqlite3.connect(index_path)
    try:
        count = connection.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        assert count == 2
    finally:
        connection.close()


def test_query_embedding_index_returns_sorted_chunk_ids(db_path: Path) -> None:
    index_path = db_path.parent / "embeddings.sqlite3"
    provider = HashEmbeddingProvider(dimension=64)
    build_embedding_index(db_path, index_path, provider)
    results = query_embedding_index(index_path, "银色的头发", provider, top_k=5)
    assert [chunk_id for chunk_id, _ in results] == ["C000001", "C000002"]
    assert results[0][1] >= 0.0


def test_query_embedding_index_validates_top_k(db_path: Path) -> None:
    index_path = db_path.parent / "embeddings.sqlite3"
    provider = HashEmbeddingProvider(dimension=64)
    build_embedding_index(db_path, index_path, provider)
    with pytest.raises(ValueError, match="top_k"):
        query_embedding_index(index_path, "头发", provider, top_k=0)
    with pytest.raises(ValueError, match="non-empty"):
        query_embedding_index(index_path, "   ", provider)


def test_hash_provider_rejects_bad_dimension() -> None:
    with pytest.raises(ValueError, match="dimension"):
        HashEmbeddingProvider(dimension=4)


def test_query_skips_dimension_mismatch_rows(db_path: Path) -> None:
    index_path = db_path.parent / "embeddings.sqlite3"
    build_embedding_index(db_path, index_path, HashEmbeddingProvider(dimension=64))
    other = HashEmbeddingProvider(dimension=32)
    results = query_embedding_index(index_path, "希露菲", other)
    assert results == []
