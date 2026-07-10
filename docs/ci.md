# CI/CD 集成

仓库提供 GitHub Actions、GitLab CI 和 Jenkins 三套配置。共同流程是：

```text
ruff 检查 -> 离线框架自测 -> API/Web 业务测试 -> 合并 Allure -> 通知
```

## 执行范围

- push、PR/MR：业务测试使用 `smoke`。
- 定时流水线：业务测试使用 `regression`。
- Jenkins 通过 `TEST_MARKER` 参数选择；定时触发由 Jenkins 任务配置负责。
- GitLab 的定时执行需要在项目 Pipeline schedules 中创建计划。
- GitHub 定时配置已写入 workflow，北京时间每天 02:00 执行。

框架离线自测始终先执行。它失败时不应继续相信业务测试结果。

## CI Secret

按实际需要配置：

| 变量 | 用途 |
|---|---|
| `TEST_USERNAME` / `TEST_PASSWORD` | 测试账号 |
| `API_TOKEN` | 固定 API token |
| `DB_USER` / `DB_PASSWORD` | 测试数据库 |
| `REDIS_PASSWORD` | Redis |
| `DINGTALK_WEBHOOK` / `DINGTALK_SECRET` | 钉钉通知 |
| `WECOM_WEBHOOK` | 企业微信通知 |
| `SMTP_HOST` / `SMTP_PORT` | SMTP 服务 |
| `SMTP_USER` / `SMTP_PASSWORD` / `EMAIL_TO` | 邮件通知 |

不要把这些值直接写入 workflow、`.gitlab-ci.yml` 或 Jenkinsfile。

## 报告目录

并行任务必须写入不同目录：

```text
reports/allure-framework
reports/allure-api
reports/allure-web
```

报告阶段再合并。禁止两个并行 pytest 进程同时使用带 `--clean-alluredir` 的同一个目录。

## GitHub Actions

文件：`.github/workflows/automation-test.yml`

需要：

1. 在仓库 Settings -> Secrets and variables -> Actions 配置 Secret。
2. 在 Settings -> Pages 确认允许发布 Pages。
3. 主分支不是 `main` 时修改 workflow 触发分支。
4. 公司网络无法访问 GitHub 托管 runner 时使用 self-hosted runner。

## GitLab CI

文件：`.gitlab-ci.yml`

需要：

1. 在 Settings -> CI/CD -> Variables 配置变量并设置 masked/protected。
2. 在 Build -> Pipeline schedules 创建每日回归计划。
3. Runner 无法访问测试环境时使用内网 Runner。
4. GitLab Pages 被禁用时，将 `pages` job 改成上传到公司报告服务器。

## Jenkins

文件：`Jenkinsfile`

需要安装 JUnit、Allure 插件，并建立与 Jenkinsfile 一致的 Secret text 凭据 ID。Jenkins agent 需要 Python 3.10-3.12；Web 测试还需要安装 Playwright 浏览器的权限。

`TEST_MARKER` 参数默认是 `smoke`。创建每日定时构建时将参数改成 `regression`。

## 生产环境

流水线不应默认设置 `ALLOW_PROD_TESTS=1`。生产只读验证应使用独立、受审批的手动任务，并同时传入：

```text
ALLOW_PROD_TESTS=1
--allow-prod
```

框架仍只会收集 `prod_safe` 用例。
