import json, pathlib
from overlord_worldsim.canon.parse import parse_source
from overlord_worldsim.canon.enrich_model import (
    EvidenceRef, EvidenceType, EnrichmentBatch, CharacterProfile, BehaviorCase, DetailedEvent,
    EventPrerequisite, EventPrerequisiteKind, EventDependency, EventDependencyKind, StateChange,
    Belief, BeliefState, RelationshipChange, SpeechProfile, CharacterQuirk, CharacterPreference,
    BodyLanguageProfile, CharacterPersona, ItemDef, AbilityProfile, WorldRule, WorldRuleDomain,
    AbilityType, CanonGap, GapStatus, EventImportance, BehaviorTag
)
from overlord_worldsim.canon.extract_model import Confidence, DatePrecision
from overlord_worldsim.canon.enrich_registry import load_enrichment_batches, load_entity_registry
from overlord_worldsim.canon.enrich_verifier import verify_enrichment

raw = pathlib.Path("data/raw/无职转生TXT合集.txt").read_text(encoding="utf-8")
doc = parse_source(raw)
v4_chunks = [c for c in doc.chunks if c.volume_no==4]
# pick 24 spread indices
picked_indices = [0,2,4,5,7,8,9,10,13,15,17,18,20,22,26,30,34,37,40,42,46,52,58,61]
picked = [v4_chunks[i] for i in picked_indices if i < len(v4_chunks)]

notes = [
    "温恩港回望：鲁迪十一岁纵贯魔大陆抵达魔大陆唯一港都",
    "货币换算：魔大陆B委托百五石钱，米里斯B委托千五石钱相差十倍",
    "Dead End名声在公会传开，狂犬艾莉丝与看门犬瑞杰路德已有外号",
    "关卡询价：斯佩路德渡海要绿矿钱两百枚，官称防恐与奴隶作乱",
    "作战会议列三条路：正当赚钱太慢、闯迷宫危险、找走私最快",
    "人神梦谕：去摊位买大量串烧独自进小巷，像设局找饿肚子小孩",
    "次日依谕买串烧进小巷徘徊，反思被花言巧语牵走想最后一次听从",
    "巷内岩弹击倒拉扯少女的凶男，调整力道留活口观察后续",
    "紫发山羊角少女自称魔界大帝奇希莉卡，称饿了一年未进食",
    "奇希莉卡说鲁迪魔力量胜拉普拉斯，点出双胞胎与一死一生",
    "赠魔眼前的推辞与戏弄，奇希莉卡蹦上屋顶说去找巴迪冈迪",
    "得魔眼后惊喜不安，想起剑术老师眼罩下也藏魔眼",
    "沙滩木棒对峙：艾莉丝自信满满说有了魔眼别想赢",
    "比试后艾莉丝抱膝闷闷不乐，鲁迪满心邪念被打断",
    "夜里思索渡海仍无解，觉得得到只有魔眼连赌博也无用",
    "瑞杰路德视走私贩为恶，因其清单常含奴隶与儿童拐卖",
    "贾尔斯说欠恩必还尽快清账，报名后承接走私组织委托",
    "洛琪希踏上温恩港，见街景似赞特港急于寻鲁迪与家人",
    "艾莉娜丽洁与塔尔争吵，洛琪希以中立调停晕船与琐事",
    "贾尔斯约定十五天后通报，任务是放走被关对象送回家",
    "抵达赞特港，木造增多，鲁迪忆艾莉丝曾睡马厩稻草堆",
    "洞窟潮湿行一小时入森，瑞杰路德低声提醒人多须警惕",
    "七名兽耳少年少女全裸被铐，鲁迪向猫耳少女问被抓缘由",
    "裘斯塔夫自称为德路迪亚老战士基列奴兄长，誓要将孩子送回",
]

evidence = []
for idx, chunk in enumerate(picked):
    eid = f"EV040{idx+1:02d}"
    note = notes[idx] if idx < len(notes) else f"V04证据{idx+1} " + chunk.text[:30].replace("\n"," ")
    et = EvidenceType.CANON_EXPLICIT if idx < 17 else EvidenceType.STRONG_INFERENCE
    conf = Confidence.EXPLICIT if idx < 17 else Confidence.STRONG_INFERENCE
    evidence.append(EvidenceRef(
        evidence_id=eid, volume_no=4, unit_id=chunk.unit_id, chapter_title=chunk.chapter_title,
        source_start_line=chunk.source_start_line, source_end_line=chunk.source_end_line,
        evidence_type=et, confidence=conf, note=note,
    ))

def ev(*nums):
    return tuple(f"EV040{n:02d}" for n in nums)

