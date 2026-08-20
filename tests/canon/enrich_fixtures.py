"""Shared fixtures for enrichment-layer tests.

The corpus is small but structured so evidence line ranges resolve against
real parsed units. The registry mirrors the extraction-layer shape so the
enrichment verifier can resolve entity references.
"""

from __future__ import annotations

from pathlib import Path

from overlord_worldsim.canon.enrich_model import (
    AbilityProfile,
    AbilityType,
    BehaviorCase,
    BehaviorTag,
    Belief,
    BeliefState,
    CanonConflict,
    CanonGap,
    CharacterProfile,
    Confidence,
    ConflictStatus,
    CreatureProfile,
    DatePrecision,
    DetailedEvent,
    EconomicObservation,
    EnrichmentBatch,
    EventDependency,
    EventDependencyKind,
    EventImportance,
    EventPrerequisite,
    EventPrerequisiteKind,
    EvidenceRef,
    EvidenceType,
    GapStatus,
    ItemDef,
    ItemInstance,
    LocationProfile,
    LocationType,
    OrganizationProfile,
    OwnershipEntry,
    PoliticalState,
    PowerComparison,
    PriceClass,
    RelationshipChange,
    Route,
    SpeciesProfile,
    SpeechProfile,
    StateChange,
    TravelObservation,
    WorldRule,
    WorldRuleDomain,
)
from overlord_worldsim.canon.enrich_registry import EntityRegistry
from overlord_worldsim.canon.extract_model import (
    Entity,
    EntityKind,
    Relationship,
    TimelineEvent,
)
from overlord_worldsim.canon.parse import parse_source

CORPUS = (
    "第一卷 幼年期 序章\n"
    "\n"
    "    希露菲的头发是银色的。\n"
    "\n"
    "第一卷 幼年期 第一话「测试章节」\n"
    "\n"
    "    保罗是鲁迪乌斯的父亲。\n"
    "\n"
    "    鲁迪乌斯四岁。\n"
    "\n"
    "    鲁迪乌斯学会了火魔术。\n"
    "\n"
    "第一卷 幼年期 第二话「搬家」\n"
    "\n"
    "    一家搬往布埃纳村。\n"
    "\n"
    "    鲁迪乌斯离家前往魔大陆。\n"
)

DOC = parse_source(CORPUS, source_name="corpus.txt")


def _entity(entity_id: str, name: str, kind: EntityKind, line: int) -> Entity:
    return Entity(
        entity_id=entity_id,
        name=name,
        aliases=(),
        kind=kind,
        introduced_volume=1,
        introduced_line=line,
        description="测试实体。",
    )


ENTITIES = (
    _entity("E0001", "鲁迪乌斯", EntityKind.CHARACTER, 3),
    _entity("E0002", "保罗", EntityKind.CHARACTER, 7),
    _entity("E0003", "布埃纳村", EntityKind.LOCATION, 15),
    _entity("E0004", "魔大陆", EntityKind.LOCATION, 17),
    _entity("E0005", "冒险者公会", EntityKind.ORGANIZATION, 15),
    _entity("E0006", "火之魔剑", EntityKind.ITEM, 11),
)

TIMELINE_EVENTS = (
    TimelineEvent(
        event_id="T0001",
        title="搬家",
        description="一家搬往布埃纳村。",
        date=None,
        date_precision=DatePrecision.UNKNOWN,
        participants=("E0001", "E0002"),
        evidence_volumes=(1,),
        evidence_lines=((15, 15),),
    ),
)

RELATIONSHIPS = (
    Relationship(
        relationship_id="R0001",
        source_id="E0002",
        target_id="E0001",
        rel_type="父子",
        evidence_volumes=(1,),
        evidence_lines=((7, 7),),
        confidence=Confidence.EXPLICIT,
        visible_from_volume=1,
    ),
)

REGISTRY = EntityRegistry(
    entities=ENTITIES,
    timeline_events=TIMELINE_EVENTS,
    relationships=RELATIONSHIPS,
)


