---
title: README
status: active
last_updated: 2026-10-13
owner: harness
summary: agent-tiller 框架介绍与快速接入指南
---
# agent-tiller

> AI-native 的 COLA DDD 项目治理框架：**意图路由 + 红线门禁 + 文档园丁 + 自进化闭环**。
> 把一个"AI 写代码"的项目，升级成一个"AI 在规则里写代码、规则在踩坑中进化"的项目。

## 这是什么

一套可直接拷进任意 COLA DDD 项目（Java / Spring Boot / Maven 多模块）的治理体系：

- **意图路由（SSOT）**：`CLAUDE.md` 一张路由表，把"分析需求 / 写代码 / 评审 / 重构 / 文档"等意图分派给 8 个专职 Agent，每个 Agent 配独立 Skill playbook。
- **红线门禁**：`rules/01` 定义 B1-B4 业务安全 / D1-D7 DDD 分层 / C1-C5 代码规范红线；`harness_gate.py` 挂进 pre-commit，CRITICAL 违规直接阻断提交。
- **红蓝对抗的需求管线**：红军（doc-analysis）产出结构化需求报告（状态机/时序图/决策表 + SQL DDL），蓝军（requirement-review）独立 session 对抗评审，lint 工具先做机械检查，蓝军只做语义判断。
- **文档园丁**：新鲜度 / 死链 / 文档↔代码漂移三类扫描，产物统一收敛到 `.harness/index/DOC_HEALTH.md`。
- **自进化闭环**：踩坑 → lessons 暂存 → 蒸馏回流 rules/skills/tools；`changes/active → shipped` 归档强制知识蒸馏；规则变更强制 ADR 留痕（`EVOLUTION_LOG.md`）。
- **渐进式 DDD 重构引擎**：遗留模块按 API 逐个迁移，8 步工作流 + PROGRESS.md 状态机 + 强制挂起/回滚护栏。

## 核心特性

| 特性 | 机制 | 入口 |
|------|------|------|
| 意图路由 | 关键词 → Agent → Skill 三步分派，歧义消解规则内置 | `CLAUDE.md` |
| 红线守护 | B/D/C 三组红线 SSOT，违反 CRITICAL 即终止 | `.harness/rules/01_ARCHITECTURE_CONSTRAINTS.md` |
| 可执行门禁 | AST 索引 + DDD 合规检查 + pre-commit 钩子 | `.harness/tools/harness_gate.py` |
| 需求红蓝对抗 | 意图对齐（Step 0.5）→ 红军报告 → lint → 蓝军 9 项评审 → 整改闭环（最多 2 轮） | `skills/doc-analysis` + `skills/requirement-review` |
| 文档健康 | 新鲜度 90 天阈值 / 死链 / 漂移，报告型不阻断 | `tools/doc_*` 三件套 |
| 知识蒸馏 | 归档强制蒸馏章节；同类问题 2 次必须固化为规则或 lint | `rules/03_SELF_EVOLUTION.md` |
| 遗留迁移状态机 | 逐 API 8 步、⬜/✅/❌ 三态、失败回滚矩阵 | `skills/harness-api-refactor` |

## 目录结构

```
agent-tiller/
├── README.md               # 本文件：框架介绍 + 快速接入
├── AGENTS.md               # 项目入口：代码地图 + 治理索引（拷入后按项目填写）
├── CLAUDE.md               # 意图路由 SSOT（Claude Code 自动加载）
└── .harness/
    ├── agents/             # 8 个 Agent 角色定义 + README
    ├── rules/              # 01 红线 SSOT / 02 COLA 模式 / 03 自进化 / 工程结构 / 编码规范 / 开发流程 / 文档元数据
    ├── skills/             # 8 个技能 playbook（doc-analysis / requirement-review / coding-skill / ...）
    ├── tools/              # 9 个可执行治理脚本（见下表）
    ├── lessons/            # 教训暂存区（open → distilled → closed）
    ├── specs/              # 模块规格（README 为编写指南，接入后自建）
    ├── wiki/               # 业务模型 / 接口协议 / 数据模型 / 领域术语（空模板）
    ├── changes/            # active（进行中）/ shipped（已上线快照）
    ├── requests/           # 需求分析报告输出（目录即档案）
    ├── index/              # 工具生成物（AST_INDEX / COMPLIANCE_REPORT / DOC_HEALTH，禁手改）
    └── EVOLUTION_LOG.md    # 规则 ADR 日志
```

