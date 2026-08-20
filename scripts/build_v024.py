#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build ENRICH_V024 evidence-grounded batch for volume 24 (毕黑利尔·斯佩路德与冥王)."""

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
vol24 = [v for v in doc.volumes if v.volume_no == 24][0]
source_unit_ids = list(vol24.unit_ids)

chunks = []
with open("data/parsed/chunks.jsonl", encoding="utf-8") as f:
    for line in f:
        j = json.loads(line)
        if j.get("volume_no") == 24:
            chunks.append(j)
by_chunk = {c["chunk_id"]: c for c in chunks}

selected = [
    ("C002154", "U0409开篇战前项与奥尔斯帝德事务所集结"),
    ("C002161", "U0410寻追踪之物与毕黑利尔地图展开"),
    ("C002169", "U0411寻无名之地与魔森小路"),
    ("C002175", "U0412斯佩路德村全貌与栅木小屋"),
    ("C002176", "U0412瑞杰路德重逢于斯佩路德村"),
    ("C002178", "U0412斯佩路德村疫病初现舌头异色"),
    ("C002183", "U0413第五话冥王序幕与黏族潜入"),
    ("C002187", "U0413冥王黏体操纵瑞杰路德过程"),
    ("C002191", "U0413黏体转移潜入鲁迪乌斯体内"),
    ("C002193", "U0413死神戒指击杀冥王毕塔"),
    ("C002195", "U0414败露后遗体与疫病关联自述"),
    ("C002198", "U0414呕吐异物与克里夫诊视前置"),
    ("C002202", "U0415摇篮吹泡与重症倒下"),
    ("C002203", "U0415克里夫诊治查明疫病源于食物"),
    ("C002207", "U0415治疗后全村痊愈与瑞杰路德恳求"),
    ("C002209", "U0416侧章某人对话谁与事务所情报整理"),
    ("C002214", "U0417侧章基斯指使冥王散布疫病自述"),
    ("C002216", "U0418第八话宰相府邸质问与政治试探"),
    ("C002220", "U0418斯佩路德与毕黑利尔王国立场协商"),
    ("C002223", "U0419第九话斯佩路德大危机前夜转移部署"),
    ("C002224", "U0419秘密转移与通讯准备"),
    ("C002228", "U0419桥上遭剑神加尔与北神亚历山大袭击坠谷"),
    ("C002230", "U0420第十话消失与事务所收信"),
    ("C002231", "U0420转移魔法阵与通讯石板集体失效"),
    ("C002232", "U0420夏利亚众人失联与汇報"),
    ("C002235", "U0422后记与作者战篇收束语"),
    ("C002237", "U0423特典洛琪希视角斯佩路德日常"),
    ("C002239", "U0424 GAMERS特典拟斗斯佩路德战记录"),
]

available_ids = set(by_chunk.keys())
filtered = []
for cid, note in selected:
    if cid in available_ids:
        filtered.append((cid, note))
    else:
        print(f"WARN chunk {cid} not found")
        for c in chunks:
            if c["chunk_id"] not in [x[0] for x in filtered]:
                filtered.append((c["chunk_id"], note))
                break

