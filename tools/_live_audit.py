"""Live Canon quality audit — read-only, no mutations."""
from __future__ import annotations

import json
import pathlib
from collections import Counter, defaultdict
from typing import Any

from tools.canon_quality_check import contains_template, score_volume

ROOT = pathlib.Path(".")
ENRICHED = ROOT / "data" / "canon_enriched"
CANON = ROOT / "data" / "canon"

COLLECTIONS = [
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
]

PROFILE_DEEP = [
    "identity",
    "origin",
    "origin_location_id",
    "status_rank",
    "appearance_traits",
    "body_traits",
    "core_personality",
    "surface_personality",
    "hidden_personality",
    "interests",
    "dislikes",
    "weaknesses",
    "obsessions",
    "habits",
    "emotional_triggers",
    "decision_logic",
    "extreme_choice_note",
    "phase_personality_note",
]

PROFILE_CORE = [
    "age_description",
    "personality_traits",
    "values",
    "desires",
    "fears",
    "taboos",
    "insecurities",
    "pride",
    "impulsiveness",
    "patience",
    "risk_tolerance",
    "self_control",
    "attachment_style",
    "authority_attitude",
    "family_attitude",
    "romantic_attitude",
    "violence_attitude",
    "money_attitude",
    "status_attitude",
    "race_attitude",
    "religious_attitude",
    "loyalty",
    "ambition",
    "short_term_goals",
    "long_term_goals",
    "obligations",
    "decision_tendencies",
    "speech_tendencies",
    "social_tendencies",
    "conflict_tendencies",
    "known_skills",
    "knowledge_state",
    "relationship_tendencies",
    "behavior_changes_note",
    "summary",
]

EVENT_FIELDS = [
    "time_date",
    "time_note",
    "location_id",
    "participants",
    "prerequisites",
    "dependencies",
    "state_changes",
    "trigger",
    "actions",
    "outcome",
    "involved_factions",
    "long_term_impacts",
    "political_impacts",
    "world_impacts",
    "participant_actions",
]

ITEM_FIELDS = [
    "canonical_name",
    "description",
    "material",
    "rarity",
    "value_information",
    "creator",
    "origin",
    "manufacturer",
    "abilities",
    "effects",
    "requirements",
    "limitations",
]


