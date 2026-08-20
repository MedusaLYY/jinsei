"""Read-only query API over the canon enrichment layer.

Every function is a pure read: no writes, no time, no RNG. Queries apply the
requester's knowledge projection where the schema supports it (profiles and
beliefs carry visibility windows; behavior cases carry their occurrence
volume). All record payloads include their resolved evidence references so a
runtime resolver can always trace a claim back to the raw source.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from overlord_worldsim.canon.extract_model import canon_date_sort_key
from overlord_worldsim.canon.loader import open_canon_db as _open_canon_db


def open_enrichment_db(path: Path) -> sqlite3.Connection:
    """Open the canon database for enrichment queries."""
    return _open_canon_db(path)


def _json_loads(value: str | None) -> object:
    if value is None:
        return None
    return json.loads(value)


def _evidence_for(
    connection: sqlite3.Connection,
    collection: str,
    record_id: str,
) -> list[dict[str, object]]:
    rows = connection.execute(
        "SELECT e.evidence_id, e.volume_no, e.unit_id, e.chapter_title, "
        "e.source_start_line, e.source_end_line, e.evidence_type, e.confidence, e.note "
        "FROM enrichment_evidence e "
        "JOIN enrichment_evidence_links l ON l.evidence_id = e.evidence_id "
        "WHERE l.collection = ? AND l.record_id = ? "
        "ORDER BY e.volume_no, e.source_start_line",
        (collection, record_id),
    ).fetchall()
    return [dict(row) for row in rows]


def _attach_evidence(
    connection: sqlite3.Connection,
    records: list[dict[str, object]],
    collection: str,
    id_key: str,
) -> list[dict[str, object]]:
    for record in records:
        record["evidence"] = _evidence_for(connection, collection, str(record[id_key]))
    return records


def get_character_behavior_profile(
    db_path: Path,
    character_id: str,
    *,
    at_date: str | None = None,
    at_volume: int | None = None,
) -> list[dict[str, object]]:
    """Phase-specific behavior profiles for a character.

    Filters by the profile visibility window (at_volume) and, when a date is
    given, by the profile's covered date range.
    """
    connection = _open_canon_db(db_path)
    try:
        rows = connection.execute(
            "SELECT * FROM character_profiles WHERE character_id = ? ORDER BY profile_id",
            (character_id,),
        ).fetchall()
        profiles = [_profile_dict(row) for row in rows]
        if at_volume is not None:
            profiles = [
                profile
                for profile in profiles
                if profile["visible_from_volume"] <= at_volume
                and (
                    profile["visible_to_volume"] is None
                    or profile["visible_to_volume"] >= at_volume
                )
            ]
        if at_date is not None:
            key = canon_date_sort_key(at_date)
            profiles = [
                profile
                for profile in profiles
                if (profile["start_date"] is None or canon_date_sort_key(profile["start_date"]) <= key)
                and (profile["end_date"] is None or canon_date_sort_key(profile["end_date"]) >= key)
            ]
        return _attach_evidence(connection, profiles, "character_profiles", "profile_id")
    finally:
        connection.close()


def _profile_dict(row: sqlite3.Row) -> dict[str, object]:
    profile = dict(row)
    profile["values"] = profile.pop("profile_values")
    for column in (
        "personality_traits",
        "values",
        "desires",
        "fears",
        "taboos",
        "insecurities",
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
    ):
        profile[column] = _json_loads(str(profile[column]))
    return profile


def _case_dict(row: sqlite3.Row, connection: sqlite3.Connection) -> dict[str, object]:
    case = dict(row)
    case["tags"] = [
        tag_row["tag"]
        for tag_row in connection.execute(
            "SELECT tag FROM behavior_case_tags WHERE case_id = ? ORDER BY tag",
            (case["case_id"],),
        ).fetchall()
    ]
    return case


def get_behavior_cases(
    db_path: Path,
    *,
    character_id: str | None = None,
    tags: tuple[str, ...] = (),
    situation_type: str | None = None,
    at_volume: int | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Behavior cases, filterable by character, tags, situation, and volume."""
    connection = _open_canon_db(db_path)
    try:
        query = "SELECT * FROM behavior_cases"
        clauses: list[str] = []
        parameters: list[object] = []
        if character_id is not None:
            clauses.append("character_id = ?")
            parameters.append(character_id)
        if situation_type is not None:
            clauses.append("situation_type = ?")
            parameters.append(situation_type)
        if at_volume is not None:
            clauses.append("volume_no <= ?")
            parameters.append(at_volume)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY case_id"
        rows = connection.execute(query, parameters).fetchall()
        cases = [_case_dict(row, connection) for row in rows]
        if tags:
            cases = [
                case
                for case in cases
                if all(tag in case["tags"] for tag in tags)
            ]
        if limit is not None:
            cases = cases[:limit]
        return _attach_evidence(connection, cases, "behavior_cases", "case_id")
    finally:
        connection.close()


