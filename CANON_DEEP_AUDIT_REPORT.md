# Canon 深度质量审计报告（Deep Quality Audit）

> 范围：`data/canon/V001..V026.json`（抽取层）+ `data/canon_enriched/V001..V026.json`（富化层）+ `data/parsed/*` + `data/volumes_txt/*`
> 原则：只读审计，不修改任何数据；所有判断以 `data/volumes_txt/` 原文与 `evidence` 指向为准；禁止 wiki/粉丝设定/AI 幻觉。
> 版本：2026-08-20 审计基线（enrichment schema v1.0.0，manifest content_version 1）

## 1. 执行摘要

**总体结论：当前 Canon 是“结构化小说知识库”，尚未达到“支持长期人生模拟的世界模拟知识库”。**

- 26 卷覆盖在形式上达成（`canon_enriched` 26 批次、`canon` 26 批次），但**有效信息密度极度不均**：V001 富集、V002 中等、V016+ 部分真实增强、**V003-V015 与 V019-V020 为 `build_enrich_generic.py` 生成的确定性占位模板**（每卷固定 41 条记录的占位特征在 `manifest.json:batch_counts` 中直接可见）。
- 校验器 `enrich_verifier` 报告 `is_clean=true`，说明**结构与引用层面通过**（`evidence` 行号落在 `ParsedDocument` 内、`entity_id` 可解析），但**语义深度与模拟可用性未通过**。
- 六维评分：无 A；1 个 B-；其余 C/D。见 §3。

**最关键的 5 个阻塞项（按对世界模拟的影响排序）：**

1. **地点与势力几乎空白**：富化层仅 10 个 `locations`、1 个 `organizations`、1 个 `political_states`，无法回答“玩家加入阿斯拉王国会遇到什么政治问题”。
2. **事件因果图名存实亡**：`detailed_events.involved_factions` 0 填充、`political_impacts` 0、`world_impacts` 0，`dependencies` 多为“为后事提供前提”的空话，无法回答“改变某事件会造成什么后果”。
3. **人物深层人格未建模**：`CharacterProfile` 的 `origin` 0、`appearance_traits` 0、`body_traits` 0、`obsessions` 0；S 级角色除鲁迪/希露菲外多数只有 1-4 个 phase 侧写，且 V003+ 大量为模板句。
4. **关系网络稀疏且占位**：全库 71 条 `relationship_changes`，平均每角色 0.17 条；`dimension` 去重后出现 `Э��`/`�ж�` 等模板编码残留，V003 后每卷固定 1 条“协作深化”。
5. **编码与文本质量污染**：部分批次中 `abilities.name` 等字段存在 latin1/gbk 误编码残留（终端复现为 `��ӽ��ħ��` 等），虽不影响校验器但直接影响 LLM 可读性与检索。

---

## 2. 审计方法

1. **全量计数**：遍历 `data/canon_enriched/V*.json` 26 批次，统计 26 类记录总数与分卷分布；遍历 `data/canon/V*.json` 统计抽取层实体。
2. **抽样质检**：V001/V002/V016（真实增强）与 V003/V004/V010（模板卷）对照抽样，人工比对 `unit_id`/`source_start_line`/`source_end_line` 与 `chunks.jsonl` 的实际指向；核查 `evidence_type`/`confidence` 分布。
3. **字段填充率**：对 `CharacterProfile` v1.1 新增的 16 个世界模拟字段与 `DetailedEvent` 的 5 个扩展字段分别计算非空率。
4. **S 级角色点名**：以 `data/canon` 实体表为权威 `id->name` 映射，统计 12 个 S 级角色的 `character_profiles` 与 `behavior_cases` 覆盖。
5. **真实性红线**：凡 `note`/`statement` 含“V0x 阶段性”“见证据段”等无指称句，或跨卷复用同一句话术的，标记为**占位/需重抽取**。

> 不确定性声明：部分批次在 Windows 控制台下展示为乱码，审计以 `Read` 工具的 UTF-8 直读为准；凡展示异常的均在落盘文件中二次校验。

---

## 3. 六维评分总览

