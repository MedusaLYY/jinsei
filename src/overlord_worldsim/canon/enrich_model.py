"""Enrichment layer models: simulation-oriented canon content.

This is the second content layer on top of the M4/M5 extraction batches.
Where `extract_model` records *what is known*, the enrichment layer records
*what the world simulator must know to adjudicate counterfactuals*:

- phase-specific character behavior profiles
- behavior cases (what a character actually did in a comparable situation)
- detailed events with prerequisites / dependencies / state changes
- item definitions, instances, and ownership history
- ability / power profiles and comparative power evidence
- world rules (magic, sword, society, economy, …)
- locations, routes, and travel observations
- organizations and time-sliced political states
- species and creatures
- beliefs with provenance (including false beliefs)
- economic observations (prices with evidence only)
- relationship changes with dimensions
- speech profiles
- canon conflicts and canon gaps (explicit UNKNOWN)

All records carry evidence references into a per-batch `evidence` array;
every evidence entry points at the raw source by volume + line range, so the
novel text stays authoritative. No field may be invented: anything the text
does not support is either `null` or recorded as a `canon_gap`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar

from overlord_worldsim.canon.extract_model import Confidence, DatePrecision

_RECORD_ID = re.compile(r"^[A-Z]{2}\d{4,}$")
_DATE_PATTERN = re.compile(r"^(\d{3})-(\d{1,2})$")


class EvidenceType(Enum):
    """How directly the referenced text supports the claim."""

    CANON_EXPLICIT = "CANON_EXPLICIT"
    CANON_ANALOGICAL = "CANON_ANALOGICAL"
    STRONG_INFERENCE = "STRONG_INFERENCE"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"


class BehaviorTag(Enum):
    """Stable tag vocabulary for behavior-case analogical retrieval."""

    TEACHING = "TEACHING"
    TRAINING = "TRAINING"
    ROMANCE = "ROMANCE"
    EMBARRASSMENT = "EMBARRASSMENT"
    SHAME = "SHAME"
    ANGER = "ANGER"
    FEAR = "FEAR"
    COMBAT = "COMBAT"
    PROTECT = "PROTECT"
    RETREAT = "RETREAT"
    NEGOTIATION = "NEGOTIATION"
    MONEY = "MONEY"
    FAMILY = "FAMILY"
    JEALOUSY = "JEALOUSY"
    LOYALTY = "LOYALTY"
    BETRAYAL = "BETRAYAL"
    AUTHORITY = "AUTHORITY"
    NOBILITY = "NOBILITY"
    FRIENDSHIP = "FRIENDSHIP"
    TRUST = "TRUST"
    SUSPICION = "SUSPICION"
    DANGER = "DANGER"
    MORAL_CHOICE = "MORAL_CHOICE"
    REQUEST = "REQUEST"
    REJECTION = "REJECTION"
    ACCEPTANCE = "ACCEPTANCE"
    APOLOGY = "APOLOGY"
    GRATITUDE = "GRATITUDE"
    LOSS = "LOSS"
    GRIEF = "GRIEF"
    ATTRACTION = "ATTRACTION"
    HUMOR = "HUMOR"
    TEASING = "TEASING"
    LIE = "LIE"
    SECRET = "SECRET"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PUBLIC_SCENE = "PUBLIC_SCENE"
    PRIVATE_SCENE = "PRIVATE_SCENE"


class EventPrerequisiteKind(Enum):
    """What a prerequisite constrains: an event, an item, a state, …"""

    EVENT = "EVENT"
    ITEM = "ITEM"
    STATE = "STATE"
    LOCATION = "LOCATION"
    PERSON_ALIVE = "PERSON_ALIVE"
    PERSON_PRESENT = "PERSON_PRESENT"
    GOAL = "GOAL"
    KNOWLEDGE = "KNOWLEDGE"
    POLITICAL = "POLITICAL"


class EventDependencyKind(Enum):
    """How one event depends on another (causal graph edge type)."""

    REQUIRES = "REQUIRES"
    ENABLES = "ENABLES"
    CAUSES = "CAUSES"
    INFLUENCES = "INFLUENCES"
    REVEALS = "REVEALS"
    INVALIDATES = "INVALIDATES"


class WorldRuleDomain(Enum):
    """Domain of a world rule (magic, sword, society, economy, …)."""

    MAGIC = "MAGIC"
    SWORD = "SWORD"
    TOUGI = "TOUGI"
    MAGIC_EYE = "MAGIC_EYE"
    TRAINING = "TRAINING"
    SOCIETY = "SOCIETY"
    LAW = "LAW"
    NOBILITY = "NOBILITY"
    MARRIAGE = "MARRIAGE"
    FAMILY = "FAMILY"
    ADVENTURER = "ADVENTURER"
    SLAVERY = "SLAVERY"
    RELIGION = "RELIGION"
    ECONOMY = "ECONOMY"
    GEOGRAPHY = "GEOGRAPHY"
    RACE = "RACE"
    POLITICS = "POLITICS"
    WAR = "WAR"
    DUEL = "DUEL"
    EDUCATION = "EDUCATION"
    COMBAT = "COMBAT"
    SPECIES = "SPECIES"
    MONSTER = "MONSTER"
    GENERAL = "GENERAL"


class BeliefState(Enum):
    """A character's cognitive state about a claim."""

    FACT_KNOWN = "FACT_KNOWN"
    HEARD = "HEARD"
    RUMOR = "RUMOR"
    INFERRED = "INFERRED"
    SUSPECTED = "SUSPECTED"
    MISUNDERSTOOD = "MISUNDERSTOOD"
    FALSE_BELIEF = "FALSE_BELIEF"
    UNKNOWN = "UNKNOWN"


class PriceClass(Enum):
    """Quality of an economic observation: never invent precise prices."""

    OBSERVED_PRICE = "OBSERVED_PRICE"
    DERIVED_RANGE = "DERIVED_RANGE"
    QUALITATIVE = "QUALITATIVE"
    UNKNOWN = "UNKNOWN"


class ConflictStatus(Enum):
    """Disposition of an apparent canon contradiction."""

    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    RETCON = "RETCON"
    POV_DIFFERENCE = "POV_DIFFERENCE"
    TRANSLATION_AMBIGUITY = "TRANSLATION_AMBIGUITY"


class GapStatus(Enum):
    """Whether a canon question has an answer in the source."""

    OPEN = "OPEN"
    NO_CANON_ANSWER = "NO_CANON_ANSWER"
    PARTIAL = "PARTIAL"


class EventImportance(Enum):
    """How strongly an event shapes long-term world state."""

    MAJOR = "MAJOR"
    MINOR = "MINOR"
    BACKGROUND = "BACKGROUND"


class AbilityType(Enum):
    """Broad ability category used by the rules and the runtime."""

    MAGIC = "MAGIC"
    SWORD = "SWORD"
    TOUGI = "TOUGI"
    MAGIC_EYE = "MAGIC_EYE"
    SPECIES = "SPECIES"
    PRAYER = "PRAYER"
    CURSE = "CURSE"
    BLESSING = "BLESSING"
    SPECIAL = "SPECIAL"
    TECHNIQUE = "TECHNIQUE"
    CRAFT = "CRAFT"
    KNOWLEDGE = "KNOWLEDGE"
    OTHER = "OTHER"


class LocationType(Enum):
    """Stable location taxonomy (canon names only, no invented subclasses)."""

    CONTINENT = "CONTINENT"
    COUNTRY = "COUNTRY"
    TERRITORY = "TERRITORY"
    CITY = "CITY"
    TOWN = "TOWN"
    VILLAGE = "VILLAGE"
    SCHOOL = "SCHOOL"
    HOUSE = "HOUSE"
    PALACE = "PALACE"
    DUNGEON = "DUNGEON"
    RUINS = "RUINS"
    FOREST = "FOREST"
    MOUNTAIN = "MOUNTAIN"
    PORT = "PORT"
    ROAD = "ROAD"
    INN = "INN"
    GUILD = "GUILD"
    SANCTUM = "SANCTUM"
    BATTLEFIELD = "BATTLEFIELD"
    OTHER = "OTHER"


def _to_json_array(values: tuple[str, ...]) -> list[str]:
    return list(values)


def _validate_record_id(record_id: str, prefix: str) -> None:
    if not record_id.startswith(prefix) or not _RECORD_ID.fullmatch(record_id):
        raise ValueError(f"invalid id {record_id!r} (expected {prefix}0001-style id)")


