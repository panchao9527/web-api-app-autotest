# CI/CD 集成（GitHub / GitLab / Jenkins）

框架提供三套等价的流水线配置，用哪个平台就用哪份。逻辑一致：
**跑接口+Web测试 → 生成 junit/Allure → 发布报告 → 汇总结果推送钉钉/企微/邮件**。

| 平台 | 配置文件 | 报告发布 | 密钥放哪 |
|------|---------|---------|---------|
| GitHub Actions | `.github/workflows/automation-test.yml` | GitHub Pages | 仓库 Settings → Secrets |
| GitLab CI | `.gitlab-ci.yml` | GitLab Pages | 项目 Settings → CI/CD → Variables |
| Jenkins | `Jenkinsfile` | Allure 插件 | 凭据(Credentials) |

## 共用的密钥/变量（按需配置，不用的留空即可）

| 名称 | 用途 |
|------|------|
| `TEST_USERNAME` / `TEST_PASSWORD` | 测试账号 |
| `DINGTALK_WEBHOOK` / `WECOM_WEBHOOK` | 钉钉/企微机器人 |
| `SMTP_HOST` `SMTP_PORT` `SMTP_USER` `SMTP_PASSWORD` `EMAIL_TO` | 邮件 |
| `DB_USER` `DB_PASSWORD` `REDIS_PASSWORD` | 数据库/缓存(如用到) |

> 通知渠道未配置会自动跳过；配哪个发哪个。

## 报告地址 REPORT_URL（可改）

通知里的报告链接由 `REPORT_URL` 控制，各平台默认：
- GitHub: workflow 里写死的 Pages 地址（`https://<user>.github.io/<repo>/`）
- GitLab: 内置变量 `$CI_PAGES_URL`
- Jenkins: `${BUILD_URL}allure`

**换成公司地址**：直接改对应配置文件里的 `REPORT_URL` 一行即可，例如：
- 公司 GitLab Pages / 内网 Nginx：`http://内网地址/allure-report/`
- Jenkins 归档：`http://jenkins.公司.com/job/xxx/allure/`

> GitLab 建议用 CI/CD Variables 配 `REPORT_URL`，换地址不用改代码。

## 触发时机

三份配置都支持：推送/MR(PR)、每日定时、手动触发（GitHub 的 cron / GitLab 可加 `rules` + pipeline schedule / Jenkins 配置定时构建）。

## 说明

- 汇总推送逻辑统一在 `scripts/notify_from_junit.py`：解析所有 junit 结果 → 合并成一条 → 调 `clients/notify.py`(钉钉/企微) + `clients/email_client.py`(邮件)。
- 三平台**只发一条合并报告**，不会接口、Web 各发一条。
