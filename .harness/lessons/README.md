---
title: lessons README
status: active
last_updated: 2026-10-13
owner: harness
summary: 教训暂存区：lesson 文件命名、生命周期与回流规则
---

# lessons/ — 教训暂存区

> lessons 是教训的**暂存区，不是终点**。每条教训最终都要回流到 rules/（新红线）、skills/（流程补丁）或 tools/（lint 检查项），回流规则见 [rules/03_SELF_EVOLUTION.md](../rules/03_SELF_EVOLUTION.md)。

## 文件命名

每条 lesson 一个文件：`YYYY-MM-DD-{slug}.md`

- 日期 = 教训发生/记录当天
- slug = 英文短横线小写，能看懂是啥事，如 `2026-10-13-acl-dto-leak.md`
- 模板：[LESSON_TEMPLATE.md](LESSON_TEMPLATE.md)

## 生命周期

```
open（已记录） → distilled（已回流，注明去向） → closed（验证有效后关闭）
```

| 状态 | 含义 | 流转条件 |
|------|------|---------|
| open | 已记录，待分类回流 | 发现问题时立即开 |
| distilled | 已回流到 rules/skills/tools | 回流产物落地，正文中注明去向 |
| closed | 回流产物验证有效 | 同类问题不再出现（至少经过一个变更周期） |

| 规则 | 说明 |
|------|------|
| 🔴 open 状态积压是流程失效信号 | 月度健康页检查，积压必须清理 |
| 🟡 同类问题第 2 次出现，对应 lesson 必须转 distilled | 见 03_SELF_EVOLUTION.md §5 进化触发器 |
| 🟡 closed 的 lesson 不删除 | 留着当判例，EVOLUTION_LOG 引用用 |
