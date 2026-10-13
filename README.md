---
title: README
status: active
last_updated: 2026-10-13
owner: harness
summary: agent-tiller 框架介绍与快速接入指南（架构无关，DDD 仅为示例规则包）
---
# agent-tiller

> AI-native 的编码治理框架：**意图路由 + 红线门禁 + 文档园丁 + 自进化闭环**。
> 把一个"AI 写代码"的项目，升级成一个"AI 在规则里写代码、规则在踩坑中进化"的项目。

## 这是什么

一套可直接拷进任意项目的治理体系。它解决的不是"怎么分层"，而是四个更底层的问题：

- **AI 怎么知道该听谁的**：`CLAUDE.md` 一张意图路由表（SSOT），把"分析需求 / 写代码 / 评审 / 重构 / 文档"分派给 8 个专职 Agent，每个 Agent 配独立 Skill playbook。
- **AI 怎么不越线**：红线写成文档更写成代码，`harness_gate.py` 挂进 pre-commit，CRITICAL 违规直接阻断提交。
- **文档怎么不腐烂**：文档园丁三类扫描（新鲜度 / 死链 / 文档↔代码漂移），产物统一收敛到 `.harness/index/DOC_HEALTH.md`。
- **体系怎么越用越聪明**：踩坑 → lessons 暂存 → 蒸馏回流 rules/skills/tools；归档强制知识蒸馏；规则变更强制 ADR 留痕。

## ⚠️ 架构无关性：本框架不依赖 DDD

**先说明白：agent-tiller 的内核与你的架构风格毫无关系。** 充血模型、贫血模型、MVC 三层、事务脚本、整洁架构——都能用。仓库里自带的 COLA 四层 DDD 内容只是一个**示例规则包**（rule pack），来自框架诞生时的实战项目，演示"规则能写到多细、门禁能压到多实"。它不是前提，更不是布道。

| 层次 | 内容 | 与架构的关系 |
|------|------|--------------|
| **内核（架构无关，直接用）** | 意图路由、Agent/Skill 机制、pre-commit 门禁编排、文档园丁三件套、红蓝对抗需求管线、lessons/蒸馏/ADR 自进化闭环、变更管理（changes） | 零依赖。任何语言、任何架构、任何团队规范都适用 |
| **示例规则包（可整体替换）** | `rules/01` 的 D1-D7 分层红线、`rules/02` COLA 模式、`ddd_compliance_check.py` 检查器、`harness-api-refactor` 遗留迁移技能 | 只是"红线即代码"的一种实现。你的架构是什么，就把规则包换成什么 |

**不用 DDD 怎么接入？** 三步：

1. 把 `rules/01` 里 D1-D7 换成你自己的架构红线（比如"Controller 不许直连 Mapper""Service 不许跨库 join"），B1-B4（幂等/脱敏/SQL 注入/异常处理）是通用安全底线，建议原样保留；
2. 把 `ddd_compliance_check.py` 换成检查你自己红线的脚本（它本质是"AST 索引 + 规则断言 + 退出码"的骨架，照着改即可；`build_ast_index.py` 和门禁编排、文档三件套都是通用的，不用动）；
3. 其余内核组件原样工作。

现实里大多数项目是贫血模型——没关系，治理的价值恰恰在"规矩说了算并且跑得动"，而不在流派。**你的规范是什么，门禁就检查什么；AI 犯的错，会变成下一条自动检查的规矩。** 这才是 agent-tiller。

## 核心特性

| 特性 | 机制 | 架构依赖 |
|------|------|:---:|
| 意图路由 | 关键词 → Agent → Skill 三步分派，歧义消解规则内置（`CLAUDE.md`） | 无 |
| 红线守护 | B/D/C 三组红线 SSOT，违反 CRITICAL 即终止（`rules/01`） | 规则包可换 |
| 可执行门禁 | AST 索引 + 合规检查 + pre-commit 钩子（`tools/harness_gate.py`） | 检查器可换 |
| 需求红蓝对抗 | 红军报告 → lint 机械检查 → 蓝军 9 项评审 → 整改闭环 | 无 |
| 文档健康 | 新鲜度 90 天阈值 / 死链 / 漂移，报告型不阻断（`tools/doc_*`） | 无 |
| 知识蒸馏 | 归档强制蒸馏章节；同类问题 2 次必须固化为规则或 lint（`rules/03`） | 无 |
| 遗留迁移状态机 | 逐 API 8 步、三态进度、失败回滚矩阵（`skills/harness-api-refactor`） | 示例（DDD 向） |

## 目录结构

```
agent-tiller/
├── README.md               # 本文件：框架介绍 + 快速接入
├── AGENTS.md               # 项目入口：代码地图 + 治理索引（拷入后按项目填写）
├── CLAUDE.md               # 意图路由 SSOT（Claude Code 自动加载）
└── .harness/
    ├── agents/             # 8 个 Agent 角色定义 + README
    ├── rules/              # 01 红线 SSOT / 02 架构模式示例 / 03 自进化 / 工程结构 / 编码规范 / 开发流程 / 文档元数据
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
#    - .harness/rules/01：换成你的架构红线（不用 DDD 就替换 D1-D7，保留 B1-B4）
#    - .harness/wiki/ 四个模板：业务模型/接口协议/数据模型/领域术语
#    - .harness/skills/code-discovery/SKILL.md「项目标识」：CBM_PROJECT / CG_PATH（不用 MCP 图谱工具可跳过）
#    - 包名前缀默认自动推断（build_ast_index.py），如需显式指定：export HARNESS_INTERNAL_PREFIX=com.yourcompany

# 5. 验证门禁
python .harness/tools/harness_gate.py --fast    # 阻断式：AST 索引 + 红线合规
python .harness/tools/harness_gate.py --full    # 全量：追加文档健康三件套
```

## 工具一览

| 工具 | 用途 | 阻断式 | 架构依赖 |
|------|------|:---:|---|
| `build_ast_index.py` | tree-sitter 解析全模块 Java，生成 AST 索引树（`index/AST_INDEX.md` + `ast_index.json`）；模块自动发现，内部包前缀自动推断 | — | 无（Java 通用） |
| `ddd_compliance_check.py` | 红线合规检查器（自带 DDD D3/D4/D5/D6 规则 + 3 项启发式 WARNING），输出 COMPLIANCE_REPORT + 历史趋势 jsonl | ✅ CRITICAL 非零退出 | 规则可换 |
| `harness_gate.py` | 门禁编排器：`--fast`（pre-commit）/ `--full`（追加文档健康） | ✅ fast 档 | 无 |
| `install_hooks.py` | 幂等安装 pre-commit 钩子（已有钩子自动备份 .bak） | — | 无 |
| `doc_freshness_scan.py` | frontmatter 元数据 + 90 天新鲜度 + 代码 mtime 漂移 + deprecated 引用检查 | — | 无 |
| `doc_link_check.py` | Markdown 死链 + specs 索引一致性（兼容根目录 / .claude/ 两种 CLAUDE.md 布局） | — | 无 |
| `doc_drift_scan.py` | wiki/specs 中的类名、API 路径对照真实代码，检测文档↔代码漂移 | — | 无 |
| `summary_lint.py` | 需求报告机械检查（状态机终态/死状态/锚点错位/表读写矩阵 L1-L8）+ 蓝军矩阵骨架生成 | ✅ CRITICAL 非零退出 | 无 |
| `alignment_mapper.py` | 意图注入映射表草稿生成：落点锚点脚本真实定位，杜绝手写错位 | — | 无 |

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

MIT（见 LICENSE）
