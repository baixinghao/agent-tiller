---
title: AGENTS
status: active
last_updated: 2026-10-13
owner: harness
summary: 项目入口：代码地图与治理索引（接入后按项目填写概览与索引）
---
# AGENTS.md — 项目入口与代码地图

> 本文件是 AI Agent 进入项目的**第一张地图**：项目概览、红线指针、意图路由速览、文件索引。
> 意图路由的完整定义（SSOT）在 [CLAUDE.md](CLAUDE.md)；红线的唯一定义在 [.harness/rules/01](.harness/rules/01_ARCHITECTURE_CONSTRAINTS.md)。
> 🔧 标注「接入填写」的小节，拷入你的项目后必须改写。

## 项目概览（🔧 接入填写）

| 属性 | 值 |
|------|-----|
| 项目 | {项目名} — {一句话定位} |
| 技术栈 | {如 Spring Boot 3.x / MyBatis-Plus / Redisson / Spring AMQP} |
| JDK/构建 | {如 JDK 21, Maven 多模块} |
| 数据库 | {如 MySQL (生产) / H2 (本地)} |
| 架构 | COLA 四层 DDD (interfaces → application → domain ← infrastructure) |
| 现状 | {如 user 模块已完成 DDD 化，作为分层标杆；order 模块正常开发中} |

---

## 红线（不可违反）

> 📌 **唯一来源（SSOT）**：[.harness/rules/01_ARCHITECTURE_CONSTRAINTS.md](.harness/rules/01_ARCHITECTURE_CONSTRAINTS.md) §1（B1-B4 业务安全 / D1-D7 DDD 分层 / C1-C5 代码规范）。
> 执行任何代码任务前必须 Read 该文件 §1 逐条校验。本文件不内嵌红线副本。

---

## 意图路由（速览）

> 📌 SSOT 在 [CLAUDE.md](CLAUDE.md)「⚡ 意图路由与执行指令」（含歧义消解、BATCH_MODE、"架构探索"行）。
> 此处仅核心路由速览；新增/修改路由只改 CLAUDE.md。

| 用户意图关键词 | → Agent | → Skill |
|---------------|---------|---------|
| "分析需求"/"解析PRD"/"需求分析" | requirement-analysis-agent | doc-analysis |
| "评审需求"/"需求评审"/"蓝军评审" | requirement-review-agent | requirement-review |
| "整改需求"/"按findings整改" | requirement-analysis-agent | doc-analysis（§5.3 接单模式） |
| "实现"/"修改"/"新增功能"/"修bug" | coding-agent | coding-skill |
| "测试"/"验证"/"覆盖率" | testing-agent | unit-test-write / unit-test-ci |
| "DDD合规"/"分层检查"/"架构评审" | ddd-architect-agent | code-discovery + expert-reviewer |
| "文档"/"新鲜度"/"一致性" | doc-gardening-agent | code-discovery（驱动 doc_* 三件套） |
| "DDD重构"/"API重构"/"四层架构"/"DDD迁移" | ddd-refactor-agent | harness-api-refactor（遗留模块迁移） |
| "架构探索" | owner（自执行） | arch-explore（仅手动触发） |

---

## 文件索引（🔧 接入填写业务路径）

| 你想做什么 | 去哪里 |
|----------|--------|
| 了解 Agent 角色与协作 | [.harness/agents/README.md](.harness/agents/README.md) |
| 了解意图路由规则 | [CLAUDE.md](CLAUDE.md) |
| 查看 DDD 架构约束（红线 SSOT） | [.harness/rules/01_ARCHITECTURE_CONSTRAINTS.md](.harness/rules/01_ARCHITECTURE_CONSTRAINTS.md) |
| 查看 COLA DDD 模式指南 | [.harness/rules/02_COLA_DDD_PATTERNS.md](.harness/rules/02_COLA_DDD_PATTERNS.md) |
| 查看自进化机制 | [.harness/rules/03_SELF_EVOLUTION.md](.harness/rules/03_SELF_EVOLUTION.md) |
| 查看项目模块结构与依赖 | [.harness/rules/工程结构.md](.harness/rules/工程结构.md) |
| 查看编码规范 | [.harness/rules/编码规范.md](.harness/rules/编码规范.md) |
| 了解开发流程与质量门禁 | [.harness/rules/开发流程规范.md](.harness/rules/开发流程规范.md) |
| 了解业务模型与实体关系 | [.harness/wiki/业务模型.md](.harness/wiki/业务模型.md) |
| 查看 API 接口协议 | [.harness/wiki/接口协议.md](.harness/wiki/接口协议.md) |
| 查看数据库表结构 | [.harness/wiki/数据模型.md](.harness/wiki/数据模型.md) |
| 查看术语与 Redis Key 约定 | [.harness/wiki/领域术语.md](.harness/wiki/领域术语.md) |
| 查看/编写模块规格 | [.harness/specs/](.harness/specs/) |
| 记录变更 | [.harness/changes/](.harness/changes/) |
| 查看技能模板 | [.harness/skills/](.harness/skills/) |
| AST 索引树（生成物） | [.harness/index/AST_INDEX.md](.harness/index/AST_INDEX.md)（重生成：`python .harness/tools/build_ast_index.py`） |

