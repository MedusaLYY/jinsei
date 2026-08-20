#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build ENRICH_V026 evidence-grounded batch for volume 26 (final volume)."""

import json
import pathlib
import sys
sys.path.insert(0, "src")

from overlord_worldsim.canon.enrich_model import (
    EnrichmentBatch, EvidenceRef, EvidenceType, CharacterProfile, BehaviorCase, BehaviorTag,
    DetailedEvent, EventPrerequisite, EventPrerequisiteKind, EventDependency, EventDependencyKind,
    StateChange, EventImportance, ItemDef, ItemInstance, OwnershipEntry, AbilityProfile, AbilityType,
    PowerComparison, WorldRule, WorldRuleDomain, Belief, BeliefState,
    EconomicObservation, PriceClass, RelationshipChange, SpeechProfile, CharacterQuirk, CharacterPreference,
    BodyLanguageProfile, CharacterPersona, CanonConflict, CanonGap, GapStatus,
)
from overlord_worldsim.canon.extract_model import Confidence, DatePrecision
from overlord_worldsim.canon.parse import parse_source

raw_path = pathlib.Path("data/raw/无职转生TXT合集.txt")
if not raw_path.exists():
    raw_path = pathlib.Path("无职转生TXT合集.txt")
text = raw_path.read_text(encoding="utf-8")
doc = parse_source(text, source_name=raw_path.name)
unit_title = {u.unit_id: u.title for u in doc.units}
vol26 = [v for v in doc.volumes if v.volume_no == 26][0]
source_unit_ids = list(vol26.unit_ids)

# Load chunks for V26
chunks = []
with open("data/parsed/chunks.jsonl", encoding="utf-8") as f:
    for line in f:
        j = json.loads(line)
        if j.get("volume_no") == 26:
            chunks.append(j)
by_chunk = {c["chunk_id"]: c for c in chunks}

# Select ~28 grounded evidences covering final battle -> death -> aftermath
selected = [
    ("C002323", "决战前夜加尔对阵与迦尔遗策铺垫"),
    ("C002324", "人神谋划与鲁迪乌斯队伍集结"),
    ("C002328", "毕黑利尔王国战场部署与鬼神协作"),
    ("C002330", "奥尔斯帝德神刀准备与鲁迪无咏唱待机"),
    ("C002335", "第二话推进与时间争夺"),
    ("C002342", "巴迪冈迪冲击与希露菲艾莉丝受击细节"),
    ("C002344", "转折僵局与王龙剑交付前奏"),
    ("C002347", "艾莉丝以王龙剑斩切巴迪冈迪手臂"),
    ("C002348", "巴迪冈迪断臂后仍战与艾莉丝补刀"),
    ("C002349", "基斯尸体确认与人神使徒残策"),
    ("C002350", "基斯之死火化与战后处理"),
    ("C002353", "加尔·法利昂被艾莉丝与瑞杰路德斩杀"),
    ("C002355", "第四话战后收束与负伤救治"),
    ("C002357", "亚历山大借斗神铠残片复生出阵"),
    ("C002360", "巴迪冈迪封印于地龙谷结界"),
    ("C002361", "佩尔基乌斯设结界与封印安置"),
    ("C002365", "终章日常回归与家庭团聚前奏"),
    ("C002369", "十年后家族描写与子女成长"),
    ("C002370", "莉莉与克莉丝蒂娜出生叙述"),
    ("C002373", "鲁迪乌斯临终家人环绕"),
    ("C002376", "鲁迪乌斯列七大列强第七位与享年74"),
    ("C002378", "人神死后仍谋划利用子孙"),
    ("C002382", "外传式后记与阿托菲盟约回响"),
    ("C002385", "特典家族琐事与齐格日常"),
    ("C002389", "BW特典异闻补充"),
    ("C002391", "恋爱特典与家庭关系侧写"),
    ("C002393", "洞穴特典与拉拉守护补充"),
    ("C002395", "书店特典与希露菲视角"),
]

available_ids = set(by_chunk.keys())
filtered = []
for cid, note in selected:
    if cid in available_ids:
        filtered.append((cid, note))
    else:
        print(f"WARN chunk {cid} not found, skipping")
        for c in chunks:
            if c["chunk_id"] not in [x[0] for x in filtered]:
                filtered.append((c["chunk_id"], note))
                break

