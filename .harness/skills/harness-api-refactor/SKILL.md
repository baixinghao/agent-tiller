---
title: SKILL
status: active
last_updated: 2026-10-13
owner: harness
summary: 渐进式DDD重构引擎：8步工作流（遗留模块迁移流程）
---
# SKILL — 渐进式 DDD 驱动：API 级重构与生成引擎

> 本技能定义 AI 如何按模块逐个 API 将遗留代码
> 翻译为 COLA DDD 四层架构代码（JDK 21 + Spring Boot 3.x）。

---

## 1. 目标架构：COLA DDD 四层

```
interfaces → application → domain ← infrastructure
```

| 层 | 职责 | 关键约束 |
|----|------|----------|
| **interfaces** | REST Controller / DTO / Assembler | Controller 极薄：接收请求 + Assembler 转换 + 调 AppService |
| **application** | AppService / Command / 事件发布契约 | 编排而非实现：每行一个关注点，零循环零判断 |
| **domain** | 聚合根 / 实体 / 值对象 / 领域事件 / ACL 契约 / Repository 契约 / policy / 领域服务 | 零外部依赖：纯 POJO，domain/ 下禁止 @Service/@Component/@Repository |
| **infrastructure** | persistence / aclImpl / eventImpl / idempotency | 实现 domain 定义的接口，技术细节封装于此 |

### 硬约束（红线）

> 📌 **红线的唯一来源（SSOT）**：[rules/01_ARCHITECTURE_CONSTRAINTS.md §1](../../rules/01_ARCHITECTURE_CONSTRAINTS.md)（B1-B4 业务安全 / D1-D7 DDD 分层 / C1-C5 代码规范）。
> 每个 API 重构前逐条校验，违反 CRITICAL 项即终止。本文件不维护红线副本。

---

## 2. 目录规范

### 2.1 新项目结构（写入）

```
{module}/src/main/java/com/example/{module}/
├── interfaces/
│   ├── rest/                          # *Controller.java
│   ├── dto/                           # *Request.java, *Response.java
│   └── assembler/                     # *Assembler.java
├── application/
│   ├── DomainConfig.java              # 领域 Bean 装配
│   └── service/                       # *AppService.java, *Command.java (record)
├── domain/
│   ├── model/                         # 聚合根 / 实体 / 值对象 / DomainException
│   ├── service/                       # *DomainService.java
│   ├── repository/                    # *Repository.java (接口)
│   ├── acl/                           # *Acl.java (接口)
│   ├── gateway/                       # *Gateway.java (接口)
│   ├── event/                         # 领域事件
│   └── policy/                        # *Spec.java (纯函数)
│       └── validation/
└── infrastructure/
    ├── persistence/
    │   ├── *RepositoryImpl.java       # Repository 实现
    │   ├── po/                        # *PO.java (MyBatis-Plus)
    │   └── mapper/                    # *Mapper.java (BaseMapper)
    ├── aclImpl/                       # *AclImpl.java
    ├── gateway/                       # *GatewayImpl.java
    ├── eventImpl/                     # 事件发布实现
    └── idempotency/                   # 幂等性实现
```

> 包名前缀 `com.example` 按项目实际 groupId 调整。

---

## 3. 重构顺序

> 按业务域逐模块重构，每个模块内按 API 逐个推进。
> 🔧 下表为占位示例：先在某个模块完成标杆重构，再按 Roadmap 逐个迁移遗留模块。

### 重构顺序表（按项目 Roadmap 填写）

| 序号 | 域 | 模块 | API 数量 | 说明 |
|------|-----|------|----------|------|
| 1 | {DOM} | {标杆模块} | N | 先行完成，建立分层标杆 |
| 2 | {DOM-A} | {遗留模块-a} | 待评估 | {职责} |
| 3 | {DOM-B} | {遗留模块-b} | 待评估 | {职责} |

---

## 4. 每个 API 的 8 步工作流

### 4.0 PROGRESS.md 状态模型（🔴 不可违反）

> PROGRESS.md 中每个 Step 的值**仅允许以下 3 种**，禁止使用任何其他符号。
> 框架不附带 PROGRESS.md——首次启动遗留迁移时在 `specs/PROGRESS.md` 创建，逐 API 逐 Step 登记。