### 快速路径（示例，接入改写）

| 找什么 | 位置 |
|--------|------|
| 启动类 | `{module}/src/main/java/com/example/{module}/{Module}Application.java` |
| 领域配置 | `{module}/.../application/DomainConfig.java` |
| Controller 层 | `{module}/.../interfaces/rest/` |
| AppService 层 | `{module}/.../application/service/` |
| 领域模型 | `{module}/.../domain/model/` |
| ACL 接口 / 实现 | `{module}/.../domain/acl/` ↔ `{module}/.../infrastructure/aclImpl/` |
| Repository 接口 / 实现 | `{module}/.../domain/repository/` ↔ `{module}/.../infrastructure/persistence/` |
| PO + Mapper | `{module}/.../infrastructure/persistence/po/` + `mapper/` |
| API 注册表 | `{module}/API_REGISTRY.md` |

---

## .harness/ 目录结构

```
.harness/
├── agents/             # Agent 角色定义（owner/coding/ddd-refactor/ddd-architect/testing/doc-gardening/requirement-analysis/requirement-review）
├── rules/              # 规则（01红线SSOT/02 COLA模式/03自进化机制/工程结构/编码规范/开发流程/文档元数据）
├── specs/              # 规格（项目全景/重构路线图/PROGRESS/模块规格，README 为编写指南）
├── wiki/               # 知识库（业务模型/接口协议/数据模型/领域术语）
├── skills/             # 技能（doc-analysis/requirement-review/coding-skill/expert-reviewer/unit-test-write/unit-test-ci/code-discovery/harness-api-refactor）
├── lessons/            # 教训暂存区（open → distilled → closed 回流管道）
├── tools/              # 可执行治理（build_ast_index/ddd_compliance_check/doc_*_scan/doc_link_check/harness_gate/install_hooks/summary_lint/alignment_mapper）
├── index/              # 生成物（AST_INDEX/COMPLIANCE_REPORT/DOC_HEALTH/compliance_history，脚本产物禁手改）
├── changes/            # 变更管理（active/shipped，归档强制知识蒸馏）
├── requests/           # 需求分析报告（目录即档案，_review/ 红蓝对抗过程文件）
└── EVOLUTION_LOG.md    # harness 体系演化日志（ADR 式）
```

---

## 数据流（COLA DDD 四层）

```
HTTP Request
  → Controller (@RestController)
    → Assembler (DTO → Command)
      → AppService (@Service, 编排而非实现)
        → Policy/Spec (纯函数校验)
        → DomainService (领域流程编排)
        → AggregateRoot (状态流转)
        → Repository (持久化契约)
        → ACL (防腐层契约, 隔离外部服务)
          → RepositoryImpl (MyBatis-Plus)
          → ACLImpl (Redis/HTTP/MQ)
```

---

## 文档维护

| 文件 | 更新时机 |
|------|----------|
| CLAUDE.md | 意图路由变更 / Agent 增删 |
| AGENTS.md（本文件） | 项目概览 / 代码地图 / 模块结构变更 |
| .harness/agents/ | Agent 角色职责变更 |
| .harness/rules/ | 规范变更/架构模式更新（实质修改需 EVOLUTION_LOG ADR） |
| .harness/wiki/ | 新增表/API/业务实体 |
| .harness/specs/ | 模块边界/依赖变更 / 重构进度 |
| .harness/changes/ | 每次功能发布 |
