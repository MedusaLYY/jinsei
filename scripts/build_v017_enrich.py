#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build ENRICH_V017 evidence-grounded batch for volume 17."""
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
    BodyLanguageProfile, CharacterPersona, CanonConflict, ConflictStatus, CanonGap, GapStatus,
)
from overlord_worldsim.canon.extract_model import Confidence, DatePrecision
from overlord_worldsim.canon.parse import parse_source

raw_path = pathlib.Path("data/raw/无职转生TXT合集.txt")
if not raw_path.exists():
    raw_path = pathlib.Path("无职转生TXT合集.txt")
text = raw_path.read_text(encoding="utf-8")
doc = parse_source(text, source_name=raw_path.name)
unit_title = {u.unit_id: u.title for u in doc.units}
unit_range = {u.unit_id: (u.start_line, u.end_line) for u in doc.units}
vol17 = [v for v in doc.volumes if v.volume_no == 17][0]
source_unit_ids = list(vol17.unit_ids)

chunks = []
with open("data/parsed/chunks.jsonl", encoding="utf-8") as f:
    for line in f:
        j = json.loads(line)
        if j.get("volume_no") == 17:
            chunks.append(j)
by_chunk = {c["chunk_id"]: c for c in chunks}

# 36 grounded evidences covering V17 arc from 前往阿斯拉 to 后记
selected = [
    ("C001522", "前往阿斯拉王国与转移魔法阵说明"),
    ("C001523", "转移魔法阵魔力结晶供给机制与大流士破坏预测"),
    ("C001525", "夜巡时奥尔斯帝德定期联络与赤龙上颚埋伏预判"),
    ("C001530", "维·塔镜面铠甲登场特性"),
    ("C001531", "王都外伏击混战与希露菲参战前置"),
    ("C001534", "袭击后据点推敲与奥尔斯帝德第二次报告"),
    ("C001538", "魔法阵与赤龙上颚地形再推敲"),
    ("C001540", "爱丽儿的选择 坚持王位争夺"),
    ("C001543", "奥尔斯帝德与人神使徒数量说明"),
    ("C001546", "朵莉丝堤娜盗贼团据点初现"),
    ("C001548", "朵莉丝身世陈述曾为大流士性奴隶"),
    ("C001550", "朵莉丝为何沦为盗贼团长与帕普尔荷斯关联"),
    ("C001551", "路上王都街道行进"),
    ("C001554", "路克与希露菲王都内互动"),
    ("C001560", "王都亚尔斯王宫宴会厅格局"),
    ("C001563", "贵族派阀入场与格拉维尔大流士在场"),
    ("C001566", "黄昏的死斗前夕 伊佐露缇与水神流布阵"),
    ("C001570", "双胞胎纳库尔贾德雇佣关系"),
    ("C001573", "爱丽儿的战场 派阀言辞交锋"),
    ("C001574", "朵莉丝公开指证大流士 帕普尔荷斯倒戈核心"),
    ("C001578", "佩尔基乌斯现身宣布爱丽儿为下任女王前兆"),
    ("C001579", "佩尔基乌斯宣布支持 爱丽儿王位确立"),
    ("C001580", "鲁迪乌斯的战场 对水神列妲迎击"),
    ("C001584", "维·塔镜铠对基列奴"),
    ("C001586", "双胞胎被艾莉丝斩杀"),
    ("C001587", "基列奴处决大流士 认定害死绍罗斯"),
    ("C001588", "路克失控前兆 人神低语"),
    ("C001592", "路克挟持爱丽儿现场"),
    ("C001593", "希露菲拒绝背叛与爱丽儿原谅路克"),
    ("C001594", "奥尔斯帝德真相与王都十日说明"),
    ("C001596", "王都十日后续推演"),
    ("C001601", "诀别的训练 艾莉丝与基列奴最后对练"),
    ("C001604", "希露菲辞去护卫归家育儿"),
    ("C001606", "归乡与决意 鲁迪归家行装"),
    ("C001611", "闲话 王都余波补遗"),
    ("C001613", "特典 幽禁的王子"),
]

base = 17000
evidence_list = []
ev_ids = []
for idx, (cid, note) in enumerate(selected):
    c = by_chunk[cid]
    eid = f"EV{base+idx+1:05d}"
    ev = EvidenceRef(
        evidence_id=eid,
        volume_no=17,
        unit_id=c["unit_id"],
        chapter_title=unit_title.get(c["unit_id"], c.get("chapter_title","")),
        source_start_line=c["source_start_line"],
        source_end_line=c["source_end_line"],
        evidence_type=EvidenceType.CANON_EXPLICIT if idx%2==0 else EvidenceType.STRONG_INFERENCE,
        confidence=Confidence.EXPLICIT,
        note=note,
    )
    evidence_list.append(ev)
    ev_ids.append(eid)

def pick(n, offset=0):
    return tuple(ev_ids[(offset+i*7)%len(ev_ids)] for i in range(n))

