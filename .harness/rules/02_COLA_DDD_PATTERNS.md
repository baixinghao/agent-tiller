---
title: 02_COLA_DDD_PATTERNS
status: active
last_updated: 2026-10-13
owner: harness
summary: COLA四层模式指南：ACL/Policy/DomainConfig/Command/Assembler范式
---
# 02 — COLA DDD 架构模式指南

> 本文件定义 COLA 架构风格的核心模式和范式。
> AI 执行引擎在每次代码生成/重构时必须遵循这些模式。
> 文中代码示例基于 demo 域（user/order），仅作范式演示，接入项目时按真实业务替换命名。

## 1. ACL 模式（Anti-Corruption Layer / 防腐层）

### 1.1 核心原则

- ACL 接口定义在 `domain/acl/`，实现在 `infrastructure/aclImpl/`
- ACL 返回**领域值对象**（domain/model 下的类型），绝不返回外部 DTO
- ACL 隔离外部服务的协议细节，使 domain 层不感知外部变化
- 一个 ACL 接口对应一个外部服务能力

### 1.2 ACL 接口范式

```java
// domain/acl/SmsAcl.java
public interface SmsAcl {
    /**
     * 发送短信验证码
     * @return SendSmsResult 领域值对象（非外部 DTO）
     */
    SendSmsResult sendSmsCode(String mobile, String templateId);
}
```

### 1.3 ACL 实现范式

```java
// infrastructure/aclImpl/SmsAclImpl.java
@Service
public class SmsAclImpl implements SmsAcl {
    private final SmsClient smsClient;  // 外部服务客户端

    @Override
    public SendSmsResult sendSmsCode(String mobile, String templateId) {
        // 1. 调用外部服务
        SmsResponse response = smsClient.send(mobile, templateId);
        // 2. 转换为领域值对象（防腐的关键）
        return new SendSmsResult(response.isSuccess(), response.getMsgId());
    }
}
```

### 1.4 ACL 清单（示例格式，按项目维护）

| ACL 接口 | 隔离的外部系统 | 返回的领域值对象 |
|---------|--------------|----------------|
| SmsAcl（示例） | 短信服务 | SendSmsResult |
| FileStorageAcl（示例） | 对象存储服务 | FileUploadResult |
| UserCenterAcl（示例） | 用户中心 | UserInfo |
| ConfigAcl（示例） | 配置中心 | 业务配置值 |

---

## 2. Policy/Spec 模式（领域规约）

### 2.1 核心原则

- Policy 是**纯函数**：不调 ACL、不调 Repository、不碰 IO
- Policy 接收预取数据作为参数，返回校验结果或抛出 DomainException
- Policy 定义在 `domain/policy/validation/`
- Policy 通过 DomainConfig 注册为 Spring Bean（唯一框架接触点）

### 2.2 Policy 范式

```java
// domain/policy/validation/LoginValidationSpec.java
public class LoginValidationSpec {
    /**
     * 纯函数：校验登录前置条件
     * @throws DomainException 校验失败时抛出
     */
    public void validate(UserAccount userAccount, ChannelInfo channel) {
        if (userAccount.isLocked()) {
            throw new DomainException(ErrorCode.ACCOUNT_LOCKED, "账号已锁定");
        }
        if (!channel.isActive()) {
            throw new DomainException(ErrorCode.CHANNEL_CLOSED, "渠道已关闭");
        }
    }
}
```

### 2.3 Policy 清单（示例格式，按项目维护）

| Policy | 校验内容 | 参数 |
|--------|---------|------|
| LoginValidationSpec（示例） | 登录前置条件校验 | UserAccount, ChannelInfo |
| SmsSendLimitSpec（示例） | 短信发送频率限制 | SmsSendContext |
| OrderSubmitSpec（示例） | 下单前置校验 | Order, UserProfile |

---

## 3. DomainConfig 模式（领域 Bean 装配）

### 3.1 核心原则

- DomainConfig 是 domain 层与 Spring 框架的**唯一接触点**
- 所有领域纯 POJO（DomainService、Policy/Spec）通过 `@Bean` 注册
- domain 层其他类**禁止**使用任何 Spring 注解

### 3.2 DomainConfig 范式

```java
// application/DomainConfig.java
@Configuration
public class DomainConfig {
    @Bean
    public LoginValidationSpec loginValidationSpec() {
        return new LoginValidationSpec();
    }

    @Bean
    public OrderDomainService orderDomainService() {
        return new OrderDomainService();
    }

    // ... 其他领域 Bean
}
```

---

## 4. Command 模式（应用层参数对象）

### 4.1 核心原则

- Command 是 JDK 21 **record**，不可变
- Command 携带 AppService 所需的全部参数
- Command 定义在 `application/service/` 下
- 替代传统的 JSONObject 弱类型参数

