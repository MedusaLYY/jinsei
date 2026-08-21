# Canon Personality Model Upgrade (AI GM Simulation)

> **For agentic workers:** Execute wave-by-wave. Do not generic-generate. Every claim must resolve to `data/volumes_txt/` via `evidence_refs`. Do not delete existing correct records for structural uniformity.

**Goal:** Upgrade Canon from a novel fact dump into an NPC behavior model that an AI GM can use to simulate *Mushoku Tensei* characters under counterfactual player actions.

**Architecture:** Additive enrichment on the existing layer (`data/canon_enriched/V###.json` + `enrich_model.py` / loader / verifier / query). New first-class `CharacterBehaviorRule` ("if X then Y") sits beside `BehaviorCase` (what actually happened) and `CharacterQuirk` (idiosyncrasy). Ariel is the gold-standard character, including the canon private incontinence preference, with anti-overplay flags so the GM does not turn a private tendency into a primary plot driver.

**Tech stack:** Python 3.14, existing enrichment schema 1.0.0 (optional new fields, no breaking bump), pytest / ruff / mypy, `tools/canon_quality_check.py`.

---

## 0. Current baseline (do not pretend this is already a sim DB)

From `CANON_DEEP_AUDIT_REPORT.md` + `CANON_QUALITY_SCORE.json` (2026-08-20):

| Module | Score /100 | Why |
| --- | --- | --- |
| 人物 | **48** | Schema exists (public/private/core, desires, fears). Fill rate: `origin`/`appearance_traits`/`body_traits`/`obsessions` = 0%. ~2/3 of 125 profiles never entered the deep model. V003–V015 / V019–V020 still template-polluted. |
| 事件 | **45** | `detailed_events` exist but `involved_factions` / `political_impacts` / `world_impacts` are empty. Template volumes title events "V0x 要事 N". |
| 世界规则 | **42** | 84 rules; V001 useful, later volumes 2 template sentences each. Magic ranks, sword schools, Asura succession, coin system, race lifespan are not systematic. |
| 时间线 | **40** | Extraction-layer events exist; enrichment causality graph is hollow. |
| 关系 | **35** | 71 `relationship_changes`; average 0.17 per character. Template "协作深化". No trust/affection/respect/fear/dependency trajectories. |
| **AI 模拟能力** | **32** | GM still has to fall back on model memory. No "if X then Y" rules. Private/public split missing for most S-tier NPCs. |

**Lowest-quality module:** NPC behavior model (personality depth + behavior rules + relationship dynamics). Quantity is not the bottleneck.

**Error cases already in the corpus (do not repeat):**

1. Generic 41-record volumes (`scripts/build_enrich_generic.py`) — "V0x 阶段性人格侧重见证据段".
2. V016 Ariel `age_description` = "约十六七岁" — **wrong**. V008 explicit: 「爱丽儿·阿涅摩伊·阿斯拉，十七岁。」 V016 is 青年期 / 已婚鲁迪 ~18, so Ariel is ~19–20.
3. V016 Ariel quirks record "tea stretch reset" but **omit** the explicit V016 incontinence line.
4. Adjective-only personalities ("聪明、优雅、有野心") instead of public/private/drive split.
5. BehaviorCase used as a synonym for plot summary, not as analogical retrieval fuel.

**Hard rules (from `Canon数据库要求.md` + this request):**

- Source = LN vols 1–26 only (`data/volumes_txt/`, `data/raw/无职转生TXT合集.txt`).
- No invention. Missing = `canon_gap` or `null`.
- Do not delete correct existing records to force a uniform shape.
- Do not write novel-synopsis prose.
- Private sexual/shame traits are **private tendencies, not primary action goals**. Every such record carries `simulation_weight` + `overplay_warning`.

---

## 1. Approaches considered

