"""Serialization of parsed canon artifacts to data/parsed/."""

from __future__ import annotations

import json
from pathlib import Path

from overlord_worldsim.canon.parse import ParsedDocument


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def write_parsed(doc: ParsedDocument, out_dir: Path) -> Path:
    """Write all parsed artifacts deterministically; returns out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "volumes.json").write_text(
        json.dumps(doc.to_volumes_json(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "chapters.json").write_text(
        json.dumps(doc.to_units_json(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_jsonl(out_dir / "scenes.jsonl", doc.to_scenes_jsonl())
    _write_jsonl(out_dir / "chunks.jsonl", doc.to_chunks_jsonl())
    _write_jsonl(out_dir / "parse_report.jsonl", doc.to_report_jsonl())
    (out_dir / "summary.json").write_text(
        json.dumps(doc.to_summary(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_dir