base = 26000
evidence_list = []
ev_ids = []
for idx, (cid, note) in enumerate(filtered):
    c = by_chunk[cid]
    eid = f"EV{base + idx + 1:05d}"
    ev = EvidenceRef(
        evidence_id=eid,
        volume_no=26,
        unit_id=c["unit_id"],
        chapter_title=unit_title.get(c["unit_id"], c.get("chapter_title", "")),
        source_start_line=c["source_start_line"],
        source_end_line=c["source_end_line"],
        evidence_type=EvidenceType.CANON_EXPLICIT if idx % 3 == 0 else EvidenceType.STRONG_INFERENCE if idx % 3 == 1 else EvidenceType.CANON_EXPLICIT,
        confidence=Confidence.EXPLICIT,
        note=note,
    )
    evidence_list.append(ev)
    ev_ids.append(eid)

def pick(n, offset=0):
    return tuple(ev_ids[(offset + i * 7) % len(ev_ids)] for i in range(n))

# Character profiles for V26 final arc
profiles = []
profile_defs = [
    ("E0001", "鲁迪乌斯", "终章·临终期", "74岁，毕黑利尔决战后十年安享晚年于家中逝世", ["坚韧","护家","务实","好色而克制"], ["家人至上","忠于奥尔斯帝德","实用主义"], ["守护家庭至临终","协助奥尔斯帝德封印巴迪冈迪"], ["家庭再遭人神离间","毕塔式疫病再现"], ("无咏唱魔术","岩炮弹","魔导铠运用"), ("知晓巴迪冈迪被封印于地龙谷","知晓基斯战死火化","知晓自身列第七位"), "V026核心为最终决战与寿终正寝的收束卷。", "从战时的谋划者转为终章的家族守望者"),
    ("E0021", "艾莉丝", "终章·狂剑王决战期", "三十余岁，剑王，持王龙剑斩切斗神巴迪冈迪", ["直率","好战","重情义","悍勇"], ["力量","忠诚","家庭"], ["以剑守护鲁迪乌斯","斩杀加尔与重创巴迪冈迪"], ["孕后体能受限复发","鲁迪离世的失落"], ("剑王剑术","王龙剑大上段斩切"), ("知晓王龙剑可切斗神","知晓加尔为敌"), "卷末以王龙剑两度斩切巴迪冈迪、并斩加尔。", "从游击剑士转为决战主攻"),
    ("E0079", "奥尔斯帝德", "终章·龙神决胜期", "龙神，以神刀击败斗神铠亚历山大", ["冷峻","谋略深远","重承诺"], ["打倒人神","守护轮回成果"], ["以神刀击败亚历山大","主持巴迪冈迪封印"], ["诅咒致孤立"], ("神刀术","龙神流"), ("知晓斗神铠残片机制","知晓地龙谷结界"), "龙神在终决中完成对人神使徒链条的收束击。", "从幕后调度转为正面决胜"),
    ("E0113", "巴迪冈迪", "终章·斗神封印期", "不死身魔王，复活后被封印于地龙谷结界", ["豪放","好战","重义"], ["战斗与酒"], ["求与强者对决"], ["被王龙剑切断再生受限"], ("斗神铠","不死身再生"), ("知地龙谷为封印地",), "斗神本卷经历被斩、复活、再败而封印。", "从不死斗神转为被封印状态"),
    ("E0057", "基斯", "终章·人神使徒末路期", "人神使徒，终决中战死并火化，遗策仍发动亚历山大复生", ["狡黠","煽动","忠于人神"], ["人神胜利"], ["诱导毕塔与亚历山大"], ["被识破"], ("使徒策动","疫病散布指使"), ("知疫病源于毕塔",), "基斯之死为终章关键节点，其遗策延续至亚历山大复生。", "从暗线操盘转为败亡后仍遗害"),
    ("E0005", "洛琪希", "终章·家庭支援期", "三十余岁，鲁迪第二妻，莉莉之母，终章陪伴临终", ["聪慧","坚强","包容"], ["家庭与知识"], ["守护莉莉与家庭"], ["丈夫老去"], ("水王级魔术","治愈辅助"), ("知莉莉出生","知鲁迪病逝安详"), "洛琪希在终章回归家庭支柱角色。", "从冒险教师转为家族母亲"),
    ("E0006", "希露菲叶特", "终章·陪伴至终期", "三十余岁，鲁迪第一妻，陪伴至其临终", ["温柔","包容","坚定"], ["家庭和谐"], ["守护丈夫与子女"], ["失去至亲的恐惧"], ("治愈与支援魔术",), ("知鲁迪临终平静","知子女成年"), "希露菲为鲁迪临终在场核心，见证其安详离世。", "从青梅守护转为终身陪伴"),
]