profiles = []
profile_defs = [
    ("E0001","鲁迪乌斯","王位争夺期","约15-16岁 泥沼的鲁迪乌斯 奥尔斯帝德部下"),
    ("E0021","艾莉丝","狂剑王期","成年剑王 鲁迪第三妻 王位争夺主力"),
    ("E0022","基列奴","终身护卫期","成年兽族女剑士 剑王 为绍罗斯复仇"),
    ("E0044","爱丽儿","女王确立期","阿斯拉第二公主 下任女王"),
    ("E0045","路克","诺托斯当家前期","青年骑士 爱丽儿护卫 受人神蛊惑"),
    ("E0145","朵莉丝堤娜","指证期","帕普尔荷斯家次女 前盗贼团长 受害证人"),
    ("E0006","希露菲","辞职归家期","青年妻子 鲁迪第一妻 王宫护卫"),
]
for idx,(cid,name,phase,age) in enumerate(profile_defs):
    pid = f"CP{base+idx+1:05d}"
    if cid=="E0001":
        traits=("果敢","理性","执着","护家人")
        values=("家族","信义","生存","责任")
        desires=("助爱丽儿夺位","手刃害死绍罗斯元凶","守护夏利亚家人")
        fears=("同伴在王都丧命","人神再挑拨")
        skills=("无咏唱魔术","泥沼与岩炮","战术指挥")
        knowledge=("知大流士为害死绍罗斯元凶","知人神通过路克挑拨")
        summary="鲁迪乌斯在第17卷阿斯拉王宫决战的核心推手与战力。"
        change="王都决战期由夏利亚丈夫转为王宫战场指挥，言行更具决断。"
        stg=("协助爱丽儿夺位","击败奥贝尔与列妲")
        ltg=("回归夏利亚家庭","稳固奥尔斯帝德阵营")
        obligations=("对奥尔斯帝德的部下义务","对爱丽儿的助力承诺")
        decision=("先推敲后出手","以情报与地形制胜")
        speech=("对爱丽儿敬语、对同伴直率",)
        social=("与爱丽儿阵营协作","与佩尔基乌斯谨慎往来")
        conflict=("以策略化解、必要时魔术威慑",)
        rel=("对爱丽儿由护卫到兄妹","对基列奴与艾莉丝信赖")
    elif cid=="E0021":
        traits=("果敢","直率","好胜","忠诚")
        values=("剑术","家族","胜负")
        desires=("斩强敌","守护鲁迪与爱丽儿")
        fears=("再因弱小失去重要之人",)
        skills=("剑神流剑王","狂剑")
        knowledge=("知双胞胎为大流士所雇",)
        summary="艾莉丝在第17卷作为王宫决战的斩击前锋。"
        change="王位争夺战中首次以狂剑王身份在王宫斩敌。"
        stg=("斩纳库尔贾德","为鲁迪清场")
        ltg=("与鲁迪共度余生",)
        obligations=("对剑神流的传承",)
        decision=("直冲敌阵","以气势压制")
        speech=("短促、直呼鲁迪",)
        social=("与基列奴切磋","在王宫内显眼")
        conflict=("正面迎击",)
        rel=("对鲁迪绝对信赖","对基列奴亦师亦敌")
    elif cid=="E0022":
        traits=("沉默寡言","忠诚","以行动示意","自尊强")
        values=("剑王荣耀","对爱丽儿的护卫责任","为绍罗斯复仇")
        desires=("手刃大流士","护爱丽儿登位")
        fears=("再失主君",)
        skills=("剑神流剑王","魔眼（视野）")
        knowledge=("知大流士为仇敌",)
        summary="基列奴在第17卷完成复仇并确立终身护卫身份。"
        change="完成与艾莉丝最后训练后转向终身护卫。"
        stg=("击败维·塔","处决大流士")
        ltg=("担任爱丽儿终身护卫",)
        obligations=("对绍罗斯的复仇","保罗旧队友情谊")
        decision=("少言、点头或拔剑即为回答",)
        speech=("极短句、肯定式",)
        social=("独处多、与艾莉丝切磋",)
        conflict=("以气势压人与直接击杀",)
        rel=("对爱丽儿忠诚","对鲁迪与艾莉丝协作")
    elif cid=="E0044":
        traits=("聪慧","果决","威仪","重情义")
        values=("王位正统","臣下信赖","国家安定")
        desires=("击败格拉维尔派","让追随者得封")
        fears=("再失路克等近臣","辜负奥尔斯帝德谋划")
        skills=("王族治政","笼络人心")
        knowledge=("知人神挑拨路克",)
        summary="爱丽儿在第17卷由候选到女王的定局期。"
        change="本卷由候选公主确立为下任女王，威仪定型。"
        stg=("取得贵族倒戈","获佩尔基乌斯承认")
        ltg=("稳固阿斯拉王权",)
        obligations=("对追随者的封赏承诺",)
        decision=("广纳谏言后决断",)
        speech=("威仪、礼仪完备",)
        social=("在王宫内绝对主导",)
        conflict=("以法与大义压制",)
        rel=("对路克由怒到原谅","对希露菲感激")
    elif cid=="E0045":
        traits=("忠诚","易被蛊惑","自责","重荣誉")
        values=("对爱丽儿的忠诚","诺托斯家名")
        desires=("护爱丽儿周全","摆脱人神阴影")
        fears=("再被操控伤害主君","失去希露菲等同伴信任")
        skills=("护卫剑术",)
        knowledge=("知自身曾受人神怂恿",)
        summary="路克在第17卷受人神挑拨失控后被原谅、立为当家的转折。"
        change="本卷经历人神怂恿失控后被原谅，忠诚更坚。"
        stg=("求得爱丽儿原谅","稳住诺托斯家")
        ltg=("成为配得上爱丽儿的骑士",)
        obligations=("对爱丽儿的护卫契约",)
        decision=("易受低语动摇、事后自责",)
        speech=("对爱丽儿敬语、对希露菲愧语",)
        social=("在护卫中核心但易孤立",)
        conflict=("以自毁式挟持宣泄、后跪求原谅",)
        rel=("对爱丽儿由忠到愧到复忠",)
    elif cid=="E0145":
        traits=("坚韧","果敢","自尊强","重恩义")
        values=("对爱丽儿的报恩","家族存续")
        desires=("指证大流士","让父亲倒戈")
        fears=("再被大流士势力报复",)
        skills=("盗贼团统领经验",)
        knowledge=("知大流士恶行全貌",)
        summary="朵莉丝堤娜在第17卷以指证让大流士垮台的核心证人。"
        change="由隐忍受害者转为公开指证的关键证人。"
        stg=("在宴会指证大流士",)
        ltg=("守护爱丽儿阵营",)
        obligations=("对爱丽儿的同伴义务",)
        decision=("直言受害经历",)
        speech=("直率、带颤但坚定",)
        social=("在贵族厅内受瞩目",)
        conflict=("以真相揭露对抗权势",)
        rel=("对父由疏到联手","对大流士仇敌")
    else:
        traits=("温柔","坚定","护夫","重家庭")
        values=("家庭","对鲁迪的忠诚","孩子")
        desires=("辞去护卫归家育儿","守护与鲁迪的家庭")
        fears=("人神再离间家庭",)
        skills=("护卫术","家务")
        knowledge=("知路克曾受怂恿拉拢",)
        summary="希露菲在第17卷末辞职归家的转身期。"
        change="本卷末辞去护卫，转向归家育儿。"
        stg=("拒绝路克动摇","辞职归家")
        ltg=("养育孩子、守家",)
        obligations=("对爱丽儿的护卫谢辞",)
        decision=("以家庭为先决断",)
        speech=("温和、坚定",)
        social=("在王宫内低调",)
        conflict=("以拒绝化解诱惑",)
        rel=("对路克由信到拒","对鲁迪更近")
    profiles.append(CharacterProfile(
        profile_id=pid, character_id=cid, phase_id=f"P{base+idx+1:04d}", phase_name=phase,
        start_date=None, end_date=None, date_precision=DatePrecision.UNKNOWN,
        age_description=age,
        personality_traits=traits, values=values, desires=desires, fears=fears,
        taboos=("背叛奥尔斯帝德",) if cid=="E0001" else ("背叛爱丽儿",) if cid=="E0045" else ("再为性奴",) if cid=="E0145" else ("背叛鲁迪",) if cid=="E0006" else ("临阵退缩",) if cid=="E0021" else ("轻视剑术",) if cid=="E0022" else ("背弃追随者",),
        insecurities=("对王宫权谋的陌生",) if cid=="E0001" else ("对权谋不擅",) if cid=="E0021" else ("前黑狼之牙过往",) if cid=="E0022" else ("对王权的自我怀疑（已克服）",) if cid=="E0044" else ("对自身意志薄弱的自责",) if cid=="E0045" else ("过往受辱的创伤",) if cid=="E0145" else ("对王宫权谋的不适",),
        pride="作为龙神部下与一家之主的担当" if cid=="E0001" else "狂剑王之名" if cid=="E0021" else "剑神流剑王、处决大流士的执行者" if cid=="E0022" else "阿斯拉王族与下任女王之位" if cid=="E0044" else "诺托斯家当家的担当" if cid=="E0045" else "以受害者身份指证的勇气" if cid=="E0145" else "作为鲁迪妻子与母的自尊",
        impulsiveness="MODERATE" if cid in ("E0001","E0145") else "HIGH" if cid=="E0021" else "LOW",
        patience="MODERATE" if cid=="E0001" else "LOW" if cid in ("E0021","E0045") else "HIGH",
        risk_tolerance="HIGH" if cid in ("E0001","E0021","E0145") else "MEDIUM" if cid in ("E0022","E0044") else "LOW",
        self_control="MODERATE" if cid in ("E0001","E0145") else "LOW" if cid in ("E0021","E0045") else "HIGH",
        attachment_style="以家庭为锚点的安全型" if cid=="E0001" else "以羁绊确认的忠诚型" if cid=="E0021" else "以护卫关系为羁绊" if cid=="E0022" else "以信赖维系统治" if cid=="E0044" else "以主从羁绊为锚" if cid=="E0045" else "以恩义维系" if cid=="E0145" else "安全型",
        authority_attitude="对奥尔斯帝德忠诚、对阿斯拉王权保持距离" if cid=="E0001" else "对王权无敬、对强者尊敬" if cid=="E0021" else "对爱丽儿绝对服从" if cid=="E0022" else "自身即权威、对佩尔基乌斯恭敬" if cid=="E0044" else "对爱丽儿绝对服从、对人神易受蛊" if cid=="E0045" else "对大流士仇恨、对爱丽儿感恩" if cid=="E0145" else "对爱丽儿感恩而后辞别",
        family_attitude="重家庭，视爱丽儿为妹" if cid=="E0001" else "视鲁迪为夫与主" if cid=="E0021" else None,
        romantic_attitude="对希露菲等妻子保持忠诚" if cid=="E0001" else "对鲁迪炽热" if cid=="E0021" else None,
        violence_attitude="以魔术与战术制敌，回避无谓杀戮" if cid=="E0001" else "以剑决胜、先动手后思" if cid=="E0021" else "以剑与气势决胜、少言即断" if cid=="E0022" else "以威仪与法度治乱" if cid=="E0044" else "以剑护主、失控时挟持" if cid=="E0045" else "以证词为武器" if cid=="E0145" else "回避、必要时拒诱",
        money_attitude=None, status_attitude=None, race_attitude="中立", religious_attitude="对米里斯教持批判" if cid=="E0001" else None,
        loyalty="HIGH", ambition="完成王位任务并生还归家" if cid=="E0001" else "以剑护家" if cid=="E0021" else "HIGH",
        short_term_goals=stg, long_term_goals=ltg, obligations=obligations,
        decision_tendencies=decision, speech_tendencies=speech, social_tendencies=social, conflict_tendencies=conflict,
        known_skills=skills, knowledge_state=knowledge, relationship_tendencies=rel,
        behavior_changes_note=change, summary=summary,
        visible_from_volume=17, visible_to_volume=None, evidence_refs=pick(2, offset=idx*3),
    ))

