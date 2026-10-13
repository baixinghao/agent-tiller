---
title: SKILL
status: active
last_updated: 2026-10-13
owner: harness
summary: 单元测试编写规范
---
# unit-test-write — 单元测试编写技能

## 测试框架

- 后端：JUnit 5 + Mockito + Spring Boot Test
- 测试运行：Maven Surefire

## AppService 层测试模板

```java
@ExtendWith(MockitoExtension.class)
class LoginAppServiceTest {

    @Mock
    private LoginValidationSpec loginValidationSpec;
    @Mock
    private UserAccountRepository userAccountRepository;
    @Mock
    private SmsAcl smsAcl;
    @Mock
    private UserCenterAcl userCenterAcl;

    @InjectMocks
    private LoginAppService loginAppService;

    @Test
    void loginWithSms_ShouldReturnToken_WhenValid() {
        // Arrange
        LoginWithSmsCommand command = new LoginWithSmsCommand("13800138000", "123456", "APP");
        UserAccount userAccount = UserAccount.rebuild(...);
        when(userAccountRepository.findByMobile(command.mobile())).thenReturn(userAccount);
        when(smsAcl.verifyCode(command.mobile(), command.smsCode())).thenReturn(new SendSmsResult(true, "msgId"));

        // Act
        LoginResult result = loginAppService.loginWithSms(command);

        // Assert
        assertNotNull(result);
        assertNotNull(result.token());
    }

    @Test
    void loginWithSms_ShouldThrow_WhenAccountLocked() {
        // Arrange
        UserAccount lockedAccount = UserAccount.rebuild(...); // locked state
        when(userAccountRepository.findByMobile(any())).thenReturn(lockedAccount);

        // Act & Assert
        assertThrows(DomainException.class, () ->
            loginAppService.loginWithSms(command)
        );
    }
}
```

## Controller 层测试模板

```java
@WebMvcTest(LoginController.class)
class LoginControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private LoginAppService loginAppService;

    @Test
    void loginWithSms_ShouldReturn200_WhenValid() throws Exception {
        LoginResult result = new LoginResult("token", true, ...);
        when(loginAppService.loginWithSms(any())).thenReturn(result);

        mockMvc.perform(post("/api/users/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"mobile\":\"13800138000\",\"smsCode\":\"123456\"}"))
            .andExpect(status().isOk());
    }
}
```

## Policy/Spec 层测试模板

```java
class LoginValidationSpecTest {

    private final LoginValidationSpec spec = new LoginValidationSpec();

    @Test
    void validate_ShouldPass_WhenAccountActive() {
        UserAccount userAccount = UserAccount.rebuild(...); // active state
        ChannelInfo channel = new ChannelInfo("APP", true);
        assertDoesNotThrow(() -> spec.validate(userAccount, channel));
    }

    @Test
    void validate_ShouldThrow_WhenAccountLocked() {
        UserAccount lockedAccount = UserAccount.rebuild(...); // locked state
        assertThrows(DomainException.class, () -> spec.validate(lockedAccount, channel));
    }
}
```

## 测试覆盖目标

| 层级 | 覆盖率 | 说明 |
|------|--------|------|
| AppService 核心逻辑 | ≥ 80% | 正常路径 + 异常路径 |
| AppService 辅助逻辑 | ≥ 60% | 至少覆盖正常路径 |
| Controller | ≥ 50% | 主要验证 Assembler 和响应格式 |
| Policy/Spec | ≥ 90% | 所有边界条件 |
| Repository | ≥ 50% | 主要验证 PO↔Domain 转换 |

## 关键测试场景

- AppService: 正常编排、Policy 校验失败、ACL 调用失败、Repository 异常
- Controller: 请求反序列化、Assembler 转换、响应格式
- Policy: 所有校验规则通过、每条规则单独失败、边界条件
- ACL: 外部服务返回成功、外部服务返回失败、超时
- Repository: PO↔Domain 双向转换正确性
