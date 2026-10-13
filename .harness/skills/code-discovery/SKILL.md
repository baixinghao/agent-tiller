---
title: SKILL
status: active
last_updated: 2026-10-13
owner: harness
summary: 统一代码发现：CBM/codegraph工具路由与CLI降级
---
# code-discovery — 统一代码发现技能

> 整合 **codebase-memory-mcp**（深度图分析）与 **codegraph**（快速代码探索）的优势，
> 为 harness 框架中的所有 Agent 提供统一的代码发现入口。

## 项目标识（🔧 接入时改为你的项目）

```
CBM_PROJECT  = "{你的CBM项目标识}"        # 建议由项目路径派生，如 "F-DDD-your-project"
CG_PATH      = "{你的项目根目录绝对路径}"   # 如 "F:/DDD/your-project"
```

---

## 运行时可用性（MCP / CLI 双通道）

两个工具以 MCP 形式注册在 Claude Code（`~/.claude.json` → mcpServers）。
在 MCP 不可见的环境中（如 Kimi CLI），两者都有 CLI 入口，能力等价，经 Bash 直调：

| 工具 | CLI 调用（🔧 按本机安装路径调整） | 说明 |
|------|-------------------------------|------|
| CBM | `"{CBM 安装目录}/codebase-memory-mcp.exe" cli <tool> '<json>'` | 深度图分析（架构/调用链/ADR） |
| codegraph | `codegraph <子命令>`（init / status / query / explore / node / callers / sync，npm 全局安装后直接在 PATH） | 快速代码探索 |

MCP → CLI 映射（CLI 侧）：

| MCP 调用（Claude Code） | CLI 等价调用 |
|------------------------|----------------------|
| `codegraph_explore(query, projectPath)` | 在项目目录执行 `codegraph explore <query>` |
| `get_architecture` / `trace_path` / `search_graph` / `query_graph` / `detect_changes` / `manage_adr` / `get_code_snippet` / `search_code` | `codebase-memory-mcp.exe cli <tool> '{"project":"{CBM_PROJECT}", ...}'` |
| `index_repository`（CBM）/ `codegraph init` | CBM：`cli index_repository '{"project":"{CBM_PROJECT}", "root_path":"{CG_PATH}"}'`；codegraph：`codegraph sync {CG_PATH}` |

> 🔴 CBM 的 CLI json 必须带 `"project":"{CBM_PROJECT}"`。
> 🟡 本地兜底：`.harness/index/AST_INDEX.md`（tree-sitter 生成，`python .harness/tools/build_ast_index.py` 重建）可覆盖 D1/D5/D8/D12 的基础场景。

---

## 工具路由表

根据场景自动路由到最优工具，避免重复调用：

| # | 场景 | 首选工具 | 调用方式 | 说明 |
|---|------|---------|---------|------|
| D1 | 快速探索函数/类的源码+调用链+影响范围 | **codegraph** | `codegraph_explore(query, projectPath)` | 一次调用返回 verbatim 源码 + call paths + blast radius |
| D2 | 架构概览（模块聚类/分层/边界） | **CBM** | `get_architecture(aspects=['all'])` | Leiden 社区检测，clusters/layers/boundaries |
| D3 | 调用链追踪（calls/data_flow/cross_service） | **CBM** | `trace_path(function_name, mode, depth)` | 3 种模式，深度可配，支持跨服务 |
| D4 | 影响分析（变更波及范围） | **CBM** | `detect_changes(since, base_branch)` | 基于 git diff 的图上影响传播 |
| D5 | 符号精确源码（按 qualified_name） | **CBM** | `get_code_snippet(qualified_name)` | 精确到行号范围 |
| D6 | 语义搜索（跨词汇匹配） | **CBM** | `search_graph(semantic_query=[...])` | 向量余弦搜索，"publish" 匹配 "send" |
| D7 | 名称模式搜索（正则） | **CBM** | `search_graph(name_pattern='...')` | BM25 + 正则混合搜索 |
| D8 | 文本搜索（图增强 grep） | **CBM** | `search_code(pattern)` | grep 命中 + 图去重 + 结构重要性排序 |
| D9 | 复杂多跳查询（Cypher） | **CBM** | `query_graph(query)` | 完整 Cypher，支持 complexity/loop_depth 等属性 |
| D10 | 热路径检测（O(n²) 等） | **CBM** | `query_graph(MATCH ... WHERE transitive_loop_depth>=3 ...)` | 查询 hidden complexity 属性 |
| D11 | 架构决策记录 | **CBM** | `manage_adr(mode='update')` | ADR 持久化，跨会话保留 |
| D12 | 路由/API 端点发现 | **CBM** | `search_graph(label='Route')` | 查找所有 HTTP 端点 |

> **CBM** = codebase-memory-mcp，所有调用需传 `project=CBM_PROJECT`
> **codegraph** 所有调用需传 `projectPath=CG_PATH`