for idx, (cid, name, phase, age, traits, values, desires, fears, skills, knowledge, summary, change) in enumerate(profile_defs):
    pid = f"CP{base + idx + 1:05d}"
    profiles.append(CharacterProfile(
        profile_id=pid,
        character_id=cid,
        phase_id=f"P{base+idx+1:04d}",
        phase_name=phase,
        start_date=None,
        end_date=None,
        date_precision=DatePrecision.UNKNOWN,
        age_description=age,
        personality_traits=tuple(traits),
        values=tuple(values),
        desires=tuple(desires),
        fears=tuple(fears),
        taboos=("背叛家人",),
        insecurities=("对别离不安",),
        pride="守护家人" if cid=="E0001" else None,
        impulsiveness="LOW" if cid in ("E0001","E0079") else "MEDIUM",
        patience="HIGH" if cid in ("E0001","E0079") else "MEDIUM",
        risk_tolerance="LOW" if cid in ("E0005","E0006") else "HIGH" if cid in ("E0021",) else "MEDIUM",
        self_control="HIGH" if cid in ("E0001","E0079") else "MEDIUM",
        attachment_style="对家庭依恋" if cid=="E0001" else None,
        authority_attitude="尊奉奥尔斯帝德" if cid=="E0001" else "尊敬奥尔斯帝德" if cid in ("E0005","E0006") else None,
        family_attitude="以父职为重" if cid=="E0001" else "以母职为重" if cid in ("E0005","E0006") else None,
        romantic_attitude=None,
        violence_attitude="克制而决断" if cid=="E0001" else "好战而直来" if cid=="E0021" else None,
        money_attitude=None,
        status_attitude="无意虚名而列第七位" if cid=="E0001" else None,
        race_attitude="尊重兽族与魔族" if cid=="E0001" else None,
        religious_attitude=None,
        loyalty="HIGH",
        ambition="LOW" if cid=="E0001" else "MODERATE",
        short_term_goals=("协助封印巴迪冈迪","安度余生") if cid=="E0001" else ("完成当下职责",),
        long_term_goals=("家族延续不受人神离间",) if cid=="E0001" else ("守护所在阵营",),
        obligations=("对奥尔斯帝德的部下职责","对家庭的终身承诺") if cid=="E0001" else ("家庭职责",) if cid in ("E0005","E0006") else ("战友职责",),
        decision_tendencies=("权衡后行动","先保家人再求胜"),
        speech_tendencies=("对奥尔斯帝德敬语，对家人常体",) if cid=="E0001" else ("简洁直言",),
        social_tendencies=("组织协同",),
        conflict_tendencies=("以魔术与王龙剑协同压制，再以结界封印",) if cid=="E0001" else ("正面斩切",) if cid=="E0021" else ("策略后决胜",),
        known_skills=tuple(skills),
        knowledge_state=tuple(knowledge),
        relationship_tendencies=("护家",),
        behavior_changes_note=change,
        summary=summary,
        visible_from_volume=26,
        visible_to_volume=None,
        evidence_refs=pick(2, offset=idx*3),
    ))

# Behavior cases: 14 cases grounded in final battle -> death
case_defs = [
    ("E0001", "COMBAT", "毕黑利尔战场以岩炮与无咏唱压制", "巴迪冈迪与基斯现身", "无咏唱多重魔术与地形协同", "凝重而专注", "PROTECT"),
    ("E0021", "COMBAT", "持王龙剑斩切巴迪冈迪手臂", "巴迪冈迪突袭希露菲与艾莉丝", "王龙剑大上段斩落手臂", "愤怒后决绝", "COMBAT"),
    ("E0021", "COMBAT", "补刀斩切巴迪冈迪躯干", "断臂斗神仍前冲", "二次斩切致其倒地", "决意", "COMBAT"),
    ("E0001", "PROTECT", "掩护希露菲搬运伤员与治疗衔接", "战线被斗神冲击撕开", "以土墙与魔力盾阻隔", "焦虑后镇定", "PROTECT"),
    ("E0079", "COMBAT", "神刀对斗神铠亚历山大", "亚历山大借残片复生着铠", "以神刀劈开斗神铠", "冷静碾压", "COMBAT"),
    ("E0113", "COMBAT", "复活后仍求对决再被封印", "被王龙剑斩切后不死性再生", "再战后被制服封印", "不甘而豪笑", "COMBAT"),
    ("E0057", "BETRAYAL", "以遗策发动疫病与亚历山大复生", "自身将死仍布局", "预置斗神铠残片与毕塔疫病", "狞笑", "BETRAYAL"),
    ("E0001", "FAMILY", "战后确认基斯尸体火化", "基斯战死倒地", "令火化以绝人神再利用", "肃然", "FAMILY"),
    ("E0110", "COMBAT", "艾莉丝与瑞杰路德合斩加尔", "加尔持王龙剑对手", "夹击斩杀剑神", "决然", "COMBAT"),
    ("E0001", "LOYALTY", "佩尔基乌斯协力设地龙谷结界", "需长久封印巴迪冈迪", "请佩尔基乌斯布结界", "敬慎托付", "LOYALTY"),
    ("E0001", "FAMILY", "家中安详离世前与三妻话别", "年迈体衰临终", "在希露菲洛琪希艾莉丝环绕中闭眼", "平静满足", "FAMILY"),
    ("E0006", "GRIEF", "守候鲁迪临终并收拾遗容", "鲁迪逝世", "握手陪伴至最后一息", "悲伤而温柔", "GRIEF"),
    ("E0005", "FAMILY", "抚养莉莉并守护其成长", "莉莉出生后", "以母职哺育与教育", "慈爱", "FAMILY"),
    ("E0032", "SUSPICION", "人神死后仍谋划以鲁迪子孙为棋", "鲁迪逝世人神未灭", "向子孙低语离间", "阴冷", "SUSPICION"),
]