def get_analogous_cases(
    db_path: Path,
    *,
    character_id: str | None = None,
    tags: tuple[str, ...] = (),
    situation_type: str | None = None,
    at_volume: int | None = None,
    limit: int = 20,
) -> list[dict[str, object]]:
    """Analogical candidate retrieval for counterfactual resolution."""
    return get_behavior_cases(
        db_path,
        character_id=character_id,
        tags=tags,
        situation_type=situation_type,
        at_volume=at_volume,
        limit=limit,
    )


def search_behavior_cases(
    db_path: Path,
    query_text: str,
    *,
    limit: int = 20,
) -> list[dict[str, object]]:
    """FTS candidate retrieval over behavior-case text (retrieval only, not truth)."""
    connection = _open_canon_db(db_path)
    try:
        rows = connection.execute(
            "SELECT bc.* FROM behavior_cases_fts fts "
            "JOIN behavior_cases bc ON bc.rowid = fts.rowid "
            "WHERE behavior_cases_fts MATCH ? ORDER BY rank LIMIT ?",
            (query_text, limit),
        ).fetchall()
        cases = [_case_dict(row, connection) for row in rows]
        return _attach_evidence(connection, cases, "behavior_cases", "case_id")
    except sqlite3.OperationalError:
        return []
    finally:
        connection.close()


def get_world_rules(
    db_path: Path,
    *,
    domain: str | None = None,
    at_volume: int | None = None,
) -> list[dict[str, object]]:
    """World rules, optionally by domain and visibility window."""
    connection = _open_canon_db(db_path)
    try:
        clauses: list[str] = []
        parameters: list[object] = []
        if domain is not None:
            clauses.append("domain = ?")
            parameters.append(domain)
        if at_volume is not None:
            clauses.append("visible_from_volume <= ?")
            parameters.append(at_volume)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = connection.execute(
            f"SELECT * FROM world_rules{where} ORDER BY rule_id", parameters
        ).fetchall()
        rules = [dict(row) for row in rows]
        return _attach_evidence(connection, rules, "world_rules", "rule_id")
    finally:
        connection.close()


def get_social_rules(db_path: Path, *, at_volume: int | None = None) -> list[dict[str, object]]:
    """Social / legal / marriage / nobility rules for the requester's time."""
    domains = ("SOCIETY", "LAW", "NOBILITY", "MARRIAGE", "FAMILY")
    rules: list[dict[str, object]] = []
    for domain in domains:
        rules.extend(get_world_rules(db_path, domain=domain, at_volume=at_volume))
    return sorted(rules, key=lambda rule: str(rule["rule_id"]))


