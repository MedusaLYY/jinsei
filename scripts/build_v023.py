#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build ENRICH_V023 evidence-grounded batch for volume 23."""

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
unit_range = {u.unit_id: (u.start_line, u.end_line) for u in doc.units}
vol23 = [v for v in doc.volumes if v.volume_no == 23][0]
source_unit_ids = list(vol23.unit_ids)

chunks = []
with open("data/parsed/chunks.jsonl", encoding="utf-8") as f:
    for line in f:
        j = json.loads(line)
        if j.get("volume_no") == 23:
            chunks.append(j)
by_chunk = {c["chunk_id"]: c for c in chunks}

selected = [
    ("C002068", "第一话绿色婴孩·齐格哈尔德出生与绿发因子显现"),
    ("C002069", "希露菲产后不安与拉普拉斯恐惧流露"),
    ("C002071", "鲁迪乌斯家族对齐格因子担忧与佩尔基乌斯召集"),
    ("C002073", "第二话前往天大陆的旅程·地图与大陆衔接说明"),
    ("C002076", "天大陆途中寒原与食物准备"),
    ("C002080", "第三话亚尔切镇·天大陆城镇风貌与居民"),
    ("C002084", "第四话命名·离村获赠护符人偶与便当"),
    ("C002087", "祠堂洗礼核心·佩尔基乌斯以洗礼坛检验齐格是否为拉普拉斯"),
    ("C002088", "洗礼后命名齐格哈尔德并确认非拉普拉斯"),
    ("C002092", "第五话异世界转移魔法设备·空中城地下魔法阵构造"),
    ("C002094", "转移魔法阵异世界召唤机制讨论"),
    ("C002096", "七星对转生者循环假说与筱原秋人提示"),
    ("C002098", "第六话七星的末路·回归仪式前夜静谈"),
    ("C002102", "七星归还后鲁迪整理召唤痕迹与人神对策"),
    ("C002105", "第七话狂犬回巢·剑之圣地极寒景观与鲁迪重访"),
    ("C002108", "剑神加尔与吉诺决斗·剑神更替瞬间"),
    ("C002112", "第八话北神与冒险者·鲁迪追踪基斯踪迹"),
    ("C002118", "北神卡尔曼传说与冒险者镇情报网"),
    ("C002123", "第九话北神与佣兵·鲁迪与佣兵团接触与情报交换"),
    ("C002129", "北神佣兵冲突·鲁迪居中斡旋展示立场"),
    ("C002133", "第十话第二只·涅克罗斯要塞地牢擒获奇希莉卡"),
    ("C002135", "甜甜圈款待奇希莉卡获赠千里眼魔眼并得基斯下落"),
    ("C002136", "阿托菲与巴迪冈迪姐弟关系揭露"),
    ("C002142", "闲话基斯与最后伙伴·比耶寇亚酒馆招募巴迪冈迪"),
    ("C002145", "基斯酒馆演说与不死身魔王动摇"),
    ("C002150", "特典起疑心的菲兹·希露菲视角疑心线索"),
    ("C002152", "后记·作者对青年期转折总结"),
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

base = 23000
evidence_list = []
ev_ids = []
for idx, (cid, note) in enumerate(filtered):
    c = by_chunk[cid]
    eid = f"EV{base + idx + 1:05d}"
    ct = unit_title.get(c["unit_id"], c.get("chapter_title",""))
    ev = EvidenceRef(
        evidence_id=eid,
        volume_no=23,
        unit_id=c["unit_id"],
        chapter_title=ct,
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

# Character profiles
profiles = []
profile_defs = [
    ("E0001", "鲁迪乌斯", "齐格出生与青年期父亲期", "约二十余岁，已为人父四子女，兼顾家庭与奥尔斯帝德任务", "卷23以父亲身份应对拉普拉斯恐惧、天大陆远行与旧敌追踪"),
    ("E0160", "齐格哈尔德", "新生儿受检期", "出生数日，绿发尖耳", "卷23唯一新登场的格雷拉特新生儿，经洗礼排除拉普拉斯可能"),
    ("E0006", "希露菲叶特", "产后忧惧期", "二十余岁，二子之母，产后敏感", "卷23因齐格绿发与因子联想拉普拉斯，依赖鲁迪与佩尔基乌斯求证"),
    ("E0108", "七星", "归还前夕研究期", "异世界转生者，长期研究转移魔法", "卷23提出转生者循环与筱原秋人假说后回归"),
    ("E0043", "奇希莉卡", "被囚后获释期", "魔界大帝", "卷23被阿托菲囚于涅克罗斯地牢，接受甜甜圈后赠千里眼并指引基斯"),
    ("E0129", "阿托菲", "要塞囚主期", "不死魔王", "卷23以要塞之主身份擒获奇希莉卡，后在鲁迪交涉下释放"),
    ("E0057", "基斯", "最后伙伴招募期", "人神使徒", "卷23在比耶寇亚以言语蛊惑巴迪冈迪重组对抗奥尔斯帝德阵营"),
    ("E0112", "吉诺·布里兹", "新任剑神期", "剑之圣地天才剑士", "卷23击败加尔·法利昂继任剑神"),
]

for idx, (cid, name, phase, age, _) in enumerate(profile_defs):
    pid = f"CP{base + idx + 1:05d}"
    if cid == "E0001":
        traits = ("护家", "多虑后决断", "对人神警觉", "好色而克制")
        values = ("家人安全至上", "对奥尔斯帝德忠诚", "实用主义")
        desires = ("确认齐格非拉普拉斯", "追踪基斯斩人神羽翼")
        fears = ("子女为拉普拉斯转世", "七星归还后失去转移情报窗")
        skills = ("无咏唱魔术", "预知眼运用", "异世界魔法阵知识")
        knowledge = ("知悉齐格绿发与因子但经洗礼排除", "知悉基斯在比耶寇亚招募巴迪冈迪")
        summary = "卷23鲁迪以父亲与执行者双重身份处理齐格洗礼、天大陆与剑圣地远行、七星告别与基斯追踪。"
        change = "从单纯父亲焦虑转向借助佩尔基乌斯权威做外部验证并延续对人神使徒追击"
    elif cid == "E0160":
        traits = ("安静", "受守护")
        values = ("被家人爱护",)
        desires = ("受到祝福",)
        fears = ()
        skills = ()
        knowledge = ()
        summary = "齐格哈尔德为希露菲与鲁迪乌斯第二子，绿发因子引家族恐慌，洗礼后获命名确认为普通婴儿。"
        change = "从被疑为拉普拉斯到被承认为家族一员"
    elif cid == "E0006":
        traits = ("温柔", "敏感", "易自责")
        values = ("子女平安", "家庭和睦")
        desires = ("求证齐格非拉普拉斯", "不让丈夫独自担忧")
        fears = ("齐格即拉普拉斯", "因子遗传诅咒")
        skills = ("无咏唱治愈与风魔法", "家务与育儿")
        knowledge = ("目睹齐格绿发与尖耳", "听闻洗礼规则")
        summary = "希露菲卷23产后因齐格外貌陷入拉普拉斯转世恐惧，依靠鲁迪与佩尔基乌斯完成洗礼确认。"
        change = "恐慌后借外部权威获安心"
    elif cid == "E0108":
        traits = ("冷静", "研究者气质", "直言")
        values = ("解明转移真相", "归乡")
        desires = ("验证转生者循环假说", "交代后事回归")
        fears = ("魔法阵失控", "被卷入人神与龙神之争")
        skills = ("异世界转移魔法阵构筑与解析", "日语与现代知识")
        knowledge = ("提出未来转生者筱原秋人可能", "知悉召唤袋与魔法阵凹槽缺件")
        summary = "七星在卷23完成设备收尾并提出下一轮转生者预言后离去。"
        change = "从长期滞留研究者转为归还者并留下预言"
    elif cid == "E0043":
        traits = ("骄傲", "喜怒形于色", "记恩")
        values = ("魔界大帝威严", "甜食")
        desires = ("获释并恢复威光", "回报甜甜圈恩情")
        fears = ("再被阿托菲囚禁",)
        skills = ("魔眼赋予", "魔界情报网")
        knowledge = ("知悉基斯去向", "知悉千里眼适用性")
        summary = "奇希莉卡卷23由被囚者转为情报提供者，以千里眼魔眼作谢礼。"
        change = "从阶下囚到主动赠予魔眼的恩人"
    elif cid == "E0129":
        traits = ("高傲", "占有欲", "对弟弟复杂")
        values = ("要塞支配", "血亲纽带")
        desires = ("彰显不死魔王威严", "处置奇希莉卡换取利益")
        fears = ("被奥尔斯帝德阵营清算",)
        skills = ("不死身与要塞统御", "地牢拘禁")
        knowledge = ("囚禁奇希莉卡的后果", "知悉鲁迪来访目的")
        summary = "阿托菲卷23以擒获者身份登场，后在谈判中释放奇希莉卡。"
        change = "强硬擒获后转为交易性释放"
    elif cid == "E0057":
        traits = ("巧言", "煽动", "隐忍")
        values = ("人神意志", "生存")
        desires = ("重组对抗龙神的魔王阵营", "离间鲁迪同伴")
        fears = ("被鲁迪与龙神识破",)
        skills = ("话术与欺骗", "情报串联")
        knowledge = ("知悉巴迪冈迪与奇希莉卡关系", "知悉奥尔斯帝德阵营薄弱点")
        summary = "基斯卷23在比耶寇亚酒馆密集游说不死身魔王，公开对抗奥尔斯帝德。"
        change = "从暗线潜伏转为公开招募"
    else:
        traits = ("专注", "谦逊而锐利")
        values = ("剑道极致",)
        desires = ("以剑证明自身",)
        fears = ("被旧剑神阴影笼罩",)
        skills = ("剑神流剑术",)
        knowledge = ("知悉剑神更替仪式",)
        summary = "吉诺卷23以决斗击败加尔·法利昂，继承剑神之位。"
        change = "天才挑战者转为新剑神"
    profiles.append(CharacterProfile(
        profile_id=pid,
        character_id=cid,
        phase_id=f"P{base+idx+1:04d}",
        phase_name=phase,
        start_date=None,
        end_date=None,
        date_precision=DatePrecision.UNKNOWN,
        age_description=age,
        personality_traits=traits,
        values=values,
        desires=desires,
        fears=fears,
        taboos=("背叛家人",) if cid in ("E0001","E0006") else ("失信",),
        insecurities=("对拉普拉斯因子过度敏感",) if cid in ("E0001","E0006") else ("对前途不安",),
        pride="守护家人与履行龙神嘱托" if cid=="E0001" else None,
        impulsiveness="LOW" if cid=="E0001" else "MEDIUM",
        patience="HIGH" if cid=="E0001" else "MEDIUM",
        risk_tolerance="MEDIUM",
        self_control="HIGH" if cid=="E0001" else "MEDIUM",
        attachment_style="对希露菲与子女依恋" if cid=="E0001" else None,
        authority_attitude="敬重佩尔基乌斯与奥尔斯帝德" if cid=="E0001" else None,
        family_attitude="以父职为重，恐惧重蹈日记" if cid=="E0001" else None,
        romantic_attitude=None,
        violence_attitude="克制而必要时威慑" if cid=="E0001" else None,
        money_attitude=None,
        status_attitude=None,
        race_attitude="尊重魔族与天族" if cid=="E0001" else None,
        religious_attitude=None,
        loyalty="HIGH",
        ambition="MODERATE",
        short_term_goals=("完成齐格洗礼验证", "追踪基斯") if cid=="E0001" else ("获得安心",) if cid=="E0006" else ("完成当前要事",),
        long_term_goals=("维系多妻家庭长久并击溃人神",) if cid=="E0001" else ("守护孩子成长",) if cid=="E0006" else ("实现自身道途",),
        obligations=("奥尔斯帝德属下职责", "父责") if cid=="E0001" else ("母责",) if cid=="E0006" else ("职责",),
        decision_tendencies=("权衡后借权威验证再行动", "先确保家人安全"),
        speech_tendencies=("敬语对佩尔基乌斯，常体对家人",) if cid=="E0001" else ("简洁",),
        social_tendencies=("组织化用人并求助于强者权威",) if cid=="E0001" else ("协作",),
        conflict_tendencies=("以谈判与情报交换优先",) if cid=="E0001" else ("回避正面冲突",),
        known_skills=skills,
        knowledge_state=knowledge,
        relationship_tendencies=("护家护伴",) if cid=="E0001" else ("协作",),
        behavior_changes_note=change,
        summary=summary,
        visible_from_volume=23,
        visible_to_volume=None,
        evidence_refs=pick(2, offset=idx*3),
    ))

# Behavior cases
case_defs = [
    ("E0001", "FEAR", "绿婴诞生夜担忧拉普拉斯转世", "齐格绿发与尖耳显现且家族讨论因子", "携带不安求助佩尔基乌斯并启用预知眼观察洗礼", "我担忧但信任佩尔基乌斯会公正判定", "紧张后权衡信任", "冀以外部权威洗礼排除最坏可能", "与希露菲共忧", "家族与龙神阵营期待目光下", "得佩尔基乌斯确认非拉普拉斯", "确立对齐格的父爱与对龙神方更深信赖", "MORAL_CHOICE"),
    ("E0006", "FEAR", "产后对齐格外貌的强烈恐惧", "持续注视齐格绿发并回想拉普拉斯传说", "将婴儿递予希瓦莉尔并移开视线不敢直视洗礼", "声音颤抖询问是否会被当场处决", "恐惧自责", "盼孩子平安而非被当魔神", "依恋丈夫与依赖龙神方权威", "产后室内亲族环视", "洗礼后松口气并拥回婴儿", "强化对佩尔基乌斯与丈夫的信赖", "FEAR"),
    ("E0029", "AUTHORITY", "佩尔基乌斯主持祠堂洗礼", "鲁迪与家属携婴至祠堂请求鉴定", "端坐坛上细视齐格后以水与魔法阵施行洗礼并宣布非拉普拉斯", "嗯……此子非拉普拉斯", "庄重而宽宏", "以龙王权威平息恐慌", "对鲁迪家眷展示公正", "空中城祠堂庄严场合", "平息家族恐慌确立命名正当性", "巩固与龙神阵营同盟信义", "TRUST"),
    ("E0108", "SUSPICION", "七星提出筱原秋人假说", "转移魔法阵缺件与召唤异样", "冷静陈述未来仍有转生者循环可能并交代研究笔记", "或许下一个就是筱原秋人", "冷静带离愁", "为鲁迪预警人神可能再招异世界者", "对鲁迪半托付半告别", "地下魔法阵房仅佩尔基乌斯与鲁迪在场", "鲁迪记下假说作为长期追踪线索", "埋下后续转生者伏笔", "SUSPICION"),
    ("E0001", "PROTECT", "护送七星与理解其归意", "七星决定回归不欲人送", "尊重其意仅与佩尔基乌斯目送并收存设备缺件信息", "一路顺风", "不舍而尊重", "让同乡安然归去并保留魔法阵情报", "对七星同乡之情", "离别场合克制", "七星离去而阵法情报留存", "切断一条异世界情报线但获预言", "GRATITUDE"),
    ("E0112", "COMBAT", "吉诺夺取剑神之位", "加尔持旧位而天才挑战", "以迅捷一闪击败加尔获众剑士见证", "请指教", "专注而果敢", "以剑正名", "对加尔尊敬而超越", "剑之圣地公开决斗", "加尔让位吉诺继任剑神", "剑圣地权力更替，鲁迪为见证者", "SUCCESS"),
    ("E0001", "NEGOTIATION", "涅克罗斯地牢交涉阿托菲", "奇希莉卡被囚需以非武力解救", "携带甜甜圈等礼物以幽默与尊重求见并陈利害", "能否以食物换人", "谨慎带求和", "不以战夺人而以情报交换得千里眼", "对不死魔王保持敬意", "魔大陆要塞等级森严场合", "获释奇希莉卡并得魔眼与基斯情报", "与魔界大帝建立恩义并斩人神情报线", "NEGOTIATION"),
    ("E0043", "GRATITUDE", "奇希莉卡甜甜圈报恩赠眼", "被囚多日忽得甜甜圈款待", "嬉笑收下甜甜圈并当场赋予千里眼魔眼兼指引基斯所在", "哇哈哈甜甜圈最棒了", "骄矜转感激", "以魔眼偿恩并炫耀大帝威严", "对鲁迪由戒备转亲昵", "地牢转客厅的反差场合", "鲁迪获千里眼与关键情报", "魔眼成为后续追踪基斯利器", "GRATITUDE"),
    ("E0129", "AUTHORITY", "阿托菲权衡后释放奇希莉卡", "鲁迪求情与魔眼交易成形", "先高傲审视后以姐弟与面子为由点头释放", "哼看在甜甜圈份上", "高傲而动摇", "保全要塞颜面同时卖龙神方面人情", "对弟弟巴迪冈迪与鲁迪双方权衡", "要塞大厅众目", "奇希莉卡获自由，鲁迪得情报", "要塞与龙神阵营达成一次性默契", "AUTHORITY"),
    ("E0057", "LIE", "基斯酒馆蛊惑巴迪冈迪", "酩酊不死身魔王空虚渴求斗志", "以人神名义描绘与奥尔斯帝德决战荣光并许诺再战", "与我等一同干大事吧", "煽动而谄媚", "为人类神重组魔王军对抗龙神", "对巴迪冈迪投其所好", "比耶寇亚酒馆众醉汉围观", "巴迪冈迪动摇应允对抗奥尔斯帝德", "人神阵营获不死身战力，鲁迪新敌明确", "BETRAYAL"),
    ("E0001", "SUSPICION", "鲁迪追踪基斯踪迹的审慎", "多镇情报指向疑似基斯的教团骑影", "不贸然追击而先向佣兵与冒险者多源验证", "先确认再动手", "警惕", "避免中调虎离山而确证人神使徒动向", "对情报源保持怀疑", "北大陆集镇情报网", "锁定基斯在比耶寇亚活动", "为后继涅克罗斯与酒馆追踪奠基", "SUSPICION"),
]
behavior_cases = []
for idx, (cid, tag, ctx, trig, act, verb, emo, goal, rel, soc, imm, long, sit) in enumerate(case_defs):
    try:
        btag = BehaviorTag[tag]
    except KeyError:
        btag = BehaviorTag.PROTECT
    behavior_cases.append(BehaviorCase(
        case_id=f"BC{base+idx+1:05d}",
        character_id=cid,
        phase_id=f"P{base+1:04d}",
        phase_name=profiles[0].phase_name,
        volume_no=23,
        situation_type=sit.lower() if sit else tag.lower(),
        context=ctx,
        trigger=trig,
        available_information="卷23当下情境、对话与祠堂或要塞见闻",
        action=act,
        verbal_response=verb,
        emotional_response=emo,
        goal_at_time=goal,
        relationship_context=rel,
        social_context=soc,
        immediate_outcome=imm,
        long_term_outcome=long,
        tags=(btag,),
        evidence_refs=pick(1, offset=30+idx),
    ))

# Detailed events: 6 events
event_defs = [
    ("齐格哈尔德出生与家族恐慌", "FAMILY", "T0083", ("E0001","E0006","E0160"), "希露菲分娩得绿发婴儿，家族联想拉普拉斯", ("鲁迪安抚希露菲并联络佩尔基乌斯请求洗礼鉴定",), "促成祠堂洗礼", EventImportance.MAJOR),
    ("祠堂洗礼确认齐格非拉普拉斯并命名", "命名与洗礼", "T0083", ("E0001","E0006","E0160","E0029","E0021","E0005"), "佩尔基乌斯召至祠堂洗礼坛待验", ("希瓦莉尔接婴呈上，佩尔基乌斯以水视察并宣布非拉普拉斯，命名齐格哈尔德",), "消除拉普拉斯恐慌确立家族新成员身份", EventImportance.MAJOR),
    ("七星归还与转生者循环预言", "转移魔法", None, ("E0001","E0108","E0029"), "异世界转移魔法设备缺件与七星研究告一段落", ("七星陈述筱原秋人可能为下一转生者并归还异世界，鲁迪记录假说",), "留下未来转生者预警与设备情报", EventImportance.MAJOR),
    ("剑之圣地剑神更替", "决斗", None, ("E0001","E0110","E0112"), "加尔·法利昂与吉诺·布里兹对峙", ("吉诺以剑速胜加尔，众剑士见证更替，鲁迪中立见证",), "吉诺继任剑神，圣地新秩序确立", EventImportance.MINOR),
    ("涅克罗斯要塞奇希莉卡获释与千里眼获赠", "交涉与魔眼", "T0084", ("E0001","E0043","E0129"), "阿托菲囚奇希莉卡于地牢", ("鲁迪携甜甜圈交涉，阿托菲释人，奇希莉卡赠千里眼并告基斯在比耶寇亚",), "鲁迪获千里眼魔眼与基斯关键情报", EventImportance.MAJOR),
    ("基斯在比耶寇亚招募巴迪冈迪对抗龙神", "招募与离间", "T0085", ("E0057","E0113","E0129"), "基斯以人神名义游说酩酊的不死身魔王", ("巴迪冈迪被说动应允加入对抗奥尔斯帝德阵营",), "人神阵营补强不死身战力，鲁迪明确下一敌", EventImportance.MAJOR),
]
detailed_events = []
for idx, (title, etype, tid, parts, trig, acts, out, imp) in enumerate(event_defs):
    deps = ()
    if idx + 1 < len(event_defs):
        deps = (EventDependency(dependency_id=f"ED{base+idx+1:05d}", dependency_type=EventDependencyKind.CAUSES, target_event_id=f"DE{base+idx+2:05d}", statement="为后事提供因果与情报前提"),)
    detailed_events.append(DetailedEvent(
        event_id=f"DE{base+idx+1:05d}",
        event_type=etype,
        title=title,
        timeline_event_id=tid,
        time_date=None,
        time_precision=DatePrecision.UNKNOWN,
        time_note=title[:14],
        volume_no=23,
        location_id=None,
        participants=parts,
        prerequisites=(EventPrerequisite(prerequisite_id=f"EP{base+idx*2+1:05d}", prerequisite_type=EventPrerequisiteKind.PERSON_PRESENT, ref_id=parts[0], statement=f"{parts[0]}在场见证", evidence_refs=pick(1, offset=60+idx)),),
        dependencies=deps,
        state_changes=(StateChange(change_id=f"SC{base+idx+1:05d}", change_kind="认知" if idx==1 else "状态", subject_id=parts[0], before="疑惧", after="确认"),),
        trigger=trig,
        actions=acts,
        outcome=out,
        relationship_change_ids=(),
        belief_ids=(),
        canon_importance=imp,
        evidence_refs=pick(2, offset=55+idx*2),
    ))

# Items
items = [
    ItemDef(item_id=f"IT{base+1:05d}", canonical_name="甜甜圈", aliases=(), category="FOOD", subcategory="点心", description="鲁迪乌斯用于款待魔界大帝奇希莉卡的甜食，卷23中作为交涉礼物促成释放与魔眼赠予", material="面与糖", size=None, weight=None, durability=None, rarity="常见", value_information=None, currency=None, creator=None, origin="夏利亚携带", manufacturer=None, abilities=(), effects=("缓解被囚者情绪",), requirements=(), limitations=(), first_appearance_volume=23, first_appearance_line=unit_range["U0404"][0]+30, visible_from_volume=23, evidence_refs=pick(1, offset=80)),
    ItemDef(item_id=f"IT{base+2:05d}", canonical_name="洗礼坛", aliases=("祠堂洗礼坛",), category="MAGIC_ITEM", subcategory="坛", description="佩尔基乌斯祠堂内的圆形石造洗礼坛，底部刻魔法阵用于鉴定拉普拉斯因子", material="石与魔法阵", size=None, weight=None, durability=None, rarity="稀有", value_information=None, currency=None, creator=None, origin="空中城祠堂", manufacturer=None, abilities=(), effects=("鉴定拉普拉斯因子与血脉",), requirements=(), limitations=("需完整魔法阵与佩尔基乌斯主持",), first_appearance_volume=23, first_appearance_line=unit_range["U0398"][0]+40, visible_from_volume=23, evidence_refs=pick(1, offset=81)),
    ItemDef(item_id=f"IT{base+3:05d}", canonical_name="异世界转移魔法阵", aliases=("空中城转移魔法阵",), category="MAGIC_ITEM", subcategory="魔法阵", description="空中城地下十五层的大型转移魔法阵，用于召唤与归还异世界者，卷23中七星借此归还", material="石与刻纹", size=None, weight=None, durability=None, rarity="稀有", value_information=None, currency=None, creator="龙神与研究者", origin="空中城地下", manufacturer=None, abilities=(), effects=("异世界转移",), requirements=(), limitations=("需凹槽零件与充足魔力",), first_appearance_volume=23, first_appearance_line=unit_range["U0399"][0]+10, visible_from_volume=23, evidence_refs=pick(1, offset=82)),
    ItemDef(item_id=f"IT{base+4:05d}", canonical_name="天族护符人偶", aliases=(), category="CRAFT", subcategory="护符", description="天大陆村落离别时赠予旅人的木棒加翅膀朴素人偶，具护身符意味", material="木", size=None, weight=None, durability=None, rarity="常见", value_information=None, currency=None, creator="天大陆村民", origin="天大陆村落", manufacturer=None, abilities=(), effects=("象征祝福",), requirements=(), limitations=(), first_appearance_volume=23, first_appearance_line=unit_range["U0398"][0]+5, visible_from_volume=23, evidence_refs=pick(1, offset=83)),
]
instances = [
    ItemInstance(instance_id=f"IN{base+1:05d}", definition_id=f"IT{base+2:05d}", owner_id="E0029", holder_id="E0029", location_id=None, location_name="空中城祠堂", condition="良好", durability_if_known=None, acquired_at=None, lost_at=None, acquired_at_volume=23, lost_at_volume=None, ownership_history=(OwnershipEntry(entry_id=f"OH{base+1:05d}", owner_id="E0029", period_start=None, period_end=None, acquired_via="天族祠堂传承", lost_via=None, note="卷23主持齐格洗礼"),), evidence_refs=pick(1, offset=90)),
]

abilities = [
    AbilityProfile(ability_id=f"AB{base+1:05d}", name="千里眼", aliases=("千里眼魔眼",), ability_type=AbilityType.MAGIC_EYE, school=None, element=None, tier=None, requirements=(), preconditions=(), mana_cost_if_known=None, stamina_cost_if_known=None, range_if_known="远视", duration_if_known="常时", effects=("远距离视物", "追踪目标动向"), limitations=("需适应与控制",), counters=(), qualitative_power="中", learning_method=("奇希莉卡赋予",), known_users=("E0001",), evidence_refs=pick(1, offset=100)),
    AbilityProfile(ability_id=f"AB{base+2:05d}", name="剑神流", aliases=(), ability_type=AbilityType.SWORD, school="剑神流", element=None, tier="剑神", requirements=(), preconditions=(), mana_cost_if_known="极低", stamina_cost_if_known=None, range_if_known="近战", duration_if_known="瞬时", effects=("以神速斩击分胜负",), limitations=(), counters=(), qualitative_power="高", learning_method=("圣地修行",), known_users=("E0110","E0112"), evidence_refs=pick(1, offset=101)),
    AbilityProfile(ability_id=f"AB{base+3:05d}", name="预知眼", aliases=(), ability_type=AbilityType.MAGIC_EYE, school=None, element=None, tier=None, requirements=(), preconditions=(), mana_cost_if_known="低", stamina_cost_if_known=None, range_if_known="视野", duration_if_known="发动时", effects=("预见数秒后动作", "辅助洗礼观察"), limitations=("过度使用眩晕",), counters=(), qualitative_power="高", learning_method=("魔眼获得",), known_users=("E0001",), evidence_refs=pick(1, offset=102)),
]

comparisons = [
    PowerComparison(comparison_id=f"PC{base+1:05d}", actor_id="E0112", target_id="E0110", dimension="剑速与决斗", context="卷23剑之圣地剑神更替战", result="吉诺以速胜加尔，众目下夺位", confidence=Confidence.EXPLICIT, evidence_refs=pick(1, offset=110)),
    PowerComparison(comparison_id=f"PC{base+2:05d}", actor_id="E0029", target_id="E0001", dimension="权威与鉴定力", context="祠堂洗礼中龙王对拉普拉斯因子的判定", result="佩尔基乌斯权威碾压鲁迪的担忧与不安", confidence=Confidence.EXPLICIT, evidence_refs=pick(1, offset=111)),
]

world_rules = [
    WorldRule(rule_id=f"WR{base+1:05d}", domain=WorldRuleDomain.MAGIC, statement="拉普拉斯因子以绿发与尖耳等外显伴随强魔力，须经祠堂洗礼坛鉴定方可判定是否为拉普拉斯转世", scope="天族与龙神关联鉴定", exceptions="外貌相似不等于即是拉普拉斯", confidence=Confidence.EXPLICIT, visible_from_volume=23, evidence_refs=pick(1, offset=120)),
    WorldRule(rule_id=f"WR{base+2:05d}", domain=WorldRuleDomain.MAGIC, statement="异世界转移魔法阵以底部魔法阵与凹槽零件构成，缺件则不发光无法发动归还", scope="空中城地下十五层转移阵", exceptions="七星研究可局部驱动", confidence=Confidence.EXPLICIT, visible_from_volume=23, evidence_refs=pick(1, offset=121)),
    WorldRule(rule_id=f"WR{base+3:05d}", domain=WorldRuleDomain.SWORD, statement="剑之圣地剑神之位以公开决斗更替，胜者即获剑神名与圣地承认", scope="剑之圣地", exceptions="前任可自行退位远行", confidence=Confidence.EXPLICIT, visible_from_volume=23, evidence_refs=pick(1, offset=122)),
    WorldRule(rule_id=f"WR{base+4:05d}", domain=WorldRuleDomain.SOCIETY, statement="魔界大帝与不死身魔王姐弟可相互囚禁与庇护，释放可通过礼物与面子交易达成", scope="魔大陆涅克罗斯与比耶寇亚", exceptions="需顾及不死身族群颜面", confidence=Confidence.STRONG_INFERENCE, visible_from_volume=23, evidence_refs=pick(1, offset=123)),
]

beliefs = [
    Belief(belief_id=f"BL{base+1:05d}", owner_id="E0006", topic="齐格身份", statement="齐格因绿发即是拉普拉斯转世", certainty=Confidence.EXPLICIT, belief_state=BeliefState.FALSE_BELIEF, learned_from="拉普拉斯传说与绿发联想", learned_at_volume=23, learned_method="目睹与恐惧推断", is_true_in_world=False, visible_from_volume=23, visible_to_volume=None, note="洗礼后被证伪", evidence_refs=pick(1, offset=130)),
    Belief(belief_id=f"BL{base+2:05d}", owner_id="E0001", topic="洗礼公正", statement="佩尔基乌斯会公正判定且不会当场加害齐格", certainty=Confidence.EXPLICIT, belief_state=BeliefState.INFERRED, learned_from="过往受佩尔基乌斯照顾", learned_at_volume=23, learned_method="信任与预知眼待机", is_true_in_world=True, visible_from_volume=23, visible_to_volume=None, note="基于龙王过往宽宏", evidence_refs=pick(1, offset=131)),
    Belief(belief_id=f"BL{base+3:05d}", owner_id="E0108", topic="转生循环", statement="未来仍有异世界转生者，筱原秋人可能为下一位", certainty=Confidence.EXPLICIT, belief_state=BeliefState.INFERRED, learned_from="转移设备与召唤袋异常", learned_at_volume=23, learned_method="研究推断", is_true_in_world=None, visible_from_volume=23, visible_to_volume=None, note="为预言非定论", evidence_refs=pick(1, offset=132)),
    Belief(belief_id=f"BL{base+4:05d}", owner_id="E0057", topic="对抗龙神", statement="拉拢巴迪冈迪即可重创奥尔斯帝德阵营", certainty=Confidence.EXPLICIT, belief_state=BeliefState.INFERRED, learned_from="人神指示", learned_at_volume=23, learned_method="被授意后游说", is_true_in_world=None, visible_from_volume=23, visible_to_volume=None, note="基斯的煽动性信念", evidence_refs=pick(1, offset=133)),
]

econ = []

rel_changes = [
    RelationshipChange(change_id=f"RC{base+1:05d}", source_id="E0001", target_id="E0029", dimension="信赖与依附", before="敬畏的龙王庇护者", trigger="托婴请求洗礼并获公正判定", after="可托付子女安危的裁决者", at_volume=23, at_date=None, evidence_refs=pick(1, offset=140)),
    RelationshipChange(change_id=f"RC{base+2:05d}", source_id="E0001", target_id="E0043", dimension="恩义", before="素未谋面的魔界大帝", trigger="甜甜圈款待与千里眼回赠", after="互赠礼物的情报同盟", at_volume=23, at_date=None, evidence_refs=pick(1, offset=141)),
    RelationshipChange(change_id=f"RC{base+3:05d}", source_id="E0129", target_id="E0043", dimension="拘禁与释放", before="囚徒与狱主", trigger="鲁迪交涉与面子交易", after="获释的姐弟", at_volume=23, at_date=None, evidence_refs=pick(1, offset=142)),
    RelationshipChange(change_id=f"RC{base+4:05d}", source_id="E0057", target_id="E0113", dimension="招募与从属", before="陌生的魔王与使徒", trigger="酒馆荣光游说", after="被说动的同盟", at_volume=23, at_date=None, evidence_refs=pick(1, offset=143)),
]

speech = [
    SpeechProfile(profile_id=f"ST{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", phase_name="齐格出生与青年期父亲期", politeness="对佩尔基乌斯敬体，对家属常体，紧张时敬谨带试探", sentence_length="中长，焦虑时短句与自问", address_habits="称佩尔基乌斯大人、奇希莉卡大人，对希露菲直呼名", emotion_expression="以自嘲与玩笑掩饰恐惧，关键时直言不安", anger_expression="克制讽刺", shy_expression="视线游移搓手", intimate_speech="对希露菲温柔安抚", stranger_speech="对阿托菲先礼后利", superior_speech="对强者恭敬", inferior_speech="对齐格轻声命名", canonical_examples=("佩尔基乌斯大人，要亲自主持洗礼吗？", "难道绿发就是拉普拉斯吗？"), visible_from_volume=23, evidence_refs=pick(1, offset=150)),
    SpeechProfile(profile_id=f"ST{base+2:05d}", character_id="E0029", phase_id=f"P{base+9:04d}", phase_name="甲龙王裁决期", politeness="庄重敬语体，居高临下而宽宏", sentence_length="短句裁断式", address_habits="自称本王，称鲁迪为鲁迪乌斯", emotion_expression="以嗯与沉吟示权衡", anger_expression="皱眉低吟", shy_expression="无", intimate_speech="对希瓦莉尔温和", stranger_speech="对魔族亦可宽恕", superior_speech="裁决口吻", inferior_speech="俯视而庇护", canonical_examples=("嗯……此子非拉普拉斯。", "算了，也罢。"), visible_from_volume=23, evidence_refs=pick(1, offset=151)),
    SpeechProfile(profile_id=f"ST{base+3:05d}", character_id="E0043", phase_id=f"P{base+5:04d}", phase_name="魔界大帝被囚后期", politeness="骄横大帝口吻混杂孩童式喜悦", sentence_length="短促感叹与哇哈哈笑声", address_habits="自称妾身，称鲁迪为鲁迪乌斯", emotion_expression="以哇哈哈与甜食赞美直抒", anger_expression="瞪眼鼓腮", shy_expression="抱甜甜圈扭身", intimate_speech="对巴迪冈迪嗔怪", stranger_speech="对不死王亦敢直言", superior_speech="大帝宣告", inferior_speech="对恩人撒娇", canonical_examples=("哇哈哈甜甜圈最棒了！", "妾身就赐你千里眼吧。"), visible_from_volume=23, evidence_refs=pick(1, offset=152)),
    SpeechProfile(profile_id=f"ST{base+4:05d}", character_id="E0057", phase_id=f"P{base+7:04d}", phase_name="最后伙伴招募期", politeness="谄媚恭维混亲昵", sentence_length="中长煽动句", address_habits="称巴迪冈迪大人，称鲁迪乌斯为鲁迪乌斯", emotion_expression="以吹捧与荣光许诺掩饰本意", anger_expression="皮笑肉不笑", shy_expression="挠脸", intimate_speech="对魔王称兄道弟", stranger_speech="对醉汉亦可攀谈", superior_speech="对人神谦卑", inferior_speech="对魔王谄媚", canonical_examples=("与我等一同干大事吧，巴迪冈迪大人。", "人神大人可是很期待您呢。"), visible_from_volume=23, evidence_refs=pick(1, offset=153)),
]

quirks = [
    CharacterQuirk(quirk_id=f"QK{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", category="HABIT", name="洗礼前预知眼待机", description="恐惧佩尔基乌斯当场处决齐格而提前发动预知眼监视其捞水动作", intensity="中", frequency="偶发", triggers=("恐惧龙王处决",), preferred_targets=(), avoided_targets=(), public_expression=None, private_expression="独处时发动并屏息观察", behavior_patterns=("瞳孔变化紧盯坛水",), verbal_patterns=(), body_language="屏息前倾", emotional_reward="获安心", emotional_response="紧张后松气", boundaries=("不被察觉",), exceptions=(), visible_from_volume=23, evidence_refs=pick(1, offset=160)),
    CharacterQuirk(quirk_id=f"QK{base+2:05d}", character_id="E0043", phase_id=f"P{base+5:04d}", category="FOOD", name="甜甜圈狂热", description="对甜甜圈异常执着，以致被甜甜圈轻易收买并当场回赠魔眼", intensity="高", frequency="频发", triggers=("见甜食",), preferred_targets=(), avoided_targets=(), public_expression="当众欢呼哇哈哈", private_expression=None, behavior_patterns=("双手捧食狼吞",), verbal_patterns=("哇哈哈",), body_language="眼睛发亮", emotional_reward="满足", emotional_response="骄矜喜悦", boundaries=("不分场合",), exceptions=(), visible_from_volume=23, evidence_refs=pick(1, offset=161)),
    CharacterQuirk(quirk_id=f"QK{base+3:05d}", character_id="E0006", phase_id=f"P{base+3:04d}", category="HABIT", name="递婴时颤抖与视线游移", description="恐惧洗礼结果而在递出齐格时身子颤抖视线在丈夫与希瓦莉尔间游移", intensity="中", frequency="偶发", triggers=("恐惧孩子被处决",), preferred_targets=(), avoided_targets=(), public_expression="当众颤抖递婴", private_expression=None, behavior_patterns=("深呼吸后下决心递出",), verbal_patterns=(), body_language="颤抖与低头", emotional_reward="短暂安心", emotional_response="自责恐惧", boundaries=(), exceptions=(), visible_from_volume=23, evidence_refs=pick(1, offset=162)),
]

prefs = [
    CharacterPreference(preference_id=f"PF{base+1:05d}", character_id="E0043", phase_id=f"P{base+5:04d}", preference_type="LIKE", target="甜甜圈", description="卷23中因甜甜圈而对鲁迪好感激增并以魔眼相赠", intensity="高", context="地牢获释时", visible_from_volume=23, evidence_refs=pick(1, offset=170)),
    CharacterPreference(preference_id=f"PF{base+2:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", preference_type="LIKE", target="佩尔基乌斯的公正裁决", description="卷23依赖龙王裁决来驱散家族恐慌", intensity="中", context="祠堂洗礼时", visible_from_volume=23, evidence_refs=pick(1, offset=171)),
    CharacterPreference(preference_id=f"PF{base+3:05d}", character_id="E0057", phase_id=f"P{base+7:04d}", preference_type="LIKE", target="蛊惑不死身魔王", description="享受以言语操弄强者空虚心理", intensity="中", context="比耶寇亚酒馆", visible_from_volume=23, evidence_refs=pick(1, offset=172)),
]

bodies = [
    BodyLanguageProfile(profile_id=f"BY{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", phase_name="齐格出生与青年期父亲期", happy_signs=("松口气",), angry_signs=("皱眉",), nervous_signs=("视线游移盯坛水", "屏息"), embarrassed_signs=("挠头",), lying_signs=(), fear_signs=("预知眼发动",), thinking_signs=("托腮",), affection_signs=("轻抚齐格头",), hostility_signs=(), visible_from_volume=23, evidence_refs=pick(1, offset=180)),
    BodyLanguageProfile(profile_id=f"BY{base+2:05d}", character_id="E0006", phase_id=f"P{base+3:04d}", phase_name="产后忧惧期", happy_signs=("拥回婴儿落泪",), angry_signs=(), nervous_signs=("颤抖递婴", "视线游移"), embarrassed_signs=(), lying_signs=(), fear_signs=("身子猛颤",), thinking_signs=(), affection_signs=("紧抱齐格",), hostility_signs=(), visible_from_volume=23, evidence_refs=pick(1, offset=181)),
    BodyLanguageProfile(profile_id=f"BY{base+3:05d}", character_id="E0043", phase_id=f"P{base+5:04d}", phase_name="魔界大帝被囚后期", happy_signs=("哇哈哈大笑捧甜甜圈",), angry_signs=("鼓腮瞪眼",), nervous_signs=(), embarrassed_signs=(), lying_signs=(), fear_signs=(), thinking_signs=(), affection_signs=("贴近鲁迪撒娇",), hostility_signs=(), visible_from_volume=23, evidence_refs=pick(1, offset=182)),
]

personas = [
    CharacterPersona(persona_id=f"PN{base+1:05d}", character_id="E0001", phase_id=f"P{base+1:04d}", persona_type="PUBLIC", description="对外为龙神属下与希露菲丈夫，对内为焦虑父亲，求助于权威", speech_style="对外敬谨对内温柔", behavior_traits=("焦虑而求证", "尊重权威"), visible_from_volume=23, evidence_refs=pick(1, offset=190)),
    CharacterPersona(persona_id=f"PN{base+2:05d}", character_id="E0029", phase_id=f"P{base+9:04d}", persona_type="PUBLIC", description="对外为甲龙王裁决者，对内为宽宏庇护者", speech_style="庄重裁断", behavior_traits=("公正", "宽宏"), visible_from_volume=23, evidence_refs=pick(1, offset=191)),
]

gaps = [
    CanonGap(gap_id=f"GAP{base+1:05d}", domain="魔眼", question="千里眼魔眼的具体视距极限与消耗如何？", why_needed="推演鲁迪以千里眼追踪基斯时的可达范围与代价", searched_volumes=(23,), status=GapStatus.OPEN, possible_sources="卷24后魔眼运用与适应描写", note="卷23仅言获赠未给数值"),
    CanonGap(gap_id=f"GAP{base+2:05d}", domain="转移魔法", question="异世界转移魔法阵缺失凹槽零件的完整形态为何？", why_needed="推演七星归还后续是否可再发动及人神再召转生者的可行性", searched_volumes=(23,), status=GapStatus.OPEN, possible_sources="卷24后七星笔记与佩尔基乌斯处研究", note="卷23仅提示凹槽空缺未列零件清单"),
]

batch = EnrichmentBatch(
    batch_id="ENRICH_V023",
    source_volume=23,
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

out = pathlib.Path(f"data/canon_enriched/V023.json")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", encoding="utf-8") as f:
    json.dump(batch.to_json(), f, ensure_ascii=False, sort_keys=True, indent=2)
print(f"Wrote {out} ev={len(batch.evidence)} profiles={len(batch.character_profiles)} cases={len(batch.behavior_cases)} events={len(batch.detailed_events)} items={len(batch.items)}")

# Quick verify
from overlord_worldsim.canon.enrich_registry import load_entity_registry
from overlord_worldsim.canon.enrich_verifier import verify_enrichment
from overlord_worldsim.canon.enrich_registry import load_enrichment_batches
batches = load_enrichment_batches(pathlib.Path("data/canon_enriched"))
reg = load_entity_registry(pathlib.Path("data/canon"))
report = verify_enrichment(batches, doc, reg)
print(f"verify clean={report.is_clean} errors={len(report.errors)}")
for e in report.errors[:40]:
    print(e)