profiles = [
    CharacterProfile(profile_id="CP04001", character_id="E0001", phase_id="P04001", phase_name="温恩港至德路迪亚村漂流期", start_date=None, end_date=None, date_precision=DatePrecision.UNKNOWN, age_description="十一岁，已为A级冒险者Dead End参谋", personality_traits=("谨慎","好色妄想","重情义","好学"), values=("与艾莉丝瑞杰路德同行回家","替瑞杰路德挽回族名"), desires=("尽快筹措两百绿矿钱渡海","让艾莉丝安稳成长"), fears=("再被卷入拐卖组织","与同伴分散"), taboos=("抛下瑞杰路德单独渡海",), insecurities=("魔眼失控","被误认冒牌Dead End"), pride="无咏唱魔术与岩炮弹", impulsiveness="MEDIUM", patience="MEDIUM", risk_tolerance="MEDIUM", self_control="MEDIUM", attachment_style="对艾莉丝半监护半倾慕，对瑞杰路德敬依赖", authority_attitude="对关卡与走私头目表面恭敬私下盘算", family_attitude="挂念塞妮丝与妹妹们", romantic_attitude="对艾莉丝有少年倾慕但克制", violence_attitude="能下手但尽量以岩炮弹击晕留活口", money_attitude="精算石钱与绿矿钱汇率", status_attitude="不在意饲主外号更求实利", race_attitude="愿为斯佩路德族正名", religious_attitude="无", loyalty="HIGH", ambition="MODERATE", short_term_goals=("取得渡海船位","安顿蜥蜴与住处","试控预知眼"), long_term_goals=("回到菲托亚寻找家人",), obligations=("看护艾莉丝","偿还瑞杰路德恩情"), decision_tendencies=("列三选项再挑","先问价再决断","遇人神谕先试一次"), speech_tendencies=("对艾莉丝轻佻玩笑","对瑞杰路德认真请教","对蕾儿式敬语"), social_tendencies=("在公会柜台与关卡主动探听",), conflict_tendencies=("以岩弹先制后补救","能谈则谈不妄杀"), known_skills=("无咏唱多系魔术","岩炮弹","治愈术"), knowledge_state=("知斯佩路德渡海高价","知人神梦谕","知魔眼来源"), relationship_tendencies=("对艾莉丝制止与调侃","对瑞杰路德参谋汇报"), behavior_changes_note="从初到港都观光心态转为筹划走私与试控魔眼的务实参谋", summary="十一岁的鲁迪在温恩港为两百绿矿钱发愁，依人神谕得预知眼后转向走私合作与德路迪亚解救。", visible_from_volume=4, visible_to_volume=None, evidence_refs=ev(4,5,6,11,15)),
    CharacterProfile(profile_id="CP04002", character_id="E0031", phase_id="P04002", phase_name="护卫正名期", start_date=None, end_date=None, date_precision=DatePrecision.UNKNOWN, age_description="斯佩路德战士，剃光头掩绿发", personality_traits=("严肃","重诺","爱护孩童","寡言"), values=("守护孩子","以行动洗刷族名"), desires=("让世人知斯佩路德并非恶魔","安全送艾莉丝回家"), fears=("族名再被利用作恶","护卫失职"), taboos=("参与奴隶买卖",), insecurities=("过度自责连累路费",), pride="额头感觉器官与枪术", impulsiveness="LOW", patience="HIGH", risk_tolerance="LOW", self_control="HIGH", attachment_style="对鲁迪艾莉丝如监护人", authority_attitude="对走私头目不让步", family_attitude="视同伴为家族", romantic_attitude="无", violence_attitude="必要时果断击杀走私恶徒", money_attitude="视钱为负担不贪", status_attitude="不求名只求正名", race_attitude="以身示范族与族可共处", religious_attitude="无", loyalty="HIGH", ambition="LOW", short_term_goals=("探清走私据点","守住仓库孩子"), long_term_goals=("重建斯佩路德名誉",), obligations=("护送艾莉丝","看住鲁迪别乱来"), decision_tendencies=("先观察再出手","拒绝迷宫冒险"), speech_tendencies=("短句制止艾莉丝","低声对鲁迪耳语警示"), social_tendencies=("在公会被认出后淡然处之",), conflict_tendencies=("正面迎敌掩护孩子",), known_skills=("斯佩路德枪术","额头索敌","徒手制敌"), knowledge_state=("知渡海歧视价","知走私与拐卖勾连"), relationship_tendencies=("对鲁迪像父亲般指正","对艾莉丝拉住制止"), behavior_changes_note="从独行战士转为以Dead End名号公开行动的护卫者", summary="剃光头的瑞杰路德为高额船费自责，却坚持不与拐卖同流并独担解救。", visible_from_volume=4, visible_to_volume=None, evidence_refs=ev(4,16,22,23)),
    CharacterProfile(profile_id="CP04003", character_id="E0021", phase_id="P04003", phase_name="渡海前少女期", start_date=None, end_date=None, date_precision=DatePrecision.UNKNOWN, age_description="十三岁，阿斯拉贵族少女，红发", personality_traits=("直率","好胜","任性","重情"), values=("与鲁迪同行","不被当小鬼"), desires=("下海游泳","在沙滩比试赢鲁迪"), fears=("再次被卷绑架","在众人前丢脸"), taboos=("被摸臀不道歉",), insecurities=("魔神语读写仍弱",), pride="剑术与体能", impulsiveness="HIGH", patience="LOW", risk_tolerance="HIGH", self_control="LOW", attachment_style="对鲁迪依赖与斗嘴", authority_attitude="对瑞杰路德尊敬听制止", family_attitude="念祖父绍罗斯", romantic_attitude="对鲁迪朦胧好感", violence_attitude="一言不合即痛扁", money_attitude="不计较", status_attitude="不以贵族自居", race_attitude="与魔族同行无隔阂", religious_attitude="无", loyalty="HIGH", ambition="MODERATE", short_term_goals=("学会魔神语读写","沙滩上赢一场"), long_term_goals=("回到菲托亚",), obligations=("听瑞杰路德制止",), decision_tendencies=("先冲再思考","被制止才收手"), speech_tendencies=("流利魔神语带贵族腔","怒时连发你摸了哪里"), social_tendencies=("在公会一呼百应围观",), conflict_tendencies=("追打骚扰者至要害",), known_skills=("基础剑术","魔神语口语"), knowledge_state=("知大海与港口规矩","知Dead End外号"), relationship_tendencies=("与鲁迪斗嘴又偷瞄","对瑞杰路德信服"), behavior_changes_note="从凶猛大小姐学会在魔大陆用魔神语吵架与沙滩比试", summary="十三岁的艾莉丝在温恩港从好斗少女转为能在魔神语与沙滩比试中成长的同伴。", visible_from_volume=4, visible_to_volume=None, evidence_refs=ev(1,3,13,14)),
    CharacterProfile(profile_id="CP04004", character_id="E0043", phase_id="P04004", phase_name="复活饿倒期", start_date=None, end_date=None, date_precision=DatePrecision.UNKNOWN, age_description="外表幼女，紫发山羊角，魔界大帝", personality_traits=("张扬","喜演","重礼节","孩子气"), values=("受人跪拜","有恩必赏"), desires=("填饱肚子","赴约巴迪冈迪"), fears=("被拉普拉斯知饿倒丑态",), taboos=("让人久饿",), insecurities=("被当Cos小孩",), pride="不死身与魔眼赐予", impulsiveness="MEDIUM", patience="LOW", risk_tolerance="HIGH", self_control="LOW", attachment_style="对救命人随性亲近", authority_attitude="自居帝王要求行礼", family_attitude="无", romantic_attitude="无", violence_attitude="不轻动手", money_attitude="不涉金钱", status_attitude="极重帝号", race_attitude="视各族为臣民", religious_attitude="无", loyalty="MEDIUM", ambition="HIGH", short_term_goals=("饱餐后再撑一年","寻巴迪冈迪"), long_term_goals=("重建魔族秩序",), obligations=("回赠魔眼",), decision_tendencies=("见魔量即断双胞胎","说走就跳屋顶"), speech_tendencies=("本宫自称","呼哈哈大笑"), social_tendencies=("在巷内与鲁迪一问一答",), conflict_tendencies=("以魔眼话题压人",), known_skills=("魔眼赐予","瞬间识魔量"), knowledge_state=("知拉普拉斯","知鲁迪双胞胎底细"), relationship_tendencies=("对鲁迪由审视到赠礼",), behavior_changes_note="从饿倒墙边到饱餐后蹦跳赠魔眼的帝王作派", summary="复活三百年后饿倒小巷的奇希莉卡，受串烧得救即赠预知眼。", visible_from_volume=4, visible_to_volume=None, evidence_refs=ev(8,9,10,11)),
    CharacterProfile(profile_id="CP04005", character_id="E0005", phase_id="P04005", phase_name="追踪弟子期", start_date=None, end_date=None, date_precision=DatePrecision.UNKNOWN, age_description="米格路德族少女，魔术师，持杖", personality_traits=("认真","细心","宽容","自省"), values=("找到鲁迪与塞妮丝","履行教师责任"), desires=("重逢弟子","收集Dead End情报"), fears=("再与同伴争吵失散",), taboos=("放任艾莉娜丽洁乱来",), insecurities=("担心被误认为少女",), pride="水圣级魔术与教学", impulsiveness="LOW", patience="MEDIUM", risk_tolerance="LOW", self_control="HIGH", attachment_style="对鲁迪如师如姊", authority_attitude="对冒险者公会礼貌询问", family_attitude="牵挂米格路德村", romantic_attitude="对塔尔韩德保持距离", violence_attitude="非必要不动冰霜击", money_attitude="节约", status_attitude="不以魔族自卑", race_attitude="察觉瑞杰路德身份仍冷静", religious_attitude="无", loyalty="HIGH", ambition="MODERATE", short_term_goals=("在温恩港打听情报","前往米里斯"), long_term_goals=("带鲁迪回家",), obligations=("照看艾莉娜丽洁与塔尔",), decision_tendencies=("先观察再发问","冲突时居中调停"), speech_tendencies=("温和敬语","对同伴直言相劝"), social_tendencies=("在公会四处观察",), conflict_tendencies=("以冰霜击误毁旅社半栋",), known_skills=("水系魔术","冰霜击","教学"), knowledge_state=("知温恩与赞特相似","知鲁迪才能显眼"), relationship_tendencies=("对艾莉娜丽洁劝诫","对塔尔韩德制止"), behavior_changes_note="从海上旅程晕船到踏上魔大陆独立探访", summary="踏上温恩港的洛琪希为寻鲁迪一家而重新启程，仍以教师心态行事。", visible_from_volume=4, visible_to_volume=None, evidence_refs=ev(18,19)),
    CharacterProfile(profile_id="CP04006", character_id="E0057", phase_id="P04006", phase_name="牢中相识期", start_date=None, end_date=None, date_precision=DatePrecision.UNKNOWN, age_description="猴脸轻佻青年，嗜赌", personality_traits=("轻浮","好赌","有义气","怕事"), values=("欠钱必还","小恩小惠记心"), desires=("早日出狱","赢点赌本"), fears=("被圣兽报复","被战士厌恶"), taboos=("赖账",), insecurities=("战力弱被轻视",), pride="嘴皮与消息", impulsiveness="MEDIUM", patience="LOW", risk_tolerance="HIGH", self_control="LOW", attachment_style="对同牢鲁迪套近乎", authority_attitude="对裘耶斯等战士畏缩", family_attitude="无", romantic_attitude="无", violence_attitude="不正面打", money_attitude="嗜赌轻财", status_attitude="不求名", race_attitude="对兽族亲近", religious_attitude="无", loyalty="MEDIUM", ambition="LOW", short_term_goals=("借背心保暖","打探失火逃路"), long_term_goals=("混口饭吃",), obligations=("报瑞杰路德救命之恩",), decision_tendencies=("嘴上轻佻实则察言观色","有烟味先示警"), speech_tendencies=("前辈新人互称",), social_tendencies=("牢中与鲁迪聊天解闷",), conflict_tendencies=("逃跑时抱肩跳下",), known_skills=("赌博","牢中生存","消息探听"), knowledge_state=("知雨季与失火动乱","知圣兽与村落关系"), relationship_tendencies=("对鲁迪由借衣到共逃","对瑞杰路德感恩"), behavior_changes_note="从赌徒新人到与鲁迪共历失火与村庄袭击的同牢同伴", summary="牢里的轻佻赌徒基斯，意外与鲁迪共患难并在失火中协作逃生。", visible_from_volume=4, visible_to_volume=None, evidence_refs=ev(23,24)),
]

