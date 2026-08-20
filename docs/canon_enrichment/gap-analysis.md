# Canon Enrichment Gap Analysis (Phase A audit result)

Audit date: 2026-08-19 · Branch: `feat/canon-enrichment-v1`

## Existing Canon layer (M4/M5, audited, not to be rebuilt)

| Artifact | Status | Location |
| --- | --- | --- |
| Raw novel TXT (26 volumes + tail) | git-ignored, SHA-256 pinned | `data/raw/无职转生TXT合集.txt` |
| Parsed chunks (2731 chunks, 541 units, 526 scenes) | git-ignored, derived | `data/parsed/` |
| Canon SQLite | git-ignored, derived | `data/db/canon.sqlite3` |
| Extraction batches V001–V026 | versioned | `data/canon/V###.json` |
| Entities | 145 (108 CHARACTER, 34 LOCATION, 3 ORGANIZATION) | registry in batches |
| Facts | 226 | `facts` table |
| Relationships | 65 | `relationships` table |
| Knowledge | 106 | `knowledge` table |
| Timeline events | 98 | `timeline_events` table |
| Character phases | 12 | `character_phases` table |
| Query API | 10 read-only interfaces | `canon/query.py` |
| Verifier | structural only (evidence containment, ID uniqueness, FK resolve) | `canon/verifier.py` |
| Loader | per-batch delete-then-insert, one transaction | `canon/loader.py` |
| FTS + embeddings | chunks only | `canon/fts.py`, `canon/embeddings.py` |

Existing predicates are coarse (`年纪`, `职业`, `身份`, `性格`, `擅长`, …) and
`character_phases` has only 12 rows — far below what a counterfactual resolver
needs (phase-specific behavior profiles, behavior cases, event causality,
item ownership, world rules, travel, society, economy, beliefs).

## What the existing layer CANNOT express (enrichment gap)

1. **Phase-specific personality**: no traits/values/fears/goals per phase;
   no behavioral tendencies (impulsiveness, self-control, risk tolerance…).
2. **Behavior cases**: no record of "what did the character actually do when
   situation X happened" — no tags for analogical retrieval.
3. **Event causality**: timeline events have no prerequisites, dependencies,
   state changes, or item/location/relationship implications.
4. **Items**: only entities with kind ITEM exist (none in current registry);
   no item definitions, instances, ownership history, or effects.
5. **Abilities / magic / sword styles**: no structured ability registry;
   no power comparisons ("A defeated B").
6. **World rules**: no structured rules for magic learning, chanting,
   mana, sword schools, social norms, marriage, nobility, adventurer ranks.
7. **Geography**: locations exist as entities with facts only; no routes,
   travel observations, or duration data.
8. **Organizations**: only 3 org entities; no leaders/members/goals/states.
9. **Species / creatures**: none registered.
10. **Beliefs**: knowledge rows only link to facts; no false beliefs,
    rumor/heard/inferred distinctions, or learned-from provenance.
11. **Economy**: no price/wage/lodging observations with evidence.
12. **Speech patterns**: none.
13. **Relationship dynamics**: only static directed relationship rows; no
    dimension-based change records (before/trigger/after).
14. **Conflicts & gaps**: no canon conflict registry, no missing-canon registry.

## Enrichment layer design (additive)

- Authored content: `data/canon_enriched/V###.json` (one batch per volume) +
  `data/canon_enriched/manifest.json` (build output, pinned in git).
- Evidence model: per-batch `evidence` array; records reference evidence by id.
- Collections: character_profiles, behavior_cases, detailed_events, items,
  item_instances, abilities, power_comparisons, world_rules, locations,
  routes, travel_observations, organizations, political_states, species,
  creatures, beliefs, economic_observations, relationship_changes,
  speech_profiles, canon_conflicts, canon_gaps.
- Pipeline: versioned JSON → verifier (against parsed source + entity
  registry + cross-batch references) → deterministic loader (one transaction,
  wipe-and-reload of enrichment tables) → Canon SQLite → read-only query API.
- New modules: `canon/enrich_model.py`, `canon/enrich_registry.py`,
  `canon/enrich_verifier.py`, `canon/enrich_loader.py`, `canon/enrich_query.py`.
- CLI: `canon enrich-verify` and `canon enrich-apply`.
- Gates: pytest ≥95% coverage on canon package, ruff, mypy strict.

## Content priority (per plan §10)

Character behavioral profiles → detailed event ledger → item registry →
ability/power profiles → world rules → locations/travel → society/law →
organizations/politics → economy → species/monsters → knowledge/belief →
behavior cases → ordinary facts.

## Pilot scope (Phase C)

Volumes 1–2 with core characters 鲁迪, 洛琪希, 保罗, 塞妮丝, 莉莉雅, 希露菲
(plus 艾莉丝/基列奴 where the text supports it), then stress-test with the
three acceptance examples before scaling to V003–V026.
