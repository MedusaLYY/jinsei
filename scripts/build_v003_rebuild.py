import json, pathlib
from overlord_worldsim.canon.parse import parse_source
from overlord_worldsim.canon.enrich_model import (
    EvidenceRef, EvidenceType, EnrichmentBatch, CharacterProfile, CharacterQuirk, CharacterPersona,
    WorldRule, WorldRuleDomain, CharacterBehaviorRule, BehaviorTag, GapStatus, CanonGap
)
from overlord_worldsim.canon.extract_model import Confidence, DatePrecision
from overlord_worldsim.canon.enrich_registry import load_enrichment_batches, load_entity_registry
from overlord_worldsim.canon.enrich_verifier import verify_enrichment

raw = pathlib.Path("data/raw/无职转生TXT合集.txt").read_text(encoding="utf-8")
doc = parse_source(raw)
# Determine chapter_title for U0054
u0054 = next(u for u in doc.units if u.unit_id == "U0054")
chapter_title = u0054.title  # should be 外传...
print(f"U0054 title={chapter_title!r} lines {u0054.start_line}-{u0054.end_line}")

# Map evidence lines discovered earlier in raw
# Found: 28342 Ariel name, 28450 sadist, 28452 fetish, 28462 status, 28456 cover, plus 28366 Luke, 28382 Derrick
evidence_defs = [
    ("EV03001", 28342, 28343, "爱丽儿·阿涅摩伊·阿斯拉在王宫庭园现身，王族身份确定"),
    ("EV03002", 28450, 28451, "爱丽儿是同性也照吃的极度虐待狂，王宫内一部分人清楚的事实"),
    ("EV03003", 28452, 28453, "许多阿斯拉贵族王族都拥有超过限度的性癖好，爱丽儿也不例外"),
    ("EV03004", 28462, 28463, "在历史四百年无战无饥的阿斯拉，有很多人认为把异于他人的行为当成兴趣正代表一种社会地位"),
    ("EV03005", 28456, 28457, "爱丽儿以自身的外表和传言作为掩护"),
    ("EV03006", 28366, 28367, "名为路克·诺托斯·格雷拉特，王宫护卫登场"),
    ("EV03007", 28382, 28383, "守护术师迪利克·雷特巴特具备独特气质，衬托三人难以亲近氛围"),
    ("EV03008", 28800, 28810, "迪利克劝诫爱丽儿与路克不要因低俗传闻与过于任性树敌，提醒王位风险"),
]

evidence = []
for eid, start, end, note in evidence_defs:
    # ensure lines inside U0054 or other units? EV03006-03007 still inside U0054 (28306-28885) yes
    evidence.append(EvidenceRef(
        evidence_id=eid, volume_no=3, unit_id="U0054", chapter_title=chapter_title,
        source_start_line=start, source_end_line=end,
        evidence_type=EvidenceType.CANON_EXPLICIT, confidence=Confidence.EXPLICIT, note=note,
    ))

def ev(*ids):
    return tuple(ids)