cases = [
    BehaviorCase(case_id="BC04001", character_id="E0001", phase_id="P04001", phase_name="温恩港至德路迪亚村漂流期", volume_no=4, situation_type="渡海筹款", context="温恩港关卡告知斯佩路德需两百绿矿钱，人族只需铁钱五枚", trigger="三人合计费用高到需一年积攒，瑞杰路德面露自责", available_information="知B级差价十倍、知关卡拜金只要付钱就能过", action="列出三条路并倾向找走私贩，先去冒险者公会探价再决定", verbal_response="方法有三种，先靠委托、再闯迷宫、最后找走私", emotional_response="对高价惊愕转务实盘算", goal_at_time="尽快凑齐船费又别抛下瑞杰路德", relationship_context="对瑞杰路德安抚，对艾莉丝商量", social_context="旅社晚餐后作战会议", immediate_outcome="定调先观望船期再试走私联络", long_term_outcome="走向与走私组织接触并承接委托", tags=(BehaviorTag.MONEY, BehaviorTag.NEGOTIATION, BehaviorTag.FAMILY), evidence_refs=ev(4,5)),
    BehaviorCase(case_id="BC04002", character_id="E0001", phase_id="P04001", phase_name="温恩港至德路迪亚村漂流期", volume_no=4, situation_type="依神谕行动", context="人神梦中让去摊位买串烧独自进小巷，像要过上饿倒小孩", trigger="被嘲一年未现身，人神说别想太复杂会有有趣发展", available_information="知近期无信仰依赖，但想验证是否真有奖赏", action="次日买干贝贝柱与烤鱼等串烧，刻意避开同伴独自进巷", verbal_response="先老实照办，最后一次随他摆布", emotional_response="既觉得被玩弄又期待爽到的可能", goal_at_time="验证神谕真伪顺手蹭奖励", relationship_context="瞒着瑞杰路德与艾莉丝单独行动", social_context="小巷独行", immediate_outcome="撞见被凶男拉扯的紫发少女", long_term_outcome="获预知眼改变后段战法", tags=(BehaviorTag.SUSPICION, BehaviorTag.DANGER, BehaviorTag.TRUST), evidence_refs=ev(6,7)),
    BehaviorCase(case_id="BC04003", character_id="E0001", phase_id="P04001", phase_name="温恩港至德路迪亚村漂流期", volume_no=4, situation_type="巷内救人", context="瞥见凶男拉少女手，以为是典型拐带", trigger="少女坐墙边被拉，男子满脸泛红笑容", available_information="知拐卖多、岩弹可调力道", action="率先投岩弹调至职业拳击刺拳力道，二击碎脸放倒", verbal_response="你没事吧小姐", emotional_response="自认为爽朗正义实则色心", goal_at_time="救少女并博好感", relationship_context="对陌生少女搭讪，对倒地男不管", social_context="巷内独对", immediate_outcome="男子昏倒，少女却惊呼认识", long_term_outcome="揭露对方是魔界大帝与魔眼契机", tags=(BehaviorTag.COMBAT, BehaviorTag.PROTECT, BehaviorTag.EMBARRASSMENT), evidence_refs=ev(8,9)),
    BehaviorCase(case_id="BC04004", character_id="E0001", phase_id="P04001", phase_name="温恩港至德路迪亚村漂流期", volume_no=4, situation_type="试控魔眼", context="得魔眼后回旅社，艾莉丝正抱膝气恼", trigger="艾莉丝提议比试以检验魔眼实战", available_information="知魔眼可预见零点几秒后动作", action="与艾莉丝到沙滩以木棒对峙，靠预知先一步格挡胜一回", verbal_response="你以为有了魔眼就能赢吗那就试试", emotional_response="兴奋又怕失控", goal_at_time="在近身战中不用魔术赢一次", relationship_context="与艾莉丝一对一比试，瑞杰路德见证", social_context="沙滩公开比试", immediate_outcome="首次不用魔术打赢艾莉丝", long_term_outcome="坚定修炼魔眼与体术结合", tags=(BehaviorTag.TRAINING, BehaviorTag.SUCCESS, BehaviorTag.FRIENDSHIP), evidence_refs=ev(13,14)),
    BehaviorCase(case_id="BC04005", character_id="E0043", phase_id="P04004", phase_name="复活饿倒期", volume_no=4, situation_type="受救回赠", context="被投喂后恢复力气，空翻起身", trigger="被说恶心后仍获三根串烧并夺走剩余十根", available_information="观鲁迪魔量异常高、察觉双胞胎底细", action="跳上屋顶前赠预知眼并说去找巴迪冈迪有困扰可求助", verbal_response="很好你确实能看到吧，本宫差不多该走了", emotional_response="兴高采烈带咳笑", goal_at_time="报食物之恩并留下再会话头", relationship_context="对鲁迪由审视转赏赐", social_context="巷内二人", immediate_outcome="鲁迪获预知眼", long_term_outcome="鲁迪短期战力质变", tags=(BehaviorTag.GRATITUDE, BehaviorTag.SUCCESS, BehaviorTag.HUMOR), evidence_refs=ev(10,11)),
    BehaviorCase(case_id="BC04006", character_id="E0001", phase_id="P04001", phase_name="温恩港至德路迪亚村漂流期", volume_no=4, situation_type="走私谈判", context="夜会贾尔斯，谈及走私清单含奴隶", trigger="贾尔斯说欠恩必还尽快清账，提运兽族孩子委托", available_information="知瑞杰路德厌恶拐卖，知价差与风险", action="与瑞杰路德对视后答应承接，约定放走被关对象并送回家", verbal_response="我明白了就接受吧", emotional_response="犹豫后转向务实", goal_at_time="以低价换船位同时救人", relationship_context="与瑞杰路德同决，与贾尔斯立约", social_context="旅社私会", immediate_outcome="定下存放建筑位置与行动不问手段", long_term_outcome="潜入赞特港仓库与洞窟", tags=(BehaviorTag.NEGOTIATION, BehaviorTag.MORAL_CHOICE, BehaviorTag.TRUST), evidence_refs=ev(16,20)),
    BehaviorCase(case_id="BC04007", character_id="E0001", phase_id="P04001", phase_name="温恩港至德路迪亚村漂流期", volume_no=4, situation_type="仓库救出", context="赞特港潮湿洞窟行一小时入森，到仓库见全裸兽耳七孩被铐", trigger="猫耳少女不哭，其余孩子缩团发抖", available_information="知组织用孩子作货，知瑞杰路德在外放风", action="上前软言询问被抓原因，让猫耳少女开口说明经过", verbal_response="我可以请教你们被抓来这里的原因吗喵", emotional_response="怜惜与克制杂念", goal_at_time="安抚并套取情报以利带回", relationship_context="对猫耳少女为问话对象", social_context="昏暗房间", immediate_outcome="猫耳少女带头回应", long_term_outcome="定下不走原洞窟改走森林回镇", tags=(BehaviorTag.PROTECT, BehaviorTag.NEGOTIATION, BehaviorTag.FAMILY), evidence_refs=ev(22,23)),
    BehaviorCase(case_id="BC04008", character_id="E0031", phase_id="P04002", phase_name="护卫正名期", volume_no=4, situation_type="处决恶徒", context="确认仓库外莫霍克男等走私贩欲作恶", trigger="鲁迪耳语告知孩子被关细节，脸色难看", available_information="知组织与拐卖勾连，知自己额头可索敌", action="独力出击击杀走私恶徒，留鲁迪负责解铐带孩子", verbal_response="别露出那种表情，你的双手要用来保护艾莉丝", emotional_response="愤怒而克制", goal_at_time="肃清拐卖链并保孩子活口", relationship_context="对鲁迪分工，对恶徒零容忍", social_context="仓库外林地", immediate_outcome="仓库肃清", long_term_outcome="孩子得救被裘斯塔夫接应", tags=(BehaviorTag.COMBAT, BehaviorTag.PROTECT, BehaviorTag.ANGER), evidence_refs=ev(22,23)),
    BehaviorCase(case_id="BC04009", character_id="E0001", phase_id="P04001", phase_name="温恩港至德路迪亚村漂流期", volume_no=4, situation_type="牢狱共处", context="因解救过程被裘耶斯误判关进免费公寓牢房", trigger="裘耶斯以疑犯名义枷住，称回来前不准动手", available_information="知雨季、知圣兽珍贵、知不能硬闯", action="与基斯同牢聊天，借背心、探烟味与热度异常", verbal_response="前辈你的背心看起来挺暖的给我吧", emotional_response="无奈转自嘲", goal_at_time="熬过关押等瑞杰路德接应", relationship_context="与基斯新人前辈互称", social_context="牢内双人房", immediate_outcome="探得失火前兆", long_term_outcome="借混乱逃出并投入村庄防卫", tags=(BehaviorTag.FRIENDSHIP, BehaviorTag.DANGER, BehaviorTag.HUMOR), evidence_refs=ev(23,24)),
    BehaviorCase(case_id="BC04010", character_id="E0001", phase_id="P04001", phase_name="温恩港至德路迪亚村漂流期", volume_no=4, situation_type="失火逃生", context="闻到呛烟与热气，远方传吵杂", trigger="基斯说有烟，鲁迪竖耳确认", available_information="知村内木造密集，牢门可破", action="与基斯合力踹开牢门，冲出后岩炮弹击晕沿途拦路人族打手", verbal_response="岩炮弹", emotional_response="急迫而兴奋", goal_at_time="冲出火场并弄清袭击真相", relationship_context="与基斯共逃，与人族打手对敌", social_context="村庄火场", immediate_outcome="逃至外围见人族追杀兽族", long_term_outcome="转入护兽作战与对峙贾尔斯", tags=(BehaviorTag.DANGER, BehaviorTag.COMBAT, BehaviorTag.PROTECT), evidence_refs=ev(24,)),
    BehaviorCase(case_id="BC04011", character_id="E0005", phase_id="P04005", phase_name="追踪弟子期", volume_no=4, situation_type="港都打听", context="刚下船到温恩港，见街景似赞特港", trigger="问及Dead End冒牌真货议论", available_information="知鲁迪显眼必留痕迹", action="带艾莉娜丽洁与塔尔在公会四处观察，记录旅人传闻", verbal_response="要吵请晚点再吵，先收集情报", emotional_response="急切而克制嫌恶", goal_at_time="捕捉鲁迪与塞妮丝线索", relationship_context="对艾莉娜丽洁管束，对塔尔韩德制止", social_context="公会内", immediate_outcome="听闻Dead End队伍情报", long_term_outcome="决定继续往米里斯大陆追踪", tags=(BehaviorTag.REQUEST, BehaviorTag.FRIENDSHIP, BehaviorTag.SUSPICION), evidence_refs=ev(18,19)),
    BehaviorCase(case_id="BC04012", character_id="E0001", phase_id="P04001", phase_name="温恩港至德路迪亚村漂流期", volume_no=4, situation_type="护兽对峙", context="村庄遇袭，人族打手挟圣兽与少年作人质", trigger="贾尔斯以剑抵少年脖颈嘲讽饲主", available_information="知圣兽被视为神，知投鼠忌器", action="以冲击波弹开贾尔斯与人质距离，让圣兽逃脱再对峙", verbal_response="放开那孩子", emotional_response="怒与紧绷", goal_at_time="保住圣兽与人质活口", relationship_context="对贾尔斯对峙，对圣兽急救", social_context="村庄森林边", immediate_outcome="人质与圣兽脱离剑尖", long_term_outcome="裘斯塔夫率众接管残局并邀请留村过雨季", tags=(BehaviorTag.COMBAT, BehaviorTag.PROTECT, BehaviorTag.NEGOTIATION), evidence_refs=ev(24,)),
]