| 符号 | 含义 | 前置检查判定 | 允许的后续转换 |
|------|------|-------------|--------------|
| ⬜ | 未执行 | **不满足** | → ✅（正常完成）或 → ❌（失败） |
| ✅ | 已完成且通过验证 | **满足** | 不可回退（永久标记） |
| ❌ | 已执行但失败 | **不满足** | → ✅（修复后重试通过）或 → ⬜（回滚后重新执行） |

**禁止项**：
- 🔴 禁止使用 🔄、⚠️、❓ 或任何其他符号
- 🔴 禁止在未走完 8 步工作流的情况下将任何 Step 标记为 ✅
- 🔴 并行生成的代码**不构成任何 Step = ✅ 的依据**——必须按工作流逐API串行执行

#### 4.0.1 Step 失败处理规则

| 失败Step | 回滚范围 | PROGRESS.md 更新 | 后续动作 |
|----------|---------|-----------------|---------|
| Step 1-3 | 无代码写入，无需回滚 | 该Step = ❌ | INTERACTIVE: 等待人工; BATCH_MODE: 终止 |
| Step 4 | 删除本次写入的文件 | Step4 = ❌ | 修复后从Step4重新执行 |
| Step 5 | 无代码影响 | Step5 = ❌ | 重新登记 |
| Step 6 | **删除 Step 4 写入的全部文件** | Step4=⬜, Step5=⬜, Step6=❌ | 修复后从Step4重新执行 |
| Step 7 | **删除 Step 4 写入的全部文件** | Step4=⬜, Step5=⬜, Step6=⬜, Step7=❌ | 修复后从Step4重新执行 |

### 4.1 强制前置检查（不可跳过）

> 📌 **本节的前置检查表是唯一来源（SSOT）**，PROGRESS.md 仅含指针。
> **🔴 硬约束**：AI 在执行任何 Step 前必须先 Read `specs/PROGRESS.md`，
> 确认该 API 的前置 Step 全部为 ✅（参见 §4.0 状态模型定义）。
> ⬜ 和 ❌ 均视为"不满足"。跳步即违反硬约束，必须终止。

| 即将执行 | 必须满足的前置条件 | 不满足时动作 |
|---------|-------------------|-------------|
| Step 1 | 无（起始步骤） | — |
| Step 2 | Step 1 = ✅ | 终止，报告"未读取老代码" |
| Step 3 | Step 1-2 = ✅ | 终止，报告"未完成DDD分层映射" |
| Step 4 | Step 1-3 = ✅ | 终止，报告"未完成COLA模式校验" |
| Step 5 | Step 4 = ✅ | 终止，报告"未写入新模块代码" |
| Step 6 | Step 4-5 = ✅ | 终止，报告"未登记URN" |
| Step 7 | Step 6 = ✅ 且编译通过 | 终止，报告"编译未通过，不可做合规检查" |
| Step 8 | Step 6-7 = ✅ | 终止，报告"编译或合规未通过" |

### 4.2 执行模式

| 模式 | 触发条件 | Step 8 行为 | 适用场景 |
|------|---------|------------|---------|
| INTERACTIVE | 默认 | 强制挂起，等待人类 `[NEXT]` | 逐API人工审查 |
| BATCH_MODE | 用户请求含"全部"/"完成"/"批量" | 不挂起，自动推进下一API | 批量渐进（Step 6/7 仍强制） |

> **⚠️ BATCH_MODE 不等于跳步**：仍然逐API串行执行8步工作流，
> 仍然强制执行 Step 6（编译）和 Step 7（合规），只是 Step 8 不挂起。

### 4.3 工作流定义