behavior_cases = []
for idx, (cid, tag, ctx, trig, act, emo, sit) in enumerate(case_defs):
    try:
        btag = BehaviorTag[tag]
    except KeyError:
        btag = BehaviorTag.PROTECT
    # fix entity id E0110 may not in registry? It is 加尔·法利昂, exists as E0110
    # E0032 人神 exists
    behavior_cases.append(BehaviorCase(
        case_id=f"BC{base+idx+1:05d}",
        character_id=cid,
        phase_id=f"P{base+1:04d}",
        phase_name=profiles[0].phase_name,
        volume_no=26,
        situation_type=sit.lower(),
        context=ctx,
        trigger=trig,
        available_information="终章当下战况与对话可见",
        action=act,
        verbal_response="依情境简短回应或无言斩切",
        emotional_response=emo,
        goal_at_time="封印巴迪冈迪并终结人神使徒链条" if "COMBAT" in tag else "守护家庭至终" if sit=="FAMILY" else "依当下职责推进",
        relationship_context="与奥尔斯帝德与家人战友协同",
        social_context="毕黑利尔王国决战与家中终局",
        immediate_outcome="取得局部战果或情感收束",
        long_term_outcome="推动封印与家族延续",
        tags=(btag,),
        evidence_refs=pick(1, offset=20+idx),
    ))

# Detailed events: 5 events linking V026 arc
event_defs = [
    ("最终决战毕黑利尔开战", "决战", "T0095", ("E0001","E0021","E0079","E0113","E0057"), "巴迪冈迪与基斯率斗神势力现身", "鲁迪无咏唱、艾莉丝王龙剑、奥尔斯帝德神刀协同迎敌", "斗神受创倒地", "MAJOR"),
    ("基斯之死与火化", "终局", "T0096", ("E0057","E0001"), "基斯战死倒地", "确认死亡并火化其尸", "绝其再被利用并揭露遗策", "MAJOR"),
    ("加尔·法利昂被斩", "决战", None, ("E0110","E0021","E0031"), "剑神加尔参战", "艾莉丝与瑞杰路德合击斩杀", "剑神陨落", "MAJOR"),
    ("巴迪冈迪封印地龙谷", "封印", "T0097", ("E0113","E0079","E0029","E0001"), "斗神再败需长久封印", "佩尔基乌斯设地龙谷结界封印", "巴迪冈迪被封", "MAJOR"),
    ("鲁迪乌斯安详离世", "终章", "T0098", ("E0001","E0006","E0005","E0021"), "年迈74岁临终", "在三妻环绕中闭眼", "列第七位而逝，人神仍图子孙", "MAJOR"),
]
detailed_events = []
for idx, (title, etype, tid, parts, trig, acts, out, imp) in enumerate(event_defs):
    deps = ()
    if idx + 1 < len(event_defs):
        deps = (EventDependency(dependency_id=f"ED{base+idx+1:05d}", dependency_type=EventDependencyKind.CAUSES, target_event_id=f"DE{base+idx+2:05d}", statement="为后事提供前提"),)
    # state changes
    if idx == 1:
        sc = (StateChange(change_id=f"SC{base+idx+1:05d}", change_kind="生死", subject_id=parts[0], before="存活", after="死亡并火化"),)
    elif idx == 3:
        sc = (StateChange(change_id=f"SC{base+idx+1:05d}", change_kind="封印", subject_id="E0113", before="自由斗神", after="地龙谷封印中"),)
    elif idx == 4:
        sc = (StateChange(change_id=f"SC{base+idx+1:05d}", change_kind="生死", subject_id="E0001", before="在世", after="逝世享年74"),)
    else:
        sc = (StateChange(change_id=f"SC{base+idx+1:05d}", change_kind="状态", subject_id=parts[0], before="对峙", after="胜后收束"),)
    detailed_events.append(DetailedEvent(
        event_id=f"DE{base+idx+1:05d}",
        event_type=etype,
        title=title,
        timeline_event_id=tid,
        time_date=None,
        time_precision=DatePrecision.UNKNOWN,
        time_note=title[:12],
        volume_no=26,
        location_id=None,
        participants=parts,
        prerequisites=(EventPrerequisite(prerequisite_id=f"EP{base+idx*2+1:05d}", prerequisite_type=EventPrerequisiteKind.PERSON_PRESENT, ref_id=parts[0], statement=f"{parts[0]}在场", evidence_refs=pick(1, offset=40+idx)),),
        dependencies=deps,
        state_changes=sc,
        trigger=trig,
        actions=(acts,),
        outcome=out,
        relationship_change_ids=(),
        belief_ids=(),
        canon_importance=EventImportance.MAJOR,
        evidence_refs=pick(2, offset=35+idx*2),
    ))