| 维度 | 评分 | 一句话判定 |
|------|------|------------|
| 人物质量 | **C** | 鲁迪/希露菲相对可用，其余 S 级浅薄且模板化；深层人格/外貌/身体特征几乎空白 |
| 事件质量 | **C** | V001 事件可用，V003-V015 模板化（标题即“V0x 要事 N”），因果与政治影响字段大面积空置 |
| 关系质量 | **D** | 数量不足、维度噪声大、无 `trust/affection/respect/fear/dependency` 联动模型 |
| 地点质量 | **D** | 仅 10 地点且 9 个在 V001，缺大陆/国家/城市/迷宫层级与地理/经济/危险度 |
| 势力质量 | **D** | 仅 1 个组织（魔法大学），国家/教会/种族/军队/冒险者协会体系缺失 |
| 世界规则质量 | **C-** | 84 条但 V003+ 每卷 2 条模板句，缺魔法/剑术/社会/经济等域的系统性规则与例外 |

评分标尺：A=可直接驱动模拟且证据闭环；B=可用但有缺口；C=结构可用、语义不可用；D=不可用。

---

## 4. 数据基线（审计快照）

### 4.1 富化层总量（26 卷合计）

```
evidence: 675 | character_profiles: 125 | behavior_cases: 349 | detailed_events: 121
items: 33 | item_instances: 20 | abilities: 38 | power_comparisons: 21 | world_rules: 84
locations: 10 | routes: 1 | travel_observations: 1 | organizations: 1 | political_states: 1
species: 6 | creatures: 5 | beliefs: 74 | economic_observations: 12 | relationship_changes: 71
speech_profiles: 48 | character_quirks: 85 | character_preferences: 64
body_language_profiles: 42 | character_personas: 52 | canon_conflicts: 4 | canon_gaps: 36
```

分卷分布（关键特征）：

- `manifest.batch_counts`：`ENRICH_V001:465, V002:122, V003:41, V004:41, ..., V015:41, V016:74, V017:101, V018:91, V019:41, V020:41, V021:104 ...` — **V003-V015、V019-V020 的 41 条为 `build_enrich_generic.py` 的固定模板产量**。
- `detailed_events`：V001 12 / V002 3 / V003-V015 各 4（模板）/ V016+ 5-6。
- `relationship_changes`：V001 14 / V002 8 / V003-V015 各 1（模板）/ V016+ 3-4。
- `locations`：V001 9 / V002 1 / V003-V026 0。
- `world_rules`：V001 18 / 其余每卷 2-4（模板卷各 2）。
- `evidence`：675 条，`evidence_type` 仅两种（`CANON_EXPLICIT 466 / STRONG_INFERENCE 209`），`confidence` 全为 `EXPLICIT`（675）— 未区分 `INFERENCE/UNKNOWN`，可信度分层失效。

### 4.2 抽取层总量

- 实体 414：`CHARACTER 371 / LOCATION 39 / ORGANIZATION 4`
- `data/parsed/summary.json`：`chunks 2731 / scenes 526 / units 541 / volumes 26 / total_chars 3,481,474`

### 4.3 人物侧写分布（富化层）

- 去重 `character_id`：52 个有侧写。
- 侧写数 Top：`E0001 鲁迪乌斯 26`（每卷 1 个，唯一达标）、`E0006 希露菲 10`、`E0021 艾莉丝 7`、`E0057 6`、`E0031 5`、`E0022 4`、`E0005 洛琪希 3`、`E0079 奥尔斯帝德 3`、`E0102 3`、`E0065 克里夫 3`。
- 其余 S 级：`E0002 保罗` 仅 1 个 profile、`E0104 艾莉娜丽洁` 2 个、`E0022 扎诺巴` 4 个（仍薄）、`基列奴` 需核对 id（未在 Top15，疑似 ≤2）。

---

## 5. 分维度深检

### 5.1 人物质量 — C

**目标对照（任务书 §3）：** 每个 S 级角色需覆盖 `identity/origin/race/status/appearance/body_traits` + 三层人格 + 价值观/欲望/恐惧/执念/习惯 + 心理触发与应激 + 决策逻辑 + 语言 + 成长分期，且每条带 `source_volume/source_unit/evidence_ref/evidence_text`。

**实际：**

