---
title: requirement-review
status: active
last_updated: 2026-10-13
owner: harness
summary: 蓝军评审技能：独立session对抗审查需求分析产物，产出findings驱动红军整改
---

# SKILL — 需求分析蓝军评审（Requirement Review）

> 红蓝对抗的蓝军 playbook。对 requirement-analysis-agent 的产出做**对抗性审查**，
> 产出结构化 findings，驱动红军整改闭环。
> **适用门槛：仅 complexity=complex 的需求强制评审；simple/medium 直接 PASS 放行。**

---

## 1. 独立性与信息节食（🔴 对抗有效性的根基）

- 🔴 蓝军必须在**独立 session** 执行，与红军 session 上下文隔离
- 🔴 **信息不对称**：蓝军只读"产物 + 回放日志 + rubric 文件"，
  **禁止**向人类索要红军的思维链、对话记录或"当时是怎么想的"——
  看到红军推理过程即继承其假设，对抗失效
- 🔴 蓝军**不修改**红军的任何产物，唯一输出是 `review-findings.md`
- 🟡 同厂商异 session 即可满足独立性；异厂商为加分项，非准入门槛

## 2. 输入（全部来自 `.harness/requests/{需求名}/`）

| 文件 | 用途 |
|------|------|
| `summary.md` | 被审主产物（报告） |
| `_review/alignment-log.md` | 意图对齐流水（注入保真复核的依据） |
| `_review/review-request.md` | 红军开单（产物清单 + 自评 + 建议评审重点） |
| `_review/review-findings.md`（前轮，如存在） | 🔴 **并集复核**：逐条判定"仍有效→并入本轮 / 已失效→注明原因"，禁止覆盖丢弃前轮成果 |
| `sql/*.sql`（项目根目录） | 被审 DDL |
| `doc/request/{原始PRD}` | 原始输入（蓝军独立扫雷用） |

**rubric 参照**：`rules/01_ARCHITECTURE_CONSTRAINTS.md` §1、`.harness/wiki/领域术语.md`、
`.harness/skills/doc-analysis/SKILL.md` 的产出规范（§3.5-3.8 图表规范）、
`.harness/rules/文档元数据规范.md`。

## 2.5 执行流程（lint 先行 + 两遍制）

### 第 0 步：lint 先行（🔴 不可跳过）

```bash
python .harness/tools/summary_lint.py .harness/requests/{需求名}/summary.md
```

机械检查（状态机终态/死状态/锚点引用/规则引用/表读写矩阵）由脚本完成，
输出 `_review/lint-report.md`。蓝军**必须**将其作为 findings 基线：
复核真实性后并入 findings（标注来源 `[lint]`），**禁止忽略或重复劳动**。
lint 覆盖了 R4/R5/R9 的机械半边，蓝军把精力留给语义判断。

### 第 1 遍：单产物检查（R1-R8）

逐表逐节过 R1-R8，产出单产物 findings。

### 第 2 遍：跨图 + 独立扫雷（R9 + R3）——lint 出矩阵，蓝军填判断

🔴 **禁止手工建矩阵**。lint v2 已在 `_review/lint-report.md` 生成三张矩阵骨架
（① 转移清单含事件/动作、② 表读写矩阵含写入/读取动作、③ 引用核对清单含核对结果），
蓝军的工作是**填判断列**：逐行复核"时序图对应步骤/决策表规则/权威数据源/问题"，
矩阵中的空格、"待核"、❌ 格就是 findings 候选。

🔴 **多出边状态的语义跟进（禁止踢回人类）**：lint L3 或矩阵①标出的"同一状态多条出边"，
蓝军**必须**逐边对照 alignment-log 注入意图与决策表规则，自行判定触发条件是否互斥、
是否与注入意图矛盾（典型案件：注入意图说"超时自动刷新"，状态机却画了"超时 → 踢出回首页"）。
确实无法判定的，标 MAJOR 并写明缺什么信息，**禁止原样写"需人工确认"——语义分析是蓝军的活，不是人类的**。

🔴 **前轮 findings 并集（限 CRITICAL/MAJOR）**：进场发现前轮 `review-findings.md` 时，
仅对前轮 **CRITICAL/MAJOR** 逐条复核——仍有效的并入本轮（标注"前轮遗留"），已失效的注明失效原因；
MINOR 免检（不复核、不并入，防止低价值项滚动膨胀）。禁止静默丢弃。