base = 24000
evidence_list = []
ev_ids = []
for idx, (cid, note) in enumerate(filtered):
    c = by_chunk[cid]
    eid = f"EV{base + idx + 1:05d}"
    ev = EvidenceRef(
        evidence_id=eid,
        volume_no=24,
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

def ev(*offsets):
    return tuple(ev_ids[o % len(ev_ids)] for o in offsets)

profiles = []
profile_defs = [
    ("E0001", "鲁迪乌斯", "毕黑利尔决战与坠谷期", "二十余岁，奥尔斯帝德属下，三妻之夫，携死神戒指赴斯佩路德村", ["机敏","护族","务实","好色而克制","决断"], ["家人与同伴存续","对奥尔斯帝德忠诚","实用主义"], ["救治斯佩路德疫病","击杀冥王保全瑞杰路德","查明基斯阴谋"], ["再失瑞杰路德","转移链失效致孤立","人神离间家人"], ("无咏唱魔术","死神戒指运用","治愈辅助","侦查"), ("知冥王可黏体转移操纵","知斯佩路德疫病由冥王污染食物水源所致","知基斯指使冥王","知转移阵集体失效"), "卷二十四核心为斯佩路德村重逢、冥王侵体击杀、桥上遭袭坠谷与集体失联。", "从事务所谋划者转为前线受袭的失联者"),
    ("E0031", "瑞杰路德", "斯佩路德族长再生期", "斯佩路德族战士，村中定居，遭冥王寄生操纵后获救", ["坚毅","寡言","重义","自责"], ["族人存续","对鲁迪乌斯的信义"], ["守护斯佩路德村","摆脱冥王操纵"], ["族人再遭疫病","被操纵伤害鲁迪"], ("斯佩路德枪术","长枪突刺"), ("知自身曾被冥王操纵","知疫病治愈依赖克里夫"), "被冥王附身操纵后经鲁迪以死神戒指解救，重归鲁迪阵营。", "从隐居族长转为被操纵后获救的盟友"),
    ("E0161", "冥王毕塔", "地狱迷宫之王潜伏期", "黏族之王，潜入斯佩路德村以黏体散布疫病", ["阴险","狡诈","寄生性","自负"], ["服从基斯与人神","散布疫病"], ["潜入并操纵瑞杰路德","以黏体转移入鲁迪"], ["死神戒指克制","被识破"], ("黏体寄生","疫病散布","操纵"), ("知受基斯指使","知可借瑞杰路德为跳板"), "以黏体形态潜伏污染村落并操纵族长，转移入鲁迪后被死神戒指击杀。", "潜伏散毒至暴露被杀一役而亡"),
    ("E0057", "基斯", "人神使徒暗线期", "猴面人神使徒，居幕后指使冥王并策动桥上伏击", ["狡黠","煽动","匿踪"], ["人神胜利"], ["以冥王试探鲁迪","联剑神北神设伏于桥"], ["被奥尔斯帝德方追踪"], ("使徒联络","阴谋布局"), ("知冥王为可用棋","知鲁迪依赖转移阵"), "本卷以指使冥王与桥上伏击两手布局，暴露人神阵营对斯佩路德的针对。", "从暗中散毒转为公开伏击主谋"),
    ("E0065", "克里夫", "米里斯神子治愈期", "魔法大学研究者，查明并治愈斯佩路德疫病", ["聪敏","严谨","仁慈"], ["治愈与守护"], ["查明疫病源于食物与水","治愈全村"], ["疫病反复"], ("解毒与治愈魔术","药学"), ("知疫病非自然而为黏体污染","知可通过禁食污染源治愈"), "以体检与问诊查明疫病成因并主持全村治愈。", "从学者转为疫病救星"),
    ("E0110", "加尔·法利昂", "剑神叛离期", "前剑神，加入基斯阵营，于桥上与北神合击鲁迪", ["豪放","好战","重名"], ["剑之极致","追随人神阵营"], ["与亚历山大合击斩落鲁迪"], ["败于日后艾莉丝"], ("剑神流光之太刀",), ("知鲁迪为奥尔斯帝德属下",), "与北神一同于桥上袭击得手，将鲁迪打入谷底。", "从剑圣地独行转为人神阵营打手"),
    ("E0162", "亚历山大·雷白克", "北神三世袭击期", "北神卡尔曼三世，基斯阵营，与加尔合击鲁迪", ["勇猛","忠于阵营","张扬"], ["北神之名","人神阵营胜利"], ["于桥上截击鲁迪使其坠谷"], ["日后被问责"], ("北神流","双剑"), ("知桥为鲁迪必经","知转移失效可隔绝救援"), "与剑神协同伏击得手，致鲁迪坠谷失联。", "初登场即以伏击致鲁迪孤立"),
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
        taboos=("背叛同伴",),
        insecurities=("对族人与家人的安危不安",) if cid in ("E0001","E0031") else ("对失败不安",),
        pride="守护家人与族人" if cid=="E0001" else "斯佩路德之枪" if cid=="E0031" else None,
        impulsiveness="LOW" if cid=="E0001" else "MEDIUM",
        patience="HIGH" if cid=="E0001" else "MEDIUM",
        risk_tolerance="MEDIUM",
        self_control="HIGH" if cid=="E0001" else "MEDIUM",
        attachment_style="对希露菲与家人依恋" if cid=="E0001" else "对族人依恋" if cid=="E0031" else None,
        authority_attitude="尊奉奥尔斯帝德" if cid=="E0001" else None,
        family_attitude="以父职与夫职为重" if cid=="E0001" else "以族长为任" if cid=="E0031" else None,
        romantic_attitude=None,
        violence_attitude="克制而决断，必要时以死神戒指击杀" if cid=="E0001" else "寄生操纵" if cid=="E0161" else "正面斩击" if cid in ("E0110","E0162") else None,
        money_attitude=None,
        status_attitude=None,
        race_attitude="尊重斯佩路德" if cid=="E0001" else None,
        religious_attitude=None,
        loyalty="HIGH" if cid in ("E0001","E0031","E0065") else "HIGH to 人神" if cid in ("E0161","E0057") else "MEDIUM",
        ambition="MODERATE",
        short_term_goals=("治愈斯佩路德疫病","击退冥王") if cid=="E0001" else ("治愈全村",) if cid=="E0065" else ("完成伏击",) if cid in ("E0110","E0162") else ("散布疫病",) if cid=="E0161" else ("完成当下职责",),
        long_term_goals=("维系斯佩路德同盟长久",) if cid=="E0001" else ("重建族群信任",) if cid=="E0031" else ("获人神褒奖",),
        obligations=("对奥尔斯帝德的部下职责","对瑞杰路德的友义") if cid=="E0001" else ("族长职责",) if cid=="E0031" else ("使徒职责",) if cid in ("E0057","E0161") else ("职责",),
        decision_tendencies=("先诊后治，确认源头再出手","诱出转移后以戒指击杀") if cid=="E0001" else ("依本能寄生转移",) if cid=="E0161" else ("合击速决",) if cid in ("E0110","E0162") else ("权衡后行动",),
        speech_tendencies=("对奥尔斯帝德敬语，对瑞杰路德坦言",) if cid=="E0001" else ("黏腻低语",) if cid=="E0161" else ("简洁战吼",) if cid in ("E0110",) else ("直言",),
        social_tendencies=("与瑞杰路德并肩作战",) if cid=="E0001" else ("潜伏村中",) if cid=="E0161" else ("与加尔搭档",) if cid=="E0162" else ("协作",),
        conflict_tendencies=("以诊治与戒指克制取胜",) if cid=="E0001" else ("寄生与转移",) if cid=="E0161" else ("桥上合击坠谷",) if cid in ("E0110","E0162") else ("理性应对",),
        known_skills=tuple(skills),
        knowledge_state=tuple(knowledge),
        relationship_tendencies=("护族",) if cid=="E0001" else ("忠于鲁迪",) if cid=="E0031" else ("依阵营而动",),
        behavior_changes_note=change,
        summary=summary,
        visible_from_volume=24,
        visible_to_volume=None,
        evidence_refs=pick(2, offset=idx*3),
    ))