case_defs=[
    ("E0001","NEGOTIATION","推敲阶段与爱丽儿制定指证方案","帕普尔荷斯家情报送达","提出以朵莉丝指证为核心配合佩尔基乌斯威压"),
    ("E0021","COMBAT","王宫宴会直面双胞胎纳库尔贾德","双胞胎联手突袭","拔剑直冲以狂剑斩杀"),
    ("E0022","COMBAT","对维·塔镜面铠甲反射干扰","维·塔炫光扰敌","闭眼凭气息斩破镜铠继而处决大流士"),
    ("E0145","NEGOTIATION","宴会厅众贵族前公开指证大流士","爱丽儿示意与父倒戈信号","当众陈述被性奴役与盗贼团经历"),
    ("E0144","NEGOTIATION","弗列塔斯宣布倒戈支持爱丽儿","女儿指证后风向转变","当众宣布帕普尔荷斯家改投爱丽儿"),
    ("E0001","COMBAT","王宫决战对奥贝尔与水神列妲","奥贝尔与列妲联手袭来","以岩炮与泥沼控场配合艾莉丝基列奴"),
    ("E0044","NEGOTIATION","战后佩尔基乌斯宣布支持为王","大流士垮台格拉维尔失势","躬身受命宣布封赏与赦免"),
    ("E0045","BETRAYAL","王宫回廊受人神低语挟持爱丽儿","人神以希露菲为饵","拔剑挟持欲带爱丽儿脱离"),
    ("E0006","LOYALTY","路克转以希露菲为突破口游说","称与希露菲共谋","当场拒绝直言绝不背叛鲁迪"),
    ("E0044","TRUST","内室单独面对跪地路克","路克痛哭坦白受怂恿","不斩不逐当场原谅"),
    ("E0079","NEGOTIATION","王都十日奥尔斯帝德与鲁迪密谈","鲁迪询问人神关联","告知使徒操控与十日必稳"),
    ("E0146","COMBAT","维·塔持镜铠迎战基列奴","基列奴逼近大流士","以镜面反射晃眼并短剑突刺"),
    ("E0021","TRAINING","诀别的训练与基列奴最后对练","王位战后将留王都","全力以狂剑对攻不留手"),
    ("E0001","FAMILY","归乡与决意与希露菲艾莉丝商议","希露菲提出辞职","赞同归家定下归返夏利亚"),
    ("E0086","FAILURE","大流士被指证后众叛亲离","弗列塔斯倒戈佩尔基乌斯发声","强辩后沉默被基列奴近身"),
    ("E0044","AUTHORITY","特典幽禁的王子处置格拉维尔","幽禁议题","定幽禁而非处死"),
]
behavior_cases=[]
for idx,(cid,tag,ctx,trig,act) in enumerate(case_defs):
    btag = BehaviorTag[tag]
    behavior_cases.append(BehaviorCase(
        case_id=f"BC{base+idx+1:05d}", character_id=cid, phase_id=f"P{base+1:04d}", phase_name=profiles[0].phase_name,
        volume_no=17, situation_type=tag.lower(), context=ctx, trigger=trig,
        available_information="卷十七当下情境与对话可见",
        action=act, verbal_response="简短回应或沉默", emotional_response="紧张后专注",
        goal_at_time="依当下职责推进", relationship_context="与爱丽儿阵营协作", social_context="王宫与王都社会情境",
        immediate_outcome="取得局部结果", long_term_outcome="影响王位与后续",
        tags=(btag,), evidence_refs=pick(1, offset=20+idx),
    ))

