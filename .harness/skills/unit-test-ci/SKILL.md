---
title: SKILL
status: active
last_updated: 2026-10-13
owner: harness
summary: CI质量门禁
---
# unit-test-ci — CI 与质量门禁技能

## Maven 构建命令

```bash
# 编译
mvn clean compile

# 运行测试
mvn test

# 打包（跳过测试）
mvn package -DskipTests

# 生成覆盖率报告（JaCoCo）
mvn test jacoco:report
```

## 质量门禁

| 门禁 | 命令/工具 | 通过标准 |
|------|----------|---------|
| 编译检查 | `mvn compile` | 0 error |
| 单元测试 | `mvn test` | 全部通过 |
| 覆盖率报告 | `mvn test jacoco:report` | 报告生成于 `{module}/target/site/jacoco/` |
| 覆盖率门禁 | `mvn verify -Pci`（JaCoCo check） | AppService ≥ 80%, Policy ≥ 90% |
| Checkstyle | `mvn checkstyle:check` | 0 violation（规则集：根目录 checkstyle.xml） |

> **说明**：覆盖率门禁配置在根 pom 的 `ci` profile 中（AppService 包 ≥80% 行覆盖、
> Policy 包 ≥90% 行覆盖）。日常构建默认不强制，CI 流水线显式 `-Pci` 启用。
> Checkstyle 规则集对应红线 B4/C3（IllegalCatch 禁止 catch(Exception) 兜底）等，见根目录 `checkstyle.xml` 头部注释。

## CI 流程

```
代码提交
  ↓
1. mvn compile          → 编译检查
  ↓
2. mvn checkstyle:check → 红线规则检查（IllegalCatch 等）
  ↓
3. mvn test             → 单元测试 + 自动生成 JaCoCo 报告
  ↓
4. mvn verify -Pci      → 覆盖率门禁（AppService ≥ 80%, Policy ≥ 90%）
  ↓
5. mvn package          → 打包
  ↓
部署
```

## 故障排查

| 问题 | 排查方法 |
|------|---------|
| 测试失败 | `mvn test -Dtest=ClassName` 单独运行失败的测试 |
| 依赖冲突 | `mvn dependency:tree` 查看依赖树 |
| 编译失败 | 检查 JDK 版本 (21) 和 Maven 配置 |
| 端口冲突 | 检查 `application.yml` 中的 server.port 和中间件端口 |
| 本地库问题 | 检查 `application.yml` 中 spring.datasource 配置（如本地 H2） |