- **深层字段填充率（125 个 profiles 统计）：**
  - `identity 12.0% (15/125)`、`origin 0%`、`appearance_traits 0%`、`body_traits 0%`、`obsessions 0%`
  - `core/surface/hidden_personality 36% (45/125)`、`interests 36%`、`dislikes 36%`、`weaknesses 36%`、`habits 36%`、`emotional_triggers 36%`、`decision_logic 36%`、`extreme_choice_note 36%`、`phase_personality_note 36%`
  - 结论：约 2/3 的 profiles 完全未进入 v1.1 深层模型；已填充的 45 个集中在 V001/V002/V016+ 的鲁迪及少数主角。
- **S 级点名：**
  - `鲁迪乌斯 E0001`：26 phases，相对最完整，但 V003+ 的 13 个 phase 的 `summary/behavior_changes_note` 为模板句“V0x 阶段性人格侧重见证据段”“依该卷事件推进人物状态演进（证据见该卷证据段）”，**无指称、不可用于模拟**。
  - `爱丽儿 E0044`：点名 S 级但在富化层 profile 计数中未进 Top15，抽样显示其 profile 数量不足且缺 `政治教育/王位竞争压力/贵族政治经验` 等任务书 §4 要求的字段，**需专项重建**。
  - `奥尔斯帝德 E0079`：仅 3 个 profiles，缺“龙神视角/时间循环相关”的极端抉择与恐惧建模。
  - `人神 E0032`：2 个 profiles，缺“低语策略/信任操纵/不可信度”的行为证据链。
  - `保罗 E0002 1 个`、`基列奴` 等近乎空白。
- **行为证据**：`behavior_cases 349` 看似充足，但 V003-V015 每卷固定 8 条且句式复用（`context: V0x 场景 N：...中的人际/委托场景` / `trigger: 触发 N：对方请求或突发事件` / `action: 行动 N：权衡后协作或应对`），**非原文证据锚定**，标签虽合法（`FAMILY/TRUST/...`）但文本无区分度。
- **语言/怪癖**：`speech_profiles 48 / quirks 85 / preferences 64 / body_language 42` 数量尚可，但 V003+ 的 `quirks` 抽样显示 8 卷复用“事后复盘”同一条，`speech` 复用“敬体对外常体对内”，未体现角色差异。

**缺失项：**
- 全部 S 级的 `origin_location_id`、`appearance_traits`、`body_traits`、`obsessions` 系统性缺失。
- 爱丽儿的 `王族身份影响/公开 vs 真实人格/政治行为模型/特殊兴趣与怪癖/领导能力` 五块（§4）均未建模。
- 保罗/基列奴/艾莉娜丽洁等配角的童年/少年/成年分期演变无数据。

**低质量项：**
- V001/V002 的 profiles 相对可用但仍含 `UNKNOWN` 日期精度与 `visible_to_volume=null` 的开放区间，未做 phase 边界收敛。
- V003-V015 的全部 profiles/behavior_cases/speech/quirks 为模板句，虽通过校验但语义空洞。

**需重抽取：**
- V003-V015、V019-V020 的全部 `character_profiles` 与 `behavior_cases`（共约 11 卷 × (3 profiles + 8 cases) = 约 121 条）必须从 `data/volumes_txt` 重新抽取，替换模板。

---

### 5.2 事件质量 — C

**目标对照（§5）：** 每个重要事件需 `event_name/time/location/participants/factions/cause/background/participant_motivations/actions/conflicts/result/relationship_changes/political_changes/world_changes/future_consequences`，并能解释“世界为什么改变”（如阿斯拉政变需含各派与鲁迪作用）。

**实际：**

- **数量与分布**：121 个 `detailed_events`，名义覆盖 26 卷，但 V003-V015 每卷 4 条标题均为“V0x 要事 N：...小节 N”，`volume_no` 正确但 `title/time_note/trigger/outcome` 均为模板。
- **因果与世界影响字段（v1.1 扩展，121 事件统计）：**
  - `involved_factions 0%`、`political_impacts 0%`、`world_impacts 0%`
  - `long_term_impacts 49.6% (60/121)`、`participant_actions 49.6% (60/121)` — 但模板卷的 2 条为“长期影响 N：形塑后卷人际与立场”“E0001 主导推进”等空话。
  - `prerequisites 100% 有一条`，但模板卷为 `PERSON_PRESENT: E0001 在场`，无实质前提；`dependencies` 模板卷为链式 `CAUSES -> DE{next}` 自指式占位。
  - `state_changes` 每事件仅 1 条且 `before: 未定 after: 推进`，未记录真实状态差。