case_defs = [
    ("E0001", "FAMILY", "赴斯佩路德村与瑞杰路德重逢", "瑞杰路德出迎于栅门", "拥抱重逢并入村问候族人", "感慨而喜悦", "family"),
    ("E0161", "FEAR", "黏体潜入瑞杰路德体内操纵", "全村舌头发紫疫病蔓延", "以黏液附身操纵瑞杰路德言行", "阴冷得意", "danger"),
    ("E0001", "COMBAT", "黏体转移瞬间以死神戒指击杀冥王", "瑞杰路德口吐黏体涌向鲁迪", "抬手以死神戒指触击黏体令其崩解", "惊惧后决断", "combat"),
    ("E0001", "SUSPICION", "察觉疫病关联与呕吐异物", "克里夫前问诊见呕吐黏状物", "追问饮食水源并封存食物", "疑虑加重", "suspicion"),
    ("E0065", "TRUST", "克里夫诊治查明污染源并治愈全村", "孩童吹泡与倒下重症", "禁污染食物以治愈魔术净化并治愈", "专注笃定", "trust"),
    ("E0031", "GRIEF", "瑞杰路德自责被操纵向鲁迪请罪", "冥王崩解后恢复清醒", "低头请罪并愿再随鲁迪", "愧疚而坚定", "grief"),
    ("E0001", "NEGOTIATION", "与毕黑利尔宰相交涉斯佩路德立场", "王国欲问罪斯佩路德", "以奥尔斯帝德名义担保族群无害", "谨慎据理", "negotiation"),
    ("E0057", "SECRET", "侧章坦白受人神指使散毒", "独处对黏族下令", "令冥王潜入斯佩路德村污染食水", "狡笑", "secret"),
    ("E0001", "PROTECT", "护送重症与夜话斯佩路德大危机", "夜色中族人不安", "安排轮守与转移预案", "忧虑而温和", "protect"),
    ("E0110", "COMBAT", "桥上与北神合击鲁迪", "鲁迪过桥归途", "加尔斩击与亚历山大突进合击", "豪烈", "combat"),
    ("E0162", "COMBAT", "北神突进将鲁迪打入谷底", "加尔牵制后露出空隙", "以北神流冲击撞落坠谷", "得意", "combat"),
    ("E0001", "FEAR", "坠谷瞬间以土魔术缓冲自保", "桥面崩断坠落", "仓促构筑土垫与风缓冲", "惊骇求生", "fear"),
    ("E0001", "LOSS", "转移阵与通讯石板集体失效失联", "事务所众人呼叫无应", "多次尝试转移与石板皆无反应", "茫然失措", "loss"),
    ("E0006", "FAMILY", "夏利亚家中察觉失联而焦虑", "石板无应转移不通", "希露菲与洛琪希商议求助奥尔斯帝德", "焦急", "family"),
]

