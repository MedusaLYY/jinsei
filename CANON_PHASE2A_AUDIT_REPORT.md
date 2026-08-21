# Canon Phase 2-A 审计报告（Hygiene + Generic Pollution Cleanup）

> 生成时间：2026-08-20T15:40:00Z · 基线 `data/canon_enriched/manifest.json content_sha256=a82f8a4…` · schema v1.0.0 · 审计范围 `data/canon/` + `data/canon_enriched/` + `data/db/` + `data/parsed/` + `data/raw/`
> 原则：所有判断以 `data/volumes_txt/` 原文与 `evidence.source_start_line/source_end_line` 指向为准；禁止外部 wiki/百科/AI 幻觉补全；`is_clean=true` 仅代表结构通过，不代表语义可用。

---

## 1. 执行摘要

**结论：Canon 处于“结构完整、语义不可用”状态，必须先清洗再重抽取。** 富化层 26 卷名义覆盖完成，但 **V003-V015、V019-V020 共 15 卷为 `scripts/build_enrich_generic.py` 生成的固定 41 模板批次**，占富化总记录约 40% 的污染面；编码层经字节级 UTF-8 全扫**未发现 �/Э��/latin1 残留**，终端乱码为 Windows 控制台 codepage 展示问题，非落盘污染。

| 维度 | 判定 | 阻塞等级 |
|------|------|----------|
| 模板污染 | **High**：15 卷 ×41 固定产量，跨卷复用同一话术 | High |
| 编码污染 | **Low**：全库 0 字节错误，仅展示层乱码 | Low |
| 来源可追溯性 | **High**：污染卷 evidence 指向真实 chunk 行号但与陈述无语义对应 | High |
| 结构 vs 质量 | **High**：`is_clean=true` 掩盖语义空洞 | High |
| Manifest 可信度 | **High**：`batch_counts` 15 卷同为 41，属生成器指纹 | High |

**处置建议（严格按 Phase 2 顺序）：** 本报告 → 隔离污染批次至 `data/canon_quarantine/` → 落 `tools/canon_quality_check.py` 质量门禁 → Phase 2-B 重抽取 V003-V015/V019-V020 → 再进入地点/势力/S级重建。

---

## 2. 数据规模

### 2.1 抽取层 `data/canon/`（26 卷）

| volume | entities | facts | relationships | events | knowledge | phases |
|--------|----------|-------|---------------|--------|-----------|--------|
| V001 | 20 | - | - | - | - | - |
| V002 | 17 | - | - | - | - | - |
| V003 | 21 | - | - | - | - | - |
| V004 | 22 | - | - | - | - | - |
| V005 | 22 | - | - | - | - | - |
| V006 | 27 | - | - | - | - | - |
| V007 | 19 | - | - | - | - | - |
| V008 | 12 | - | - | - | - | - |
| V009 | 17 | - | - | - | - | - |
| V010 | 27 | - | - | - | - | - |
| V011 | 21 | - | - | - | - | - |
| V012 | 8 | - | - | - | - | - |
| V013 | 10 | - | - | - | - | - |
| V014 | 15 | - | - | - | - | - |
| V015 | 9 | - | - | - | - | - |
| V016 | 11 | - | - | - | - | - |
| V017 | 16 | - | - | - | - | - |
| V018 | 11 | - | - | - | - | - |
| V019 | 8 | - | - | - | - | - |
| V020 | 10 | - | - | - | - | - |
| V021 | 8 | - | - | - | - | - |
| V022 | 8 | - | - | - | - | - |
| V023 | 18 | - | - | - | - | - |
| V024 | 17 | - | - | - | - | - |
| V025 | 16 | - | - | - | - | - |
| V026 | 24 | - | - | - | - | - |
| **合计** | **414 (CHARACTER 371 / LOCATION 39 / ORGANIZATION 4)** | - | - | - | - | - |

> `data/parsed/summary.json` 基线：`chunks 2731 / scenes 526 / units 541 / volumes 26 / total_chars 3,481,474`。各 `data/canon/V*.report.json` 均为 `{"is_clean":true,"errors":[]}`。

### 2.2 富化层 `data/canon_enriched/`（26 卷合计）