events = [
    DetailedEvent(event_id="DE04001", event_type="神谕获宝", title="小巷魔眼获赠", timeline_event_id="T0013", time_date=None, time_precision=DatePrecision.UNKNOWN, time_note="温恩港滞留期，人神梦谕次日白天小巷", volume_no=4, location_id=None, participants=("E0001","E0043","E0032"), prerequisites=(EventPrerequisite(prerequisite_id="EP04001", prerequisite_type=EventPrerequisiteKind.STATE, ref_id=None, statement="人神梦中让去摊位买串烧独自进小巷", evidence_refs=ev(6,)), EventPrerequisite(prerequisite_id="EP04002", prerequisite_type=EventPrerequisiteKind.PERSON_PRESENT, ref_id="E0001", statement="鲁迪独自带十二根串烧进巷", evidence_refs=ev(7,))), dependencies=(), state_changes=(StateChange(change_id="SC04001", change_kind="能力获得", subject_id="E0001", before="无魔眼", after="获预知眼可视零点几秒后"), StateChange(change_id="SC04002", change_kind="关系建立", subject_id="E0043", before="饥饿倒地", after="受喂饱赠礼离去")), trigger="以岩弹击倒凶男后见饿倒紫发少女求食", actions=("投喂三根并被夺十根","听双胞胎与魔量点评","受赠魔眼并目送跳屋顶"), outcome="鲁迪获预知眼，奇希莉卡赴巴迪冈迪", relationship_change_ids=("RC04001",), belief_ids=("BL04001","BL04002"), canon_importance=EventImportance.MAJOR, evidence_refs=ev(8,9,10)),
    DetailedEvent(event_id="DE04002", event_type="潜入解救", title="赞特港仓库救出兽族孩子", timeline_event_id="T0015", time_date=None, time_precision=DatePrecision.UNKNOWN, time_note="承接走私委托后约十五天，赞特港洞窟仓库", volume_no=4, location_id=None, participants=("E0001","E0031","E0053","E0054"), prerequisites=(EventPrerequisite(prerequisite_id="EP04003", prerequisite_type=EventPrerequisiteKind.KNOWLEDGE, ref_id=None, statement="知存放建筑位置与不问手段", evidence_refs=ev(20,)), EventPrerequisite(prerequisite_id="EP04004", prerequisite_type=EventPrerequisiteKind.PERSON_PRESENT, ref_id="E0031", statement="瑞杰路德同行持索敌", evidence_refs=ev(22,))), dependencies=(EventDependency(dependency_id="ED04001", dependency_type=EventDependencyKind.REQUIRES, target_event_id="DE04001", statement="获魔眼后才有近身应对底气"),), state_changes=(StateChange(change_id="SC04003", change_kind="人身解放", subject_id="E0053", before="七孩被铐全裸", after="被解铐带离仓库"), StateChange(change_id="SC04004", change_kind="敌对肃清", subject_id="E0031", before="走私贩占仓", after="被击杀或驱散")), trigger="贾尔斯提供情报指让放走被关对象", actions=("穿潮湿洞窟一小时入森","瑞杰路德低声分工","鲁迪软言问猫耳少女并解铐"), outcome="七孩获救由裘斯塔夫接应回父母", relationship_change_ids=("RC04002",), belief_ids=("BL04003",), canon_importance=EventImportance.MAJOR, evidence_refs=ev(21,22,23)),
    DetailedEvent(event_id="DE04003", event_type="动乱", title="德路迪亚村失火与人族袭击", timeline_event_id="T0016", time_date=None, time_precision=DatePrecision.UNKNOWN, time_note="被关免费公寓第六天，村庄雨季前", volume_no=4, location_id=None, participants=("E0001","E0057","E0031","E0053"), prerequisites=(EventPrerequisite(prerequisite_id="EP04005", prerequisite_type=EventPrerequisiteKind.STATE, ref_id=None, statement="鲁迪与基斯被当疑犯关押，瑞杰路德在外联络", evidence_refs=ev(23,)),), dependencies=(EventDependency(dependency_id="ED04002", dependency_type=EventDependencyKind.CAUSES, target_event_id="DE04002", statement="救出后组织报复联手人族袭村"),), state_changes=(StateChange(change_id="SC04005", change_kind="住所焚毁", subject_id="E0053", before="村庄安宁", after="多屋失火族人四散"), StateChange(change_id="SC04006", change_kind="身份洗清", subject_id="E0001", before="疑犯关押", after="以救火与击退打手自证")), trigger="牢内闻呛烟热气远方吵杂，基斯示警", actions=("踹开牢门冲出","岩炮弹连击拦路人族","转入护村与圣兽对峙"), outcome="火势受控，打手被逐，圣兽获救", relationship_change_ids=("RC04003",), belief_ids=("BL04004",), canon_importance=EventImportance.MAJOR, evidence_refs=ev(24,)),
    DetailedEvent(event_id="DE04004", event_type="外传追踪", title="洛琪希温恩港追踪线", timeline_event_id=None, time_date=None, time_precision=DatePrecision.UNKNOWN, time_note="鲁迪离港前后，洛琪希船抵温恩港", volume_no=4, location_id=None, participants=("E0005",), prerequisites=(EventPrerequisite(prerequisite_id="EP04006", prerequisite_type=EventPrerequisiteKind.STATE, ref_id=None, statement="洛琪希结束海旅为寻鲁迪踏上魔大陆", evidence_refs=ev(18,)),), dependencies=(), state_changes=(StateChange(change_id="SC04007", change_kind="情报衔接", subject_id="E0005", before="无鲁迪踪迹", after="听闻Dead End传闻"),), trigger="见温恩与赞特街景相似而警觉", actions=("与艾莉娜丽洁塔尔韩德分头观察公会","调停争吵","收束准备追往米里斯"), outcome="错过鲁迪但锁定方向继续追踪", relationship_change_ids=(), belief_ids=("BL04005",), canon_importance=EventImportance.MINOR, evidence_refs=ev(18,19)),
    DetailedEvent(event_id="DE04005", event_type="渡海", title="化身机械的治疗与渡海准备", timeline_event_id="T0014", time_date=None, time_precision=DatePrecision.UNKNOWN, time_note="村庄安定后，沿圣剑大道北上", volume_no=4, location_id=None, participants=("E0001","E0021","E0031"), prerequisites=(EventPrerequisite(prerequisite_id="EP04007", prerequisite_type=EventPrerequisiteKind.PERSON_PRESENT, ref_id="E0001", statement="三人受邀雨季留村后决定北上", evidence_refs=ev(24,)),), dependencies=(EventDependency(dependency_id="ED04003", dependency_type=EventDependencyKind.ENABLES, target_event_id="DE04002", statement="完成解救与防卫后才有安稳北上"),), state_changes=(StateChange(change_id="SC04008", change_kind="行程推进", subject_id="E0001", before="滞留德路迪亚村", after="沿圣剑大道驶向米里斯首都"), StateChange(change_id="SC04009", change_kind="治疗关系", subject_id="E0021", before="需定期治疗姿势尴尬", after="鲁迪化身机械闭眼塞耳执行")), trigger="为防晕船与雨季而整备马车", actions=("收拾行装告别裘斯塔夫","化身机械闭眼塞耳施治疗","沿直线大道北行"), outcome="队伍离开大森林踏上圣剑大道", relationship_change_ids=("RC04004",), belief_ids=("BL04006",), canon_importance=EventImportance.MAJOR, evidence_refs=ev(24,)),
]