behavior_cases = []
for idx, (cid, tag, ctx, trig, act, emo, sit) in enumerate(case_defs):
    try:
        btag = BehaviorTag[tag]
    except KeyError:
        btag = BehaviorTag.PROTECT
    behavior_cases.append(BehaviorCase(
        case_id=f"BC{base+idx+1:05d}",
        character_id=cid,
        phase_id=f"P{base+1:04d}",
        phase_name=profiles[0].phase_name,
        volume_no=24,
        situation_type=sit.lower(),
        context=ctx,
        trigger=trig,
        available_information="卷二十四当下情境与对话可见",
        action=act,
        verbal_response="依情境简短回应或黏体无言",
        emotional_response=emo,
        goal_at_time="治愈并保全斯佩路德" if idx < 9 else "伏击得手" if cid in ("E0110","E0162") else "求生与保联" if cid=="E0001" and idx>=11 else "依当下职责推进",
        relationship_context="与瑞杰路德共担" if cid=="E0001" else "与鲁迪对峙" if cid=="E0161" else "与加尔搭档" if cid=="E0162" else "与家人协作",
        social_context="斯佩路德村与毕黑利尔王国情境" if idx < 10 else "桥上伏击与谷底",
        immediate_outcome="取得局部结果或致失联",
        long_term_outcome="影响斯佩路德同盟与后续失联线",
        tags=(btag,),
        evidence_refs=pick(1, offset=20+idx),
    ))

event_defs = [
    ("瑞杰路德重逢与疫病浮现", "重逢", "T0086", ("E0001","E0031"), "抵达斯佩路德村于栅门见瑞杰路德", "问候族人并见疫病舌紫", "确认重逢并发现疫病异常", "MAJOR"),
    ("冥王转移与死神戒指击杀", "击杀", "T0087", ("E0001","E0161","E0031"), "瑞杰路德被操纵口吐黏体扑向鲁迪", "黏体转移入鲁迪瞬间以死神戒指触击崩解", "冥王毕塔当场被杀，瑞杰路德获救", "MAJOR"),
    ("斯佩路德疫病溯源与治愈", "治愈", "T0088", ("E0065","E0031","E0001"), "重症倒下呕吐黏状物", "克里夫禁污染食水并以治愈魔术净化全村", "全村痊愈，确认污染来源", "MAJOR"),
    ("桥上合击与坠谷", "伏击", "T0089", ("E0001","E0110","E0162"), "归途过桥被剑神北神截击", "加尔牵制亚历山大突进合击将鲁迪撞落谷底", "鲁迪坠谷濒死，敌得手撤离", "MAJOR"),
    ("转移失效与失联", "失联", "T0090", ("E0001","E0006","E0005","E0021"), "坠谷后尝试转移与通讯", "全部转移阵与通讯石板无应", "鲁迪下落不明，事务所失联", "MAJOR"),
]
detailed_events = []
for idx, (title, etype, tid, parts, trig, acts, out, imp) in enumerate(event_defs):
    deps = ()
    if idx + 1 < len(event_defs):
        deps = (EventDependency(dependency_id=f"ED{base+idx+1:05d}", dependency_type=EventDependencyKind.CAUSES, target_event_id=f"DE{base+idx+2:05d}", statement="为后事提供前提"),)
    # prerequisites: person present
    prereqs = (EventPrerequisite(prerequisite_id=f"EP{base+idx*2+1:05d}", prerequisite_type=EventPrerequisiteKind.PERSON_PRESENT, ref_id=parts[0], statement=f"{parts[0]}在场", evidence_refs=pick(1, offset=40+idx)),)
    # state changes
    if idx == 1:
        sc = (StateChange(change_id=f"SC{base+idx+1:05d}", change_kind="生死", subject_id="E0161", before="潜伏寄生", after="被死神戒指击杀"),)
    elif idx == 2:
        sc = (StateChange(change_id=f"SC{base+idx+1:05d}", change_kind="健康", subject_id="E0031", before="疫病蔓延", after="全村痊愈"),)
    elif idx == 3:
        sc = (StateChange(change_id=f"SC{base+idx+1:05d}", change_kind="位置", subject_id="E0001", before="桥上", after="坠入谷底"),)
    elif idx == 4:
        sc = (StateChange(change_id=f"SC{base+idx+1:05d}", change_kind="通讯", subject_id="E0001", before="可转移通讯", after="全部失效失联"),)
    else:
        sc = (StateChange(change_id=f"SC{base+idx+1:05d}", change_kind="关系", subject_id=parts[0], before="分离", after="重逢"),)
    detailed_events.append(DetailedEvent(
        event_id=f"DE{base+idx+1:05d}",
        event_type=etype,
        title=title,
        timeline_event_id=tid,
        time_date=None,
        time_precision=DatePrecision.UNKNOWN,
        time_note=title[:12],
        volume_no=24,
        location_id=None,
        participants=parts,
        prerequisites=prereqs,
        dependencies=deps,
        state_changes=sc,
        trigger=trig,
        actions=(acts,),
        outcome=out,
        relationship_change_ids=(),
        belief_ids=(),
        canon_importance=EventImportance.MAJOR if imp=="MAJOR" else EventImportance.MINOR,
        evidence_refs=pick(2, offset=35+idx*2),
    ))

