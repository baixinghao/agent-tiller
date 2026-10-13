---
title: README
status: active
last_updated: 2026-10-13
owner: harness
summary: Agent角色索引与协作流说明（路由表SSOT见CLAUDE.md）
---
# agents/ 目录

每个 Agent 是独立上下文。元 Agent 分派任务给专职 Agent。

## 索引

| Agent | 角色 | 激活条件 | 调用 Skill | 加载上下文 |
|-------|------|---------|-----------|-----------|
| owner.md | 元 Agent（协调者） | always | — | rules/编码规范 + 工程结构 + 01_ARCHITECTURE_CONSTRAINTS + code-discovery + MCP get_architecture |
| coding-agent.md | 编码 | "实现"/"修改"/"新增功能" | coding-skill | specs/{module} + wiki/数据模型 + wiki/接口协议 + code-discovery + MCP explore/trace |
| ddd-refactor-agent.md | DDD 重构 | "DDD重构"/"渐进式DDD"/"API重构"/"四层架构"/"领域驱动" | harness-api-refactor | rules/01_ARCHITECTURE_CONSTRAINTS + 02_COLA_DDD_PATTERNS + specs/（项目全景/路线图，接入后建立）+ MCP explore/trace/detect |
| ddd-architect-agent.md | DDD 架构师 | "DDD合规"/"分层检查"/"架构评审"/"领域模型"/"限界上下文" | code-discovery + expert-reviewer | rules/01_ARCHITECTURE_CONSTRAINTS + specs + MCP get_architecture/query_graph/trace_path/manage_adr |
| testing-agent.md | 测试 | "测试"/"验证"/"CI" | unit-test-write / unit-test-ci | specs/{module} + 测试数据目录（如有）+ code-discovery + MCP explore |
| doc-gardening-agent.md | 文档园丁 | 每日/每周定时 or "文档"/"新鲜度" | code-discovery | 全部 .md 文件 + MCP 漂移检测 |
| requirement-analysis-agent.md | 需求分析（管线入口守门人） | "分析需求"/"解析PRD"/"需求分析" | doc-analysis | doc/request/ + rules/01_ARCHITECTURE_CONSTRAINTS + wiki/领域术语 + wiki/数据模型 + MCP search/trace |
| requirement-review-agent.md | 蓝军评审（红蓝对抗，独立session） | "评审需求"/"需求评审"/"蓝军评审" | requirement-review | .harness/requests/{需求名}/ 产物 + rubric 文件（🔴 信息节食，禁看红军过程） |

## 协作流

```
用户请求
  ↓
owner.md（元 Agent）
  ├─ 意图匹配（trigger_keywords）
  ├─ 分派给专职 Agent
  ├─ 监控红线不违反
  └─ 接收各 Agent 的异常报告
      ↓
  ┌─────────────────────────────────────────────────────────────┐
  │                                                             │
  requirement-analysis-agent  ← 管线入口：需求 → 结构化报告        │
  (需求分析/PRD解析)             输出 .harness/requests/ + sql/   │
  → doc-analysis                 §3.9 红线冲突 → [BLOCKER] 阻断  │
  │                                                             │
  coding-agent        ddd-refactor-agent      ddd-architect-agent│
  (COLA DDD编码)      (DDD API级重构)         (DDD合规+架构评审) │
  → coding-skill      → harness-api-refactor  → code-discovery   │
                                              → expert-reviewer │
  │                                                             │
  testing-agent       doc-gardening-agent                         │
  (验证测试)           (文档健康检查)                             │
  → unit-test-write   → code-discovery                           │
  → unit-test-ci                                                 │
  └─────────────────────────────────────────────────────────────┘
```

## DDD 重构协作流

> DDD 重构是 ddd-refactor-agent 和 ddd-architect-agent 的协作：

```
ddd-refactor-agent（执行重构）
  ↓ 每个 API 完成后
ddd-architect-agent（合规检查）
  ↓ 合规通过
[NEXT] → ddd-refactor-agent（继续下一个 API）
  ↓ 合规失败
ddd-refactor-agent（回滚 + 修复）→ 重新提交合规检查
```

## 意图路由规则

> 📌 **路由表的唯一来源（SSOT）**：根目录 `CLAUDE.md` 的「⚡ 意图路由与执行指令」（含歧义消解、BATCH_MODE 与"架构探索"行）。
> 本文件不再维护副本；新增/修改路由只改 CLAUDE.md。

## 上下文隔离
每个 Agent 只加载自己需要的文件：
- coding-agent 不需要 rules/01_ARCHITECTURE_CONSTRAINTS 的全文细节（红线由门禁机械兜底）
- ddd-refactor-agent 不需要 wiki/接口协议（API 契约不变）
- ddd-architect-agent 不修改业务代码（只读 + ADR）
- testing-agent 不需要 wiki/数据模型（它只看 specs 的契约和真实流量）
- doc-gardening-agent 不需要 rules（它不写代码）
- 项目自建的测试数据/快照目录不参与新鲜度检查（历史快照不是活文档）