beliefs = [
    Belief(belief_id="BL04001", owner_id="E0001", topic="魔眼价值", statement="预知眼能让近身战补足短板，值得花一星期掌控", certainty=Confidence.EXPLICIT, belief_state=BeliefState.FACT_KNOWN, learned_from="E0043", learned_at_volume=4, learned_method="受赠后试用与沙滩比试验证", is_true_in_world=True, visible_from_volume=4, visible_to_volume=None, note="想起老师眼罩并靠沙滩一胜确认有用", evidence_refs=ev(11,13)),
    Belief(belief_id="BL04002", owner_id="E0001", topic="人神可信度", statement="人神谕有时灵但别想太复杂，老实照办反而称其心意", certainty=Confidence.STRONG_INFERENCE, belief_state=BeliefState.INFERRED, learned_from="E0032", learned_at_volume=4, learned_method="梦对话与次日应验对比", is_true_in_world=True, visible_from_volume=4, visible_to_volume=None, note="被说想复杂才有趣，决定最后一次照办", evidence_refs=ev(6,7)),
    Belief(belief_id="BL04003", owner_id="E0031", topic="走私贩定性", statement="走私组织与拐卖链勾连，清单必含奴隶与兽族孩子", certainty=Confidence.EXPLICIT, belief_state=BeliefState.FACT_KNOWN, learned_from=None, learned_at_volume=4, learned_method="仓库现场与贾尔斯口径印证", is_true_in_world=True, visible_from_volume=4, visible_to_volume=None, note="见七孩全裸被铐确认恶行", evidence_refs=ev(16,22)),
    Belief(belief_id="BL04004", owner_id="E0001", topic="村庄危机", statement="组织会联手人族在雨季前袭村，目标是掳女性与圣兽", certainty=Confidence.EXPLICIT, belief_state=BeliefState.FACT_KNOWN, learned_from="E0053", learned_at_volume=4, learned_method="裘斯塔夫战后说明与牢中失火印证", is_true_in_world=True, visible_from_volume=4, visible_to_volume=None, note="失火与追杀亲历后被证实", evidence_refs=ev(24,)),
    Belief(belief_id="BL04005", owner_id="E0005", topic="弟子踪迹", statement="显眼的鲁迪走到哪都会留传闻，温恩港可探到Dead End", certainty=Confidence.EXPLICIT, belief_state=BeliefState.INFERRED, learned_from=None, learned_at_volume=4, learned_method="公会观察与港人议论", is_true_in_world=True, visible_from_volume=4, visible_to_volume=None, note="判断五岁显才的弟子必被议论", evidence_refs=ev(18,)),
    Belief(belief_id="BL04006", owner_id="E0001", topic="治疗与克制", statement="帮艾莉丝定期治疗需抱头贴近，必须化身机械闭眼塞耳才不失控", certainty=Confidence.EXPLICIT, belief_state=BeliefState.FACT_KNOWN, learned_from=None, learned_at_volume=4, learned_method="多次治疗体会", is_true_in_world=True, visible_from_volume=4, visible_to_volume=None, note="自述奇妙感觉后决定机械化执行", evidence_refs=ev(24,)),
]