## 快速接入

```bash
# 1. 把框架拷进你的项目根目录
cp -r .harness/ /path/to/your-project/
cp AGENTS.md CLAUDE.md /path/to/your-project/

# 2. 安装 Python 依赖（AST 索引用）
pip install tree-sitter tree-sitter-java

# 3. 安装 pre-commit 门禁钩子（幂等，已有钩子自动备份）
python .harness/tools/install_hooks.py

# 4. 按你的项目改写占位内容
#    - CLAUDE.md「项目概览」表：项目名/技术栈/模块现状
#    - .harness/rules/01 §3-§5：业务域划分、URN 登记表、模块职责字典
#    - .harness/wiki/ 四个模板：业务模型/接口协议/数据模型/领域术语
#    - .harness/skills/code-discovery/SKILL.md「项目标识」：CBM_PROJECT / CG_PATH（不用 MCP 图谱工具可跳过）
#    - 包名前缀默认自动推断（build_ast_index.py），如需显式指定：export HARNESS_INTERNAL_PREFIX=com.yourcompany

# 5. 验证门禁
python .harness/tools/harness_gate.py --fast    # 阻断式：AST 索引 + DDD 合规
python .harness/tools/harness_gate.py --full    # 全量：追加文档健康三件套
```

## 工具一览

| 工具 | 用途 | 阻断式 |
|------|------|:---:|
| `build_ast_index.py` | tree-sitter 解析全模块 Java，生成 AST 索引树（`index/AST_INDEX.md` + `ast_index.json`）；模块自动发现，内部包前缀自动推断 | — |
| `ddd_compliance_check.py` | DDD 红线可执行检查（D3/D4/D5/D6 + 3 项启发式 WARNING），输出 COMPLIANCE_REPORT + 历史趋势 jsonl | ✅ CRITICAL 非零退出 |
| `harness_gate.py` | 门禁编排器：`--fast`（pre-commit）/ `--full`（追加文档健康） | ✅ fast 档 |
| `install_hooks.py` | 幂等安装 pre-commit 钩子（已有钩子自动备份 .bak） | — |
| `doc_freshness_scan.py` | frontmatter 元数据 + 90 天新鲜度 + 代码 mtime 漂移 + deprecated 引用检查 | — |
| `doc_link_check.py` | Markdown 死链 + specs 索引一致性（兼容根目录 / .claude/ 两种 CLAUDE.md 布局） | — |
| `doc_drift_scan.py` | wiki/specs 中的类名、API 路径对照真实代码，检测文档↔代码漂移 | — |
| `summary_lint.py` | 需求报告机械检查 v2（状态机终态/死状态/锚点错位/表读写矩阵 L1-L8）+ 蓝军矩阵骨架生成 | ✅ CRITICAL 非零退出 |
| `alignment_mapper.py` | 意图注入映射表草稿生成：落点锚点脚本真实定位，杜绝手写错位 | — |

## 文档园丁与自进化

**文档园丁**（doc-gardening-agent）不人肉翻文档：跑工具 → 读 DOC_HEALTH.md → 时间戳/死链自动修，语义漂移只告警 + 开 lesson（语义判断归人）。

**自进化闭环**（rules/03）：

```
踩坑/拦截/报警 → lessons/ 暂存（open）
  → 同类问题第 2 次出现 → 强制回流：rules 新红线 / skills 流程补丁 / tools 新 lint（distilled）
  → 回流产物验证有效 → closed
changes/active → shipped 归档 = 唯一强制蒸馏节点（知识蒸馏章节为空不许归档）
rules/ 实质修改 → EVOLUTION_LOG.md 留 ADR（日期/改了什么/触发事件/影响面）
```

## License

MIT（见 LICENSE，发布前补充）