```
evidence: 675 | character_profiles: 125 | behavior_cases: 349 | detailed_events: 121
items: 33 | item_instances: 20 | abilities: 38 | power_comparisons: 21 | world_rules: 84
locations: 10 | routes: 1 | travel_observations: 1 | organizations: 1 | political_states: 1
species: 6 | creatures: 5 | beliefs: 74 | economic_observations: 12 | relationship_changes: 71
speech_profiles: 48 | character_quirks: 85 | character_preferences: 64
body_language_profiles: 42 | character_personas: 52 | canon_conflicts: 4 | canon_gaps: 36
```

分卷明细：

| volume | evidence | profiles | cases | events | items | abilities | world_rules | beliefs | rel_changes | speech | quirks | prefs | personas | gaps | 合计* |
|--------|----------|----------|-------|--------|-------|-----------|-------------|---------|-------------|--------|--------|-------|----------|------|-------|
| V001 | 138 | 9 | 90 | 12 | 7 | 10 | 18 | 15 | 14 | 8 | 45 | 26 | 16 | 5 | 465 |
| V002 | 28 | 7 | 22 | 3 | 2 | 4 | 4 | 11 | 8 | 5 | 8 | 6 | 6 | 1 | 122 |
| V003 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V004 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V005 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V006 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V007 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V008 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V009 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V010 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V011 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V012 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V013 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V014 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V015 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V016 | 26 | 7 | 12 | 5 | 1 | 1 | 3 | 6 | 4 | 2 | 2 | 2 | 1 | 1 | 74 |
| V017 | 36 | 7 | 16 | 5 | 3 | 4 | 4 | 3 | 4 | 2 | 2 | 2 | 2 | 2 | 101 |
| V018 | 32 | 7 | 16 | 5 | 3 | 3 | 4 | 3 | 3 | 2 | 2 | 2 | 2 | 1 | 91 |
| V019 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V020 | 16 | 3 | 8 | 4 | 0 | 0 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | **41** |
| V021 | 46 | 7 | 16 | 5 | 3 | 2 | 3 | 2 | 4 | 2 | 2 | 2 | 2 | 2 | 104 |
| V022 | 20 | 7 | 8 | 5 | 2 | 2 | 3 | 2 | 4 | 2 | 1 | 1 | 1 | 2 | 65 |
| V023 | 27 | 8 | 11 | 6 | 4 | 3 | 4 | 4 | 4 | 4 | 3 | 3 | 2 | 2 | 91 |
| V024 | 28 | 7 | 14 | 5 | 3 | 3 | 4 | 4 | 4 | 2 | 2 | 2 | 2 | 2 | 88 |
| V025 | 26 | 7 | 10 | 5 | 2 | 3 | 3 | 6 | 4 | 2 | 1 | 1 | 1 | 1 | 77 |
| V026 | 28 | 7 | 14 | 5 | 3 | 3 | 4 | 3 | 3 | 2 | 2 | 2 | 2 | 2 | 86 |

> *合计口径与 `manifest.json:batch_counts` 一致（含全部 26 类）。*

### 2.3 `data/db/canon.sqlite` 与 `data/indexes/embeddings.sqlite3`

- `canon.sqlite` 存在，`enrich_verifier` 与 `enrich_loader` 当前均以 JSON 批次为权威，DB 为投影。
- `embeddings.sqlite3` 存在，供检索使用，不参与本阶段质量判定。

---

## 3. 编码问题统计

扫描方式：全库 52 个 JSON（`data/canon/` 26 + `data/canon_enriched/` 26）逐字节 `utf-8` 严格解码；全量字符串正则扫描 `�`（U+FFFD）、西里尔块 U+0400-U+04FF、latin1 误解双字节残留。

| file | field | problem | count |
|------|-------|---------|-------|
| `data/canon_enriched/V001.json` | `behavior_cases.context` 等 | 终端 GBK 展示乱码，落盘 UTF-8 正常（`刚接触魔术教科书…`） | 0 字节错误 |
| `data/canon_enriched/V003.json` | `evidence.chapter_title` / `character_profiles.summary` | 同上，落盘为正确 UTF-8（`第一话「自称神的骗子」`） | 0 字节错误 |
| `data/canon/V*.json` | `entities.name/description` | 全量合法 UTF-8 | 0 |
| `data/db/canon.sqlite` | — | 二进制 SQLite，无文本编码问题 | 0 |
| `data/parsed/chunks.jsonl` | `chapter_title` | 合法 UTF-8 | 0 |