- **证据**：`events without evidence = 0/121` 看似 100% 有据，但模板卷的 `evidence_refs` 指向的是为过检而选的 16 个 chunk 证据（`build_enrich_generic` 按步长均匀采样），**证据与事件陈述无语义对应**。
- **时间**：全部 `time_date=null, time_precision=UNKNOWN`，`time_note` 仅“V0x 期间”，无法支撑时序推演与前提校验。

**缺失项：**
- 阿斯拉政变、转移事件、迷宫、学园、决战等关键战役/政变事件的 `factions/political_changes/world_changes/future_consequences` 完全缺失。
- `location_id` 大面积为 `null`（模板卷全空），无法与地点库联动。

**低质量项：**
- V001 的 12 个事件（如“鲁迪乌斯转生为婴儿”）相对可用，但 `prerequisites/dependencies/state_changes` 仍偏简，缺多前提与多后效。
- `event_type` 枚举含乱码/占位（`����` 等），需清洗。

**需重抽取：**
- V003-V015、V019-V020 的全部 4×11=44 个事件；V016-V018、V021-V026 的事件需补 `involved_factions/political_impacts/world_impacts/participant_motivations/conflicts` 四类字段（约 35+ 事件）。

---

### 5.3 关系质量 — D

**目标对照（§6）：** 需 `relationship_type/initial_state/trust_level/affection/respect/fear/dependency/conflict_points/turning_events/current_state` 的动态模型，示例“鲁迪→爱丽儿”需含初见、利益、信任变化、合作原因、未来影响。

**实际：**

- 全库 71 条 `relationship_changes`，对应 371 个角色实体，**关系密度 0.19/角色**，远不足以支撑模拟。
- 分卷：V001 14 / V002 8 / V003-V015 各 1（模板“协作深化”）/ V016+ 各 3-4。
- `dimension` 去重后 37 种，但含 `Э��/�ж�/����/���` 等编码残留维度与 `协作` 高频复用；模板卷的 `before: 既有关系 after: 协作深化 trigger: V0x 事件 1` 无区分度。
- 无 `trust_level/affection/respect/fear/dependency` 的量化或分级字段；无 `conflict_points/turning_events` 结构化列表；无 `initial_state -> current_state` 的相变证据链。
- S 级关键关系抽样：`鲁迪→爱丽儿`、`鲁迪→奥尔斯帝德`、`鲁迪→人神` 在富化层中无对应 `relationship_changes` 或仅有 1 条模板，**无法回答“在爱丽儿面前撒谎会怎样被判断”**。

**缺失项：**
- 全部 S 级互相关系的多维动态（信任/好感/敬畏/恐惧/依赖）与冲突点清单。
- 关系转折事件的 `evidence` 闭环（需指向 `detailed_events` 与 `behavior_cases`）。

**低质量项：**
- 71 条中约 15 条 `dimension=Э��` 等乱码维度，需清洗或重建。
- V001 的 14 条相对可用但仍缺数值化维度。

**需重抽取：**
- 全量关系重建；优先重建 S 级 12 角色 × 核心 8-10 关系的完全图（约 80-100 条高质量 `relationship_changes`），替换现有 71 条中的模板与乱码条。

---

### 5.4 地点质量 — D

**目标对照（§7）：** 需 `世界/大陆/国家/地区/城市/地点` 层级，每地点含 `name/type/location/environment/population/culture/government/economy/danger_level/history/important_people/related_events`，重点覆盖阿斯拉王国、米里斯神圣国、拉诺亚魔法大学、魔大陆、菲托亚领、王都、迷宫。

**实际：**

