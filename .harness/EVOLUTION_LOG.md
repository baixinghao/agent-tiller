---
title: EVOLUTION_LOG
status: active
last_updated: 2026-10-13
owner: harness
summary: harness 体系自身演化日志（ADR 式），rules/ 实质修改必须在此留痕
---

# EVOLUTION_LOG — harness 演化日志

> rules/ 下任何实质修改（新增红线、修订条文、调整阈值）必须在此追加一条 ADR 式记录：日期 / 改了什么 / 触发事件 / 影响面。
> 机制定义见 [rules/03_SELF_EVOLUTION.md](rules/03_SELF_EVOLUTION.md) §4。新记录追加在表格顶部（新的在上）。

## ADR 记录

| 日期 | 改了什么 | 触发事件 | 影响面 |
|------|---------|---------|--------|
| 2026-10-13 | 框架自实战项目抽取并开源：① 治理文档全套通用化（agents 8 角色 / rules 7 件 / skills 8 技能，业务域与项目特定表述全部改写为占位或 demo 示例）；② 工具链 9 件套开源（build_ast_index / ddd_compliance_check / doc_freshness_scan / doc_link_check / doc_drift_scan / harness_gate / install_hooks / summary_lint / alignment_mapper）；③ build_ast_index 内部包前缀由硬编码改为自动推断（HARNESS_INTERNAL_PREFIX 可覆盖），doc_link_check 兼容根目录与 .claude/ 两种 CLAUDE.md 布局；④ 新增框架级 README / AGENTS / CLAUDE 三入口 | 治理体系在实战项目中验证有效，抽取为可复用到任意 COLA DDD 项目的独立框架包 | 全体接入方：按 README 快速接入；rules/01 §3-§5 业务域占位必须按项目改写 |

## 记录规则

| 规则 | 说明 |
|------|------|
| 实质修改才记 | typo、死链修复等格式调整不强制 |
| 触发事件要可溯源 | 贴 lesson 文件名、变更名或评审记录，不许写"觉得该改" |
| 影响面写到角色 | 写清哪些 agent / skill / 流程受影响，方便相关方知会 |
