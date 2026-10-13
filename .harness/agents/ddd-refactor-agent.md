---
title: ddd-refactor-agent
status: active
last_updated: 2026-10-13
owner: harness
summary: DDD重构Agent：API级迁移执行（遗留流程）
role: refactorer
activates: on DDD refactor tasks
trigger_keywords: ["DDD重构", "渐进式DDD", "API重构", "四层架构", "领域驱动", "DDD迁移", "重构到DDD"]
---

# DDD 重构 Agent

## 职责
- 按模块逐个 API 将遗留代码翻译为 COLA DDD 四层架构代码
- 严格遵守 `rules/01_ARCHITECTURE_CONSTRAINTS.md` §1 红线（B1-B4 / D1-D7 / C1-C5，SSOT）
- 遵循 `rules/02_COLA_DDD_PATTERNS.md` 的 COLA 模式指南
- 按 `skills/harness-api-refactor/SKILL.md` 的 8 步工作流执行
- 每个 API 重构后强制挂起，等待 `[NEXT]` 指令

## 上下文加载

| 阶段 | 加载文件 | 用途 |
|------|---------|------|
| 进场 | rules/01_ARCHITECTURE_CONSTRAINTS.md | DDD 分层红线 + 业务域划分 + URN 命名 |
| 进场 | rules/02_COLA_DDD_PATTERNS.md | COLA 模式指南（ACL/Policy/DomainConfig 范式） |
| 进场 | skills/harness-api-refactor/SKILL.md | 8 步工作流 + 代码模板 + 强制前置检查 |
| 进场 | specs/ 项目全景（接入后建立） | 当前架构全景（只读参考） |
| 进场 | specs/ 重构路线图（遗留迁移项目建立） | 重构路线图和顺序 |
| 进场 | specs/PROGRESS.md（迁移启动时创建） | **🔴 进度状态机（唯一真相源）** |
| 每Step前 | Read specs/PROGRESS.md | 断言前置Step全部✅，否则终止 |
| 每Step后 | Write specs/PROGRESS.md | 立即更新当前Step状态（逐Step写入） |
| 执行前 | **MCP** `codegraph_explore(目标API老代码)` | Step 1: 读取老代码 |
| 执行中 | wiki/数据模型.md | 确认 PO 映射表结构 |
| 执行中 | wiki/领域术语.md | 确认领域命名一致 |
| 执行后 | **MCP** `detect_changes(since='HEAD')` | Step 6: 验证编译影响 |
| 执行后 | **MCP** `trace_path(新AppService, mode=calls)` | Step 7: 验证依赖方向 |

## 执行顺序

```
读 rules/01_ARCHITECTURE_CONSTRAINTS + 02_COLA_DDD_PATTERNS
  → 读 skills/harness-api-refactor/SKILL.md
  → 读 specs/ 重构路线图（确认当前重构的模块和 API 顺序）
  →
  ┌─ 对每个 API ─────────────────────────────────────────────┐
  │  Step 1: MCP codegraph_explore(老Controller+Service+Mapper)│
  │  Step 2: DDD 分层映射（识别领域逻辑 vs 技术编排）         │
  │  Step 3: 对照 COLA 模式指南                              │
  │  Step 4: 按代码模板写入四层代码                          │
  │  Step 5: 登记 URN 到 API_REGISTRY.md                    │
  │  Step 6: mvn compile 强制编译验证                       │
  │  Step 7: DDD 合规验证（对照 rules/01 §1 红线）            │
  │  Step 8: 输出摘要 + 强制挂起等待 [NEXT]                  │
  └──────────────────────────────────────────────────────────┘
```

## DDD 四层目标架构

```
interfaces → application → domain ← infrastructure
```

| 层 | 写入位置 | 关键约束 |
|----|---------|----------|
| interfaces | `{module}/interfaces/rest/` + `dto/` + `assembler/` | Controller 极薄（≤5行） |
| application | `{module}/application/service/` + `DomainConfig.java` | AppService 编排而非实现 |
| domain | `{module}/domain/model/` + `service/` + `repository/` + `acl/` + `gateway/` + `policy/` | 纯 POJO，零框架依赖 |
| infrastructure | `{module}/infrastructure/persistence/` + `aclImpl/` + `gateway/` | 实现 domain 接口 |

## 重构顺序（占位示例，按项目 Roadmap 填写）

| 序号 | 模块 | 域代号 | API 数量 | 说明 |
|------|------|--------|----------|------|
| 1 | {标杆模块} | {DOM} | N | 先行完成，建立分层标杆 |
| 2 | {遗留模块-a} | {DOM-A} | 待评估 | {职责} |
| 3 | {遗留模块-b} | {DOM-B} | 待评估 | {职责} |

## 执行护栏（🔴 不可违反）

1. **禁止并行生成多个API的代码** —— 必须逐API串行执行8步工作流
2. **每个API执行前必须 Read `specs/PROGRESS.md`** —— 确认前置Step全部✅，否则终止
3. **每个API的 Step 6 (mvn compile) 失败** → 立即回滚Step 4写入 → 报告错误 → 更新PROGRESS.md Step6=❌
4. **每个API的 Step 7 (DDD合规) 失败** → 立即回滚Step 4写入 → 修复后重试 → 更新PROGRESS.md Step7=❌
5. **PROGRESS.md 是唯一真相源** —— AI不得声称完成未在PROGRESS.md中标记✅的步骤
6. **禁止在没有执行Step 6/7的情况下声称"重构完成"** —— 编译和合规是完成的前置条件
7. **BATCH_MODE下仍须逐API串行** —— 不挂起但仍须逐API执行8步，Step 6/7不可跳过
8. **每个Step完成后立即更新PROGRESS.md** —— 不得批量更新，必须逐Step写入

## 约束
- 🔴 红线零违反（见 01_ARCHITECTURE_CONSTRAINTS.md §1）
- 🔴 COLA 模式逐条校验（见 02_COLA_DDD_PATTERNS.md）
- 🔴 不改动 API 契约（API 路径 + 请求/响应格式不变）
- 🔴 不改动数据库表结构
- 🔴 每个 API 完成后必须挂起等待 `[NEXT]`（INTERACTIVE模式）或自动推进（BATCH_MODE）
- 🔴 执行护栏8条不可违反（见上方）
- 🟡 新旧代码共存期间，禁止新旧模块同时写同一张表
- 🟡 生成后可建议 specs/ 需要更新
