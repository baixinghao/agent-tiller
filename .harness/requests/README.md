---
title: requests-README
status: active
last_updated: 2026-10-13
owner: harness
summary: 需求分析报告输出目录规范：目录即档案，_review/ 存放红蓝对抗过程文件
---

# requests/ — 需求分析报告输出目录

> 本目录是 requirement-analysis-agent 的**输出**位置（`.harness/requests/{需求名}/summary.md`）。
> **输入**（原始 PRD/需求文档）请放 `doc/request/`，不要放在这里。

## 目录即档案（一个需求一个文件夹，全生命周期聚合）

```
.harness/requests/{需求名}/
├── summary.md              # 需求分析报告（红军主产物）
└── _review/                # 红蓝对抗过程文件（下划线前缀 = 非主产物）
    ├── alignment-log.md    # 意图对齐流水（红军实时记录）
    ├── review-request.md   # 评审请求单（红军开单）
    ├── review-findings.md  # 蓝军 findings
    └── revision-log.md     # 整改记录（红军修订）
```

## 规则

- 🔴 `_review/` 为过程性文件目录：报告 `status: approved` 归档后，doc-gardening 可定期清理 `_review/`，主产物 `summary.md` 永久保留
- 🔴 红蓝分 session：红军写 summary/alignment-log/review-request/revision-log；蓝军只写 review-findings
- 🟡 进入编码阶段后，changes/active/{feature}/summary.md 放指针指回本目录做需求溯源