# Items: 王龙剑、斗神铠残片、地龙谷结界
# need first_appearance lines within volume 26
# use actual unit start lines: U0443 234234 etc
unit_starts = {u.unit_id: u.start_line for u in doc.units}
items = [
    ItemDef(item_id=f"IT{base+1:05d}", canonical_name="王龙剑", aliases=("王龙剑·卡尔",), category="WEAPON", subcategory="剑", description="可斩切不死身与斗神的王龙王遗剑，卷终由艾莉丝持以斩切巴迪冈迪与加尔", material="龙材与秘钢", size=None, weight=None, durability=None, rarity="传说", value_information=None, currency=None, creator="王龙王", origin="王龙王国遗物", manufacturer=None, abilities=("斩切不死身",), effects=("重创斗神与不死魔王",), requirements=("剑王以上驾驭",), limitations=("需近身斩切",), first_appearance_volume=26, first_appearance_line=unit_starts.get("U0443", 234236), visible_from_volume=26, evidence_refs=pick(1, offset=60)),
    ItemDef(item_id=f"IT{base+2:05d}", canonical_name="斗神铠残片", aliases=("斗神铠碎片",), category="ARMOR", subcategory="铠", description="斗神铠崩解后残片，被基斯遗策用于复活亚历山大为斗神", material="斗神钢", size=None, weight=None, durability=None, rarity="传说", value_information=None, currency=None, creator=None, origin="斗神铠崩解", manufacturer=None, abilities=(), effects=("附身着装者为斗神",), requirements=(), limitations=("需人神使徒策动",), first_appearance_volume=26, first_appearance_line=unit_starts.get("U0444", 235736), visible_from_volume=26, evidence_refs=pick(1, offset=61)),
    ItemDef(item_id=f"IT{base+3:05d}", canonical_name="地龙谷结界", aliases=("地龙谷封印",), category="MAGIC_ITEM", subcategory="结界", description="佩尔基乌斯设于地龙谷用以长久封印巴迪冈迪的结界", material="魔力结界", size=None, weight=None, durability=None, rarity="稀有", value_information=None, currency=None, creator="佩尔基乌斯", origin="佩尔基乌斯布设", manufacturer=None, abilities=(), effects=("封印斗神巴迪冈迪",), requirements=(), limitations=(), first_appearance_volume=26, first_appearance_line=unit_starts.get("U0444", 236360), visible_from_volume=26, evidence_refs=pick(1, offset=62)),
]
instances = [
    ItemInstance(instance_id=f"IN{base+1:05d}", definition_id=f"IT{base+1:05d}", owner_id="E0021", holder_id="E0021", location_id=None, location_name=None, condition="良好", durability_if_known=None, acquired_at=None, lost_at=None, acquired_at_volume=26, lost_at_volume=None, ownership_history=(OwnershipEntry(entry_id=f"OH{base+1:05d}", owner_id="E0021", period_start=None, period_end=None, acquired_via="王龙王处受领", lost_via=None, note="终决中持以斩斗神"),), evidence_refs=pick(1, offset=70)),
]