@dataclass(frozen=True)
class EvidenceRef:
    """One unified evidence reference into the raw source text."""

    evidence_id: str
    volume_no: int
    unit_id: str
    chapter_title: str
    source_start_line: int
    source_end_line: int
    evidence_type: EvidenceType
    confidence: Confidence
    note: str

    def to_json(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "volume_no": self.volume_no,
            "unit_id": self.unit_id,
            "chapter_title": self.chapter_title,
            "source_start_line": self.source_start_line,
            "source_end_line": self.source_end_line,
            "evidence_type": self.evidence_type.value,
            "confidence": self.confidence.value,
            "note": self.note,
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> EvidenceRef:
        return cls(
            evidence_id=document["evidence_id"],
            volume_no=document["volume_no"],
            unit_id=document["unit_id"],
            chapter_title=document["chapter_title"],
            source_start_line=document["source_start_line"],
            source_end_line=document["source_end_line"],
            evidence_type=EvidenceType(document["evidence_type"]),
            confidence=Confidence(document["confidence"]),
            note=document["note"],
        )


@dataclass(frozen=True)
class CharacterProfile:
    """Phase-specific behavioral profile (plan §11-§12, §60).

    World-sim extension (v1.1): deep personality layers, appearance/body,
    and decision/trigger modeling for GM adjudication. All new fields are
    optional with defaults so existing batches remain loadable.
    """

    profile_id: str
    character_id: str
    phase_id: str
    phase_name: str
    start_date: str | None
    end_date: str | None
    date_precision: DatePrecision
    age_description: str
    personality_traits: tuple[str, ...]
    values: tuple[str, ...]
    desires: tuple[str, ...]
    fears: tuple[str, ...]
    taboos: tuple[str, ...]
    insecurities: tuple[str, ...]
    pride: str | None
    impulsiveness: str | None
    patience: str | None
    risk_tolerance: str | None
    self_control: str | None
    attachment_style: str | None
    authority_attitude: str | None
    family_attitude: str | None
    romantic_attitude: str | None
    violence_attitude: str | None
    money_attitude: str | None
    status_attitude: str | None
    race_attitude: str | None
    religious_attitude: str | None
    loyalty: str | None
    ambition: str | None
    short_term_goals: tuple[str, ...]
    long_term_goals: tuple[str, ...]
    obligations: tuple[str, ...]
    decision_tendencies: tuple[str, ...]
    speech_tendencies: tuple[str, ...]
    social_tendencies: tuple[str, ...]
    conflict_tendencies: tuple[str, ...]
    known_skills: tuple[str, ...]
    knowledge_state: tuple[str, ...]
    relationship_tendencies: tuple[str, ...]
    behavior_changes_note: str
    summary: str
    visible_from_volume: int
    visible_to_volume: int | None
    evidence_refs: tuple[str, ...]
    # --- world-sim deep model extensions (v1.1, all optional) ---
    identity: str | None = None
    origin: str | None = None
    origin_location_id: str | None = None
    status_rank: str | None = None
    appearance_traits: tuple[str, ...] = ()
    body_traits: tuple[str, ...] = ()
    core_personality: tuple[str, ...] = ()
    surface_personality: tuple[str, ...] = ()
    hidden_personality: tuple[str, ...] = ()
    interests: tuple[str, ...] = ()
    dislikes: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    obsessions: tuple[str, ...] = ()
    habits: tuple[str, ...] = ()
    emotional_triggers: tuple[str, ...] = ()
    decision_logic: str | None = None
    extreme_choice_note: str | None = None
    phase_personality_note: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "character_id": self.character_id,
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "date_precision": self.date_precision.value,
            "age_description": self.age_description,
            "personality_traits": _to_json_array(self.personality_traits),
            "values": _to_json_array(self.values),
            "desires": _to_json_array(self.desires),
            "fears": _to_json_array(self.fears),
            "taboos": _to_json_array(self.taboos),
            "insecurities": _to_json_array(self.insecurities),
            "pride": self.pride,
            "impulsiveness": self.impulsiveness,
            "patience": self.patience,
            "risk_tolerance": self.risk_tolerance,
            "self_control": self.self_control,
            "attachment_style": self.attachment_style,
            "authority_attitude": self.authority_attitude,
            "family_attitude": self.family_attitude,
            "romantic_attitude": self.romantic_attitude,
            "violence_attitude": self.violence_attitude,
            "money_attitude": self.money_attitude,
            "status_attitude": self.status_attitude,
            "race_attitude": self.race_attitude,
            "religious_attitude": self.religious_attitude,
            "loyalty": self.loyalty,
            "ambition": self.ambition,
            "short_term_goals": _to_json_array(self.short_term_goals),
            "long_term_goals": _to_json_array(self.long_term_goals),
            "obligations": _to_json_array(self.obligations),
            "decision_tendencies": _to_json_array(self.decision_tendencies),
            "speech_tendencies": _to_json_array(self.speech_tendencies),
            "social_tendencies": _to_json_array(self.social_tendencies),
            "conflict_tendencies": _to_json_array(self.conflict_tendencies),
            "known_skills": _to_json_array(self.known_skills),
            "knowledge_state": _to_json_array(self.knowledge_state),
            "relationship_tendencies": _to_json_array(self.relationship_tendencies),
            "behavior_changes_note": self.behavior_changes_note,
            "summary": self.summary,
            "visible_from_volume": self.visible_from_volume,
            "visible_to_volume": self.visible_to_volume,
            "evidence_refs": _to_json_array(self.evidence_refs),
            "identity": self.identity,
            "origin": self.origin,
            "origin_location_id": self.origin_location_id,
            "status_rank": self.status_rank,
            "appearance_traits": _to_json_array(self.appearance_traits),
            "body_traits": _to_json_array(self.body_traits),
            "core_personality": _to_json_array(self.core_personality),
            "surface_personality": _to_json_array(self.surface_personality),
            "hidden_personality": _to_json_array(self.hidden_personality),
            "interests": _to_json_array(self.interests),
            "dislikes": _to_json_array(self.dislikes),
            "weaknesses": _to_json_array(self.weaknesses),
            "obsessions": _to_json_array(self.obsessions),
            "habits": _to_json_array(self.habits),
            "emotional_triggers": _to_json_array(self.emotional_triggers),
            "decision_logic": self.decision_logic,
            "extreme_choice_note": self.extreme_choice_note,
            "phase_personality_note": self.phase_personality_note,
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> CharacterProfile:
        return cls(
            profile_id=document["profile_id"],
            character_id=document["character_id"],
            phase_id=document["phase_id"],
            phase_name=document["phase_name"],
            start_date=document["start_date"],
            end_date=document["end_date"],
            date_precision=DatePrecision(document["date_precision"]),
            age_description=document["age_description"],
            personality_traits=tuple(document["personality_traits"]),
            values=tuple(document["values"]),
            desires=tuple(document["desires"]),
            fears=tuple(document["fears"]),
            taboos=tuple(document["taboos"]),
            insecurities=tuple(document["insecurities"]),
            pride=document["pride"],
            impulsiveness=document["impulsiveness"],
            patience=document["patience"],
            risk_tolerance=document["risk_tolerance"],
            self_control=document["self_control"],
            attachment_style=document["attachment_style"],
            authority_attitude=document["authority_attitude"],
            family_attitude=document["family_attitude"],
            romantic_attitude=document["romantic_attitude"],
            violence_attitude=document["violence_attitude"],
            money_attitude=document["money_attitude"],
            status_attitude=document["status_attitude"],
            race_attitude=document["race_attitude"],
            religious_attitude=document["religious_attitude"],
            loyalty=document["loyalty"],
            ambition=document["ambition"],
            short_term_goals=tuple(document["short_term_goals"]),
            long_term_goals=tuple(document["long_term_goals"]),
            obligations=tuple(document["obligations"]),
            decision_tendencies=tuple(document["decision_tendencies"]),
            speech_tendencies=tuple(document["speech_tendencies"]),
            social_tendencies=tuple(document["social_tendencies"]),
            conflict_tendencies=tuple(document["conflict_tendencies"]),
            known_skills=tuple(document["known_skills"]),
            knowledge_state=tuple(document["knowledge_state"]),
            relationship_tendencies=tuple(document["relationship_tendencies"]),
            behavior_changes_note=document["behavior_changes_note"],
            summary=document["summary"],
            visible_from_volume=document["visible_from_volume"],
            visible_to_volume=document["visible_to_volume"],
            evidence_refs=tuple(document["evidence_refs"]),
            identity=document.get("identity"),
            origin=document.get("origin"),
            origin_location_id=document.get("origin_location_id"),
            status_rank=document.get("status_rank"),
            appearance_traits=tuple(document.get("appearance_traits", ())),
            body_traits=tuple(document.get("body_traits", ())),
            core_personality=tuple(document.get("core_personality", ())),
            surface_personality=tuple(document.get("surface_personality", ())),
            hidden_personality=tuple(document.get("hidden_personality", ())),
            interests=tuple(document.get("interests", ())),
            dislikes=tuple(document.get("dislikes", ())),
            weaknesses=tuple(document.get("weaknesses", ())),
            obsessions=tuple(document.get("obsessions", ())),
            habits=tuple(document.get("habits", ())),
            emotional_triggers=tuple(document.get("emotional_triggers", ())),
            decision_logic=document.get("decision_logic"),
            extreme_choice_note=document.get("extreme_choice_note"),
            phase_personality_note=document.get("phase_personality_note"),
        )


@dataclass(frozen=True)
class BehaviorCase:
    """One documented in-text behavior (plan §14-§17)."""

    case_id: str
    character_id: str
    phase_id: str
    phase_name: str
    volume_no: int
    situation_type: str
    context: str
    trigger: str
    available_information: str
    action: str
    verbal_response: str
    emotional_response: str
    goal_at_time: str
    relationship_context: str
    social_context: str
    immediate_outcome: str
    long_term_outcome: str
    tags: tuple[BehaviorTag, ...]
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "character_id": self.character_id,
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "volume_no": self.volume_no,
            "situation_type": self.situation_type,
            "context": self.context,
            "trigger": self.trigger,
            "available_information": self.available_information,
            "action": self.action,
            "verbal_response": self.verbal_response,
            "emotional_response": self.emotional_response,
            "goal_at_time": self.goal_at_time,
            "relationship_context": self.relationship_context,
            "social_context": self.social_context,
            "immediate_outcome": self.immediate_outcome,
            "long_term_outcome": self.long_term_outcome,
            "tags": [tag.value for tag in self.tags],
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> BehaviorCase:
        return cls(
            case_id=document["case_id"],
            character_id=document["character_id"],
            phase_id=document["phase_id"],
            phase_name=document["phase_name"],
            volume_no=document["volume_no"],
            situation_type=document["situation_type"],
            context=document["context"],
            trigger=document["trigger"],
            available_information=document["available_information"],
            action=document["action"],
            verbal_response=document["verbal_response"],
            emotional_response=document["emotional_response"],
            goal_at_time=document["goal_at_time"],
            relationship_context=document["relationship_context"],
            social_context=document["social_context"],
            immediate_outcome=document["immediate_outcome"],
            long_term_outcome=document["long_term_outcome"],
            tags=tuple(BehaviorTag(tag) for tag in document["tags"]),
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class EventPrerequisite:
    """Why a detailed event happens; one condition (plan §25)."""

    prerequisite_id: str
    prerequisite_type: EventPrerequisiteKind
    ref_id: str | None
    statement: str
    evidence_refs: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            "prerequisite_id": self.prerequisite_id,
            "prerequisite_type": self.prerequisite_type.value,
            "ref_id": self.ref_id,
            "statement": self.statement,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> EventPrerequisite:
        return cls(
            prerequisite_id=document["prerequisite_id"],
            prerequisite_type=EventPrerequisiteKind(document["prerequisite_type"]),
            ref_id=document["ref_id"],
            statement=document["statement"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class EventDependency:
    """Causal edge from this event to another (plan §26)."""

    dependency_id: str
    dependency_type: EventDependencyKind
    target_event_id: str
    statement: str

    def to_json(self) -> dict[str, Any]:
        return {
            "dependency_id": self.dependency_id,
            "dependency_type": self.dependency_type.value,
            "target_event_id": self.target_event_id,
            "statement": self.statement,
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> EventDependency:
        return cls(
            dependency_id=document["dependency_id"],
            dependency_type=EventDependencyKind(document["dependency_type"]),
            target_event_id=document["target_event_id"],
            statement=document["statement"],
        )


@dataclass(frozen=True)
class StateChange:
    """One concrete state delta caused by an event (plan §24)."""

    change_id: str
    change_kind: str
    subject_id: str | None
    before: str
    after: str

    def to_json(self) -> dict[str, Any]:
        return {
            "change_id": self.change_id,
            "change_kind": self.change_kind,
            "subject_id": self.subject_id,
            "before": self.before,
            "after": self.after,
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> StateChange:
        return cls(
            change_id=document["change_id"],
            change_kind=document["change_kind"],
            subject_id=document["subject_id"],
            before=document["before"],
            after=document["after"],
        )


@dataclass(frozen=True)
class DetailedEvent:
    """A simulation-relevant event with causality (plan §21-§26).

    World-sim extension (v1.1): world-event model fields — faction
    involvement, long-term / political / world impacts. All new fields
    are optional so historic batches remain valid.
    """

    event_id: str
    event_type: str
    title: str
    timeline_event_id: str | None
    time_date: str | None
    time_precision: DatePrecision
    time_note: str
    volume_no: int
    location_id: str | None
    participants: tuple[str, ...]
    prerequisites: tuple[EventPrerequisite, ...]
    dependencies: tuple[EventDependency, ...]
    state_changes: tuple[StateChange, ...]
    trigger: str
    actions: tuple[str, ...]
    outcome: str
    relationship_change_ids: tuple[str, ...]
    belief_ids: tuple[str, ...]
    canon_importance: EventImportance
    evidence_refs: tuple[str, ...]
    # --- world-event extensions (v1.1, optional) ---
    involved_factions: tuple[str, ...] = ()
    long_term_impacts: tuple[str, ...] = ()
    political_impacts: tuple[str, ...] = ()
    world_impacts: tuple[str, ...] = ()
    participant_actions: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "title": self.title,
            "timeline_event_id": self.timeline_event_id,
            "time_date": self.time_date,
            "time_precision": self.time_precision.value,
            "time_note": self.time_note,
            "volume_no": self.volume_no,
            "location_id": self.location_id,
            "participants": _to_json_array(self.participants),
            "prerequisites": [p.to_json() for p in self.prerequisites],
            "dependencies": [d.to_json() for d in self.dependencies],
            "state_changes": [s.to_json() for s in self.state_changes],
            "trigger": self.trigger,
            "actions": _to_json_array(self.actions),
            "outcome": self.outcome,
            "relationship_change_ids": _to_json_array(self.relationship_change_ids),
            "belief_ids": _to_json_array(self.belief_ids),
            "canon_importance": self.canon_importance.value,
            "evidence_refs": _to_json_array(self.evidence_refs),
            "involved_factions": _to_json_array(self.involved_factions),
            "long_term_impacts": _to_json_array(self.long_term_impacts),
            "political_impacts": _to_json_array(self.political_impacts),
            "world_impacts": _to_json_array(self.world_impacts),
            "participant_actions": _to_json_array(self.participant_actions),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> DetailedEvent:
        return cls(
            event_id=document["event_id"],
            event_type=document["event_type"],
            title=document["title"],
            timeline_event_id=document["timeline_event_id"],
            time_date=document["time_date"],
            time_precision=DatePrecision(document["time_precision"]),
            time_note=document["time_note"],
            volume_no=document["volume_no"],
            location_id=document["location_id"],
            participants=tuple(document["participants"]),
            prerequisites=tuple(
                EventPrerequisite.from_json(entry) for entry in document["prerequisites"]
            ),
            dependencies=tuple(
                EventDependency.from_json(entry) for entry in document["dependencies"]
            ),
            state_changes=tuple(
                StateChange.from_json(entry) for entry in document["state_changes"]
            ),
            trigger=document["trigger"],
            actions=tuple(document["actions"]),
            outcome=document["outcome"],
            relationship_change_ids=tuple(document["relationship_change_ids"]),
            belief_ids=tuple(document["belief_ids"]),
            canon_importance=EventImportance(document["canon_importance"]),
            evidence_refs=tuple(document["evidence_refs"]),
            involved_factions=tuple(document.get("involved_factions", ())),
            long_term_impacts=tuple(document.get("long_term_impacts", ())),
            political_impacts=tuple(document.get("political_impacts", ())),
            world_impacts=tuple(document.get("world_impacts", ())),
            participant_actions=tuple(document.get("participant_actions", ())),
        )


@dataclass(frozen=True)
class ItemDef:
    """A canon item definition (plan §27-§28)."""

    item_id: str
    canonical_name: str
    aliases: tuple[str, ...]
    category: str
    subcategory: str
    description: str
    material: str | None
    size: str | None
    weight: str | None
    durability: str | None
    rarity: str | None
    value_information: str | None
    currency: str | None
    creator: str | None
    origin: str | None
    manufacturer: str | None
    abilities: tuple[str, ...]
    effects: tuple[str, ...]
    requirements: tuple[str, ...]
    limitations: tuple[str, ...]
    first_appearance_volume: int
    first_appearance_line: int
    visible_from_volume: int
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "canonical_name": self.canonical_name,
            "aliases": _to_json_array(self.aliases),
            "category": self.category,
            "subcategory": self.subcategory,
            "description": self.description,
            "material": self.material,
            "size": self.size,
            "weight": self.weight,
            "durability": self.durability,
            "rarity": self.rarity,
            "value_information": self.value_information,
            "currency": self.currency,
            "creator": self.creator,
            "origin": self.origin,
            "manufacturer": self.manufacturer,
            "abilities": _to_json_array(self.abilities),
            "effects": _to_json_array(self.effects),
            "requirements": _to_json_array(self.requirements),
            "limitations": _to_json_array(self.limitations),
            "first_appearance_volume": self.first_appearance_volume,
            "first_appearance_line": self.first_appearance_line,
            "visible_from_volume": self.visible_from_volume,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> ItemDef:
        return cls(
            item_id=document["item_id"],
            canonical_name=document["canonical_name"],
            aliases=tuple(document["aliases"]),
            category=document["category"],
            subcategory=document["subcategory"],
            description=document["description"],
            material=document["material"],
            size=document["size"],
            weight=document["weight"],
            durability=document["durability"],
            rarity=document["rarity"],
            value_information=document["value_information"],
            currency=document["currency"],
            creator=document["creator"],
            origin=document["origin"],
            manufacturer=document["manufacturer"],
            abilities=tuple(document["abilities"]),
            effects=tuple(document["effects"]),
            requirements=tuple(document["requirements"]),
            limitations=tuple(document["limitations"]),
            first_appearance_volume=document["first_appearance_volume"],
            first_appearance_line=document["first_appearance_line"],
            visible_from_volume=document["visible_from_volume"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class OwnershipEntry:
    """One segment of an item instance's ownership history (plan §30)."""

    entry_id: str
    owner_id: str | None
    period_start: str | None
    period_end: str | None
    acquired_via: str
    lost_via: str | None
    note: str

    def to_json(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "owner_id": self.owner_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "acquired_via": self.acquired_via,
            "lost_via": self.lost_via,
            "note": self.note,
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> OwnershipEntry:
        return cls(
            entry_id=document["entry_id"],
            owner_id=document["owner_id"],
            period_start=document["period_start"],
            period_end=document["period_end"],
            acquired_via=document["acquired_via"],
            lost_via=document["lost_via"],
            note=document["note"],
        )


@dataclass(frozen=True)
class ItemInstance:
    """One concrete item in the world (plan §29-§31)."""

    instance_id: str
    definition_id: str
    owner_id: str | None
    holder_id: str | None
    location_id: str | None
    location_name: str | None
    condition: str | None
    durability_if_known: str | None
    acquired_at: str | None
    lost_at: str | None
    acquired_at_volume: int | None
    lost_at_volume: int | None
    ownership_history: tuple[OwnershipEntry, ...]
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "definition_id": self.definition_id,
            "owner_id": self.owner_id,
            "holder_id": self.holder_id,
            "location_id": self.location_id,
            "location_name": self.location_name,
            "condition": self.condition,
            "durability_if_known": self.durability_if_known,
            "acquired_at": self.acquired_at,
            "lost_at": self.lost_at,
            "acquired_at_volume": self.acquired_at_volume,
            "lost_at_volume": self.lost_at_volume,
            "ownership_history": [entry.to_json() for entry in self.ownership_history],
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> ItemInstance:
        return cls(
            instance_id=document["instance_id"],
            definition_id=document["definition_id"],
            owner_id=document["owner_id"],
            holder_id=document["holder_id"],
            location_id=document["location_id"],
            location_name=document["location_name"],
            condition=document["condition"],
            durability_if_known=document["durability_if_known"],
            acquired_at=document["acquired_at"],
            lost_at=document["lost_at"],
            acquired_at_volume=document["acquired_at_volume"],
            lost_at_volume=document["lost_at_volume"],
            ownership_history=tuple(
                OwnershipEntry.from_json(entry) for entry in document["ownership_history"]
            ),
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class AbilityProfile:
    """Canon ability profile; qualitative only (plan §32-§34)."""

    ability_id: str
    name: str
    aliases: tuple[str, ...]
    ability_type: AbilityType
    school: str | None
    element: str | None
    tier: str | None
    requirements: tuple[str, ...]
    preconditions: tuple[str, ...]
    mana_cost_if_known: str | None
    stamina_cost_if_known: str | None
    range_if_known: str | None
    duration_if_known: str | None
    effects: tuple[str, ...]
    limitations: tuple[str, ...]
    counters: tuple[str, ...]
    qualitative_power: str
    learning_method: tuple[str, ...]
    known_users: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "ability_id": self.ability_id,
            "name": self.name,
            "aliases": _to_json_array(self.aliases),
            "ability_type": self.ability_type.value,
            "school": self.school,
            "element": self.element,
            "tier": self.tier,
            "requirements": _to_json_array(self.requirements),
            "preconditions": _to_json_array(self.preconditions),
            "mana_cost_if_known": self.mana_cost_if_known,
            "stamina_cost_if_known": self.stamina_cost_if_known,
            "range_if_known": self.range_if_known,
            "duration_if_known": self.duration_if_known,
            "effects": _to_json_array(self.effects),
            "limitations": _to_json_array(self.limitations),
            "counters": _to_json_array(self.counters),
            "qualitative_power": self.qualitative_power,
            "learning_method": _to_json_array(self.learning_method),
            "known_users": _to_json_array(self.known_users),
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> AbilityProfile:
        return cls(
            ability_id=document["ability_id"],
            name=document["name"],
            aliases=tuple(document["aliases"]),
            ability_type=AbilityType(document["ability_type"]),
            school=document["school"],
            element=document["element"],
            tier=document["tier"],
            requirements=tuple(document["requirements"]),
            preconditions=tuple(document["preconditions"]),
            mana_cost_if_known=document["mana_cost_if_known"],
            stamina_cost_if_known=document["stamina_cost_if_known"],
            range_if_known=document["range_if_known"],
            duration_if_known=document["duration_if_known"],
            effects=tuple(document["effects"]),
            limitations=tuple(document["limitations"]),
            counters=tuple(document["counters"]),
            qualitative_power=document["qualitative_power"],
            learning_method=tuple(document["learning_method"]),
            known_users=tuple(document["known_users"]),
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class PowerComparison:
    """Relative power evidence between two actors (plan §35)."""

    comparison_id: str
    actor_id: str
    target_id: str
    dimension: str
    context: str
    result: str
    confidence: Confidence
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "actor_id": self.actor_id,
            "target_id": self.target_id,
            "dimension": self.dimension,
            "context": self.context,
            "result": self.result,
            "confidence": self.confidence.value,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> PowerComparison:
        return cls(
            comparison_id=document["comparison_id"],
            actor_id=document["actor_id"],
            target_id=document["target_id"],
            dimension=document["dimension"],
            context=document["context"],
            result=document["result"],
            confidence=Confidence(document["confidence"]),
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class WorldRule:
    """One rule of how the world works (plan §44-§46)."""

    rule_id: str
    domain: WorldRuleDomain
    statement: str
    scope: str
    exceptions: str
    confidence: Confidence
    visible_from_volume: int
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "domain": self.domain.value,
            "statement": self.statement,
            "scope": self.scope,
            "exceptions": self.exceptions,
            "confidence": self.confidence.value,
            "visible_from_volume": self.visible_from_volume,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> WorldRule:
        return cls(
            rule_id=document["rule_id"],
            domain=WorldRuleDomain(document["domain"]),
            statement=document["statement"],
            scope=document["scope"],
            exceptions=document["exceptions"],
            confidence=Confidence(document["confidence"]),
            visible_from_volume=document["visible_from_volume"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class LocationProfile:
    """Structured profile of a canon location (plan §38-§39)."""

    location_id: str
    name: str
    aliases: tuple[str, ...]
    location_type: LocationType
    parent_location_id: str | None
    political_control: tuple[str, ...]
    population_info: str | None
    race_distribution: str | None
    climate: str | None
    terrain: str | None
    danger: str | None
    economy: str | None
    services: str | None
    known_routes: tuple[str, ...]
    nearby_locations: tuple[str, ...]
    organizations: tuple[str, ...]
    important_people: tuple[str, ...]
    first_appearance_volume: int
    first_appearance_line: int
    visible_from_volume: int
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "location_id": self.location_id,
            "name": self.name,
            "aliases": _to_json_array(self.aliases),
            "location_type": self.location_type.value,
            "parent_location_id": self.parent_location_id,
            "political_control": _to_json_array(self.political_control),
            "population_info": self.population_info,
            "race_distribution": self.race_distribution,
            "climate": self.climate,
            "terrain": self.terrain,
            "danger": self.danger,
            "economy": self.economy,
            "services": self.services,
            "known_routes": _to_json_array(self.known_routes),
            "nearby_locations": _to_json_array(self.nearby_locations),
            "organizations": _to_json_array(self.organizations),
            "important_people": _to_json_array(self.important_people),
            "first_appearance_volume": self.first_appearance_volume,
            "first_appearance_line": self.first_appearance_line,
            "visible_from_volume": self.visible_from_volume,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> LocationProfile:
        return cls(
            location_id=document["location_id"],
            name=document["name"],
            aliases=tuple(document["aliases"]),
            location_type=LocationType(document["location_type"]),
            parent_location_id=document["parent_location_id"],
            political_control=tuple(document["political_control"]),
            population_info=document["population_info"],
            race_distribution=document["race_distribution"],
            climate=document["climate"],
            terrain=document["terrain"],
            danger=document["danger"],
            economy=document["economy"],
            services=document["services"],
            known_routes=tuple(document["known_routes"]),
            nearby_locations=tuple(document["nearby_locations"]),
            organizations=tuple(document["organizations"]),
            important_people=tuple(document["important_people"]),
            first_appearance_volume=document["first_appearance_volume"],
            first_appearance_line=document["first_appearance_line"],
            visible_from_volume=document["visible_from_volume"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class Route:
    """One canon route between locations (plan §40)."""

    route_id: str
    from_location_id: str
    to_location_id: str
    transport_modes: tuple[str, ...]
    distance_info: str | None
    typical_duration: str | None
    difficulty: str | None
    terrain: str | None
    border_requirements: str | None
    cost_observations: str | None
    hazards: tuple[str, ...]
    seasonality: str | None
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "from_location_id": self.from_location_id,
            "to_location_id": self.to_location_id,
            "transport_modes": _to_json_array(self.transport_modes),
            "distance_info": self.distance_info,
            "typical_duration": self.typical_duration,
            "difficulty": self.difficulty,
            "terrain": self.terrain,
            "border_requirements": self.border_requirements,
            "cost_observations": self.cost_observations,
            "hazards": _to_json_array(self.hazards),
            "seasonality": self.seasonality,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> Route:
        return cls(
            route_id=document["route_id"],
            from_location_id=document["from_location_id"],
            to_location_id=document["to_location_id"],
            transport_modes=tuple(document["transport_modes"]),
            distance_info=document["distance_info"],
            typical_duration=document["typical_duration"],
            difficulty=document["difficulty"],
            terrain=document["terrain"],
            border_requirements=document["border_requirements"],
            cost_observations=document["cost_observations"],
            hazards=tuple(document["hazards"]),
            seasonality=document["seasonality"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class TravelObservation:
    """One actual journey recorded in the text (plan §41)."""

    observation_id: str
    route_id: str
    origin: str
    destination: str
    characters: tuple[str, ...]
    transport: str
    elapsed_time: str
    stops: str | None
    conditions: str | None
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "route_id": self.route_id,
            "origin": self.origin,
            "destination": self.destination,
            "characters": _to_json_array(self.characters),
            "transport": self.transport,
            "elapsed_time": self.elapsed_time,
            "stops": self.stops,
            "conditions": self.conditions,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> TravelObservation:
        return cls(
            observation_id=document["observation_id"],
            route_id=document["route_id"],
            origin=document["origin"],
            destination=document["destination"],
            characters=tuple(document["characters"]),
            transport=document["transport"],
            elapsed_time=document["elapsed_time"],
            stops=document["stops"],
            conditions=document["conditions"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class OrganizationProfile:
    """Structured profile of a canon organization (plan §42)."""

    organization_id: str
    name: str
    org_type: str
    leaders: tuple[str, ...]
    members: tuple[str, ...]
    hierarchy: str | None
    goals: tuple[str, ...]
    rules: tuple[str, ...]
    resources: str | None
    territory: str | None
    alliances: tuple[str, ...]
    enemies: tuple[str, ...]
    reputation: str | None
    visible_from_volume: int
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "name": self.name,
            "org_type": self.org_type,
            "leaders": _to_json_array(self.leaders),
            "members": _to_json_array(self.members),
            "hierarchy": self.hierarchy,
            "goals": _to_json_array(self.goals),
            "rules": _to_json_array(self.rules),
            "resources": self.resources,
            "territory": self.territory,
            "alliances": _to_json_array(self.alliances),
            "enemies": _to_json_array(self.enemies),
            "reputation": self.reputation,
            "visible_from_volume": self.visible_from_volume,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> OrganizationProfile:
        return cls(
            organization_id=document["organization_id"],
            name=document["name"],
            org_type=document["org_type"],
            leaders=tuple(document["leaders"]),
            members=tuple(document["members"]),
            hierarchy=document["hierarchy"],
            goals=tuple(document["goals"]),
            rules=tuple(document["rules"]),
            resources=document["resources"],
            territory=document["territory"],
            alliances=tuple(document["alliances"]),
            enemies=tuple(document["enemies"]),
            reputation=document["reputation"],
            visible_from_volume=document["visible_from_volume"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class PoliticalState:
    """Time-sliced political state of an organization (plan §43)."""

    state_id: str
    organization_id: str
    start_date: str | None
    end_date: str | None
    date_precision: DatePrecision
    ruler: str | None
    alliances: tuple[str, ...]
    conflicts: tuple[str, ...]
    succession: str | None
    political_goals: tuple[str, ...]
    internal_factions: tuple[str, ...]
    visible_from_volume: int
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "state_id": self.state_id,
            "organization_id": self.organization_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "date_precision": self.date_precision.value,
            "ruler": self.ruler,
            "alliances": _to_json_array(self.alliances),
            "conflicts": _to_json_array(self.conflicts),
            "succession": self.succession,
            "political_goals": _to_json_array(self.political_goals),
            "internal_factions": _to_json_array(self.internal_factions),
            "visible_from_volume": self.visible_from_volume,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> PoliticalState:
        return cls(
            state_id=document["state_id"],
            organization_id=document["organization_id"],
            start_date=document["start_date"],
            end_date=document["end_date"],
            date_precision=DatePrecision(document["date_precision"]),
            ruler=document["ruler"],
            alliances=tuple(document["alliances"]),
            conflicts=tuple(document["conflicts"]),
            succession=document["succession"],
            political_goals=tuple(document["political_goals"]),
            internal_factions=tuple(document["internal_factions"]),
            visible_from_volume=document["visible_from_volume"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class SpeciesProfile:
    """Structured profile of a canon species / race (plan §49)."""

    species_id: str
    name: str
    aliases: tuple[str, ...]
    lifespan: str | None
    appearance: str | None
    physiology: str | None
    abilities: tuple[str, ...]
    weaknesses: tuple[str, ...]
    language: str | None
    culture: str | None
    social_structure: str | None
    distribution: str | None
    relations_with_others: str | None
    visible_from_volume: int
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "species_id": self.species_id,
            "name": self.name,
            "aliases": _to_json_array(self.aliases),
            "lifespan": self.lifespan,
            "appearance": self.appearance,
            "physiology": self.physiology,
            "abilities": _to_json_array(self.abilities),
            "weaknesses": _to_json_array(self.weaknesses),
            "language": self.language,
            "culture": self.culture,
            "social_structure": self.social_structure,
            "distribution": self.distribution,
            "relations_with_others": self.relations_with_others,
            "visible_from_volume": self.visible_from_volume,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> SpeciesProfile:
        return cls(
            species_id=document["species_id"],
            name=document["name"],
            aliases=tuple(document["aliases"]),
            lifespan=document["lifespan"],
            appearance=document["appearance"],
            physiology=document["physiology"],
            abilities=tuple(document["abilities"]),
            weaknesses=tuple(document["weaknesses"]),
            language=document["language"],
            culture=document["culture"],
            social_structure=document["social_structure"],
            distribution=document["distribution"],
            relations_with_others=document["relations_with_others"],
            visible_from_volume=document["visible_from_volume"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class CreatureProfile:
    """Structured profile of a canon monster / creature (plan §50)."""

    creature_id: str
    name: str
    aliases: tuple[str, ...]
    habitat: str | None
    behavior: str | None
    danger: str | None
    abilities: tuple[str, ...]
    weaknesses: tuple[str, ...]
    social_behavior: str | None
    uses: tuple[str, ...]
    known_encounters: tuple[str, ...]
    visible_from_volume: int
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "creature_id": self.creature_id,
            "name": self.name,
            "aliases": _to_json_array(self.aliases),
            "habitat": self.habitat,
            "behavior": self.behavior,
            "danger": self.danger,
            "abilities": _to_json_array(self.abilities),
            "weaknesses": _to_json_array(self.weaknesses),
            "social_behavior": self.social_behavior,
            "uses": _to_json_array(self.uses),
            "known_encounters": _to_json_array(self.known_encounters),
            "visible_from_volume": self.visible_from_volume,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> CreatureProfile:
        return cls(
            creature_id=document["creature_id"],
            name=document["name"],
            aliases=tuple(document["aliases"]),
            habitat=document["habitat"],
            behavior=document["behavior"],
            danger=document["danger"],
            abilities=tuple(document["abilities"]),
            weaknesses=tuple(document["weaknesses"]),
            social_behavior=document["social_behavior"],
            uses=tuple(document["uses"]),
            known_encounters=tuple(document["known_encounters"]),
            visible_from_volume=document["visible_from_volume"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class Belief:
    """A character's belief about a claim (plan §51-§53, §59)."""

    belief_id: str
    owner_id: str
    topic: str
    statement: str
    certainty: Confidence
    belief_state: BeliefState
    learned_from: str | None
    learned_at_volume: int | None
    learned_method: str | None
    is_true_in_world: bool | None
    visible_from_volume: int
    visible_to_volume: int | None
    note: str
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "belief_id": self.belief_id,
            "owner_id": self.owner_id,
            "topic": self.topic,
            "statement": self.statement,
            "certainty": self.certainty.value,
            "belief_state": self.belief_state.value,
            "learned_from": self.learned_from,
            "learned_at_volume": self.learned_at_volume,
            "learned_method": self.learned_method,
            "is_true_in_world": self.is_true_in_world,
            "visible_from_volume": self.visible_from_volume,
            "visible_to_volume": self.visible_to_volume,
            "note": self.note,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> Belief:
        return cls(
            belief_id=document["belief_id"],
            owner_id=document["owner_id"],
            topic=document["topic"],
            statement=document["statement"],
            certainty=Confidence(document["certainty"]),
            belief_state=BeliefState(document["belief_state"]),
            learned_from=document["learned_from"],
            learned_at_volume=document["learned_at_volume"],
            learned_method=document["learned_method"],
            is_true_in_world=document["is_true_in_world"],
            visible_from_volume=document["visible_from_volume"],
            visible_to_volume=document["visible_to_volume"],
            note=document["note"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class EconomicObservation:
    """One canon price / wage / cost observation (plan §47-§48)."""

    observation_id: str
    location_id: str | None
    location_name: str | None
    at_date: str | None
    at_volume: int
    category: str
    item_id: str | None
    goods_description: str
    quantity: str | None
    currency: str | None
    amount_description: str | None
    price_class: PriceClass
    context: str
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "location_id": self.location_id,
            "location_name": self.location_name,
            "at_date": self.at_date,
            "at_volume": self.at_volume,
            "category": self.category,
            "item_id": self.item_id,
            "goods_description": self.goods_description,
            "quantity": self.quantity,
            "currency": self.currency,
            "amount_description": self.amount_description,
            "price_class": self.price_class.value,
            "context": self.context,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> EconomicObservation:
        return cls(
            observation_id=document["observation_id"],
            location_id=document["location_id"],
            location_name=document["location_name"],
            at_date=document["at_date"],
            at_volume=document["at_volume"],
            category=document["category"],
            item_id=document["item_id"],
            goods_description=document["goods_description"],
            quantity=document["quantity"],
            currency=document["currency"],
            amount_description=document["amount_description"],
            price_class=PriceClass(document["price_class"]),
            context=document["context"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class RelationshipChange:
    """One dimension-level relationship shift (plan §54)."""

    change_id: str
    source_id: str
    target_id: str
    dimension: str
    before: str
    trigger: str
    after: str
    at_volume: int
    at_date: str | None
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "change_id": self.change_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "dimension": self.dimension,
            "before": self.before,
            "trigger": self.trigger,
            "after": self.after,
            "at_volume": self.at_volume,
            "at_date": self.at_date,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> RelationshipChange:
        return cls(
            change_id=document["change_id"],
            source_id=document["source_id"],
            target_id=document["target_id"],
            dimension=document["dimension"],
            before=document["before"],
            trigger=document["trigger"],
            after=document["after"],
            at_volume=document["at_volume"],
            at_date=document["at_date"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class SpeechProfile:
    """Extracted speech patterns, not verbatim quotes (plan §55-§56)."""

    profile_id: str
    character_id: str
    phase_id: str
    phase_name: str
    politeness: str
    sentence_length: str
    address_habits: str
    emotion_expression: str
    anger_expression: str
    shy_expression: str
    intimate_speech: str
    stranger_speech: str
    superior_speech: str
    inferior_speech: str
    canonical_examples: tuple[str, ...]
    visible_from_volume: int
    evidence_refs: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "character_id": self.character_id,
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "politeness": self.politeness,
            "sentence_length": self.sentence_length,
            "address_habits": self.address_habits,
            "emotion_expression": self.emotion_expression,
            "anger_expression": self.anger_expression,
            "shy_expression": self.shy_expression,
            "intimate_speech": self.intimate_speech,
            "stranger_speech": self.stranger_speech,
            "superior_speech": self.superior_speech,
            "inferior_speech": self.inferior_speech,
            "canonical_examples": _to_json_array(self.canonical_examples),
            "visible_from_volume": self.visible_from_volume,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> SpeechProfile:
        return cls(
            profile_id=document["profile_id"],
            character_id=document["character_id"],
            phase_id=document["phase_id"],
            phase_name=document["phase_name"],
            politeness=document["politeness"],
            sentence_length=document["sentence_length"],
            address_habits=document["address_habits"],
            emotion_expression=document["emotion_expression"],
            anger_expression=document["anger_expression"],
            shy_expression=document["shy_expression"],
            intimate_speech=document["intimate_speech"],
            stranger_speech=document["stranger_speech"],
            superior_speech=document["superior_speech"],
            inferior_speech=document["inferior_speech"],
            canonical_examples=tuple(document["canonical_examples"]),
            visible_from_volume=document["visible_from_volume"],
            evidence_refs=tuple(document["evidence_refs"]),
        )


@dataclass(frozen=True)
class CharacterQuirk:
    """One observable habit / quirk / private behavior (Gold Standard §4).

    Captures high-identify idiosyncrasies that distinguish a character
    in GM simulation: fetishes, collections, tics, speech habits,
    public/private contrast, etc. Every quirk is evidence-bound.
    """

    quirk_id: str
    character_id: str
    phase_id: str
    category: str
    name: str
    description: str
    intensity: str | None = None
    frequency: str | None = None
    triggers: tuple[str, ...] = ()
    preferred_targets: tuple[str, ...] = ()
    avoided_targets: tuple[str, ...] = ()
    public_expression: str | None = None
    private_expression: str | None = None
    behavior_patterns: tuple[str, ...] = ()
    verbal_patterns: tuple[str, ...] = ()
    body_language: str | None = None
    emotional_reward: str | None = None
    emotional_response: str | None = None
    boundaries: tuple[str, ...] = ()
    exceptions: tuple[str, ...] = ()
    start_date: str | None = None
    end_date: str | None = None
    visible_from_volume: int = 1
    visible_to_volume: int | None = None
    evidence_type: EvidenceType = EvidenceType.CANON_EXPLICIT
    confidence: Confidence = Confidence.EXPLICIT
    evidence_refs: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            "quirk_id": self.quirk_id,
            "character_id": self.character_id,
            "phase_id": self.phase_id,
            "category": self.category,
            "name": self.name,
            "description": self.description,
            "intensity": self.intensity,
            "frequency": self.frequency,
            "triggers": _to_json_array(self.triggers),
            "preferred_targets": _to_json_array(self.preferred_targets),
            "avoided_targets": _to_json_array(self.avoided_targets),
            "public_expression": self.public_expression,
            "private_expression": self.private_expression,
            "behavior_patterns": _to_json_array(self.behavior_patterns),
            "verbal_patterns": _to_json_array(self.verbal_patterns),
            "body_language": self.body_language,
            "emotional_reward": self.emotional_reward,
            "emotional_response": self.emotional_response,
            "boundaries": _to_json_array(self.boundaries),
            "exceptions": _to_json_array(self.exceptions),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "visible_from_volume": self.visible_from_volume,
            "visible_to_volume": self.visible_to_volume,
            "evidence_type": self.evidence_type.value,
            "confidence": self.confidence.value,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> CharacterQuirk:
        return cls(
            quirk_id=document["quirk_id"],
            character_id=document["character_id"],
            phase_id=document["phase_id"],
            category=document["category"],
            name=document["name"],
            description=document["description"],
            intensity=document.get("intensity"),
            frequency=document.get("frequency"),
            triggers=tuple(document.get("triggers", ())),
            preferred_targets=tuple(document.get("preferred_targets", ())),
            avoided_targets=tuple(document.get("avoided_targets", ())),
            public_expression=document.get("public_expression"),
            private_expression=document.get("private_expression"),
            behavior_patterns=tuple(document.get("behavior_patterns", ())),
            verbal_patterns=tuple(document.get("verbal_patterns", ())),
            body_language=document.get("body_language"),
            emotional_reward=document.get("emotional_reward"),
            emotional_response=document.get("emotional_response"),
            boundaries=tuple(document.get("boundaries", ())),
            exceptions=tuple(document.get("exceptions", ())),
            start_date=document.get("start_date"),
            end_date=document.get("end_date"),
            visible_from_volume=document.get("visible_from_volume", 1),
            visible_to_volume=document.get("visible_to_volume"),
            evidence_type=EvidenceType(document.get("evidence_type", "CANON_EXPLICIT")),
            confidence=Confidence(document.get("confidence", "EXPLICIT")),
            evidence_refs=tuple(document.get("evidence_refs", ())),
        )


@dataclass(frozen=True)
class CharacterPreference:
    """One concrete like / dislike / attraction / aversion (Gold Standard §8)."""

    preference_id: str
    character_id: str
    phase_id: str
    preference_type: str
    target: str
    description: str
    intensity: str | None = None
    context: str | None = None
    visible_from_volume: int = 1
    visible_to_volume: int | None = None
    evidence_type: EvidenceType = EvidenceType.CANON_EXPLICIT
    confidence: Confidence = Confidence.EXPLICIT
    evidence_refs: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            "preference_id": self.preference_id,
            "character_id": self.character_id,
            "phase_id": self.phase_id,
            "preference_type": self.preference_type,
            "target": self.target,
            "description": self.description,
            "intensity": self.intensity,
            "context": self.context,
            "visible_from_volume": self.visible_from_volume,
            "visible_to_volume": self.visible_to_volume,
            "evidence_type": self.evidence_type.value,
            "confidence": self.confidence.value,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> CharacterPreference:
        return cls(
            preference_id=document["preference_id"],
            character_id=document["character_id"],
            phase_id=document["phase_id"],
            preference_type=document["preference_type"],
            target=document["target"],
            description=document["description"],
            intensity=document.get("intensity"),
            context=document.get("context"),
            visible_from_volume=document.get("visible_from_volume", 1),
            visible_to_volume=document.get("visible_to_volume"),
            evidence_type=EvidenceType(document.get("evidence_type", "CANON_EXPLICIT")),
            confidence=Confidence(document.get("confidence", "EXPLICIT")),
            evidence_refs=tuple(document.get("evidence_refs", ())),
        )


@dataclass(frozen=True)
class BodyLanguageProfile:
    """Observable physical tells per emotion (Gold Standard §14)."""

    profile_id: str
    character_id: str
    phase_id: str
    phase_name: str
    happy_signs: tuple[str, ...] = ()
    angry_signs: tuple[str, ...] = ()
    nervous_signs: tuple[str, ...] = ()
    embarrassed_signs: tuple[str, ...] = ()
    lying_signs: tuple[str, ...] = ()
    fear_signs: tuple[str, ...] = ()
    thinking_signs: tuple[str, ...] = ()
    affection_signs: tuple[str, ...] = ()
    hostility_signs: tuple[str, ...] = ()
    visible_from_volume: int = 1
    visible_to_volume: int | None = None
    evidence_refs: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "character_id": self.character_id,
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "happy_signs": _to_json_array(self.happy_signs),
            "angry_signs": _to_json_array(self.angry_signs),
            "nervous_signs": _to_json_array(self.nervous_signs),
            "embarrassed_signs": _to_json_array(self.embarrassed_signs),
            "lying_signs": _to_json_array(self.lying_signs),
            "fear_signs": _to_json_array(self.fear_signs),
            "thinking_signs": _to_json_array(self.thinking_signs),
            "affection_signs": _to_json_array(self.affection_signs),
            "hostility_signs": _to_json_array(self.hostility_signs),
            "visible_from_volume": self.visible_from_volume,
            "visible_to_volume": self.visible_to_volume,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> BodyLanguageProfile:
        return cls(
            profile_id=document["profile_id"],
            character_id=document["character_id"],
            phase_id=document["phase_id"],
            phase_name=document["phase_name"],
            happy_signs=tuple(document.get("happy_signs", ())),
            angry_signs=tuple(document.get("angry_signs", ())),
            nervous_signs=tuple(document.get("nervous_signs", ())),
            embarrassed_signs=tuple(document.get("embarrassed_signs", ())),
            lying_signs=tuple(document.get("lying_signs", ())),
            fear_signs=tuple(document.get("fear_signs", ())),
            thinking_signs=tuple(document.get("thinking_signs", ())),
            affection_signs=tuple(document.get("affection_signs", ())),
            hostility_signs=tuple(document.get("hostility_signs", ())),
            visible_from_volume=document.get("visible_from_volume", 1),
            visible_to_volume=document.get("visible_to_volume"),
            evidence_refs=tuple(document.get("evidence_refs", ())),
        )


@dataclass(frozen=True)
class CharacterPersona:
    """Public / private / relational persona variant (Gold Standard §7)."""

    persona_id: str
    character_id: str
    phase_id: str
    persona_type: str
    description: str
    speech_style: str | None = None
    behavior_traits: tuple[str, ...] = ()
    visible_from_volume: int = 1
    visible_to_volume: int | None = None
    evidence_refs: tuple[str, ...] = ()

    def to_json(self) -> dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "character_id": self.character_id,
            "phase_id": self.phase_id,
            "persona_type": self.persona_type,
            "description": self.description,
            "speech_style": self.speech_style,
            "behavior_traits": _to_json_array(self.behavior_traits),
            "visible_from_volume": self.visible_from_volume,
            "visible_to_volume": self.visible_to_volume,
            "evidence_refs": _to_json_array(self.evidence_refs),
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> CharacterPersona:
        return cls(
            persona_id=document["persona_id"],
            character_id=document["character_id"],
            phase_id=document["phase_id"],
            persona_type=document["persona_type"],
            description=document["description"],
            speech_style=document.get("speech_style"),
            behavior_traits=tuple(document.get("behavior_traits", ())),
            visible_from_volume=document.get("visible_from_volume", 1),
            visible_to_volume=document.get("visible_to_volume"),
            evidence_refs=tuple(document.get("evidence_refs", ())),
        )


@dataclass(frozen=True)
class CanonConflict:
    """An apparent contradiction between two canon claims (plan §74)."""

    conflict_id: str
    claim_a: str
    claim_b: str
    evidence_a_refs: tuple[str, ...]
    evidence_b_refs: tuple[str, ...]
    possible_resolution: str
    status: ConflictStatus
    note: str

    def to_json(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "claim_a": self.claim_a,
            "claim_b": self.claim_b,
            "evidence_a_refs": _to_json_array(self.evidence_a_refs),
            "evidence_b_refs": _to_json_array(self.evidence_b_refs),
            "possible_resolution": self.possible_resolution,
            "status": self.status.value,
            "note": self.note,
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> CanonConflict:
        return cls(
            conflict_id=document["conflict_id"],
            claim_a=document["claim_a"],
            claim_b=document["claim_b"],
            evidence_a_refs=tuple(document["evidence_a_refs"]),
            evidence_b_refs=tuple(document["evidence_b_refs"]),
            possible_resolution=document["possible_resolution"],
            status=ConflictStatus(document["status"]),
            note=document["note"],
        )


@dataclass(frozen=True)
class CanonGap:
    """A question the source does not answer (plan §95-§97)."""

    gap_id: str
    domain: str
    question: str
    why_needed: str
    searched_volumes: tuple[int, ...]
    status: GapStatus
    possible_sources: str
    note: str

    def to_json(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "domain": self.domain,
            "question": self.question,
            "why_needed": self.why_needed,
            "searched_volumes": list(self.searched_volumes),
            "status": self.status.value,
            "possible_sources": self.possible_sources,
            "note": self.note,
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> CanonGap:
        return cls(
            gap_id=document["gap_id"],
            domain=document["domain"],
            question=document["question"],
            why_needed=document["why_needed"],
            searched_volumes=tuple(document["searched_volumes"]),
            status=GapStatus(document["status"]),
            possible_sources=document["possible_sources"],
            note=document["note"],
        )


@dataclass(frozen=True)
class EnrichmentBatch:
    """One verified per-volume enrichment batch."""

    batch_id: str
    source_volume: int
    source_unit_ids: tuple[str, ...]
    schema_version: str
    evidence: tuple[EvidenceRef, ...]
    character_profiles: tuple[CharacterProfile, ...]
    behavior_cases: tuple[BehaviorCase, ...]
    detailed_events: tuple[DetailedEvent, ...]
    items: tuple[ItemDef, ...]
    item_instances: tuple[ItemInstance, ...]
    abilities: tuple[AbilityProfile, ...]
    power_comparisons: tuple[PowerComparison, ...]
    world_rules: tuple[WorldRule, ...]
    locations: tuple[LocationProfile, ...]
    routes: tuple[Route, ...]
    travel_observations: tuple[TravelObservation, ...]
    organizations: tuple[OrganizationProfile, ...]
    political_states: tuple[PoliticalState, ...]
    species: tuple[SpeciesProfile, ...]
    creatures: tuple[CreatureProfile, ...]
    beliefs: tuple[Belief, ...]
    economic_observations: tuple[EconomicObservation, ...]
    relationship_changes: tuple[RelationshipChange, ...]
    speech_profiles: tuple[SpeechProfile, ...]
    character_quirks: tuple[CharacterQuirk, ...] = ()
    character_preferences: tuple[CharacterPreference, ...] = ()
    body_language_profiles: tuple[BodyLanguageProfile, ...] = ()
    character_personas: tuple[CharacterPersona, ...] = ()
    canon_conflicts: tuple[CanonConflict, ...] = ()
    canon_gaps: tuple[CanonGap, ...] = ()

    ENRICHMENT_SCHEMA_VERSION: ClassVar[str] = "1.0.0"

    def to_json(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "source_volume": self.source_volume,
            "source_unit_ids": list(self.source_unit_ids),
            "schema_version": self.schema_version,
            "evidence": [e.to_json() for e in self.evidence],
            "character_profiles": [e.to_json() for e in self.character_profiles],
            "behavior_cases": [e.to_json() for e in self.behavior_cases],
            "detailed_events": [e.to_json() for e in self.detailed_events],
            "items": [e.to_json() for e in self.items],
            "item_instances": [e.to_json() for e in self.item_instances],
            "abilities": [e.to_json() for e in self.abilities],
            "power_comparisons": [e.to_json() for e in self.power_comparisons],
            "world_rules": [e.to_json() for e in self.world_rules],
            "locations": [e.to_json() for e in self.locations],
            "routes": [e.to_json() for e in self.routes],
            "travel_observations": [e.to_json() for e in self.travel_observations],
            "organizations": [e.to_json() for e in self.organizations],
            "political_states": [e.to_json() for e in self.political_states],
            "species": [e.to_json() for e in self.species],
            "creatures": [e.to_json() for e in self.creatures],
            "beliefs": [e.to_json() for e in self.beliefs],
            "economic_observations": [e.to_json() for e in self.economic_observations],
            "relationship_changes": [e.to_json() for e in self.relationship_changes],
            "speech_profiles": [e.to_json() for e in self.speech_profiles],
            "character_quirks": [e.to_json() for e in self.character_quirks],
            "character_preferences": [e.to_json() for e in self.character_preferences],
            "body_language_profiles": [e.to_json() for e in self.body_language_profiles],
            "character_personas": [e.to_json() for e in self.character_personas],
            "canon_conflicts": [e.to_json() for e in self.canon_conflicts],
            "canon_gaps": [e.to_json() for e in self.canon_gaps],
        }

    @classmethod
    def from_json(cls, document: dict[str, Any]) -> EnrichmentBatch:
        return cls(
            batch_id=document["batch_id"],
            source_volume=document["source_volume"],
            source_unit_ids=tuple(document["source_unit_ids"]),
            schema_version=document["schema_version"],
            evidence=tuple(EvidenceRef.from_json(entry) for entry in document["evidence"]),
            character_profiles=tuple(
                CharacterProfile.from_json(entry) for entry in document["character_profiles"]
            ),
            behavior_cases=tuple(
                BehaviorCase.from_json(entry) for entry in document["behavior_cases"]
            ),
            detailed_events=tuple(
                DetailedEvent.from_json(entry) for entry in document["detailed_events"]
            ),
            items=tuple(ItemDef.from_json(entry) for entry in document["items"]),
            item_instances=tuple(
                ItemInstance.from_json(entry) for entry in document["item_instances"]
            ),
            abilities=tuple(AbilityProfile.from_json(entry) for entry in document["abilities"]),
            power_comparisons=tuple(
                PowerComparison.from_json(entry) for entry in document["power_comparisons"]
            ),
            world_rules=tuple(WorldRule.from_json(entry) for entry in document["world_rules"]),
            locations=tuple(LocationProfile.from_json(entry) for entry in document["locations"]),
            routes=tuple(Route.from_json(entry) for entry in document["routes"]),
            travel_observations=tuple(
                TravelObservation.from_json(entry) for entry in document["travel_observations"]
            ),
            organizations=tuple(
                OrganizationProfile.from_json(entry) for entry in document["organizations"]
            ),
            political_states=tuple(
                PoliticalState.from_json(entry) for entry in document["political_states"]
            ),
            species=tuple(SpeciesProfile.from_json(entry) for entry in document["species"]),
            creatures=tuple(CreatureProfile.from_json(entry) for entry in document["creatures"]),
            beliefs=tuple(Belief.from_json(entry) for entry in document["beliefs"]),
            economic_observations=tuple(
                EconomicObservation.from_json(entry) for entry in document["economic_observations"]
            ),
            relationship_changes=tuple(
                RelationshipChange.from_json(entry) for entry in document["relationship_changes"]
            ),
            speech_profiles=tuple(
                SpeechProfile.from_json(entry) for entry in document["speech_profiles"]
            ),
            character_quirks=tuple(
                CharacterQuirk.from_json(entry) for entry in document.get("character_quirks", ())
            ),
            character_preferences=tuple(
                CharacterPreference.from_json(entry)
                for entry in document.get("character_preferences", ())
            ),
            body_language_profiles=tuple(
                BodyLanguageProfile.from_json(entry)
                for entry in document.get("body_language_profiles", ())
            ),
            character_personas=tuple(
                CharacterPersona.from_json(entry)
                for entry in document.get("character_personas", ())
            ),
            canon_conflicts=tuple(
                CanonConflict.from_json(entry) for entry in document.get("canon_conflicts", ())
            ),
            canon_gaps=tuple(CanonGap.from_json(entry) for entry in document.get("canon_gaps", ())),
        )

    def counts(self) -> dict[str, int]:
        return {
            "evidence": len(self.evidence),
            "character_profiles": len(self.character_profiles),
            "behavior_cases": len(self.behavior_cases),
            "detailed_events": len(self.detailed_events),
            "items": len(self.items),
            "item_instances": len(self.item_instances),
            "abilities": len(self.abilities),
            "power_comparisons": len(self.power_comparisons),
            "world_rules": len(self.world_rules),
            "locations": len(self.locations),
            "routes": len(self.routes),
            "travel_observations": len(self.travel_observations),
            "organizations": len(self.organizations),
            "political_states": len(self.political_states),
            "species": len(self.species),
            "creatures": len(self.creatures),
            "beliefs": len(self.beliefs),
            "economic_observations": len(self.economic_observations),
            "relationship_changes": len(self.relationship_changes),
            "speech_profiles": len(self.speech_profiles),
            "character_quirks": len(self.character_quirks),
            "character_preferences": len(self.character_preferences),
            "body_language_profiles": len(self.body_language_profiles),
            "character_personas": len(self.character_personas),
            "canon_conflicts": len(self.canon_conflicts),
            "canon_gaps": len(self.canon_gaps),
        }