- 富化层 `locations 10`：V001 9 + V002 1，V003-V026 共 0。
- V001 的 9 个地点（含布埃纳村、阿斯拉王国、菲托亚领、罗亚、魔法大学、米里斯神圣国、格雷拉特家宅、森林、山丘大树、龙神孔）与抽取层 `LOCATION 39` 相比，**覆盖率 25%**，且抽取层已知的 39 个地点中约 29 个未进入富化。
- 富化 `LocationProfile` 字段抽样显示 `parent_id`/`population`/`danger_level` 等多为 `null` 或缺省，未形成层级；`culture/government/economy/history` 文本为空或仅一句话。
- 重点地点：`拉诺亚魔法大学` 在富化中仅以 `组织` 形式出现 1 次，未作为地点建模；`魔大陆`、`王都`等未在富化地点中出现；`迷宫` 仅 1 个（龙神孔）。
- 无大陆/国家层级划分，无地点间 `routes` 网络（全库仅 1 条 `routes` + 1 条 `travel_observations`）。

**缺失项：**
- 大陆（中央/魔/米里斯/贝卡利特）、国家（阿斯拉/米里斯/王龙/西隆 等）、地区（菲托亚领）、城市（罗亚/夏利亚/王都）、迷宫（转移迷宫/龙神孔等）及学园建筑的完整层级与 11 字段补全。
- 地点间路径与旅行约束（距离、危险度、季节影响）。

**需重抽取：**
- 基于 `data/parsed/chunks.jsonl` 与 `data/canon.*.LOCATION` 实体，重建地点库至 ≥30 个核心地点；新建 `routes/travel_observations` 至可用水平。

---

### 5.5 势力质量 — D

**目标对照（§8）：** 需 `国家/组织/教会/种族/军队/冒险者协会` 的 `leader/goal/ideology/resources/military_power/political_position/allies/enemies`。

**实际：**

- 全库 `organizations 1`（魔法大学，`org_type` 含编码残留 `��������`，`leaders/members/hierarchy/territory/enemies` 多为空）、`political_states 1`。
- 抽取层 `ORGANIZATION 4` 未被富化引入；文本中明确的势力（阿斯拉王国及贵族派系、米里斯教会、拉诺亚魔法大学、冒险者协会、龙神阵营、人神阵营、魔族/人族/兽族/长耳族等种族势力）**均未建模**。
- 无 `military_power/political_position/allies/enemies` 的结构化数据，无法回答“加入阿斯拉王国会遇到什么政治问题”。

**缺失项：**
- 阿斯拉王国内部的王位派系（爱丽儿派 vs 格拉维尔派 vs 其他贵族）、教会派系、学园派系、冒险者公会体系、种族势力。
- 每势力的 `ideology/resources/military_power` 量化或分级。

**需重抽取：**
- 新建势力库 ≥10 个核心势力，含阿斯拉王国及其内部派系的拆分建模。

---

### 5.6 世界规则质量 — C-

**目标对照：** 需 `魔法/剑术/斗气/魔眼/修炼/社会/法律/贵族/婚姻/家庭/冒险者/奴隶/宗教/经济/地理/种族/政治/战争/决斗/教育/战斗/物种/怪物/通用` 等域的规则，每条含 `statement/scope/exceptions/confidence/evidence`。

**实际：**

- 84 条 `world_rules`，域枚举已覆盖 `MAGIC/SOCIETY/...`，但：
  - V001 18 条相对可用；V003+ 每卷 2-4 条且为模板句（`V0x《...》阶段的社会与委托范式见该卷场景` / `V0x 中魔术/能力运用的一般约束见该卷演示`），无可执行规则。
  - `confidence` 全为 `STRONG_INFERENCE/INFERENCE`，无 `CANON_EXPLICIT` 锚定到具体法条/对话。
  - 缺 `数值/阈值/前提/例外` 的可判定表述（如魔力总量、咏唱位阶、贵族继承顺位、冒险者等级任务约束等）。
- `canon_gaps 36 / canon_conflicts 4` 有记录但未与规则关联，未形成“已知未知”清单对模拟的约束。

**低质量项：**
- 模板卷的 2×13=26 条规则需替换为从原文抽取的具指称规则（如“无咏唱可行”“水圣级需...”等需逐条带证据）。

**需重抽取：**
- V003-V015、V019-V020 的 26 条模板规则；补充魔法体系、贵族/教会/冒险者制度、经济/物价等域的系统性规则至 ≥60 条高质量规则。

---

## 6. S 级角色点名（任务书 §3 所列 12 人）