rel_changes = [
    RelationshipChange(change_id="RC04001", source_id="E0001", target_id="E0043", dimension="赠予", before="素不相识", trigger="以串烧喂饱饿倒帝王", after="获赠预知眼并约再会可求助", at_volume=4, at_date=None, evidence_refs=ev(9,10)),
    RelationshipChange(change_id="RC04002", source_id="E0001", target_id="E0053", dimension="救助", before="陌生旅人", trigger="解铐七孩并护送回村", after="被老战士视为恩人邀雨季留驻", at_volume=4, at_date=None, evidence_refs=ev(23,)),
    RelationshipChange(change_id="RC04003", source_id="E0001", target_id="E0057", dimension="共患", before="同牢新人前辈", trigger="共踹牢门冲火场并共击打手", after="成可互称前辈的共患同伴", at_volume=4, at_date=None, evidence_refs=ev(24,)),
    RelationshipChange(change_id="RC04004", source_id="E0001", target_id="E0021", dimension="治疗默契", before="治疗时尴尬躁动", trigger="化身机械闭眼塞耳固定姿势施术", after="建立可控的定期治疗协作", at_volume=4, at_date=None, evidence_refs=ev(24,)),
]

speech_profiles = [
    SpeechProfile(profile_id="ST04001", character_id="E0001", phase_id="P04001", phase_name="温恩港至德路迪亚村漂流期", politeness="对关卡与贾尔斯礼貌询问，对艾莉丝轻佻对瑞杰路德认真", sentence_length="叙事长句夹短促岩炮弹等施法名", address_habits="称瑞杰路德先生、艾莉丝、贾尔斯", emotion_expression="以妄想吐槽与耶～之类欢呼表现好色与兴奋", anger_expression="以岩弹代骂", shy_expression="被夸显眼时掩面自嘲", intimate_speech="与艾莉丝斗嘴带赖皮腔", stranger_speech="对外先报Dead End再探价", superior_speech="对基斯以前辈自居", inferior_speech="对奇希莉卡先跪后本宫对答", canonical_examples=("岩炮弹","方法有三种，先靠委托再找走私"), visible_from_volume=4, evidence_refs=ev(4,6,13)),
    SpeechProfile(profile_id="ST04002", character_id="E0043", phase_id="P04004", phase_name="复活饿倒期", politeness="帝王口吻，不容置疑", sentence_length="短句加夸张笑声", address_habits="自称本宫，称鲁迪鸟斯、巴迪冈迪", emotion_expression="呼哈哈大笑带咳", anger_expression="以威吓压人", shy_expression="无", intimate_speech="对救命人称再会可求助", stranger_speech="对路人直接点出双胞胎底细", superior_speech="居高临下赏赐体", inferior_speech="无", canonical_examples=("本宫是奇希莉卡·奇希里斯，人称魔界大帝","很好你确实能看到吧"), visible_from_volume=4, evidence_refs=ev(9,10)),
]