```
┌─────────────────────────────────────────────────────────────────┐
│ 前置: Read specs/PROGRESS.md，断言前置Step全部✅，否则终止        │
├─────────────────────────────────────────────────────────────────┤
│ Step 1: 读取老代码                                                │
│   - Controller + Service + Mapper + Entity                      │
│   - 识别业务逻辑 vs 技术关注点                                      │
│   - 完成后: 更新 PROGRESS.md Step1=✅                            │
├─────────────────────────────────────────────────────────────────┤
│ Step 2: DDD 分层映射                                              │
│   - 哪些是领域逻辑 → domain/model + domain/service + policy       │
│   - 哪些是技术编排 → application/service                          │
│   - 哪些是外部依赖 → domain/acl + domain/gateway                  │
│   - 哪些是持久化   → domain/repository + infrastructure/persistence│
│   - 完成后: 更新 PROGRESS.md Step2=✅                            │
├─────────────────────────────────────────────────────────────────┤
│ Step 3: 对照 COLA 模式指南                                        │
│   - 逐条校验 02_COLA_DDD_PATTERNS.md                              │
│   - ACL 返回领域值对象？Policy 纯函数？DomainConfig 注册？         │
│   - 完成后: 更新 PROGRESS.md Step3=✅                            │
├─────────────────────────────────────────────────────────────────┤
│ Step 4: 写入新模块                                                │
│   - 按目录规范生成四层代码                                          │
│   - 生成 DomainConfig.java 注册领域 Bean                          │
│   - 生成 Assembler 做 DTO↔Command↔DomainObject 转换              │
│   - 完成后: 更新 PROGRESS.md Step4=✅                            │
├─────────────────────────────────────────────────────────────────┤
│ Step 5: 登记 URN                                                  │
│   - 在 API_REGISTRY.md 中登记 API 映射关系                        │
│   - 标注重构状态：✅ 已完成 / ⬜ 未开始（禁止使用🔄等非标准符号）   │
│   - 完成后: 更新 PROGRESS.md Step5=✅                            │
├─────────────────────────────────────────────────────────────────┤
│ Step 6: 强制编译验证                                              │
│   - mvn compile -pl {module}                                     │
│   - 失败则回滚 Step 4 写入，报告错误，更新 PROGRESS.md Step6=❌   │
│   - 成功后: 更新 PROGRESS.md Step6=✅                            │
├─────────────────────────────────────────────────────────────────┤
│ Step 7: DDD 合规验证（委托 ddd-architect-agent）                  │
│   - 领域层无 Spring 注解？                                        │
│   - Policy 纯函数？                                               │
│   - ACL 返回领域值对象？                                           │
│   - 依赖方向正确？                                                 │
│   - 违规则回滚 Step 4，修复后重新提交合规检查                      │
│   - 失败: 更新 PROGRESS.md Step7=❌                              │
│   - 成功后: 更新 PROGRESS.md Step7=✅                            │
├─────────────────────────────────────────────────────────────────┤
│ Step 8: 输出摘要 + 推进                                           │
│   - 输出本次重构摘要（见 §9.1）                                    │
│   - 更新 PROGRESS.md Step8=✅                                    │
│   - INTERACTIVE 模式: 挂起等待 [NEXT]                            │
│   - BATCH_MODE 模式: 自动推进到下一个API                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 代码模板要点

> AI 已理解 COLA DDD 四层模式，无需完整模板。以下仅列出关键约束和骨架。

### 5.1 Controller (interfaces/rest/) — 极薄
- `@RestController` + `@Tag` + `@Operation` (SpringDoc)
- 方法体 ≤ 5 行：Assembler 转换 → 调 AppService → 包装返回

### 5.2 AppService (application/service/) — 编排而非实现
- `@Service` + 构造器注入（Repository/ACL/其他AppService）
- 每行一个关注点：Policy校验 → 领域对象创建/状态流转 → Repository持久化 → ACL副作用
- 零循环零判断（业务规则在 domain 层）

### 5.3 聚合根 (domain/model/) — 纯 POJO
- 工厂方法：`register()`（创建）、`rebuild()`（从持久化重建）
- 行为方法：状态流转 + 不变量保护（违反抛 `DomainException`）
- getter 无 setter，状态变更通过行为方法

### 5.4 Repository 接口 (domain/repository/) — 依赖倒置
- 返回领域对象（非 PO），方法命名用领域语言（`findById`/`save`/`findPage`）

### 5.5 Repository 实现 (infrastructure/persistence/)
- `@Repository` implements domain 接口
- `toDomain(PO)` / `toPO(Domain)` 双向转换

### 5.6 Assembler (interfaces/assembler/) — DTO↔Command↔Domain 转换
- `@Component`，纯转换函数，零业务逻辑

### 5.7 DomainConfig (application/) — 领域 Bean 装配
- `@Configuration` + `@Bean` 注册领域纯 POJO（DomainService/Spec）

### 5.8 Command (application/service/) — JDK 21 record
- 不可变值对象，携带 AppService 所需的全部参数

---

## 6. DDD 合规检查规则

### 6.1 编译期检查 (ArchUnit 风格)

```java
// 领域层无 Spring 注解
noClasses()
    .that().resideInAPackage("..domain..")
    .should().beAnnotatedWith("@Service", "@Component", "@Repository")
    .check(importedClasses);