---

## 组合模式

### 模式 A：快速定位 → 深度分析（推荐日常使用）

```
1. codegraph_explore("目标符号")     → 快速获得源码 + 调用链 + 影响范围概览
2. 如需深度分析：
   a. trace_path(符号, mode=calls)   → 精确调用链（含 MyBatis 代理等动态分派）
   b. trace_path(符号, mode=data_flow) → 数据流追踪（参数传递路径）
```

**适用场景**：编码前了解现有代码、评审时追踪依赖、Bug 定位时追踪数据流

### 模式 B：架构感知 → 变更安全（推荐跨模块变更）

```
1. get_architecture(aspects=['all'])  → 获取模块聚类/分层/边界
2. detect_changes(since='HEAD~5')    → 检测最近变更的影响范围
3. 对每个受影响模块：
   trace_path(模块入口, mode=cross_service) → 追踪跨模块影响
```

**适用场景**：元 Agent 审批跨模块变更、重构前影响评估

### 模式 C：漂移检测 → 一致性验证（推荐文档园丁）

```
1. search_graph(label='Route')       → 获取所有实际 API 端点
2. 对比 specs/ 和 wiki/ 中记录的端点 → 检测漂移
3. search_graph(label='Class')       → 获取所有实体类
4. 对比 wiki/数据模型.md 中的字段定义 → 检测漂移
```

**适用场景**：文档新鲜度检查、spec 与实现一致性验证

### 模式 D：热路径扫描 → 性能风险（推荐评审/重构）

```
1. query_graph("MATCH (f:Function|Method)
     WHERE f.transitive_loop_depth >= 3
        OR f.linear_scan_in_loop >= 1
        OR f.unguarded_recursion = true
     RETURN f.qualified_name, f.transitive_loop_depth,
            f.linear_scan_in_loop, f.file_path
     ORDER BY f.transitive_loop_depth DESC")
2. 对每个热路径：
   codegraph_explore(符号) → 获取完整上下文评估风险
```

**适用场景**：代码评审、性能优化、技术债务清理

---

## Agent 集成指南

### coding-agent 使用方式

| 阶段 | 调用 | 目的 |
|------|------|------|
| 进场 | 加载本文件 | 知道何时用哪个工具 |
| 生成前 | D1: `codegraph_explore(目标模块)` | 快速了解现有代码模式 |
| 生成前 | D3: `trace_path(目标AppService, mode=calls, depth=2)` | 确认依赖链不跨越模块边界 |
| 生成前 | D7: `search_graph(name_pattern='新实体名')` | 确认无同名实体冲突 |
| 生成后 | D4: `detect_changes(since='HEAD')` | 验证变更影响范围在预期内 |

### expert-reviewer 使用方式

| 维度 | 调用 | 目的 |
|------|------|------|
| 模块边界 | D3: `trace_path(变更符号, mode=calls, depth=2)` | 验证无越界调用 |
| 重复性 | D6: `search_graph(semantic_query=[功能关键词])` | 搜索已有相似实现 |
| 热路径 | D10: `query_graph(热路径Cypher)` | 检测性能风险 |

### owner (元 Agent) 使用方式

| 场景 | 调用 | 目的 |
|------|------|------|
| 架构决策 | D2: `get_architecture(aspects=['all'])` | 获取聚类/分层/边界 |
| 审批跨模块变更 | D3: `trace_path(入口, mode=cross_service)` | 追踪跨模块影响 |
| 记录决策 | D11: `manage_adr(mode='update')` | 持久化架构决策 |

### doc-gardening-agent 使用方式

| 检查 | 调用 | 目的 |
|------|------|------|
| API 漂移 | D12: `search_graph(label='Route')` | 对比 specs 记录的端点 |
| 实体漂移 | D7: `search_graph(label='Class')` | 对比 wiki 数据模型 |
| 引用可达 | D8: `search_code(引用路径)` | 验证 cross-reference |

### testing-agent 使用方式

| 阶段 | 调用 | 目的 |
|------|------|------|
| 测试前 | D1: `codegraph_explore(被测方法)` | 获取完整源码+调用链，辅助编写 mock |
| 覆盖率缺口 | D9: `query_graph(未测试方法Cypher)` | 查询未被测试调用的 Method |

---

## 约束

- 🔴 优先使用本技能路由表（Claude Code 走 MCP；MCP 不可见的环境走上文「运行时可用性」的 CLI 等价调用），而非直接 Grep/Glob/Read 查找代码定义
- 🔴 不在同一个场景中重复调用两个工具获取相同信息
- 🟡 简单场景（已知文件路径的配置/文档读取）仍使用 Read，不走 MCP
- 🟡 工具不可用或超时 → 降级 Grep/Glob/Read，或用 `.harness/index/AST_INDEX.md` 兜底
- 🟡 项目未索引时，先运行 `index_repository`（CBM）和 `codegraph init`（codegraph）