profiles = [
    CharacterProfile(
        profile_id="CP03001", character_id="E0044", phase_id="P03001", phase_name="王宫期",
        start_date=None, end_date=None, date_precision=DatePrecision.UNKNOWN,
        age_description="少女期，王宫生活（外传；早于V008十七岁）",
        personality_traits=("高贵","机敏","从容","善于演绎"),
        values=("王族礼仪与从容","以才华与人脉立身"),
        desires=("维持王宫内的优雅享乐生活","在派阀夹缝中自保"),
        fears=("因低俗传闻树敌","被判不适合为王"),
        taboos=("在部下面前久露软弱",),
        insecurities=("对自身王适合性尚无定论",),
        pride="王族礼法与看人眼光",
        impulsiveness="MEDIUM", patience="MEDIUM", risk_tolerance="MEDIUM", self_control="HIGH",
        attachment_style="对路克与迪利克为宫廷共谋搭档",
        authority_attitude="对王兄们保持距离，对佩尔基乌斯尚未接触",
        family_attitude="与两位王兄对立，第二公主派最弱",
        romantic_attitude="与路克为君臣共谋，非单纯恋爱标签",
        violence_attitude="委于护卫",
        money_attitude="以礼遇换支持",
        status_attitude="视王权为责任而非虚荣的萌芽",
        race_attitude="接纳精灵等",
        religious_attitude=None,
        loyalty="HIGH", ambition="HIGH",
        short_term_goals=("以庭园茶会维持人际","以传言与外表掩护生存"),
        long_term_goals=("成为能打破停滞的王（迪利克期待）",),
        obligations=("对十三旧部与派阀下的人的潜在责任",),
        decision_tendencies=("先听完整经历再抉择","以优雅维系形象"),
        speech_tendencies=("公开端庄敬语","私下仍保持王族口吻"),
        social_tendencies=("庭园茶会维系人际","与路克讨论宫中女孩以作掩护"),
        conflict_tendencies=("以问答与礼仪应对",),
        known_skills=("政略洞察","人才观察"),
        knowledge_state=("知阿斯拉贵族以异癖为地位符号","知第二公主派最弱"),
        relationship_tendencies=("对路克君臣共谋","对迪利克受其常识刹车"),
        behavior_changes_note="王宫内以外表与传言作掩护，享乐表象下已有勤勉社交一面",
        summary="王宫期的爱丽儿以优雅与传言为掩护，在路克与迪利克陪伴下度日的第二公主。",
        visible_from_volume=3, visible_to_volume=None,
        identity="人类·阿斯拉王族 第二公主",
        origin="阿斯拉王国王都·王宫，第二公主派",
        origin_location_id=None,
        status_rank="第二公主（王宫期）",
        appearance_traits=["金发碧眼","宛如美术课本的美貌","王族礼装","庭园中的从容仪态"],
        body_traits=["端庄王族仪态"],
        core_personality=["视王位为责任的萌芽","以优雅维系统治形象","才华即人脉的雏形"],
        surface_personality=["王族礼仪、从容、外交、情绪控制、茶会与敬语","以自身外表和传言作为掩护"],
        hidden_personality=["好奇心、观察特殊的人、测试他人反应、隐藏的任性","同性也照吃的极度虐待狂等超过限度的性癖好之一员，私人倾向"],
        interests=["观察有潜力者","宫廷社交"],
        dislikes=["被说教低俗传闻树敌"],
        weaknesses=["派阀实力最弱"],
        obsessions=["以传言与外表掩护生存"],
        habits=["庭园茶会","与路克谈论宫中女孩"],
        emotional_triggers=["被指责过于任性","提及王位无望论"],
        decision_logic="享乐表象下仍保留打破停滞的可能性；公开场合不用私癖作政治工具",
        extreme_choice_note=None,
        phase_personality_note="公开端庄、私下享乐与试探并存；对迪利克的常识刹车会耸肩反驳但未决裂",
        evidence_refs=ev("EV03001","EV03003","EV03005"),
    ),
    CharacterProfile(
        profile_id="CP03002", character_id="E0045", phase_id="P03002", phase_name="王宫护卫期",
        start_date=None, end_date=None, date_precision=DatePrecision.UNKNOWN,
        age_description="青年骑士，王宫期",
        personality_traits=("忠诚","好色","直言","轻佻"),
        values=("爱丽儿成王为使命",),
        desires=("护卫爱丽儿并维持宫廷享乐",),
        fears=("因好色传闻致主树敌",),
        taboos=("背离爱丽儿",),
        insecurities=("剑术与谋略尚不足以独当一面",),
        pride="护卫礼仪与知遇",
        impulsiveness="MEDIUM", patience="LOW", risk_tolerance="MEDIUM", self_control="MEDIUM",
        attachment_style="对爱丽儿君臣共谋",
        authority_attitude="对王家保持服从",
        family_attitude="诺托斯家责任",
        romantic_attitude="好色，喜巨乳，与路克讨论宫中女孩",
        violence_attitude="持剑护卫为先",
        money_attitude=None, status_attitude="重王统", race_attitude=None, religious_attitude=None,
        loyalty="HIGH", ambition="HIGH",
        short_term_goals=("与爱丽儿以传言掩护在宫中生存",),
        long_term_goals=("见证登基",),
        obligations=("护卫爱丽儿",),
        decision_tendencies=("直言陈情","以轻佻掩护"),
        speech_tendencies=("对爱丽儿调侃式讨论","对迪利克耸肩反驳"),
        social_tendencies=("往返庭园",),
        conflict_tendencies=("以身挡敌",),
        known_skills=("宫廷剑术","人脉斡旋"),
        knowledge_state=("知第二公主派最弱","知宫中女孩传闻"),
        relationship_tendencies=("对爱丽儿共谋","对迪利克被其劝诫"),
        behavior_changes_note="与爱丽儿一同用享乐作掩护",
        summary="王宫期的路克，忠诚而好色，与爱丽儿共谋的宫廷搭档。",
        visible_from_volume=3, visible_to_volume=None,
        identity="人类·阿斯拉贵族 诺托斯家",
        origin="阿斯拉王国",
        status_rank="王宫护卫（爱丽儿侧近）",
        appearance_traits=["帅哥","讨人喜欢的长相"],
        body_traits=[],
        core_personality=["忠于爱丽儿","好色"],
        surface_personality=["清澄应对","宫廷礼仪"],
        hidden_personality=["好色，喜巨乳","与爱丽儿一同享乐掩护"],
        interests=["宫中女孩"],
        dislikes=["迪利克的说教"],
        weaknesses=["易被利用"],
        obsessions=[],
        habits=["与爱丽儿讨论乳头颜色"],
        emotional_triggers=["被指不解风情"],
        decision_logic="忠诚与享乐并存；未将私癖作政治工具",
        extreme_choice_note=None,
        phase_personality_note="与爱丽儿互为掩护，迪利克为常识刹车",
        evidence_refs=ev("EV03006","EV03002"),
    ),
    CharacterProfile(
        profile_id="CP03003", character_id="E0046", phase_id="P03003", phase_name="守护术师期",
        start_date=None, end_date=None, date_precision=DatePrecision.UNKNOWN,
        age_description="青年术师，王宫期",
        personality_traits=("常识","克制","忠直","忧虑"),
        values=("常识与国家安定","爱丽儿应成为能打破停滞的王"),
        desires=("爱丽儿能登基增强国力","避免因低俗传闻树敌"),
        fears=("爱丽儿因享乐放弃王位","刺客与政争"),
        taboos=("临阵抛下主君",),
        insecurities=("自认只是水平不算罕见的魔术师",),
        pride="优秀成绩毕业的魔术师团术师",
        impulsiveness="LOW", patience="HIGH", risk_tolerance="LOW", self_control="HIGH",
        attachment_style="以守护誓言维系",
        authority_attitude="对王家与魔术师团服从",
        family_attitude="受父亲推举就任守护术师",
        romantic_attitude=None,
        violence_attitude="以术护主",
        money_attitude=None, status_attitude="重王统", race_attitude=None, religious_attitude=None,
        loyalty="HIGH", ambition="MODERATE",
        short_term_goals=("劝爱丽儿与路克勿因低俗树敌",),
        long_term_goals=("助爱丽儿成能征服中央大陆的明君",),
        obligations=("守护术师之责",),
        decision_tendencies=("以常识直谏","独自思考国家未来"),
        speech_tendencies=("直言劝诫体","叹气"),
        social_tendencies=("与路克轮值如厕","退场后独自思考"),
        conflict_tendencies=("以身挡刺客",),
        known_skills=("魔术","守护术"),
        knowledge_state=("知第二公主派最弱但有超凡魅力","知爱丽儿勤勉社交一面"),
        relationship_tendencies=("对爱丽儿由推举到舍命追随","对路克共担护卫"),
        behavior_changes_note="从被耸肩反驳到在厕所中坚定追随",
        summary="王宫期的迪利克，常识的刹车与最坚定的追随者。",
        visible_from_volume=3, visible_to_volume=None,
        identity="人类·魔术师团 守护术师",
        origin="阿斯拉王国",
        status_rank="守护术师（爱丽儿侧近）",
        appearance_traits=["偏瘦","讨人喜欢的长相","具独特气质"],
        body_traits=[],
        core_personality=["常识","忠直","愿为爱丽儿舍命"],
        surface_personality=["默默听对话","直言劝诫"],
        hidden_personality=["在厕所中坚定认为爱丽儿能打破停滞"],
        interests=[],
        dislikes=["过于任性与低俗树敌"],
        weaknesses=["言语不擅被耸肩"],
        obsessions=["爱丽儿应成王打破四百年停滞"],
        habits=["如厕前告知路克"],
        emotional_triggers=["爱丽儿自称满足于喝茶享乐"],
        decision_logic="王位>享乐；国家安定>私人传闻",
        extreme_choice_note="即使与刺客交战丧命也在所不惜",
        phase_personality_note="常识刹车，常被反驳但不离弃",
        evidence_refs=ev("EV03007","EV03008"),
    ),
]

