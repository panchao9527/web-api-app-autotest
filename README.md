# API + Web + App 自动化测试框架

基于 Python 和 pytest 的三端自动化测试框架。保留简单的业务分层，同时内置离线自测、配置校验、敏感数据脱敏、生产环境保护、Allure 报告和三套 CI 配置。

## 第一次使用

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
python scripts/automation.py doctor
python scripts/automation.py self-test
```

详细教程见：[新项目自动化测试：从 0 开始操作指南](docs/新项目从0开始.md)。

## 统一命令

```powershell
# 检查环境
python scripts/automation.py doctor --env uat

# 只跑离线框架自测，不访问外部系统
python scripts/automation.py self-test

# 真实业务测试
python scripts/automation.py test --type api --env uat
python scripts/automation.py test --type web --env uat --headed
python scripts/automation.py test --type app --env uat
python scripts/automation.py test --type all --env uat --marker smoke

# 仅在刚初始化、业务目录尚无用例时显式放行；正式 CI 不要使用
python scripts/automation.py test --type api --env uat --allow-empty

# 清理报告和缓存
python scripts/automation.py clean
```

默认执行 `pytest` 只运行 `tests/framework/` 下的离线框架自测。真实项目用例必须放在 `testcases/`，并通过统一命令或显式目录运行。业务测试没有收集到任何用例时默认失败，防止路径或 marker 写错后 CI 仍显示绿色；只有模板初始化阶段才使用 `--allow-empty`。

## 目录

```text
api/                 API 业务封装
pages/               Web Page Object
screens/             App Screen Object
testcases/           真实业务测试
tests/framework/     框架自身离线测试
examples/            外部站点和占位教学示例，默认不执行
fixtures/            共享 fixture 和数据清理
clients/             DB、Redis、通知和邮件客户端
core/                HTTP、断言、Web/App driver 等核心能力
config/              多环境配置
data/                测试数据
scripts/              统一命令和 CI 脚本
docs/                 使用文档
```

## 依赖安装

```powershell
# 只做 API
python -m pip install -r requirements-api.txt

# API + Web
python -m pip install -r requirements-web.txt
python -m playwright install chromium

# App
python -m pip install -r requirements-app.txt

# MySQL / Redis
python -m pip install -r requirements-infra.txt

# 一次安装全部
python -m pip install -r requirements.txt
```

## 安全规则

- API、Web、App、网络录制和基础设施日志中的密码、token、Authorization、Cookie、手机号等字段强制脱敏。
- `prod` 默认禁止运行。
- 生产测试必须同时使用 `--allow-prod` 和 `ALLOW_PROD_TESTS=1`。
- 获得生产授权后仍只收集 `prod_safe` 用例。
- 生产环境 HTTP 仅允许访问配置的同源 API，并只允许 GET/HEAD/OPTIONS。
- 生产环境禁止数据库和 Redis 写入；保护同时作用于 fixture 和直接客户端调用。
- 全局失败重试已取消，避免真实缺陷被重试成绿色。

## Marker

| Marker | 用途 |
|---|---|
| `api` / `web` / `app` | 测试端类型 |
| `smoke` | 每次提交执行的核心链路 |
| `regression` | 定时完整回归 |
| `p0` / `p1` / `p2` | 业务优先级 |
| `prod_safe` | 人工审核后的生产只读用例 |
| `flaky` | 已登记的不稳定用例，不代表默认重试 |

## CI

仓库提供 GitHub Actions、GitLab CI 和 Jenkins 配置。框架自测是业务测试的前置门禁；API 和 Web 使用独立 Allure 目录并行执行，结束后合并报告。详见 [CI/CD 集成](docs/ci.md)。

## 其他文档

- [API 测试指南](docs/api-guide.md)
- [Web 测试指南](docs/web-guide.md)
- [Appium 环境搭建](docs/appium-setup.md)
- [基础设施客户端](docs/infra-clients.md)
- [工具与 Fixture](docs/utils-fixtures.md)
- [代码规范](docs/coding-standards.md)
- [UI 与 API 分工策略](docs/ui-api-strategy.md)