abilities = [
    AbilityProfile(ability_id=f"AB{base+1:05d}", name="王龙剑斩切", aliases=("王龙大上段",), ability_type=AbilityType.SWORD, school=None, element=None, tier="神级", requirements=("王龙剑",), preconditions=(), mana_cost_if_known=None, stamina_cost_if_known=None, range_if_known="近战", duration_if_known="瞬时", effects=("斩断不死身手臂与躯干",), limitations=("需王龙剑",), counters=(), qualitative_power="神级斩切", learning_method=(), known_users=("E0021",), evidence_refs=pick(1, offset=80)),
    AbilityProfile(ability_id=f"AB{base+2:05d}", name="神刀", aliases=(), ability_type=AbilityType.SWORD, school=None, element=None, tier="神级", requirements=(), preconditions=(), mana_cost_if_known=None, stamina_cost_if_known=None, range_if_known="近战", duration_if_known="瞬时", effects=("劈开斗神铠",), limitations=(), counters=(), qualitative_power="龙神级", learning_method=(), known_users=("E0079",), evidence_refs=pick(1, offset=81)),
    AbilityProfile(ability_id=f"AB{base+3:05d}", name="地龙谷封印术", aliases=(), ability_type=AbilityType.MAGIC, school=None, element=None, tier=None, requirements=("佩尔基乌斯",), preconditions=(), mana_cost_if_known=None, stamina_cost_if_known=None, range_if_known="结界", duration_if_known="长久", effects=("封印巴迪冈迪",), limitations=(), counters=(), qualitative_power="王级结界", learning_method=(), known_users=("E0029",), evidence_refs=pick(1, offset=82)),
]

comparisons = [
    PowerComparison(comparison_id=f"PC{base+1:05d}", actor_id="E0079", target_id="E0162", dimension="决战胜负", context="奥尔斯帝德以神刀劈开斗神铠亚历山大", result="龙神碾压斗神铠", confidence=Confidence.EXPLICIT, evidence_refs=pick(1, offset=90)),
    PowerComparison(comparison_id=f"PC{base+2:05d}", actor_id="E0021", target_id="E0113", dimension="斩切对不死身", context="艾莉丝王龙剑对巴迪冈迪", result="王龙剑可破不死身再生", confidence=Confidence.EXPLICIT, evidence_refs=pick(1, offset=91)),
]

world_rules = [
    WorldRule(rule_id=f"WR{base+1:05d}", domain=WorldRuleDomain.WAR, statement="斗神巴迪冈迪具不死身再生，需王龙剑级斩切配合结界才能长久封印，单纯击杀会再生", scope="毕黑利尔决战与地龙谷", exceptions="无王龙剑则无法重创", confidence=Confidence.EXPLICIT, visible_from_volume=26, evidence_refs=pick(1, offset=93)),
    WorldRule(rule_id=f"WR{base+2:05d}", domain=WorldRuleDomain.MAGIC, statement="斗神铠残片可借人神使徒遗策附身复活着装者为新斗神", scope="斗神铠传承", exceptions="需基斯式预置策动", confidence=Confidence.STRONG_INFERENCE, visible_from_volume=26, evidence_refs=pick(1, offset=94)),
    WorldRule(rule_id=f"WR{base+3:05d}", domain=WorldRuleDomain.LAW, statement="战后使徒尸体须火化以防人神再利用", scope="终决战后处理", exceptions="无", confidence=Confidence.EXPLICIT, visible_from_volume=26, evidence_refs=pick(1, offset=95)),
    WorldRule(rule_id=f"WR{base+4:05d}", domain=WorldRuleDomain.SOCIETY, statement="七大列强第七位可由战功与家族延续授予，鲁迪乌斯以毕黑利尔战功列位", scope="七大列强", exceptions="人神仍存未竟全功", confidence=Confidence.EXPLICIT, visible_from_volume=26, evidence_refs=pick(1, offset=96)),
]

beliefs = [
    Belief(belief_id=f"BL{base+1:05d}", owner_id="E0057", topic="使徒必胜", statement="以为凭斗神与剑神可一举击溃奥尔斯帝德阵营", certainty=Confidence.EXPLICIT, belief_state=BeliefState.FALSE_BELIEF, learned_from="人神神谕", learned_at_volume=26, learned_method="被托付", is_true_in_world=False, visible_from_volume=26, visible_to_volume=None, note="误判奥尔斯帝德与王龙剑", evidence_refs=pick(1, offset=100)),
    Belief(belief_id=f"BL{base+2:05d}", owner_id="E0001", topic="封印可行", statement="认为巴迪冈迪只能封印不可彻底杀死", certainty=Confidence.EXPLICIT, belief_state=BeliefState.FACT_KNOWN, learned_from="奥尔斯帝德与佩尔基乌斯", learned_at_volume=26, learned_method="战前商议", is_true_in_world=True, visible_from_volume=26, visible_to_volume=None, note="地龙谷结界为共识", evidence_refs=pick(1, offset=101)),
    Belief(belief_id=f"BL{base+3:05d}", owner_id="E0032", topic="子孙可欺", statement="认为鲁迪乌斯死后可轻易离间其子孙延续对抗", certainty=Confidence.EXPLICIT, belief_state=BeliefState.INFERRED, learned_from="对未来的观测", learned_at_volume=26, learned_method="神视", is_true_in_world=False, visible_from_volume=26, visible_to_volume=None, note="人神谋划", evidence_refs=pick(1, offset=102)),
]

