"""Deterministic verification of the enrichment corpus.

The enrichment verifier enforces structural, referential, and temporal
invariants over the whole corpus (all batches loaded together), grounding
every check in the parsed source document and the extraction entity registry:

- evidence entries must point inside the parsed volume units they claim
- every referenced entity / item / event / route must resolve
- ids must be unique per collection, aliases must not collide
- dates must be parseable and ordered; visibility windows must be coherent
- behavior-case tags must be part of the stable vocabulary

It never invents content: semantic correctness stays with the author, and the
raw text stays the authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from overlord_worldsim.canon.enrich_model import (
    AbilityProfile,
    DetailedEvent,
    EnrichmentBatch,
    EventPrerequisite,
    EventPrerequisiteKind,
    ItemDef,
    ItemInstance,
    LocationProfile,
    OrganizationProfile,
    Route,
)
from overlord_worldsim.canon.enrich_registry import EntityRegistry
from overlord_worldsim.canon.extract_model import EntityKind, parse_canon_date
from overlord_worldsim.canon.parse import ParsedDocument

EVIDENCE_PREFIX = "EV"
PROFILE_PREFIX = "CP"
CASE_PREFIX = "BC"
EVENT_PREFIX = "DE"
PREREQ_PREFIX = "EP"
DEP_PREFIX = "ED"
CHANGE_PREFIX = "SC"
ITEM_PREFIX = "IT"
INSTANCE_PREFIX = "IN"
OWNERSHIP_PREFIX = "OH"
ABILITY_PREFIX = "AB"
COMPARE_PREFIX = "PC"
RULE_PREFIX = "WR"
LOCATION_PREFIX = "LO"
ROUTE_PREFIX = "RT"
TRAVEL_PREFIX = "TO"
ORGANIZATION_PREFIX = "OR"
POLITICAL_PREFIX = "PS"
SPECIES_PREFIX = "SP"
CREATURE_PREFIX = "CR"
BELIEF_PREFIX = "BL"
ECONOMY_PREFIX = "EC"
RELATION_PREFIX = "RC"
SPEECH_PREFIX = "ST"
CONFLICT_PREFIX = "CC"
GAP_PREFIX = "GAP"


@dataclass(frozen=True)
class VerificationError:
    code: str
    path: str
    message: str

    def to_json(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


@dataclass(frozen=True)
class VerificationReport:
    is_clean: bool
    errors: tuple[VerificationError, ...] = field(default_factory=tuple)

    def to_json(self) -> dict[str, object]:
        return {
            "is_clean": self.is_clean,
            "errors": [error.to_json() for error in self.errors],
        }


def _check_id_prefix(
    errors: list[VerificationError],
    collection: str,
    record_id: str,
    prefix: str,
) -> None:
    if not record_id.startswith(prefix):
        errors.append(
            VerificationError(
                "id_prefix",
                f"{collection}.{record_id}",
                f"id must start with {prefix}",
            )
        )


def _check_evidence_set(
    errors: list[VerificationError],
    path: str,
    evidence_ids: tuple[str, ...],
    batch_evidence: set[str],
) -> None:
    for evidence_id in evidence_ids:
        if evidence_id not in batch_evidence:
            errors.append(
                VerificationError(
                    "evidence_ref",
                    path,
                    f"unknown evidence ref {evidence_id} in batch",
                )
            )


def _check_date(
    errors: list[VerificationError],
    path: str,
    label: str,
    value: str | None,
) -> tuple[int, int] | None:
    if value is None:
        return None
    try:
        return parse_canon_date(value)
    except ValueError as error:
        errors.append(VerificationError("date", path, f"{label}: {error}"))
        return None


def _check_visible_window(
    errors: list[VerificationError],
    path: str,
    visible_from_volume: int,
    visible_to_volume: int | None,
) -> None:
    if visible_to_volume is not None and visible_to_volume < visible_from_volume:
        errors.append(
            VerificationError(
                "visible_window",
                path,
                "visible_to_volume precedes visible_from_volume",
            )
        )


class _Corpus:
    """Merged view over all enrichment batches for cross-reference checks."""

    def __init__(self, batches: list[EnrichmentBatch]) -> None:
        self.items: dict[str, ItemDef] = {}
        self.instances: dict[str, ItemInstance] = {}
        self.abilities: dict[str, AbilityProfile] = {}
        self.locations: dict[str, LocationProfile] = {}
        self.routes: dict[str, Route] = {}
        self.organizations: dict[str, OrganizationProfile] = {}
        self.species: dict[str, object] = {}
        self.creatures: dict[str, object] = {}
        self.detailed_events: dict[str, DetailedEvent] = {}
        self.events_by_volume: dict[int, list[str]] = {}
        for batch in batches:
            for item in batch.items:
                self.items[item.item_id] = item
            for instance in batch.item_instances:
                self.instances[instance.instance_id] = instance
            for ability in batch.abilities:
                self.abilities[ability.ability_id] = ability
            for location in batch.locations:
                self.locations[location.location_id] = location
            for route in batch.routes:
                self.routes[route.route_id] = route
            for org in batch.organizations:
                self.organizations[org.organization_id] = org
            for event in batch.detailed_events:
                self.detailed_events[event.event_id] = event
                self.events_by_volume.setdefault(event.volume_no, []).append(event.event_id)


class _Checker:
    def __init__(
        self,
        errors: list[VerificationError],
        doc: ParsedDocument,
        registry: EntityRegistry,
        corpus: _Corpus,
    ) -> None:
        self.errors = errors
        self.doc = doc
        self.registry = registry
        self.corpus = corpus
        self.batch_evidence: set[str] = set()
        self.unit_by_id = {unit.unit_id: unit for unit in doc.units}
        self.volume_ranges: dict[int, tuple[tuple[int, int], ...]] = {}
        collected: dict[int, list[tuple[int, int]]] = {}
        for unit in doc.units:
            if unit.volume_no is None:
                continue
            collected.setdefault(unit.volume_no, []).append((unit.start_line, unit.end_line))
        self.volume_ranges = {v: tuple(r) for v, r in collected.items()}
        self.timeline_event_ids = registry.timeline_event_ids()

    def _in_volume(self, volume_no: int, line: int) -> bool:
        ranges = self.volume_ranges.get(volume_no)
        if ranges is None:
            return False
        return any(start <= line <= end for start, end in ranges)

    def _check_entity_ref(
        self,
        path: str,
        entity_id: str | None,
        *,
        kind: EntityKind | None = None,
    ) -> bool:
        if entity_id is None:
            return True
        entity = self.registry.by_id(entity_id)
        if entity is None:
            self.errors.append(VerificationError("entity_ref", path, f"unknown entity {entity_id}"))
            return False
        if kind is not None and entity.kind is not EntityKind.UNKNOWN and entity.kind is not kind:
            self.errors.append(
                VerificationError(
                    "entity_kind",
                    path,
                    f"{entity_id} is {entity.kind.value}, expected {kind.value}",
                )
            )
            return False
        return True

    def check_evidence(self, batch: EnrichmentBatch) -> set[str]:
        ids: set[str] = set()
        for evidence in batch.evidence:
            path = f"{batch.batch_id}.evidence.{evidence.evidence_id}"
            if evidence.evidence_id in ids:
                self.errors.append(VerificationError("duplicate_id", path, "duplicate evidence_id"))
            ids.add(evidence.evidence_id)
            _check_id_prefix(self.errors, "evidence", evidence.evidence_id, EVIDENCE_PREFIX)
            if evidence.volume_no not in self.volume_ranges:
                self.errors.append(
                    VerificationError(
                        "evidence_volume", path, f"volume {evidence.volume_no} is not parsed"
                    )
                )
                continue
            unit = self.unit_by_id.get(evidence.unit_id)
            if unit is None:
                self.errors.append(
                    VerificationError("evidence_unit", path, f"unknown unit {evidence.unit_id}")
                )
                continue
            if unit.volume_no != evidence.volume_no:
                self.errors.append(
                    VerificationError(
                        "evidence_unit_volume",
                        path,
                        f"unit {evidence.unit_id} belongs to volume {unit.volume_no}, "
                        f"not {evidence.volume_no}",
                    )
                )
            if evidence.source_start_line > evidence.source_end_line:
                self.errors.append(
                    VerificationError(
                        "evidence_order", path, "source_start_line after source_end_line"
                    )
                )
            if not (
                unit.start_line <= evidence.source_start_line <= unit.end_line
                and unit.start_line <= evidence.source_end_line <= unit.end_line
            ):
                self.errors.append(
                    VerificationError(
                        "evidence_lines",
                        path,
                        f"lines {evidence.source_start_line}-{evidence.source_end_line} "
                        f"fall outside unit {evidence.unit_id}",
                    )
                )
        return ids

    def check_profiles(self, batch: EnrichmentBatch) -> None:
        for profile in batch.character_profiles:
            path = f"profiles.{profile.profile_id}"
            _check_id_prefix(self.errors, "profiles", profile.profile_id, PROFILE_PREFIX)
            self._check_entity_ref(path, profile.character_id)
            start = _check_date(self.errors, path, "start_date", profile.start_date)
            end = _check_date(self.errors, path, "end_date", profile.end_date)
            if start is not None and end is not None and start > end:
                self.errors.append(
                    VerificationError("date_order", path, "start_date after end_date")
                )
            _check_visible_window(
                self.errors, path, profile.visible_from_volume, profile.visible_to_volume
            )
            _check_evidence_set(self.errors, path, profile.evidence_refs, self.batch_evidence)

    def check_cases(self, batch: EnrichmentBatch) -> None:
        for case in batch.behavior_cases:
            path = f"cases.{case.case_id}"
            _check_id_prefix(self.errors, "cases", case.case_id, CASE_PREFIX)
            self._check_entity_ref(path, case.character_id)
            if case.volume_no not in self.volume_ranges:
                self.errors.append(
                    VerificationError("case_volume", path, f"volume {case.volume_no} is not parsed")
                )
            _check_evidence_set(self.errors, path, case.evidence_refs, self.batch_evidence)

    def check_events(self, batch: EnrichmentBatch) -> None:
        for event in batch.detailed_events:
            path = f"events.{event.event_id}"
            _check_id_prefix(self.errors, "events", event.event_id, EVENT_PREFIX)
            if event.timeline_event_id is not None and event.timeline_event_id not in (
                self.timeline_event_ids | set(self.corpus.detailed_events)
            ):
                self.errors.append(
                    VerificationError(
                        "timeline_event_ref",
                        path,
                        f"unknown timeline event {event.timeline_event_id}",
                    )
                )
            if event.volume_no not in self.volume_ranges:
                self.errors.append(
                    VerificationError(
                        "event_volume", path, f"volume {event.volume_no} is not parsed"
                    )
                )
            _check_date(self.errors, path, "time_date", event.time_date)
            self._check_entity_ref(path, event.location_id, kind=EntityKind.LOCATION)
            for participant in event.participants:
                self._check_entity_ref(f"{path}.participant", participant)
            for prerequisite in event.prerequisites:
                prereq_path = f"{path}.prerequisites.{prerequisite.prerequisite_id}"
                _check_id_prefix(
                    self.errors, "prerequisites", prerequisite.prerequisite_id, PREREQ_PREFIX
                )
                self._check_prerequisite(prereq_path, prerequisite)
            for dependency in event.dependencies:
                dep_path = f"{path}.dependencies.{dependency.dependency_id}"
                _check_id_prefix(self.errors, "dependencies", dependency.dependency_id, DEP_PREFIX)
                if dependency.target_event_id not in (
                    self.timeline_event_ids | set(self.corpus.detailed_events)
                ):
                    self.errors.append(
                        VerificationError(
                            "dependency_event_ref",
                            dep_path,
                            f"unknown target event {dependency.target_event_id}",
                        )
                    )
            for state_change in event.state_changes:
                _check_id_prefix(
                    self.errors, "state_changes", state_change.change_id, CHANGE_PREFIX
                )
            for change_id in event.relationship_change_ids:
                if change_id not in {c.change_id for c in batch.relationship_changes}:
                    self.errors.append(
                        VerificationError(
                            "relationship_change_ref",
                            path,
                            f"unknown relationship change {change_id}",
                        )
                    )
            for belief_id in event.belief_ids:
                if belief_id not in {b.belief_id for b in batch.beliefs}:
                    self.errors.append(
                        VerificationError("belief_ref", path, f"unknown belief {belief_id}")
                    )
            _check_evidence_set(self.errors, path, event.evidence_refs, self.batch_evidence)

    def _check_prerequisite(self, path: str, prerequisite: EventPrerequisite) -> None:
        ref_id = prerequisite.ref_id
        kind = prerequisite.prerequisite_type
        if ref_id is None:
            return
        if kind is EventPrerequisiteKind.EVENT:
            if ref_id not in (self.timeline_event_ids | set(self.corpus.detailed_events)):
                self.errors.append(
                    VerificationError("prereq_event_ref", path, f"unknown event {ref_id}")
                )
        elif kind is EventPrerequisiteKind.ITEM:
            if ref_id not in self.corpus.items:
                self.errors.append(
                    VerificationError("prereq_item_ref", path, f"unknown item {ref_id}")
                )
        elif kind is EventPrerequisiteKind.LOCATION:
            self._check_entity_ref(path, ref_id, kind=EntityKind.LOCATION)
        elif kind in (
            EventPrerequisiteKind.PERSON_ALIVE,
            EventPrerequisiteKind.PERSON_PRESENT,
        ):
            self._check_entity_ref(path, ref_id)
        _check_evidence_set(self.errors, path, prerequisite.evidence_refs, self.batch_evidence)

    def check_items(self, batch: EnrichmentBatch) -> None:
        for item in batch.items:
            path = f"items.{item.item_id}"
            _check_id_prefix(self.errors, "items", item.item_id, ITEM_PREFIX)
            if item.first_appearance_volume not in self.volume_ranges:
                self.errors.append(
                    VerificationError(
                        "item_first_volume",
                        path,
                        f"volume {item.first_appearance_volume} is not parsed",
                    )
                )
            elif not self._in_volume(item.first_appearance_volume, item.first_appearance_line):
                self.errors.append(
                    VerificationError(
                        "item_first_line",
                        path,
                        f"line {item.first_appearance_line} outside "
                        f"volume {item.first_appearance_volume}",
                    )
                )
            _check_visible_window(self.errors, path, item.visible_from_volume, None)
            _check_evidence_set(self.errors, path, item.evidence_refs, self.batch_evidence)
        for instance in batch.item_instances:
            path = f"instances.{instance.instance_id}"
            _check_id_prefix(self.errors, "instances", instance.instance_id, INSTANCE_PREFIX)
            if instance.definition_id not in self.corpus.items:
                self.errors.append(
                    VerificationError(
                        "instance_definition",
                        path,
                        f"unknown item definition {instance.definition_id}",
                    )
                )
            self._check_entity_ref(path, instance.owner_id)
            self._check_entity_ref(path, instance.holder_id)
            self._check_entity_ref(path, instance.location_id, kind=EntityKind.LOCATION)
            entry_ids: set[str] = set()
            for entry in instance.ownership_history:
                entry_path = f"{path}.ownership.{entry.entry_id}"
                _check_id_prefix(self.errors, "ownership", entry.entry_id, OWNERSHIP_PREFIX)
                if entry.entry_id in entry_ids:
                    self.errors.append(
                        VerificationError("duplicate_id", entry_path, "duplicate entry_id")
                    )
                entry_ids.add(entry.entry_id)
                self._check_entity_ref(entry_path, entry.owner_id)
            _check_evidence_set(self.errors, path, instance.evidence_refs, self.batch_evidence)

    def check_abilities(self, batch: EnrichmentBatch) -> None:
        for ability in batch.abilities:
            path = f"abilities.{ability.ability_id}"
            _check_id_prefix(self.errors, "abilities", ability.ability_id, ABILITY_PREFIX)
            for user in ability.known_users:
                self._check_entity_ref(f"{path}.user", user)
            _check_evidence_set(self.errors, path, ability.evidence_refs, self.batch_evidence)

    def check_comparisons(self, batch: EnrichmentBatch) -> None:
        for comparison in batch.power_comparisons:
            path = f"comparisons.{comparison.comparison_id}"
            _check_id_prefix(self.errors, "comparisons", comparison.comparison_id, COMPARE_PREFIX)
            self._check_entity_ref(path, comparison.actor_id)
            self._check_entity_ref(path, comparison.target_id)
            _check_evidence_set(self.errors, path, comparison.evidence_refs, self.batch_evidence)

    def check_world_rules(self, batch: EnrichmentBatch) -> None:
        for rule in batch.world_rules:
            path = f"rules.{rule.rule_id}"
            _check_id_prefix(self.errors, "rules", rule.rule_id, RULE_PREFIX)
            _check_evidence_set(self.errors, path, rule.evidence_refs, self.batch_evidence)

    def check_locations(self, batch: EnrichmentBatch) -> None:
        for location in batch.locations:
            path = f"locations.{location.location_id}"
            # Location profiles are keyed by their entity id (E-prefix), so the
            # prefix rule does not apply; the entity-kind check is the gate.
            self._check_entity_ref(path, location.location_id, kind=EntityKind.LOCATION)
            self._check_entity_ref(
                f"{path}.parent", location.parent_location_id, kind=EntityKind.LOCATION
            )
            if location.first_appearance_volume not in self.volume_ranges:
                self.errors.append(
                    VerificationError(
                        "location_first_volume",
                        path,
                        f"volume {location.first_appearance_volume} is not parsed",
                    )
                )
            elif not self._in_volume(
                location.first_appearance_volume, location.first_appearance_line
            ):
                self.errors.append(
                    VerificationError(
                        "location_first_line",
                        path,
                        f"line {location.first_appearance_line} outside "
                        f"volume {location.first_appearance_volume}",
                    )
                )
            for route_id in location.known_routes:
                if route_id not in self.corpus.routes:
                    self.errors.append(
                        VerificationError("route_ref", path, f"unknown route {route_id}")
                    )
            for neighbor in location.nearby_locations:
                self._check_entity_ref(f"{path}.nearby", neighbor, kind=EntityKind.LOCATION)
            for person in location.important_people:
                self._check_entity_ref(f"{path}.person", person)
            _check_evidence_set(self.errors, path, location.evidence_refs, self.batch_evidence)

    def check_routes(self, batch: EnrichmentBatch) -> None:
        for route in batch.routes:
            path = f"routes.{route.route_id}"
            _check_id_prefix(self.errors, "routes", route.route_id, ROUTE_PREFIX)
            self._check_entity_ref(path, route.from_location_id, kind=EntityKind.LOCATION)
            self._check_entity_ref(path, route.to_location_id, kind=EntityKind.LOCATION)
            _check_evidence_set(self.errors, path, route.evidence_refs, self.batch_evidence)
        for observation in batch.travel_observations:
            path = f"travel.{observation.observation_id}"
            _check_id_prefix(self.errors, "travel", observation.observation_id, TRAVEL_PREFIX)
            if observation.route_id not in self.corpus.routes:
                self.errors.append(
                    VerificationError(
                        "travel_route_ref", path, f"unknown route {observation.route_id}"
                    )
                )
            for character in observation.characters:
                self._check_entity_ref(f"{path}.character", character)
            _check_evidence_set(self.errors, path, observation.evidence_refs, self.batch_evidence)

    def check_organizations(self, batch: EnrichmentBatch) -> None:
        for organization in batch.organizations:
            path = f"organizations.{organization.organization_id}"
            # Organization profiles are keyed by their entity id (E-prefix) or a
            # dedicated OR-prefixed id; both are valid registry references.
            self._check_entity_ref(path, organization.organization_id)
            for leader in organization.leaders:
                self._check_entity_ref(f"{path}.leader", leader)
            for member in organization.members:
                self._check_entity_ref(f"{path}.member", member)
            _check_evidence_set(self.errors, path, organization.evidence_refs, self.batch_evidence)
        for state in batch.political_states:
            path = f"political.{state.state_id}"
            _check_id_prefix(self.errors, "political", state.state_id, POLITICAL_PREFIX)
            if state.organization_id not in self.corpus.organizations and not self.registry.has(
                state.organization_id
            ):
                self.errors.append(
                    VerificationError(
                        "political_org_ref",
                        path,
                        f"unknown organization {state.organization_id}",
                    )
                )
            start = _check_date(self.errors, path, "start_date", state.start_date)
            end = _check_date(self.errors, path, "end_date", state.end_date)
            if start is not None and end is not None and start > end:
                self.errors.append(
                    VerificationError("date_order", path, "start_date after end_date")
                )
            _check_evidence_set(self.errors, path, state.evidence_refs, self.batch_evidence)

    def check_species(self, batch: EnrichmentBatch) -> None:
        seen: set[str] = set()
        for species in batch.species:
            path = f"species.{species.species_id}"
            _check_id_prefix(self.errors, "species", species.species_id, SPECIES_PREFIX)
            if species.species_id in seen:
                self.errors.append(VerificationError("duplicate_id", path, "duplicate id"))
            seen.add(species.species_id)
            _check_evidence_set(self.errors, path, species.evidence_refs, self.batch_evidence)
        for creature in batch.creatures:
            path = f"creatures.{creature.creature_id}"
            _check_id_prefix(self.errors, "creatures", creature.creature_id, CREATURE_PREFIX)
            _check_evidence_set(self.errors, path, creature.evidence_refs, self.batch_evidence)

    def check_beliefs(self, batch: EnrichmentBatch) -> None:
        for belief in batch.beliefs:
            path = f"beliefs.{belief.belief_id}"
            _check_id_prefix(self.errors, "beliefs", belief.belief_id, BELIEF_PREFIX)
            self._check_entity_ref(path, belief.owner_id)
            if belief.learned_at_volume is not None and belief.learned_at_volume not in (
                self.volume_ranges
            ):
                self.errors.append(
                    VerificationError(
                        "belief_learned_volume",
                        path,
                        f"volume {belief.learned_at_volume} is not parsed",
                    )
                )
            if (
                belief.learned_at_volume is not None
                and belief.visible_from_volume is not None
                and belief.learned_at_volume > belief.visible_from_volume
            ):
                self.errors.append(
                    VerificationError(
                        "belief_learned_window",
                        path,
                        "learned_at_volume after visible_from_volume",
                    )
                )
            _check_visible_window(
                self.errors, path, belief.visible_from_volume, belief.visible_to_volume
            )
            _check_evidence_set(self.errors, path, belief.evidence_refs, self.batch_evidence)

    def check_economy(self, batch: EnrichmentBatch) -> None:
        for observation in batch.economic_observations:
            path = f"economy.{observation.observation_id}"
            _check_id_prefix(self.errors, "economy", observation.observation_id, ECONOMY_PREFIX)
            if observation.location_id is not None:
                self._check_entity_ref(path, observation.location_id, kind=EntityKind.LOCATION)
            if observation.item_id is not None and observation.item_id not in self.corpus.items:
                self.errors.append(
                    VerificationError(
                        "economy_item_ref", path, f"unknown item {observation.item_id}"
                    )
                )
            _check_date(self.errors, path, "at_date", observation.at_date)
            if observation.at_volume not in self.volume_ranges:
                self.errors.append(
                    VerificationError(
                        "economy_volume", path, f"volume {observation.at_volume} is not parsed"
                    )
                )
            _check_evidence_set(self.errors, path, observation.evidence_refs, self.batch_evidence)

    def check_relationships(self, batch: EnrichmentBatch) -> None:
        for change in batch.relationship_changes:
            path = f"relationships.{change.change_id}"
            _check_id_prefix(self.errors, "relationships", change.change_id, RELATION_PREFIX)
            self._check_entity_ref(path, change.source_id)
            self._check_entity_ref(path, change.target_id)
            _check_date(self.errors, path, "at_date", change.at_date)
            _check_evidence_set(self.errors, path, change.evidence_refs, self.batch_evidence)

    def check_speech(self, batch: EnrichmentBatch) -> None:
        for profile in batch.speech_profiles:
            path = f"speech.{profile.profile_id}"
            _check_id_prefix(self.errors, "speech", profile.profile_id, SPEECH_PREFIX)
            self._check_entity_ref(path, profile.character_id)
            _check_evidence_set(self.errors, path, profile.evidence_refs, self.batch_evidence)

    def check_conflicts(self, batch: EnrichmentBatch) -> None:
        for conflict in batch.canon_conflicts:
            path = f"conflicts.{conflict.conflict_id}"
            _check_id_prefix(self.errors, "conflicts", conflict.conflict_id, CONFLICT_PREFIX)
            _check_evidence_set(self.errors, path, conflict.evidence_a_refs, self.batch_evidence)
            _check_evidence_set(self.errors, path, conflict.evidence_b_refs, self.batch_evidence)

    def check_gaps(self, batch: EnrichmentBatch) -> None:
        for gap in batch.canon_gaps:
            path = f"gaps.{gap.gap_id}"
            _check_id_prefix(self.errors, "gaps", gap.gap_id, GAP_PREFIX)
            for volume in gap.searched_volumes:
                if volume not in self.volume_ranges:
                    self.errors.append(
                        VerificationError("gap_volume", path, f"volume {volume} is not parsed")
                    )


def _check_duplicate_names(
    errors: list[VerificationError],
    collection: str,
    records: list[object],
) -> None:
    """Flag duplicate canonical names and alias collisions within a collection."""
    names: dict[str, str] = {}
    for record in records:
        record_id = getattr(record, "record_id", None) or getattr(record, "item_id", None) or ""
        if record_id is None or record_id == "":
            continue
        canonical_name = getattr(record, "canonical_name", None) or getattr(record, "name", None)
        if canonical_name:
            existing = names.get(canonical_name)
            if existing is not None and existing != record_id:
                errors.append(
                    VerificationError(
                        "duplicate_name",
                        f"{collection}.{record_id}",
                        f"canonical name {canonical_name!r} also used by {existing}",
                    )
                )
            names[canonical_name] = record_id
        for alias in getattr(record, "aliases", ()):
            existing = names.get(alias)
            if existing is not None and existing != record_id:
                errors.append(
                    VerificationError(
                        "alias_collision",
                        f"{collection}.{record_id}",
                        f"alias {alias!r} also used by {existing}",
                    )
                )
            names[alias] = record_id


def verify_enrichment(
    batches: list[EnrichmentBatch],
    doc: ParsedDocument,
    registry: EntityRegistry,
) -> VerificationReport:
    """Verify the whole enrichment corpus; returns a deterministic report."""
    errors: list[VerificationError] = []
    corpus = _Corpus(batches)
    checker = _Checker(errors, doc, registry, corpus)

    batch_evidence: dict[str, set[str]] = {}
    for batch in batches:
        if batch.schema_version != EnrichmentBatch.ENRICHMENT_SCHEMA_VERSION:
            errors.append(
                VerificationError(
                    "schema_version",
                    batch.batch_id,
                    f"schema_version {batch.schema_version} != "
                    f"{EnrichmentBatch.ENRICHMENT_SCHEMA_VERSION}",
                )
            )
        if batch.source_volume not in checker.volume_ranges:
            errors.append(
                VerificationError(
                    "batch_volume",
                    batch.batch_id,
                    f"source_volume {batch.source_volume} is not parsed",
                )
            )
        for unit_id in batch.source_unit_ids:
            if unit_id not in checker.unit_by_id:
                errors.append(
                    VerificationError("batch_unit", batch.batch_id, f"unknown unit {unit_id}")
                )
            elif checker.unit_by_id[unit_id].volume_no != batch.source_volume:
                errors.append(
                    VerificationError(
                        "batch_unit_volume",
                        batch.batch_id,
                        f"unit {unit_id} is not in volume {batch.source_volume}",
                    )
                )

    for batch in batches:
        batch_evidence[batch.batch_id] = checker.check_evidence(batch)
        checker.batch_evidence = batch_evidence[batch.batch_id]
        checker.check_profiles(batch)
        checker.check_cases(batch)
        checker.check_events(batch)
        checker.check_items(batch)
        checker.check_abilities(batch)
        checker.check_comparisons(batch)
        checker.check_world_rules(batch)
        checker.check_locations(batch)
        checker.check_routes(batch)
        checker.check_organizations(batch)
        checker.check_species(batch)
        checker.check_beliefs(batch)
        checker.check_economy(batch)
        checker.check_relationships(batch)
        checker.check_speech(batch)
        checker.check_conflicts(batch)
        checker.check_gaps(batch)

    _check_unique_ids(errors, batches)
    _check_duplicate_names(errors, "items", list(corpus.items.values()))
    _check_duplicate_names(errors, "abilities", list(corpus.abilities.values()))

    errors.sort(key=lambda error: (error.path, error.code, error.message))
    return VerificationReport(is_clean=not errors, errors=tuple(errors))


def _check_unique_ids(errors: list[VerificationError], batches: list[EnrichmentBatch]) -> None:
    """Detect duplicate record ids per collection across all batches."""
    collection_ids: dict[str, dict[str, str]] = {
        "profiles": {},
        "cases": {},
        "events": {},
        "prerequisites": {},
        "dependencies": {},
        "state_changes": {},
        "items": {},
        "instances": {},
        "ownership": {},
        "abilities": {},
        "comparisons": {},
        "rules": {},
        "locations": {},
        "routes": {},
        "travel": {},
        "organizations": {},
        "political": {},
        "species": {},
        "creatures": {},
        "beliefs": {},
        "economy": {},
        "relationships": {},
        "speech": {},
        "conflicts": {},
        "gaps": {},
    }

    def register(collection: str, record_id: str, batch_id: str) -> None:
        table = collection_ids[collection]
        if record_id in table:
            errors.append(
                VerificationError(
                    "duplicate_id",
                    f"{collection}.{record_id}",
                    f"duplicate across batches ({table[record_id]}, {batch_id})",
                )
            )
        table[record_id] = batch_id

    for batch in batches:
        for profile in batch.character_profiles:
            register("profiles", profile.profile_id, batch.batch_id)
        for case in batch.behavior_cases:
            register("cases", case.case_id, batch.batch_id)
        for event in batch.detailed_events:
            register("events", event.event_id, batch.batch_id)
            for prerequisite in event.prerequisites:
                register("prerequisites", prerequisite.prerequisite_id, batch.batch_id)
            for dependency in event.dependencies:
                register("dependencies", dependency.dependency_id, batch.batch_id)
            for state_change in event.state_changes:
                register("state_changes", state_change.change_id, batch.batch_id)
        for item in batch.items:
            register("items", item.item_id, batch.batch_id)
        for instance in batch.item_instances:
            register("instances", instance.instance_id, batch.batch_id)
            for entry in instance.ownership_history:
                register("ownership", entry.entry_id, batch.batch_id)
        for ability in batch.abilities:
            register("abilities", ability.ability_id, batch.batch_id)
        for comparison in batch.power_comparisons:
            register("comparisons", comparison.comparison_id, batch.batch_id)
        for rule in batch.world_rules:
            register("rules", rule.rule_id, batch.batch_id)
        for location in batch.locations:
            register("locations", location.location_id, batch.batch_id)
        for route in batch.routes:
            register("routes", route.route_id, batch.batch_id)
        for observation in batch.travel_observations:
            register("travel", observation.observation_id, batch.batch_id)
        for organization in batch.organizations:
            register("organizations", organization.organization_id, batch.batch_id)
        for state in batch.political_states:
            register("political", state.state_id, batch.batch_id)
        for species in batch.species:
            register("species", species.species_id, batch.batch_id)
        for creature in batch.creatures:
            register("creatures", creature.creature_id, batch.batch_id)
        for belief in batch.beliefs:
            register("beliefs", belief.belief_id, batch.batch_id)
        for economic in batch.economic_observations:
            register("economy", economic.observation_id, batch.batch_id)
        for change in batch.relationship_changes:
            register("relationships", change.change_id, batch.batch_id)
        for speech in batch.speech_profiles:
            register("speech", speech.profile_id, batch.batch_id)
        for conflict in batch.canon_conflicts:
            register("conflicts", conflict.conflict_id, batch.batch_id)
        for gap in batch.canon_gaps:
            register("gaps", gap.gap_id, batch.batch_id)