### 4.2 Command 范式

```java
// application/service/LoginWithSmsCommand.java
public record LoginWithSmsCommand(
    String mobile,
    String smsCode,
    String channelId
) {}
```

---

## 5. Assembler 模式（DTO ↔ Command ↔ Domain 转换）

### 5.1 核心原则

- Assembler 是纯转换函数，零业务逻辑
- Assembler 定义在 `interfaces/assembler/`
- 标注 `@Component`，由 Controller 调用
- 转换方向：Request DTO → Command, Domain Result → Response DTO

### 5.2 Assembler 范式

```java
// interfaces/assembler/LoginAssembler.java
@Component
public class LoginAssembler {
    public LoginWithSmsCommand toCommand(LoginSmsRequest request) {
        return new LoginWithSmsCommand(
            request.getMobile(),
            request.getSmsCode(),
            request.getChannelId()
        );
    }

    public LoginSmsResponse toResponse(LoginResult result) {
        LoginSmsResponse response = new LoginSmsResponse();
        response.setToken(result.token());
        response.setNeedProfile(result.needProfile());
        return response;
    }
}
```

---

## 6. Repository 模式（仓储）

### 6.1 核心原则

- Repository 接口定义在 `domain/repository/`，返回领域对象（非 PO）
- Repository 实现在 `infrastructure/persistence/`
- 实现类负责 PO ↔ Domain 双向转换
- 方法命名用领域语言：`findById` / `save` / `findPage`

### 6.2 Repository 接口范式

```java
// domain/repository/OrderRepository.java
public interface OrderRepository {
    Order findById(Long orderId);
    void save(Order order);
}
```

### 6.3 Repository 实现范式

```java
// infrastructure/persistence/OrderRepositoryImpl.java
@Repository
public class OrderRepositoryImpl implements OrderRepository {
    private final OrderMapper mapper;

    @Override
    public Order findById(Long orderId) {
        OrderPO po = mapper.selectById(orderId);
        return po != null ? toDomain(po) : null;
    }

    private Order toDomain(OrderPO po) { ... }
    private OrderPO toPO(Order domain) { ... }
}
```

---

## 7. DomainException 模式（领域异常）

### 7.1 核心原则

- 领域异常统一使用 `DomainException`（code + message）
- 由 `GlobalExceptionHandler` 在 interfaces 层统一处理
- 禁止在 domain 层使用 Spring 的异常体系

### 7.2 DomainException 范式

```java
// domain/model/DomainException.java
public class DomainException extends RuntimeException {
    private final int code;
    public DomainException(int code, String message) {
        super(message);
        this.code = code;
    }
    public int getCode() { return code; }
}

// interfaces/rest/GlobalExceptionHandler.java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(DomainException.class)
    public ResponseEntity<ApiResponse<Void>> handleDomain(DomainException ex) {
        return ResponseEntity.badRequest()
            .body(ApiResponse.error(ex.getCode(), ex.getMessage()));
    }
}
```

---

## 8. 外部系统集成清单（示例格式，按项目维护）

| 外部系统 | 用途 | ACL 接口 | Gateway 接口 | 通信方式 |
|---------|------|---------|-------------|---------|
| 短信服务（示例） | 短信验证码/通知 | SmsAcl | — | HTTP |
| 对象存储（示例） | 文件上传/下载 | FileStorageAcl | — | HTTP |
| 用户中心（示例） | 用户注册状态 | UserCenterAcl | — | HTTP |
| 配置中心（示例） | 业务配置/开关 | ConfigAcl | — | HTTP/Redis |
| Redis | 缓存/分布式锁/Token | — | — | Redisson |
| RabbitMQ | 异步消息 | — | — | Spring AMQP |

---

## 9. Per API 检查清单

> 每个 API 重构/新增完成后，AI 执行引擎必须逐项校验：

| # | 检查项 | 通过标准 |
|---|--------|----------|
| 1 | 领域层无 Spring 注解 | domain/ 下无 @Service/@Component/@Repository |
| 2 | Policy 纯函数 | 不调 ACL/Repository/IO |
| 3 | ACL 返回领域值对象 | 返回类型在 domain/model/ 下 |
| 4 | Controller 极薄 | 仅接收请求 + Assembler + 调 AppService |
| 5 | AppService 极薄 | 每行一个关注点，零循环零判断 |
| 6 | DomainConfig 注册了所有领域 Bean | 新增的 Spec/DomainService 已注册 |
| 7 | Command 使用 record | 参数对象是不可变 record |
| 8 | Assembler 双向转换 | Request→Command 和 Result→Response 均覆盖 |
| 9 | 编译通过 | mvn compile 无错误 |