| Approach | What | Trade-off |
| --- | --- | --- |
| A. Fill empty fields on existing profiles only | Fast, no schema change | Cannot express "if X then Y"; Ariel fetish still missing; template volumes stay garbage |
| B. Rebuild all 15 template volumes + all characters in one pass | Matches the full wish list on paper | This is how the 41-record pollution happened. Quality collapses. |
| **C. Schema + Ariel gold standard + character waves** (recommended) | New `CharacterBehaviorRule`; Ariel is the completeness bar; then S-tier waves; events/world-rules only on volumes being touched | Slower, but every record is GM-usable and evidence-bound |

**Recommendation: C.** Previous Phase 2-A already proved B fails.

---

## 2. Schema change (Wave 0) — additive, backward compatible

Keep `EnrichmentBatch.ENRICHMENT_SCHEMA_VERSION = "1.0.0"`. Add optional collections with `document.get(..., ())` so historic batches still load.

### 2.1 New type: `CharacterBehaviorRule`

This is **not** a `BehaviorCase`. A case is one historical instance. A rule is a generalized tendency the GM uses when the player does something the novel never did.

```python
@dataclass(frozen=True)
class CharacterBehaviorRule:
    rule_id: str                  # BR0001-style
    character_id: str
    phase_id: str
    condition: str                # 条件：世界/关系/信息状态
    trigger_event: str            # 触发事件
    response: str                 # 角色倾向做 Y
    psychological_reason: str     # 心理原因
    known_at_time: str            # 当时知道什么
    unknown_at_time: str          # 当时不知道什么
    public_vs_private: str        # PUBLIC | PRIVATE | MIXED
    simulation_weight: str        # PRIMARY | SECONDARY | COLOR  (anti-overplay)
    overplay_warning: str | None  # 禁止 GM 如何夸大
    tags: tuple[BehaviorTag, ...]
    visible_from_volume: int
    visible_to_volume: int | None
    evidence_type: EvidenceType
    confidence: Confidence
    evidence_refs: tuple[str, ...]
```

Query API: `get_behavior_rules(character_id, *, at_volume, tag=None) -> list`.

### 2.2 Anti-overplay on existing `CharacterQuirk`

Add optional fields (defaults keep old JSON valid):

- `simulation_weight: str | None` — `PRIMARY` / `SECONDARY` / `COLOR`
- `overplay_warning: str | None`
- `is_private_tendency: bool` default `False`

### 2.3 Identity completeness (no new type)

`CharacterProfile` already has `identity`, `origin`, `origin_location_id`, `status_rank`, `appearance_traits`, `body_traits`, `core_personality`, `surface_personality`, `hidden_personality`, `obsessions`, `desires`, `fears`. **Fill them.** Do not add parallel "姓名/别名/种族" fields that duplicate the extraction-layer entity.

