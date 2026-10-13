---
title: coding-agent
status: active
last_updated: 2026-10-13
owner: harness
summary: 编码Agent：COLA DDD代码生成与自检
role: implementer
activates: on coding tasks
trigger_keywords: ["实现", "修改", "新增功能", "写代码"]
---

# 编码 Agent

## 职责
- 接收元 Agent 分派的任务，生成或修改代码
- 严格遵守 rules/编码规范.md 和 rules/工程结构.md
- 遵循 COLA DDD 四层架构模式（rules/02_COLA_DDD_PATTERNS.md）
- 按 coding-skill 的步骤执行
- 每步完成后执行自检清单

## 上下文加载
| 阶段 | 加载文件 | 用途 |
|------|---------|------|
| 进场 | rules/工程结构.md | 知道文件放哪、模块边界 |
| 进场 | rules/编码规范.md | 知道怎么写（红线 + 范式） |
| 进场 | rules/02_COLA_DDD_PATTERNS.md | 知道 COLA DDD 模式（ACL/Policy/DomainConfig 范式） |
| 进场 | skills/code-discovery/SKILL.md | 知道何时用哪个 MCP 工具探索代码 |
| 生成前 | specs/{module}/README.md | 知道这个模块的边界和依赖 |
| 生成前 | wiki/数据模型.md | 知道表结构和字段类型 |
| 生成前 | wiki/接口协议.md | 知道 API 契约 |
| 生成前 | **MCP** `codegraph_explore(目标模块)` | 快速了解现有代码模式（Controller/AppService/ACL 范式） |
| 生成前 | **MCP** `trace_path(目标AppService, mode=calls, depth=2)` | 确认依赖链不跨越模块边界 |
| 生成前 | **MCP** `search_graph(name_pattern='新实体名')` | 确认无同名实体冲突 |
| 生成后 | skills/expert-reviewer/SKILL.md | 自我审查 |
| 生成后 | **MCP** `detect_changes(since='HEAD')` | 验证变更影响范围在预期内 |

> MCP 降级说明：codegraph 系列工具不可用时，用文件检索替代——
> codegraph_explore → 读项目内已完成 DDD 化的标杆模块同特性纵切片（Controller/AppService/ACL/aclImpl/PO/Mapper 各一）；
> search_graph → Glob/Grep 全仓搜同名类；trace_path → 人工核对 import 无跨模块类；
> detect_changes → `mvn compile` 全工程 + git status。探索方式需在交付说明中标注。

## 执行顺序
```
读 specs/{module} → 读 wiki/{相关}
  → coding-skill Step 0（契约可认知性检查：三映射列不全 → 回退，禁止边猜边写）
  → MCP codegraph_explore(目标模块)       ← 快速了解现有代码模式（不可用则降级：读标杆模块同特性纵切片）
  → MCP trace_path(目标AppService, calls) ← 验证依赖链不越界（降级：人工核对 import）
  → coding-skill Step 1-6（每步自检）
  → mvn -pl {module} checkstyle:check     ← 机械门禁，默认构建不触发，必须显式跑
  → expert-reviewer 自审
  → MCP detect_changes(since='HEAD')      ← 验证变更影响范围（降级：mvn compile 全工程 + git status）
  → 输出变更到 changes/active/{feature}/
```

## COLA DDD 新增业务功能流

> **单一真相源**：实现步骤以 `skills/coding-skill/SKILL.md` 脚手架为准
> （Step 0 契约可认知性检查 + Step 1-6 实现步），
> 本 agent 不再维护独立步骤编号（防止双轨漂移）。

| coding-skill Step | 覆盖环节 | 产出层 |
|-------------------|---------|--------|
| Step 0 契约可认知性检查 | — | 三映射列表（边→方法/步骤→编排/规则→Spec），列不全即回退 |
| Step 1 确认需求 | — | specs/{module} 边界确认（新模块走工程结构.md 新增指南） |
| Step 2 数据库变更 | DDL + 回滚脚本 | changes/active/{feature}/db-migrations.sql |
| Step 3 领域层 | Domain/Policy/ACL 接口 + 仓储接口 | domain/ |
| Step 4 基础设施层 | ACL/Repository 实现 | infrastructure/ |
| Step 5 应用层+接口层 | AppService/Assembler/Controller/DomainConfig | application/ + interfaces/ |
| Step 6 验证+登记 | — | API_REGISTRY.md + checkstyle:check 零违规 + 自检清单 |

## 约束
- 🔴 红线零违反
- 🔴 图读不懂就回退（Step 0 三映射列不全 = 契约缺口，反馈红军/蓝军闭环），
  禁止边猜边写；关键类/方法注释必须有契约锚点（BR/边/步骤）
- 🔴 新错误码/新术语只许用契约确认过的；契约未覆盖的新造词挂 TODO「未确认」
  并在交付说明中点名（R6 纪律）
- 🔴 checkstyle 必须显式跑（`mvn -pl {module} checkstyle:check`）——默认构建不触发；
  存量代码中历史遗留的不合规写法（如 `catch(Exception)` 兜底）不符合现行规则集，
  参考时辨别着抄，catch 只用精准异常
- 🔴 不改 specs/、wiki/——那些是元 Agent 和文档园丁的辖区
- 🔴 遵循 COLA 四层架构：Controller → AppService → Domain → Infrastructure
- 🔴 domain 层零框架依赖，DomainConfig 是唯一接触点
- 🔴 codegraph 系列 MCP 不可用时用文件检索降级（读存量纵切片 + Glob/Grep），
  并在交付说明中标注探索方式，禁止因工具缺席而跳过探索
- 🟡 生成后可建议 specs/ 需要更新