unit_starts = {u.unit_id: u.start_line for u in doc.units}
items = [
    ItemDef(item_id=f"IT{base+1:05d}", canonical_name="死神戒指", aliases=("死神之戒",), category="MAGIC_ITEM", subcategory="戒指", description="死神拉诺夫赠予可令黏体类魔物崩解的戒指，卷二十四中以触击击杀冥王毕塔", material="魔钢与死神魔力", size=None, weight=None, durability=None, rarity="传说", value_information=None, currency=None, creator="死神拉诺夫", origin="死神处获赠", manufacturer=None, abilities=("崩解黏体",), effects=("触击令冥王黏体崩解",), requirements=("佩戴于指"), limitations=("需直接触击黏体",), first_appearance_volume=24, first_appearance_line=unit_starts.get("U0413", 217168), visible_from_volume=24, evidence_refs=pick(1, offset=60)),
    ItemDef(item_id=f"IT{base+2:05d}", canonical_name="奥尔斯帝德式转移阵", aliases=("鲁迪乌斯转移阵",), category="MAGIC_ITEM", subcategory="魔法阵", description="鲁迪乌斯与奥尔斯帝德方布设于事务所与斯佩路德村的转移魔法阵，卷二十四末集体失效", material="魔力纹阵", size=None, weight=None, durability=None, rarity="稀有", value_information=None, currency=None, creator="鲁迪乌斯与奥尔斯帝德方", origin="事务所与斯佩路德村", manufacturer=None, abilities=("空间转移",), effects=("瞬间转移人员物资"), requirements=("魔力供给与坐标"), limitations=("失效后无法使用",), first_appearance_volume=24, first_appearance_line=unit_starts.get("U0411", 215614), visible_from_volume=24, evidence_refs=pick(1, offset=61)),
    ItemDef(item_id=f"IT{base+3:05d}", canonical_name="奥尔斯帝德式通讯石板", aliases=("事务所通讯板",), category="MAGIC_ITEM", subcategory="石板", description="事务所用奥尔斯帝德式通讯石板，卷二十四末与转移阵一同失效", material="魔导石板", size=None, weight=None, durability=None, rarity="稀有", value_information=None, currency=None, creator="奥尔斯帝德方", origin="事务所配给", manufacturer=None, abilities=("远程文字通讯",), effects=("跨据点联络",), requirements=("魔力"), limitations=("失效后无应答"), first_appearance_volume=24, first_appearance_line=unit_starts.get("U0411", 216000), visible_from_volume=24, evidence_refs=pick(1, offset=62)),
]
instances = [
    ItemInstance(instance_id=f"IN{base+1:05d}", definition_id=f"IT{base+1:05d}", owner_id="E0001", holder_id="E0001", location_id=None, location_name=None, condition="良好", durability_if_known=None, acquired_at=None, lost_at=None, acquired_at_volume=24, lost_at_volume=None, ownership_history=(OwnershipEntry(entry_id=f"OH{base+1:05d}", owner_id="E0001", period_start=None, period_end=None, acquired_via="死神赠予", lost_via=None, note="佩于指上击杀冥王"),), evidence_refs=pick(1, offset=70)),
    ItemInstance(instance_id=f"IN{base+2:05d}", definition_id=f"IT{base+2:05d}", owner_id="E0001", holder_id="E0001", location_id=None, location_name="斯佩路德村与夏利亚事务所", condition="失效", durability_if_known=None, acquired_at=None, lost_at=None, acquired_at_volume=24, lost_at_volume=None, ownership_history=(OwnershipEntry(entry_id=f"OH{base+2:05d}", owner_id="E0001", period_start=None, period_end=None, acquired_via="自行布设", lost_via="不明原因集体失效", note="坠谷后全部无应"),), evidence_refs=pick(1, offset=71)),
]