最后执行 R3 独立扫雷：通读原始 PRD，列出红军未标记的歧义。

## 3. 评审检查项（9 项，逐项过）

> 🔴 **R9 跨图一致性为最高优先级**：单图规范合格不代表产物合格，需求报告的核心产物是 Mermaid 图，图与图打架就是实现事故。

| # | 检查项 | 通过标准 |
|---|--------|---------|
| R1 | **注入保真** | 对照 alignment-log：每条注入意图**忠于人类原话**，无添油加醋、无缩水、无静默丢弃 |
| R2 | **降级合规** | 每个 `[🟡待澄清]` 项附人类确认记录；无人类确认的降级 = CRITICAL |
| R3 | **歧义漏判** | 蓝军**独立**通读原始 PRD 扫一遍歧义，红军漏掉的每个语义断层 = MAJOR 起 |
| R4 | **报告规范** | 状态图技术打标、时序图 autonumber/participant/数据变量、决策表矩阵格式（对照 doc-analysis §3.5-3.8） |
| R5 | **数据模型** | 三范式合理性（快照反范式需有注释说明）、唯一约束、索引覆盖查询场景 |
| R6 | **术语对齐** | 实体/字段命名符合 wiki/领域术语，新造词 = MAJOR |
| R7 | **红线** | 对照 rules/01 §1 逐条，B1 防重/B2 脱敏在方案中必须有明确机制 |
| R8 | **状态一致性** | frontmatter `status` 与红灯消除/降级确认的实际状态匹配；`intent_aligned` 真实性 |
| R9 | **跨图一致性**（最高优先级） | 状态机↔时序图↔决策表↔注入意图四方互查，逐项核对：<br>① 每个状态机转移在时序图中有对应步骤，反之亦然<br>② 每张 DDL 表至少有一张图写入、一张图读取（无人写入的表 = CRITICAL）<br>③ 决策表规则触发条件与状态机转移条件不互斥（同一事件两条互斥转移 = CRITICAL）<br>④ 注入意图的落点引用（状态名/转移名/步骤号/规则号）**真实存在**，引用不存在的锚点 = MAJOR<br>⑤ 同一数据只有一个权威数据源；DB/Redis 双写必须声明以谁为准<br>⑥ 接口职责单一：查询接口不得夹带写库动作；与遗产/PRD 不同的 redesign 必须有文字说明 |

## 4. 输出：`review-findings.md` 模板

```markdown
---
feature: {需求名}
review_round: 1
verdict: PASS | FAIL-可整改 | FAIL-重做
reviewer: requirement-review-agent
date: YYYY-MM-DD
---

# 蓝军评审 Findings — {需求名}（第 N 轮）

## 结论
{一句话结论 + 统计：CRITICAL x / MAJOR x / MINOR x}

## Findings

| # | 级别 | 位置（文件/章节/图/字段） | 问题 | 整改要求 |
|---|------|--------------------------|------|---------|
| F-1 | CRITICAL | summary.md §4 状态机 | 无成功终态，SUBMIT_ORDER 后断裂 | 补 FINISHED 终态及 WAITING_PUSH→FINISHED 转移 |

## 通过项（抽查确认无问题的检查项）
- R2 降级合规：4 项均附人类确认原话 ✅
```

**结论三态**：
- `PASS`：无 CRITICAL/MAJOR → 红军将 status 转 `approved`，对抗闭环
- `FAIL-可整改`：有 CRITICAL/MAJOR 但不推翻主干 → 红军按 findings 整改，写 revision-log，进入第 2 轮
- `FAIL-重做`：主干逻辑错误/注入大面积失真 → 报告作废，红军重走 Step 0

## 5. 熔断与升级

- 最多 **2 轮**评审；第 2 轮仍 FAIL → findings 标注 `ESCALATE`，由人类裁决，禁止无限抛光
- MINOR 项不阻断 PASS，登记即可（可随编码阶段顺手修）

## 6. 禁止

- 🔴 禁止修改红军产物（报告/DDL/日志）
- 🔴 禁止评审 simple/medium 需求（看到 complexity ≠ complex 直接输出 PASS 并说明）
- 🔴 禁止把 findings 写成建议清单散文——必须逐条可执行（位置 + 问题 + 整改要求）
- 🔴 禁止与红军同 session 执行
- 🔴 **findings 的位置引用必须真实可复核**——行号/规则号/状态名/转移名必须指向真实存在的锚点，禁止凭印象编造引用；引用前必须打开文件核对
