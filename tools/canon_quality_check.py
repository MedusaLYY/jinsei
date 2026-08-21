"""Canon Quality Checker — Phase 2-A semantic gate.

Scores every enrichment record 0/60/100 and emits per-volume rollups.

100: has source_volume + source_unit evidence + explicit entity/fact usable for sim
60 : has source but info is simple / thin
0  : template / no source / hallucination / empty

Also checks manifest batch_counts finger-print (41 fixed) and encoding.

Usage:
  PYTHONPATH=src python tools/canon_quality_check.py --audit
  PYTHONPATH=src python tools/canon_quality_check.py --check-manifest
  PYTHONPATH=src python tools/canon_quality_check.py --quarantine-report

Sources of truth: data/canon_enriched/V*.json (authored), data/canon/ (registry).
Never invents content; only inspects.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

ENRICHED_DIR = pathlib.Path("data/canon_enriched")
CANON_DIR = pathlib.Path("data/canon")
QUARANTINE_DIR = pathlib.Path("data/canon_quarantine")
SCORE_PATH = pathlib.Path("CANON_QUALITY_SCORE.json")
MANIFEST_PATH = ENRICHED_DIR / "manifest.json"

# Deterministic placeholder fingerprints observed from build_enrich_generic.py
TEMPLATE_SUBSTRINGS: tuple[str, ...] = (
    "见证据段",
    "见该卷",
    "见该卷证据段",
    "依该卷事件推进",
    "阶段性收束并为后事铺垫",
    "形塑后卷",
    "为后事提供前提",
    "权衡后协作",
    "当卷可见的对话",
    "取得局部进展",
    "为人际与后续事件奠基",
    "完成本卷委托",
    "阶段性人格侧重见证据段",
    "中魔术/能力运用的一般约束见该卷演示",
    "阶段的社会与委托范式见该卷场景",
    "协作深化",
    "认为按当前情报行事",
    "触发条件小节",
    "要事",
    "小节",
    "长期影响",
    "既有关系",
    "未定",
    "E0001在场",
    "E0001 主导推进",
    "人际/委托场景",
    "对方请求或突发事件",
    "推动后卷发展",
    "影响后续关系",
    "塑造未来局势",
    "推动发展",
    "影响剧情",
    "产生影响",
    "后续未知",
    "待补全",
)

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")


def contains_template(text: str) -> bool:
    if not text:
        return False
    for pat in TEMPLATE_SUBSTRINGS:
        if pat in text:
            # short generic tokens like 要事/小节 need disambiguation
            if pat in ("要事", "小节", "未定", "长期影响", "既有关系"):
                # only flag when combined with Vxx prefix or surrounding template
                if re.search(r"V\d{2}.*" + re.escape(pat), text) or (
                    pat == "未定" and text.strip() == "未定"
                ):
                    return True
                if pat in ("要事", "小节") and re.search(r"V\d{2}\s*要事\d+", text):
                    return True
                continue
            return True
    return "人际/委托场景" in text


def has_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text))


def text_is_empty(text: Any) -> bool:
    if text is None:
        return True
    if isinstance(text, str):
        return text.strip() == ""
    return False


def _is_shallow_personality(obj: dict[str, Any]) -> bool:
    """True if profile only has adjective personality_traits and no deep layers."""
    if "profile_id" not in obj or "personality_traits" not in obj:
        return False
    traits = obj.get("personality_traits")
    if not isinstance(traits, (list, tuple)) or not traits:
        return False
    core = obj.get("core_personality", [])
    surface = obj.get("surface_personality", [])
    hidden = obj.get("hidden_personality", [])
    # empty deep layers -> shallow
    core_empty = not core if isinstance(core, (list, tuple)) else not core
    surface_empty = not surface if isinstance(surface, (list, tuple)) else not surface
    hidden_empty = not hidden if isinstance(hidden, (list, tuple)) else not hidden
    return bool(core_empty and surface_empty and hidden_empty)


def _quirk_missing_overplay(obj: dict[str, Any]) -> bool:
    """COLOR-weight quirk/rule without overplay_warning."""
    if "quirk_id" in obj:
        weight = obj.get("simulation_weight")
        warning = obj.get("overplay_warning")
        return weight == "COLOR" and (
            not warning or (isinstance(warning, str) and not warning.strip())
        )
    if "rule_id" in obj:
        weight = obj.get("simulation_weight")
        warning = obj.get("overplay_warning")
        return weight == "COLOR" and (
            not warning or (isinstance(warning, str) and not warning.strip())
        )
    return False


def score_record(
    obj: dict[str, Any], evidence_ids: set[str], *, strict_personality: bool = False
) -> tuple[int, list[str]]:
    """Return (score 0/60/100, reasons). Deterministic, no external knowledge."""
    reasons: list[str] = []

    # collect all string values for template scan
    all_strings: list[str] = []
    for v in obj.values():
        if isinstance(v, str):
            all_strings.append(v)
        elif isinstance(v, (list, tuple)):
            for e in v:
                if isinstance(e, str):
                    all_strings.append(e)

    # 0: encoding error
    for s in all_strings:
        if "\ufffd" in s or CYRILLIC_RE.search(s):
            reasons.append("encoding_error")
            return 0, reasons

    # 0: template pollution
    for s in all_strings:
        if contains_template(s):
            reasons.append("template_pollution")
            return 0, reasons

    # 0: strict personality / overplay gates (only for newly rebuilt volumes)
    if strict_personality:
        if _is_shallow_personality(obj):
            reasons.append("shallow_personality")
            return 0, reasons
        if _quirk_missing_overplay(obj):
            reasons.append("missing_overplay_warning")
            return 0, reasons

    # 0: missing source (enrichment records must carry evidence_refs)
    if "evidence_refs" in obj:
        refs = obj.get("evidence_refs")
        if not refs:
            reasons.append("missing_evidence")
            return 0, reasons
        # refs point outside batch
        for rid in refs if isinstance(refs, (list, tuple)) else []:
            if isinstance(rid, str) and rid not in evidence_ids:
                reasons.append("dangling_evidence_ref")
                return 0, reasons

    # 0: empty critical descriptive fields
    # behavior_cases / profiles / events all have a primary text field
    critical_keys = (
        "context",
        "summary",
        "title",
        "trigger",
        "outcome",
        "statement",
        "description",
        "note",
    )
    has_critical = any(k in obj for k in critical_keys)
    if has_critical:
        for k in critical_keys:
            if k in obj and text_is_empty(obj[k]):
                reasons.append(f"empty_{k}")
                return 0, reasons

    # Determine richness for 60 vs 100
    # 60: has source but thin (short CJK or trivial)
    # Heuristic: primary text length
    primary_text = ""
    for k in ("context", "summary", "title", "statement", "description", "outcome", "trigger"):
        if k in obj and isinstance(obj[k], str) and obj[k].strip():
            primary_text = obj[k].strip()
            break
    if not primary_text:
        # items without primary text but with evidence still count as 60 if not template
        if "evidence_refs" in obj and obj.get("evidence_refs"):
            return 60, ["thin_but_grounded"]
        return 0, ["empty_primary"]

    cjk_len = sum(1 for c in primary_text if "\u4e00" <= c <= "\u9fff")
    total_len = len(primary_text)
    # thin: very short or no CJK in a CJK corpus expected
    if total_len < 16 or (has_cjk(primary_text) and cjk_len < 6):
        reasons.append("thin_content")
        return 60, reasons
    # contains generic scaffold like "V03" prefix without substantive content
    if re.match(r"^V\d{2}\s", primary_text) and total_len < 28:
        reasons.append("prefixed_thin")
        return 60, reasons

    return 100, ["grounded"]


@dataclass(frozen=True)
class VolumeScore:
    volume: str
    score: int
    total_records: int
    counts_by_score: dict[str, int]
    issues: list[str]
    quarantine_recommended: bool


def score_volume(volume_no: int) -> VolumeScore:
    path = ENRICHED_DIR / f"V{volume_no:03d}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    evidence_ids: set[str] = {
        str(e.get("evidence_id"))
        for e in data.get("evidence", [])
        if isinstance(e, dict) and isinstance(e.get("evidence_id"), str)
    }

    # all collections that are enrichment records (exclude meta keys)
    collections = [
        "evidence",
        "character_profiles",
        "behavior_cases",
        "detailed_events",
        "items",
        "item_instances",
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
        "character_quirks",
        "character_preferences",
        "body_language_profiles",
        "character_personas",
        "canon_conflicts",
        "canon_gaps",
        "behavior_rules",
    ]

    scores: list[int] = []
    reasons_all: list[str] = []
    # Evidence entries themselves: score on chapter_title/note
    for ev in data.get("evidence", []):
        # evidence is grounding, not scored as 0/60/100 for volume rollup in same way
        # but we check for template in note/chapter_title
        tmp = False
        for k in ("note", "chapter_title"):
            v = ev.get(k, "")
            if isinstance(v, str) and contains_template(v):
                tmp = True
        if tmp:
            scores.append(0)
            reasons_all.append("template_pollution")
        elif text_is_empty(ev.get("note")) and text_is_empty(ev.get("chapter_title")):
            scores.append(0)
            reasons_all.append("empty_evidence")
        else:
            # evidence with real lines -> 100 if not template, else 60
            nt = ev.get("note", "")
            if isinstance(nt, str) and len(nt.strip()) < 10:
                scores.append(60)
                reasons_all.append("thin_evidence")
            else:
                scores.append(100)
                reasons_all.append("grounded")

    # strict personality / overplay gates only for newly rebuilt volumes
    # (those carrying the behavior_rules collection)
    strict = "behavior_rules" in data

    for coll in collections:
        if coll == "evidence":
            continue
        for obj in data.get(coll, []):
            sc, rs = score_record(
                obj if isinstance(obj, dict) else {},
                evidence_ids,
                strict_personality=strict,
            )
            scores.append(sc)
            reasons_all.extend(rs)
    # issues derived after loop — include personality/overplay gates
    # so Wave 1+ rebuilt volumes surface them

    total = len(scores)
    avg = 0 if total == 0 else round(sum(scores) / total)

    cnt = Counter(scores)
    counts_by_score = {"100": cnt.get(100, 0), "60": cnt.get(60, 0), "0": cnt.get(0, 0)}

    # derive issues list
    issues: list[str] = []
    if cnt.get(0, 0) > 0:
        # classify
        if any("template" in r for r in reasons_all):
            issues.append("template_entries")
        if any("missing_evidence" in r or "dangling" in r for r in reasons_all):
            issues.append("missing_evidence")
        if any("encoding_error" in r for r in reasons_all):
            issues.append("encoding_error")
        if any("shallow_personality" in r for r in reasons_all):
            issues.append("shallow_personality")
        if any("missing_overplay_warning" in r for r in reasons_all):
            issues.append("missing_overplay_warning")
        if not issues:
            issues.append("low_quality_entries")
    if cnt.get(60, 0) / max(total, 1) > 0.3:
        issues.append("thin_content")
    # duplicate detection: identical primary texts within volume
    seen: Counter[str] = Counter()
    for coll in collections:
        if coll == "evidence":
            continue
        for obj in data.get(coll, []):
            if not isinstance(obj, dict):
                continue
            for k in ("context", "summary", "title", "trigger", "outcome", "statement"):
                if k in obj and isinstance(obj[k], str) and obj[k].strip():
                    seen[obj[k].strip()] += 1
    dups = sum(1 for _, c in seen.items() if c >= 3)
    if dups > 0:
        issues.append("duplicate_templates")

    # quarantine recommendation: template rate > 30% or known fixed-41 volumes
    quarantine = cnt.get(0, 0) / max(total, 1) >= 0.3 or volume_no in [*range(3, 16), 19, 20]

    # keep issues deduplicated, stable order
    issues = sorted(set(issues))
    return VolumeScore(
        volume=f"V{volume_no:03d}",
        score=avg,
        total_records=total,
        counts_by_score=counts_by_score,
        issues=issues,
        quarantine_recommended=quarantine,
    )


def check_manifest() -> dict[str, Any]:
    raw = MANIFEST_PATH.read_text(encoding="utf-8")
    manifest = json.loads(raw)
    batch_counts_raw = manifest.get("batch_counts", "{}")
    try:
        batch_counts: dict[str, int] = (
            json.loads(batch_counts_raw)
            if isinstance(batch_counts_raw, str)
            else dict(batch_counts_raw)
        )
    except Exception:
        batch_counts = {}
    dist = Counter(batch_counts.values())
    fixed_41 = [k for k, v in batch_counts.items() if v == 41]
    generic_prob = len(fixed_41) >= 3
    return {
        "manifest_path": str(MANIFEST_PATH),
        "batch_counts": batch_counts,
        "distribution": dict(dist),
        "generic_generation_probability": generic_prob,
        "fixed_41_volumes": sorted(fixed_41),
        "fixed_41_count": len(fixed_41),
        "verdict": "HIGH generic risk" if generic_prob else "ok",
    }


def build_quarantine_report() -> dict[str, Any]:
    invalid_path = QUARANTINE_DIR / "invalid_entries.json"
    manifest_analysis_path = QUARANTINE_DIR / "manifest_analysis.json"
    result: dict[str, Any] = {
        "quarantine_dir": str(QUARANTINE_DIR),
        "invalid_entries_path": str(invalid_path),
        "exists": invalid_path.exists(),
    }
    if invalid_path.exists():
        entries = json.loads(invalid_path.read_text(encoding="utf-8"))
        result["invalid_entries_count"] = len(entries)
        result["by_reason"] = dict(Counter(e.get("reason", "unknown") for e in entries))
        result["by_type"] = dict(Counter(e.get("type", "unknown") for e in entries))
        result["by_source_file"] = dict(Counter(e.get("source_file", "unknown") for e in entries))
    if manifest_analysis_path.exists():
        result["manifest_analysis"] = json.loads(manifest_analysis_path.read_text(encoding="utf-8"))
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Canon Quality Checker")
    ap.add_argument(
        "--audit",
        action="store_true",
        help="run per-volume audit and write CANON_QUALITY_SCORE.json",
    )
    ap.add_argument(
        "--check-manifest",
        action="store_true",
        help="check manifest batch_counts for generic fingerprint",
    )
    ap.add_argument("--quarantine-report", action="store_true", help="report quarantine status")
    ap.add_argument("--output", type=str, default=str(SCORE_PATH), help="output path for audit")
    args = ap.parse_args()

    if not (args.audit or args.check_manifest or args.quarantine_report):
        args.audit = True

    if args.check_manifest:
        info = check_manifest()
        print(json.dumps(info, ensure_ascii=False, indent=2))
    if args.quarantine_report:
        info = build_quarantine_report()
        print(json.dumps(info, ensure_ascii=False, indent=2))
    if args.audit:
        volumes: list[dict[str, Any]] = []
        for v in range(1, 27):
            vs = score_volume(v)
            volumes.append(
                {
                    "volume": vs.volume,
                    "score": vs.score,
                    "total_records": vs.total_records,
                    "counts_by_score": vs.counts_by_score,
                    "issues": vs.issues,
                    "quarantine_recommended": vs.quarantine_recommended,
                }
            )
        payload = {
            "generated_at": __import__("datetime")
            .datetime.now(__import__("datetime").timezone.utc)
            .isoformat(),
            "tool": "tools/canon_quality_check.py",
            "schema_version": "1.0.0",
            "volumes": volumes,
            "manifest": check_manifest(),
            "quarantine": build_quarantine_report(),
        }
        out = pathlib.Path(args.output)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {out}")
        # summary
        low = [v for v in volumes if v["score"] < 50]
        print(f"volumes={len(volumes)} low(<50)={len(low)} {[v['volume'] for v in low]}")
        avg = round(sum(v["score"] for v in volumes) / len(volumes)) if volumes else 0
        print(f"corpus_avg={avg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