quirks = [
    CharacterQuirk(quirk_id="QK04001", character_id="E0001", phase_id="P04001", category="口癖", name="爽朗借口式搭讪", description="打倒凶男后必以你没事吧小姐作开场，借正当理由行接触", intensity="MEDIUM", frequency="偶发", triggers=("见少女遇险","自认有正当理由"), preferred_targets=("艾莉丝","陌生少女"), avoided_targets=(), behavior_patterns=("先击倒再伸手","边道歉边靠近"), verbal_patterns=("你没事吧小姐","我基于人神命令才帮你"), boundaries=("不对瑞杰路德使用",), exceptions=("仅在确认非梦魔后",), start_date=None, end_date=None, visible_from_volume=4, visible_to_volume=None, evidence_refs=ev(8,)),
    CharacterQuirk(quirk_id="QK04002", character_id="E0043", phase_id="P04004", category="仪式化动作", name="叉腰后仰挺胯", description="报帝号时双手叉腰上身后仰顺势前挺胯下展示帝威", intensity="HIGH", frequency="每次自报", triggers=("让人报名","自称魔界大帝"), preferred_targets=(), avoided_targets=(), behavior_patterns=("先叉腰再后仰","配合呼哈哈笑"), verbal_patterns=("本宫是奇希莉卡","人称魔界大帝"), boundaries=("仅在兴起时",), exceptions=(), start_date=None, end_date=None, visible_from_volume=4, visible_to_volume=None, evidence_refs=ev(9,)),
]

prefs = [
    CharacterPreference(preference_id="PF04001", character_id="E0001", phase_id="P04001", preference_type="偏好", target="串烧与海鲜", description="依人神谕优先买便于携带的贝柱烤鱼等串烧，喜海鲜风味", intensity="MEDIUM", context="温恩港摊位采购", visible_from_volume=4, visible_to_volume=None, evidence_refs=ev(7,)),
    CharacterPreference(preference_id="PF04002", character_id="E0021", phase_id="P04003", preference_type="喜欢", target="海与沙滩比试", description="向往下海游泳与沙滩上用木棒比试", intensity="HIGH", context="温恩港海边与沙滩", visible_from_volume=4, visible_to_volume=None, evidence_refs=ev(3,13)),
]

body_profiles = [
    BodyLanguageProfile(profile_id="BY04001", character_id="E0021", phase_id="P04003", phase_name="渡海前少女期", happy_signs=("跳下蜥蜴奔向大海","高高兴兴用力踢地跳上蜥蜴"), angry_signs=("毫无前兆突然暴怒痛扁骚扰男","连续践踏要害"), nervous_signs=(), embarrassed_signs=("偷瞄鲁迪脸带红晕",), lying_signs=(), fear_signs=(), thinking_signs=(), affection_signs=("与鲁迪斗嘴后脸红",), hostility_signs=("逼上绝境的追杀手法",), visible_from_volume=4, visible_to_volume=None, evidence_refs=ev(1,3)),
]

personas = [
    CharacterPersona(persona_id="PN04001", character_id="E0001", phase_id="P04001", persona_type="参谋", description="Dead End对外以瑞杰路德之名宣扬，对内以参谋列三策定行止，兼顾钱与道义", speech_style="对外宣瑞杰路德之名，对内条列一二三", behavior_traits=("探价","列三策","耳语分工","岩炮弹控力"), visible_from_volume=4, visible_to_volume=None, evidence_refs=ev(3,5,22)),
]

