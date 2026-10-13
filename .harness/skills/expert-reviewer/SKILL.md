---
title: SKILL
status: active
last_updated: 2026-10-13
owner: harness
summary: 8维度专家评审
---
# expert-reviewer — 专家评审技能

## 评审维度

| 维度 | 权重 | 说明 |
|------|------|------|
| DDD 分层 | 🔴 | 代码是否放在正确的层（Controller→AppService→Domain→Infrastructure） |
| 命名规范 | 🔴 | 类名/方法名/字段名是否遵循 COLA 项目约定 |
| 安全 | 🔴 | 敏感信息脱敏，幂等校验 |
| 异常处理 | 🟡 | 是否使用 DomainException 体系 |
| ACL 隔离 | 🟡 | ACL 是否返回领域值对象，不泄露外部 DTO |
| 重复性 | 🟡 | 是否复用了已有工具类/领域模型 |
| 测试 | 🟡 | 核心逻辑是否有测试覆盖 |
| **MCP 热路径** | 🟡 | **`query_graph` 检测 O(n²) 隐患：transitive_loop_depth≥3 或 linear_scan_in_loop≥1** |
| **MCP 语义重复** | 🟡 | **`search_graph(semantic_query=[功能关键词])` 搜索已有相似实现** |

## 评审流程

```
1. 审查 DDD 分层 → 代码放在正确的层？
   → MCP trace_path(变更符号, mode=calls, depth=2) 验证无越界调用
2. 审查命名 → 遵循命名约定？
3. 审查安全 → 敏感信息脱敏？幂等校验？
4. 审查异常 → DomainException？
5. 审查 ACL 隔离 → ACL 返回领域值对象？
6. 审查重复 → 是否使用了已有的工具类/领域模型？
   → MCP search_graph(semantic_query=[功能关键词]) 搜索已有相似实现
7. 审查测试 → 核心路径和异常路径覆盖？
8. 审查热路径 → MCP query_graph 检测 transitive_loop_depth≥3 或 linear_scan_in_loop≥1
```

## 常见问题

| 问题 | 严重度 | 修正方式 |
|------|--------|---------|
| Controller 包含业务逻辑 | 🔴 | 将逻辑移到 AppService 或 Domain |
| AppService 包含 if/else 业务判断 | 🔴 | 将规则移到 Policy/Spec |
| domain 层有 @Service 注解 | 🔴 | 移除注解，通过 DomainConfig 注册 |
| ACL 返回外部 DTO | 🔴 | 转换为领域值对象 |
| Policy 调用了 ACL/Repository | 🔴 | Policy 必须纯函数，数据由 AppService 传入 |
| 忘记 DomainConfig 注册 | 🔴 | 在 DomainConfig 中添加 @Bean |
| 手写 JSONObject 参数解析 | 🟡 | 使用 Command record |
| 未使用 record 定义值对象 | 🟡 | 改为 record（不可变） |