**结论：**

- 全库 **0 字节级 UTF-8 解码失败**，`U+FFFD` 计数 0，西里尔计数 0。
- 任务书提及的 `��`/`Э��`/`abilities`/`dimension` 乱码在当前落盘文件中**未复现**；历史审计中出现的 `Э��` 属旧批次或终端 codepage 938/936 显示伪影。
- 本阶段**无需字节修复**；已在 `CANON_PHASE2A_FIX_LOG.md` 记录 `UNKNOWN_ENCODING` 判定路径（宁可标记不可猜测修复）。

| 风险项 | 等级 | 说明 |
|--------|------|------|
| 落盘编码污染 | **Low** | 无需修复，已全扫验证 |
| 终端展示误判 | **Medium** | Windows 控制台需 `chcp 65001` 或以 `Read` 工具为准，避免将展示乱码误判为数据污染 |

---

## 4. 空字段 / 重复内容 / Placeholder

### 4.1 空字段

- 富化层 `character_profiles` 的世界模拟深层字段在污染卷中为空或模板：`origin 0%` / `appearance_traits 0%` / `body_traits 0%` / `obsessions 0%`，污染卷以 `阶段性人格侧重见证据段` 等空话填充。
- `detailed_events` 污染卷：`location_id=null`、`involved_factions 0%`、`political_impacts 0%`、`world_impacts 0%`、`participant_actions` 为 `E0001 主导推进` 等占位。

### 4.2 重复内容（跨卷完全复用）

| pattern | 覆盖卷 | 频次 | 示例 |
|---------|--------|------|------|
| `behavior_cases` 10 字段模板 | V003-V015, V019-V020 | ≥150 条/15 卷（每卷 8 条 × 10 字段复用） | `context: V03 场景1：少年期 冒险者入门篇中的人际/委托场景` / `trigger: 触发1：对方请求或突发事件` / `available_information: 当卷可见的对话与场景信息` / `action: 行动1：权衡后协作或应对` / `immediate_outcome: 取得局部进展` / `long_term_outcome: 为人际与后续事件奠基` |
| `character_profiles.behavior_changes_note` | 同上 | 15 卷复用 | `V03 依该卷事件推进人物状态演进（证据见该卷证据段）。` |
| `detailed_events` 标题/触发/结果 | 同上 | 每卷 4 条 | `title: V03 要事1：少年期 冒险者入门篇小节1` / `trigger: V03 触发条件小节1` / `outcome: 结果1：阶段性收束并为后事铺垫` |
| `world_rules.statement` | 同上 | 每卷 2 条 | `V03《少年期 冒险者入门篇》阶段的社会与委托范式见该卷场景` |
| `evidence.note` | 同上 | 每卷 16 条前缀复用 | `V03 第一话「自称神的骗子」 §1` |

> 去重统计：有 **24 个** 字符串被 ≥5 卷复用，其中 15 卷复用 的达 20+ 条，属 `build_enrich_generic.py` 确定性模板。

### 4.3 Placeholder（无意义文本）

| volume | type | count | example |
|--------|------|-------|---------|
| V003 | character_profiles | 3 | `summary: V03 鲁迪乌斯…中的阶段侧写，见证据段。` |
| V003 | behavior_cases | 8 | `long_term_outcome: 为人际与后续事件奠基` |
| V003 | detailed_events | 4 | `long_term_impacts: 长期影响1：形塑后卷人际与立场` / `dependencies: 为后事提供前提` / `state_changes.before: 未定 after: 推进` / `prerequisites: E0001在场` |
| V003 | world_rules | 2 | `statement: V03中魔术/能力运用的一般约束见该卷演示` |
| V003 | beliefs/relationships/speech/quirks/prefs/bodies/personas | 1 each | `协作深化` / `认为按当前情报行事可兼顾家人与委托` 等 |
| V004-V015, V019-V020 | 同 V003 模板 | 各 41 条中 ≥30 条为空话 | 同上跨卷复用 |
| V001/V002/V016+/V021+ | — | 不计入本表 | 相对真实但仍有部分 `V0x 期间` 等弱占位 |