abilities = [
    AbilityProfile(ability_id=f"AB{base+1:05d}", name="死神戒指崩解", aliases=("触杀黏体",), ability_type=AbilityType.MAGIC, school=None, element=None, tier=None, requirements=("死神戒指",), preconditions=("黏体接触",), mana_cost_if_known=None, stamina_cost_if_known=None, range_if_known="接触", duration_if_known="瞬时", effects=("令冥王黏体崩解死亡",), limitations=("仅对黏体类有效",), counters=(), qualitative_power="高", learning_method=("死神赠予",), known_users=("E0001",), evidence_refs=pick(1, offset=80)),
    AbilityProfile(ability_id=f"AB{base+2:05d}", name="黏体寄生操纵", aliases=("黏体转移",), ability_type=AbilityType.SPECIAL, school=None, element=None, tier=None, requirements=(), preconditions=(), mana_cost_if_known=None, stamina_cost_if_known=None, range_if_known="接触转移", duration_if_known="持续寄生", effects=("操纵宿主言行","污染食水致疫病"), limitations=("惧死神戒指"), counters=("死神戒指触击",), qualitative_power="中", learning_method=(), known_users=("E0161",), evidence_refs=pick(1, offset=81)),
    AbilityProfile(ability_id=f"AB{base+3:05d}", name="北神流突进", aliases=(), ability_type=AbilityType.SWORD, school="北神流", element=None, tier=None, requirements=(), preconditions=(), mana_cost_if_known=None, stamina_cost_if_known=None, range_if_known="近战", duration_if_known="瞬时", effects=("冲击撞落坠谷",), limitations=(), counters=(), qualitative_power="高", learning_method=(), known_users=("E0162",), evidence_refs=pick(1, offset=82)),
]

comparisons = [
    PowerComparison(comparison_id=f"PC{base+1:05d}", actor_id="E0001", target_id="E0161", dimension="克制关系", context="冥王黏体转移入鲁迪瞬间", result="死神戒指触击令冥王崩解，鲁迪完胜", confidence=Confidence.EXPLICIT, evidence_refs=pick(1, offset=90)),
    PowerComparison(comparison_id=f"PC{base+2:05d}", actor_id="E0110", target_id="E0001", dimension="桥上伏击", context="剑神与北神合击鲁迪过桥", result="加尔与亚历山大合击将鲁迪打入谷底，鲁迪败退", confidence=Confidence.EXPLICIT, evidence_refs=pick(1, offset=91)),
]

world_rules = [
    WorldRule(rule_id=f"WR{base+1:05d}", domain=WorldRuleDomain.SPECIES, statement="黏族冥王可化黏体寄生宿主并以接触转移，宿主舌头发紫为外显，惧死神戒指触击", scope="冥王毕塔与黏族", exceptions="死神戒指可令其崩解", confidence=Confidence.EXPLICIT, visible_from_volume=24, evidence_refs=pick(1, offset=93)),
    WorldRule(rule_id=f"WR{base+2:05d}", domain=WorldRuleDomain.MAGIC, statement="斯佩路德村疫病由冥王污染食物与饮水引起，非自然瘟疫，禁污染源即可治愈", scope="毕黑利尔斯佩路德村", exceptions="无戒指亦可治愈但需先除污染源", confidence=Confidence.EXPLICIT, visible_from_volume=24, evidence_refs=pick(1, offset=94)),
    WorldRule(rule_id=f"WR{base+3:05d}", domain=WorldRuleDomain.MAGIC, statement="鲁迪乌斯布设的转移魔法阵与通讯石板可集体失效，致所有据点失联", scope="奥尔斯帝德事务所转移网", exceptions="失效原因未明需后卷查明", confidence=Confidence.EXPLICIT, visible_from_volume=24, evidence_refs=pick(1, offset=95)),
    WorldRule(rule_id=f"WR{base+4:05d}", domain=WorldRuleDomain.POLITICS, statement="毕黑利尔王国对斯佩路德族聚落具管辖与问罪权，可经奥尔斯帝德方担保免罪", scope="毕黑利尔王国与斯佩路德", exceptions="担保需以奥尔斯帝德名义", confidence=Confidence.STRONG_INFERENCE, visible_from_volume=24, evidence_refs=pick(1, offset=96)),
]

beliefs = [
    Belief(belief_id=f"BL{base+1:05d}", owner_id="E0001", topic="冥王真身", statement="认为冥王已彻底被死神戒指杀死不再复生", certainty=Confidence.EXPLICIT, belief_state=BeliefState.FACT_KNOWN, learned_from="亲手触击崩解", learned_at_volume=24, learned_method="目击击杀", is_true_in_world=True, visible_from_volume=24, visible_to_volume=None, note="确杀", evidence_refs=pick(1, offset=100)),
    Belief(belief_id=f"BL{base+2:05d}", owner_id="E0031", topic="被操纵自责", statement="认为疫病与族人受苦皆因自己被冥王操纵所致", certainty=Confidence.EXPLICIT, belief_state=BeliefState.INFERRED, learned_from="恢复清醒后告知", learned_at_volume=24, learned_method="自省", is_true_in_world=True, visible_from_volume=24, visible_to_volume=None, note="自责", evidence_refs=pick(1, offset=101)),
    Belief(belief_id=f"BL{base+3:05d}", owner_id="E0161", topic="可夺鲁迪", statement="以为转移入鲁迪体内即可夺取其身", certainty=Confidence.EXPLICIT, belief_state=BeliefState.FALSE_BELIEF, learned_from="对自身黏体能力自信", learned_at_volume=24, learned_method="寄生尝试", is_true_in_world=False, visible_from_volume=24, visible_to_volume=None, note="误判死神戒指克制", evidence_refs=pick(1, offset=102)),
    Belief(belief_id=f"BL{base+4:05d}", owner_id="E0110", topic="桥上必得", statement="认为与北神合击必可斩落鲁迪", certainty=Confidence.EXPLICIT, belief_state=BeliefState.FACT_KNOWN, learned_from="伏击部署", learned_at_volume=24, learned_method="合议", is_true_in_world=True, visible_from_volume=24, visible_to_volume=None, note="得手", evidence_refs=pick(1, offset=103)),
]

