---
title: README
status: active
last_updated: 2026-10-13
owner: harness
summary: 已上线变更归档规范（历史快照只读）
---
# changes/shipped/ — 已上线的变更

## 目录结构

```
shipped/{feature-name}/
├── summary.md          # 变更概述（历史快照）
├── db-migrations.sql   # 数据库变更（已执行）
└── rollback.sql        # 回滚脚本
```

## 规则

- 🔴 shipped 中的内容是**历史快照**，Agent 不可修改
- 🔴 仅由元 Agent 在变更上线后从 active/ 移动到 shipped/
- 🟡 可供回滚参考
- 🟡 归档前必须完成知识蒸馏：summary.md 的 `## 知识蒸馏` 章节非空，蒸馏产物（lesson/规则变更/skill 补丁）随 summary 一并归档，机制见 [rules/03_SELF_EVOLUTION.md](../../rules/03_SELF_EVOLUTION.md) §2