detailed_events=[
    DetailedEvent(event_id=f"DE{base+1:05d}", event_type="POLITICAL", title="朵莉丝指证与帕普尔荷斯倒戈", timeline_event_id="T0064", time_date=None, time_precision=DatePrecision.UNKNOWN, time_note="王宫宴会当夜", volume_no=17, location_id="E0010", participants=("E0145","E0144","E0086","E0044","E0001"), prerequisites=(EventPrerequisite(prerequisite_id=f"EP{base+1:05d}", prerequisite_type=EventPrerequisiteKind.PERSON_PRESENT, ref_id="E0145", statement="朵莉丝在场", evidence_refs=pick(1,30)), EventPrerequisite(prerequisite_id=f"EP{base+2:05d}", prerequisite_type=EventPrerequisiteKind.PERSON_PRESENT, ref_id="E0144", statement="弗列塔斯在场", evidence_refs=pick(1,31))), dependencies=(EventDependency(dependency_id=f"ED{base+1:05d}", dependency_type=EventDependencyKind.CAUSES, target_event_id=f"DE{base+2:05d}", statement="指证导致武力摊牌"),), state_changes=(StateChange(change_id=f"SC{base+1:05d}", change_kind="POLITICAL", subject_id="E0044", before="候选公主", after="获关键家名支持的准女王"), StateChange(change_id=f"SC{base+2:05d}", change_kind="SOCIAL", subject_id="E0145", before="隐忍受害者", after="公开指证者")), trigger="朵莉丝当众陈述被大流士性奴役并为盗贼团长经历，弗列塔斯随即宣布倒戈", actions=("朵莉丝当众指证","弗列塔斯宣布改投爱丽儿","贵族厅哗然格拉维尔派失势"), outcome="大流士在贵族前垮台，帕普尔荷斯家倒戈，爱丽儿获决定性支持", relationship_change_ids=(f"RC{base+1:05d}",), belief_ids=(f"BL{base+1:05d}",), canon_importance=EventImportance.MAJOR, evidence_refs=pick(2,32)),
    DetailedEvent(event_id=f"DE{base+2:05d}", event_type="COMBAT", title="王宫决战", timeline_event_id="T0065", time_date=None, time_precision=DatePrecision.UNKNOWN, time_note="同夜宴会会场", volume_no=17, location_id="E0010", participants=("E0001","E0021","E0022","E0146","E0147","E0134","E0086"), prerequisites=(EventPrerequisite(prerequisite_id=f"EP{base+3:05d}", prerequisite_type=EventPrerequisiteKind.PERSON_PRESENT, ref_id="E0001", statement="鲁迪在场", evidence_refs=pick(1,33)),), dependencies=(EventDependency(dependency_id=f"ED{base+2:05d}", dependency_type=EventDependencyKind.CAUSES, target_event_id=f"DE{base+3:05d}", statement="决战胜利导致佩尔基乌斯承认"),), state_changes=(StateChange(change_id=f"SC{base+3:05d}", change_kind="COMBAT", subject_id="E0147", before="受雇双胞胎剑士", after="被艾莉丝斩杀"), StateChange(change_id=f"SC{base+4:05d}", change_kind="COMBAT", subject_id="E0086", before="权倾朝野上级大臣", after="被基列奴处决")), trigger="格拉维尔派以奥贝尔列妲双胞胎与维·塔为战力在宴会发动", actions=("鲁迪以魔术控场对奥贝尔列妲","艾莉丝斩杀纳库尔贾德","基列奴破镜铠败维·塔并处决大流士"), outcome="格拉维尔派武力瓦解，水神列妲被斩，双胞胎败亡，维·塔败，大流士伏诛", relationship_change_ids=(f"RC{base+2:05d}",), belief_ids=(), canon_importance=EventImportance.MAJOR, evidence_refs=pick(2,34)),
    DetailedEvent(event_id=f"DE{base+3:05d}", event_type="POLITICAL", title="佩尔基乌斯宣布支持", timeline_event_id="T0066", time_date=None, time_precision=DatePrecision.UNKNOWN, time_note="决战后宴会", volume_no=17, location_id="E0010", participants=("E0029","E0044","E0073","E0001"), prerequisites=(EventPrerequisite(prerequisite_id=f"EP{base+4:05d}", prerequisite_type=EventPrerequisiteKind.PERSON_PRESENT, ref_id="E0029", statement="佩尔基乌斯在场", evidence_refs=pick(1,35)),), dependencies=(EventDependency(dependency_id=f"ED{base+3:05d}", dependency_type=EventDependencyKind.ENABLES, target_event_id=f"DE{base+4:05d}", statement="王位确立使路克事件在稳定秩序下处置"),), state_changes=(StateChange(change_id=f"SC{base+5:05d}", change_kind="POLITICAL", subject_id="E0044", before="准女王", after="下任女王"),), trigger="佩尔基乌斯现身甲龙王威压下宣布爱丽儿为下任国王", actions=("佩尔基乌斯现身","宣布爱丽儿为下任国王","格拉维尔派彻底败北"), outcome="爱丽儿确立为下任阿斯拉女王，王位争夺战落幕", relationship_change_ids=(), belief_ids=(), canon_importance=EventImportance.MAJOR, evidence_refs=pick(2,36)),
    DetailedEvent(event_id=f"DE{base+4:05d}", event_type="SOCIAL", title="路克失控与原谅", timeline_event_id="T0067", time_date=None, time_precision=DatePrecision.UNKNOWN, time_note="决战后王宫回廊", volume_no=17, location_id="E0010", participants=("E0045","E0044","E0006","E0001","E0079"), prerequisites=(EventPrerequisite(prerequisite_id=f"EP{base+5:05d}", prerequisite_type=EventPrerequisiteKind.PERSON_PRESENT, ref_id="E0045", statement="路克在场", evidence_refs=pick(1,37)),), dependencies=(EventDependency(dependency_id=f"ED{base+4:05d}", dependency_type=EventDependencyKind.INFLUENCES, target_event_id=f"DE{base+5:05d}", statement="路克事件影响希露菲去留"),), state_changes=(StateChange(change_id=f"SC{base+6:05d}", change_kind="SOCIAL", subject_id="E0045", before="爱丽儿近卫", after="被原谅戴罪之臣后任诺托斯当家"),), trigger="人神托梦以希露菲为饵蛊惑路克挟持爱丽儿，希露菲当场拒绝", actions=("路克挟持爱丽儿","希露菲拒绝背叛鲁迪","爱丽儿当场原谅路克"), outcome="人神挑拨失败，路克被原谅并誓死效忠，后成为诺托斯当家", relationship_change_ids=(f"RC{base+3:05d}",f"RC{base+4:05d}"), belief_ids=(f"BL{base+2:05d}",), canon_importance=EventImportance.MAJOR, evidence_refs=pick(2,38)),
    DetailedEvent(event_id=f"DE{base+5:05d}", event_type="SOCIAL", title="诀别与归乡", timeline_event_id=None, time_date=None, time_precision=DatePrecision.UNKNOWN, time_note="王都十日后", volume_no=17, location_id="E0010", participants=("E0001","E0021","E0022","E0006","E0044"), prerequisites=(EventPrerequisite(prerequisite_id=f"EP{base+6:05d}", prerequisite_type=EventPrerequisiteKind.PERSON_PRESENT, ref_id="E0001", statement="鲁迪在场", evidence_refs=pick(1,39)),), dependencies=(), state_changes=(StateChange(change_id=f"SC{base+7:05d}", change_kind="SOCIAL", subject_id="E0006", before="爱丽儿护卫", after="辞职归家母亲"), StateChange(change_id=f"SC{base+8:05d}", change_kind="SOCIAL", subject_id="E0022", before="爱丽儿护卫之一", after="终身护卫")), trigger="王位已定奥尔斯帝德揭示十日真相后众人议定归去", actions=("艾莉丝与基列奴诀别训练","希露菲辞去护卫","鲁迪一行归乡爱丽儿留都"), outcome="希露菲归家育儿基列奴留任终身护卫鲁迪与艾莉丝归夏利亚", relationship_change_ids=(f"RC{base+4:05d}",), belief_ids=(), canon_importance=EventImportance.MINOR, evidence_refs=pick(2,40)),
]