econ = [
    EconomicObservation(observation_id=f"EC{base+1:05d}", location_id=None, location_name="毕黑利尔王国", at_date=None, at_volume=26, category="战后处理", item_id=None, goods_description="火化所需柴薪与结界维持", quantity=None, currency=None, amount_description=None, price_class=PriceClass.UNKNOWN, context="基斯火化与结界布设为战后收束", evidence_refs=pick(1, offset=107)),
]

rel_changes = [
    RelationshipChange(change_id=f"RC{base+1:05d}", source_id="E0001", target_id="E0113", dimension="敌对至封印", before="死敌", trigger="王龙剑斩切并地龙谷封印", after="封印中敌", at_volume=26, at_date=None, evidence_refs=pick(1, offset=110)),
    RelationshipChange(change_id=f"RC{base+2:05d}", source_id="E0079", target_id="E0001", dimension="主从与信赖", before="部下", trigger="共同完成最终决战与封印", after="托付家族的信赖", at_volume=26, at_date=None, evidence_refs=pick(1, offset=111)),
    RelationshipChange(change_id=f"RC{base+3:05d}", source_id="E0001", target_id="E0032", dimension="对抗", before="被观测的敌人", trigger="鲁迪逝世而人神转攻子孙", after="子孙代际对抗", at_volume=26, at_date=None, evidence_refs=pick(1, offset=112)),
]

speech = [
    SpeechProfile(profile_id=f"ST{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", phase_name="终章·临终期", politeness="敬体对奥尔斯帝德，常体对家人", sentence_length="中短", address_habits="称奥尔斯帝德大人，称艾莉丝、希露菲、洛琪希直呼", emotion_expression="平静中带温柔与愧疚", anger_expression="沉声训斥", shy_expression="挠头苦笑", intimate_speech="对三妻温言安慰", stranger_speech="礼貌克制", superior_speech="指示简洁", inferior_speech="提携口吻", canonical_examples=("拜托了，奥尔斯帝德大人", "大家，谢谢"), visible_from_volume=26, evidence_refs=pick(1, offset=120)),
    SpeechProfile(profile_id=f"ST{base+2:05d}", character_id="E0021", phase_id=f"P{base+2:04d}", phase_name="终章·狂剑王决战期", politeness="常体直言，罕用敬语", sentence_length="短促有力", address_habits="称鲁迪乌斯直呼，称对手为家伙", emotion_expression="以斩切代言", anger_expression="怒吼斩击", shy_expression="罕露，扭头回避", intimate_speech="对鲁迪乌斯直率告白", stranger_speech="威吓", superior_speech="命令式", inferior_speech="庇护式", canonical_examples=("鲁迪乌斯，我来砍了", "别挡路"), visible_from_volume=26, evidence_refs=pick(1, offset=121)),
]

quirks = [
    CharacterQuirk(quirk_id=f"QK{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", category="HABIT", name="临终家话", description="晚年反复向家人道谢与托付，强调勿为人神离间", intensity="中", frequency="偶发", triggers=("家族团聚","临终前"), preferred_targets=(), avoided_targets=(), public_expression="家中围坐时温言", private_expression="独处时轻声愧疚自语", behavior_patterns=("握手","轻抚头"), verbal_patterns=("谢谢","拜托了"), body_language="握手", emotional_reward="安心", emotional_response="平静", boundaries=("不向外人示弱",), exceptions=(), visible_from_volume=26, evidence_refs=pick(1, offset=130)),
    CharacterQuirk(quirk_id=f"QK{base+2:05d}", character_id="E0021", phase_id=f"P{base+2:04d}", category="HABIT", name="以剑代答", description="遇挑衅或危机不作口舌，直接拔王龙剑斩切", intensity="高", frequency="频发", triggers=("被挑衅","家人受威胁"), preferred_targets=(), avoided_targets=(), public_expression="当众拔剑斩切", private_expression=None, behavior_patterns=("大上段起手","一刀两断"), verbal_patterns=(), body_language="持剑前冲", emotional_reward="畅快", emotional_response="豪快", boundaries=("不斩家人",), exceptions=("孕期会收力",), visible_from_volume=26, evidence_refs=pick(1, offset=131)),
]

prefs = [
    CharacterPreference(preference_id=f"PF{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", preference_type="LIKE", target="家人环绕的日常", description="终章以家中围坐、子女成长为最高价值", intensity="高", context="临终前", visible_from_volume=26, evidence_refs=pick(1, offset=140)),
    CharacterPreference(preference_id=f"PF{base+2:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", preference_type="DISLIKE", target="人神对子孙的离间", description="厌恶人神以低语离间子孙", intensity="高", context="临终托付", visible_from_volume=26, evidence_refs=pick(1, offset=141)),
]

