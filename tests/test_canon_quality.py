from __future__ import annotations

import json
import pathlib

from tools.canon_quality_check import (
    build_quarantine_report,
    check_manifest,
    contains_template,
    score_record,
    score_volume,
)


def test_contains_template_detects_placeholders() -> None:
    assert contains_template("V03 依该卷事件推进人物状态演进（证据见该卷证据段）。")
    assert contains_template("阶段性收束并为后事铺垫")
    assert contains_template("形塑后卷人际与立场")
    assert contains_template("为后事提供前提")
    assert contains_template("见该卷证据段")
    assert not contains_template("刚接触魔术教科书，尝试咏唱水弹。")
    assert not contains_template("阿斯拉王国的政变由贵族派系推动")


def test_score_record_100_grounded() -> None:
    obj = {
        "case_id": "BC00001",
        "context": "刚接触魔术教科书，尝试咏唱水弹并在庭院中练习。",
        "trigger": "洛琪希布置了每日咏唱训练任务",
        "evidence_refs": ("EV00001",),
    }
    sc, _ = score_record(obj, {"EV00001"})
    assert sc == 100


def test_score_record_0_template() -> None:
    obj = {
        "case_id": "BC03001",
        "context": "V03 场景1：少年期 冒险者入门篇中的人际/委托场景",
        "trigger": "触发1：对方请求或突发事件",
        "evidence_refs": ("EV03001",),
    }
    sc, reasons = score_record(obj, {"EV03001"})
    assert sc == 0
    assert "template_pollution" in reasons


def test_score_record_0_missing_evidence() -> None:
    obj = {"case_id": "BC00002", "context": "某个具体场景描述文本足够长以判定", "evidence_refs": ()}
    sc, reasons = score_record(obj, set())
    assert sc == 0
    assert "missing_evidence" in reasons


def test_score_record_60_thin() -> None:
    obj = {"case_id": "BC00003", "context": "短句", "evidence_refs": ("EV00001",)}
    sc, _ = score_record(obj, {"EV00001"})
    assert sc == 60


def test_score_volume_v001_passes_threshold() -> None:
    vs = score_volume(1)
    assert vs.score >= 60
    assert vs.quarantine_recommended is False


def test_score_volume_polluted_volumes_flagged() -> None:
    # V003 was rebuilt in Wave 1 (外传-grounded, natural count 19) and now scores ≥60.
    vs3 = score_volume(3)
    assert vs3.score >= 60, f"V003 should be rebuilt: {vs3.score}"
    assert "template_entries" not in vs3.issues
    for v in [7, 15, 19, 20]:
        vs = score_volume(v)
        assert vs.score < 50, f"V{v:03d} should be low: {vs.score}"
        assert vs.quarantine_recommended is True
        assert "template_entries" in vs.issues


def test_check_manifest_detects_generic() -> None:
    info = check_manifest()
    assert info["generic_generation_probability"] is True
    # Wave 1 rebuilt V003 from fixed-41 template (19 records); V004/V006 already
    # rebuilt to 72, so fixed-41 drops 15→12.
    assert info["fixed_41_count"] == 12
    assert "ENRICH_V003" not in info["fixed_41_volumes"]


def test_quarantine_report_exists_and_counts() -> None:
    info = build_quarantine_report()
    assert info["exists"] is True
    assert info["invalid_entries_count"] == 615
    assert info["by_reason"]["template_pollution"] == 615


def test_canon_quality_score_json_schema() -> None:
    p = pathlib.Path("CANON_QUALITY_SCORE.json")
    assert p.exists(), "must run tools/canon_quality_check.py --audit first"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "volumes" in data and len(data["volumes"]) == 26
    for v in data["volumes"]:
        assert "volume" in v and "score" in v and "issues" in v
        assert 0 <= v["score"] <= 100
