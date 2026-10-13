---
title: README
status: active
last_updated: 2026-10-13
owner: harness
summary: 进行中变更目录规范与summary模板（含知识蒸馏强制章节）
---
# changes/active/ — 进行中的变更

## 目录结构

```
active/{feature-name}/
├── summary.md          # 变更概述
├── db-migrations.sql   # 数据库变更（DDL/DML）
└── rollback.sql        # 回滚脚本
```

## summary.md 模板

```markdown
---
feature: {feature-name}
status: in_progress
created: YYYY-MM-DD
owner: {owner}
---

## 变更概述
<!-- 描述本次变更的内容 -->

## 影响模块
<!-- 列出受影响的模块 -->

## 数据库变更
<!-- 描述数据库变更 -->

## API 变更
<!-- 描述 API 变更 -->

## Redis 变更
<!-- 描述 Redis Key 变更 -->

## 关键约束
<!-- 列出关键约束 -->

## 回滚方案
<!-- 描述回滚步骤 -->

## 知识蒸馏
<!-- 必填章节：本次变更沉淀下来的知识，归档 shipped 前校验，为空（或只剩注释）则不允许归档 -->

### 踩坑与教训
<!-- 本次变更踩了什么坑、怎么踩的、怎么爬出来的；没踩坑写"无" -->

### 回流清单
<!-- 教训回流到哪：rules | skills | tools | wiki | 无回流（无回流须说明原因） -->
```

## 规则

- 🔴 每个变更必须包含 summary.md
- 🔴 数据库变更必须同时提供 rollback.sql
- 🔴 变更完成后移动到 changes/shipped/
- 🔴 `## 知识蒸馏` 为必填章节：归档 shipped 时此章节为空（或只剩占位注释）则不允许归档，机制见 [rules/03_SELF_EVOLUTION.md](../../rules/03_SELF_EVOLUTION.md) §2