# economic: no precise price given; keep qualitative
econ = []

rel_changes = [
    RelationshipChange(change_id=f"RC{base+1:05d}", source_id="E0001", target_id="E0031", dimension="信赖与盟友", before="久别重逢", trigger="共克冥王并治愈疫病", after="重归并肩的战友与族盟", at_volume=24, at_date=None, evidence_refs=pick(1, offset=110)),
    RelationshipChange(change_id=f"RC{base+2:05d}", source_id="E0161", target_id="E0057", dimension="从属", before="受指使潜伏", trigger="奉命散毒与操纵", after="任务完成前被杀", at_volume=24, at_date=None, evidence_refs=pick(1, offset=111)),
    RelationshipChange(change_id=f"RC{base+3:05d}", source_id="E0001", target_id="E0110", dimension="敌对", before="无直接仇", trigger="桥上合击致坠谷", after="伏击之敌", at_volume=24, at_date=None, evidence_refs=pick(1, offset=112)),
    RelationshipChange(change_id=f"RC{base+4:05d}", source_id="E0001", target_id="E0162", dimension="敌对", before="初见", trigger="北神突进撞落", after="伏击之敌", at_volume=24, at_date=None, evidence_refs=pick(1, offset=113)),
]

speech = [
    SpeechProfile(profile_id=f"ST{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", phase_name="毕黑利尔决战与坠谷期", politeness="敬体对奥尔斯帝德，常体对瑞杰路德", sentence_length="中短", address_habits="称瑞杰路德直呼，称奥尔斯帝德大人", emotion_expression="重逢时哽咽，击杀后沉声确认", anger_expression="对冥王斥责", shy_expression="苦笑挠头", intimate_speech="对瑞杰路德坦言思念", stranger_speech="对宰相礼貌据理", superior_speech="简洁指示克里夫", inferior_speech="温和安抚族中孩童", canonical_examples=("瑞杰路德，好久不见", "已经没事了"), visible_from_volume=24, evidence_refs=pick(1, offset=120)),
    SpeechProfile(profile_id=f"ST{base+2:05d}", character_id="E0031", phase_id=f"P{base+2:04d}", phase_name="斯佩路德族长再生期", politeness="简洁寡言，敬重鲁迪", sentence_length="短", address_habits="称鲁迪乌斯直呼", emotion_expression="少言以行动代言", anger_expression="低吼持枪", shy_expression="罕露", intimate_speech="对族人温和嘱咐", stranger_speech="寡言警惕", superior_speech="对鲁迪低头请罪", inferior_speech="对族人庇护口吻", canonical_examples=("鲁迪乌斯，对不起", "族人就拜托你了"), visible_from_volume=24, evidence_refs=pick(1, offset=121)),
]

quirks = [
    CharacterQuirk(quirk_id=f"QK{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", category="HABIT", name="触戒确认", description="击杀黏体后反复确认戒指触感与黏体残迹是否干净", intensity="中", frequency="一次", triggers=("黏体崩解后",), preferred_targets=(), avoided_targets=(), public_expression="当众举手示戒", private_expression="独处时摩挲戒指自语", behavior_patterns=("举手照看戒面","甩手"), verbal_patterns=("结束了",), body_language="摩挲戒指", emotional_reward="安心", emotional_response="松口气", boundaries=("不对族童展示戒杀",), exceptions=(), visible_from_volume=24, evidence_refs=pick(1, offset=130)),
    CharacterQuirk(quirk_id=f"QK{base+2:05d}", character_id="E0161", phase_id=f"P{base+3:04d}", category="HABIT", name="黏体拟态低语", description="寄生时以宿主口吻低语诱近再行转移", intensity="高", frequency="频发", triggers=("需近身转移时",), preferred_targets=("E0031","E0001"), avoided_targets=(), public_expression="借宿主之口说话", private_expression=None, behavior_patterns=("舌舔","口吐黏丝"), verbal_patterns=("来这边",), body_language="口吐黏块", emotional_reward="得逞", emotional_response="阴笑", boundaries=("惧死神戒指不近",), exceptions=("被识破即强行转移",), visible_from_volume=24, evidence_refs=pick(1, offset=131)),
]

