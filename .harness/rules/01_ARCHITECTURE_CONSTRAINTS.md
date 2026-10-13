---
title: 01_ARCHITECTURE_CONSTRAINTS
status: active
last_updated: 2026-10-13
owner: harness
summary: DDD分层红线、业务域划分、URN命名与依赖矩阵（红线SSOT）
---
# 01 — 架构约束与业务域字典

> 本文件定义 COLA DDD 项目的**绝对红线**、**分层规则**、**业务域划分**和**语义 ID 命名规范**。
> AI 执行引擎在每次代码生成/重构前必须逐条校验，违反任何 CRITICAL 项即终止。
> 🔧 **接入新项目时**：§1 红线为通用约束可直接沿用；§3/§4/§5/§8 含 `{...}` 占位与 demo 示例（order/user），必须替换为项目真实业务域。

---

## 1. 绝对红线 (CRITICAL CONSTRAINTS)

> 📌 **本节是红线的唯一来源（SSOT）**（B1-B4 业务安全 / D1-D7 DDD 分层 / C1-C5 代码规范）。
> AGENTS.md、agents/owner.md、skills/harness-api-refactor 仅含指针，禁止另存副本。

### 1.1 业务安全红线（金融级通用要求）

| # | 红线 | 说明 |
|---|------|------|
| B1 | 防重幂等 | 所有 POST 核心业务 API 首行必须调用幂等校验或分布式锁 |
| B2 | 敏感信息脱敏 | 手机号/身份证等敏感字段在日志和 API 响应中必须脱敏 |
| B3 | SQL 注入防御 | 禁止字符串拼接 SQL，MyBatis-Plus 使用 `#{}` 而非 `${}`（动态表名除外） |
| B4 | 异常精准处理 | 禁止 `catch(Exception)` 兜底，禁止 `printStackTrace`，禁止一个异常打多次日志 |

### 1.2 DDD 分层红线

| # | 红线 | 说明 |
|---|------|------|
| D1 | 实体只做不变量 + 纯状态流转 | 无 IO、无外部数据、无 ACL 调用 |
| D2 | 领域服务封装领域流程编排 | 不碰技术资源（不落库、不发事件、不管事务/幂等） |
| D3 | Policy 必须纯 | 不调 ACL、不调 Repository、不碰 IO |
| D4 | 依赖倒置 | domain 拥有全部契约接口，infrastructure 实现 |
| D5 | 领域层零框架依赖 | `domain/` 下禁止 `@Service` / `@Component` / `@Repository` |
| D6 | ACL 返回领域值对象 | 不能是 ACL 包内的 DTO，必须是 domain/model 下的类型 |
| D7 | DomainConfig 唯一接触点 | domain 层与 Spring 框架的唯一接触面是 application/DomainConfig.java，其余领域类禁用 Spring 注解 |

### 1.3 代码规范红线

| # | 红线 | 说明 |
|---|------|------|
| C1 | 实体极简原则 | 优先复用已有 DTO/VO/Entity，禁止为单个 API 创建重复嵌套内部类 |
| C2 | 参数强类型 | 禁止 JSONObject 手工解析参数，使用强类型 Command (record) |
| C3 | 异常精准处理 | 同 B4（保留编号以兼容既有引用，条文以 B4 为准） |
| C4 | Controller 极薄 | 仅做三件事：接收请求 + Assembler 转换 + 调用 AppService |
| C5 | AppService 极薄 | 每行一个关注点，零循环零判断，编排而非实现 |

---

## 2. 目标架构：COLA DDD 四层

```
interfaces → application → domain ← infrastructure
                              ↑          ↑
                              │          └── implements Repository/ACL/Gateway
                              │
                        DomainConfig (@Bean 注册领域纯 POJO)
```

### 2.1 各层职责

| 层 | 包路径 | 职责 | 依赖方向 |
|----|--------|------|----------|
| **interfaces** | `{module}/interfaces/` | HTTP 协议适配、参数校验、DTO 转换 | → application |
| **application** | `{module}/application/` | 技术编排（事务/幂等/ACL调用/事件发布），无业务规则 | → domain |
| **domain** | `{module}/domain/` | 纯业务逻辑，零框架依赖（纯 POJO） | 无外部依赖 |
| **infrastructure** | `{module}/infrastructure/` | 技术实现（持久化/外部服务/缓存/消息） | → domain (实现接口) |

### 2.2 各层子包规范

```
{module}/
├── interfaces/
│   ├── rest/              # REST Controller (@RestController)
│   ├── dto/               # Request / Response DTO (Jackson 序列化)
│   └── assembler/         # DTO ↔ Command / DTO ↔ DomainObject 转换器
│
├── application/
│   ├── DomainConfig.java  # 领域层 Bean 装配 (纯 POJO 注册为 @Bean)
│   └── service/           # AppService (@Service) + Command (record)
│
├── domain/
│   ├── model/             # 聚合根 / 实体 / 值对象 / 领域异常
│   ├── service/           # 领域服务 (纯 POJO，跨实体编排)
│   ├── repository/        # 仓储接口 (依赖倒置)
│   ├── acl/               # 防腐层接口 (依赖倒置，隔离外部服务)
│   ├── gateway/           # 外部网关接口 (依赖倒置，隔离 HTTP 调用)
│   ├── event/             # 领域事件定义
│   └── policy/            # 领域规约 (纯函数，无副作用)
│       └── validation/    # 校验规约
│
└── infrastructure/
    ├── persistence/        # Repository 实现 + PO + Mapper
    │   ├── po/             # 持久化对象 (MyBatis-Plus @TableName)
    │   └── mapper/         # MyBatis-Plus Mapper (BaseMapper<PO>)
    ├── aclImpl/            # ACL 接口实现
    ├── gateway/            # Gateway 接口实现 (RestClient)
    ├── eventImpl/          # 领域事件发布实现
    └── idempotency/        # 幂等性/分布式锁实现
```