| 角色 | 实体 id | 富化 profiles | 判定 | 缺的最关键 3 项 |
|------|---------|---------------|------|----------------|
| 鲁迪乌斯 | E0001 | 26 | B-（量够、质半占位） | `appearance/body` 未建模；V003+ 13 个 phase 为模板；`origin_location_id` 缺 |
| 爱丽儿 | E0044 | ≤2（未进 Top15） | **D** | 政治五块全缺；`公开 vs 真实人格` 未拆分；`特殊兴趣/怪癖` 无证据 |
| 奥尔斯帝德 | E0079 | 3 | C- | 极端抉择/恐惧/龙神使命缺；行为案例仅 3 相位 |
| 人神 | E0032 | 2 | C- | 低语策略/信任操纵/不可信度模型缺 |
| 洛琪希 | E0005 | 3 | C | 米格路德族/水圣级/家庭教师期的 phase 演变断档；外貌/身体缺 |
| 艾莉丝 | E0021 | 7 | C+ | 剑术成长与暴力倾向的触发/应激模型薄 |
| 希露菲 | E0006 | 10 | C+ | 相对最好，但 `appearance/body/habits` 仍空 |
| 保罗 | E0002 | 1 | **D** | 几乎空白 |
| 扎诺巴 | E0022/E0152* | 4 | C- | 人偶执念/王族背景/与鲁迪的主从模型薄；`*需核对 id 归一` |
| 克里夫 | E0065 | 3 | C- | 教会/研究线与魔术才能的冲突模型缺 |
| 基列奴 | E0104 近似* | 2 | **D** | 剑王/兽族/忠诚模型几乎空白；`*id 待核` |
| 艾莉娜丽洁 | E0104/E0110* | 2 | **D** | 诅咒/冒险者生涯/人际网缺；`*id 待核` |

> 注：后三人的实体 id 存在 `E0022/E0152/E0104/E0110` 等候选，需以 `data/canon` 的全量 `entities` 表做一次 id 归一校验后再定重抽取清单。

---

## 7. 事件/关系/地点/势力 专项缺口清单

### 7.1 事件（需重建/增强的代表性清单，非穷举）

- **阿斯拉政变**（任务书示例）：当前无对应 `detailed_event`；需新建 1 个主事件 + 2-3 个子事件，补 `participants: 爱丽儿/格拉维尔/鲁迪/奥尔斯帝德阵营`、`involved_factions: 王位派系`、`political_impacts/world_impacts/long_term_impacts`、`participant_motivations/conflicts`。
- **转移事件/菲托亚领覆灭**、**魔大陆漂流**、**魔法大学入学**、**迷宫（转移迷宫）**、**人神低语关键节点**、**决战篇**：均需从 `events` 抽取层反查 `T00xx` 并落到富化 `detailed_events`，当前或缺或为模板句。

### 7.2 关系（优先 80-100 条高质量重建）

- 鲁迪→爱丽儿 / 爱丽儿→鲁迪（利益-信任双向）
- 鲁迪→奥尔斯帝德 / 奥尔斯帝德→鲁迪（恐惧-敬畏-合作演变）
- 鲁迪→人神（信任-怀疑拉锯，`beliefs` 需联动）
- 鲁迪↔洛琪希/艾莉丝/希露菲/保罗/扎诺巴/克里夫/基列奴/艾莉娜丽洁 的家庭/师徒/主从/恋爱维度
- 爱丽儿阵营内部（路克/希尔瓦等）与贵族派系对抗关系

### 7.3 地点（≥30 核心地点，三级层级）

- 大陆：中央大陆、魔大陆、米里斯大陆、贝卡利特大陆（若原文有据）
- 国家/地区：阿斯拉王国、米里斯神圣国、王龙王国、菲托亚领、夏利亚周边
- 城市/据点：罗亚、王都亚尔斯、夏利亚、魔法大学（地点+组织双建模）、布埃纳村
- 特殊：各类迷宫、龙神孔、森林/山丘地标

### 7.4 势力（≥10 核心势力）

- 阿斯拉王国（拆派系：爱丽儿派/格拉维尔派/中立贵族）、米里斯教会、魔法大学、冒险者协会、龙神阵营、人神阵营、魔族/兽族/长耳族等种族势力

---

## 8. 文本与编码质量