items = [
    ItemDef(item_id="IT04001", canonical_name="预知眼", aliases=("魔眼","预知魔眼"), category="能力", subcategory="魔眼", description="奇希莉卡赠予，能看见零点几秒后未来的眼睛，近身可先一步格挡", material=None, size=None, weight=None, durability=None, rarity="稀有", value_information="非卖品，战力质变", currency=None, creator="E0043", origin="温恩港小巷", manufacturer=None, abilities=(), effects=("预见对手动作","补足近战短板"), requirements=(), limitations=("需适应期约一星期","用脑负担"), first_appearance_volume=4, first_appearance_line=30972, visible_from_volume=4, evidence_refs=ev(10,11,13)),
]

abilities = [
    AbilityProfile(ability_id="AB04001", name="预知眼", aliases=("魔眼","未来视"), ability_type=AbilityType.MAGIC_EYE, school=None, element=None, tier="高阶", requirements=("奇希莉卡赐予",), preconditions=("直视对手",), mana_cost_if_known="无额外魔力消耗", stamina_cost_if_known=None, range_if_known="视线内", duration_if_known="持续被动", effects=("看见零点几秒后","可先制格挡"), limitations=("初期需一星期适应控魔力",), counters=(), qualitative_power="让十一岁初学者在木棒比试中首胜艾莉丝", learning_method=("魔界大帝赐予","自行一周训练掌握"), known_users=("E0001",), evidence_refs=ev(11,13,15)),
]

world_rules = [
    WorldRule(rule_id="WR04001", domain=WorldRuleDomain.ECONOMY, statement="温恩港关卡对斯佩路德收绿矿钱两百枚，余族仅一至两枚，人族五铁钱，拜金付钱可过", scope="温恩港至赞特港渡海关卡", exceptions="无钱则无法乘船", confidence=Confidence.EXPLICIT, visible_from_volume=4, evidence_refs=ev(4,)),
    WorldRule(rule_id="WR04001a", domain=WorldRuleDomain.ADVENTURER, statement="冒险者公会B级差价：魔大陆百五至两百石钱，米里斯十五大铜币约千五石钱相差十倍", scope="两大陆委托报酬体系", exceptions="A/S级更高但耗时", confidence=Confidence.EXPLICIT, visible_from_volume=4, evidence_refs=ev(1,)),
    WorldRule(rule_id="WR04002", domain=WorldRuleDomain.SOCIETY, statement="德路迪亚族圣兽数百年一诞，无正式名，被奉为守护神，平时受老战士与族长守护", scope="德路迪亚村信仰", exceptions="被拐时会引全村追击", confidence=Confidence.EXPLICIT, visible_from_volume=4, evidence_refs=ev(23,24)),
    WorldRule(rule_id="WR04003", domain=WorldRuleDomain.GEOGRAPHY, statement="米里斯大森林雨季约三月，期间村落闭锁，圣剑大道直线通首都无魔物且排水优异", scope="赞特港至米里斯首都沿线", exceptions="雨季外可通行马车", confidence=Confidence.EXPLICIT, visible_from_volume=4, evidence_refs=ev(24,)),
]

# fix duplicate id WR04001a -> need WR prefix numeric
world_rules = [
    WorldRule(rule_id="WR04001", domain=WorldRuleDomain.ECONOMY, statement="温恩港关卡对斯佩路德收绿矿钱两百枚，余族仅一至两枚，人族五铁钱，拜金付钱可过", scope="温恩港至赞特港渡海关卡", exceptions="无钱则无法乘船", confidence=Confidence.EXPLICIT, visible_from_volume=4, evidence_refs=ev(4,)),
    WorldRule(rule_id="WR04002", domain=WorldRuleDomain.ADVENTURER, statement="冒险者公会B级差价：魔大陆百五至两百石钱，米里斯十五大铜币约千五石钱相差十倍", scope="两大陆委托报酬体系", exceptions="A/S级更高但耗时", confidence=Confidence.EXPLICIT, visible_from_volume=4, evidence_refs=ev(1,)),
    WorldRule(rule_id="WR04003", domain=WorldRuleDomain.SOCIETY, statement="德路迪亚族圣兽数百年一诞，无正式名，被奉为守护神，平时受老战士与族长守护", scope="德路迪亚村信仰", exceptions="被拐时会引全村追击", confidence=Confidence.EXPLICIT, visible_from_volume=4, evidence_refs=ev(23,24)),
    WorldRule(rule_id="WR04004", domain=WorldRuleDomain.GEOGRAPHY, statement="米里斯大森林雨季约三月，期间村落闭锁，圣剑大道直线通首都无魔物且排水优异", scope="赞特港至米里斯首都沿线", exceptions="雨季外可通行马车", confidence=Confidence.EXPLICIT, visible_from_volume=4, evidence_refs=ev(24,)),
]

gaps = [
    CanonGap(gap_id="GAP04001", domain="地理", question="除走私船外正当渡海船期与票价细节未载", why_needed="估算不靠走私的归途时长", searched_volumes=(4,), status=GapStatus.OPEN, possible_sources="温恩港关卡时刻表或后续卷航运记录", note="本卷只载关卡报价与三策未给时刻"),
]

batch = EnrichmentBatch(batch_id="ENRICH_V004", source_volume=4, source_unit_ids=tuple(sorted({c.unit_id for c in picked})), schema_version="1.0.0", evidence=tuple(evidence), character_profiles=tuple(profiles), behavior_cases=tuple(cases), detailed_events=tuple(events), items=tuple(items), item_instances=(), abilities=tuple(abilities), power_comparisons=(), world_rules=tuple(world_rules), locations=(), routes=(), travel_observations=(), organizations=(), political_states=(), species=(), creatures=(), beliefs=tuple(beliefs), economic_observations=(), relationship_changes=tuple(rel_changes), speech_profiles=tuple(speech_profiles), character_quirks=tuple(quirks), character_preferences=tuple(prefs), body_language_profiles=tuple(body_profiles), character_personas=tuple(personas), canon_conflicts=(), canon_gaps=tuple(gaps))

out = pathlib.Path("data/canon_enriched/V004.json")
out.write_text(json.dumps(batch.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {out} ev={len(evidence)} prof={len(profiles)} cases={len(cases)} events={len(events)}")

reg = load_entity_registry(pathlib.Path("data/canon"))
doc2 = parse_source(pathlib.Path("data/raw/无职转生TXT合集.txt").read_text(encoding="utf-8"))
batches = load_enrichment_batches(pathlib.Path("data/canon_enriched"))
report = verify_enrichment(batches, doc2, reg)
print("is_clean", report.is_clean)
for e in report.errors:
    print(e.code, e.path, e.message)
pathlib.Path("data/canon_enriched/report.json").write_text(json.dumps(report.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