Identity mapping convention (write into the volume's profile, not a new table):

| User field | Existing slot |
| --- | --- |
| 姓名 / 别名 | extraction entity `name` / `aliases` (enrich, don't fork) |
| 年龄阶段 | `age_description` + `phase_name` |
| 种族 | `identity` (e.g. "人类·阿斯拉王族") |
| 出生地 | `origin` + `origin_location_id` |
| 家庭背景 | `origin` / `family_attitude` |
| 社会身份 / 职业 / 阶级 | `identity` + `status_rank` |
| 外貌 | `appearance_traits` + `body_traits` |

### 2.4 Files to touch in Wave 0

- `src/overlord_worldsim/canon/enrich_model.py` — type + batch field `behavior_rules: tuple[CharacterBehaviorRule, ...] = ()`
- `src/overlord_worldsim/canon/enrich_loader.py` — table `character_behavior_rules`, insert, evidence links
- `src/overlord_worldsim/canon/enrich_verifier.py` — id prefix `BR`, entity FK, evidence resolve
- `src/overlord_worldsim/canon/enrich_query.py` — `get_behavior_rules`
- `tests/canon/enrich_fixtures.py` — one rule on the tiny corpus
- `tests/canon/test_enrich_model.py` / `test_enrich_loader.py` / `test_enrich_verifier.py` / `test_enrich_query.py`
- `tools/canon_quality_check.py` — personality-completeness scoring (see §7)

TDD order: write failing tests for JSON round-trip, loader table, verifier FK, query filter → then implement.

---

## 3. Gold-standard character: 爱丽儿 (E0044) — Wave 1

This is the completeness bar. Every later character must reach this shape, not this word count.

### 3.1 Phases (do not collapse)

| Phase | Volumes | Age in text | Notes |
| --- | --- | --- | --- |
| 王宫期 | V003 外传「阿斯拉公主与奇迹天使」 | "还年轻"; V008 later states 17 at university | Palace, Luke, Derrick. Do not invent extra erotic scenes. Record only what the extra states. |
| 流亡学园期 | V008–V009 | **十七岁** (V008 explicit) | Student council president, Fizz/Luke, talent-scouting. |
| 空要 / 归国期 | V016–V017 | ~19–20 (derive from V008 17 + elapsed years; do not write "十六七岁") | Tea with Perugius, kingship crisis, Asura coup. |
| 即位后 | V017 end onward, only if text supports | Queen | Only if the volume actually shows post-coronation behavior. |

### 3.2 Public vs private vs drive (must not be adjective lists)

**公开人格 (surface_personality / persona PUBLIC):**

- 王族礼仪、从容、外交、情绪控制、茶会与敬语。
- 用外貌与传言作掩护（V003 外传: 「以自身的外表和传言作为掩护」）。

**私人人格 (hidden_personality / persona PRIVATE):**

- 好奇心；观察特殊的人；测试他人反应；隐藏的任性。
- 对普通贵族套路缺乏兴趣，对异常/有潜力者主动接近（学园期收希露菲、试探鲁迪）。
- 阿斯拉贵族式「超过限度的性癖好」之一员（V003 外传 explicit）。这是私人倾向。

**核心驱动力 (desires / long_term_goals / ambition):**

- 成为阿斯拉统治者（责任，不是虚荣）。V016: 自认「持有不符之力者毁灭」，一度动摇是否适合为王。
- 保护国家与派阀下的人。
- 告慰十三旧部 / 以「挚友」定义王（V016 日记与龙王问答）。
- 获得被认真对待的认可（佩尔基乌斯、奥尔斯帝德、鲁迪）。

**恐惧:**

- 被判定不适合为王。
- 再失去重要的人（十三旧部）。
- 在部下面前久露软弱（taboo）。
- 被人神/诅咒体系当成棋子（V016 叙述者怀疑她是否可被操控；奥尔斯帝德未暗示此可能 — 记为鲁迪的 `INFERRED` belief，不是世界真相）。

**执念:**

- 「王应继承无名者遗志、与挚友同行」——卡瓦尼斯答案。
- 对路克：君臣 + 共谋的宫廷搭档，不是单纯恋爱标签。

**价值观（冲突时怎么选）:**

- 王位/国家 > 私人羞耻兴趣。
- 挚友与能成事的人才 > 血统傲慢。
- 公开场合绝不把私人癖好当成政治工具（希露菲会当场喝止）。

### 3.3 Private quirk: 当众失禁倾向 — canon, detailed, anti-overplay

**This is canon. Do not invent extra acts. Do not omit it.**

Primary evidence, `data/volumes_txt/V016_第十六卷 青年期 阿斯拉王国篇 前.txt` approx. lines 2757–2773:

> 「因为我远远地看他就害怕到全身发抖，要是近距离听到他的声音，或许会忍不住失禁呢。」
> 爱丽儿虽然脸上笑咪咪的……但她刚才是不是说失禁来著？
> 「不过呢，在别人面前失禁实在是非常舒服……」
> 「爱丽儿大人！」 希露菲的声音听来就像是在说「不行喔」
> 刚才我好像听到她说失禁会很舒服什么的……算了，就当作没听到吧。
> 毕竟阿斯拉王国的贵族大多都是变态嘛，嗯。
> 不过话说回来，这个宛如从美术课本中跳出来的人居然说失禁，听起来实在不道德。

Supporting evidence:

- V003 外传: 「许多阿斯拉的贵族王族都拥有超过限度的性癖好，爱丽儿也不例外。」「在历史已经长达四百年以上……有很多人认为把异于他人的行为当成兴趣正代表一种社会地位。」
- V017 ~1703: 叙述者推测「假如她有不被人看着就无法解放的那种特殊性癖，事到如今我也不会诧异」—— **INFERENCE / 鲁迪信念，不是已发生事件。** 禁止写成「她上厕所必须被人看」。

**Quirk record (target shape):**

- `category`: `private_fetish`
- `name`: 当众失禁的羞耻快感
- `description`: 爱丽儿在空要庭园茶会、讨论奥尔斯帝德诅咒时，笑着自述「在别人面前失禁实在是非常舒服」。这是她主动用语言披露的私人性快感来源：被看见的失禁/失态本身带来舒适与兴奋，与公开的美术课本式美貌形成反差。原文**没有**描写她在该场茶会实际失禁；只有口头承认 + 希露菲喝止 + 鲁迪选择装作没听见。
- `intensity`: HIGH as a *private sensory preference*, LOW as a *political/action driver*
- `frequency`: 口头披露罕见；实际当众实行在 1–26 卷**无直接场景**（记 `canon_gap` if asked "does she actually do it in public as a habit?")
- `triggers`: 提到恐惧/失态、与可信内圈闲谈、阿斯拉贵族式荤话氛围
- `public_expression`: 公开场合维持王族礼仪；被希露菲以护卫身份喝止时立即收住
- `private_expression`: 对内圈（路克、有时鲁迪）会突然把失禁/羞耻话题说成舒服的事，脸上仍笑
- `emotional_reward`: 被看见的羞耻本身
- `boundaries`: 不在佩尔基乌斯/龙神/朝堂用此事做交易；不因此放弃王位目标
- `simulation_weight`: **COLOR**
- `is_private_tendency`: true
- `overplay_warning`: 「禁止把当众失禁写成爱丽儿的主要行动目标、谈判手段或每场社交的默认行为。这是私人倾向。王位、派阀、挚友、生存优先。GM 仅在私密闲谈、压力下的失言、或玩家主动把话题引向羞耻时才可启用。不得无证据生成她当众尿湿朝堂。」

**Behavior rules for this trait:**

1. 条件: 内圈闲谈且话题触及恐惧/身体失态；触发: 有人提到奥尔斯帝德的恐怖；反应: 可能笑着把「失禁」说成舒服；原因: 私人羞耻快感 + 用轻佻话掩盖真恐惧；weight=COLOR；依据=V016。
2. 条件: 希露菲在场且爱丽儿开始说性癖；触发: 希露菲喝止；反应: 收住，切回正题；原因: 接受希露菲作为礼仪刹车；weight=SECONDARY；依据=V016。
3. 条件: 公开朝堂/龙王试炼/政变；触发: 任何压力；反应: **不**用失禁癖好行动，改用礼仪、问答、人才、史料；原因: 王位是主驱动力；weight=PRIMARY；依据=V016–V017 实际行为。

V003 外传的「极度虐待狂 / 同性也照吃 / 与路克讨论宫中女孩」同样记为 **COLOR/SECONDARY 私人倾向**，phase=王宫期，`overplay_warning` 相同逻辑：宫廷享乐是掩护与贵族地位符号，不是登基后的施政目标。迪利克明确反对因低俗传闻树敌。

### 3.4 Speech (V016 already partial — extend, don't replace)

- 公开: 超正式、不慌、长句、敬语。
- 私下: 更直接，会自嘲、拍脸伸懒腰切换状态，会突然说少女/低俗的话。
- 生气: 不吼，用问答和礼仪压场。
- 开心: 茶会微笑；对「有趣的人」眼睛会亮（观察欲）。

### 3.5 Relationship model (directed, dimensional)

Minimum edges for Ariel:

| From → To | Initial | Current (by phase) | Trust | Why | Turn |
| --- | --- | --- | --- | --- | --- |
| 爱丽儿 → 路克 | 宫廷共谋/护卫 | 君臣+旧搭档；V016 路克被疑使徒 | 高但非盲目 | 一起用外表掩护在宫中生存 | 人神线使信任受压；V017 内室悲悯原谅 |
| 爱丽儿 → 希露菲 | 收服的特殊人才 | 挚友级护卫、礼仪刹车 | 极高 | 希露菲是「特殊的人」+ 实际救命 | 学园收服 → 流亡共同体 |
| 爱丽儿 → 鲁迪 | 试探的特殊人才 | 可托付的盟友 | 中→高 | 观察反应、测试；后因史料/龙神线托付 | V016 茶会试探 → 日记答案 |
| 爱丽儿 → 佩尔基乌斯 | 求援对象 | 后盾 | 敬畏 | 需要发言力 | 龙王问答 |
| 爱丽儿 → 迪利克 | 守护术师 | 亡者/执念 | 高 | 唯一常常识的刹车 | 十三旧部 |

`relationship_changes` must use dimensions `trust` / `affection` / `respect` / `fear` / `loyalty` / `dependency` / `attraction` / `obligation` — not the word "朋友".

### 3.6 Volumes to edit in Wave 1

- **Rebuild** `data/canon_enriched/V003.json` (currently template/quarantine) from the 外传 + Demon Continent chapters that actually mention Ariel. Natural record count, not 41.
- **Extend** `V008.json` / `V009.json` if still template — at least Ariel/Luke/Fizz/Zanoba/Cliff profiles for 学园期. If a full V008 rebuild exceeds this wave, extract Ariel-related units first and leave a `canon_gap` for the rest of the volume rather than generating filler.
- **Extend, do not wipe** `V016.json` / `V017.json`: fix Ariel age; add incontinence quirk + behavior rules + public/private personas; keep existing correct tea-stretch, kingship, Perugius records.

Script pattern: follow `scripts/build_v016.py` style (parse_source → pick **semantically relevant** chunks, not evenly spaced indices) but **never** copy `build_enrich_generic.py`.

---

## 4. Character waves after Ariel (Wave 2–4)

Each S-tier character gets, per relevant phase, all of: identity block, public/private/core, desires/fears/obsessions/values, ≥3 `CharacterBehaviorRule`, ≥1 speech profile, quirks (including anti-image traits), directed relationship changes. Source-bound. Skip fields the text does not support.

### Wave 2 — Greyrat core (highest GM traffic)

| ID | Name | Priority phases | Signature behavior (must not flatten) |
| --- | --- | --- | --- |
| E0001 | 鲁迪乌斯 | 幼年 / 少年 / 学园 / 已婚 | 前世耻感 + 重家庭 + 对「喜欢的女孩失禁」有性兴趣（V016 他自己承认）但 **不等于** 爱丽儿的当众癖好；决策先密报再与希露菲商量 |
| E0005 | 洛琪希 | 家庭教师 / 魔大陆 / 大学 / 妻子 | 矮小敏感、教学严谨、被无视会受伤、对鲁迪从师生转到对等伴侣 |
| E0006 | 希露菲 | 幼年绿发 / 菲兹 / 妻子护卫 | 双重忠诚（鲁迪与爱丽儿）；礼仪刹车；风魔法掩护；不让私人话题毁掉主君形象 |
| E0021 | 艾莉丝 | 罗亚大小姐 / Dead End / 剑王 / 妻子 | 好胜直率；以剑表达感情；对「距离感」后期自省 |
| E0002 | 保罗 | 布埃纳骑士 / 出轨危机 / 搜索队 / 迷宫死 | 冲动、好色、父爱真实但不稳定；失败后会逃也会拼死赎 |
| E0004 | 莉莉雅 | 女仆 / 出轨对象 / 后妻 | 原后宫禁卫；克制；把生存与孩子放在尊严前面 |
| E0007 | 诺伦 | 婴儿 / 米里斯 / 妹 | 对保罗/鲁迪的怨与孝；米里斯信仰压力 |
| E0008 | 爱夏 | 婴儿 / 西隆 / 妹 | 早熟、计算、对鲁迪的忠诚接近执念 |

V001–V002 already have usable density — **enrich missing deep fields, do not replace working cases**.

### Wave 3 — named S-tier

| ID | Name | Must capture |
| --- | --- | --- |
| E0022 | 基列奴 | 寡言、以剑表忠、性知识空白、对艾莉丝是师傅 |
| E0080 | 札诺巴 | 人偶执念、对鲁迪的师徒/友人狂热、战斗力与社交幼稚并存 |
| E0065 | 克里夫 | 米里斯天才、十六岁成年无人祝贺、对艾莉娜丽洁、宗教与魔法研究冲突 |
| E0079 | 奥尔斯帝德 | 诅咒导致被厌恶、时间循环疲劳、对鲁迪是工具也是例外、不浪费情绪 |
| E0045 | 路克 | 好色、忠于爱丽儿、人神使徒风险、剑术上限、诺托斯立场 |

### Wave 4 — faction casts (only named, recurring, plot-relevant)

**阿斯拉:** 格拉维尔、哈尔法斯、大流士、迪利克、佩尔基乌斯、七星、朵莉丝缇娜 — political behavior rules (派阀、倒阁、继承)。

**魔大陆:** 瑞杰路德、奇希莉卡、巴迪冈迪、贾尔斯 — honor/curse/hunger/reputation rules.

Do not encyclopedia every extra. If a name appears once with no decision on-page, skip or `canon_gap`.

---

## 5. Event and world-rule upgrade (Wave 5, only on volumes being edited)

When a volume is opened for a character wave, upgrade its `detailed_events` in the same pass:

Required event fields (already on `DetailedEvent`): time, location, participants, trigger, actions, outcome, `state_changes`, `relationship_change_ids`, `belief_ids`, `long_term_impacts`, `political_impacts`, `world_impacts`. **Fill them from the text.** Ban titles like "V0x 要事 N".

World rules to add when the volume actually states them:

| Domain | Examples already in text |
| --- | --- |
| MAGIC | 咏唱 / 无咏唱、圣级、转移禁术（V003 瑞杰路德） |
| SWORD | 剑神/水神/北神、等级称呼 |
| NOBILITY / POLITICS | 阿斯拉王位继承、第二公主派最弱、转移事件导致失势（V008） |
| ECONOMY | 石钱/绿矿钱、魔大陆 vs 米里斯委托价差（V004 script notes） |
| RACE | 米格路德寿命与外观、兽族、长耳族 — only stated physiology |
| SOCIETY | 「把异于他人的性癖当社会地位」是阿斯拉宫廷规则（V003 外传） — world rule, not just Ariel trivia |

---

## 6. Implementation order (bite-sized)

### Task 1 — Failing tests for `CharacterBehaviorRule`

- Files: `tests/canon/test_enrich_model.py`, `enrich_fixtures.py`
- Assert JSON round-trip, id `BR\d+`, optional empty list on old batches.

### Task 2 — Implement model + loader + verifier + query

- Files: `enrich_model.py`, `enrich_loader.py`, `enrich_verifier.py`, `enrich_query.py` + matching tests.
- Existing batches must still `is_clean=true`.

### Task 3 — Quality gate for personality completeness

- Extend `tools/canon_quality_check.py` + `tests/test_canon_quality.py`:
  - Fail a profile that only has adjective `personality_traits` and empty `core_personality`/`surface_personality`/`hidden_personality`.
  - Fail a COLOR-weight quirk that lacks `overplay_warning`.
  - Do **not** fail historic V001 yet; gate applies to newly rebuilt volumes via an allowlist or `schema` presence of `behavior_rules`.

### Task 4 — Ariel gold standard on V016/V017 (extend)

- Fix age; add personas, incontinence quirk, 3+ behavior rules, relationship dimensions, speech private/public.
- Evidence chunks must include the V016 tea-party lines (~2757–2773), not evenly spaced indices.
- Run `canon enrich-verify` until clean.
- Do not delete tea-stretch / kingship / Perugius records.

### Task 5 — Rebuild V003 (quarantine replacement)

- Source: 外传「阿斯拉公主与奇迹天使」 + 本卷魔大陆章节。
- Ariel + Luke + Derrick personality; Asura-nobility-fetish-as-status **world rule**; Ruijerd trust rules if the chapter supports them.
- Natural count ≠ 41.
- After rebuild, `tests/test_canon_quality.py::test_score_volume_polluted_volumes_flagged` currently asserts V003 < 50 — **update that assertion** only after the new V003 scores ≥ 60.

### Task 6 — Wave 2 characters on V001/V002 (enrich in place) then V004/V006 (already partially rebuilt)

- Fill 0% fields (`origin`, `appearance_traits`, `obsessions`).
- Add behavior rules for each core character from existing evidence first (cheapest, already grounded).

### Task 7 — Remaining template volumes character-first

- Order: V008–V009 (university / Ariel 17) → V005 (Ariel death extra) → V007 → V010–V015 → V019–V020.
- Stop a volume when S-tier characters in that volume have rules + personas. Do not pad.

### Task 8 — Score report

Regenerate `CANON_QUALITY_SCORE.json` and write `CANON_PERSONALITY_AUDIT.md` with:

1. Six scores /100 (人物/事件/世界规则/时间线/关系/AI模拟能力)
2. Lowest module
3. Error cases
4. Next-phase plan
5. Priority list

Target after Wave 1 (Ariel + schema), not after the entire wishlist:

| Module | Target after Wave 1 |
| --- | --- |
| 人物 | 55–60 (Ariel A-grade, others still uneven) |
| AI 模拟能力 | 45 (rules exist and queryable) |
| 关系 | 42 (Ariel subgraph only) |

Target after Wave 2–3: 人物 ≥ 75, AI 模拟 ≥ 70, 关系 ≥ 65.

---

## 7. Simulation acceptance test (must pass before calling a character "done")

Pick a counterfactual the novel did not write. The GM answer must cite `CharacterProfile` + `BehaviorRule` + `Quirk` + `RelationshipChange` + evidence ids — not model memory.

Ariel acceptance prompts:

1. 玩家在朝堂公开羞辱爱丽儿 → 应走礼仪/派阀反击（PRIMARY rules），**不应**失禁。
2. 玩家在只有路克/希露菲的房间里把话题引到羞耻 → 可以触发 COLOR 口头披露，希露菲会喝止。
3. 玩家展示明显「特殊才能」 → 爱丽儿主动接近观察，而不是因为性癖。
4. 玩家要她为了性癖放弃王位 → 拒绝。王位是主驱动力。

---

## 8. Out of scope / anti-patterns

- Do not write HP/MP/charm numbers.
- Do not rebuild extraction-layer `data/canon/V*.json` unless an entity alias is actually missing.
- Do not use wiki/fandom ages. V008 十七岁 is the age anchor.
- Do not generate a public incontinence **scene** that the LN does not contain.
- Do not let `scripts/build_enrich_generic.py` run again.
- Do not flatten Luke/Ariel palace sexuality into "优秀王女" or into "every scene is fetish".
- Sexual content for Ariel: primary detailed record is V016 (post-university, ~19–20). V003 extra records palace-era personality as stated, without writing new underage erotic narrative.

---

## 9. Priority ranking (after this plan)

1. Schema `CharacterBehaviorRule` + query (without this, GM cannot retrieve "if X then Y").
2. Ariel gold standard including private incontinence + anti-overplay (user-specified; also the completeness bar).
3. Fix V016 age error; do not wipe V016/V017.
4. Replace V003 template with 外传-grounded batch.
5. Greyrat core behavior rules from existing V001/V002 evidence.
6. University volumes V008–V009 (Ariel 17, Zanoba, Cliff, Fizz).
7. Remaining S-tier (Orsted, Ghislaine, Paul…).
8. Asura / Demon Continent supporting cast.
9. Systematic world rules (magic/sword/succession/economy/race) on volumes already open.
10. Event causality fill — only together with character work, never as a separate generic pass.