- **乱码/占位**：`abilities.name` 中出现 `��ӽ��ħ��`、`����ħ������ӽ������` 等；`relationship_changes.dimension` 出现 `Э��`/`�ж�`；`organizations.org_type` 含 `��������`；`character_profiles.phase_name` 存在 `��ͥ��ʦ��` 等。成因疑似早期富化批次在非 UTF-8 终端/脚本中写入导致，虽不触发 `enrich_verifier` 失败，但会污染检索与 LLM 上下文。
- **证据分层失效**：`confidence` 全 `EXPLICIT`，`evidence_type` 仅两类，未使用 `INFERENCE/UNKNOWN`，导致“强推断”与“原文显式”不可区分。
- **模板句污染**：`summary/behavior_changes_note/trigger/outcome` 中高频“见证据段”“V0x 期间”“形塑后卷人际与立场”等无指称句，约覆盖 11 个模板卷的 80% 文本。

---

## 9. 风险与约束

1. **原著真实性红线**：所有新增信息必须来自 `data/volumes_txt/` 或已有 `evidence`，每条重要数据保留 `source_volume/source_unit/evidence_ref/evidence_text`；禁止 wiki/粉丝设定/AI 幻想。
2. **分阶段替换**：模板卷（V003-V015、V019-V020）不可一次性全量重写，需按审计报告分阶段替换，每阶段后运行 `pytest` + `ruff` + `mypy` + `verify_enrichment` 并生成阶段报告。
3. **id 归一**：重建前需冻结 `data/canon` 的 `entity_id` 注册表，避免新建 `E0xxx` 与抽取层冲突。
4. **编码**：全链路强制 UTF-8，重跑前需对已污染字段做一次清洗迁移。

---

## 10. 下一步（严格按任务书 §10 执行顺序）

- **Phase 1（本报告）**：已完成。结论：不可直接进入模拟，需进入 Phase 2。
- **Phase 2 — S 级人物深度化**：以 12 人清单为范围，逐人补 `Character Simulation Profile` 的 30+ 字段，每人 ≥1 个 phase 的证据闭环，先鲁迪/爱丽儿/奥尔斯帝德/人神四人试点，验收标准见 §3。
- **Phase 3 — 爱丽儿专项增强**：单独建立 `Ariel Political Profile`，五块（王族身份/公开 vs 真实/政治行为模型/特殊兴趣与怪癖/领导能力）逐条带证据，禁止为丰富而创造。
- **Phase 4 — 事件深度化**：重建阿斯拉政变等关键事件的 `Event Simulation Model` 全字段，因果图可回答“改变某事件的后果”。
- **Phase 5 — 关系网络**：重建 80-100 条 `Relationship Dynamics`，量化 `trust/affection/respect/fear/dependency` 并绑定转折事件。
- **Phase 6 — 地图与势力**：地点 ≥30、势力 ≥10、路径与旅行观测补全。
- **Phase 7 — 生成 `WORLD_SIM_READINESS.md`**：以 §9 的四个自测问为准（爱丽儿面前撒谎/挑战奥尔斯帝德/加入阿斯拉/改变事件的后果），逐问给出数据库可回答性证明。

---

## 附录 A：审计证据索引

- 全量计数脚本：`python` 遍历 `data/canon_enriched/V*.json` 26 批次（见审计会话内 `/tmp/audit_clean.json`）。
- 字段填充率脚本：`CharacterProfile` 16 字段、`DetailedEvent` 5 扩展字段的非空率统计（本报告 §5.1/§5.2）。
- 抽样对照：V001（真实富集，465 条）、V003（模板，41 条）`character_profiles/behavior_cases/detailed_events/relationship_changes/world_rules` 的标题与句式差异（`build_enrich_generic.py:51-178` 为模板源）。
- 校验：`data/canon_enriched/report.json: is_clean=true, errors=[]`（结构层通过，语义层未覆盖）。

## 附录 B：术语

- **占位模板**：`scripts/build_enrich_generic.py` 为闭合 26 卷覆盖而生成的确定性模板批次，文本由卷名与固定句式拼装，证据为均匀采样的 chunk 行号，仅保证过检，不保证语义。
- **世界模拟就绪**：指 AI 仅凭数据库即可对反事实问题给出带证据的判定，而非仅能回答“该角色出现在哪一卷”。

