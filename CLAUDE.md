---
title: CLAUDE
status: active
last_updated: 2026-10-13
owner: harness
summary: 项目唯一入口：意图路由SSOT与全生命周期分派
---
# CLAUDE.md — 项目入口（意图路由 SSOT）

> **本文件是整个项目的唯一入口**：意图路由与生命周期分派的唯一来源（SSOT）。
> 详细规范不内嵌于此，一律通过指针按需加载，保持本文件轻量。
> 🔧 标注「接入填写」的小节，拷入你的项目后必须改写。


## 项目概览（🔧 接入填写）

| 属性 | 值 |
|------|-----|
| 项目 | {项目名} {版本} — {一句话定位} |
| 后端 | {技术栈，如 Spring Boot 3.3.5, MyBatis-Plus 3.5.9, Redisson, Spring AMQP} |
| JDK/构建 | {如 JDK 21, Maven 多模块} |
| 数据库 | {如 MySQL (生产) / H2 (本地开发)} |
| 架构 | COLA 四层 DDD (interfaces → application → domain ← infrastructure) |
| 现状 | {如：order 模块 DDD 重构已完成（作为分层标杆）；项目处于正常功能开发阶段} |

---

## 红线

> 📌 **唯一来源（SSOT）**：[.harness/rules/01_ARCHITECTURE_CONSTRAINTS.md §1](.harness/rules/01_ARCHITECTURE_CONSTRAINTS.md)（B1-B4 业务安全 / D1-D7 DDD 分层 / C1-C5 代码规范）。
> 任何代码任务执行前必须 Read 该节并逐条校验，违反 CRITICAL 项即终止。

---

## ⚡ 意图路由与执行指令（SSOT）

> 匹配成功后执行三步：① 确定目标 Agent → ② Read 对应 Skill 文件 → ③ 携带 Skill 指令执行任务。

| 用户意图关键词 | → Agent | → Skill | 说明 |
|---------------|---------|---------|------|
| "分析需求"/"解析PRD"/"需求分析" | requirement-analysis-agent | doc-analysis | **管线入口**：需求 → 结构化报告（输出 .harness/requests/），红线冲突即 [BLOCKER] |
| "评审需求"/"需求评审"/"蓝军评审" | requirement-review-agent | requirement-review | **蓝军对抗**（独立 session 执行）：审查 requests/{需求名}/ 产物，产出 review-findings.md |
| "整改需求"/"需求整改"/"按findings整改" | requirement-analysis-agent | doc-analysis（§5.3 接单模式） | **红军整改**：凭 requests/{需求名}/ 档案接管，不依赖原 session 上下文 |
| "实现"/"修改"/"新增功能"/"修bug" | coding-agent | coding-skill | COLA DDD 编码 6 步流程 |
| "重构"（无 DDD 上下文） | coding-agent | coding-skill | 常规重构走编码流程 |
| "测试"/"验证"/"覆盖率" | testing-agent | unit-test-write / unit-test-ci | 单测编写 + CI 质量门禁 |
| "DDD合规"/"分层检查"/"架构评审"/"领域模型"/"限界上下文" | ddd-architect-agent | code-discovery + expert-reviewer | 合规检查与架构评审（只读 + ADR） |
| "文档"/"新鲜度"/"一致性" | doc-gardening-agent | code-discovery | 文档健康检查（驱动 doc_freshness_scan / doc_link_check / doc_drift_scan，产物 DOC_HEALTH.md） |
| "DDD重构"/"API重构"/"四层架构"/"DDD迁移" | ddd-refactor-agent | harness-api-refactor | **遗留迁移流程**：仅遗留模块迁移时启用，走 specs/PROGRESS.md 状态机；含"全部"/"批量"时 BATCH_MODE |
| "架构探索" | owner（自执行） | arch-explore | 仅手动 /arch-explore 触发 |

> **歧义消解**："重构"一词 — 上下文涉及 DDD/四层架构/领域驱动 → ddd-refactor-agent；否则 → coding-agent。

---

## 🔄 标准开发流水线（正常功能开发）

