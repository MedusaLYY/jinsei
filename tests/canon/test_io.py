"""Tests for canon artifact serialization to data/parsed/."""

from __future__ import annotations

import json
from pathlib import Path

from overlord_worldsim.canon.io import write_parsed
from overlord_worldsim.canon.parse import parse_source

CORPUS = (
    "★☆★☆★☆轻小说文库(Www.WenKu8.Com)☆★☆★☆★\n"
    "<无职转生～到了异世界就拿出真本事～(无职转生~在异世界认真地活下去~)>\n"
    "第一卷 幼年期 序章\n"
    "\n"
    "    第一段正文。\n"
    "\n"
    "    第二段正文。\n"
    "\n"
    "第一卷 幼年期 第一话「测试章节」\n"
    "\n"
    "    正文一。\n"
    "\n"
    "    ※\n"
    "\n"
    "    正文二。\n"
    "\n"
    "第一卷 幼年期 插图\n"
    "\n"
    "短篇 广播剧特典 样例短篇\n"
    "\n"
    "    网译版\n"
    "\n"
    "    翻译：某人\n"
    "\n"
    "    尾巴第一段。\n"
)


def test_write_parsed_creates_all_artifacts(tmp_path: Path) -> None:
    doc = parse_source(CORPUS, source_name="corpus.txt")
    out = write_parsed(doc, tmp_path)
    assert (out / "volumes.json").is_file()
    assert (out / "chapters.json").is_file()
    assert (out / "scenes.jsonl").is_file()
    assert (out / "chunks.jsonl").is_file()
    assert (out / "parse_report.jsonl").is_file()
    assert (out / "summary.json").is_file()

    volumes = json.loads((out / "volumes.json").read_text(encoding="utf-8"))
    assert volumes["version"] == "1.0.0"
    assert volumes["source"] == "corpus.txt"
    assert len(volumes["volumes"]) == 1

    chapters = json.loads((out / "chapters.json").read_text(encoding="utf-8"))
    assert len(chapters["units"]) == 4

    scenes = [
        json.loads(line) for line in (out / "scenes.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(scenes) == 4
    chunks = [
        json.loads(line) for line in (out / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(chunks) == 4
    assert chunks[0]["source_start_line"] == 5
    assert chunks[0]["text"] == "第一段正文。\n第二段正文。"

    report = [
        json.loads(line)
        for line in (out / "parse_report.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert any(entry["reason"] == "banner" for entry in report)
    assert any(entry["reason"] == "file_title" for entry in report)
    assert any(entry["reason"] == "unit_metadata" for entry in report)

    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["volume_count"] == 1
    assert summary["unit_count"] == 4
    assert summary["chunk_count"] == 4


def test_write_parsed_is_deterministic(tmp_path: Path) -> None:
    doc = parse_source(CORPUS, source_name="corpus.txt")
    first = write_parsed(doc, tmp_path / "a")
    second = write_parsed(parse_source(CORPUS, source_name="corpus.txt"), tmp_path / "b")
    for name in ("volumes.json", "chapters.json", "scenes.jsonl", "chunks.jsonl", "summary.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