---

## 3. 业务域划分 (Bounded Context)

> 🔧 **占位示例**：以下以 demo 域（ORD 订单 / USR 用户）示范填写格式，接入时替换为你的真实业务域。

### 3.1 核心业务域（示例，按项目改写）

| 域代号 | 域名称 | Maven 模块 | 说明 | 核心聚合 |
|--------|--------|-----------|------|----------|
| **ORD** | 订单（示例） | `order` | {订单创建/查询/取消} | Order, OrderItem |
| **USR** | 用户（示例） | `user` | {登录/注册/资料} | User, UserProfile |

### 3.2 支撑域（示例，按项目改写）

| 域代号 | 域名称 | 说明 |
|--------|--------|------|
| **MSG** | 消息通知 | 短信/推送/站内信 |
| **FILE** | 文件存储 | 文件上传/下载 |
| **CFG** | 配置中心 | 业务配置/开关/参数 |

### 3.3 通用域 (Shared Kernel)

| 域代号 | 域名称 | Maven 模块 | 说明 |
|--------|--------|-----------|------|
| **COMMON** | 通用 | `common` | 注解/常量/异常/工具/基类 |

---

## 4. 全局语义 ID 命名规范 (Semantic URNs)

> 格式：`[域代号_动宾短语]`，禁止数字递增 ID。
> 每个 API、Command、领域事件均需登记 URN。

### 4.1 URN 登记表（示例，按项目扩充）

| URN | 说明 | 对应 API |
|-----|------|---------|
| ORD_OrderSubmit | 提交订单（示例） | POST /api/orders/submit |
| ORD_OrderCancel | 取消订单（示例） | POST /api/orders/cancel |
| USR_UserLogin | 用户登录（示例） | POST /api/users/login |

---

## 5. 微服务职责字典 (当前阶段：单体模块化)

> 当前阶段保持单体部署，但按业务域拆分为独立 Maven 模块，为未来微服务化做准备。
> 🔧 下表为占位示例，接入时按 §3 的业务域划分填写。

| 模块 | 域代号 | 职责 | 状态 |
|------|--------|------|------|
| order（示例） | ORD | {订单相关职责} | ⬜ 待迁移 / ✅ 已完成 |
| user（示例） | USR | {用户相关职责} | ⬜ 待迁移 |
| common | COMMON | 通用工具/注解/异常/基类 | ⬜ 待拆分 |

---

## 6. 当前重构边界

### 6.1 第一阶段约束

- **不改动 API 契约**：API 路径、请求/响应格式保持不变
- **不改动数据库表结构**：表名/字段名保持不变
- **仅重构内部实现**：Controller → AppService → DomainService → Repository
- **渐进式迁移**：新旧代码共存，通过 Maven 模块隔离

### 6.2 后续阶段开放

- 可改动 API 接口（统一 RESTful 规范）
- 可调整数据库表结构（遵循领域模型）
- 可拆分为微服务独立部署

---

## 7. 单步 API 断点模式（遗留模块迁移时启用）

> 每个 API 重构遵循状态机：`[待命] → [执行] → [强制挂起/自动推进]`
> **唯一真相源**：`specs/PROGRESS.md` —— 所有进度状态以此文件为准。
> 本框架不附带 PROGRESS.md：首次启动遗留迁移时按 [skills/harness-api-refactor/SKILL.md](../skills/harness-api-refactor/SKILL.md) §4.0 的状态模型创建。

1. AI 执行前必须 Read `specs/PROGRESS.md`，断言前置Step全部✅，否则终止
2. AI 读取老代码 → DDD 分层映射 → 对照 COLA 模式指南 → 写入新模块
3. 登记 URN → 强制编译验证 → DDD 合规验证
4. 每个 Step 完成后立即更新 `specs/PROGRESS.md`（逐Step写入，禁止批量更新）
5. **INTERACTIVE 模式**：强制挂起，等待人类指令 `[NEXT]` 才继续下一个 API
6. **BATCH_MODE**：不挂起，自动推进下一API，但 Step 6/7 仍强制执行
7. 任何一步失败 → 回滚本次写入 → 报告错误 → 更新 PROGRESS.md 为 ❌ → 等待人工介入（INTERACTIVE）或终止（BATCH_MODE）

> 📌 8 步工作流与前置检查表的详细定义见 [skills/harness-api-refactor/SKILL.md §4](../skills/harness-api-refactor/SKILL.md)（唯一来源）。

---

## 8. 依赖矩阵 (模块间依赖规则)

```
                    ┌──────────────────────────────────────────────┐
                    │           {your-project} (root POM)           │
                    └──────┬──────────┬──────────┬────────────────┘
                           │          │          │
                    ┌──────▼──┐ ┌─────▼───┐ ┌───▼────────┐
                    │{module-a}│ │{module-b}│ │ {module-c} │ ...
                    └────┬────┘ └────┬─────┘ └─────┬──────┘
                         │           │              │
                    ┌────▼───────────▼──────────────▼────┐
                    │         common (通用域)              │
                    └────────────────────────────────────┘

规则：
- 同层业务模块禁止互相依赖 ({module-a} ↛ {module-b})
- 所有模块可依赖 common
- common 禁止依赖任何业务模块
```