```
需求 → requirement-analysis-agent（.harness/requests/ 结构化报告）
     → coding-agent（COLA DDD 编码，遵守红线）
     → 合规门禁（pre-commit 自动跑 python .harness/tools/harness_gate.py --fast，CRITICAL 阻断提交）
     → testing-agent（单测 + CI）
     → 变更记录（.harness/changes/active/ → shipped/，归档前必须完成知识蒸馏）
     → 教训回流（lessons/ → rules/skills/tools，见 rules/03_SELF_EVOLUTION.md）
```

> DDD 重构遗留流程（PROGRESS.md 状态机 / 8 步工作流）仅在迁移遗留模块时启用，不参与日常开发。
> 框架不附带 PROGRESS.md——首次启动遗留迁移时按 harness-api-refactor §4.0 状态模型创建。

---

## 🧰 工具与索引

| 资产 | 位置 | 用途 |
|------|------|------|
| 代码发现 | [.harness/skills/code-discovery/SKILL.md](.harness/skills/code-discovery/SKILL.md) | CBM / codegraph 工具路由（Claude Code 走 MCP，其他环境走 CLI，含降级策略） |
| AST 索引 | [.harness/index/AST_INDEX.md](.harness/index/AST_INDEX.md) | 全模块结构树（模块自动发现，重生成：`python .harness/tools/build_ast_index.py`） |
| 合规门禁 | `.harness/tools/ddd_compliance_check.py` | DDD 红线可执行检查（输出 COMPLIANCE_REPORT.md + compliance_history.jsonl 趋势，CRITICAL 非零退出） |
| 质量门禁编排 | `.harness/tools/harness_gate.py` | `--fast`（pre-commit 阻断 CRITICAL）/ `--full`（追加文档健康三件套）；钩子安装：`install_hooks.py` |
| 文档健康 | `.harness/tools/doc_freshness_scan.py` / `doc_link_check.py` / `doc_drift_scan.py` | 新鲜度+元数据 / 死链+索引一致性 / 文档↔代码漂移，统一输出 [.harness/index/DOC_HEALTH.md](.harness/index/DOC_HEALTH.md) |
| 自进化 | [.harness/rules/03_SELF_EVOLUTION.md](.harness/rules/03_SELF_EVOLUTION.md) | 教训回流管道 + 蒸馏节点 + 度量 + 规则 ADR（日志见 [.harness/EVOLUTION_LOG.md](.harness/EVOLUTION_LOG.md)） |

---

## 📂 文件索引

| 类别 | 位置 | 用途 |
|------|------|------|
| Agent 定义 | [.harness/agents/](.harness/agents/) | owner / coding / testing / ddd-architect / doc-gardening / requirement-analysis / requirement-review（蓝军）/ ddd-refactor（遗留迁移） |
| 规则 | [.harness/rules/](.harness/rules/) | 01 架构约束（红线 SSOT）/ 02 COLA 模式 / 03 自进化机制 / 工程结构 / 编码规范 / 开发流程规范 / 文档元数据规范 |
| 教训暂存 | [.harness/lessons/](.harness/lessons/) | open → distilled → closed 生命周期的教训回流管道（见 rules/03） |
| 演化日志 | [.harness/EVOLUTION_LOG.md](.harness/EVOLUTION_LOG.md) | harness 体系自身的 ADR 式变更记录（rules/ 修改必填） |
| 规格 | [.harness/specs/](.harness/specs/) | 模块规格（README 为编写指南：项目全景 / 重构路线图 / PROGRESS.md 接入后按需建立） |
| 知识库 | [.harness/wiki/](.harness/wiki/) | 业务模型 / 接口协议 / 数据模型 / 领域术语（接入后填充） |
| 技能 | [.harness/skills/](.harness/skills/) | doc-analysis / requirement-review（蓝军）/ coding-skill / expert-reviewer / unit-test-write / unit-test-ci / code-discovery / harness-api-refactor（遗留迁移） |
| 原始需求（输入） | `doc/request/` | 原始 PRD/需求文档（接入后自建），requirement-analysis-agent 的分析输入 |
| 需求分析报告（输出） | [.harness/requests/](.harness/requests/) | `{需求名}/summary.md` 结构化分析报告（由 agent 生成） |
| 变更 | [.harness/changes/](.harness/changes/) | active（进行中，可读写）/ shipped（已上线，只读） |
| 代码地图 | [AGENTS.md](AGENTS.md) | 项目入口与代码地图（接入后按项目填写） |