def evidence(
    evidence_id: str, *, line_start: int, line_end: int, unit: str = "U0002"
) -> EvidenceRef:
    return EvidenceRef(
        evidence_id=evidence_id,
        volume_no=1,
        unit_id=unit,
        chapter_title="第一话「测试章节」",
        source_start_line=line_start,
        source_end_line=line_end,
        evidence_type=EvidenceType.CANON_EXPLICIT,
        confidence=Confidence.EXPLICIT,
        note="测试证据。",
    )


def make_profile(profile_id: str = "CP0001") -> CharacterProfile:
    return CharacterProfile(
        profile_id=profile_id,
        character_id="E0001",
        phase_id="childhood",
        phase_name="幼年期",
        start_date=None,
        end_date=None,
        date_precision=DatePrecision.UNKNOWN,
        age_description="约四岁",
        personality_traits=("认真", "好学"),
        values=("家族",),
        desires=("掌握魔术",),
        fears=("父母失望",),
        taboos=(),
        insecurities=("前世的记忆",),
        pride=None,
        impulsiveness="MODERATE",
        patience="HIGH",
        risk_tolerance="LOW",
        self_control="HIGH",
        attachment_style="安全型",
        authority_attitude="顺从",
        family_attitude="重视",
        romantic_attitude="UNKNOWN",
        violence_attitude="回避",
        money_attitude=None,
        status_attitude=None,
        race_attitude=None,
        religious_attitude=None,
        loyalty="HIGH",
        ambition="MODERATE",
        short_term_goals=("学会更多魔术",),
        long_term_goals=("平稳生活",),
        obligations=("家事",),
        decision_tendencies=("先观察再行动",),
        speech_tendencies=("礼貌",),
        social_tendencies=("避免与同龄人冲突",),
        conflict_tendencies=("避免正面冲突",),
        known_skills=("火魔术",),
        knowledge_state=("知道父母是冒险者",),
        relationship_tendencies=("亲近父母",),
        behavior_changes_note="",
        summary="测试用幼年期人格。",
        visible_from_volume=1,
        visible_to_volume=None,
        evidence_refs=("EV0001",),
    )


def make_case(case_id: str = "BC0001") -> BehaviorCase:
    return BehaviorCase(
        case_id=case_id,
        character_id="E0001",
        phase_id="childhood",
        phase_name="幼年期",
        volume_no=1,
        situation_type="学习魔术",
        context="鲁迪乌斯在家中学习火魔术。",
        trigger="第一次咏唱失败",
        available_information="知道魔力咒文",
        action="反复练习直到成功",
        verbal_response="再试一次。",
        emotional_response="平静",
        goal_at_time="学会火魔术",
        relationship_context="独自一人",
        social_context="家中",
        immediate_outcome="成功释放火魔术",
        long_term_outcome="魔术能力提升",
        tags=(BehaviorTag.TEACHING, BehaviorTag.TRAINING),
        evidence_refs=("EV0002",),
    )


def make_event(event_id: str = "DE0001") -> DetailedEvent:
    seq = event_id.removeprefix("DE")
    return DetailedEvent(
        event_id=event_id,
        event_type="移动",
        title="搬家",
        timeline_event_id="T0001",
        time_date=None,
        time_precision=DatePrecision.UNKNOWN,
        time_note="幼年期",
        volume_no=1,
        location_id="E0003",
        participants=("E0001", "E0002"),
        prerequisites=(
            EventPrerequisite(
                prerequisite_id=f"EP{seq}01",
                prerequisite_type=EventPrerequisiteKind.PERSON_ALIVE,
                ref_id="E0001",
                statement="鲁迪乌斯出生且存活",
            ),
        ),
        dependencies=(
            EventDependency(
                dependency_id=f"ED{seq}01",
                dependency_type=EventDependencyKind.ENABLES,
                target_event_id="DE0002",
                statement="搬家后鲁迪乌斯得以前往魔大陆",
            ),
        ),
        state_changes=(
            StateChange(
                change_id=f"SC{seq}01",
                change_kind="LOCATION",
                subject_id="E0001",
                before="原住地",
                after="布埃纳村",
            ),
        ),
        trigger="家庭决定搬往布埃纳村",
        actions=("出发", "抵达"),
        outcome="一家定居布埃纳村",
        relationship_change_ids=(),
        belief_ids=(),
        canon_importance=EventImportance.MAJOR,
        evidence_refs=("EV0003",),
    )