def get_item(
    db_path: Path,
    item_id: str,
) -> dict[str, object] | None:
    """Item definition with its instances and ownership history."""
    connection = _open_canon_db(db_path)
    try:
        row = connection.execute("SELECT * FROM items WHERE item_id = ?", (item_id,)).fetchone()
        if row is None:
            return None
        item = dict(row)
        for column in (
            "aliases",
            "abilities",
            "effects",
            "requirements",
            "limitations",
        ):
            item[column] = _json_loads(str(item[column]))
        item["evidence"] = _evidence_for(connection, "items", item_id)
        instances: list[dict[str, object]] = []
        for instance_row in connection.execute(
            "SELECT * FROM item_instances WHERE definition_id = ? ORDER BY instance_id",
            (item_id,),
        ).fetchall():
            instance = dict(instance_row)
            instance["ownership_history"] = [
                dict(history_row)
                for history_row in connection.execute(
                    "SELECT * FROM item_ownership_history WHERE instance_id = ? "
                    "ORDER BY period_start",
                    (instance["instance_id"],),
                ).fetchall()
            ]
            instance["evidence"] = _evidence_for(
                connection, "item_instances", instance["instance_id"]
            )
            instances.append(instance)
        item["instances"] = instances
        return item
    finally:
        connection.close()


def get_item_history(
    db_path: Path,
    *,
    item_id: str | None = None,
    instance_id: str | None = None,
) -> list[dict[str, object]]:
    """Ownership timeline for an item definition or a specific instance."""
    connection = _open_canon_db(db_path)
    try:
        rows: list[sqlite3.Row] = []
        if instance_id is not None:
            rows = connection.execute(
                "SELECT * FROM item_ownership_history WHERE instance_id = ? "
                "ORDER BY period_start",
                (instance_id,),
            ).fetchall()
        elif item_id is not None:
            rows = connection.execute(
                "SELECT h.* FROM item_ownership_history h "
                "JOIN item_instances i ON i.instance_id = h.instance_id "
                "WHERE i.definition_id = ? ORDER BY h.period_start",
                (item_id,),
            ).fetchall()
        else:
            raise ValueError("get_item_history requires item_id or instance_id")
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_ability(
    db_path: Path,
    ability_id: str,
) -> dict[str, object] | None:
    connection = _open_canon_db(db_path)
    try:
        row = connection.execute(
            "SELECT * FROM abilities WHERE ability_id = ?", (ability_id,)
        ).fetchone()
        if row is None:
            return None
        ability = dict(row)
        for column in (
            "aliases",
            "requirements",
            "preconditions",
            "effects",
            "limitations",
            "counters",
            "learning_method",
            "known_users",
        ):
            ability[column] = _json_loads(str(ability[column]))
        ability["evidence"] = _evidence_for(connection, "abilities", ability_id)
        return ability
    finally:
        connection.close()


def get_power_comparisons(
    db_path: Path,
    *,
    actor_id: str | None = None,
    target_id: str | None = None,
) -> list[dict[str, object]]:
    connection = _open_canon_db(db_path)
    try:
        clauses: list[str] = []
        parameters: list[object] = []
        if actor_id is not None:
            clauses.append("actor_id = ?")
            parameters.append(actor_id)
        if target_id is not None:
            clauses.append("target_id = ?")
            parameters.append(target_id)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = connection.execute(
            f"SELECT * FROM power_comparisons{where} ORDER BY comparison_id", parameters
        ).fetchall()
        comparisons = [dict(row) for row in rows]
        return _attach_evidence(connection, comparisons, "power_comparisons", "comparison_id")
    finally:
        connection.close()


def _event_dict(
    connection: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    with_children: bool,
) -> dict[str, object]:
    event = dict(row)
    event["participants"] = [
        participant_row["entity_id"]
        for participant_row in connection.execute(
            "SELECT entity_id FROM enrichment_event_participants WHERE event_id = ? ORDER BY entity_id",
            (event["event_id"],),
        ).fetchall()
    ]
    event["actions"] = json.loads(str(row["actions"])) if row["actions"] else []
    event["prerequisites"] = (
        [
            dict(prerequisite_row)
            for prerequisite_row in connection.execute(
                "SELECT * FROM event_prerequisites WHERE event_id = ? "
                "ORDER BY prerequisite_id",
                (event["event_id"],),
            ).fetchall()
        ]
        if with_children
        else []
    )
    event["dependencies"] = (
        [
            dict(dependency_row)
            for dependency_row in connection.execute(
                "SELECT * FROM event_dependencies WHERE event_id = ? ORDER BY dependency_id",
                (event["event_id"],),
            ).fetchall()
        ]
        if with_children
        else []
    )
    event["state_changes"] = (
        [
            dict(change_row)
            for change_row in connection.execute(
                "SELECT * FROM event_state_changes WHERE event_id = ? ORDER BY change_id",
                (event["event_id"],),
            ).fetchall()
        ]
        if with_children
        else []
    )
    if with_children:
        event["evidence"] = _evidence_for(connection, "detailed_events", event["event_id"])
    return event


