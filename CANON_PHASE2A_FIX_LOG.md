# Canon Phase 2-A 修复日志（Fix Log）

> 对应审计报告：`CANON_PHASE2A_AUDIT_REPORT.md` · 质量评分：`CANON_QUALITY_SCORE.json` · 隔离库：`data/canon_quarantine/` · 工具：`tools/canon_quality_check.py`
> 原则：所有正式 Canon 信息必须来自 `data/raw/无职转生TXT合集.txt` 经 `parse_source → source_unit → evidence_text` 链路；禁止外部 wiki/百科/AI 幻觉补全；`UNKNOWN_ENCODING` 宁可标记不猜测修复。

---

## 变更 1 — 新建审计报告

- 文件: `CANON_PHASE2A_AUDIT_REPORT.md`（新建，14KB）
- 修改: 全库扫描并落盘 §1-§9 审计结论、数据规模、编码/空字段/重复/Placeholder 统计、风险等级、Manifest 指纹、来源可信度与复现命令。
- 原因: Phase 2-A 要求“结构检查 ≠ 质量检查”，需建立语义质量基线并为隔离提供依据。
- 依据: 26 卷 JSON 全量遍历（`data/canon/` 414 entities、`data/canon_enriched/` 675 evidence 等）、`manifest.json:batch_counts` 固定 41 产量、跨卷去重统计（24 个字符串 ≥5 卷复用）。
- 影响: 明确污染面 15 卷×41=615 条；后续 Phase 2-B 重抽取范围锁定为 V003-V015/V019-V020；不改任何权威数据。

## 变更 2 — 新建隔离库（不删除原数据）

- 文件: `data/canon_quarantine/invalid_entries.json`（新建，626KB，615 条）
- 修改: 将 V003-V015、V019-V020 共 15 卷的全部 enrichment 记录镜像隔离为 `{"id","type","source_file","original_content","reason":"template_pollution"}`。
- 原因: 全量批次均为 `build_enrich_generic.py` 确定性模板（每卷 16 evidence + 3 profiles + 8 cases + 4 events + 2 rules + 1×7 杂项 =41），属“假完整”且语义空洞，不能进入正式 Canon。
- 依据: `manifest.json` 15 卷同为 41 的固定产量指纹；`behavior_cases` 等 10 字段跨 15 卷完全复用同一话术；`evidence` 为均匀采样 16 个 chunk、与陈述无语义对应。
- 影响: 原 `data/canon_enriched/V*.json` 保持不变（不删除、不覆写），隔离库仅作审计与回滚依据；Phase 2-B 重抽取后方可替换。

- 文件: `data/canon_quarantine/V003.json … V015.json, V019.json, V020.json`（复制，15 份，各 ~36KB）
- 修改: 原批次完整复制至隔离目录作“污染快照”。
- 原因: 保留现场以支撑 diff 与回溯。
- 依据: 同上。
- 影响: 不影响运行；为 git 提供完整隔离前后对比。

- 文件: `data/canon_quarantine/manifest_analysis.json`（新建，2.1KB）
- 修改: 记录 `batch_counts` 分布、`fixed_41_count=15`、`generic_generation_probability=true`、`quarantine_volumes`、`invalid_entries_by_type`。
- 原因: Task 5 要求标记 `generic_generation_probability`；不直接改写 `manifest.json` 以免破坏权威快照。
- 依据: `data/canon_enriched/manifest.json` 的 `batch_counts` JSON 串解包后 `Counter` 统计。
- 影响: 质量门禁与审计可直接读取该标记；Phase 2-B 重抽取后需重算 `manifest.json:content_sha256` 与 `batch_counts`。

## 变更 3 — 编码修复判定（UNKNOWN_ENCODING 路径）

- 文件: 无直接落盘修复（符合“不能 100% 确认则不猜”原则）
- 修改: 对 `data/canon/` 26 + `data/canon_enriched/` 26 + `data/parsed/` + `data/db/` 全库 52 个 JSON 逐字节 `utf-8` 严格解码扫描；追加西里尔块 `[\u0400-\u04FF]` 与 `U+FFFD` 全扫。
- 原因: 任务书指摘 `��/Э��/latin1/gbk` 污染；终端曾复现 GBK 展示乱码，易误判为落盘污染。
- 依据: 实测结果 **0 字节解码失败、0 个 U+FFFD、0 个西里尔字符**（见审计报告 §3 表）；`V001 behavior_cases.context: 刚接触魔术教科书…` 与 `V003 evidence.chapter_title: 第一话「自称神的骗子」` 均可正常通过 `Read` 工具读取。
- 影响: 不产生 `UNKNOWN_ENCODING` 条目；若后续在旧备份中发现真实残留，按本日志约定的 `reason=encoding_error` 进入隔离库且不做猜测映射（如不将 `Э��` 臆断为某角色）。

## 变更 4 — 新建 Canon Quality Checker

- 文件: `tools/canon_quality_check.py`（新建，~430 行）
- 修改: 实现 `contains_template / score_record(0/60/100) / score_volume / check_manifest / build_quarantine_report / main --audit/--check-manifest/--quarantine-report`；输出 `CANON_QUALITY_SCORE.json`（26 卷评分、manifest 指纹、quarantine 汇总）。
- 原因: Task 4 要求“每条数据评分”与可复现的语义门禁；`is_clean` 仅覆盖结构，需语义层门禁。
- 依据: 评分规则 100=有 source_volume/source_unit/evidence_text 且实体/事实明确可用；60=有来源但信息单薄；0=模板/无来源/空描述/编码错误。模板指纹取自 `build_enrich_generic.py` 的 `title_hint/synopsis/evidence_note` 等 32 个子串（含 `见证据段/阶段性收束…/形塑后卷/为后事提供前提/见该卷/权衡后协作…`）。
- 影响: `V001 83分(465条)`、`V002 80分` 达标；`V003-V015/V019-V020 均 45-46分` 被标 `quarantine_recommended=true`；全库均分 62 用作 Phase 2-B 准入门槛。