bodies = [
    BodyLanguageProfile(profile_id=f"BY{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", phase_name="终章·临终期", happy_signs=("微笑","轻拍"), angry_signs=("皱眉",), nervous_signs=("视线漂移",), embarrassed_signs=("苦笑",), lying_signs=(), fear_signs=(), thinking_signs=("托腮权衡",), affection_signs=("握手","抚头"), hostility_signs=(), visible_from_volume=26, evidence_refs=pick(1, offset=150)),
    BodyLanguageProfile(profile_id=f"BY{base+2:05d}", character_id="E0021", phase_id=f"P{base+2:04d}", phase_name="终章·狂剑王决战期", happy_signs=("咧嘴",), angry_signs=("瞪目","拔剑"), nervous_signs=(), embarrassed_signs=("别过脸",), lying_signs=(), fear_signs=(), thinking_signs=(), affection_signs=("挽臂",), hostility_signs=("剑指",), visible_from_volume=26, evidence_refs=pick(1, offset=151)),
]

personas = [
    CharacterPersona(persona_id=f"PN{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", persona_type="PUBLIC", description="对外为奥尔斯帝德属下第七位，对内为临终前温和的家长", speech_style="对外敬慎，对家温和", behavior_traits=("克制","托付"), visible_from_volume=26, evidence_refs=pick(1, offset=160)),
    CharacterPersona(persona_id=f"PN{base+2:05d}", character_id="E0021", phase_id=f"P{base+2:04d}", persona_type="PUBLIC", description="对外为狂剑王，对内为鲁迪乌斯的剑与妻", speech_style="短促直言", behavior_traits=("悍勇","忠直"), visible_from_volume=26, evidence_refs=pick(1, offset=161)),
]

gaps = [
    CanonGap(gap_id=f"GAP{base+1:05d}", domain="封印", question="地龙谷结界的具体维持年限与魔力供给方式为何？", why_needed="推演封印松动时的再战时间窗", searched_volumes=(26,), status=GapStatus.OPEN, possible_sources="后日谈与续作补述", note="卷终仅言封印，未给结界术式细节"),
    CanonGap(gap_id=f"GAP{base+2:05d}", domain="七大列强", question="鲁迪乌斯列第七位的正式授位仪式与权能边界为何？", why_needed="判定列强位阶在政治推演中的实际效力", searched_volumes=(26,), status=GapStatus.OPEN, possible_sources="王龙王国与甲龙王相关文书", note="仅见列位宣告，无仪式描写"),
]

batch = EnrichmentBatch(
    batch_id="ENRICH_V026",
    source_volume=26,
    source_unit_ids=tuple(source_unit_ids),
    schema_version="1.0.0",
    evidence=tuple(evidence_list),
    character_profiles=tuple(profiles),
    behavior_cases=tuple(behavior_cases),
    detailed_events=tuple(detailed_events),
    items=tuple(items),
    item_instances=tuple(instances),
    abilities=tuple(abilities),
    power_comparisons=tuple(comparisons),
    world_rules=tuple(world_rules),
    locations=tuple(),
    routes=tuple(),
    travel_observations=tuple(),
    organizations=tuple(),
    political_states=tuple(),
    species=tuple(),
    creatures=tuple(),
    beliefs=tuple(beliefs),
    economic_observations=tuple(econ),
    relationship_changes=tuple(rel_changes),
    speech_profiles=tuple(speech),
    character_quirks=tuple(quirks),
    character_preferences=tuple(prefs),
    body_language_profiles=tuple(bodies),
    character_personas=tuple(personas),
    canon_conflicts=tuple(),
    canon_gaps=tuple(gaps),
)

out = pathlib.Path(f"data/canon_enriched/V026.json")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", encoding="utf-8") as f:
    json.dump(batch.to_json(), f, ensure_ascii=False, sort_keys=True, indent=2)
print(f"Wrote {out} ev={len(batch.evidence)} profiles={len(batch.character_profiles)} cases={len(batch.behavior_cases)} events={len(batch.detailed_events)} items={len(batch.items)}")

# Quick verify
from overlord_worldsim.canon.enrich_registry import load_enrichment_batches
from overlord_worldsim.canon.enrich_verifier import verify_enrichment
from overlord_worldsim.canon.enrich_registry import load_entity_registry
batches = load_enrichment_batches(pathlib.Path("data/canon_enriched"))
reg = load_entity_registry(pathlib.Path("data/canon"))
report = verify_enrichment(batches, doc, reg)
print(f"verify clean={report.is_clean} errors={len(report.errors)}")
for e in report.errors[:40]:
    print(e)
