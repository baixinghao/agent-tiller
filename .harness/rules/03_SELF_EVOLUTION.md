---
title: 03_SELF_EVOLUTION
status: active
last_updated: 2026-10-13
owner: harness
summary: harness 体系自进化机制 SSOT：回流管道、蒸馏节点、度量、规则 ADR、进化触发器
---

# 03 — 自进化机制（SSOT）

> 核心主张：**AI-native 体系必须让 AI 越来越懂系统，规则不能只在人脑子里演化。**
> 每一次踩坑、每一次蓝军拦截、每一次门禁报警，都要沉淀成可复用的资产——红线、技能、lint 检查项，而不是当事人口头记住就算完。
> 本文档是自进化机制的唯一来源（SSOT），其余文件只留指针。

---

## 1. 回流管道

四类回流来源，四个目的地。来源负责"产生教训"，目的地负责"固化教训"。

| 回流来源 | 典型形态 | 目的地 | 固化形态 |
|---------|---------|--------|---------|
| 蓝军 review-findings 的共性问题 | 同一类缺陷在多次评审中反复出现 | rules/ | 新红线（进 01 §1 或对应专项规则） |
| shipped 变更踩的坑 | 上线后回滚、返工、线上异常 | skills/ | 流程补丁（前置检查、操作步骤修订） |
| 合规门禁的历史违规模式 | compliance_history.jsonl 中反复出现的违规项 | tools/ | 新 lint 检查项（机械检查，不再靠人盯） |
| AI 执行任务时的误判记录 | 路由错、工具用错、上下文读漏 | lessons/ | 暂存待分类，评审后分流到前三个目的地 |

回流优先级：**tools/ > rules/ > skills/ > lessons/**。能写成机械检查的绝不留给人记——先例：`summary_lint v2` 把蓝军 R9 评审项沉淀为脚本检查，蓝军不再重复审同一件事。

lessons/ 是缓冲带，不是垃圾桶：每条 lesson 必须有明确的回流去向或"暂无"的说明，评审通过后状态流转（见 [.harness/lessons/README.md](../lessons/README.md)）。

---

## 2. 蒸馏节点（强制）

`changes/active → changes/shipped` 归档是**唯一的强制知识蒸馏节点**：

- summary.md 必须填写 `## 知识蒸馏` 章节（模板见 [changes/active/README.md](../changes/active/README.md)）。
- 章节为空（或只有占位注释）**不允许归档**，由执行归档操作的角色在移动目录前校验。
- 蒸馏产物（lesson 文件 / 规则变更 / skill 补丁）随 summary 一并进入 shipped 快照。

理由：踩坑的记忆在归档那一刻最新鲜，过了这个村就没这个店。不强制，蒸馏永远不会发生。

---

## 3. 度量

进化有没有效，看趋势，不看感觉。

| 度量指标 | 数据来源 | 健康方向 |
|---------|---------|---------|
| 合规违规趋势 | `.harness/index/compliance_history.jsonl`（ddd_compliance_check.py 累计） | CRITICAL/WARN 数量逐月下降 |
| 文档 stale 率 | `.harness/index/DOC_HEALTH.md`（doc_freshness_scan.py 生成） | stale 文档占比逐月下降 |
| 死链/漂移数量 | DOC_HEALTH.md 的 LINK_CHECK / DRIFT 区块 | 逐月收敛到 0 |
| open 状态 lesson 数量 | `.harness/lessons/` 目录 | 不积压，每条有归宿 |

**每月由 owner 角色过一遍"系统健康页"**（compliance_history.jsonl + DOC_HEALTH.md + lessons/ 清单）。任何指标趋势恶化，必须开 lesson 记录原因和改进动作——不许"下个月再说"。

---

## 4. 规则 ADR

`rules/` 下任何实质修改（新增红线、修订条文、调整阈值），必须在 [.harness/EVOLUTION_LOG.md](../EVOLUTION_LOG.md) 留 ADR 式记录：

| 字段 | 内容 |
|------|------|
| 日期 | 变更生效日 |
| 改了什么 | 具体到条文编号或章节 |
| 触发事件 | 哪次评审/踩坑/违规触发的（贴 lesson 或变更名） |
| 影响面 | 影响哪些 agent / skill / 流程 |

格式调整（typo、链接修复）不强制记录。原则：**教训不丢**——半年后没人记得为什么加这条红线，但 ADR 记得。

---

## 5. 进化触发器

> **同一类问题出现 ≥ 2 次 → 必须固化为规则或 lint，不许第三次还靠人记。**

执行判定：

| 触发信号 | 动作 |
|---------|------|
| 同一类问题第 1 次出现 | 开 lesson 记录（status: open） |
| 同一类问题第 2 次出现 | 强制回流：升级为 rules 红线 / skill 补丁 / tools lint 检查项，lesson 转 distilled |
| 第 3 次仍靠人肉拦截 | 视为流程失效，在月度健康页复盘时追责到机制，不追责到人 |

---

## 6. 与其他文件的关系

| 文件 | 关系 |
|------|------|
| [01_ARCHITECTURE_CONSTRAINTS.md](01_ARCHITECTURE_CONSTRAINTS.md) §1 | 红线 SSOT，自进化回流的目的地之一，本文件不复制红线内容 |
| [开发流程规范.md](开发流程规范.md) | QG-10/QG-11 与蒸馏节点是本机制的流程落点 |
| [changes/active/README.md](../changes/active/README.md) | 蒸馏模板与归档校验规则 |
| [lessons/README.md](../lessons/README.md) | lesson 生命周期定义 |
| [EVOLUTION_LOG.md](../EVOLUTION_LOG.md) | 规则 ADR 的存放处 |