def make_item(item_id: str = "IT0001") -> ItemDef:
    return ItemDef(
        item_id=item_id,
        canonical_name="火之魔剑",
        aliases=("魔剑",),
        category="武器",
        subcategory="剑",
        description="能喷出火焰的剑。",
        material=None,
        size=None,
        weight=None,
        durability=None,
        rarity=None,
        value_information=None,
        currency=None,
        creator=None,
        origin=None,
        manufacturer=None,
        abilities=("火焰附加",),
        effects=("攻击附带火焰",),
        requirements=(),
        limitations=("需要魔力",),
        first_appearance_volume=1,
        first_appearance_line=11,
        visible_from_volume=1,
        evidence_refs=("EV0004",),
    )


def make_instance(instance_id: str = "IN0001") -> ItemInstance:
    return ItemInstance(
        instance_id=instance_id,
        definition_id="IT0001",
        owner_id="E0001",
        holder_id="E0001",
        location_id="E0003",
        location_name="布埃纳村",
        condition="完好",
        durability_if_known=None,
        acquired_at=None,
        lost_at=None,
        acquired_at_volume=1,
        lost_at_volume=None,
        ownership_history=(
            OwnershipEntry(
                entry_id="OH0001",
                owner_id="E0001",
                period_start=None,
                period_end=None,
                acquired_via="获得",
                lost_via=None,
                note="测试持有。",
            ),
        ),
        evidence_refs=("EV0004",),
    )


def make_ability(ability_id: str = "AB0001") -> AbilityProfile:
    return AbilityProfile(
        ability_id=ability_id,
        name="火魔术",
        aliases=(),
        ability_type=AbilityType.MAGIC,
        school="魔术",
        element="火",
        tier="初等",
        requirements=(),
        preconditions=(),
        mana_cost_if_known=None,
        stamina_cost_if_known=None,
        range_if_known=None,
        duration_if_known=None,
        effects=("释放火焰",),
        limitations=(),
        counters=(),
        qualitative_power="幼童可学的入门魔术",
        learning_method=("咏唱", "练习"),
        known_users=("E0001",),
        evidence_refs=("EV0002",),
    )


def make_comparison(comparison_id: str = "PC0001") -> PowerComparison:
    return PowerComparison(
        comparison_id=comparison_id,
        actor_id="E0001",
        target_id="E0002",
        dimension="魔术",
        context="父子对练",
        result="鲁迪乌斯胜",
        confidence=Confidence.INFERENCE,
        evidence_refs=("EV0002",),
    )


def make_rule(rule_id: str = "WR0001") -> WorldRule:
    return WorldRule(
        rule_id=rule_id,
        domain=WorldRuleDomain.MAGIC,
        statement="魔术需要咏唱咒文才能发动。",
        scope="初等魔术",
        exceptions="无咏唱者例外",
        confidence=Confidence.EXPLICIT,
        visible_from_volume=1,
        evidence_refs=("EV0002",),
    )


def make_location(location_id: str = "E0003") -> LocationProfile:
    return LocationProfile(
        location_id=location_id,
        name="布埃纳村",
        aliases=(),
        location_type=LocationType.VILLAGE,
        parent_location_id=None,
        political_control=("菲托亚领",),
        population_info=None,
        race_distribution=None,
        climate=None,
        terrain=None,
        danger=None,
        economy=None,
        services=None,
        known_routes=("RT0001",),
        nearby_locations=(),
        organizations=("E0005",),
        important_people=("E0002",),
        first_appearance_volume=1,
        first_appearance_line=15,
        visible_from_volume=1,
        evidence_refs=("EV0003",),
    )


