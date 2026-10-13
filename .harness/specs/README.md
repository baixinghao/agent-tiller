---
title: specs README
status: active
last_updated: 2026-10-13
owner: harness
summary: 模块规格编写指南：如何为新项目建立 specs 目录（框架附带模板说明，不含具体项目规格）
---
# specs/ — 模块规格编写指南

> 本框架不附带任何具体项目的规格文件。接入新项目后，按本指南在 specs/ 下建立自己的规格体系。
> specs 是 coding-agent / testing-agent / ddd-architect-agent 的进场必读上下文——规格缺失，Agent 只能靠猜。

## 建议建立的文件

| 文件 | 时机 | 内容 | 读者 |
|------|------|------|------|
| `00_PROJECT_OVERVIEW.md` | 接入时 | 项目全景：业务域划分、模块清单、技术栈、外部系统清单 | 全体 Agent |
| `01_REFACTOR_ROADMAP.md` | 有遗留模块待迁移时 | 重构路线图：模块顺序、里程碑、当前阶段 | owner / ddd-refactor |
| `PROGRESS.md` | 遗留迁移启动时 | 逐 API × 8 Step 的进度状态机（符号仅限 ⬜/✅/❌，模型定义见 [skills/harness-api-refactor/SKILL.md](../skills/harness-api-refactor/SKILL.md) §4.0） | ddd-refactor |
| `{module}/README.md` | 每个 DDD 模块一个 | 模块边界、实体清单、约束（模板见下） | coding / testing |

## 模块 README 模板（`{module}/README.md`）

每个模块的 README.md 必须包含：

```markdown
---
title: {module} 模块规格
status: active
last_updated: YYYY-MM-DD
owner: {责任角色}
summary: {模块一句话定位}
---
# {module} 模块规格

## 1. 边界

| 维度 | 内容 |
|------|------|
| input | {入口：哪些 Controller/API 属于本模块} |
| output | {出口：对外暴露哪些领域能力/事件} |
| dependencies | {依赖哪些模块/外部系统（经 ACL/Gateway）} |
| dependents | {被谁依赖} |

## 2. 业务实体清单

| 实体 | 类型（聚合根/实体/值对象） | 说明 | 关键属性 |
|------|--------------------------|------|---------|

## 3. 约束列表

- {本模块特有的业务/技术约束，逐条列出}
```

## 规则

- 🔴 模块 README 由元 Agent / 文档园丁维护，coding-agent 只读（可建议更新，不直接改）
- 🔴 `PROGRESS.md` 是遗留迁移的唯一真相源：AI 不得声称完成未标记 ✅ 的步骤
- 🟡 模块规格与实际代码漂移时，由 doc-gardening 告警（doc_drift_scan.py）+ 开 lesson