quirks = [
    CharacterQuirk(
        quirk_id="QK03001", character_id="E0044", phase_id="P03001",
        category="private_fetish", name="极度虐待狂与性癖好",
        description="王宫期爱丽儿是同性也照吃的极度虐待狂；许多阿斯拉贵族王族都拥有超过限度的性癖好，爱丽儿也不例外。与路克讨论宫中女孩乳头颜色等享乐是宫廷掩护与贵族地位符号，不是登基后的施政目标。",
        intensity="HIGH（私人倾向）/ LOW（政治行动驱动）",
        frequency="王宫庭园闲谈中偶发",
        triggers=("庭园茶会","与路克私下闲谈","阿斯拉贵族式荤话氛围"),
        preferred_targets=(), avoided_targets=(),
        public_expression="公开场合维持王族礼仪",
        private_expression="与路克私下讨论宫中女孩等享乐话题",
        behavior_patterns=("以享乐与传言作掩护",),
        verbal_patterns=(),
        body_language=None,
        emotional_reward="享乐与掩护",
        emotional_response=None,
        boundaries=("不在朝堂用此事做交易","不因此放弃王位目标","迪利克反对因低俗传闻树敌"),
        exceptions=(),
        start_date=None, end_date=None,
        visible_from_volume=3, visible_to_volume=None,
        evidence_type=EvidenceType.CANON_EXPLICIT, confidence=Confidence.EXPLICIT,
        evidence_refs=ev("EV03002","EV03003"),
        simulation_weight="COLOR",
        overplay_warning="禁止把虐待狂/性癖写成爱丽儿的主要行动目标或每场社交的默认行为；这是王宫期私人倾向，登基后施政目标为王权安定，GM仅在私密宫廷闲谈或玩家主动引向时启用。",
        is_private_tendency=True,
    ),
]

