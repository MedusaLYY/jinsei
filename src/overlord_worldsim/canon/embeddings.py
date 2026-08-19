"""Pluggable embedding providers and offline embedding index (data/indexes/).

The build requires zero ML dependencies: providers are optional and swapped
in through `register_provider`. Without a provider the pipeline degrades to
BM25-only search; no provider is ever auto-selected for query semantics.
"""

from __future__ import annotations

import hashlib
import math
import sqlite3
from pathlib import Path
from typing import Protocol, runtime_checkable

from overlord_worldsim.canon.loader import open_canon_db

_PROVIDERS: dict[str, EmbeddingProvider] = {}

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS embeddings (
    chunk_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    dimension INTEGER NOT NULL,
    vector BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS index_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for deterministic offline embedding providers."""

    @property
    def name(self) -> str: ...

    @property
    def dimension(self) -> int: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashEmbeddingProvider:
    """Reference provider: deterministic char-bigram hashing into a fixed vector.

    Offline test reference only; never used for production semantics.
    """

    def __init__(self, *, dimension: int = 256) -> None:
        if not 16 <= dimension <= 4096:
            raise ValueError("dimension out of range")
        self._dimension = dimension

    @property
    def name(self) -> str:
        return "hash-ngram-v1"

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self._dimension
        bigrams = [text[i : i + 2] for i in range(max(len(text) - 1, 0))]
        for bigram in bigrams:
            digest = hashlib.sha256(bigram.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self._dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


def register_provider(name: str, provider: EmbeddingProvider) -> EmbeddingProvider:
    """Register a provider by name; returns it for chaining."""
    if not isinstance(provider, EmbeddingProvider):
        raise TypeError("provider must implement EmbeddingProvider")
    _PROVIDERS[name] = provider
    return provider


def get_provider(name: str) -> EmbeddingProvider | None:
    return _PROVIDERS.get(name)


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def build_embedding_index(db_path: Path, index_path: Path, provider: EmbeddingProvider) -> Path:
    """Embed every chunk and store vectors in an offline index database."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(index_path)
    try:
        connection.executescript(_SCHEMA_SQL)
        connection.execute("DELETE FROM embeddings")
        connection.execute("DELETE FROM index_meta")
        canon = open_canon_db(db_path)
        try:
            rows = canon.execute("SELECT chunk_id, text FROM chunks ORDER BY chunk_id").fetchall()
            chunk_ids = [row["chunk_id"] for row in rows]
            texts = [row["text"] for row in rows]
        finally:
            canon.close()
        vectors = provider.embed(texts)
        connection.executemany(
            "INSERT INTO embeddings(chunk_id, provider, dimension, vector) VALUES (?, ?, ?, ?)",
            [
                (chunk_id, provider.name, provider.dimension, _pack(vector))
                for chunk_id, vector in zip(chunk_ids, vectors, strict=True)
            ],
        )
        connection.executemany(
            "INSERT INTO index_meta(key, value) VALUES (?, ?)",
            [("provider", provider.name), ("dimension", str(provider.dimension))],
        )
        connection.commit()
    finally:
        connection.close()
    return index_path


def query_embedding_index(
    index_path: Path,
    text: str,
    provider: EmbeddingProvider,
    *,
    top_k: int = 20,
) -> list[tuple[str, float]]:
    """Cosine-nearest chunk ids for a query text (pure read)."""
    if not text or not text.strip():
        raise ValueError("text must be non-empty")
    if not 1 <= top_k <= 500:
        raise ValueError("top_k out of range")
    vector = provider.embed([text])[0]
    connection = sqlite3.connect(index_path)
    try:
        rows = connection.execute(
            "SELECT chunk_id, vector FROM embeddings WHERE provider = ?",
            (provider.name,),
        ).fetchall()
        scored: list[tuple[str, float]] = []
        for chunk_id, blob in rows:
            stored = _unpack(blob)
            if len(stored) != len(vector):
                continue
            scored.append((chunk_id, _cosine(vector, stored)))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]
    finally:
        connection.close()


def _pack(vector: list[float]) -> bytes:
    import struct

    return struct.pack(f"<{len(vector)}f", *vector)


def _unpack(blob: bytes) -> list[float]:
    import struct

    return list(struct.unpack(f"<{len(blob) // 4}f", blob))