- 文件: `tools/__init__.py`（新建，空）
- 修改: 使 `tools` 成为可导入包以通过 `from tools.canon_quality_check import …` 的 pytest 导入。
- 原因: 测试需导入 checker。
- 依据: Python 包约定。
- 影响: 无运行影响。

- 文件: `CANON_QUALITY_SCORE.json`（生成，13KB，`tools/canon_quality_check.py --audit` 产物）
- 修改: 26 卷 `{"volume","score","total_records","counts_by_score":{"100":..,"60":..,"0":..},"issues","quarantine_recommended"}` + `manifest` + `quarantine` 聚合。
- 原因: 为 GM 模拟提供“是否可用”的机器可读门禁。
- 依据: 同变更 4。
- 影响: 示例：`V003 score 46 issues:[template_entries] quarantine_recommended:true`；后续 PR 可对此文件做阈值断言。

## 变更 5 — 新建测试与配置

- 文件: `tests/test_canon_quality.py`（新建，10 用例）
- 修改: 覆盖 `contains_template / score_record 100/0/60 / score_volume 阈值 / check_manifest generic指纹 / quarantine 615条 / CANON_QUALITY_SCORE.json schema`。
- 原因: 工程规则“生产行为测试先行”；为质量门禁提供回归网。
- 依据: 审计报告与隔离库事实。
- 影响: 全量 `pytest 289 passed`（含既有 279）；新增用例对重抽取后的分数提升可直接断言。

- 文件: `pyproject.toml`（编辑，2 行）
- 修改: `tool.ruff.lint.per-file-ignores` 追加 `"tests/test_canon_quality.py" = ["RUF001","RUF003"]` 与 `"tools/*.py" = ["RUF001","RUF003"]`。
- 原因: 富化语料与模板指纹含大量全角标点（`（ ） ， ： 「 」`），属语料本身，不应被 `RUF001/RUF003` 误报。
- 依据: 既有 `src/overlord_worldsim/canon/*.py` 与 `tests/canon/*.py` 的同类豁免。
- 影响: `ruff check` 全通过；不放宽其他规则。

## 变更 6 — 格式化与类型修复

- 文件: `tools/canon_quality_check.py` / `tests/test_canon_quality.py`（ruff format 定型）
- 修改: `ruff format` 与 `ruff check --fix` 后的缩进/引号/导入排序定型；修复 `mypy` 的 `evidence_ids: set[str]` 显式注解。
- 原因: 满足 `ruff check + ruff format --check + mypy --pretty` 全绿门禁。
- 依据: `pyproject.toml` 的 `line-length 100 / target-version py314 / strict mypy`。
- 影响: 289 用例不受影响。

---

## 未变更项（刻意保留）

- `data/canon/` 26 卷抽取层：未改（权威层，仅审计不修复）。
- `data/canon_enriched/manifest.json`：未改（保留 `content_sha256 a82f8a4…` 快照；污染标记落在隔离库与评分文件中，避免直接改写权威 manifest）。
- `data/canon_enriched/V001/V002/V016-V018/V021-V026` 等非污染卷：未改（评分已达标，留待 Phase 2-C/2-D 再补强地点/势力/S级）。
- `data/raw/无职转生TXT合集.txt` / `data/parsed/`：未改（来源链权威，仅作只读校验）。

---

## 验证

```bash
PYTHONPATH=src python tools/canon_quality_check.py --audit            # 26 卷评分，15 卷 <50
PYTHONPATH=src python tools/canon_quality_check.py --check-manifest   # generic_generation_probability true, fixed_41=15
PYTHONPATH=src python tools/canon_quality_check.py --quarantine-report # invalid_entries 615
.venv/Scripts/python -m pytest -q                   # 289 passed
.venv/Scripts/python -m ruff check src tools tests  # All checks passed
.venv/Scripts/python -m ruff format --check src tools tests # 45 already formatted
.venv/Scripts/python -m mypy src tools --pretty     # Success: no issues in 20 files
```

---

## 验收对照（Phase 2-A §六）

- [x] 全库无乱码字段 — 52 JSON 零字节错误，西里尔/FFFD 零命中（展示乱码属终端 codepage，已记录）
- [x] 所有正式 Canon 数据可追溯 source — `volume_no/unit_id/source_start_line/source_end_line` 全量校验通过，污染卷语义脱钩已隔离
- [x] Generic 模板数据全部隔离 — `data/canon_quarantine/invalid_entries.json` 615 条 + 15 份快照
- [x] 不存在无来源事实 — `score_record` 对 `evidence_refs` 空/悬空直接判 0 分，门禁已落地
- [x] manifest 统计可信 — `manifest_analysis.json` 与 `CANON_QUALITY_SCORE.json:manifest` 标记 `generic_generation_probability=true`
- [x] 新增 quality checker — `tools/canon_quality_check.py` + 10 用例
- [x] pytest 通过 — 289/289
- [x] 不破坏 source canon — 原文件零覆写，仅隔离
- [x] 保留完整 git diff — 本日志即 diff 说明，隔离库保留污染快照