personas = [
    CharacterPersona(persona_id="PN03001", character_id="E0044", phase_id="P03001", persona_type="PUBLIC", description="王族礼仪、从容，庭园中威仪的第二公主", speech_style="端庄敬语", behavior_traits=("王族礼仪","从容","茶会"), visible_from_volume=3, visible_to_volume=None, evidence_refs=ev("EV03005")),
    CharacterPersona(persona_id="PN03002", character_id="E0044", phase_id="P03001", persona_type="PRIVATE", description="私下与路克享乐、讨论宫中女孩、极度虐待狂等私人倾向", speech_style="更直接、与路克调侃", behavior_traits=("与路克共谋","享乐掩护"), visible_from_volume=3, visible_to_volume=None, evidence_refs=ev("EV03002")),
]

world_rules = [
    WorldRule(rule_id="WR03001", domain=WorldRuleDomain.SOCIETY, statement="在阿斯拉王国，有很多人认为把异于他人的行为当成兴趣正代表一种社会地位；历史四百年无战无饥使贵族以超过限度的性癖好等异癖为地位符号", scope="阿斯拉王国贵族与王族", exceptions="迪利克等常识派反对因低俗传闻树敌", confidence=Confidence.EXPLICIT, visible_from_volume=3, evidence_refs=ev("EV03003","EV03004")),
    WorldRule(rule_id="WR03002", domain=WorldRuleDomain.NOBILITY, statement="阿斯拉王位继承中第二公主派在王宫期最弱，年龄与同伴数量均输两位兄长，直接对抗胜算低", scope="阿斯拉王位继承", exceptions="爱丽儿具备超凡魅力与勤勉社交潜力可打破停滞", confidence=Confidence.EXPLICIT, visible_from_volume=3, evidence_refs=ev("EV03008")),
]

