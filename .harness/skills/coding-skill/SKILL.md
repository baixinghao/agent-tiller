---
title: SKILL
status: active
last_updated: 2026-10-13
owner: harness
summary: COLA DDD编码脚手架（Step 0 契约可认知性检查 + 六步实现 + 机械门禁）
---

# coding-skill — COLA DDD 编码实现技能

> 单一真相源：编码实现步骤以本文件为准（coding-agent 不再维护独立步骤编号）。

## Step 0: 契约可认知性检查（🔴 进场闸门，不过不开工）

三张图（状态机/时序图/决策表）是 coding 的**唯一契约**，原始 PRD 只作溯源参考。
图是人机共治的产物——coding Agent 通常是**纯读图者**，进场先做可认知性检查：

1. **状态前置**：summary frontmatter 必须 `status: approved` 且 `intent_aligned: true`；
   跑 `summary_lint`（或项目 lint 脚本），CRITICAL 未归零禁止开工
2. **三映射列表**（列在脑内或 changes 工作单里）：
   - 状态机每条边 → 聚合状态流转方法 / AppService 分支
   - 时序图每个步骤 → AppService 编排行
   - 决策表每条规则 → Policy/Spec 方法 + 错误码
3. 🔴 **列不出来 = 图的缺口，立即回退**（反馈红军/蓝军，走 review 闭环），
   **禁止边猜边写**——猜的方向与人类拍板方向大概率不一致，返工主要来源
4. 图与图打架（同一边两处矛盾）同样是回退信号，不是自由裁量空间

## Step 1: 确认需求

- 读 specs/{module}/README.md 确认模块边界
- **新模块分叉**：specs/{module} 不存在属正常 → 走 rules/工程结构.md
  「新增模块指南」（父 POM 注册、包名 `com.example.{module}`（按项目 groupId 调整）、四层目录、
  DomainConfig、API_REGISTRY.md），可建议元 Agent 补 specs
- 确认变更是否涉及新的数据库表（无新表也要在 db-migrations.sql 写明"无变更"）
- **MCP** `codegraph_explore(目标模块)` 快速了解现有代码模式
  （**MCP 不可用时降级**：读项目内已完成 DDD 化的标杆模块同特性纵切片——Controller/AppService/
  ACL/aclImpl/PO/Mapper 各一，范式即现行标准）

## Step 2: 数据库变更

- 在 .harness/changes/active/{feature}/db-migrations.sql 中添加 DDL
- 同步更新 .harness/changes/active/{feature}/rollback.sql
- 无 DDL 变更时两个文件也要存在（写明"无变更"与回滚方式），不许省略

## Step 3: 领域层

- **MCP** `search_graph(name_pattern='新实体名')` 确认无同名实体冲突
  （降级：Glob/Grep 全仓搜同名类）
- domain/model/: 新增聚合根/实体/值对象（优先使用 record）；
  聚合根用 `register()`（创建）/ `rebuild()`（仓储重建）工厂，行为方法保护不变量
- domain/policy/validation/: 新增领域规约（纯函数，接收预取数据，不碰 IO）
- domain/acl/: 新增防腐层接口（返回领域值对象，绝不返回外部 DTO）
- domain/repository/: 新增仓储接口（方法命名用领域语言）
- 🔴 **新错误码/新术语必须先确认**（R6 纪律）：只使用契约已确认的命名；
  契约未覆盖的新造词，挂 TODO 标注「未确认」并在交付说明中点名，禁止静默造词

## Step 4: 基础设施层

- infrastructure/persistence/: Repository 实现 + PO（@TableName）+ Mapper
- infrastructure/aclImpl/: ACL 实现；桥接遗产用 ApplicationContext 反射模式，
  降级返回要对应契约的异常列语义（如"外部数据获取失败视同无该数据，主流程降级不阻断"）
- infrastructure/gateway/: Gateway 实现（如需）
- infrastructure/idempotency/: 分布式锁/幂等组件（无成员状态，线程安全）

## Step 5: 应用层 + 接口层

- application/service/: 新增 AppService + Command (record)
- application/DomainConfig.java: 注册新增领域 Bean
- interfaces/assembler/: 新增 Assembler（DTO↔Command↔Domain 双向覆盖）
- interfaces/rest/: 新增 Controller + DTO
- **MCP** `trace_path(目标AppService, mode=calls, depth=2)` 验证依赖链不越界
  （降级：人工核对 import 无其他业务模块类）
- 🔴 **事务语义核对**：失败路径要分清"回滚"与"需持久化的状态置位"
  （如"审核失败需置为已关闭状态"）——后者不能抛异常，用结果对象返回

## Step 6: 验证 + 登记

- 更新 {module}/API_REGISTRY.md 登记 URN（命名：`[{域}_{Feature}]`，仿项目内已完成模块的既有条目）
- 🔴 **机械门禁（必跑，默认构建不触发）**：`mvn -pl {module} checkstyle:check` 零违规
  - ⚠️ 预警：存量代码中历史遗留的不合规写法（如 `catch(Exception)` 兜底）
    不符合现行 checkstyle 规则集——**范式参考时辨别着抄**；
    catch 必须精准异常（如 `BeansException`），禁止 Exception/Throwable 兜底
- **MCP** `detect_changes` 影响范围在预期内（降级：`mvn compile` 全工程通过 + git status 核对）
- 自检清单逐项验证

## 契约锚定纪律（🔴 全六步通用）

关键类/方法的注释必须标契约出处（BR 编号 / 状态机边 / 时序图步骤），
如 `// BR-01 承载者`、`// §5.2 CLOSED 边`——让蓝军评审与后续整改能双向回溯。
写不出出处的代码 = 图外私货，要么删、要么回退确认（Step 0 纪律）。

## 自检清单

- [ ] Step 0 三映射列全（边→方法、步骤→编排、规则→Spec），无回退遗留
- [ ] Controller 极薄（≤5行）
- [ ] AppService 编排而非实现（零循环零判断；编排段用领域谓词，不写业务条件）
- [ ] domain 层无 Spring 注解
- [ ] Policy 纯函数（无副作用，参数由 AppService 预取）
- [ ] ACL 返回领域值对象
- [ ] DomainConfig 注册了新增的领域 Bean
- [ ] Command 使用 record（不可变）
- [ ] Assembler 双向转换覆盖
- [ ] 异常使用 DomainException，错误码出自契约确认集（未确认码挂 TODO 已点名）
- [ ] 敏感字段脱敏（出域前掩码，不明文下发）
- [ ] 关键类/方法注释有契约锚点（BR/边/步骤）
- [ ] `mvn -pl {module} checkstyle:check` 零违规（显式跑过，非默认构建恩赐）
- [ ] 事务语义核对：需持久化的失败置位不走异常回滚
- [ ] 模块依赖不跨越边界
- [ ] **MCP** `detect_changes` 影响范围在预期内（或降级核对记录）
