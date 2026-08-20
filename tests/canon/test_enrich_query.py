"""Tests for the enrichment read-only query API."""

from __future__ import annotations

from pathlib import Path

from overlord_worldsim.canon.enrich_query import (
    enrichment_summary,
    get_ability,
    get_analogous_cases,
    get_behavior_cases,
    get_beliefs_at_time,
    get_canon_conflicts,
    get_canon_gaps,
    get_character_behavior_profile,
    get_creatures,
    get_detailed_event,
    get_economic_observations,
    get_enrichment_manifest,
    get_event_dependencies,
    get_event_prerequisites,
    get_item,
    get_item_history,
    get_location_profile,
    get_organization,
    get_power_comparisons,
    get_relationship_changes,
    get_routes,
    get_social_rules,
    get_species,
    get_speech_profile,
    get_travel_observations,
    get_world_rules,
    search_behavior_cases,
)

from .test_enrich_loader import _apply


def test_get_character_behavior_profile(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    profiles = get_character_behavior_profile(db_path, "E0001")
    assert len(profiles) == 1
    profile = profiles[0]
    assert profile["profile_id"] == "CP0001"
    assert profile["personality_traits"] == ["认真", "好学"]
    assert profile["evidence"][0]["evidence_id"] == "EV0001"


def test_get_character_behavior_profile_visibility(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    assert get_character_behavior_profile(db_path, "E0001", at_volume=1)
    assert not get_character_behavior_profile(db_path, "E0001", at_volume=0)


def test_get_behavior_cases_by_character_and_tag(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    cases = get_behavior_cases(db_path, character_id="E0001", tags=("TEACHING",))
    assert len(cases) == 1
    assert cases[0]["tags"] == ["TEACHING", "TRAINING"]
    assert get_behavior_cases(db_path, character_id="E0001", tags=("GRIEF",)) == []


def test_get_analogous_cases(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    cases = get_analogous_cases(
        db_path, tags=("TEACHING", "TRAINING"), situation_type="学习魔术"
    )
    assert len(cases) == 1


def test_search_behavior_cases_fts(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    hits = search_behavior_cases(db_path, "火魔术")
    assert len(hits) == 1
    assert hits[0]["case_id"] == "BC0001"


def test_get_world_rules_by_domain(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    rules = get_world_rules(db_path, domain="MAGIC")
    assert len(rules) == 1
    assert rules[0]["domain"] == "MAGIC"
    assert get_world_rules(db_path, domain="SOCIETY") == []


def test_get_social_rules(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    assert get_social_rules(db_path) == []


def test_get_item_with_instances_and_history(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    item = get_item(db_path, "IT0001")
    assert item is not None
    assert item["canonical_name"] == "火之魔剑"
    assert len(item["instances"]) == 1
    history = item["instances"][0]["ownership_history"]
    assert history[0]["owner_id"] == "E0001"
    flat_history = get_item_history(db_path, item_id="IT0001")
    assert len(flat_history) == 1


def test_get_ability(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    ability = get_ability(db_path, "AB0001")
    assert ability is not None
    assert ability["ability_type"] == "MAGIC"
    assert ability["known_users"] == ["E0001"]


def test_get_power_comparisons(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    comparisons = get_power_comparisons(db_path, actor_id="E0001")
    assert len(comparisons) == 1
    assert comparisons[0]["result"] == "鲁迪乌斯胜"


def test_get_detailed_event_children(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    event = get_detailed_event(db_path, "DE0001")
    assert event is not None
    assert event["title"] == "搬家"
    assert event["participants"] == ["E0001", "E0002"]
    assert event["prerequisites"][0]["statement"].startswith("鲁迪乌斯出生")
    assert event["dependencies"][0]["target_event_id"] == "DE0002"
    assert event["state_changes"][0]["after"] == "布埃纳村"
    prereqs = get_event_prerequisites(db_path, "DE0001")
    assert len(prereqs) == 1
    deps = get_event_dependencies(db_path, "DE0001")
    assert len(deps) == 1


def test_get_location_profile_and_routes(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    location = get_location_profile(db_path, "E0003")
    assert location is not None
    assert location["location_type"] == "VILLAGE"
    routes = get_routes(db_path, from_id="E0003", to_id="E0004")
    assert len(routes) == 1
    observations = get_travel_observations(db_path, route_id="RT0001")
    assert len(observations) == 1


def test_get_organization_with_political_states(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    organization = get_organization(db_path, "E0005")
    assert organization is not None
    assert organization["org_type"] == "公會"
    assert len(organization["political_states"]) == 1


def test_get_beliefs_at_time(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    beliefs = get_beliefs_at_time(db_path, "E0001", at_volume=1)
    assert len(beliefs) == 1
    assert beliefs[0]["belief_state"] == "FACT_KNOWN"
    assert get_beliefs_at_time(db_path, "E0001", at_volume=0) == []


def test_get_relationship_changes(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    changes = get_relationship_changes(db_path, "E0002", "E0001")
    assert len(changes) == 1
    assert changes[0]["dimension"] == "affection"


def test_get_speech_profile(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    profiles = get_speech_profile(db_path, "E0001")
    assert len(profiles) == 1
    assert profiles[0]["address_habits"] == "称呼父母为父亲大人"


def test_get_species_and_creatures(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    species = get_species(db_path)
    assert len(species) == 1
    assert species[0]["name"] == "人族"
    creatures = get_creatures(db_path)
    assert len(creatures) == 1
    assert creatures[0]["abilities"] == ["火焰吐息"]


def test_get_economic_observations(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    observations = get_economic_observations(db_path, location_id="E0003")
    assert len(observations) == 1
    assert observations[0]["price_class"] == "QUALITATIVE"


def test_get_conflicts_and_gaps(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    conflicts = get_canon_conflicts(db_path)
    assert len(conflicts) == 1
    gaps = get_canon_gaps(db_path, domain="GEOGRAPHY")
    assert len(gaps) == 1
    assert gaps[0]["status"] == "NO_CANON_ANSWER"


def test_get_enrichment_manifest_and_summary(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    manifest = get_enrichment_manifest(db_path)
    assert manifest["schema_version"] == "1.0.0"
    summary = enrichment_summary(db_path)
    assert summary["character_profiles"] == 1
    assert summary["evidence"] == 4
    assert summary["detailed_events"] == 2


def test_queries_are_read_only(tmp_path: Path) -> None:
    db_path = _apply(tmp_path)
    before = enrichment_summary(db_path)
    get_character_behavior_profile(db_path, "E0001")
    get_behavior_cases(db_path, character_id="E0001")
    get_world_rules(db_path)
    get_item(db_path, "IT0001")
    get_detailed_event(db_path, "DE0001")
    get_routes(db_path)
    get_creatures(db_path)
    after = enrichment_summary(db_path)
    assert before == after