def make_route(route_id: str = "RT0001") -> Route:
    return Route(
        route_id=route_id,
        from_location_id="E0003",
        to_location_id="E0004",
        transport_modes=("马车",),
        distance_info=None,
        typical_duration="数日",
        difficulty=None,
        terrain=None,
        border_requirements=None,
        cost_observations=None,
        hazards=("魔物",),
        seasonality=None,
        evidence_refs=("EV0003",),
    )


def make_travel(observation_id: str = "TO0001") -> TravelObservation:
    return TravelObservation(
        observation_id=observation_id,
        route_id="RT0001",
        origin="布埃纳村",
        destination="魔大陆",
        characters=("E0001",),
        transport="马车",
        elapsed_time="数日",
        stops=None,
        conditions="途中遭遇魔物",
        evidence_refs=("EV0003",),
    )


def make_organization(organization_id: str = "E0005") -> OrganizationProfile:
    return OrganizationProfile(
        organization_id=organization_id,
        name="冒险者公会",
        org_type="公會",
        leaders=(),
        members=(),
        hierarchy=None,
        goals=("管理冒险者",),
        rules=("任务登记",),
        resources=None,
        territory=None,
        alliances=(),
        enemies=(),
        reputation=None,
        visible_from_volume=1,
        evidence_refs=("EV0003",),
    )


def make_political(state_id: str = "PS0001") -> PoliticalState:
    return PoliticalState(
        state_id=state_id,
        organization_id="E0005",
        start_date=None,
        end_date=None,
        date_precision=DatePrecision.UNKNOWN,
        ruler=None,
        alliances=(),
        conflicts=(),
        succession=None,
        political_goals=(),
        internal_factions=(),
        visible_from_volume=1,
        evidence_refs=("EV0003",),
    )


def make_species(species_id: str = "SP0001") -> SpeciesProfile:
    return SpeciesProfile(
        species_id=species_id,
        name="人族",
        aliases=(),
        lifespan=None,
        appearance=None,
        physiology=None,
        abilities=(),
        weaknesses=(),
        language=None,
        culture=None,
        social_structure=None,
        distribution=None,
        relations_with_others=None,
        visible_from_volume=1,
        evidence_refs=("EV0003",),
    )


def make_creature(creature_id: str = "CR0001") -> CreatureProfile:
    return CreatureProfile(
        creature_id=creature_id,
        name="火狼",
        aliases=(),
        habitat="森林",
        behavior=None,
        danger="低",
        abilities=("火焰吐息",),
        weaknesses=("水",),
        social_behavior=None,
        uses=(),
        known_encounters=("鲁迪乌斯在旅行中遭遇",),
        visible_from_volume=1,
        evidence_refs=("EV0003",),
    )


def make_belief(belief_id: str = "BL0001") -> Belief:
    return Belief(
        belief_id=belief_id,
        owner_id="E0001",
        topic="父亲身份",
        statement="保罗是鲁迪乌斯的父亲。",
        certainty=Confidence.EXPLICIT,
        belief_state=BeliefState.FACT_KNOWN,
        learned_from="E0002",
        learned_at_volume=1,
        learned_method="HEARD_FROM_PERSON",
        is_true_in_world=True,
        visible_from_volume=1,
        visible_to_volume=None,
        note="家庭常识。",
        evidence_refs=("EV0001",),
    )


def make_economy(observation_id: str = "EC0001") -> EconomicObservation:
    return EconomicObservation(
        observation_id=observation_id,
        location_id="E0003",
        location_name="布埃纳村",
        at_date=None,
        at_volume=1,
        category="食物",
        item_id=None,
        goods_description="一份晚餐",
        quantity=None,
        currency=None,
        amount_description="数枚铜币",
        price_class=PriceClass.QUALITATIVE,
        context="村民日常开销",
        evidence_refs=("EV0003",),
    )