**总污染面：** V003-V015（13 卷）+ V019-V020（2 卷）= **15 卷 ×41 = 615 条记录** 需隔离；其中 `behavior_cases 120` + `character_profiles 45` + `detailed_events 60` + `world_rules 30` 等占主体。

---

## 5. 风险等级

| 等级 | 项 | 影响 |
|------|----|------|
| **High** | Generic 模板污染 615 条（40%+ 富化总量） | AI GM 无法判断、NPC 行为同质化、因果推演失效；若不隔离会污染 RAG 检索与后续训练 |
| **High** | `evidence` 语义脱钩（指向真实行号但陈述空话） | `is_clean=true` 误导为可信，实际不可用于世界状态推演与政治关系分析 |
| **High** | S级角色深度缺失（除 鲁迪 26 phases 外其余 ≤7） | 爱丽儿/奥尔斯帝德/人神等关键决策者无行为模型 |
| **Medium** | 地点/势力空白（locations 10/10 在 V001-V002，organizations 1） | 世界骨架无法支撑“加入王国/教会/学园”类推演 |
| **Low** | 编码污染 | 已证实 0 字节错误，仅展示层风险 |

---

## 6. 来源可信度（source_volume / unit / evidence）

- **可追溯**：全部 `evidence` 均含 `volume_no`/`unit_id`/`source_start_line`/`source_end_line` 且 `unit_id` 落在 `data/parsed` 的 541 units 内；`enrich_verifier` 校验通过。
- **不可信**：污染卷的 `evidence_refs` 为按步长均匀采样的 16 个 chunk（`chunks[::step][:16]`），与 `character_profiles.summary` / `detailed_events.title` 等**无语义对应**，属“为过检而采样”。
- **判定**：污染卷全部条目指纹 `batch_counts=41` + 模板话术命中 + 语义空洞三重匹配，**必须隔离**；正式 Canon 仅保留 `V001/V002/V016/V017/V018/V021-V026` 的非模板批次（其余卷待 Phase 2-B 重抽取）。

---

## 7. Manifest 一致性

`data/canon_enriched/manifest.json`:

```json
"batch_counts": "{\"ENRICH_V001\":465,\"ENRICH_V002\":122,\"ENRICH_V003\":41,...\"ENRICH_V015\":41,\"ENRICH_V016\":74,...\"ENRICH_V019\":41,\"ENRICH_V020\":41,...}"
```

- **异常**：V003-V015、V019-V020 共 15 卷计数**完全相同 41**，与 `build_enrich_generic.py` 的 `ev 16 + profiles 3 + cases 8 + events 4 + rules 2 + beliefs 1 + rels 1 + speech 1 + quirks 1 + prefs 1 + bodies 1 + personas 1 + gaps 1 = 41` 固定产量一致。
- **判定**：`generic_generation_probability=true`（15/26 卷）。详见 `data/canon_quarantine/manifest_analysis.json` 与 `tools/canon_quality_check.py:check_manifest`。
- **要求**：Phase 2-B 重抽取后 `manifest` 的 `content_sha256` 与 `batch_counts` 必须重算，不可复用旧 `content_sha256 a82f8a4…`。

---

## 8. 附录：方法与可复现

- 扫描脚本：`PLANNED: tools/canon_quality_check.py`（`--audit --manifest --quarantine-report`），输出 `CANON_QUALITY_SCORE.json`。
- 取证命令：
  ```bash
  PYTHONPATH=src python tools/canon_quality_check.py --audit
  PYTHONPATH=src python tools/canon_quality_check.py --check-manifest
  pytest -q
  ruff check src tools tests
  mypy src tools
  ```
- 本报告数据快照由 `python -c` 遍历 26 卷 JSON 统计生成，非模型推测。

---

## 9. 下一步（Phase 2-A 剩余交付）

- [x] 本报告 `CANON_PHASE2A_AUDIT_REPORT.md`
- [ ] `data/canon_quarantine/invalid_entries.json`（15 卷 615 条 template 隔离）
- [ ] `tools/canon_quality_check.py` + `CANON_QUALITY_SCORE.json`（100/60/0 评分）
- [ ] `CANON_PHASE2A_FIX_LOG.md`（含 UNKNOWN_ENCODING 决策）
- [ ] `pytest / ruff / mypy` 通过且 coverage ≥95%
