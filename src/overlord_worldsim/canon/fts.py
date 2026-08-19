"""Full-text search over the canon database using FTS5 trigram + BM25.

Query commands are pure reads: no writes, no time, no RNG. Results reference
verbatim source line ranges so the raw text stays authoritative.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from overlord_worldsim.canon.loader import open_canon_db

_MAX_QUERY_CHARS = 128
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_UNBALANCED_QUOTE = re.compile(r"^[^\"]*\"[^\"]*$")

_SELECT_SQL = """
SELECT c.chunk_id, c.unit_id, c.scene_id, c.volume_no, c.chapter_title,
       c.source_start_line, c.source_end_line, c.text,
       bm25(chunks_fts) AS score
FROM chunks_fts
JOIN chunks c ON c.rowid = chunks_fts.rowid
JOIN units u ON u.unit_id = c.unit_id
WHERE chunks_fts MATCH ?
{filter_sql}
ORDER BY score
LIMIT ?
"""


@dataclass(frozen=True)
class SearchHit:
    """One full-text match with its location and verbatim text."""

    chunk_id: str
    unit_id: str
    scene_id: str
    volume_no: int | None
    chapter_title: str
    source_start_line: int
    source_end_line: int
    text: str
    score: float


def _validate_query(query: str) -> None:
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")
    if len(query) > _MAX_QUERY_CHARS:
        raise ValueError(f"query must be at most {_MAX_QUERY_CHARS} characters")
    if _CONTROL_CHARS.search(query):
        raise ValueError("query contains control characters")
    if query.count('"') % 2 != 0:
        raise ValueError("query has unbalanced quotes")
    if " OR " in query and '"' not in query:
        raise ValueError("query with OR requires quoted phrases")


def _validate_filters(*, volume_no: int | None, canon_layer: str | None, limit: int) -> str:
    if volume_no is not None and not 1 <= volume_no <= 999:
        raise ValueError("volume_no out of range")
    if canon_layer is not None and canon_layer not in ("CORE", "UNKNOWN"):
        raise ValueError("canon_layer must be CORE or UNKNOWN")
    if not 1 <= limit <= 500:
        raise ValueError("limit out of range")
    filters: list[str] = []
    if volume_no is not None:
        filters.append("AND c.volume_no = ?")
    if canon_layer is not None:
        filters.append("AND u.canon_layer = ?")
    return "\n".join(filters)


def search_canon_text(
    db_path: Path,
    query: str,
    *,
    volume_no: int | None = None,
    canon_layer: str | None = None,
    limit: int = 20,
) -> list[SearchHit]:
    """Run an FTS5 BM25 search; returns hits ordered by relevance."""
    _validate_query(query)
    filter_sql = _validate_filters(volume_no=volume_no, canon_layer=canon_layer, limit=limit)
    parameters: list[object] = [query]
    if volume_no is not None:
        parameters.append(volume_no)
    if canon_layer is not None:
        parameters.append(canon_layer)
    parameters.append(limit)

    connection = open_canon_db(db_path)
    try:
        rows = connection.execute(_SELECT_SQL.format(filter_sql=filter_sql), parameters).fetchall()
        return [
            SearchHit(
                chunk_id=row["chunk_id"],
                unit_id=row["unit_id"],
                scene_id=row["scene_id"],
                volume_no=row["volume_no"],
                chapter_title=row["chapter_title"],
                source_start_line=row["source_start_line"],
                source_end_line=row["source_end_line"],
                text=row["text"],
                score=float(row["score"]),
            )
            for row in rows
        ]
    except sqlite3.OperationalError as error:
        raise ValueError(f"invalid search query: {error}") from error
    finally:
        connection.close()