def make_relationship_change(change_id: str = "RC0001") -> RelationshipChange:
    return RelationshipChange(
        change_id=change_id,
        source_id="E0002",
        target_id="E0001",
        dimension="affection",
        before="普通",
        trigger="搬家的共同经历",
        after="亲近",
        at_volume=1,
        at_date=None,
        evidence_refs=("EV0003",),
    )


def make_speech(profile_id: str = "ST0001") -> SpeechProfile:
    return SpeechProfile(
        profile_id=profile_id,
        character_id="E0001",
        phase_id="childhood",
        phase_name="幼年期",
        politeness="礼貌",
        sentence_length="短句",
        address_habits="称呼父母为父亲大人",
        emotion_expression="克制",
        anger_expression="沉默",
        shy_expression="转移话题",
        intimate_speech="放松",
        stranger_speech="谨慎",
        superior_speech="敬语",
        inferior_speech="平语",
        canonical_examples=("V001 L11",),
        visible_from_volume=1,
        evidence_refs=("EV0002",),
    )


def make_conflict(conflict_id: str = "CC0001") -> CanonConflict:
    return CanonConflict(
        conflict_id=conflict_id,
        claim_a="火魔术需要咏唱",
        claim_b="鲁迪乌斯无咏唱",
        evidence_a_refs=("EV0002",),
        evidence_b_refs=("EV0002",),
        possible_resolution="鲁迪乌斯是例外",
        status=ConflictStatus.RESOLVED,
        note="测试冲突。",
    )


def make_gap(gap_id: str = "GAP0001") -> CanonGap:
    return CanonGap(
        gap_id=gap_id,
        domain="GEOGRAPHY",
        question="布埃纳村到魔大陆的准确距离",
        why_needed="旅行时间估算",
        searched_volumes=(1,),
        status=GapStatus.NO_CANON_ANSWER,
        possible_sources="后续卷的旅行记录",
        note="原文未给出准确距离。",
    )


def make_batch(batch_id: str = "ENRICH_V001") -> EnrichmentBatch:
    """A complete, verifiable enrichment batch over the test corpus."""
    return EnrichmentBatch(
        batch_id=batch_id,
        source_volume=1,
        source_unit_ids=("U0001", "U0002", "U0003"),
        schema_version=EnrichmentBatch.ENRICHMENT_SCHEMA_VERSION,
        evidence=(
            evidence("EV0001", line_start=3, line_end=3, unit="U0001"),
            evidence("EV0002", line_start=11, line_end=11),
            evidence("EV0003", line_start=15, line_end=15, unit="U0003"),
            evidence("EV0004", line_start=11, line_end=11),
        ),
        character_profiles=(make_profile(),),
        behavior_cases=(make_case(),),
        detailed_events=(make_event(), make_event("DE0002")),
        items=(make_item(),),
        item_instances=(make_instance(),),
        abilities=(make_ability(),),
        power_comparisons=(make_comparison(),),
        world_rules=(make_rule(),),
        locations=(make_location(),),
        routes=(make_route(),),
        travel_observations=(make_travel(),),
        organizations=(make_organization(),),
        political_states=(make_political(),),
        species=(make_species(),),
        creatures=(make_creature(),),
        beliefs=(make_belief(),),
        economic_observations=(make_economy(),),
        relationship_changes=(make_relationship_change(),),
        speech_profiles=(make_speech(),),
        canon_conflicts=(make_conflict(),),
        canon_gaps=(make_gap(),),
    )


def write_batches(tmp_path: Path, *batches: EnrichmentBatch) -> Path:
    """Write batches into a temp enrichment content directory."""
    import json

    content_dir = tmp_path / "enrich"
    content_dir.mkdir(exist_ok=True)
    for batch in batches:
        (content_dir / f"V{batch.source_volume:03d}.json").write_text(
            json.dumps(batch.to_json(), ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return content_dir
