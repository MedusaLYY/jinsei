"""Enrichment database schema and deterministic loader.

The enrichment layer is stored in the same canon SQLite file as the
extraction layer, as additive tables (never touching the extraction tables).
The loader wipes only the enrichment tables and rebuilds them from the
versioned JSON corpus in one transaction, so applying is idempotent and the
SQLite file remains a pure derived artifact.

Manifest identity: the save game locks canon by the canonical hash of the
enrichment content (computed over the deterministic JSON serialization), not
by the SQLite file bytes.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from overlord_worldsim.canon.enrich_model import (
    AbilityProfile,
    BehaviorCase,
    Belief,
    CanonConflict,
    CanonGap,
    CharacterProfile,
    CreatureProfile,
    DetailedEvent,
    EconomicObservation,
    EnrichmentBatch,
    ItemDef,
    ItemInstance,
    LocationProfile,
    OrganizationProfile,
    PoliticalState,
    PowerComparison,
    RelationshipChange,
    Route,
    SpeechProfile,
    TravelObservation,
    WorldRule,
)

ENRICH_SCHEMA_VERSION = "1.0.0"

_ENRICHMENT_TABLES = (
    "enrichment_manifest",
    "enrichment_evidence",
    "enrichment_evidence_links",
    "character_profiles",
    "behavior_cases",
    "behavior_case_tags",
    "detailed_events",
    "event_prerequisites",
    "event_dependencies",
    "event_state_changes",
    "enrichment_event_participants",
    "items",
    "item_instances",
    "item_ownership_history",
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
    "canon_conflicts",
    "canon_gaps",
)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS enrichment_manifest (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS enrichment_evidence (
    evidence_id TEXT PRIMARY KEY,
    volume_no INTEGER NOT NULL,
    unit_id TEXT NOT NULL,
    chapter_title TEXT NOT NULL,
    source_start_line INTEGER NOT NULL,
    source_end_line INTEGER NOT NULL,
    evidence_type TEXT NOT NULL,
    confidence TEXT NOT NULL,
    note TEXT NOT NULL,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_enrich_evidence_volume ON enrichment_evidence(volume_no);
CREATE TABLE IF NOT EXISTS enrichment_evidence_links (
    collection TEXT NOT NULL,
    record_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL REFERENCES enrichment_evidence(evidence_id),
    PRIMARY KEY (collection, record_id, evidence_id)
);
CREATE INDEX IF NOT EXISTS idx_evidence_links_evid ON enrichment_evidence_links(evidence_id);

CREATE TABLE IF NOT EXISTS character_profiles (
    profile_id TEXT PRIMARY KEY,
    character_id TEXT NOT NULL,
    phase_id TEXT NOT NULL,
    phase_name TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    date_precision TEXT NOT NULL,
    age_description TEXT NOT NULL,
    personality_traits TEXT NOT NULL,
    profile_values TEXT NOT NULL,
    desires TEXT NOT NULL,
    fears TEXT NOT NULL,
    taboos TEXT NOT NULL,
    insecurities TEXT NOT NULL,
    pride TEXT,
    impulsiveness TEXT,
    patience TEXT,
    risk_tolerance TEXT,
    self_control TEXT,
    attachment_style TEXT,
    authority_attitude TEXT,
    family_attitude TEXT,
    romantic_attitude TEXT,
    violence_attitude TEXT,
    money_attitude TEXT,
    status_attitude TEXT,
    race_attitude TEXT,
    religious_attitude TEXT,
    loyalty TEXT,
    ambition TEXT,
    short_term_goals TEXT NOT NULL,
    long_term_goals TEXT NOT NULL,
    obligations TEXT NOT NULL,
    decision_tendencies TEXT NOT NULL,
    speech_tendencies TEXT NOT NULL,
    social_tendencies TEXT NOT NULL,
    conflict_tendencies TEXT NOT NULL,
    known_skills TEXT NOT NULL,
    knowledge_state TEXT NOT NULL,
    relationship_tendencies TEXT NOT NULL,
    behavior_changes_note TEXT NOT NULL,
    summary TEXT NOT NULL,
    visible_from_volume INTEGER NOT NULL,
    visible_to_volume INTEGER,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_profiles_character ON character_profiles(character_id);
CREATE INDEX IF NOT EXISTS idx_profiles_phase ON character_profiles(phase_id);
CREATE INDEX IF NOT EXISTS idx_profiles_visible
    ON character_profiles(visible_from_volume, visible_to_volume);

CREATE TABLE IF NOT EXISTS behavior_cases (
    case_id TEXT PRIMARY KEY,
    character_id TEXT NOT NULL,
    phase_id TEXT NOT NULL,
    phase_name TEXT NOT NULL,
    volume_no INTEGER NOT NULL,
    situation_type TEXT NOT NULL,
    context TEXT NOT NULL,
    trigger_text TEXT NOT NULL,
    available_information TEXT NOT NULL,
    action TEXT NOT NULL,
    verbal_response TEXT NOT NULL,
    emotional_response TEXT NOT NULL,
    goal_at_time TEXT NOT NULL,
    relationship_context TEXT NOT NULL,
    social_context TEXT NOT NULL,
    immediate_outcome TEXT NOT NULL,
    long_term_outcome TEXT NOT NULL,
    tags TEXT NOT NULL,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cases_character ON behavior_cases(character_id);
CREATE INDEX IF NOT EXISTS idx_cases_volume ON behavior_cases(volume_no);
CREATE INDEX IF NOT EXISTS idx_cases_situation ON behavior_cases(situation_type);
CREATE TABLE IF NOT EXISTS behavior_case_tags (
    case_id TEXT NOT NULL REFERENCES behavior_cases(case_id),
    tag TEXT NOT NULL,
    PRIMARY KEY (case_id, tag)
);
CREATE INDEX IF NOT EXISTS idx_case_tags_tag ON behavior_case_tags(tag);

CREATE TABLE IF NOT EXISTS detailed_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    timeline_event_id TEXT,
    time_date TEXT,
    time_precision TEXT NOT NULL,
    time_note TEXT NOT NULL,
    volume_no INTEGER NOT NULL,
    location_id TEXT,
    participants TEXT NOT NULL,
    trigger_text TEXT NOT NULL,
    actions TEXT NOT NULL,
    outcome TEXT NOT NULL,
    canon_importance TEXT NOT NULL,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_de_volume ON detailed_events(volume_no);
CREATE INDEX IF NOT EXISTS idx_de_location ON detailed_events(location_id);
CREATE INDEX IF NOT EXISTS idx_de_timeline ON detailed_events(timeline_event_id);
CREATE TABLE IF NOT EXISTS event_prerequisites (
    prerequisite_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES detailed_events(event_id),
    prerequisite_type TEXT NOT NULL,
    ref_id TEXT,
    statement TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS event_dependencies (
    dependency_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES detailed_events(event_id),
    dependency_type TEXT NOT NULL,
    target_event_id TEXT NOT NULL,
    statement TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dep_target ON event_dependencies(target_event_id);
CREATE TABLE IF NOT EXISTS event_state_changes (
    change_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES detailed_events(event_id),
    change_kind TEXT NOT NULL,
    subject_id TEXT,
    before TEXT NOT NULL,
    after TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_state_subject ON event_state_changes(subject_id);
CREATE TABLE IF NOT EXISTS enrichment_event_participants (
    event_id TEXT NOT NULL REFERENCES detailed_events(event_id),
    entity_id TEXT NOT NULL,
    PRIMARY KEY (event_id, entity_id)
);
CREATE INDEX IF NOT EXISTS idx_enrichment_event_participant ON enrichment_event_participants(entity_id);

CREATE TABLE IF NOT EXISTS items (
    item_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    aliases TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT NOT NULL,
    description TEXT NOT NULL,
    material TEXT,
    size TEXT,
    weight TEXT,
    durability TEXT,
    rarity TEXT,
    value_information TEXT,
    currency TEXT,
    creator TEXT,
    origin TEXT,
    manufacturer TEXT,
    abilities TEXT NOT NULL,
    effects TEXT NOT NULL,
    requirements TEXT NOT NULL,
    limitations TEXT NOT NULL,
    first_appearance_volume INTEGER NOT NULL,
    first_appearance_line INTEGER NOT NULL,
    visible_from_volume INTEGER NOT NULL,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_items_name ON items(canonical_name);

CREATE TABLE IF NOT EXISTS item_instances (
    instance_id TEXT PRIMARY KEY,
    definition_id TEXT NOT NULL REFERENCES items(item_id),
    owner_id TEXT,
    holder_id TEXT,
    location_id TEXT,
    location_name TEXT,
    condition TEXT,
    durability_if_known TEXT,
    acquired_at TEXT,
    lost_at TEXT,
    acquired_at_volume INTEGER,
    lost_at_volume INTEGER,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_instances_def ON item_instances(definition_id);
CREATE INDEX IF NOT EXISTS idx_instances_owner ON item_instances(owner_id);
CREATE TABLE IF NOT EXISTS item_ownership_history (
    entry_id TEXT PRIMARY KEY,
    instance_id TEXT NOT NULL REFERENCES item_instances(instance_id),
    owner_id TEXT,
    period_start TEXT,
    period_end TEXT,
    acquired_via TEXT NOT NULL,
    lost_via TEXT,
    note TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ownership_instance ON item_ownership_history(instance_id);

CREATE TABLE IF NOT EXISTS abilities (
    ability_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    aliases TEXT NOT NULL,
    ability_type TEXT NOT NULL,
    school TEXT,
    element TEXT,
    tier TEXT,
    requirements TEXT NOT NULL,
    preconditions TEXT NOT NULL,
    mana_cost_if_known TEXT,
    stamina_cost_if_known TEXT,
    range_if_known TEXT,
    duration_if_known TEXT,
    effects TEXT NOT NULL,
    limitations TEXT NOT NULL,
    counters TEXT NOT NULL,
    qualitative_power TEXT NOT NULL,
    learning_method TEXT NOT NULL,
    known_users TEXT NOT NULL,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_abilities_type ON abilities(ability_type);

CREATE TABLE IF NOT EXISTS power_comparisons (
    comparison_id TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    dimension TEXT NOT NULL,
    context TEXT NOT NULL,
    result TEXT NOT NULL,
    confidence TEXT NOT NULL,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_compare_actor ON power_comparisons(actor_id);
CREATE INDEX IF NOT EXISTS idx_compare_target ON power_comparisons(target_id);

CREATE TABLE IF NOT EXISTS world_rules (
    rule_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    statement TEXT NOT NULL,
    scope TEXT NOT NULL,
    exceptions TEXT NOT NULL,
    confidence TEXT NOT NULL,
    visible_from_volume INTEGER NOT NULL,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rules_domain ON world_rules(domain);

CREATE TABLE IF NOT EXISTS locations (
    location_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    aliases TEXT NOT NULL,
    location_type TEXT NOT NULL,
    parent_location_id TEXT,
    political_control TEXT NOT NULL,
    population_info TEXT,
    race_distribution TEXT,
    climate TEXT,
    terrain TEXT,
    danger TEXT,
    economy TEXT,
    services TEXT,
    known_routes TEXT NOT NULL,
    nearby_locations TEXT NOT NULL,
    organizations TEXT NOT NULL,
    important_people TEXT NOT NULL,
    first_appearance_volume INTEGER NOT NULL,
    first_appearance_line INTEGER NOT NULL,
    visible_from_volume INTEGER NOT NULL,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_locations_type ON locations(location_type);

CREATE TABLE IF NOT EXISTS routes (
    route_id TEXT PRIMARY KEY,
    from_location_id TEXT NOT NULL,
    to_location_id TEXT NOT NULL,
    transport_modes TEXT NOT NULL,
    distance_info TEXT,
    typical_duration TEXT,
    difficulty TEXT,
    terrain TEXT,
    border_requirements TEXT,
    cost_observations TEXT,
    hazards TEXT NOT NULL,
    seasonality TEXT,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_routes_from ON routes(from_location_id);
CREATE INDEX IF NOT EXISTS idx_routes_to ON routes(to_location_id);

CREATE TABLE IF NOT EXISTS travel_observations (
    observation_id TEXT PRIMARY KEY,
    route_id TEXT NOT NULL REFERENCES routes(route_id),
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    characters TEXT NOT NULL,
    transport TEXT NOT NULL,
    elapsed_time TEXT NOT NULL,
    stops TEXT,
    conditions TEXT,
    batch_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS organizations (
    organization_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    org_type TEXT NOT NULL,
    leaders TEXT NOT NULL,
    members TEXT NOT NULL,
    hierarchy TEXT,
    goals TEXT NOT NULL,
    rules TEXT NOT NULL,
    resources TEXT,
    territory TEXT,
    alliances TEXT NOT NULL,
    enemies TEXT NOT NULL,
    reputation TEXT,
    visible_from_volume INTEGER NOT NULL,
    batch_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS political_states (
    state_id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    date_precision TEXT NOT NULL,
    ruler TEXT,
    alliances TEXT NOT NULL,
    conflicts TEXT NOT NULL,
    succession TEXT,
    political_goals TEXT NOT NULL,
    internal_factions TEXT NOT NULL,
    visible_from_volume INTEGER NOT NULL,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_political_org ON political_states(organization_id);

CREATE TABLE IF NOT EXISTS species (
    species_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    aliases TEXT NOT NULL,
    lifespan TEXT,
    appearance TEXT,
    physiology TEXT,
    abilities TEXT NOT NULL,
    weaknesses TEXT NOT NULL,
    language TEXT,
    culture TEXT,
    social_structure TEXT,
    distribution TEXT,
    relations_with_others TEXT,
    visible_from_volume INTEGER NOT NULL,
    batch_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS creatures (
    creature_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    aliases TEXT NOT NULL,
    habitat TEXT,
    behavior TEXT,
    danger TEXT,
    abilities TEXT NOT NULL,
    weaknesses TEXT NOT NULL,
    social_behavior TEXT,
    uses TEXT NOT NULL,
    known_encounters TEXT NOT NULL,
    visible_from_volume INTEGER NOT NULL,
    batch_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS beliefs (
    belief_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    statement TEXT NOT NULL,
    certainty TEXT NOT NULL,
    belief_state TEXT NOT NULL,
    learned_from TEXT,
    learned_at_volume INTEGER,
    learned_method TEXT,
    is_true_in_world INTEGER,
    visible_from_volume INTEGER NOT NULL,
    visible_to_volume INTEGER,
    note TEXT NOT NULL,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_beliefs_owner ON beliefs(owner_id);
CREATE INDEX IF NOT EXISTS idx_beliefs_topic ON beliefs(topic);

CREATE TABLE IF NOT EXISTS economic_observations (
    observation_id TEXT PRIMARY KEY,
    location_id TEXT,
    location_name TEXT,
    at_date TEXT,
    at_volume INTEGER NOT NULL,
    category TEXT NOT NULL,
    item_id TEXT,
    goods_description TEXT NOT NULL,
    quantity TEXT,
    currency TEXT,
    amount_description TEXT,
    price_class TEXT NOT NULL,
    context TEXT NOT NULL,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_economy_location ON economic_observations(location_id);
CREATE INDEX IF NOT EXISTS idx_economy_category ON economic_observations(category);

CREATE TABLE IF NOT EXISTS relationship_changes (
    change_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    dimension TEXT NOT NULL,
    before TEXT NOT NULL,
    trigger_text TEXT NOT NULL,
    after TEXT NOT NULL,
    at_volume INTEGER NOT NULL,
    at_date TEXT,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_relchange_source ON relationship_changes(source_id);
CREATE INDEX IF NOT EXISTS idx_relchange_target ON relationship_changes(target_id);

CREATE TABLE IF NOT EXISTS speech_profiles (
    profile_id TEXT PRIMARY KEY,
    character_id TEXT NOT NULL,
    phase_id TEXT NOT NULL,
    phase_name TEXT NOT NULL,
    politeness TEXT NOT NULL,
    sentence_length TEXT NOT NULL,
    address_habits TEXT NOT NULL,
    emotion_expression TEXT NOT NULL,
    anger_expression TEXT NOT NULL,
    shy_expression TEXT NOT NULL,
    intimate_speech TEXT NOT NULL,
    stranger_speech TEXT NOT NULL,
    superior_speech TEXT NOT NULL,
    inferior_speech TEXT NOT NULL,
    canonical_examples TEXT NOT NULL,
    visible_from_volume INTEGER NOT NULL,
    batch_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS canon_conflicts (
    conflict_id TEXT PRIMARY KEY,
    claim_a TEXT NOT NULL,
    claim_b TEXT NOT NULL,
    evidence_a_refs TEXT NOT NULL,
    evidence_b_refs TEXT NOT NULL,
    possible_resolution TEXT NOT NULL,
    status TEXT NOT NULL,
    note TEXT NOT NULL,
    batch_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS canon_gaps (
    gap_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    question TEXT NOT NULL,
    why_needed TEXT NOT NULL,
    searched_volumes TEXT NOT NULL,
    status TEXT NOT NULL,
    possible_sources TEXT NOT NULL,
    note TEXT NOT NULL,
    batch_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_gaps_domain ON canon_gaps(domain);
"""

_FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS behavior_cases_fts USING fts5(
    context, trigger_text, action, verbal_response, immediate_outcome,
    content='behavior_cases', content_rowid='rowid', tokenize='trigram'
);
CREATE TRIGGER IF NOT EXISTS behavior_cases_ai AFTER INSERT ON behavior_cases BEGIN
    INSERT INTO behavior_cases_fts(rowid, context, trigger_text, action, verbal_response,
                                   immediate_outcome)
    VALUES (new.rowid, new.context, new.trigger_text, new.action, new.verbal_response,
            new.immediate_outcome);
END;
"""


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_content_hash(batches: Iterable[EnrichmentBatch]) -> str:
    """Deterministic SHA-256 of the whole enrichment corpus (manifest identity)."""
    digest = hashlib.sha256()
    for batch in sorted(batches, key=lambda item: (item.source_volume, item.batch_id)):
        digest.update(_json_bytes(batch.to_json()))
        digest.update(b"\n")
    return digest.hexdigest()


def _link_evidence(
    connection: sqlite3.Connection,
    collection: str,
    record_id: str,
    evidence_ids: tuple[str, ...],
) -> None:
    connection.executemany(
        "INSERT INTO enrichment_evidence_links(collection, record_id, evidence_id) "
        "VALUES (?, ?, ?)",
        [(collection, record_id, evidence_id) for evidence_id in evidence_ids],
    )


def _insert_profiles(
    connection: sqlite3.Connection,
    profiles: Iterable[CharacterProfile],
    batch_id: str,
) -> None:
    for profile in profiles:
        connection.execute(
            "INSERT INTO character_profiles(profile_id, character_id, phase_id, phase_name, "
            "start_date, end_date, date_precision, age_description, personality_traits, "
            "profile_values, desires, fears, taboos, insecurities, pride, impulsiveness, patience, "
            "risk_tolerance, self_control, attachment_style, authority_attitude, "
            "family_attitude, romantic_attitude, violence_attitude, money_attitude, "
            "status_attitude, race_attitude, religious_attitude, loyalty, ambition, "
            "short_term_goals, long_term_goals, obligations, decision_tendencies, "
            "speech_tendencies, social_tendencies, conflict_tendencies, known_skills, "
            "knowledge_state, relationship_tendencies, behavior_changes_note, summary, "
            "visible_from_volume, visible_to_volume, batch_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                profile.profile_id,
                profile.character_id,
                profile.phase_id,
                profile.phase_name,
                profile.start_date,
                profile.end_date,
                profile.date_precision.value,
                profile.age_description,
                json.dumps(list(profile.personality_traits), ensure_ascii=False),
                json.dumps(list(profile.values), ensure_ascii=False),
                json.dumps(list(profile.desires), ensure_ascii=False),
                json.dumps(list(profile.fears), ensure_ascii=False),
                json.dumps(list(profile.taboos), ensure_ascii=False),
                json.dumps(list(profile.insecurities), ensure_ascii=False),
                profile.pride,
                profile.impulsiveness,
                profile.patience,
                profile.risk_tolerance,
                profile.self_control,
                profile.attachment_style,
                profile.authority_attitude,
                profile.family_attitude,
                profile.romantic_attitude,
                profile.violence_attitude,
                profile.money_attitude,
                profile.status_attitude,
                profile.race_attitude,
                profile.religious_attitude,
                profile.loyalty,
                profile.ambition,
                json.dumps(list(profile.short_term_goals), ensure_ascii=False),
                json.dumps(list(profile.long_term_goals), ensure_ascii=False),
                json.dumps(list(profile.obligations), ensure_ascii=False),
                json.dumps(list(profile.decision_tendencies), ensure_ascii=False),
                json.dumps(list(profile.speech_tendencies), ensure_ascii=False),
                json.dumps(list(profile.social_tendencies), ensure_ascii=False),
                json.dumps(list(profile.conflict_tendencies), ensure_ascii=False),
                json.dumps(list(profile.known_skills), ensure_ascii=False),
                json.dumps(list(profile.knowledge_state), ensure_ascii=False),
                json.dumps(list(profile.relationship_tendencies), ensure_ascii=False),
                profile.behavior_changes_note,
                profile.summary,
                profile.visible_from_volume,
                profile.visible_to_volume,
                batch_id,
            ),
        )
        _link_evidence(
            connection, "character_profiles", profile.profile_id, profile.evidence_refs
        )


def _insert_cases(
    connection: sqlite3.Connection,
    cases: Iterable[BehaviorCase],
    batch_id: str,
) -> None:
    for case in cases:
        tags = [tag.value for tag in case.tags]
        connection.execute(
            "INSERT INTO behavior_cases(case_id, character_id, phase_id, phase_name, volume_no, "
            "situation_type, context, trigger_text, available_information, action, verbal_response, "
            "emotional_response, goal_at_time, relationship_context, social_context, "
            "immediate_outcome, long_term_outcome, tags, batch_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                case.case_id,
                case.character_id,
                case.phase_id,
                case.phase_name,
                case.volume_no,
                case.situation_type,
                case.context,
                case.trigger,
                case.available_information,
                case.action,
                case.verbal_response,
                case.emotional_response,
                case.goal_at_time,
                case.relationship_context,
                case.social_context,
                case.immediate_outcome,
                case.long_term_outcome,
                json.dumps(tags, ensure_ascii=False),
                batch_id,
            ),
        )
        connection.executemany(
            "INSERT INTO behavior_case_tags(case_id, tag) VALUES (?, ?)",
            [(case.case_id, tag) for tag in tags],
        )
        _link_evidence(connection, "behavior_cases", case.case_id, case.evidence_refs)


def _insert_events(
    connection: sqlite3.Connection,
    events: Iterable[DetailedEvent],
    batch_id: str,
) -> None:
    for event in events:
        connection.execute(
            "INSERT INTO detailed_events(event_id, event_type, title, timeline_event_id, "
            "time_date, time_precision, time_note, volume_no, location_id, participants, "
            "trigger_text, actions, outcome, canon_importance, batch_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                event.event_id,
                event.event_type,
                event.title,
                event.timeline_event_id,
                event.time_date,
                event.time_precision.value,
                event.time_note,
                event.volume_no,
                event.location_id,
                json.dumps(list(event.participants), ensure_ascii=False),
                event.trigger,
                json.dumps(list(event.actions), ensure_ascii=False),
                event.outcome,
                event.canon_importance.value,
                batch_id,
            ),
        )
        connection.executemany(
            "INSERT INTO enrichment_event_participants(event_id, entity_id) VALUES (?, ?)",
            [(event.event_id, participant) for participant in event.participants],
        )
        connection.executemany(
            "INSERT INTO event_prerequisites(prerequisite_id, event_id, prerequisite_type, "
            "ref_id, statement) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    prerequisite.prerequisite_id,
                    event.event_id,
                    prerequisite.prerequisite_type.value,
                    prerequisite.ref_id,
                    prerequisite.statement,
                )
                for prerequisite in event.prerequisites
            ],
        )
        connection.executemany(
            "INSERT INTO event_dependencies(dependency_id, event_id, dependency_type, "
            "target_event_id, statement) VALUES (?, ?, ?, ?, ?)",
            [
                (
                    dependency.dependency_id,
                    event.event_id,
                    dependency.dependency_type.value,
                    dependency.target_event_id,
                    dependency.statement,
                )
                for dependency in event.dependencies
            ],
        )
        connection.executemany(
            "INSERT INTO event_state_changes(change_id, event_id, change_kind, subject_id, "
            "before, after) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    change.change_id,
                    event.event_id,
                    change.change_kind,
                    change.subject_id,
                    change.before,
                    change.after,
                )
                for change in event.state_changes
            ],
        )
        _link_evidence(connection, "detailed_events", event.event_id, event.evidence_refs)


def _insert_items(connection: sqlite3.Connection, items: Iterable[ItemDef], batch_id: str) -> None:
    for item in items:
        connection.execute(
            "INSERT INTO items(item_id, canonical_name, aliases, category, subcategory, "
            "description, material, size, weight, durability, rarity, value_information, "
            "currency, creator, origin, manufacturer, abilities, effects, requirements, "
            "limitations, first_appearance_volume, first_appearance_line, "
            "visible_from_volume, batch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item.item_id,
                item.canonical_name,
                json.dumps(list(item.aliases), ensure_ascii=False),
                item.category,
                item.subcategory,
                item.description,
                item.material,
                item.size,
                item.weight,
                item.durability,
                item.rarity,
                item.value_information,
                item.currency,
                item.creator,
                item.origin,
                item.manufacturer,
                json.dumps(list(item.abilities), ensure_ascii=False),
                json.dumps(list(item.effects), ensure_ascii=False),
                json.dumps(list(item.requirements), ensure_ascii=False),
                json.dumps(list(item.limitations), ensure_ascii=False),
                item.first_appearance_volume,
                item.first_appearance_line,
                item.visible_from_volume,
                batch_id,
            ),
        )
        _link_evidence(connection, "items", item.item_id, item.evidence_refs)


def _insert_instances(
    connection: sqlite3.Connection,
    instances: Iterable[ItemInstance],
    batch_id: str,
) -> None:
    for instance in instances:
        connection.execute(
            "INSERT INTO item_instances(instance_id, definition_id, owner_id, holder_id, "
            "location_id, location_name, condition, durability_if_known, acquired_at, "
            "lost_at, acquired_at_volume, lost_at_volume, batch_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                instance.instance_id,
                instance.definition_id,
                instance.owner_id,
                instance.holder_id,
                instance.location_id,
                instance.location_name,
                instance.condition,
                instance.durability_if_known,
                instance.acquired_at,
                instance.lost_at,
                instance.acquired_at_volume,
                instance.lost_at_volume,
                batch_id,
            ),
        )
        connection.executemany(
            "INSERT INTO item_ownership_history(entry_id, instance_id, owner_id, period_start, "
            "period_end, acquired_via, lost_via, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    entry.entry_id,
                    instance.instance_id,
                    entry.owner_id,
                    entry.period_start,
                    entry.period_end,
                    entry.acquired_via,
                    entry.lost_via,
                    entry.note,
                )
                for entry in instance.ownership_history
            ],
        )
        _link_evidence(connection, "item_instances", instance.instance_id, instance.evidence_refs)


def _insert_abilities(
    connection: sqlite3.Connection,
    abilities: Iterable[AbilityProfile],
    batch_id: str,
) -> None:
    for ability in abilities:
        connection.execute(
            "INSERT INTO abilities(ability_id, name, aliases, ability_type, school, element, "
            "tier, requirements, preconditions, mana_cost_if_known, stamina_cost_if_known, "
            "range_if_known, duration_if_known, effects, limitations, counters, "
            "qualitative_power, learning_method, known_users, batch_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ability.ability_id,
                ability.name,
                json.dumps(list(ability.aliases), ensure_ascii=False),
                ability.ability_type.value,
                ability.school,
                ability.element,
                ability.tier,
                json.dumps(list(ability.requirements), ensure_ascii=False),
                json.dumps(list(ability.preconditions), ensure_ascii=False),
                ability.mana_cost_if_known,
                ability.stamina_cost_if_known,
                ability.range_if_known,
                ability.duration_if_known,
                json.dumps(list(ability.effects), ensure_ascii=False),
                json.dumps(list(ability.limitations), ensure_ascii=False),
                json.dumps(list(ability.counters), ensure_ascii=False),
                ability.qualitative_power,
                json.dumps(list(ability.learning_method), ensure_ascii=False),
                json.dumps(list(ability.known_users), ensure_ascii=False),
                batch_id,
            ),
        )
        _link_evidence(connection, "abilities", ability.ability_id, ability.evidence_refs)


def _insert_comparisons(
    connection: sqlite3.Connection,
    comparisons: Iterable[PowerComparison],
    batch_id: str,
) -> None:
    for comparison in comparisons:
        connection.execute(
            "INSERT INTO power_comparisons(comparison_id, actor_id, target_id, dimension, "
            "context, result, confidence, batch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                comparison.comparison_id,
                comparison.actor_id,
                comparison.target_id,
                comparison.dimension,
                comparison.context,
                comparison.result,
                comparison.confidence.value,
                batch_id,
            ),
        )
        _link_evidence(
            connection, "power_comparisons", comparison.comparison_id, comparison.evidence_refs
        )


def _insert_rules(
    connection: sqlite3.Connection,
    rules: Iterable[WorldRule],
    batch_id: str,
) -> None:
    for rule in rules:
        connection.execute(
            "INSERT INTO world_rules(rule_id, domain, statement, scope, exceptions, "
            "confidence, visible_from_volume, batch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                rule.rule_id,
                rule.domain.value,
                rule.statement,
                rule.scope,
                rule.exceptions,
                rule.confidence.value,
                rule.visible_from_volume,
                batch_id,
            ),
        )
        _link_evidence(connection, "world_rules", rule.rule_id, rule.evidence_refs)


def _insert_locations(
    connection: sqlite3.Connection,
    locations: Iterable[LocationProfile],
    batch_id: str,
) -> None:
    for location in locations:
        connection.execute(
            "INSERT INTO locations(location_id, name, aliases, location_type, "
            "parent_location_id, political_control, population_info, race_distribution, "
            "climate, terrain, danger, economy, services, known_routes, nearby_locations, "
            "organizations, important_people, first_appearance_volume, "
            "first_appearance_line, visible_from_volume, batch_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                location.location_id,
                location.name,
                json.dumps(list(location.aliases), ensure_ascii=False),
                location.location_type.value,
                location.parent_location_id,
                json.dumps(list(location.political_control), ensure_ascii=False),
                location.population_info,
                location.race_distribution,
                location.climate,
                location.terrain,
                location.danger,
                location.economy,
                location.services,
                json.dumps(list(location.known_routes), ensure_ascii=False),
                json.dumps(list(location.nearby_locations), ensure_ascii=False),
                json.dumps(list(location.organizations), ensure_ascii=False),
                json.dumps(list(location.important_people), ensure_ascii=False),
                location.first_appearance_volume,
                location.first_appearance_line,
                location.visible_from_volume,
                batch_id,
            ),
        )
        _link_evidence(connection, "locations", location.location_id, location.evidence_refs)


def _insert_routes(
    connection: sqlite3.Connection,
    routes: Iterable[Route],
    batch_id: str,
) -> None:
    for route in routes:
        connection.execute(
            "INSERT INTO routes(route_id, from_location_id, to_location_id, transport_modes, "
            "distance_info, typical_duration, difficulty, terrain, border_requirements, "
            "cost_observations, hazards, seasonality, batch_id) VALUES (?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?)",
            (
                route.route_id,
                route.from_location_id,
                route.to_location_id,
                json.dumps(list(route.transport_modes), ensure_ascii=False),
                route.distance_info,
                route.typical_duration,
                route.difficulty,
                route.terrain,
                route.border_requirements,
                route.cost_observations,
                json.dumps(list(route.hazards), ensure_ascii=False),
                route.seasonality,
                batch_id,
            ),
        )
        _link_evidence(connection, "routes", route.route_id, route.evidence_refs)


def _insert_travel(
    connection: sqlite3.Connection,
    observations: Iterable[TravelObservation],
    batch_id: str,
) -> None:
    for observation in observations:
        connection.execute(
            "INSERT INTO travel_observations(observation_id, route_id, origin, destination, "
            "characters, transport, elapsed_time, stops, conditions, batch_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                observation.observation_id,
                observation.route_id,
                observation.origin,
                observation.destination,
                json.dumps(list(observation.characters), ensure_ascii=False),
                observation.transport,
                observation.elapsed_time,
                observation.stops,
                observation.conditions,
                batch_id,
            ),
        )
        _link_evidence(
            connection, "travel_observations", observation.observation_id, observation.evidence_refs
        )


def _insert_organizations(
    connection: sqlite3.Connection,
    organizations: Iterable[OrganizationProfile],
    batch_id: str,
) -> None:
    for organization in organizations:
        connection.execute(
            "INSERT INTO organizations(organization_id, name, org_type, leaders, members, "
            "hierarchy, goals, rules, resources, territory, alliances, enemies, reputation, "
            "visible_from_volume, batch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                organization.organization_id,
                organization.name,
                organization.org_type,
                json.dumps(list(organization.leaders), ensure_ascii=False),
                json.dumps(list(organization.members), ensure_ascii=False),
                organization.hierarchy,
                json.dumps(list(organization.goals), ensure_ascii=False),
                json.dumps(list(organization.rules), ensure_ascii=False),
                organization.resources,
                organization.territory,
                json.dumps(list(organization.alliances), ensure_ascii=False),
                json.dumps(list(organization.enemies), ensure_ascii=False),
                organization.reputation,
                organization.visible_from_volume,
                batch_id,
            ),
        )
        _link_evidence(
            connection, "organizations", organization.organization_id, organization.evidence_refs
        )


def _insert_political(
    connection: sqlite3.Connection,
    states: Iterable[PoliticalState],
    batch_id: str,
) -> None:
    for state in states:
        connection.execute(
            "INSERT INTO political_states(state_id, organization_id, start_date, end_date, "
            "date_precision, ruler, alliances, conflicts, succession, political_goals, "
            "internal_factions, visible_from_volume, batch_id) VALUES (?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?)",
            (
                state.state_id,
                state.organization_id,
                state.start_date,
                state.end_date,
                state.date_precision.value,
                state.ruler,
                json.dumps(list(state.alliances), ensure_ascii=False),
                json.dumps(list(state.conflicts), ensure_ascii=False),
                state.succession,
                json.dumps(list(state.political_goals), ensure_ascii=False),
                json.dumps(list(state.internal_factions), ensure_ascii=False),
                state.visible_from_volume,
                batch_id,
            ),
        )
        _link_evidence(connection, "political_states", state.state_id, state.evidence_refs)


def _insert_species(
    connection: sqlite3.Connection,
    species: Iterable[object],
    batch_id: str,
) -> None:
    for entry in species:
        connection.execute(
            "INSERT INTO species(species_id, name, aliases, lifespan, appearance, physiology, "
            "abilities, weaknesses, language, culture, social_structure, distribution, "
            "relations_with_others, visible_from_volume, batch_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entry.species_id,
                entry.name,
                json.dumps(list(entry.aliases), ensure_ascii=False),
                entry.lifespan,
                entry.appearance,
                entry.physiology,
                json.dumps(list(entry.abilities), ensure_ascii=False),
                json.dumps(list(entry.weaknesses), ensure_ascii=False),
                entry.language,
                entry.culture,
                entry.social_structure,
                entry.distribution,
                entry.relations_with_others,
                entry.visible_from_volume,
                batch_id,
            ),
        )
        _link_evidence(connection, "species", entry.species_id, entry.evidence_refs)


def _insert_creatures(
    connection: sqlite3.Connection,
    creatures: Iterable[CreatureProfile],
    batch_id: str,
) -> None:
    for creature in creatures:
        connection.execute(
            "INSERT INTO creatures(creature_id, name, aliases, habitat, behavior, danger, "
            "abilities, weaknesses, social_behavior, uses, known_encounters, "
            "visible_from_volume, batch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                creature.creature_id,
                creature.name,
                json.dumps(list(creature.aliases), ensure_ascii=False),
                creature.habitat,
                creature.behavior,
                creature.danger,
                json.dumps(list(creature.abilities), ensure_ascii=False),
                json.dumps(list(creature.weaknesses), ensure_ascii=False),
                creature.social_behavior,
                json.dumps(list(creature.uses), ensure_ascii=False),
                json.dumps(list(creature.known_encounters), ensure_ascii=False),
                creature.visible_from_volume,
                batch_id,
            ),
        )
        _link_evidence(connection, "creatures", creature.creature_id, creature.evidence_refs)


def _insert_beliefs(
    connection: sqlite3.Connection,
    beliefs: Iterable[Belief],
    batch_id: str,
) -> None:
    for belief in beliefs:
        connection.execute(
            "INSERT INTO beliefs(belief_id, owner_id, topic, statement, certainty, "
            "belief_state, learned_from, learned_at_volume, learned_method, is_true_in_world, "
            "visible_from_volume, visible_to_volume, note, batch_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                belief.belief_id,
                belief.owner_id,
                belief.topic,
                belief.statement,
                belief.certainty.value,
                belief.belief_state.value,
                belief.learned_from,
                belief.learned_at_volume,
                belief.learned_method,
                None if belief.is_true_in_world is None else int(belief.is_true_in_world),
                belief.visible_from_volume,
                belief.visible_to_volume,
                belief.note,
                batch_id,
            ),
        )
        _link_evidence(connection, "beliefs", belief.belief_id, belief.evidence_refs)


def _insert_economy(
    connection: sqlite3.Connection,
    observations: Iterable[EconomicObservation],
    batch_id: str,
) -> None:
    for observation in observations:
        connection.execute(
            "INSERT INTO economic_observations(observation_id, location_id, location_name, "
            "at_date, at_volume, category, item_id, goods_description, quantity, currency, "
            "amount_description, price_class, context, batch_id) VALUES (?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?)",
            (
                observation.observation_id,
                observation.location_id,
                observation.location_name,
                observation.at_date,
                observation.at_volume,
                observation.category,
                observation.item_id,
                observation.goods_description,
                observation.quantity,
                observation.currency,
                observation.amount_description,
                observation.price_class.value,
                observation.context,
                batch_id,
            ),
        )
        _link_evidence(
            connection, "economic_observations", observation.observation_id, observation.evidence_refs
        )


def _insert_relationship_changes(
    connection: sqlite3.Connection,
    changes: Iterable[RelationshipChange],
    batch_id: str,
) -> None:
    for change in changes:
        connection.execute(
            "INSERT INTO relationship_changes(change_id, source_id, target_id, dimension, "
            "before, trigger_text, after, at_volume, at_date, batch_id) VALUES (?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?)",
            (
                change.change_id,
                change.source_id,
                change.target_id,
                change.dimension,
                change.before,
                change.trigger,
                change.after,
                change.at_volume,
                change.at_date,
                batch_id,
            ),
        )
        _link_evidence(connection, "relationship_changes", change.change_id, change.evidence_refs)


def _insert_speech(connection: sqlite3.Connection, profiles: Iterable[SpeechProfile], batch_id: str) -> None:
    for profile in profiles:
        connection.execute(
            "INSERT INTO speech_profiles(profile_id, character_id, phase_id, phase_name, "
            "politeness, sentence_length, address_habits, emotion_expression, "
            "anger_expression, shy_expression, intimate_speech, stranger_speech, "
            "superior_speech, inferior_speech, canonical_examples, visible_from_volume, "
            "batch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                profile.profile_id,
                profile.character_id,
                profile.phase_id,
                profile.phase_name,
                profile.politeness,
                profile.sentence_length,
                profile.address_habits,
                profile.emotion_expression,
                profile.anger_expression,
                profile.shy_expression,
                profile.intimate_speech,
                profile.stranger_speech,
                profile.superior_speech,
                profile.inferior_speech,
                json.dumps(list(profile.canonical_examples), ensure_ascii=False),
                profile.visible_from_volume,
                batch_id,
            ),
        )
        _link_evidence(connection, "speech_profiles", profile.profile_id, profile.evidence_refs)


def _insert_conflicts(
    connection: sqlite3.Connection,
    conflicts: Iterable[CanonConflict],
    batch_id: str,
) -> None:
    for conflict in conflicts:
        connection.execute(
            "INSERT INTO canon_conflicts(conflict_id, claim_a, claim_b, evidence_a_refs, "
            "evidence_b_refs, possible_resolution, status, note, batch_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                conflict.conflict_id,
                conflict.claim_a,
                conflict.claim_b,
                json.dumps(list(conflict.evidence_a_refs), ensure_ascii=False),
                json.dumps(list(conflict.evidence_b_refs), ensure_ascii=False),
                conflict.possible_resolution,
                conflict.status.value,
                conflict.note,
                batch_id,
            ),
        )


def _insert_gaps(connection: sqlite3.Connection, gaps: Iterable[CanonGap], batch_id: str) -> None:
    for gap in gaps:
        connection.execute(
            "INSERT INTO canon_gaps(gap_id, domain, question, why_needed, searched_volumes, "
            "status, possible_sources, note, batch_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                gap.gap_id,
                gap.domain,
                gap.question,
                gap.why_needed,
                json.dumps(list(gap.searched_volumes), ensure_ascii=False),
                gap.status.value,
                gap.possible_sources,
                gap.note,
                batch_id,
            ),
        )


def _wipe_enrichment(connection: sqlite3.Connection) -> None:
    connection.execute("DROP TABLE IF EXISTS behavior_cases_fts")
    connection.execute("DROP TRIGGER IF EXISTS behavior_cases_ai")
    for table in reversed(_ENRICHMENT_TABLES):
        connection.execute(f"DELETE FROM {table}")


def apply_enrichment(
    connection: sqlite3.Connection,
    batches: Iterable[EnrichmentBatch],
    manifest: dict[str, str],
) -> None:
    """Apply the enrichment corpus in one transaction (idempotent rebuild)."""
    ordered = sorted(batches, key=lambda batch: (batch.source_volume, batch.batch_id))
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(_SCHEMA_SQL)
    _wipe_enrichment(connection)
    connection.executescript(_FTS_SQL)
    for batch in ordered:
        batch_id = batch.batch_id
        connection.executemany(
            "INSERT INTO enrichment_evidence(evidence_id, volume_no, unit_id, chapter_title, "
            "source_start_line, source_end_line, evidence_type, confidence, note, batch_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    evidence.evidence_id,
                    evidence.volume_no,
                    evidence.unit_id,
                    evidence.chapter_title,
                    evidence.source_start_line,
                    evidence.source_end_line,
                    evidence.evidence_type.value,
                    evidence.confidence.value,
                    evidence.note,
                    batch_id,
                )
                for evidence in batch.evidence
            ],
        )
        _insert_profiles(connection, batch.character_profiles, batch_id)
        _insert_cases(connection, batch.behavior_cases, batch_id)
        _insert_events(connection, batch.detailed_events, batch_id)
        _insert_items(connection, batch.items, batch_id)
        _insert_instances(connection, batch.item_instances, batch_id)
        _insert_abilities(connection, batch.abilities, batch_id)
        _insert_comparisons(connection, batch.power_comparisons, batch_id)
        _insert_rules(connection, batch.world_rules, batch_id)
        _insert_locations(connection, batch.locations, batch_id)
        _insert_routes(connection, batch.routes, batch_id)
        _insert_travel(connection, batch.travel_observations, batch_id)
        _insert_organizations(connection, batch.organizations, batch_id)
        _insert_political(connection, batch.political_states, batch_id)
        _insert_species(connection, batch.species, batch_id)
        _insert_creatures(connection, batch.creatures, batch_id)
        _insert_beliefs(connection, batch.beliefs, batch_id)
        _insert_economy(connection, batch.economic_observations, batch_id)
        _insert_relationship_changes(connection, batch.relationship_changes, batch_id)
        _insert_speech(connection, batch.speech_profiles, batch_id)
        _insert_conflicts(connection, batch.canon_conflicts, batch_id)
        _insert_gaps(connection, batch.canon_gaps, batch_id)
    connection.executemany(
        "INSERT INTO enrichment_manifest(key, value) VALUES (?, ?)",
        sorted(manifest.items()),
    )
    connection.commit()


def build_manifest(
    *,
    content_sha256: str,
    source_sha256: str,
    source_volumes: list[int],
    source_unit_count: int,
    build_tool_version: str,
    batch_counts: dict[str, int],
    generated_at: str,
) -> dict[str, str]:
    """Build the enrichment manifest key/value map."""
    return {
        "schema_version": ENRICH_SCHEMA_VERSION,
        "content_version": "1",
        "source_scope": "V001-V026 mainline",
        "source_volumes": json.dumps(source_volumes, separators=(",", ":")),
        "source_sha256": source_sha256,
        "entity_registry_version": "1",
        "build_tool_version": build_tool_version,
        "generated_at": generated_at,
        "content_sha256": content_sha256,
        "batch_counts": json.dumps(
            {key: batch_counts[key] for key in sorted(batch_counts)}, separators=(",", ":")
        ),
    }


def write_manifest_json(manifest: dict[str, str], manifest_path: Path) -> None:
    """Write the manifest deterministically (sorted keys)."""
    payload = json.loads(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def manifest_bytes(manifest: dict[str, str]) -> bytes:
    """Deterministic byte serialization of a manifest (for identity checks)."""
    return _json_bytes(manifest)