def get_detailed_event(
    db_path: Path,
    event_id: str,
) -> dict[str, object] | None:
    """A detailed event with participants, prerequisites, dependencies, and changes."""
    connection = _open_canon_db(db_path)
    try:
        row = connection.execute(
            "SELECT * FROM detailed_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        if row is None:
            return None
        return _event_dict(connection, row, with_children=True)
    finally:
        connection.close()


def get_event_prerequisites(
    db_path: Path,
    event_id: str,
) -> list[dict[str, object]]:
    connection = _open_canon_db(db_path)
    try:
        return [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM event_prerequisites WHERE event_id = ? "
                "ORDER BY prerequisite_id",
                (event_id,),
            ).fetchall()
        ]
    finally:
        connection.close()


def get_event_dependencies(
    db_path: Path,
    event_id: str,
) -> list[dict[str, object]]:
    connection = _open_canon_db(db_path)
    try:
        return [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM event_dependencies WHERE event_id = ? ORDER BY dependency_id",
                (event_id,),
            ).fetchall()
        ]
    finally:
        connection.close()


def get_location_profile(
    db_path: Path,
    location_id: str,
) -> dict[str, object] | None:
    connection = _open_canon_db(db_path)
    try:
        row = connection.execute(
            "SELECT * FROM locations WHERE location_id = ?", (location_id,)
        ).fetchone()
        if row is None:
            return None
        location = dict(row)
        for column in (
            "aliases",
            "political_control",
            "known_routes",
            "nearby_locations",
            "organizations",
            "important_people",
        ):
            location[column] = _json_loads(str(location[column]))
        location["evidence"] = _evidence_for(connection, "locations", location_id)
        return location
    finally:
        connection.close()


def get_routes(
    db_path: Path,
    *,
    from_id: str | None = None,
    to_id: str | None = None,
) -> list[dict[str, object]]:
    connection = _open_canon_db(db_path)
    try:
        clauses: list[str] = []
        parameters: list[object] = []
        if from_id is not None:
            clauses.append("(from_location_id = ? OR to_location_id = ?)")
            parameters.extend((from_id, from_id))
        if to_id is not None:
            clauses.append("(from_location_id = ? OR to_location_id = ?)")
            parameters.extend((to_id, to_id))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = connection.execute(
            f"SELECT * FROM routes{where} ORDER BY route_id", parameters
        ).fetchall()
        routes = [dict(row) for row in rows]
        for route in routes:
            route["transport_modes"] = _json_loads(str(route["transport_modes"]))
            route["hazards"] = _json_loads(str(route["hazards"]))
            route["evidence"] = _evidence_for(connection, "routes", route["route_id"])
        return routes
    finally:
        connection.close()