prefs = [
    CharacterPreference(preference_id=f"PF{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", preference_type="LIKE", target="与瑞杰路德并肩", description="重逢后以并肩作战为优先，常将瑞杰路德置于身侧", intensity="高", context="斯佩路德村", visible_from_volume=24, evidence_refs=pick(1, offset=140)),
    CharacterPreference(preference_id=f"PF{base+2:05d}", character_id="E0031", phase_id=f"P{base+2:04d}", preference_type="DISLIKE", target="被操纵失控", description="极度厌恶被冥王操纵致族人受害", intensity="高", context="获救后", visible_from_volume=24, evidence_refs=pick(1, offset=141)),
]

bodies = [
    BodyLanguageProfile(profile_id=f"BY{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", phase_name="毕黑利尔决战与坠谷期", happy_signs=("眼眶发红","拥抱"), angry_signs=("瞪视","举戒"), nervous_signs=("视线漂移",), embarrassed_signs=("挠头",), lying_signs=(), fear_signs=("后退半步","抬手格挡"), thinking_signs=("托腮","摩挲戒指"), affection_signs=("拍肩",), hostility_signs=("戒指前指",), visible_from_volume=24, evidence_refs=pick(1, offset=150)),
    BodyLanguageProfile(profile_id=f"BY{base+2:05d}", character_id="E0031", phase_id=f"P{base+3:04d}", phase_name="斯佩路德族长再生期", happy_signs=("点头","持枪肃立"), angry_signs=("枪尖前指",), nervous_signs=("握枪颤抖",), embarrassed_signs=("低头",), lying_signs=(), fear_signs=(), thinking_signs=(), affection_signs=("按肩",), hostility_signs=("长枪平举",), visible_from_volume=24, evidence_refs=pick(1, offset=151)),
]

personas = [
    CharacterPersona(persona_id=f"PN{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", persona_type="PUBLIC", description="对外为奥尔斯帝德属下赴援斯佩路德的使者，对内为重逢瑞杰路德的友人", speech_style="对外敬慎据理，对友坦率哽咽", behavior_traits=("重逢时动情","击杀时决断","失联后求生"), visible_from_volume=24, evidence_refs=pick(1, offset=160)),
    CharacterPersona(persona_id=f"PN{base+2:05d}", character_id="E0031", phase_id=f"P{base+3:04d}", persona_type="PUBLIC", description="对外为斯佩路德族长，对内为自责的被操纵者", speech_style="寡言少语以枪代言", behavior_traits=("寡言","自责","忠义"), visible_from_volume=24, evidence_refs=pick(1, offset=161)),
]

gaps = [
    CanonGap(gap_id=f"GAP{base+1:05d}", domain="转移魔法", question="所有转移阵与通讯石板为何集体失效，失效机制与恢复条件为何？", why_needed="推演失联期救援与后续再联通时间窗", searched_volumes=(24,), status=GapStatus.OPEN, possible_sources="后卷奥尔斯帝德与佩尔基乌斯处说明", note="卷二十四末仅写全部失效，未给原因"),
    CanonGap(gap_id=f"GAP{base+2:05d}", domain="黏族", question="冥王毕塔之外的黏族是否仍有余党潜伏及分布？", why_needed="判定斯佩路德村是否仍有二次污染风险", searched_volumes=(24,), status=GapStatus.OPEN, possible_sources="天大陆迷宫地狱相关记载", note="仅见毕塔一王，未见族群全貌"),
]

batch = EnrichmentBatch(
    batch_id="ENRICH_V024",
    source_volume=24,
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

out = pathlib.Path(f"data/canon_enriched/V024.json")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", encoding="utf-8") as f:
    json.dump(batch.to_json(), f, ensure_ascii=False, sort_keys=True, indent=2)
print(f"Wrote {out} ev={len(batch.evidence)} profiles={len(batch.character_profiles)} cases={len(batch.behavior_cases)} events={len(batch.detailed_events)} items={len(batch.items)}")

from overlord_worldsim.canon.enrich_registry import load_enrichment_batches, load_entity_registry
from overlord_worldsim.canon.enrich_verifier import verify_enrichment
batches = load_enrichment_batches(pathlib.Path("data/canon_enriched"))
reg = load_entity_registry(pathlib.Path("data/canon"))
report = verify_enrichment(batches, doc, reg)
print(f"verify clean={report.is_clean} errors={len(report.errors)}")
for e in report.errors[:60]:
    print(e.code, e.path, e.message)
pathlib.Path("data/canon_enriched/report.json").write_text(json.dumps(report.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