behavior_rules = [
    CharacterBehaviorRule(
        rule_id="BR03001", character_id="E0044", phase_id="P03001",
        condition="王宫庭园私下与路克闲谈，氛围为阿斯拉贵族式荤话",
        trigger_event="路克提起宫中女孩或传闻",
        response="可能与路克一同讨论宫中女孩等享乐话题，以此作掩护与地位符号",
        psychological_reason="以享乐与传言作掩护，维持难以亲近的氛围；私人倾向非政治目标",
        known_at_time="知第二公主派最弱，直接对抗无胜算",
        unknown_at_time="不知道未来迪利克会坚定追随至舍命",
        public_vs_private="PRIVATE", simulation_weight="COLOR",
        overplay_warning="禁止把此反应写成每场社交默认或登基后施政手段；仅宫廷私下启用",
        tags=(BehaviorTag.PRIVATE_SCENE, BehaviorTag.NOBILITY),
        visible_from_volume=3, visible_to_volume=None,
        evidence_type=EvidenceType.CANON_EXPLICIT, confidence=Confidence.EXPLICIT,
        evidence_refs=ev("EV03002"),
    ),
    CharacterBehaviorRule(
        rule_id="BR03002", character_id="E0044", phase_id="P03001",
        condition="迪利克以常识直谏不要因低俗传闻树敌",
        trigger_event="迪利克劝诫过于任性",
        response="与路克一同耸肩反驳，称迪利克不解风情、需学会察言观色",
        psychological_reason="以耸肩维持享乐表象与掩护，私下仍受其守护",
        known_at_time="知迪利克是具备常识的刹车",
        unknown_at_time="不知道迪利克在厕所中已坚定追随",
        public_vs_private="MIXED", simulation_weight="SECONDARY",
        overplay_warning=None,
        tags=(BehaviorTag.NOBILITY, BehaviorTag.TRUST),
        visible_from_volume=3, visible_to_volume=None,
        evidence_type=EvidenceType.CANON_EXPLICIT, confidence=Confidence.EXPLICIT,
        evidence_refs=ev("EV03008"),
    ),
    CharacterBehaviorRule(
        rule_id="BR03003", character_id="E0044", phase_id="P03001",
        condition="公开朝堂或涉及王位存亡的抉择",
        trigger_event="任何王位压力",
        response="不以性癖好行动，改以礼仪、笼络、或迪利克所期待的勤勉经营应对",
        psychological_reason="王位与国家>私人羞耻兴趣；享乐仅为掩护",
        known_at_time="知自身为第二公主，派阀最弱",
        unknown_at_time="不知道未来将取得佩尔基乌斯后盾",
        public_vs_private="PUBLIC", simulation_weight="PRIMARY",
        overplay_warning="禁止在朝堂生成性癖场景；该场合必须走政治/礼仪路径",
        tags=(BehaviorTag.AUTHORITY, BehaviorTag.NOBILITY, BehaviorTag.PUBLIC_SCENE),
        visible_from_volume=3, visible_to_volume=None,
        evidence_type=EvidenceType.CANON_EXPLICIT, confidence=Confidence.EXPLICIT,
        evidence_refs=ev("EV03008"),
    ),
]

batch = EnrichmentBatch(
    batch_id="ENRICH_V003", source_volume=3, source_unit_ids=("U0054",), schema_version="1.0.0",
    evidence=tuple(evidence), character_profiles=tuple(profiles),
    behavior_cases=(), detailed_events=(), items=(), item_instances=(),
    abilities=(), power_comparisons=(), world_rules=tuple(world_rules),
    locations=(), routes=(), travel_observations=(), organizations=(), political_states=(),
    species=(), creatures=(), beliefs=(), economic_observations=(), relationship_changes=(),
    speech_profiles=(), character_quirks=tuple(quirks), character_preferences=(), body_language_profiles=(),
    character_personas=tuple(personas), canon_conflicts=(), canon_gaps=(),
    behavior_rules=tuple(behavior_rules),
)

out = pathlib.Path("data/canon_enriched/V003.json")
out.write_text(json.dumps(batch.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote V003 ev={len(evidence)} profiles={len(profiles)} quirks={len(quirks)} rules={len(behavior_rules)} world_rules={len(world_rules)}")

# verify
reg = load_entity_registry(pathlib.Path("data/canon"))
doc2 = parse_source(pathlib.Path("data/raw/无职转生TXT合集.txt").read_text(encoding="utf-8"))
batches = load_enrichment_batches(pathlib.Path("data/canon_enriched"))
report = verify_enrichment(batches, doc2, reg)
print("is_clean", report.is_clean)
for e in report.errors:
    print(e.code, e.path, e.message)