def nonempty(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != ""
    if isinstance(v, (list, tuple)):
        return len(v) > 0
    return True


def load_entity_map() -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    for p in sorted(CANON.glob("V*.json")):
        if p.name.endswith(".report.json"):
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        for e in data.get("entities", []):
            eid = e.get("entity_id") or e.get("id")
            if not eid:
                continue
            mapping[eid] = {
                "name": e.get("canonical_name") or e.get("name") or "",
                "kind": e.get("kind") or e.get("entity_kind") or "",
                "aliases": "|".join(e.get("aliases") or []),
            }
    return mapping


def load_batches() -> list[dict[str, Any]]:
    batches = []
    for p in sorted(ENRICHED.glob("V*.json")):
        batches.append(json.loads(p.read_text(encoding="utf-8")))
    return batches


def main() -> None:
    entities = load_entity_map()
    batches = load_batches()

    totals: Counter[str] = Counter()
    per_vol: dict[int, dict[str, int]] = {}
    template_by_vol: Counter[int] = Counter()
    template_by_type: Counter[str] = Counter()

    all_profiles: list[dict[str, Any]] = []
    all_events: list[dict[str, Any]] = []
    all_items: list[dict[str, Any]] = []
    all_rules: list[dict[str, Any]] = []
    all_rels: list[dict[str, Any]] = []
    all_abilities: list[dict[str, Any]] = []
    all_orgs: list[dict[str, Any]] = []
    all_locs: list[dict[str, Any]] = []
    all_cases: list[dict[str, Any]] = []
    all_speech: list[dict[str, Any]] = []
    all_quirks: list[dict[str, Any]] = []
    all_prefs: list[dict[str, Any]] = []
    all_beliefs: list[dict[str, Any]] = []
    all_species: list[dict[str, Any]] = []
    all_econ: list[dict[str, Any]] = []
    all_personas: list[dict[str, Any]] = []

    for b in batches:
        vol = b.get("source_volume")
        counts: dict[str, int] = {}
        for col in COLLECTIONS:
            recs = b.get(col) or []
            counts[col] = len(recs)
            totals[col] += len(recs)
            for rec in recs:
                blob = json.dumps(rec, ensure_ascii=False)
                if contains_template(blob):
                    template_by_vol[vol] += 1
                    template_by_type[col] += 1
        per_vol[vol] = counts
        all_profiles.extend(b.get("character_profiles") or [])
        all_events.extend(b.get("detailed_events") or [])
        all_items.extend(b.get("items") or [])
        all_rules.extend(b.get("world_rules") or [])
        all_rels.extend(b.get("relationship_changes") or [])
        all_abilities.extend(b.get("abilities") or [])
        all_orgs.extend(b.get("organizations") or [])
        all_locs.extend(b.get("locations") or [])
        all_cases.extend(b.get("behavior_cases") or [])
        all_speech.extend(b.get("speech_profiles") or [])
        all_quirks.extend(b.get("character_quirks") or [])
        all_prefs.extend(b.get("character_preferences") or [])
        all_beliefs.extend(b.get("beliefs") or [])
        all_species.extend(b.get("species") or [])
        all_econ.extend(b.get("economic_observations") or [])
        all_personas.extend(b.get("character_personas") or [])

    print("=== TOTALS ===")
    for k in COLLECTIONS:
        print(f"{k}: {totals[k]}")
    print("total_records", sum(totals.values()))

    print("\n=== PER VOLUME RECORD COUNTS ===")
    for vol in sorted(per_vol):
        n = sum(per_vol[vol].values())
        tmpl = template_by_vol[vol]
        print(f"V{vol:03d}: n={n:4d} template_hits={tmpl:3d} events={per_vol[vol]['detailed_events']} profiles={per_vol[vol]['character_profiles']} items={per_vol[vol]['items']} rules={per_vol[vol]['world_rules']} locs={per_vol[vol]['locations']} orgs={per_vol[vol]['organizations']}")

    print("\n=== TEMPLATE BY TYPE ===")
    for k, v in template_by_type.most_common():
        print(f"  {k}: {v}")

    # entity kinds
    kind_c: Counter[str] = Counter()
    for e in entities.values():
        kind_c[e["kind"]] += 1
    print("\n=== EXTRACTION ENTITIES ===")
    print("n_entities", len(entities), dict(kind_c))

    # name search
    name_needles = [
        "鲁迪", "洛琪希", "希露菲", "艾莉丝", "保罗", "莉莉娅", "莉莉雅",
        "诺伦", "爱夏", "基列奴", "扎诺巴", "札诺巴", "克里夫", "奥尔斯帝德",
        "爱丽儿", "人神", "龙神", "拉普拉斯", "塞妮丝", "艾莉娜丽洁",
        "路克", "奇希莉卡", "瑞杰路德", "奥菲莉亚", "佩尔吉乌斯",
        "奥尔斯特德", "奥尔迪斯",
    ]
    print("\n=== ENTITY NAME HITS ===")
    hits: dict[str, list[str]] = defaultdict(list)
    for eid, info in entities.items():
        blob = info["name"] + "|" + info["aliases"]
        for n in name_needles:
            if n in blob:
                hits[n].append(f"{eid}:{info['name']}:{info['kind']}")
    for n in name_needles:
        print(f"  {n}: {hits.get(n, [])[:8]}{'...' if len(hits.get(n, []))>8 else ''} count={len(hits.get(n, []))}")

    # character profile coverage
    char_profiles: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in all_profiles:
        char_profiles[p["character_id"]].append(p)

    print("\n=== TOP PROFILE CHARACTERS ===")
    ranked = sorted(char_profiles.items(), key=lambda kv: -len(kv[1]))
    for cid, plist in ranked[:25]:
        name = entities.get(cid, {}).get("name", "?")
        vols = sorted({int(x["profile_id"][2:4]) if x["profile_id"][2:4].isdigit() else -1 for x in plist})
        tmpl = sum(1 for x in plist if contains_template(json.dumps(x, ensure_ascii=False)))
        print(f"  {cid} {name}: {len(plist)} profiles, template={tmpl}, vols~{vols}")

    target_ids = {
        "鲁迪乌斯": None,
        "洛琪希": None,
        "希露菲": None,
        "艾莉丝": None,
        "保罗": None,
        "莉莉娅": None,
        "诺伦": None,
        "爱夏": None,
        "基列奴": None,
        "扎诺巴": None,
        "克里夫": None,
        "奥尔斯帝德": None,
        "爱丽儿": None,
        "人神": None,
        "塞妮丝": None,
        "瑞杰路德": None,
        "奇希莉卡": None,
        "艾莉娜丽洁": None,
    }
    # resolve by name
    resolved: dict[str, list[str]] = defaultdict(list)
    for eid, info in entities.items():
        blob = info["name"] + info["aliases"]
        for key in target_ids:
            if key in blob or (key == "莉莉娅" and "莉莉雅" in blob) or (key == "扎诺巴" and "札诺巴" in blob):
                resolved[key].append(eid)

    print("\n=== TARGET CHARACTER AUDIT ===")
    for key, ids in resolved.items():
        print(f"\n-- {key} ids={ids}")
        for cid in ids:
            plist = char_profiles.get(cid, [])
            cases = [c for c in all_cases if c.get("character_id") == cid]
            speech = [s for s in all_speech if s.get("character_id") == cid]
            quirks = [q for q in all_quirks if q.get("character_id") == cid]
            prefs = [q for q in all_prefs if q.get("character_id") == cid]
            rels = [r for r in all_rels if r.get("from_id") == cid or r.get("to_id") == cid or r.get("character_a") == cid or r.get("character_b") == cid]
            beliefs = [b for b in all_beliefs if b.get("character_id") == cid]
            abils = [a for a in all_abilities if a.get("character_id") == cid]
            personas = [p for p in all_personas if p.get("character_id") == cid]
            print(f"  {cid} {entities.get(cid, {}).get('name')}: profiles={len(plist)} cases={len(cases)} speech={len(speech)} quirks={len(quirks)} prefs={len(prefs)} rels={len(rels)} beliefs={len(beliefs)} abilities={len(abils)} personas={len(personas)}")
            if plist:
                # field fill
                core_fill = Counter()
                deep_fill = Counter()
                tmpl = 0
                phases = []
                for p in plist:
                    phases.append(p.get("phase_name"))
                    if contains_template(json.dumps(p, ensure_ascii=False)):
                        tmpl += 1
                    for f in PROFILE_CORE:
                        if nonempty(p.get(f)):
                            core_fill[f] += 1
                    for f in PROFILE_DEEP:
                        if nonempty(p.get(f)):
                            deep_fill[f] += 1
                n = len(plist)
                print(f"    template_profiles={tmpl}/{n}")
                print(f"    phases={phases}")
                print(f"    core_fill_pct: " + ", ".join(f"{k}={core_fill[k]*100//n}%" for k in ["age_description","personality_traits","values","desires","fears","known_skills","decision_tendencies","speech_tendencies"]))
                print(f"    deep_fill: " + ", ".join(f"{k}={deep_fill[k]}/{n}" for k in PROFILE_DEEP if deep_fill[k] > 0) or "(all empty)")
                if deep_fill.total() == 0:
                    print("    deep_fill: ALL EMPTY")

    # profile field global fill
    print("\n=== GLOBAL PROFILE FIELD FILL ===")
    n = len(all_profiles)
    for f in PROFILE_DEEP:
        filled = sum(1 for p in all_profiles if nonempty(p.get(f)))
        print(f"  {f}: {filled}/{n} = {filled*100//max(n,1)}%")

    # events
    print("\n=== EVENT FIELD FILL ===")
    n = len(all_events)
    for f in EVENT_FIELDS:
        filled = sum(1 for e in all_events if nonempty(e.get(f)))
        print(f"  {f}: {filled}/{n} = {filled*100//max(n,1)}%")
    event_tmpl = sum(1 for e in all_events if contains_template(json.dumps(e, ensure_ascii=False)))
    print(f"  template_events={event_tmpl}/{n}")
    print("  sample titles:")
    for e in all_events:
        if contains_template(e.get("title", "") + e.get("trigger", "") + e.get("outcome", "")):
            continue
        print("   *", e.get("title"), "vol", e.get("volume_no"), "loc", e.get("location_id"))
    # print a few template titles
    print("  template titles sample:")
    shown = 0
    for e in all_events:
        if contains_template(json.dumps(e, ensure_ascii=False)):
            print("   T", e.get("title"), "vol", e.get("volume_no"))
            shown += 1
            if shown >= 8:
                break

    # items
    print("\n=== ITEMS ===")
    n = len(all_items)
    print("n_items", n)
    for f in ITEM_FIELDS:
        filled = sum(1 for i in all_items if nonempty(i.get(f)))
        print(f"  {f}: {filled}/{n} = {filled*100//max(n,1)}%")
    for i in all_items:
        print(f"  ITEM {i.get('item_id')} {i.get('canonical_name')} rarity={i.get('rarity')} creator={i.get('creator')} origin={i.get('origin')} abilities={i.get('abilities')}")

    # world rules
    print("\n=== WORLD RULES ===")
    n = len(all_rules)
    domains = Counter(r.get("domain") for r in all_rules)
    tmpl = sum(1 for r in all_rules if contains_template(json.dumps(r, ensure_ascii=False)))
    print(f"n={n} template={tmpl} domains={dict(domains)}")
    print("  non-template sample:")
    shown = 0
    for r in all_rules:
        if contains_template(json.dumps(r, ensure_ascii=False)):
            continue
        print("   *", r.get("domain"), r.get("statement", "")[:80])
        shown += 1
        if shown >= 15:
            break

    # locations / orgs / species
    print("\n=== LOCATIONS ===")
    for loc in all_locs:
        print(" ", loc.get("location_id"), loc.get("canonical_name") or loc.get("name"), loc.get("location_type") or loc.get("kind"), "parent", loc.get("parent_id"))
    print("n_locs", len(all_locs), "n_orgs", len(all_orgs), "n_species", len(all_species), "n_econ", len(all_econ), "n_routes", totals["routes"])
    for o in all_orgs:
        print(" ORG", o.get("org_id") or o.get("organization_id"), o.get("canonical_name") or o.get("name"), o.get("org_type"))

    print("\n=== RELATIONSHIP CHANGES ===")
    dims = Counter(r.get("dimension") for r in all_rels)
    tmpl = sum(1 for r in all_rels if contains_template(json.dumps(r, ensure_ascii=False)))
    print(f"n={len(all_rels)} template={tmpl} dims={dict(dims)}")

    print("\n=== ABILITIES ===")
    for a in all_abilities:
        print(" ", a.get("ability_id"), a.get("canonical_name") or a.get("name"), "char", a.get("character_id"), "type", a.get("ability_type"))

    print("\n=== QUALITY GATE PER VOLUME ===")
    for v in range(1, 27):
        vs = score_volume(v)
        print(f"  V{v:03d} score={vs.score} n={vs.total_records} issues={vs.issues} quarantine={vs.quarantine_recommended}")


if __name__ == "__main__":
    main()