def get_travel_observations(
    db_path: Path,
    *,
    route_id: str | None = None,
) -> list[dict[str, object]]:
    connection = _open_canon_db(db_path)
    try:
        if route_id is not None:
            rows = connection.execute(
                "SELECT * FROM travel_observations WHERE route_id = ? ORDER BY observation_id",
                (route_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM travel_observations ORDER BY observation_id"
            ).fetchall()
        observations = [dict(row) for row in rows]
        for observation in observations:
            observation["characters"] = _json_loads(str(observation["characters"]))
            observation["evidence"] = _evidence_for(
                connection, "travel_observations", observation["observation_id"]
            )
        return observations
    finally:
        connection.close()


def get_economic_observations(
    db_path: Path,
    *,
    location_id: str | None = None,
    at_volume: int | None = None,
    category: str | None = None,
) -> list[dict[str, object]]:
    connection = _open_canon_db(db_path)
    try:
        clauses: list[str] = []
        parameters: list[object] = []
        if location_id is not None:
            clauses.append("location_id = ?")
            parameters.append(location_id)
        if category is not None:
            clauses.append("category = ?")
            parameters.append(category)
        if at_volume is not None:
            clauses.append("at_volume <= ?")
            parameters.append(at_volume)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = connection.execute(
            f"SELECT * FROM economic_observations{where} ORDER BY at_volume, observation_id",
            parameters,
        ).fetchall()
        observations = [dict(row) for row in rows]
        return _attach_evidence(
            connection, observations, "economic_observations", "observation_id"
        )
    finally:
        connection.close()


def get_beliefs_at_time(
    db_path: Path,
    character_id: str,
    *,
    at_volume: int,
) -> list[dict[str, object]]:
    """Beliefs a character holds at a given volume (knowledge projection)."""
    connection = _open_canon_db(db_path)
    try:
        rows = connection.execute(
            "SELECT * FROM beliefs WHERE owner_id = ? ORDER BY belief_id",
            (character_id,),
        ).fetchall()
        beliefs = [dict(row) for row in rows]
        beliefs = [
            belief
            for belief in beliefs
            if belief["visible_from_volume"] <= at_volume
            and (belief["visible_to_volume"] is None or belief["visible_to_volume"] >= at_volume)
        ]
        return _attach_evidence(connection, beliefs, "beliefs", "belief_id")
    finally:
        connection.close()


def get_relationship_changes(
    db_path: Path,
    character_a: str,
    character_b: str,
    *,
    at_volume: int | None = None,
) -> list[dict[str, object]]:
    connection = _open_canon_db(db_path)
    try:
        rows = connection.execute(
            "SELECT * FROM relationship_changes "
            "WHERE (source_id = ? AND target_id = ?) OR (source_id = ? AND target_id = ?) "
            "ORDER BY at_volume, change_id",
            (character_a, character_b, character_b, character_a),
        ).fetchall()
        changes = [dict(row) for row in rows]
        if at_volume is not None:
            changes = [change for change in changes if change["at_volume"] <= at_volume]
        return _attach_evidence(connection, changes, "relationship_changes", "change_id")
    finally:
        connection.close()


def get_speech_profile(
    db_path: Path,
    character_id: str,
    *,
    at_volume: int | None = None,
) -> list[dict[str, object]]:
    connection = _open_canon_db(db_path)
    try:
        rows = connection.execute(
            "SELECT * FROM speech_profiles WHERE character_id = ? ORDER BY profile_id",
            (character_id,),
        ).fetchall()
        profiles = [dict(row) for row in rows]
        if at_volume is not None:
            profiles = [
                profile
                for profile in profiles
                if profile["visible_from_volume"] <= at_volume
            ]
        for profile in profiles:
            profile["canonical_examples"] = _json_loads(str(profile["canonical_examples"]))
            profile["evidence"] = _evidence_for(
                connection, "speech_profiles", profile["profile_id"]
            )
        return profiles
    finally:
        connection.close()


def get_organization(
    db_path: Path,
    organization_id: str,
) -> dict[str, object] | None:
    connection = _open_canon_db(db_path)
    try:
        row = connection.execute(
            "SELECT * FROM organizations WHERE organization_id = ?", (organization_id,)
        ).fetchone()
        if row is None:
            return None
        organization = dict(row)
        for column in ("leaders", "members", "goals", "rules", "alliances", "enemies"):
            organization[column] = _json_loads(str(organization[column]))
        organization["political_states"] = [
            dict(state_row)
            for state_row in connection.execute(
                "SELECT * FROM political_states WHERE organization_id = ? "
                "ORDER BY start_date",
                (organization_id,),
            ).fetchall()
        ]
        for state in organization["political_states"]:
            state["alliances"] = _json_loads(str(state["alliances"]))
            state["conflicts"] = _json_loads(str(state["conflicts"]))
            state["political_goals"] = _json_loads(str(state["political_goals"]))
            state["internal_factions"] = _json_loads(str(state["internal_factions"]))
            state["evidence"] = _evidence_for(connection, "political_states", state["state_id"])
        organization["evidence"] = _evidence_for(
            connection, "organizations", organization_id
        )
        return organization
    finally:
        connection.close()


def get_species(
    db_path: Path,
    species_id: str | None = None,
) -> list[dict[str, object]]:
    connection = _open_canon_db(db_path)
    try:
        if species_id is not None:
            rows = connection.execute(
                "SELECT * FROM species WHERE species_id = ?", (species_id,)
            ).fetchall()
        else:
            rows = connection.execute("SELECT * FROM species ORDER BY species_id").fetchall()
        species = [dict(row) for row in rows]
        for entry in species:
            for column in ("aliases", "abilities", "weaknesses"):
                entry[column] = _json_loads(str(entry[column]))
            entry["evidence"] = _evidence_for(connection, "species", entry["species_id"])
        return species
    finally:
        connection.close()


def get_creatures(
    db_path: Path,
    creature_id: str | None = None,
) -> list[dict[str, object]]:
    connection = _open_canon_db(db_path)
    try:
        if creature_id is not None:
            rows = connection.execute(
                "SELECT * FROM creatures WHERE creature_id = ?", (creature_id,)
            ).fetchall()
        else:
            rows = connection.execute("SELECT * FROM creatures ORDER BY creature_id").fetchall()
        creatures = [dict(row) for row in rows]
        for entry in creatures:
            for column in ("aliases", "abilities", "weaknesses", "uses", "known_encounters"):
                entry[column] = _json_loads(str(entry[column]))
            entry["evidence"] = _evidence_for(connection, "creatures", entry["creature_id"])
        return creatures
    finally:
        connection.close()


def get_canon_conflicts(
    db_path: Path,
) -> list[dict[str, object]]:
    connection = _open_canon_db(db_path)
    try:
        rows = connection.execute(
            "SELECT * FROM canon_conflicts ORDER BY conflict_id"
        ).fetchall()
        conflicts = [dict(row) for row in rows]
        for conflict in conflicts:
            conflict["evidence_a_refs"] = _json_loads(str(conflict["evidence_a_refs"]))
            conflict["evidence_b_refs"] = _json_loads(str(conflict["evidence_b_refs"]))
        return conflicts
    finally:
        connection.close()


def get_canon_gaps(
    db_path: Path,
    *,
    domain: str | None = None,
) -> list[dict[str, object]]:
    connection = _open_canon_db(db_path)
    try:
        if domain is not None:
            rows = connection.execute(
                "SELECT * FROM canon_gaps WHERE domain = ? ORDER BY gap_id", (domain,)
            ).fetchall()
        else:
            rows = connection.execute("SELECT * FROM canon_gaps ORDER BY gap_id").fetchall()
        gaps = [dict(row) for row in rows]
        for gap in gaps:
            gap["searched_volumes"] = _json_loads(str(gap["searched_volumes"]))
        return gaps
    finally:
        connection.close()


def get_enrichment_manifest(
    db_path: Path,
) -> dict[str, str]:
    connection = _open_canon_db(db_path)
    try:
        return {
            row["key"]: row["value"]
            for row in connection.execute(
                "SELECT key, value FROM enrichment_manifest ORDER BY key"
            ).fetchall()
        }
    finally:
        connection.close()


def enrichment_summary(db_path: Path) -> dict[str, int]:
    """Counts per enrichment collection for coverage reporting."""
    counts: dict[str, int] = {}
    connection = _open_canon_db(db_path)
    try:
        for table in (
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
            "canon_conflicts",
            "canon_gaps",
        ):
            counts[table] = int(
                connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            )
        counts["evidence"] = int(
            connection.execute("SELECT COUNT(*) FROM enrichment_evidence").fetchone()[0]
        )
    finally:
        connection.close()
    return counts