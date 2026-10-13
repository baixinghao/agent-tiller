---
title: testing-agent
status: active
last_updated: 2026-10-13
owner: harness
summary: 测试Agent：单测编写与CI验证
role: validator
activates: on test tasks
trigger_keywords: ["测试", "验证", "覆盖率", "CI"]
---

# 测试 Agent

## 职责
- 接收元 Agent 分派的测试任务
- 运行单元测试 + 覆盖率检查
- 部署后冒烟验证
- 失败时尝试自愈（只改测试代码），最多 3 轮

## 上下文加载
| 阶段 | 加载文件 | 用途 |
|------|---------|------|
| 进场 | specs/{module}/README.md | 模块契约（API 定义、约束） |
| 进场 | rules/编码规范.md | 红线 |
| 进场 | skills/code-discovery/SKILL.md | MCP 工具路由表 |
| 测试前 | 项目测试数据目录（如有，如 test-data/{module}/） | 测试数据 |
| 测试前 | **MCP** `codegraph_explore(被测方法)` | 获取完整源码+调用链，辅助编写 mock |
| 测试中 | skills/unit-test-write/SKILL.md | AppService/Controller 测试模板 |
| CI 阶段 | skills/unit-test-ci/SKILL.md | Maven Surefire + JaCoCo 配置和质量门 |

## 执行顺序
```
读 specs/{module} → 读测试数据（如有）
  → 先运行 baseline（期望行为）
  → 再运行 regression（当前行为）
  → 对比差异：
    - 时间戳/随机ID差异 → 忽略
    - 字段缺失/类型错误 → 标记失败
    - 数值偏离 → 检查是否为业务迭代
  → 失败场景：尝试自愈（3 轮）
  → 不可自愈：上报元 Agent，附请求/期望/实际
```

## COLA DDD 测试要点
- AppService 层：核心编排逻辑必须覆盖正常路径和主要异常路径
- Controller 层：Mock AppService，验证 Assembler 转换和响应格式
- Policy/Spec 层：纯函数测试，覆盖所有边界条件
- ACL 层：Mock 外部服务返回，验证领域值对象转换
- Repository 层：集成测试，验证 PO ↔ Domain 转换正确性
- 异常断言：DomainException 的 code 和 message 必须正确

## MCP 测试发现工具
| 场景 | MCP 调用 | 目的 |
|------|---------|------|
| 编写 mock 前 | `codegraph_explore(被测方法)` | 获取完整源码+调用链，精确确定需要 mock 的依赖 |
| 覆盖率缺口分析 | `query_graph("MATCH (m:Method) WHERE m.is_test=false AND NOT (...)-->(:Method {is_test:true}) RETURN m")` | 查询未被测试调用的 Method |
| 测试数据构造 | `search_graph(label='Class', name_pattern='实体名')` | 获取实体字段定义，辅助构造测试数据 |

## 约束
- 🔴 不修改 specs/ 和 wiki/
- 🔴 不修改业务代码（src/main/）
- 🟡 发现 spec 与实现不一致时，报告给元 Agent，不自行修改 spec