// 依赖方向：domain 不依赖 infrastructure
noClasses()
    .that().resideInAPackage("..domain..")
    .should().dependOnClassesThat()
    .resideInAPackage("..infrastructure..")
    .check(importedClasses);
```

### 6.2 运行期检查

| 检查项 | 检查方式 |
|--------|----------|
| domain/ 下无 @Service/@Component/@Repository | grep -r "@Service\|@Component\|@Repository" domain/ |
| Policy 不调 ACL/Repository | 代码审查：policy/ 下类的方法参数不含 ACL/Repository 类型 |
| ACL 返回领域值对象 | 代码审查：ACL 接口方法的返回类型在 domain/model/ 下 |
| Controller 极薄 | 代码审查：Controller 方法体 ≤ 5 行 |
| AppService 极薄 | 代码审查：AppService 方法无 for/while 循环，无 if/else 业务判断 |

> 🟡 机械检查优先用 `python .harness/tools/ddd_compliance_check.py`（基于 AST 索引，输出 COMPLIANCE_REPORT），人工审查兜语义层。

---

## 7. API 注册表格式

> 每个 DDD 模块维护一个 `API_REGISTRY.md`，格式如下（示例行为 demo 域）：

```markdown
# {Module} API 注册表

| URN | HTTP | Path | Controller | AppService | 重构状态 | 编译 | 测试 |
|-----|------|------|-----------|------------|---------|------|------|
| USR_UserLogin | POST | /api/users/login | LoginController | LoginAppService | ✅ | ✅ | ✅ |
| ORD_OrderList | POST | /api/orders/list | OrderController | OrderAppService | ✅ | ✅ | ⬜ |
```

---

## 8. 渐进式共存策略

> 新旧代码在过渡期共存，遵循以下规则：

### 8.1 Maven 模块共存

- 新 DDD 模块独立 Maven module
- 旧代码保持原有包结构
- **迁移策略**：删除旧代码 → 新 DDD 代码接管 → 验证 API 无感知

### 8.2 数据库共存

- 新旧模块共享同一数据库
- PO 对象映射相同表结构
- **禁止**新旧模块同时写同一张表（避免并发冲突）

---

## 9. 输出规范

### 9.1 每个 API 重构完成后输出

```
═══════════════════════════════════════════════════════
  ✅ USR_UserLogin 重构完成
═══════════════════════════════════════════════════════
  生成文件：
    - interfaces/rest/LoginController.java
    - interfaces/dto/LoginSmsRequest.java, LoginSmsResponse.java
    - interfaces/assembler/LoginAssembler.java
    - application/service/LoginAppService.java
    - application/service/LoginWithSmsCommand.java
    - domain/model/UserAccount.java (聚合根)
    - domain/model/LoginResult.java (值对象)
    - domain/repository/UserAccountRepository.java
    - domain/acl/SmsAcl.java, UserCenterAcl.java
    - domain/policy/validation/LoginValidationSpec.java
    - infrastructure/persistence/UserAccountRepositoryImpl.java
    - infrastructure/persistence/po/UserAccountPO.java
    - infrastructure/persistence/mapper/UserAccountMapper.java
    - infrastructure/aclImpl/SmsAclImpl.java, UserCenterAclImpl.java
    - application/DomainConfig.java (更新)

  COLA 模式：
    ✅ ACL 返回领域值对象
    ✅ Policy 纯函数
    ✅ DomainConfig 注册领域 Bean
    ✅ Command 使用 record

  DDD 合规：
    ✅ 领域层无 Spring 注解
    ✅ 依赖方向正确
    ✅ ACL 返回领域值对象

  编译：✅ 通过
═══════════════════════════════════════════════════════
  ⏸ 等待 [NEXT] 继续...
═══════════════════════════════════════════════════════
```