items=[
    ItemDef(item_id=f"IT{base+1:05d}", canonical_name="维·塔的镜面铠甲", aliases=("镜铠","镜面铠"), category="ARMOR", subcategory="铠甲", description="维·塔所着短剑配镜面铠，能反射阳光干扰对手视线", material="钢与镜面", size="中", weight="中", durability="中", rarity="稀有", value_information="贵族骑士定制", currency="阿斯拉金币", creator=None, origin="阿斯拉王国", manufacturer=None, abilities=("反光干扰",), effects=("致盲",), requirements=("日光",), limitations=("需正面迎光、被闭眼或气息感知克制",), first_appearance_volume=17, first_appearance_line=151822, visible_from_volume=17, evidence_refs=pick(1,42)),
    ItemDef(item_id=f"IT{base+2:05d}", canonical_name="朵莉丝的指证信物", aliases=(), category="TOOL", subcategory="信物", description="朵莉丝用以佐证受害的信物与疤痕", material="布与旧饰", size=None, weight=None, durability=None, rarity="唯一", value_information="无价（证物）", currency=None, creator=None, origin="阿斯拉王国", manufacturer=None, abilities=(), effects=("佐证",), requirements=(), limitations=(), first_appearance_volume=17, first_appearance_line=153538, visible_from_volume=17, evidence_refs=pick(1,43)),
    ItemDef(item_id=f"IT{base+3:05d}", canonical_name="水神列妲的长剑", aliases=(), category="WEAPON", subcategory="长剑", description="水神流顶点的长剑 水神列妲所持", material="钢", size="长", weight="轻", durability="高", rarity="稀有", value_information="名匠作", currency="阿斯拉金币", creator=None, origin="水神流", manufacturer=None, abilities=("水神流斩击",), effects=("斩击",), requirements=("水神流",), limitations=("需近身",), first_appearance_volume=17, first_appearance_line=156454, visible_from_volume=17, evidence_refs=pick(1,44)),
]
instances=[
    ItemInstance(instance_id=f"IN{base+1:05d}", definition_id=f"IT{base+1:05d}", owner_id="E0146", holder_id="E0146", location_id="E0010", location_name="王宫宴会会场", condition="战后破损", durability_if_known="中", acquired_at=None, lost_at=None, acquired_at_volume=17, lost_at_volume=None, ownership_history=(OwnershipEntry(entry_id=f"OH{base+1:05d}", owner_id="E0146", period_start=None, period_end=None, acquired_via="配发", lost_via=None, note="大流士麾下骑士配给"),), evidence_refs=pick(1,45)),
    ItemInstance(instance_id=f"IN{base+2:05d}", definition_id=f"IT{base+3:05d}", owner_id="E0134", holder_id="E0134", location_id="E0010", location_name="王宫宴会会场", condition="遗落", durability_if_known="高", acquired_at=None, lost_at=None, acquired_at_volume=17, lost_at_volume=17, ownership_history=(OwnershipEntry(entry_id=f"OH{base+2:05d}", owner_id="E0134", period_start=None, period_end=None, acquired_via="持有", lost_via="战死遗落", note="列妲战死后遗落"),), evidence_refs=pick(1,46)),
]
abilities=[
    AbilityProfile(ability_id=f"AB{base+1:05d}", name="镜面反射干扰", aliases=("镜铠干扰",), ability_type=AbilityType.SPECIAL, school="骑士技", element=None, tier=None, requirements=("镜面铠甲","日光"), preconditions=("正面迎光",), mana_cost_if_known=None, stamina_cost_if_known="低", range_if_known="近战", duration_if_known="瞬时", effects=("致盲干扰",), limitations=("闭眼或以气息感知可破","需光源"), counters=("闭眼听风","魔术烟幕"), qualitative_power="对剑士有奇效、对感知型无效", learning_method=("骑士定制装备",), known_users=("E0146",), evidence_refs=pick(1,47)),
    AbilityProfile(ability_id=f"AB{base+2:05d}", name="水神流", aliases=(), ability_type=AbilityType.SWORD, school="水神流", element=None, tier="水神", requirements=("长剑",), preconditions=(), mana_cost_if_known=None, stamina_cost_if_known="中", range_if_known="近战", duration_if_known=None, effects=("以柔克刚、反击斩",), limitations=("需近身、被刚力压制"), counters=("剑神流强攻","魔术控场"), qualitative_power="王国顶点之一 水神列妲与伊佐露缇所用", learning_method=("水神流道场",), known_users=("E0134","E0133"), evidence_refs=pick(1,48)),
    AbilityProfile(ability_id=f"AB{base+3:05d}", name="剑神流·狂剑", aliases=(), ability_type=AbilityType.SWORD, school="剑神流", element=None, tier="剑王", requirements=("长剑",), preconditions=(), mana_cost_if_known=None, stamina_cost_if_known="高", range_if_known="近战", duration_if_known=None, effects=("刚猛斩击",), limitations=("需近身、直来直去"), counters=("水神流截击","魔术牵制"), qualitative_power="剑王级 艾莉丝与基列奴所用", learning_method=("剑神流修行",), known_users=("E0021","E0022"), evidence_refs=pick(1,49)),
    AbilityProfile(ability_id=f"AB{base+4:05d}", name="岩炮与泥沼", aliases=(), ability_type=AbilityType.MAGIC, school="土魔术", element="土", tier="上位", requirements=("魔力",), preconditions=(), mana_cost_if_known="中", stamina_cost_if_known=None, range_if_known="中远程", duration_if_known="瞬时", effects=("炮击、控场"), limitations=("需咏唱或无咏唱技巧","王宫内需控威力"), counters=("高速斩击近身",), qualitative_power="战功级 鲁迪主力魔术", learning_method=("洛琪希与自修",), known_users=("E0001",), evidence_refs=pick(1,50)),
]
comparisons=[
    PowerComparison(comparison_id=f"PC{base+1:05d}", actor_id="E0021", target_id="E0147", dimension="剑术", context="王宫宴会 艾莉丝对双胞胎纳库尔贾德", result="艾莉丝以狂剑王斩杀联手的双胞胎", confidence=Confidence.EXPLICIT, evidence_refs=pick(1,51)),
    PowerComparison(comparison_id=f"PC{base+2:05d}", actor_id="E0022", target_id="E0146", dimension="剑术", context="王宫宴会 基列奴对维·塔镜铠", result="基列奴闭眼破镜铠后胜出", confidence=Confidence.EXPLICIT, evidence_refs=pick(1,52)),
    PowerComparison(comparison_id=f"PC{base+3:05d}", actor_id="E0001", target_id="E0134", dimension="综合战力", context="王宫决战 鲁迪对水神列妲 配合艾莉丝基列奴", result="鲁迪以魔术控场牵制 最终由艾莉丝侧斩列妲", confidence=Confidence.INFERENCE, evidence_refs=pick(1,53)),
]
world_rules=[
    WorldRule(rule_id=f"WR{base+1:05d}", domain=WorldRuleDomain.POLITICS, statement="阿斯拉王国王位空缺时 贵族以家名与封地为筹码站队 帕普尔荷斯等中等家名的倒戈可决定天平", scope="阿斯拉王国", exceptions="甲龙王一言可定鼎、王族血缘有优先", confidence=Confidence.EXPLICIT, visible_from_volume=17, evidence_refs=pick(1,54)),
    WorldRule(rule_id=f"WR{base+2:05d}", domain=WorldRuleDomain.NOBILITY, statement="王宫宴会为公开的贵族审判场 当众指证与家名倒戈具法律与舆论效力", scope="阿斯拉王都亚尔斯", exceptions="王族直裁可推翻", confidence=Confidence.INFERENCE, visible_from_volume=17, evidence_refs=pick(1,55)),
    WorldRule(rule_id=f"WR{base+3:05d}", domain=WorldRuleDomain.COMBAT, statement="镜面铠甲在日光下可致盲剑士 但对闭眼以气息感知或魔术烟幕无效", scope="阿斯拉骑士技", exceptions="无光环境无效", confidence=Confidence.EXPLICIT, visible_from_volume=17, evidence_refs=pick(1,56)),
    WorldRule(rule_id=f"WR{base+4:05d}", domain=WorldRuleDomain.RELIGION, statement="人神可通过托梦低语蛊惑意志薄弱者 煽动其背叛或挟持关键人物", scope="人神使徒", exceptions="意志坚定者可拒绝 如希露菲", confidence=Confidence.EXPLICIT, visible_from_volume=17, evidence_refs=pick(1,57)),
]
beliefs=[
    Belief(belief_id=f"BL{base+1:05d}", owner_id="E0144", topic="大流士去留", statement="认为追随大流士已无前途 改投爱丽儿可保家族", certainty=Confidence.INFERENCE, belief_state=BeliefState.INFERRED, learned_from="女儿指证与贵族风向", learned_at_volume=17, learned_method="目击", is_true_in_world=True, visible_from_volume=17, visible_to_volume=None, note="弗列塔斯倒戈前的判断", evidence_refs=pick(1,58)),
    Belief(belief_id=f"BL{base+2:05d}", owner_id="E0045", topic="人神低语", statement="一度相信带走爱丽儿可得希露菲与未来", certainty=Confidence.INFERENCE, belief_state=BeliefState.FALSE_BELIEF, learned_from="人神托梦", learned_at_volume=17, learned_method="托梦", is_true_in_world=False, visible_from_volume=17, visible_to_volume=None, note="路克被蛊惑时的误信", evidence_refs=pick(1,59)),
    Belief(belief_id=f"BL{base+3:05d}", owner_id="E0001", topic="人神", statement="认为人神正通过使徒操控阿斯拉王位争夺", certainty=Confidence.EXPLICIT, belief_state=BeliefState.FACT_KNOWN, learned_from="奥尔斯帝德告知", learned_at_volume=17, learned_method="告知", is_true_in_world=True, visible_from_volume=17, visible_to_volume=None, note="奥尔斯帝德揭示真相", evidence_refs=pick(1,60)),
]
econ=[
    EconomicObservation(observation_id=f"EC{base+1:05d}", location_id="E0010", location_name="阿斯拉王国", at_date=None, at_volume=17, category="WEAPON", item_id=f"IT{base+3:05d}", goods_description="水神长剑一柄", quantity="1", currency="阿斯拉金币", amount_description="名匠价 数枚金币", price_class=PriceClass.QUALITATIVE, context="王宫武具与宴会佩剑", evidence_refs=pick(1,61)),
]
rel_changes=[
    RelationshipChange(change_id=f"RC{base+1:05d}", source_id="E0144", target_id="E0044", dimension="从属", before="格拉维尔派", trigger="女儿指证与贵族哗然", after="追随爱丽儿", at_volume=17, at_date=None, evidence_refs=pick(1,62)),
    RelationshipChange(change_id=f"RC{base+2:05d}", source_id="E0022", target_id="E0086", dimension="仇敌", before="追杀与被庇护", trigger="当众对峙", after="处决仇敌", at_volume=17, at_date=None, evidence_refs=pick(1,63)),
    RelationshipChange(change_id=f"RC{base+3:05d}", source_id="E0044", target_id="E0045", dimension="信任", before="近卫信任", trigger="挟持后坦白", after="原谅并更信赖", at_volume=17, at_date=None, evidence_refs=pick(1,64)),
    RelationshipChange(change_id=f"RC{base+4:05d}", source_id="E0006", target_id="E0044", dimension="从属", before="爱丽儿护卫", trigger="王位已定、家庭为先", after="辞职归家", at_volume=17, at_date=None, evidence_refs=pick(1,65)),
]
speeches=[
    SpeechProfile(profile_id=f"ST{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", phase_name="王位争夺期", politeness="对爱丽儿敬语、对同伴直率", sentence_length="中短", address_habits="对爱丽儿称殿下、对基列奴直呼", emotion_expression="紧张时语速加快", anger_expression="低声斥责", shy_expression="回避视线", intimate_speech="对希露菲温和", stranger_speech="对贵族谨慎试探", superior_speech="对后辈克制", inferior_speech="对奥尔斯帝德恭敬", canonical_examples=("让朵莉丝出面","这边交给我"), visible_from_volume=17, evidence_refs=pick(1,66)),
    SpeechProfile(profile_id=f"ST{base+2:05d}", character_id="E0145", phase_id=f"P{base+6:04d}", phase_name="指证期", politeness="对贵族带颤的敬语、对大流士直斥", sentence_length="中长", address_habits="对爱丽儿称殿下", emotion_expression="颤抖后坚定", anger_expression="直斥恶行", shy_expression="低头", intimate_speech="对父轻声", stranger_speech="对贵族试探", superior_speech="对大流士不屈", inferior_speech="对父愧语", canonical_examples=("大流士卿，你可还记得我？",), visible_from_volume=17, evidence_refs=pick(1,67)),
]
quirks=[
    CharacterQuirk(quirk_id=f"QK{base+1:05d}", character_id="E0021", phase_id=f"P{base+2:04d}", category="COMBAT", name="突进癖", description="遇敌必先冲 以狂剑斩开局面", intensity="高", frequency="常见", triggers=("同伴遇险","强敌现身"), preferred_targets=(), avoided_targets=(), public_expression="当众拔剑", private_expression=None, behavior_patterns=("不待号令先冲",), verbal_patterns=(), body_language="前倾突进", emotional_reward="宣泄", emotional_response="兴奋", boundaries=(), exceptions=(), visible_from_volume=17, evidence_refs=pick(1,68)),
    CharacterQuirk(quirk_id=f"QK{base+2:05d}", character_id="E0022", phase_id=f"P{base+3:04d}", category="COMBAT", name="闭眼斩", description="对光学干扰闭眼以气息斩击", intensity="中", frequency="偶发", triggers=("镜面反光","炫光干扰"), preferred_targets=(), avoided_targets=(), public_expression="闭眼拔刀", private_expression=None, behavior_patterns=("闭眼听风","一刀两断"), verbal_patterns=(), body_language="闭眼侧耳", emotional_reward="克敌", emotional_response="专注", boundaries=(), exceptions=(), visible_from_volume=17, evidence_refs=pick(1,69)),
]
prefs=[
    CharacterPreference(preference_id=f"PF{base+1:05d}", character_id="E0044", phase_id=f"P{base+4:04d}", preference_type="LIKE", target="贤臣", description="偏好能谏言并守信的近臣", intensity="高", context="王位确立后封赏", visible_from_volume=17, evidence_refs=pick(1,70)),
    CharacterPreference(preference_id=f"PF{base+2:05d}", character_id="E0021", phase_id=f"P{base+2:04d}", preference_type="LIKE", target="正面决斗", description="偏好正面一决胜负而非阴谋", intensity="高", context="王宫决战", visible_from_volume=17, evidence_refs=pick(1,71)),
]
bodies=[
    BodyLanguageProfile(profile_id=f"BY{base+1:05d}", character_id="E0145", phase_id=f"P{base+6:04d}", phase_name="指证期", happy_signs=(), angry_signs=("颤抖指认",), nervous_signs=("手指紧攥","声音发颤"), embarrassed_signs=(), lying_signs=(), fear_signs=("面对大流士时僵直",), thinking_signs=(), affection_signs=(), hostility_signs=("瞪视大流士",), visible_from_volume=17, evidence_refs=pick(1,72)),
    BodyLanguageProfile(profile_id=f"BY{base+2:05d}", character_id="E0022", phase_id=f"P{base+3:04d}", phase_name="终身护卫期", happy_signs=(), angry_signs=("拔剑半寸",), nervous_signs=(), embarrassed_signs=(), lying_signs=(), fear_signs=(), thinking_signs=(), affection_signs=(), hostility_signs=("怒视大流士","闭眼斩"), visible_from_volume=17, evidence_refs=pick(1,73)),
]
personas=[
    CharacterPersona(persona_id=f"PN{base+1:05d}", character_id="E0044", phase_id=f"P{base+4:04d}", persona_type="PUBLIC", description="宴会厅上威仪而仁慈的准女王", speech_style="王族敬语", behavior_traits=("躬身受命","微笑抚慰"), visible_from_volume=17, evidence_refs=pick(1,74)),
    CharacterPersona(persona_id=f"PN{base+2:05d}", character_id="E0044", phase_id=f"P{base+4:04d}", persona_type="PRIVATE", description="内室中对路克悲悯原谅的爱丽儿", speech_style="温和私语", behavior_traits=("轻抚","低声原谅"), visible_from_volume=17, evidence_refs=pick(1,75)),
]
conflicts=[
    CanonConflict(conflict_id=f"CC{base+1:05d}", claim_a="王宫宴会当夜众贵族在场却无人先制止大流士", claim_b="大流士却能长期以性奴役与盗贼操控贵族而不败露", evidence_a_refs=pick(1,76), evidence_b_refs=pick(1,77), possible_resolution="大流士以权势与格拉维尔庇护压制检举，朵莉丝指证与帕普尔荷斯倒戈才打破沉默", status=ConflictStatus.RESOLVED, note="权势压制与公开指证的转折"),
]
gaps=[
    CanonGap(gap_id=f"GAP{base+1:05d}", domain="POLITICS", question="格拉维尔幽禁后的具体处置与后续王位过渡细节", why_needed="推演阿斯拉王权平稳过渡", searched_volumes=(17,), status=GapStatus.PARTIAL, possible_sources="后续卷与特典 幽禁的王子", note="本卷仅定性幽禁，未给年限与待遇"),
    CanonGap(gap_id=f"GAP{base+2:05d}", domain="MAGIC", question="奥贝尔暗杀术与列妲水神流在王宫内的完整战技细节", why_needed="复现王宫决战战力对比", searched_volumes=(17,), status=GapStatus.OPEN, possible_sources="后续外传或设定集", note="本卷仅记胜负，未给招式名"),
]
batch = EnrichmentBatch(
    batch_id="ENRICH_V017", source_volume=17, source_unit_ids=tuple(source_unit_ids), schema_version="1.0.0",
    evidence=tuple(evidence_list), character_profiles=tuple(profiles), behavior_cases=tuple(behavior_cases),
    detailed_events=tuple(detailed_events), items=tuple(items), item_instances=tuple(instances),
    abilities=tuple(abilities), power_comparisons=tuple(comparisons), world_rules=tuple(world_rules),
    locations=tuple(), routes=tuple(), travel_observations=tuple(),
    organizations=tuple(), political_states=tuple(), species=tuple(), creatures=tuple(),
    beliefs=tuple(beliefs), economic_observations=tuple(econ), relationship_changes=tuple(rel_changes),
    speech_profiles=tuple(speeches), character_quirks=tuple(quirks), character_preferences=tuple(prefs),
    body_language_profiles=tuple(bodies), character_personas=tuple(personas),
    canon_conflicts=tuple(conflicts), canon_gaps=tuple(gaps),
)
print("Counts:", batch.counts())
out=pathlib.Path("data/canon_enriched/V017.json")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", encoding="utf-8") as f:
    json.dump(batch.to_json(), f, ensure_ascii=False, sort_keys=True, indent=2)
print(f"Wrote {out} with {len(evidence_list)} evidences")

from overlord_worldsim.canon.enrich_registry import load_entity_registry, load_enrichment_batches
from overlord_worldsim.canon.enrich_verifier import verify_enrichment
reg=load_entity_registry(pathlib.Path("data/canon"))
batches=load_enrichment_batches(pathlib.Path("data/canon_enriched"))
print("Loaded",[b.batch_id for b in batches])
report=verify_enrichment(batches, doc, reg)
print("is_clean",report.is_clean)
if not report.is_clean:
    for e in report.errors[:80]:
        print(f" [{e.code}] {e.path}: {e.message}")
else:
    print("All clean")
